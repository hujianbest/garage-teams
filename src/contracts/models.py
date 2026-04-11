"""Shared contract definitions for the current T030 slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, TypeAlias


REFERENCE_SCHEMA_PROFILE = "reference-slice-v1"
SUPPORTED_CONTRACT_VERSION = "v1alpha1"


class ContractParseError(ValueError):
    """Raised when a contract payload cannot be parsed."""


def _copy_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    return dict(raw)


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.pop(key, None)
    if not isinstance(value, str) or not value.strip():
        raise ContractParseError(f"Expected non-empty string field {key!r}.")
    return value


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.pop(key, None)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractParseError(f"Expected optional string field {key!r} to be a non-empty string.")
    return value


def _string_tuple(data: dict[str, Any], key: str, *, required: bool) -> tuple[str, ...]:
    value = data.pop(key, None)
    if value is None:
        if required:
            raise ContractParseError(f"Missing required sequence field {key!r}.")
        return ()
    if isinstance(value, str):
        items = (value,)
    elif isinstance(value, list):
        items = tuple(value)
    else:
        raise ContractParseError(f"Expected field {key!r} to be a string or list of strings.")
    if any(not isinstance(item, str) or not item.strip() for item in items):
        raise ContractParseError(f"Expected all values in {key!r} to be non-empty strings.")
    return items


def _string_mapping(data: dict[str, Any], key: str) -> Mapping[str, str]:
    value = data.pop(key, None)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ContractParseError(f"Expected field {key!r} to be a mapping.")
    normalized: dict[str, str] = {}
    for map_key, map_value in value.items():
        if not isinstance(map_key, str) or not isinstance(map_value, str):
            raise ContractParseError(f"Expected {key!r} to contain string keys and values.")
        normalized[map_key] = map_value
    return normalized


@dataclass(slots=True, frozen=True)
class PackManifest:
    pack_id: str
    pack_version: str
    contract_version: str
    entry_node_refs: tuple[str, ...]
    role_refs: tuple[str, ...]
    node_refs: tuple[str, ...]
    supported_artifact_roles: tuple[str, ...]
    policy_refs: tuple[str, ...] = ()
    template_refs: tuple[str, ...] = ()
    bridge_refs: tuple[str, ...] = ()
    handoff_targets: tuple[str, ...] = ()
    display_name: str | None = None
    extensions: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PackManifest":
        data = _copy_mapping(raw)
        return cls(
            pack_id=_require_str(data, "packId"),
            pack_version=_require_str(data, "packVersion"),
            contract_version=_require_str(data, "contractVersion"),
            entry_node_refs=_string_tuple(data, "entryNodeRefs", required=True),
            role_refs=_string_tuple(data, "roleRefs", required=True),
            node_refs=_string_tuple(data, "nodeRefs", required=True),
            supported_artifact_roles=_string_tuple(data, "supportedArtifactRoles", required=True),
            policy_refs=_string_tuple(data, "policyRefs", required=False),
            template_refs=_string_tuple(data, "templateRefs", required=False),
            bridge_refs=_string_tuple(data, "bridgeRefs", required=False),
            handoff_targets=_string_tuple(data, "handoffTargets", required=False),
            display_name=_optional_str(data, "displayName"),
            extensions=data,
        )


@dataclass(slots=True, frozen=True)
class RoleContract:
    role_id: str
    pack_id: str
    contract_version: str
    responsibility: str
    readable_artifact_roles: tuple[str, ...]
    writable_artifact_roles: tuple[str, ...]
    triggerable_nodes: tuple[str, ...]
    handoff_scope: tuple[str, ...]
    policy_refs: tuple[str, ...] = ()
    template_refs: tuple[str, ...] = ()
    profile_hints: Mapping[str, str] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RoleContract":
        data = _copy_mapping(raw)
        return cls(
            role_id=_require_str(data, "roleId"),
            pack_id=_require_str(data, "packId"),
            contract_version=_require_str(data, "contractVersion"),
            responsibility=_require_str(data, "responsibility"),
            readable_artifact_roles=_string_tuple(data, "readableArtifactRoles", required=True),
            writable_artifact_roles=_string_tuple(data, "writableArtifactRoles", required=True),
            triggerable_nodes=_string_tuple(data, "triggerableNodes", required=True),
            handoff_scope=_string_tuple(data, "handoffScope", required=True),
            policy_refs=_string_tuple(data, "policyRefs", required=False),
            template_refs=_string_tuple(data, "templateRefs", required=False),
            profile_hints=_string_mapping(data, "profileHints"),
            extensions=data,
        )


@dataclass(slots=True, frozen=True)
class WorkflowNodeContract:
    node_id: str
    pack_id: str
    contract_version: str
    intent: str
    input_artifact_roles: tuple[str, ...]
    output_artifact_roles: tuple[str, ...]
    allowed_transitions: tuple[str, ...]
    human_confirmation_required: bool
    parallelizable: bool
    evidence_requirements: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    handoff_hints: Mapping[str, str] = field(default_factory=dict)
    extensions: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "WorkflowNodeContract":
        data = _copy_mapping(raw)
        human_confirmation_required = data.pop("humanConfirmationRequired", None)
        parallelizable = data.pop("parallelizable", None)
        if not isinstance(human_confirmation_required, bool):
            raise ContractParseError("Expected field 'humanConfirmationRequired' to be a boolean.")
        if not isinstance(parallelizable, bool):
            raise ContractParseError("Expected field 'parallelizable' to be a boolean.")
        return cls(
            node_id=_require_str(data, "nodeId"),
            pack_id=_require_str(data, "packId"),
            contract_version=_require_str(data, "contractVersion"),
            intent=_require_str(data, "intent"),
            input_artifact_roles=_string_tuple(data, "inputArtifactRoles", required=True),
            output_artifact_roles=_string_tuple(data, "outputArtifactRoles", required=True),
            allowed_transitions=_string_tuple(data, "allowedTransitions", required=True),
            human_confirmation_required=human_confirmation_required,
            parallelizable=parallelizable,
            evidence_requirements=_string_tuple(data, "evidenceRequirements", required=False),
            policy_refs=_string_tuple(data, "policyRefs", required=False),
            handoff_hints=_string_mapping(data, "handoffHints"),
            extensions=data,
        )


@dataclass(slots=True, frozen=True)
class ArtifactContract:
    artifact_role: str
    contract_version: str
    primary_format: str
    read_write_semantics: str
    authority_rule: str | None = None
    path_rule: str | None = None
    sidecar_convention: str | None = None
    lifecycle_hint: str | None = None
    bridge_hints: tuple[str, ...] = ()
    extensions: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ArtifactContract":
        data = _copy_mapping(raw)
        return cls(
            artifact_role=_require_str(data, "artifactRole"),
            contract_version=_require_str(data, "contractVersion"),
            primary_format=_require_str(data, "primaryFormat"),
            read_write_semantics=_require_str(data, "readWriteSemantics"),
            authority_rule=_optional_str(data, "authorityRule"),
            path_rule=_optional_str(data, "pathRule"),
            sidecar_convention=_optional_str(data, "sidecarConvention"),
            lifecycle_hint=_optional_str(data, "lifecycleHint"),
            bridge_hints=_string_tuple(data, "bridgeHints", required=False),
            extensions=data,
        )


@dataclass(slots=True, frozen=True)
class EvidenceContract:
    evidence_type: str
    contract_version: str
    source_pointer: str
    related_session: str
    related_node: str
    related_artifacts: tuple[str, ...]
    lineage_links: tuple[str, ...]
    outcome: str | None = None
    verdict: str | None = None
    archive_state: str | None = None
    approval_ref: str | None = None
    exception_refs: tuple[str, ...] = ()
    reviewer_ref: str | None = None
    extensions: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "EvidenceContract":
        data = _copy_mapping(raw)
        return cls(
            evidence_type=_require_str(data, "evidenceType"),
            contract_version=_require_str(data, "contractVersion"),
            source_pointer=_require_str(data, "sourcePointer"),
            related_session=_require_str(data, "relatedSession"),
            related_node=_require_str(data, "relatedNode"),
            related_artifacts=_string_tuple(data, "relatedArtifacts", required=True),
            lineage_links=_string_tuple(data, "lineageLinks", required=True),
            outcome=_optional_str(data, "outcome"),
            verdict=_optional_str(data, "verdict"),
            archive_state=_optional_str(data, "archiveState"),
            approval_ref=_optional_str(data, "approvalRef"),
            exception_refs=_string_tuple(data, "exceptionRefs", required=False),
            reviewer_ref=_optional_str(data, "reviewerRef"),
            extensions=data,
        )


@dataclass(slots=True, frozen=True)
class HostAdapterContract:
    adapter_id: str
    contract_version: str
    capabilities: tuple[str, ...]
    create_session: str
    resume_session: str
    submit_step: str
    request_approval: str | None = None
    request_publish: str | None = None
    request_closeout: str | None = None
    interrupt_or_handoff_hooks: tuple[str, ...] = ()
    extensions: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "HostAdapterContract":
        data = _copy_mapping(raw)
        return cls(
            adapter_id=_require_str(data, "adapterId"),
            contract_version=_require_str(data, "contractVersion"),
            capabilities=_string_tuple(data, "capabilities", required=True),
            create_session=_require_str(data, "createSession"),
            resume_session=_require_str(data, "resumeSession"),
            submit_step=_require_str(data, "submitStep"),
            request_approval=_optional_str(data, "requestApproval"),
            request_publish=_optional_str(data, "requestPublish"),
            request_closeout=_optional_str(data, "requestCloseout"),
            interrupt_or_handoff_hooks=_string_tuple(data, "interruptOrHandoffHooks", required=False),
            extensions=data,
        )


ContractType: TypeAlias = (
    PackManifest
    | RoleContract
    | WorkflowNodeContract
    | ArtifactContract
    | EvidenceContract
    | HostAdapterContract
)
