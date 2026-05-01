from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
MENU_CHOICE_RE = re.compile(
    r"^\s*(?:[>❯›»►▸▶︎•●◦○◆◇▪︎-]\s*)?"
    r"(?:(?:\[\s*)?(?:\d+|[A-Za-z])(?:\s*\])?[.)]?\s+|[-*]\s+)?"
    r"(?P<label>.+?)\s*$"
)
MENU_CONTEXT_RE = re.compile(
    r"(do you want|would you like|proceed|continue|confirm|allow|permission|operation|execute|run|enter to select|"
    r"是否|确认|继续|执行|允许|选择)",
    re.IGNORECASE,
)
SHELL_COMMAND_RE = re.compile(r"Bash\((?P<command>[^\r\n)]*)\)")


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
        name="ai-cli-yes-choice",
        pattern=r"(^|\n)\s*(?:[^\w\s]\s*)?\[?1[.)\]]\s*yes\b[\s\S]{0,600}\n\s*(?:[^\w\s]\s*)?\[?\d+[.)\]]\s*no\b",
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
            match = _find_yes_menu_choice(searchable, answer=rule.answer)
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
    return [match.group("command").strip() for match in SHELL_COMMAND_RE.finditer(searchable)]


def _excerpt(text: str, start: int, end: int, radius: int = 120) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    excerpt = text[left:right].strip()
    return re.sub(r"\s+", " ", excerpt)


def _normalize_terminal_text(text: str) -> str:
    without_escape_codes = ANSI_ESCAPE_RE.sub("", text)
    return without_escape_codes.replace("\r\n", "\n").replace("\r", "\n")


def _find_yes_menu_choice(text: str, *, answer: str) -> PromptMatch | None:
    lines = text.splitlines()
    for yes_index, line in enumerate(lines):
        yes_choice = _parse_menu_choice(line)
        if yes_choice != "yes":
            continue

        no_index = _find_following_no_choice(lines, yes_index)
        if no_index is None:
            continue

        start = max(0, yes_index - 4)
        end = min(len(lines), no_index + 6)
        excerpt_text = "\n".join(lines[start:end])
        if not MENU_CONTEXT_RE.search(excerpt_text):
            continue

        return PromptMatch(
            rule_name="ai-cli-yes-choice",
            answer=answer,
            excerpt=_excerpt(excerpt_text, 0, len(excerpt_text)),
        )
    return None


def _find_following_no_choice(lines: list[str], yes_index: int) -> int | None:
    for index in range(yes_index + 1, min(len(lines), yes_index + 14)):
        choice = _parse_menu_choice(lines[index])
        if choice == "no":
            return index
    return None


def _parse_menu_choice(line: str) -> str | None:
    match = MENU_CHOICE_RE.match(line)
    if match is None:
        return None
    label = match.group("label").strip().lower()
    if label.startswith("yes"):
        return "yes"
    if label.startswith("no"):
        return "no"
    return None
