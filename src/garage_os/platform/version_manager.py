"""
Version Manager for Garage Agent OS platform contracts.

Handles schema version detection, backward compatibility checks,
and migration paths for platform configuration and contract files.

Contract reference: .garage/contracts/version-manager-interface.yaml
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class CompatibilityStatus(Enum):
    """Result of a compatibility check."""

    COMPATIBLE = "compatible"
    BACKWARD_COMPATIBLE = "backward_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass
class VersionInfo:
    """Parsed semantic version representation."""

    major: int
    minor: int
    patch: int
    label: str = ""

    @classmethod
    def parse(cls, version_str: str) -> "VersionInfo":
        """Parse a version string like '1', '1.0', '1.0.0', or '0.1.0'.

        ``schema_version`` fields in contract / config files are often plain
        integers (e.g. ``1``).  This method accepts integers, short-form, and
        full semver strings.
        """
        version_str = str(version_str).strip()

        # Plain integer → treat as major version
        if version_str.isdigit():
            return cls(major=int(version_str), minor=0, patch=0)

        parts = version_str.split("-", 1)
        main = parts[0]
        label = parts[1] if len(parts) > 1 else ""

        segments = main.split(".")
        major = int(segments[0])
        minor = int(segments[1]) if len(segments) > 1 else 0
        patch = int(segments[2]) if len(segments) > 2 else 0

        return cls(major=major, minor=minor, patch=patch, label=label)

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.label:
            base += f"-{self.label}"
        return base

    def __lt__(self, other: "VersionInfo") -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )

    def __le__(self, other: "VersionInfo") -> bool:
        return self == other or self < other


@dataclass
class CompatibilityResult:
    """Outcome of a compatibility check between two versions."""

    status: CompatibilityStatus
    source_version: VersionInfo
    target_version: VersionInfo
    issues: List[str] = field(default_factory=list)
    migration_available: bool = False


class VersionError(Exception):
    """Raised when an incompatible or unsupported version is encountered."""


# ---------------------------------------------------------------------------
# Migration registry (extensible)
# ---------------------------------------------------------------------------

# Maps (from_major, to_major) → callable(data) → migrated_data
_MIGRATION_REGISTRY: Dict[Tuple[int, int], Any] = {}


def register_migration(from_major: int, to_major: int):
    """Decorator to register a migration function."""

    def decorator(func):
        _MIGRATION_REGISTRY[(from_major, to_major)] = func
        return func

    return decorator


# ---------------------------------------------------------------------------
# VersionManager
# ---------------------------------------------------------------------------

class VersionManager:
    """Detect, validate, and migrate schema versions for Garage contracts.

    The manager reads the ``schema_version`` field from JSON / YAML contract
    files and determines whether the data is compatible with the currently
    running platform version.

    Usage::

        vm = VersionManager(platform_version="0.1.0")
        version = vm.detect_version(Path(".garage/config/platform.json"))
        result = vm.check_compatibility(version, vm.platform_version_info)
    """

    # Versions that this build can natively understand (major numbers).
    # F012-E (FR-1214 + ADR-D12-6 r2): added 2 to support host-installer.json schema 2
    # (registered via @register_migration(1, 2) in manifest.py at import time)
    SUPPORTED_VERSIONS: List[int] = [1, 2]

    # The *current* schema version produced by this build.
    CURRENT_SCHEMA_VERSION: int = 1

    def __init__(
        self,
        platform_version: str = "0.1.0",
        supported_versions: Optional[List[int]] = None,
    ):
        self.platform_version = platform_version
        self.platform_version_info = VersionInfo.parse(platform_version)
        if supported_versions is not None:
            self.SUPPORTED_VERSIONS = list(supported_versions)

    # -- detection -----------------------------------------------------------

    def detect_version(self, file_path: Path) -> VersionInfo:
        """Detect the ``schema_version`` of a contract / config file.

        Supports JSON and YAML files.

        Args:
            file_path: Path to the file to inspect.

        Returns:
            Parsed ``VersionInfo`` of the file's schema version.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format cannot be determined or
                ``schema_version`` is missing.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        data: Dict[str, Any]

        if suffix == ".json":
            data = json.loads(file_path.read_text(encoding="utf-8"))
        elif suffix in (".yaml", ".yml"):
            with open(file_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                "Expected .json, .yaml, or .yml"
            )

        raw_version = data.get("schema_version")
        if raw_version is None:
            raise ValueError(
                f"Missing 'schema_version' field in {file_path}"
            )

        return VersionInfo.parse(str(raw_version))

    # -- compatibility -------------------------------------------------------

    def check_compatibility(
        self,
        file_version: VersionInfo,
        platform_version: Optional[VersionInfo] = None,
    ) -> CompatibilityResult:
        """Check whether *file_version* is compatible with the platform.

        Rules:
        1. If the file's major version is in ``SUPPORTED_VERSIONS``, it is
           ``COMPATIBLE``.
        2. If the file's major version is **older** than the minimum
           supported version, it is ``BACKWARD_COMPATIBLE`` (the platform
           can still read it with best-effort handling).
        3. If the file's major version is **newer** than any version the
           platform knows about, it is ``INCOMPATIBLE``.
        4. Otherwise ``UNKNOWN``.

        Args:
            file_version: Version detected from a contract / config file.
            platform_version: Override platform version (defaults to this
                manager's platform version).

        Returns:
            ``CompatibilityResult`` with status, issues, and migration flag.
        """
        if platform_version is None:
            platform_version = self.platform_version_info

        file_major = file_version.major
        supported = self.SUPPORTED_VERSIONS
        max_supported = max(supported)
        min_supported = min(supported)

        # Case 1 – directly supported
        if file_major in supported:
            return CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                source_version=file_version,
                target_version=platform_version,
            )

        # Case 2 – older than supported range → backward compatible
        if file_major < min_supported:
            return CompatibilityResult(
                status=CompatibilityStatus.BACKWARD_COMPATIBLE,
                source_version=file_version,
                target_version=platform_version,
                issues=[
                    f"Schema v{file_major} is older than minimum supported "
                    f"v{min_supported}. Data may load with reduced fidelity."
                ],
                migration_available=(file_major, max_supported)
                in _MIGRATION_REGISTRY,
            )

        # Case 3 – newer than anything we know → incompatible
        if file_major > max_supported:
            return CompatibilityResult(
                status=CompatibilityStatus.INCOMPATIBLE,
                source_version=file_version,
                target_version=platform_version,
                issues=[
                    f"Schema v{file_major} is newer than maximum supported "
                    f"v{max_supported}. Please upgrade Garage Agent OS."
                ],
            )

        # Case 4 – gap inside supported range (shouldn't happen normally)
        return CompatibilityResult(
            status=CompatibilityStatus.UNKNOWN,
            source_version=file_version,
            target_version=platform_version,
            issues=[
                f"Cannot determine compatibility for schema v{file_major}."
            ],
        )

    # -- migration -----------------------------------------------------------

    def migrate(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str,
    ) -> Dict[str, Any]:
        """Migrate contract data from one schema version to another.

        This is the primary extension point for future upgrade paths.
        Migration functions must be registered via ``@register_migration``.

        Args:
            data: The contract / config data to migrate.
            from_version: Source schema version string.
            to_version: Target schema version string.

        Returns:
            Migrated data dict with updated ``schema_version``.

        Raises:
            VersionError: If no migration path is registered for the
                requested versions.
        """
        from_info = VersionInfo.parse(from_version)
        to_info = VersionInfo.parse(to_version)

        if from_info == to_info:
            return dict(data)

        key = (from_info.major, to_info.major)
        migrator = _MIGRATION_REGISTRY.get(key)

        if migrator is None:
            raise VersionError(
                f"No migration path from schema v{from_info} to v{to_info}. "
                f"Registered paths: {list(_MIGRATION_REGISTRY.keys())}"
            )

        migrated = migrator(data)
        # Stamp the new version
        migrated["schema_version"] = int(to_info.major)
        return migrated

    # -- helpers -------------------------------------------------------------

    def get_supported_versions(self) -> List[str]:
        """Return all supported schema version strings."""
        return [str(v) for v in self.SUPPORTED_VERSIONS]

    def load_with_compatibility(
        self, file_path: Path
    ) -> Tuple[Dict[str, Any], CompatibilityResult]:
        """Load a file and return its data along with a compatibility report.

        If the file is incompatible a ``VersionError`` is raised.
        Backward-compatible files are loaded as-is with a warning in issues.

        Args:
            file_path: Path to the contract / config file.

        Returns:
            Tuple of (data dict, compatibility result).
        """
        version = self.detect_version(file_path)
        result = self.check_compatibility(version)

        if result.status == CompatibilityStatus.INCOMPATIBLE:
            raise VersionError(
                "; ".join(result.issues)
                if result.issues
                else f"Incompatible schema version: {version}"
            )

        suffix = file_path.suffix.lower()
        if suffix == ".json":
            data = json.loads(file_path.read_text(encoding="utf-8"))
        elif suffix in (".yaml", ".yml"):
            with open(file_path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        else:
            raise ValueError(f"Unsupported format: {suffix}")

        return data, result
