"""Core runtime record models for the current T020 slice."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SessionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    HANDOFF_PENDING = "handoff-pending"
    REVIEW_HOLD = "review-hold"
    REWORK = "rework"
    CLOSEOUT = "closeout"
    ARCHIVE_READY = "archive-ready"
    CLOSED = "closed"


class GateVerdict(StrEnum):
    ALLOW = "allow"
    HOLD = "hold"
    NEEDS_REVIEW = "need-review"
    NEEDS_APPROVAL = "need-approval"
    NEEDS_EVIDENCE = "need-evidence"
    BLOCK = "block"


class LineageLinkType(StrEnum):
    DERIVED_FROM = "derived-from"
    HANDOFF_OF = "handoff-of"
    APPROVAL_OF = "approval-of"
    SUPERSEDES = "supersedes"
    ARCHIVED_AS = "archived-as"


class WriteSemantics(StrEnum):
    CURRENT_SLOT = "current-slot"
    APPEND_ONLY = "append-only"
    IMMUTABLE = "immutable"


@dataclass(slots=True, frozen=True)
class ObjectRef:
    kind: str
    object_id: str


@dataclass(slots=True, frozen=True)
class SessionIntent:
    intent_id: str
    initiator: str
    problem_kind: str
    entry_pack: str
    entry_node: str
    goal: str
    boundaries: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ContextPointer:
    context_pointer_id: str
    session_id: str
    artifact_refs: tuple[ObjectRef, ...] = ()
    evidence_refs: tuple[ObjectRef, ...] = ()
    active_node_refs: tuple[ObjectRef, ...] = ()
    handoff_refs: tuple[ObjectRef, ...] = ()


@dataclass(slots=True, frozen=True)
class SessionState:
    session_id: str
    intent_ref: ObjectRef
    context_pointer_ref: ObjectRef
    session_status: SessionStatus
    current_pack: str
    current_node: str
    summary: str
    pending_gate_refs: tuple[ObjectRef, ...] = ()


@dataclass(slots=True, frozen=True)
class SessionSnapshot:
    snapshot_id: str
    session_ref: ObjectRef
    state_ref: ObjectRef
    context_pointer_ref: ObjectRef
    reason: str
    summary: str


@dataclass(slots=True, frozen=True)
class HandoffRecord:
    handoff_id: str
    session_ref: ObjectRef
    snapshot_ref: ObjectRef
    source_ref: ObjectRef
    target_ref: ObjectRef
    scope: str
    artifact_refs: tuple[ObjectRef, ...] = ()
    evidence_refs: tuple[ObjectRef, ...] = ()
    acceptance: str = "pending"


@dataclass(slots=True, frozen=True)
class ArtifactIntent:
    intent_id: str
    session_ref: ObjectRef
    source_node_ref: ObjectRef
    artifact_role: str
    purpose: str


@dataclass(slots=True, frozen=True)
class ArtifactDescriptor:
    artifact_id: str
    intent_ref: ObjectRef
    artifact_role: str
    pack_id: str
    primary_format: str
    locator: str


@dataclass(slots=True, frozen=True)
class AuthorityMarker:
    artifact_ref: ObjectRef
    is_authoritative: bool
    superseded_by: ObjectRef | None = None
    archived: bool = False


@dataclass(slots=True, frozen=True)
class PolicySet:
    policy_id: str
    source_levels: tuple[str, ...]
    scope: tuple[str, ...]
    rule_refs: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class GateDecision:
    decision_id: str
    action_ref: ObjectRef
    policy_set_ref: ObjectRef
    verdict: GateVerdict
    missing: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(slots=True, frozen=True)
class ExceptionRecord:
    exception_id: str
    waived: tuple[str, ...]
    rationale: str
    approved_by: str
    expires_at: str | None = None
    policy_set_ref: ObjectRef | None = None


@dataclass(slots=True, frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_type: str
    session_ref: ObjectRef
    node_ref: ObjectRef | None
    artifact_refs: tuple[ObjectRef, ...]
    outcome_or_verdict: str
    source_pointer: str
    lineage_link_refs: tuple[ObjectRef, ...] = ()


@dataclass(slots=True, frozen=True)
class LineageLink:
    link_id: str
    link_type: LineageLinkType
    source_ref: ObjectRef
    target_ref: ObjectRef
    rationale: str = ""


CURRENT_SLOT_RECORD_TYPES = (
    SessionState,
    ContextPointer,
    AuthorityMarker,
)

APPEND_ONLY_RECORD_TYPES = (
    SessionSnapshot,
    HandoffRecord,
    GateDecision,
    ExceptionRecord,
    EvidenceRecord,
    LineageLink,
)

IMMUTABLE_RECORD_TYPES = (
    SessionIntent,
    ArtifactIntent,
    ArtifactDescriptor,
    PolicySet,
)


def write_semantics_for(record_or_type: object) -> WriteSemantics:
    record_type = record_or_type if isinstance(record_or_type, type) else type(record_or_type)
    if issubclass(record_type, CURRENT_SLOT_RECORD_TYPES):
        return WriteSemantics.CURRENT_SLOT
    if issubclass(record_type, APPEND_ONLY_RECORD_TYPES):
        return WriteSemantics.APPEND_ONLY
    if issubclass(record_type, IMMUTABLE_RECORD_TYPES):
        return WriteSemantics.IMMUTABLE
    raise TypeError(f"Unsupported record type: {record_type!r}")


def build_session_creation_fixture() -> dict[str, object]:
    intent = SessionIntent(
        intent_id="intent.demo.coding",
        initiator="creator",
        problem_kind="implementation",
        entry_pack="coding",
        entry_node="intake",
        goal="Land the initial Garage runtime skeleton.",
        boundaries=("workspace-first", "do-not-touch-pack-assets"),
    )
    context_pointer = ContextPointer(
        context_pointer_id="context.session.demo",
        session_id="session.demo",
        active_node_refs=(ObjectRef(kind="node", object_id="coding.intake"),),
    )
    state = SessionState(
        session_id="session.demo",
        intent_ref=ObjectRef(kind="session-intent", object_id=intent.intent_id),
        context_pointer_ref=ObjectRef(kind="context-pointer", object_id=context_pointer.context_pointer_id),
        session_status=SessionStatus.ACTIVE,
        current_pack="coding",
        current_node="coding.intake",
        summary="The coding pack is preparing the runtime skeleton.",
    )
    return {
        "intent": intent,
        "context_pointer": context_pointer,
        "state": state,
    }


def build_handoff_fixture() -> dict[str, object]:
    session_fixture = build_session_creation_fixture()
    state = session_fixture["state"]
    context_pointer = session_fixture["context_pointer"]
    if not isinstance(state, SessionState) or not isinstance(context_pointer, ContextPointer):
        raise TypeError("Unexpected fixture payload.")

    snapshot = SessionSnapshot(
        snapshot_id="snapshot.session.demo.handoff",
        session_ref=ObjectRef(kind="session-state", object_id=state.session_id),
        state_ref=ObjectRef(kind="session-state", object_id=state.session_id),
        context_pointer_ref=ObjectRef(kind="context-pointer", object_id=context_pointer.context_pointer_id),
        reason="handoff",
        summary="Product handoff is ready for coding intake.",
    )
    handoff = HandoffRecord(
        handoff_id="handoff.demo.product-to-coding",
        session_ref=ObjectRef(kind="session-state", object_id=state.session_id),
        snapshot_ref=ObjectRef(kind="session-snapshot", object_id=snapshot.snapshot_id),
        source_ref=ObjectRef(kind="node", object_id="product-insights.bridge-ready"),
        target_ref=ObjectRef(kind="node", object_id="coding.intake"),
        scope="reference-pack bridge",
        artifact_refs=(ObjectRef(kind="artifact", object_id="artifact.bridge.spec-brief"),),
        evidence_refs=(ObjectRef(kind="evidence", object_id="evidence.bridge.ready"),),
        acceptance="accepted-with-clarifications",
    )
    return {
        "snapshot": snapshot,
        "handoff": handoff,
    }


def build_gate_decision_fixture() -> dict[str, object]:
    policy_set = PolicySet(
        policy_id="policy.runtime.default",
        source_levels=("vision", "runtime", "pack"),
        scope=("session.demo", "coding.intake"),
        rule_refs=("approval.required-on-publish", "evidence.required-on-closeout"),
    )
    decision = GateDecision(
        decision_id="gate.demo.closeout",
        action_ref=ObjectRef(kind="action", object_id="closeout.submit"),
        policy_set_ref=ObjectRef(kind="policy-set", object_id=policy_set.policy_id),
        verdict=GateVerdict.NEEDS_APPROVAL,
        missing=("creator-approval",),
        rationale="Closeout can proceed after creator approval is attached.",
    )
    return {
        "policy_set": policy_set,
        "decision": decision,
    }


def build_evidence_lineage_fixture() -> dict[str, object]:
    artifact_ref = ObjectRef(kind="artifact", object_id="artifact.runtime.skeleton")
    evidence = EvidenceRecord(
        evidence_id="evidence.runtime.foundation",
        evidence_type="verification",
        session_ref=ObjectRef(kind="session-state", object_id="session.demo"),
        node_ref=ObjectRef(kind="node", object_id="coding.verify"),
        artifact_refs=(artifact_ref,),
        outcome_or_verdict="passed",
        source_pointer="tests/runtime_skeleton_verification.md",
    )
    lineage = LineageLink(
        link_id="lineage.runtime.foundation",
        link_type=LineageLinkType.DERIVED_FROM,
        source_ref=artifact_ref,
        target_ref=ObjectRef(kind="evidence", object_id=evidence.evidence_id),
        rationale="Verification evidence was produced from the runtime skeleton artifact.",
    )
    evidence_with_links = EvidenceRecord(
        evidence_id=evidence.evidence_id,
        evidence_type=evidence.evidence_type,
        session_ref=evidence.session_ref,
        node_ref=evidence.node_ref,
        artifact_refs=evidence.artifact_refs,
        outcome_or_verdict=evidence.outcome_or_verdict,
        source_pointer=evidence.source_pointer,
        lineage_link_refs=(ObjectRef(kind="lineage", object_id=lineage.link_id),),
    )
    return {
        "evidence": evidence_with_links,
        "lineage": lineage,
    }
