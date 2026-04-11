"""Unified bootstrap chain for Garage runtime entry surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Mapping
from uuid import uuid4

from core import GateVerdict, ObjectRef, SessionIntent, SessionState, SessionStatus
from execution import ExecutionRuntime
from foundation import (
    HostAdapterBinding,
    RuntimeProfile,
    RuntimeTopology,
    TopologyBindingError,
)
from governance import GateType, GovernanceRule, GovernanceRuntime, RuntimeContext
from registry import RegistryIndex, build_registry
from session import BlockedGateError, SessionAction, SessionController
from surfaces import ArtifactRoute, FileBackedSurfaceManager

from .credential_resolution import CredentialResolutionError, ResolvedCredentials, resolve_credential_refs
from .profile_loader import load_runtime_profile
from .runtime_ops import ops_emit


def _host_binding(
    adapter_id: str,
    *,
    host_kind: str,
    capabilities: tuple[str, ...],
    metadata: Mapping[str, str] | None = None,
) -> HostAdapterBinding:
    return HostAdapterBinding(
        adapter_id=adapter_id,
        host_kind=host_kind,
        capabilities=capabilities,
        metadata=dict(metadata or {}),
    )


DEFAULT_HOST_CATALOG: dict[str, HostAdapterBinding] = {
    "cli": _host_binding(
        "cli",
        host_kind="cli",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step"),
    ),
    "web": _host_binding(
        "web",
        host_kind="web",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step", "stream-session"),
    ),
    "host-bridge": _host_binding(
        "host-bridge",
        host_kind="host-bridge",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step", "request-approval"),
    ),
    "cursor": _host_binding(
        "cursor",
        host_kind="host-bridge",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step", "open-file"),
        metadata={"bridgeFamily": "cursor"},
    ),
    "claude": _host_binding(
        "claude",
        host_kind="host-bridge",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step", "request-approval"),
        metadata={"bridgeFamily": "claude"},
    ),
    "opencode": _host_binding(
        "opencode",
        host_kind="host-bridge",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step"),
        metadata={"bridgeFamily": "opencode"},
    ),
    "ide": _host_binding(
        "ide",
        host_kind="host-bridge",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step", "open-file"),
        metadata={"legacyAlias": "true", "bridgeFamily": "cursor"},
    ),
    "chat": _host_binding(
        "chat",
        host_kind="host-bridge",
        capabilities=("create-session", "resume-session", "attach-session", "submit-step", "request-approval"),
        metadata={"legacyAlias": "true", "bridgeFamily": "chat"},
    ),
}


class LaunchMode(StrEnum):
    CREATE = "create"
    RESUME = "resume"
    ATTACH = "attach"


class BootstrapError(RuntimeError):
    """Raised when bootstrap inputs are incomplete or contradictory."""


@dataclass(slots=True, frozen=True)
class BootstrapConfig:
    launch_mode: LaunchMode
    source_root: Path
    runtime_home: Path
    workspace_root: Path | None = None
    workspace_id: str | None = None
    profile_id: str = "default"
    entry_surface: str = "cli"
    host_adapter_id: str | None = None
    session_id: str | None = None
    initiator: str = "creator"
    problem_kind: str | None = None
    entry_pack: str | None = None
    entry_node: str | None = None
    goal: str | None = None
    summary: str | None = None
    boundaries: tuple[str, ...] = ()
    runtime_capabilities: tuple[str, ...] = ()
    provider_hints: Mapping[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeServices:
    topology: RuntimeTopology
    profile: RuntimeProfile
    host: HostAdapterBinding
    resolved_credentials: ResolvedCredentials
    registry: RegistryIndex
    governance: GovernanceRuntime
    surfaces: FileBackedSurfaceManager
    session_controller: SessionController
    execution_runtime: ExecutionRuntime


@dataclass(slots=True)
class LaunchResult:
    launcher_id: str
    config: BootstrapConfig
    services: RuntimeServices
    session_state: SessionState
    session_route: ArtifactRoute


class GarageLauncher:
    """Resolve topology, bind the host, and enter the shared runtime chain."""

    def __init__(
        self,
        *,
        host_catalog: Mapping[str, HostAdapterBinding] | None = None,
        rules: tuple[GovernanceRule, ...] = (),
    ) -> None:
        self._host_catalog = dict(host_catalog or DEFAULT_HOST_CATALOG)
        self._rules = rules

    def launch(
        self,
        config: BootstrapConfig,
        *,
        existing_state: SessionState | None = None,
    ) -> LaunchResult:
        ops_emit(
            "garage.launch.start",
            {
                "launchMode": config.launch_mode.value,
                "profileId": config.profile_id,
                "entrySurface": config.entry_surface,
            },
        )
        topology = self._resolve_topology(config)
        profile = load_runtime_profile(
            topology.runtime_home,
            profile_id=config.profile_id,
            runtime_capabilities=config.runtime_capabilities,
            provider_hints=config.provider_hints,
        )
        try:
            resolved_credentials = resolve_credential_refs(profile.credential_refs, topology.runtime_home)
        except CredentialResolutionError as exc:
            raise BootstrapError(str(exc)) from exc
        host = self._resolve_host_binding(config)
        services = self._build_runtime_services(topology, profile, host, resolved_credentials)
        session_state = self._enter_runtime(config, services, existing_state)
        session_route = services.surfaces.write_session_state(session_state)
        launcher_id = f"launcher.{config.profile_id}.{session_state.session_id}"
        ops_emit(
            "garage.launch.complete",
            {
                "launcherId": launcher_id,
                "sessionId": session_state.session_id,
                "sessionStatus": session_state.session_status.value,
            },
        )
        return LaunchResult(
            launcher_id=launcher_id,
            config=config,
            services=services,
            session_state=session_state,
            session_route=session_route,
        )

    def _resolve_topology(self, config: BootstrapConfig) -> RuntimeTopology:
        if config.workspace_root is None:
            raise BootstrapError("Bootstrap requires a workspace root before entering the runtime.")
        workspace_root = config.workspace_root.resolve()
        workspace_id = config.workspace_id or workspace_root.name
        try:
            if config.source_root.resolve() == workspace_root:
                return RuntimeTopology.source_coupled(
                    source_root=config.source_root,
                    runtime_home=config.runtime_home,
                    workspace_id=workspace_id,
                )
            return RuntimeTopology.external_workspace(
                source_root=config.source_root,
                runtime_home=config.runtime_home,
                workspace_root=workspace_root,
                workspace_id=workspace_id,
            )
        except TopologyBindingError as exc:
            raise BootstrapError(str(exc)) from exc

    def _resolve_host_binding(self, config: BootstrapConfig) -> HostAdapterBinding:
        host_key = config.host_adapter_id or config.entry_surface
        try:
            return self._host_catalog[host_key]
        except KeyError as exc:
            raise BootstrapError(f"Unknown host adapter binding {host_key!r}.") from exc

    def _build_runtime_services(
        self,
        topology: RuntimeTopology,
        profile: RuntimeProfile,
        host: HostAdapterBinding,
        resolved_credentials: ResolvedCredentials,
    ) -> RuntimeServices:
        packs_root = topology.source_root.packs_root
        pack_roots = tuple(path for path in sorted(packs_root.iterdir()) if path.is_dir()) if packs_root.exists() else ()
        registry = build_registry(pack_roots)
        governance = GovernanceRuntime(rules=self._rules)
        surfaces = FileBackedSurfaceManager(topology.workspace)
        session_controller = SessionController(governance)
        execution_runtime = ExecutionRuntime(governance=governance, surfaces=surfaces)
        return RuntimeServices(
            topology=topology,
            profile=profile,
            host=host,
            resolved_credentials=resolved_credentials,
            registry=registry,
            governance=governance,
            surfaces=surfaces,
            session_controller=session_controller,
            execution_runtime=execution_runtime,
        )

    def _enter_runtime(
        self,
        config: BootstrapConfig,
        services: RuntimeServices,
        existing_state: SessionState | None,
    ) -> SessionState:
        if config.launch_mode == LaunchMode.CREATE:
            return self._create_session(config, services)
        if config.launch_mode == LaunchMode.RESUME:
            return self._resume_session(config, services, existing_state)
        if config.launch_mode == LaunchMode.ATTACH:
            return self._attach_session(config, services, existing_state)
        raise BootstrapError(f"Unsupported launch mode {config.launch_mode!r}.")

    def _create_session(self, config: BootstrapConfig, services: RuntimeServices) -> SessionState:
        if config.entry_pack is None or config.entry_node is None or config.goal is None or config.problem_kind is None:
            raise BootstrapError("Create mode requires problem_kind, entry_pack, entry_node, and goal.")

        session_id = config.session_id or f"session.{uuid4().hex[:8]}"
        intent = SessionIntent(
            intent_id=f"intent.{session_id}",
            initiator=config.initiator,
            problem_kind=config.problem_kind,
            entry_pack=config.entry_pack,
            entry_node=config.entry_node,
            goal=config.goal,
            boundaries=config.boundaries,
        )
        draft_state = SessionState(
            session_id=session_id,
            intent_ref=ObjectRef(kind="session-intent", object_id=intent.intent_id),
            context_pointer_ref=ObjectRef(kind="context-pointer", object_id=f"context.{session_id}"),
            session_status=SessionStatus.DRAFT,
            current_pack=config.entry_pack,
            current_node=config.entry_node,
            summary=config.summary or config.goal,
        )
        context = RuntimeContext(
            workspace_id=services.topology.workspace.workspace_id,
            session_id=session_id,
            pack_id=draft_state.current_pack,
            node_id=draft_state.current_node,
            action=SessionAction.CREATE,
        )
        self._ensure_entry_allowed(context, services.governance)
        outcome = services.session_controller.transition(
            draft_state,
            action=SessionAction.CREATE,
            context=context,
        )
        return outcome.next_state

    def _resume_session(
        self,
        config: BootstrapConfig,
        services: RuntimeServices,
        existing_state: SessionState | None,
    ) -> SessionState:
        state = self._load_existing_state(config, services, existing_state)
        context = RuntimeContext(
            workspace_id=services.topology.workspace.workspace_id,
            session_id=state.session_id,
            pack_id=state.current_pack,
            node_id=state.current_node,
            action=SessionAction.RESUME,
        )
        self._ensure_entry_allowed(context, services.governance)
        if state.session_status == SessionStatus.ACTIVE:
            return state
        outcome = services.session_controller.transition(
            state,
            action=SessionAction.RESUME,
            context=context,
        )
        return outcome.next_state

    def _attach_session(
        self,
        config: BootstrapConfig,
        services: RuntimeServices,
        existing_state: SessionState | None,
    ) -> SessionState:
        state = self._load_existing_state(config, services, existing_state)
        if state.session_status == SessionStatus.ACTIVE:
            self._ensure_entry_allowed(
                RuntimeContext(
                    workspace_id=services.topology.workspace.workspace_id,
                    session_id=state.session_id,
                    pack_id=state.current_pack,
                    node_id=state.current_node,
                    action=SessionAction.RESUME,
                ),
                services.governance,
            )
            return state
        return self._resume_session(config, services, state)

    def _load_existing_state(
        self,
        config: BootstrapConfig,
        services: RuntimeServices,
        existing_state: SessionState | None,
    ) -> SessionState:
        if existing_state is not None:
            if config.session_id is not None and existing_state.session_id != config.session_id:
                raise BootstrapError("Provided session state does not match the requested session_id.")
            return existing_state
        if config.session_id is None:
            raise BootstrapError("Resume and attach modes require an existing session_id.")
        try:
            return services.surfaces.read_session_state(config.session_id)
        except FileNotFoundError as exc:
            raise BootstrapError(f"Session {config.session_id!r} was not found in the current workspace.") from exc

    def _ensure_entry_allowed(self, context: RuntimeContext, governance: GovernanceRuntime) -> None:
        evaluation = governance.evaluate(context, GateType.ENTRY)
        if evaluation.decision.verdict != GateVerdict.ALLOW:
            raise BlockedGateError(evaluation.decision)
