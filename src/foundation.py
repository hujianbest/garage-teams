"""Foundational runtime bindings reserved by the T010/T110 slices."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Mapping


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


class WorkspaceMode(StrEnum):
    SOURCE_COUPLED = "source-coupled"
    EXTERNAL = "external-workspace"


class TopologyBindingError(ValueError):
    """Raised when source root, runtime home, and workspace bindings conflict."""


@dataclass(slots=True, frozen=True)
class SourceRootBinding:
    """Binding for the Garage source root and its authoring surfaces."""

    root: Path
    docs_root: Path
    packs_root: Path
    agent_skills_root: Path
    src_root: Path
    tests_root: Path

    @classmethod
    def from_root(cls, root: Path) -> "SourceRootBinding":
        root = root.resolve()
        return cls(
            root=root,
            docs_root=root / "docs",
            packs_root=root / "packs",
            agent_skills_root=root / ".agents" / "skills",
            src_root=root / "src",
            tests_root=root / "tests",
        )


@dataclass(slots=True, frozen=True)
class RuntimeHomeBinding:
    """Binding for install-scoped runtime state, profiles, and caches."""

    root: Path
    profiles_root: Path
    config_root: Path
    cache_root: Path
    adapters_root: Path

    @classmethod
    def from_root(cls, root: Path) -> "RuntimeHomeBinding":
        root = root.resolve()
        return cls(
            root=root,
            profiles_root=root / "profiles",
            config_root=root / "config",
            cache_root=root / "cache",
            adapters_root=root / "adapters",
        )


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
    mode: WorkspaceMode = WorkspaceMode.EXTERNAL

    @classmethod
    def from_root(
        cls,
        workspace_id: str,
        root: Path,
        *,
        mode: WorkspaceMode = WorkspaceMode.EXTERNAL,
    ) -> "WorkspaceBinding":
        root = root.resolve()
        return cls(
            workspace_id=workspace_id,
            root=root,
            artifacts_root=root / "artifacts",
            evidence_root=root / "evidence",
            sessions_root=root / "sessions",
            archives_root=root / "archives",
            garage_root=root / ".garage",
            mode=mode,
        )

    def workspace_fact_roots(self) -> tuple[Path, ...]:
        return (
            self.artifacts_root,
            self.evidence_root,
            self.sessions_root,
            self.archives_root,
            self.garage_root,
        )

    def owns_path(self, path: Path) -> bool:
        return _is_relative_to(path, self.root)


@dataclass(slots=True, frozen=True)
class HostAdapterBinding:
    """Minimal host binding reserved for future CLI/IDE/chat adapters."""

    adapter_id: str
    host_kind: str
    capabilities: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class RuntimeTopology:
    """Resolved source root, runtime home, and workspace layering."""

    source_root: SourceRootBinding
    runtime_home: RuntimeHomeBinding
    workspace: WorkspaceBinding

    @classmethod
    def source_coupled(
        cls,
        *,
        source_root: Path,
        runtime_home: Path,
        workspace_id: str,
    ) -> "RuntimeTopology":
        resolved_source_root = SourceRootBinding.from_root(source_root)
        return cls(
            source_root=resolved_source_root,
            runtime_home=RuntimeHomeBinding.from_root(runtime_home),
            workspace=WorkspaceBinding.from_root(
                workspace_id,
                resolved_source_root.root,
                mode=WorkspaceMode.SOURCE_COUPLED,
            ),
        ).validated()

    @classmethod
    def external_workspace(
        cls,
        *,
        source_root: Path,
        runtime_home: Path,
        workspace_root: Path,
        workspace_id: str,
    ) -> "RuntimeTopology":
        return cls(
            source_root=SourceRootBinding.from_root(source_root),
            runtime_home=RuntimeHomeBinding.from_root(runtime_home),
            workspace=WorkspaceBinding.from_root(
                workspace_id,
                workspace_root,
                mode=WorkspaceMode.EXTERNAL,
            ),
        ).validated()

    def validated(self) -> "RuntimeTopology":
        if self.workspace.mode == WorkspaceMode.SOURCE_COUPLED:
            if self.source_root.root != self.workspace.root:
                raise TopologyBindingError(
                    "source-coupled mode requires source root and workspace root to match."
                )
        elif self.source_root.root == self.workspace.root:
            raise TopologyBindingError(
                "Use source-coupled mode when source root and workspace root are the same."
            )

        if self.runtime_home.root == self.workspace.root:
            raise TopologyBindingError(
                "Runtime home must stay distinct from the workspace root."
            )

        for workspace_fact_root in self.workspace.workspace_fact_roots():
            if self.runtime_home.root == workspace_fact_root or _is_relative_to(
                self.runtime_home.root,
                workspace_fact_root,
            ):
                raise TopologyBindingError(
                    "Runtime home cannot live inside workspace fact surfaces."
                )

        return self
