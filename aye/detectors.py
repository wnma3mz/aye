from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


ANSI_LAYOUT_BREAK_RE = re.compile(r"\x1b\[(?P<count>\d*)[ABEFJK]")
ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
MENU_CHOICE_RE = re.compile(
    r"^\s*(?:[│┃|]\s*)?(?:[>❯›»►▸▶︎•●◦○◆◇▪︎]\s*)*"
    r"(?:(?:\[\s*)?(?:\d+|[A-Za-z])(?:\s*\])?[.)]?\s+|[-*]\s+)?"
    r"(?P<label>.+?)\s*$"
)
MENU_CONTEXT_RE = re.compile(
    r"(do you want|would you like|proceed|continue|confirm|allow|permission|operation|execute|enter to select|"
    r"是否|确认|继续|执行|允许|选择)",
    re.IGNORECASE,
)
MENU_ENTER_CONFIRM_RE = re.compile(r"(press\s+enter|enter\s+to\s+(confirm|select))", re.IGNORECASE)
MENU_CHOICE_SCAN_LINES = 160
MENU_CONTEXT_LOOKBACK_LINES = 140
MENU_NO_LOOKAHEAD_LINES = 40
SHELL_COMMAND_RE = re.compile(r"Bash\((?P<command>[^\r\n)]*)\)")
DOLLAR_COMMAND_RE = re.compile(r"(?m)^\s*\$\s+(?P<command>[^\r\n]+)")


@dataclass(frozen=True)
class PromptRule:
    name: str
    pattern: str
    answer: str = "yes"
    flags: int = re.IGNORECASE | re.MULTILINE

    def compile(self) -> re.Pattern[str]:
        return _compile_pattern(self.pattern, self.flags)


@dataclass(frozen=True)
class PromptMatch:
    rule_name: str
    answer: str
    excerpt: str


@dataclass(frozen=True)
class BlockedCommandRule:
    name: str
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE

    def compile(self) -> re.Pattern[str]:
        return _compile_pattern(self.pattern, self.flags)


_PATTERN_CACHE: dict[tuple[str, int], re.Pattern[str]] = {}


def _compile_pattern(pattern: str, flags: int) -> re.Pattern[str]:
    key = (pattern, flags)
    compiled = _PATTERN_CACHE.get(key)
    if compiled is None:
        compiled = re.compile(pattern, flags)
        _PATTERN_CACHE[key] = compiled
    return compiled


@dataclass(frozen=True)
class BlockedCommandMatch:
    rule_name: str
    excerpt: str


DEFAULT_RULES: tuple[PromptRule, ...] = (
    PromptRule(
        name="explicit-type-yes",
        pattern=r"(type|enter)\s+['\"]?yes['\"]?\s+to\s+(continue|proceed|confirm)",
    ),
    PromptRule(
        name="ai-cli-permission-yes",
        pattern=r"(do you want to|would you like to).{0,80}(continue|proceed|allow|run|execute).{0,80}\byes\b",
    ),
    PromptRule(
        name="ai-cli-permission-yn",
        pattern=r"((allow|approve).{0,80}(run|execute|command|tool|shell|edit|write)|(run|execute|command|tool|shell|edit|write).{0,80}(allow|approve|confirm)).{0,80}(\[y/N\]|\(y/N\)|\by/n\b)",
        answer="y",
    ),
    PromptRule(
        name="claude-trust-folder",
        pattern=r"^\s*[>❯›»]?\s*1[.)]\s*Yes,\s*I trust this folder\b",
        answer="",
    ),
    PromptRule(
        name="claude-theme-choice",
        pattern=r"^\s*[>❯›»]?\s*1[.)]\s*Dark mode\s*✔?\s*$",
        answer="",
    ),
    PromptRule(
        name="press-enter-continue",
        pattern=r"press\s+enter\s+to\s+continue",
        answer="",
    ),
    PromptRule(
        name="ai-cli-yes-choice",
        pattern=r"(^|\n)\s*(?:[^\w\s]\s*)?\[?1[.)\]]\s*yes\b[\s\S]{0,600}\n\s*(?:[^\w\s]\s*)?\[?\d+[.)\]]\s*no\b",
        answer="",
    ),
    PromptRule(
        name="selected-first-yes-choice",
        pattern=r"^\s*[>❯›»]\s*1[.)]\s*Yes\b",
        answer="",
    ),
)


