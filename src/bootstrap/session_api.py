"""Entry-facing session API that keeps create/resume/attach on one seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from execution import ExecutionContext, ExecutionOutcome, ExecutionRequest, ExecutionRuntimeError

from .launcher import BootstrapConfig, GarageLauncher, LaunchMode, LaunchResult


@dataclass(slots=True, frozen=True)
class SessionLaunchSummary:
    """Stable launch summary for CLI and future entry surfaces."""

    launcher_id: str
    session_id: str
    session_status: str
    workspace_id: str
    workspace_mode: str
    profile_id: str
    host_adapter_id: str
    session_file: str

    def as_mapping(self) -> dict[str, str]:
        return {
            "launcherId": self.launcher_id,
            "sessionId": self.session_id,
            "sessionStatus": self.session_status,
            "workspaceId": self.workspace_id,
            "workspaceMode": self.workspace_mode,
            "profileId": self.profile_id,
            "hostAdapterId": self.host_adapter_id,
            "sessionFile": self.session_file,
        }


class SessionApi:
    """Single entry-facing API for session lifecycle and step submission."""

    def __init__(self, launcher: GarageLauncher | None = None) -> None:
        self._launcher = launcher or GarageLauncher()

    def launch(
        self,
        config: BootstrapConfig,
        *,
        existing_state=None,
    ) -> LaunchResult:
        return self._launcher.launch(config, existing_state=existing_state)

    def create(
        self,
        config: BootstrapConfig,
        *,
        existing_state=None,
    ) -> LaunchResult:
        self._require_mode(config, LaunchMode.CREATE)
        return self.launch(config, existing_state=existing_state)

    def resume(
        self,
        config: BootstrapConfig,
        *,
        existing_state=None,
    ) -> LaunchResult:
        self._require_mode(config, LaunchMode.RESUME)
        return self.launch(config, existing_state=existing_state)

    def attach(
        self,
        config: BootstrapConfig,
        *,
        existing_state=None,
    ) -> LaunchResult:
        self._require_mode(config, LaunchMode.ATTACH)
        return self.launch(config, existing_state=existing_state)

    def summarize(self, result: LaunchResult) -> SessionLaunchSummary:
        return SessionLaunchSummary(
            launcher_id=result.launcher_id,
            session_id=result.session_state.session_id,
            session_status=result.session_state.session_status.value,
            workspace_id=result.services.topology.workspace.workspace_id,
            workspace_mode=result.services.topology.workspace.mode.value,
            profile_id=result.services.profile.profile_id,
            host_adapter_id=result.services.host.adapter_id,
            session_file=str(result.session_route.file_path),
        )

    def submit_step(
        self,
        result: LaunchResult,
        *,
        role_id: str,
        provider_id: str,
        prompt: str,
        requested_tool_capabilities: tuple[str, ...] = (),
        action_name: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> ExecutionOutcome:
        if not prompt.strip():
            raise ExecutionRuntimeError("submit_step requires a non-empty prompt.")

        request_id = f"exec.{result.session_state.session_id}.{uuid4().hex[:8]}"
        request = ExecutionRequest(
            request_id=request_id,
            pack_id=result.session_state.current_pack,
            node_id=result.session_state.current_node,
            role_id=role_id,
            provider_id=provider_id,
            prompt=prompt,
            requested_tool_capabilities=requested_tool_capabilities,
            action_name=action_name,
            metadata=dict(metadata or {}),
        )
        context = ExecutionContext(
            workspace_id=result.services.topology.workspace.workspace_id,
            session_id=result.session_state.session_id,
            pack_id=result.session_state.current_pack,
            node_id=result.session_state.current_node,
            role_id=role_id,
            allowed_tool_capabilities=requested_tool_capabilities,
            host_adapter_id=result.services.host.adapter_id,
        )
        return result.services.execution_runtime.execute(request, context)

    @staticmethod
    def _require_mode(config: BootstrapConfig, expected: LaunchMode) -> None:
        if config.launch_mode != expected:
            raise ValueError(
                f"SessionApi expected launch mode {expected.value!r}, got {config.launch_mode.value!r}."
            )
