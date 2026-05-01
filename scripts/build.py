from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PROJECT_ROOT / "scripts" / "consent_pilot_entry.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a standalone Aye executable.")
    parser.add_argument("--name", default="aye", help="Output executable name.")
    parser.add_argument("--clean", action="store_true", help="Remove PyInstaller cache before building.")
    args = parser.parse_args()

    _ensure_pyinstaller()

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        args.name,
    ]
    if args.clean:
        command.append("--clean")
    command.append(str(ENTRYPOINT))

    subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    print(f"Built {PROJECT_ROOT / 'dist' / args.name}")
    return 0


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is not installed. Run: uv sync --group build"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