DEFAULT_BLOCKED_COMMANDS: tuple[BlockedCommandRule, ...] = (
    BlockedCommandRule(
        name="rm",
        pattern=r"(^|[\s;&|`$()])(?:sudo\s+)?rm(?:\s|$)",
    ),
    BlockedCommandRule(
        name="rmdir",
        pattern=r"(^|[\s;&|`$()])(?:sudo\s+)?rmdir(?:\s|$)",
    ),
    BlockedCommandRule(
        name="unlink",
        pattern=r"(^|[\s;&|`$()])(?:sudo\s+)?unlink(?:\s|$)",
    ),
)


def last_lines(text: str, count: int) -> str:
    if count <= 0:
        return text
    return "\n".join(text.splitlines()[-count:])


def find_confirmation(
    text: str,
    rules: Iterable[PromptRule] = DEFAULT_RULES,
    *,
    scan_lines: int = 20,
) -> PromptMatch | None:
    searchable = _normalize_terminal_text(last_lines(text, scan_lines))
    for rule in rules:
        if rule.name == "ai-cli-yes-choice":
            menu_searchable = _normalize_terminal_text(last_lines(text, max(scan_lines, MENU_CHOICE_SCAN_LINES)))
            match = _find_yes_menu_choice(menu_searchable, answer=rule.answer)
            if match is not None:
                return match
            continue
        match = rule.compile().search(searchable)
        if match:
            return PromptMatch(
                rule_name=rule.name,
                answer=rule.answer,
                excerpt=_excerpt(searchable, match.start(), match.end()),
            )
    return None


def find_blocked_command(
    text: str,
    rules: Iterable[BlockedCommandRule] = DEFAULT_BLOCKED_COMMANDS,
    *,
    scan_lines: int = 20,
) -> BlockedCommandMatch | None:
    searchable = _normalize_terminal_text(last_lines(text, scan_lines))
    for rule in rules:
        match = rule.compile().search(searchable)
        if match:
            return BlockedCommandMatch(
                rule_name=rule.name,
                excerpt=_excerpt(searchable, match.start(), match.end()),
            )
    return None


def latest_shell_command(text: str) -> str | None:
    commands = shell_commands(text)
    if not commands:
        return None
    return commands[-1]


def shell_commands(text: str) -> list[str]:
    searchable = _normalize_terminal_text(text)
    commands = [match.group("command").strip() for match in SHELL_COMMAND_RE.finditer(searchable)]
    commands.extend(match.group("command").strip() for match in DOLLAR_COMMAND_RE.finditer(searchable))
    return commands


def _excerpt(text: str, start: int, end: int, radius: int = 120) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    excerpt = text[left:right].strip()
    return re.sub(r"\s+", " ", excerpt)


def _normalize_terminal_text(text: str) -> str:
    with_layout_breaks = ANSI_LAYOUT_BREAK_RE.sub(_layout_break_to_newlines, text)
    without_escape_codes = ANSI_ESCAPE_RE.sub("", with_layout_breaks)
    return without_escape_codes.replace("\r\n", "\n").replace("\r", "\n")


def _layout_break_to_newlines(match: re.Match[str]) -> str:
    count_text = match.group("count")
    count = int(count_text) if count_text else 1
    return "\n" * max(count, 1)


def _find_yes_menu_choice(text: str, *, answer: str) -> PromptMatch | None:
    lines = text.splitlines()
    for yes_index, line in enumerate(lines):
        yes_choice = _parse_menu_choice(line)
        if yes_choice != "yes":
            continue

        no_index = _find_following_no_choice(lines, yes_index)
        if no_index is None:
            continue

        start = max(0, yes_index - MENU_CONTEXT_LOOKBACK_LINES)
        end = min(len(lines), no_index + 6)
        excerpt_text = "\n".join(lines[start:end])
        if not MENU_CONTEXT_RE.search(excerpt_text):
            continue

        return PromptMatch(
            rule_name="ai-cli-yes-choice",
            answer=_yes_choice_answer(line, excerpt_text=excerpt_text, default=answer),
            excerpt=_excerpt(excerpt_text, 0, len(excerpt_text)),
        )
    return None


def _find_following_no_choice(lines: list[str], yes_index: int) -> int | None:
    for index in range(yes_index + 1, min(len(lines), yes_index + MENU_NO_LOOKAHEAD_LINES)):
        choice = _parse_menu_choice(lines[index])
        if choice == "no":
            return index
    return None


def _parse_menu_choice(line: str) -> str | None:
    match = MENU_CHOICE_RE.match(line)
    if match is None:
        return None
    label = match.group("label").strip().lower()
    if label.startswith(("yes", "allow", "approve")):
        return "yes"
    if label.startswith(("no", "deny", "cancel")):
        return "no"
    return None


def _yes_choice_answer(line: str, *, excerpt_text: str, default: str) -> str:
    return default
