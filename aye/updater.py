from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import stat
import tarfile
import tempfile
import urllib.error
import urllib.request

from . import __version__


LATEST_RELEASE_URL = "https://api.github.com/repos/wnma3mz/aye/releases/latest"


def update_current_binary(*, current_executable: str) -> int:
    target = Path(current_executable).resolve()
    if not target.exists():
        print("Cannot find current executable. Download the latest release manually.")
        return 1

    try:
        release = _fetch_latest_release()
        tag = str(release["tag_name"])
        asset_name = _asset_name(tag)
        asset_url = _asset_url(release, asset_name)
    except (KeyError, RuntimeError, urllib.error.URLError) as exc:
        print(f"Unable to check latest release: {exc}")
        return 1

    if tag.lstrip("v") == __version__:
        print(f"aye is already up to date ({tag}).")
        return 0

    print(f"Updating aye {__version__} -> {tag}...")
    try:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / asset_name
            extract_dir = Path(directory) / "extract"
            extract_dir.mkdir()
            _download(asset_url, archive_path)
            _extract_archive(archive_path, extract_dir)
            replacement = extract_dir / "aye"
            if not replacement.exists():
                raise RuntimeError("release archive does not contain aye")
            _replace_executable(target, replacement)
    except (OSError, RuntimeError, urllib.error.URLError, tarfile.TarError) as exc:
        print(f"Unable to update aye: {exc}")
        return 1

    print(f"Updated aye to {tag}.")
    return 0


def _fetch_latest_release() -> dict:
    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "aye-updater"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _asset_name(tag: str) -> str:
    return f"aye-{tag}-{_platform_slug()}.tar.gz"


def _platform_slug() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        os_name = "darwin"
    elif system == "linux":
        os_name = "linux"
    else:
        raise RuntimeError(f"unsupported operating system: {system}")

    if machine in {"x86_64", "amd64"}:
        arch = "x64"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        raise RuntimeError(f"unsupported architecture: {machine}")

    return f"{os_name}-{arch}"


def _asset_url(release: dict, asset_name: str) -> str:
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return str(asset["browser_download_url"])
    raise RuntimeError(f"release asset not found: {asset_name}")


def _download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "aye-updater"})
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())


def _extract_archive(archive_path: Path, extract_dir: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(extract_dir, filter="data")


def _replace_executable(target: Path, replacement: Path) -> None:
    target_mode = target.stat().st_mode
    replacement.chmod(target_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    backup = target.with_name(f"{target.name}.old")
    if backup.exists():
        backup.unlink()
    target.rename(backup)
    try:
        shutil.copy2(replacement, target)
        os.chmod(target, target_mode | stat.S_IXUSR)
    except Exception:
        if target.exists():
            target.unlink()
        backup.rename(target)
        raise
    backup.unlink()
