"""Top-level package for the Trading Bot Swarm project."""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - defensive import for installed package metadata
    __version__ = version("trading-bot-swarm")
except PackageNotFoundError:  # pragma: no cover - fallback when package metadata is unavailable
    __version__ = "0.0.0"

__all__ = ["__version__"]
