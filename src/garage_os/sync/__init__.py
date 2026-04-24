"""F010 sync package: garage sync (push) — context handoff to host context surface.

Implements F010 spec FR-1001..1009 + design ADR-D10-1..6.

Public API:
- ``compile_garage_section(workspace_root)``: top-N + budget compiler
- ``sync_hosts(workspace_root, hosts, scopes_per_host, force=False, ...)``: pipeline
- ``read_sync_manifest(garage_dir)`` / ``write_sync_manifest(garage_dir, manifest)``: manifest IO
- ``SyncManifest`` / ``SyncTargetEntry`` / ``SyncSources`` dataclasses
"""

from garage_os.sync.compiler import (
    EXPERIENCE_TOP_M,
    KNOWLEDGE_TOP_N,
    SIZE_BUDGET_BYTES,
    CompiledSection,
    compile_garage_section,
)
from garage_os.sync.manifest import (
    SyncManifest,
    SyncManifestMigrationError,
    SyncSources,
    SyncTargetEntry,
    read_sync_manifest,
    write_sync_manifest,
)
from garage_os.sync.pipeline import SyncSummary, SyncWriteAction, sync_hosts

__all__ = [
    "CompiledSection",
    "EXPERIENCE_TOP_M",
    "KNOWLEDGE_TOP_N",
    "SIZE_BUDGET_BYTES",
    "SyncManifest",
    "SyncManifestMigrationError",
    "SyncSources",
    "SyncSummary",
    "SyncTargetEntry",
    "SyncWriteAction",
    "compile_garage_section",
    "read_sync_manifest",
    "sync_hosts",
    "write_sync_manifest",
]
