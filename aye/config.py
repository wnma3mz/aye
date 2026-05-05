from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .detectors import DEFAULT_RULES, PromptRule


@dataclass(frozen=True)
class AyeConfig:
    scan_lines: int = 20
    cooldown_seconds: float = 8.0
    dedupe_repeated_prompts: bool = False
    rules: tuple[PromptRule, ...] = field(default_factory=lambda: DEFAULT_RULES)


def load_config(path: str | Path | None) -> AyeConfig:
    if path is None:
        return AyeConfig()

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = tuple(_rule_from_dict(item) for item in data.get("rules", [])) or DEFAULT_RULES
    return AyeConfig(
        scan_lines=int(data.get("scan_lines", AyeConfig().scan_lines)),
        cooldown_seconds=float(data.get("cooldown_seconds", AyeConfig().cooldown_seconds)),
        dedupe_repeated_prompts=bool(data.get("dedupe_repeated_prompts", AyeConfig().dedupe_repeated_prompts)),
        rules=rules,
    )


def default_config_json() -> str:
    data: dict[str, Any] = {
        "scan_lines": 20,
        "cooldown_seconds": 8.0,
        "dedupe_repeated_prompts": False,
        "rules": [
            {"name": rule.name, "pattern": rule.pattern, "answer": rule.answer}
            for rule in DEFAULT_RULES
        ],
    }
    return json.dumps(data, indent=2) + "\n"


def _rule_from_dict(data: dict[str, Any]) -> PromptRule:
    return PromptRule(
        name=str(data["name"]),
        pattern=str(data["pattern"]),
        answer=str(data.get("answer", "yes")),
    )
