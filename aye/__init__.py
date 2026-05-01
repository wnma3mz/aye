"""Aye package."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("aye-cli")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
