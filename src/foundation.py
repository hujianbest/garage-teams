"""Foundational runtime bindings reserved by the T010 skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(slots=True, frozen=True)
class RuntimeProfile:
    """Stable bootstrap input that selects how Garage should start."""

    profile_id: str
    runtime_home: Path | None = None
    capabilities: tuple[str, ...] = ()
    provider_hints: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class WorkspaceBinding:
    """Workspace-first binding for the current Garage session."""

    workspace_id: str
    root: Path
    artifacts_root: Path
    evidence_root: Path
    sessions_root: Path
    archives_root: Path
    garage_root: Path

    @classmethod
    def from_root(cls, workspace_id: str, root: Path) -> "WorkspaceBinding":
        root = root.resolve()
        return cls(
            workspace_id=workspace_id,
            root=root,
            artifacts_root=root / "artifacts",
            evidence_root=root / "evidence",
            sessions_root=root / "sessions",
            archives_root=root / "archives",
            garage_root=root / ".garage",
        )


@dataclass(slots=True, frozen=True)
class HostAdapterBinding:
    """Minimal host binding reserved for future CLI/IDE/chat adapters."""

    adapter_id: str
    host_kind: str
    capabilities: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
