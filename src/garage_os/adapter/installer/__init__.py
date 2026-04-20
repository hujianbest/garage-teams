"""Garage host installer subpackage.

Implements the F007 spec / D7 design contract for installing Garage-bundled
``packs/`` content into host-specific directories (Claude Code / OpenCode /
Cursor) of the cwd project at ``garage init`` time.

This subpackage lives under ``src/garage_os/adapter/`` to satisfy the
spec CON-701 mandate:

    "本 cycle 的 host adapter 注册表与三个 first-class adapter 实现必须放在
     ``src/garage_os/adapter/`` 下 ..."

Public symbols are re-exported here so callers (CLI, tests) only need:

    from garage_os.adapter.installer import install_packs, HostInstallAdapter, ...
"""

from __future__ import annotations

from garage_os.adapter.installer.host_registry import (
    HOST_REGISTRY,
    HostInstallAdapter,
    UnknownHostError,
    get_adapter,
    list_host_ids,
    resolve_hosts_arg,
)
from garage_os.adapter.installer.manifest import (
    MANIFEST_SCHEMA_VERSION,
    Manifest,
    ManifestFileEntry,
    read_manifest,
    write_manifest,
)
from garage_os.adapter.installer.marker import (
    MalformedFrontmatterError,
    extract_marker,
    inject,
)
from garage_os.adapter.installer.pack_discovery import (
    InvalidPackError,
    Pack,
    PackManifestMismatchError,
    discover_packs,
)
from garage_os.adapter.installer.pipeline import (
    MSG_NO_PACKS_FMT,
    WARN_LOCALLY_MODIFIED_FMT,
    WARN_OVERWRITE_FORCED_FMT,
    ConflictingSkillError,
    InstallSummary,
    install_packs,
)

__all__ = [
    # Registry
    "HOST_REGISTRY",
    "HostInstallAdapter",
    "UnknownHostError",
    "get_adapter",
    "list_host_ids",
    "resolve_hosts_arg",
    # Discovery
    "Pack",
    "InvalidPackError",
    "PackManifestMismatchError",
    "discover_packs",
    # Marker
    "MalformedFrontmatterError",
    "extract_marker",
    "inject",
    # Manifest
    "MANIFEST_SCHEMA_VERSION",
    "Manifest",
    "ManifestFileEntry",
    "read_manifest",
    "write_manifest",
    # Pipeline
    "ConflictingSkillError",
    "InstallSummary",
    "install_packs",
    # Stable markers (also re-exported by pipeline)
    "MSG_NO_PACKS_FMT",
    "WARN_LOCALLY_MODIFIED_FMT",
    "WARN_OVERWRITE_FORCED_FMT",
]
