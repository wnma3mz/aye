from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class PromptRule:
    name: str
    pattern: str
    answer: str = "yes"
    flags: int = re.IGNORECASE | re.MULTILINE

    def compile(self) -> re.Pattern[str]:
        return re.compile(self.pattern, self.flags)


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
        return re.compile(self.pattern, self.flags)


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
        pattern=r"(^|\n)\s*(?:>\s*)?(?:1[.)]\s*)?yes\b[^\n]*\n\s*(?:2[.)]\s*)?no\b",
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
    scan_lines: int = 12,
) -> PromptMatch | None:
    searchable = last_lines(text, scan_lines)
    for rule in rules:
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
    scan_lines: int = 12,
) -> BlockedCommandMatch | None:
    searchable = last_lines(text, scan_lines)
    for rule in rules:
        match = rule.compile().search(searchable)
        if match:
            return BlockedCommandMatch(
                rule_name=rule.name,
                excerpt=_excerpt(searchable, match.start(), match.end()),
            )
    return None


def _excerpt(text: str, start: int, end: int, radius: int = 120) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    excerpt = text[left:right].strip()
    return re.sub(r"\s+", " ", excerpt)
