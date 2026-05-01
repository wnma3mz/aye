from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .config import default_config_json, load_config
from .updater import update_current_binary
from .wrapper import run_wrapped_command


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"aye {__version__}")
        return 0

    if args.wrapped_command and args.wrapped_command[0] == "init-config":
        path = args.wrapped_command[1] if len(args.wrapped_command) > 1 else "aye.json"
        Path(path).write_text(default_config_json(), encoding="utf-8")
        print(f"Wrote config to {path}")
        return 0

    if args.wrapped_command and args.wrapped_command[0] == "update":
        return update_current_binary(current_executable=sys.argv[0])

    config = load_config(args.config)
    command = _wrapped_command(args.wrapped_command)
    return run_wrapped_command(
        command,
        config,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aye",
        description="Run Claude in this terminal and auto-confirm matching prompts.",
    )
    parser.add_argument("--config", help="Path to a JSON configuration file.")
    parser.add_argument("--version", action="store_true", help="Print the aye version and exit.")
    parser.add_argument("wrapped_command", nargs=argparse.REMAINDER, help="Command to run. Defaults to claude.")
    return parser


def _wrapped_command(command: list[str]) -> list[str]:
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        return ["claude"]
    return command


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
