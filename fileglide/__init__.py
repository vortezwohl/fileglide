"""Top-level package for the fileglide CLI."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fileglide")
except PackageNotFoundError:
    __version__ = "0.1.0"
