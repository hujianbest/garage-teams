"""Runtime diagnostics and minimal structured ops events (T200)."""

from __future__ import annotations

import time
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, cast

from foundation import RuntimeTopology, TopologyBindingError

from .install_layout import package_version
from .profile_loader import RuntimeProfileResolutionError, load_runtime_profile
from .runtime_home_doctor import DoctorSeverity, diagnose_runtime_home, findings_as_jsonable

_OPS_BUFFER: list[dict[str, Any]] = []
_OPS_BUFFER_LIMIT = 200


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


def ops_emit(event_type: str, payload: Mapping[str, Any] | None = None) -> None:
    """Append a structured ops event (in-process ring buffer for tests and local tooling)."""

    event: dict[str, Any] = {
        "ts": time.time(),
        "event": event_type,
    }
    if payload:
        event.update(dict(payload))
    _OPS_BUFFER.append(event)
    if len(_OPS_BUFFER) > _OPS_BUFFER_LIMIT:
        del _OPS_BUFFER[: len(_OPS_BUFFER) - _OPS_BUFFER_LIMIT]


def recent_ops_events(*, clear: bool = False) -> tuple[dict[str, Any], ...]:
    """Return recent events; optionally clear the buffer (for tests)."""

    out = tuple(_OPS_BUFFER)
    if clear:
        _OPS_BUFFER.clear()
    return out


def compute_install_diagnostics(
    *,
    source_root: Path | str,
    runtime_home: Path | str,
    workspace_root: Path | str,
    workspace_id: str | None,
    profile_id: str,
    entry_surface: str,
    host_adapter_id: str | None = None,
) -> dict[str, Any]:
    """
    Pre-session diagnostics: topology, doctor, and safe profile summary (no secret values).
    """

    src = Path(source_root).resolve()
    rh = Path(runtime_home).resolve()
    ws = Path(workspace_root).resolve()
    wid = workspace_id or ws.name

    base: dict[str, Any] = {
        "garageVersion": package_version(),
        "health": HealthStatus.BLOCKED.value,
        "workspaceId": wid,
        "profileId": profile_id,
        "entrySurface": entry_surface,
        "hostAdapterId": host_adapter_id or entry_surface,
        "sourceRoot": str(src),
        "runtimeHome": str(rh),
        "workspaceRoot": str(ws),
        "doctorOk": False,
        "doctorFindings": (),
        "topologyError": None,
        "profileError": None,
        "credentialSlots": (),
        "providerId": None,
        "modelId": None,
        "adapterId": None,
    }

    try:
        topology = RuntimeTopology.external_workspace(
            source_root=src,
            runtime_home=rh,
            workspace_root=ws,
            workspace_id=wid,
        )
    except TopologyBindingError as exc:
        base["topologyError"] = str(exc)
        base["doctorFindings"] = ()
        return base

    findings, doctor_ok = diagnose_runtime_home(topology.runtime_home, profile_id=profile_id)
    base["doctorOk"] = doctor_ok
    base["doctorFindings"] = findings_as_jsonable(findings)

    try:
        profile = load_runtime_profile(
            topology.runtime_home,
            profile_id=profile_id,
        )
    except RuntimeProfileResolutionError as exc:
        base["profileError"] = str(exc)
        base["health"] = HealthStatus.BLOCKED.value
        return base

    base["credentialSlots"] = tuple(sorted(profile.credential_refs.keys()))
    base["providerId"] = profile.provider_id
    base["modelId"] = profile.model_id
    base["adapterId"] = profile.adapter_id

    if not doctor_ok or any(f.get("severity") == DoctorSeverity.ERROR.value for f in base["doctorFindings"]):
        base["health"] = HealthStatus.BLOCKED.value
    elif any(f.get("severity") == DoctorSeverity.WARNING.value for f in base["doctorFindings"]):
        base["health"] = HealthStatus.DEGRADED.value
    else:
        base["health"] = HealthStatus.HEALTHY.value

    return base


def launch_summary_diagnostics(result: object) -> dict[str, Any]:
    """Post-launch operator snapshot (references SessionApi / LaunchResult)."""

    lr = cast(Any, result)
    services = lr.services
    profile = services.profile
    topo = services.topology
    return {
        "garageVersion": package_version(),
        "health": HealthStatus.HEALTHY.value,
        "sessionId": lr.session_state.session_id,
        "sessionStatus": lr.session_state.session_status.value,
        "workspaceId": topo.workspace.workspace_id,
        "workspaceMode": topo.workspace.mode.value,
        "profileId": profile.profile_id,
        "providerId": profile.provider_id,
        "modelId": profile.model_id,
        "adapterId": profile.adapter_id,
        "hostAdapterId": services.host.adapter_id,
        "entrySurface": lr.config.entry_surface,
        "credentialSlots": tuple(sorted(profile.credential_refs.keys())),
        "launcherId": lr.launcher_id,
    }
