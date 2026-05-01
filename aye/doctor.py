from __future__ import annotations

from pathlib import Path
import platform
import shutil
import sys

from . import __version__
from .updater import _asset_name, _fetch_latest_release


def run_doctor(*, current_executable: str) -> int:
    print(f"aye: {__version__}")
    print(f"python: {platform.python_version()}")
    print(f"platform: {platform.system()} {platform.machine()}")
    print(f"executable: {Path(current_executable).resolve()}")

    _print_cli_status("claude")
    _print_cli_status("gemini")
    _print_cli_status("codex")

    try:
        release = _fetch_latest_release()
        tag = str(release["tag_name"])
        _asset_name(tag)
        print(f"github: ok ({tag})")
    except Exception as exc:
        print(f"github: failed ({exc})")
        return 1

    if not sys.stdin.isatty():
        print("terminal: stdin is not a TTY")
    else:
        print("terminal: TTY ok")

    return 0


def _print_cli_status(command: str) -> None:
    path = shutil.which(command)
    if path is None:
        print(f"{command}: not found")
    else:
        print(f"{command}: {path}")
