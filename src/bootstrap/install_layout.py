"""Install-time layout defaults: runtime home location and package version (T190)."""

from __future__ import annotations

import os
import sys
from importlib import metadata
from pathlib import Path

RUNTIME_HOME_SCHEMA_VERSION = "1"
"""Documented alongside config/runtime-home-version; bump only with migration notes."""

_PACKAGE_NAME = "garage-runtime"


def package_version() -> str:
    """Installed wheel / sdist version; development trees fall back to a dev label."""

    try:
        return metadata.version(_PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "0.0.0.dev0"


def default_runtime_home_path() -> Path:
    """
    Default user-local runtime home when no CLI flag or GARAGE_RUNTIME_HOME is set.

    Layout stays out of workspace surfaces and follows common OS conventions.
    """

    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        base = Path(local) if local else Path.home() / "AppData" / "Local"
        return (base / "Garage" / "runtime-home").resolve()
    xdg_state = os.environ.get("XDG_STATE_HOME", "").strip()
    root = Path(xdg_state) if xdg_state else Path.home() / ".local" / "state"
    return (root / "garage" / "runtime-home").resolve()


def resolve_runtime_home(explicit: Path | None) -> Path:
    """CLI / entry helper: explicit path wins, then GARAGE_RUNTIME_HOME, then default."""

    if explicit is not None:
        return explicit.expanduser().resolve()
    env = os.environ.get("GARAGE_RUNTIME_HOME", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return default_runtime_home_path()


def resolve_workspace_root(explicit: Path | None) -> Path:
    """Default workspace root is the current working directory."""

    if explicit is not None:
        return explicit.expanduser().resolve()
    return Path.cwd().resolve()


def resolve_source_root(explicit: Path | None) -> Path:
    """Source root defaults to cwd; override with GARAGE_SOURCE_ROOT for fixed installs."""

    if explicit is not None:
        return explicit.expanduser().resolve()
    env = os.environ.get("GARAGE_SOURCE_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()
