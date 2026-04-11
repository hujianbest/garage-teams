"""File-backed surface routing and materialization helpers."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from core.records import (
    ArtifactDescriptor,
    AuthorityMarker,
    EvidenceRecord,
    LineageLink,
    LineageLinkType,
    ObjectRef,
    SessionState,
    SessionStatus,
)
from foundation import WorkspaceBinding


class SurfaceKind(StrEnum):
    ARTIFACTS = "artifacts"
    EVIDENCE = "evidence"
    SESSIONS = "sessions"
    ARCHIVES = "archives"
    GARAGE = ".garage"


@dataclass(slots=True, frozen=True)
class ArtifactRoute:
    surface: SurfaceKind
    file_path: Path
    sidecar_path: Path


def _format_extension(primary_format: str) -> str:
    if primary_format == "markdown":
        return ".md"
    if primary_format == "json":
        return ".json"
    return ".txt"


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return value


def _object_ref_to_mapping(ref: ObjectRef) -> dict[str, str]:
    return {"kind": ref.kind, "objectId": ref.object_id}


def _object_ref_from_mapping(raw: Mapping[str, Any]) -> ObjectRef:
    kind = raw.get("kind")
    object_id = raw.get("objectId")
    if not isinstance(kind, str) or not isinstance(object_id, str):
        raise ValueError("Expected object reference payload to contain string kind and objectId fields.")
    return ObjectRef(kind=kind, object_id=object_id)


def _session_state_to_mapping(state: SessionState) -> dict[str, Any]:
    return {
        "sessionId": state.session_id,
        "intentRef": _object_ref_to_mapping(state.intent_ref),
        "contextPointerRef": _object_ref_to_mapping(state.context_pointer_ref),
        "sessionStatus": state.session_status.value,
        "currentPack": state.current_pack,
        "currentNode": state.current_node,
        "summary": state.summary,
        "pendingGateRefs": [_object_ref_to_mapping(ref) for ref in state.pending_gate_refs],
    }


def _session_state_from_mapping(raw: Mapping[str, Any]) -> SessionState:
    session_id = raw.get("sessionId")
    session_status = raw.get("sessionStatus")
    current_pack = raw.get("currentPack")
    current_node = raw.get("currentNode")
    summary = raw.get("summary")
    pending_gate_refs = raw.get("pendingGateRefs", [])
    if not isinstance(session_id, str):
        raise ValueError("Session payload must include string field 'sessionId'.")
    if not isinstance(session_status, str):
        raise ValueError("Session payload must include string field 'sessionStatus'.")
    if not isinstance(current_pack, str):
        raise ValueError("Session payload must include string field 'currentPack'.")
    if not isinstance(current_node, str):
        raise ValueError("Session payload must include string field 'currentNode'.")
    if not isinstance(summary, str):
        raise ValueError("Session payload must include string field 'summary'.")
    if not isinstance(pending_gate_refs, list):
        raise ValueError("Session payload field 'pendingGateRefs' must be a list.")
    return SessionState(
        session_id=session_id,
        intent_ref=_object_ref_from_mapping(_require_mapping(raw, "intentRef")),
        context_pointer_ref=_object_ref_from_mapping(_require_mapping(raw, "contextPointerRef")),
        session_status=SessionStatus(session_status),
        current_pack=current_pack,
        current_node=current_node,
        summary=summary,
        pending_gate_refs=tuple(_object_ref_from_mapping(_ensure_mapping(item)) for item in pending_gate_refs),
    )


def _require_mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    return _ensure_mapping(value)


def _ensure_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("Expected mapping payload.")
    return value


def materialize_markdown(
    route: ArtifactRoute,
    *,
    title: str,
    body: str,
    sidecar_payload: Mapping[str, Any],
) -> None:
    route.file_path.parent.mkdir(parents=True, exist_ok=True)
    route.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    route.file_path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    route.sidecar_path.write_text(
        json.dumps(dict(sidecar_payload), indent=2, ensure_ascii=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


class FileBackedSurfaceManager:
    """Resolve and materialize canonical workspace surfaces."""

    def __init__(self, workspace: WorkspaceBinding) -> None:
        self.workspace = workspace

    def resolve_artifact_route(self, descriptor: ArtifactDescriptor) -> ArtifactRoute:
        extension = _format_extension(descriptor.primary_format)
        file_path = (
            self.workspace.artifacts_root
            / descriptor.pack_id
            / descriptor.artifact_role
            / f"{descriptor.artifact_id}{extension}"
        )
        sidecar_path = (
            self.workspace.garage_root
            / "sidecars"
            / SurfaceKind.ARTIFACTS.value
            / descriptor.pack_id
            / descriptor.artifact_role
            / f"{descriptor.artifact_id}.json"
        )
        return ArtifactRoute(
            surface=SurfaceKind.ARTIFACTS,
            file_path=file_path,
            sidecar_path=sidecar_path,
        )

    def resolve_evidence_route(self, *, pack_id: str, record: EvidenceRecord) -> ArtifactRoute:
        file_path = (
            self.workspace.evidence_root
            / pack_id
            / record.evidence_type
            / f"{record.evidence_id}.md"
        )
        sidecar_path = (
            self.workspace.garage_root
            / "sidecars"
            / SurfaceKind.EVIDENCE.value
            / pack_id
            / record.evidence_type
            / f"{record.evidence_id}.json"
        )
        return ArtifactRoute(
            surface=SurfaceKind.EVIDENCE,
            file_path=file_path,
            sidecar_path=sidecar_path,
        )

    def resolve_session_route(self, *, session_id: str) -> ArtifactRoute:
        file_path = self.workspace.sessions_root / f"{session_id}.json"
        sidecar_path = self.workspace.garage_root / "sidecars" / SurfaceKind.SESSIONS.value / f"{session_id}.json"
        return ArtifactRoute(
            surface=SurfaceKind.SESSIONS,
            file_path=file_path,
            sidecar_path=sidecar_path,
        )

    def write_session_state(self, state: SessionState) -> ArtifactRoute:
        route = self.resolve_session_route(session_id=state.session_id)
        route.file_path.parent.mkdir(parents=True, exist_ok=True)
        route.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        route.file_path.write_text(
            json.dumps(_session_state_to_mapping(state), indent=2, ensure_ascii=True, default=_json_default) + "\n",
            encoding="utf-8",
        )
        route.sidecar_path.write_text(
            json.dumps(
                {
                    "sessionId": state.session_id,
                    "workspaceId": self.workspace.workspace_id,
                    "surface": SurfaceKind.SESSIONS.value,
                },
                indent=2,
                ensure_ascii=True,
                default=_json_default,
            )
            + "\n",
            encoding="utf-8",
        )
        return route

    def read_session_state(self, session_id: str) -> SessionState:
        route = self.resolve_session_route(session_id=session_id)
        payload = json.loads(route.file_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Expected top-level session payload to be a JSON object.")
        return _session_state_from_mapping(payload)

    def write_artifact(
        self,
        descriptor: ArtifactDescriptor,
        *,
        body: str,
        authority: AuthorityMarker,
    ) -> ArtifactRoute:
        route = self.resolve_artifact_route(descriptor)
        materialize_markdown(
            route,
            title=f"{descriptor.artifact_role}: {descriptor.artifact_id}",
            body=body,
            sidecar_payload={
                "descriptor": asdict(descriptor),
                "authority": asdict(authority),
            },
        )
        return route

    def emit_evidence(
        self,
        *,
        pack_id: str,
        record: EvidenceRecord,
        summary: str,
    ) -> ArtifactRoute:
        route = self.resolve_evidence_route(pack_id=pack_id, record=record)
        materialize_markdown(
            route,
            title=f"{record.evidence_type}: {record.evidence_id}",
            body=summary,
            sidecar_payload={"record": asdict(record)},
        )
        return route

    def archive_route(
        self,
        *,
        original_surface: SurfaceKind,
        pack_id: str,
        object_role: str,
        object_id: str,
        extension: str,
    ) -> ArtifactRoute:
        file_path = (
            self.workspace.archives_root
            / original_surface.value
            / pack_id
            / object_role
            / f"{object_id}{extension}"
        )
        sidecar_path = (
            self.workspace.garage_root
            / "sidecars"
            / SurfaceKind.ARCHIVES.value
            / original_surface.value
            / pack_id
            / object_role
            / f"{object_id}.json"
        )
        return ArtifactRoute(
            surface=SurfaceKind.ARCHIVES,
            file_path=file_path,
            sidecar_path=sidecar_path,
        )

    def archive_artifact(
        self,
        *,
        descriptor: ArtifactDescriptor,
        authority: AuthorityMarker,
        route: ArtifactRoute,
    ) -> ArtifactRoute:
        archive_route = self.archive_route(
            original_surface=SurfaceKind.ARTIFACTS,
            pack_id=descriptor.pack_id,
            object_role=descriptor.artifact_role,
            object_id=descriptor.artifact_id,
            extension=route.file_path.suffix,
        )
        archive_route.file_path.parent.mkdir(parents=True, exist_ok=True)
        archive_route.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(route.file_path, archive_route.file_path)
        shutil.copy2(route.sidecar_path, archive_route.sidecar_path)
        archive_route.sidecar_path.write_text(
            json.dumps(
                {
                    "descriptor": asdict(descriptor),
                    "authority": asdict(authority),
                    "archivedFrom": str(route.file_path),
                },
                indent=2,
                ensure_ascii=True,
                default=_json_default,
            )
            + "\n",
            encoding="utf-8",
        )
        return archive_route

    def supersede_artifact(
        self,
        *,
        current_authority: AuthorityMarker,
        superseding_descriptor: ArtifactDescriptor,
        link_id: str,
    ) -> tuple[AuthorityMarker, AuthorityMarker, LineageLink]:
        old_authority = AuthorityMarker(
            artifact_ref=current_authority.artifact_ref,
            is_authoritative=False,
            superseded_by=ObjectRef(kind="artifact", object_id=superseding_descriptor.artifact_id),
            archived=current_authority.archived,
        )
        new_authority = AuthorityMarker(
            artifact_ref=ObjectRef(kind="artifact", object_id=superseding_descriptor.artifact_id),
            is_authoritative=True,
            superseded_by=None,
            archived=False,
        )
        lineage = LineageLink(
            link_id=link_id,
            link_type=LineageLinkType.SUPERSEDES,
            source_ref=current_authority.artifact_ref,
            target_ref=new_authority.artifact_ref,
            rationale="The newer artifact version supersedes the previous authoritative slot.",
        )
        return old_authority, new_authority, lineage
