from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.records import (
    ArtifactDescriptor,
    ArtifactIntent,
    EvidenceRecord,
    HandoffRecord,
    LineageLink,
    LineageLinkType,
    ObjectRef,
    SessionState,
    SessionStatus,
)
from session.lifecycle import SessionAction, apply_action


class AcceptanceVerdict(StrEnum):
    ACCEPTED = "accepted"
    ACCEPTED_WITH_GAPS = "accepted-with-gaps"
    NEEDS_CLARIFICATION = "needs-clarification"
    REJECTED_RETURN_UPSTREAM = "rejected-return-upstream"


@dataclass(slots=True, frozen=True)
class BridgeSurface:
    bridge_id: str
    source_pack: str
    target_pack: str
    source_session_ref: ObjectRef
    source_node_ref: ObjectRef
    target_node_ref: ObjectRef
    bridge_artifact: ArtifactDescriptor
    bridge_evidence: EvidenceRecord
    source_artifact_refs: tuple[ObjectRef, ...] = ()
    supporting_evidence_refs: tuple[ObjectRef, ...] = ()


@dataclass(slots=True, frozen=True)
class ReworkRequest:
    request_id: str
    bridge_ref: ObjectRef
    verdict: AcceptanceVerdict
    requested_from_pack: str
    requested_by_pack: str
    rationale: str
    missing_items: tuple[str, ...]
    suggested_next_steps: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class VerdictRoute:
    verdict: AcceptanceVerdict
    session_action: SessionAction
    next_status: SessionStatus
    summary: str
    needs_rework_request: bool = False


@dataclass(slots=True, frozen=True)
class AcceptanceOutcome:
    verdict: AcceptanceVerdict
    route: VerdictRoute
    next_state: SessionState
    acceptance_evidence: EvidenceRecord
    handoff_record: HandoffRecord
    lineage_links: tuple[LineageLink, ...]
    rework_request: ReworkRequest | None = None


@dataclass(slots=True, frozen=True)
class BridgeWalkthrough:
    bridge_surface: BridgeSurface
    accepted_path: AcceptanceOutcome
    clarification_path: AcceptanceOutcome
    closeout_artifact: ArtifactDescriptor
    closeout_evidence: EvidenceRecord
    closeout_lineage: LineageLink


_VERDICT_ROUTES: dict[AcceptanceVerdict, VerdictRoute] = {
    AcceptanceVerdict.ACCEPTED: VerdictRoute(
        verdict=AcceptanceVerdict.ACCEPTED,
        session_action=SessionAction.RESUME,
        next_status=SessionStatus.ACTIVE,
        summary="Bridge accepted into the target pack mainline.",
    ),
    AcceptanceVerdict.ACCEPTED_WITH_GAPS: VerdictRoute(
        verdict=AcceptanceVerdict.ACCEPTED_WITH_GAPS,
        session_action=SessionAction.RESUME,
        next_status=SessionStatus.ACTIVE,
        summary="Bridge accepted into the target pack mainline with explicit gaps.",
    ),
    AcceptanceVerdict.NEEDS_CLARIFICATION: VerdictRoute(
        verdict=AcceptanceVerdict.NEEDS_CLARIFICATION,
        session_action=SessionAction.ENTER_REVIEW_HOLD,
        next_status=SessionStatus.REVIEW_HOLD,
        summary="Bridge held for clarification before target-pack intake can continue.",
        needs_rework_request=True,
    ),
    AcceptanceVerdict.REJECTED_RETURN_UPSTREAM: VerdictRoute(
        verdict=AcceptanceVerdict.REJECTED_RETURN_UPSTREAM,
        session_action=SessionAction.ENTER_REWORK,
        next_status=SessionStatus.REWORK,
        summary="Bridge rejected and returned upstream for explicit rework.",
        needs_rework_request=True,
    ),
}


def routing_for_verdict(verdict: AcceptanceVerdict) -> VerdictRoute:
    return _VERDICT_ROUTES[verdict]


def accept_bridge(
    surface: BridgeSurface,
    *,
    session_state: SessionState,
    snapshot_ref: ObjectRef,
    acceptance_id: str,
    handoff_id: str,
    verdict: AcceptanceVerdict,
    rationale: str,
    missing_items: tuple[str, ...] = (),
    suggested_next_steps: tuple[str, ...] = (),
) -> AcceptanceOutcome:
    if session_state.session_status != SessionStatus.HANDOFF_PENDING:
        raise ValueError("Bridge acceptance requires a session in 'handoff-pending'.")

    route = routing_for_verdict(verdict)
    bridge_artifact_ref = _artifact_ref(surface.bridge_artifact)
    bridge_evidence_ref = ObjectRef(kind="evidence", object_id=surface.bridge_evidence.evidence_id)

    lineage_links = _build_lineage_links(
        surface=surface,
        acceptance_id=acceptance_id,
    )
    acceptance_evidence_ref = ObjectRef(kind="evidence", object_id=acceptance_id)
    acceptance_evidence = EvidenceRecord(
        evidence_id=acceptance_id,
        evidence_type="bridge-lineage",
        session_ref=ObjectRef(kind="session-state", object_id=session_state.session_id),
        node_ref=surface.target_node_ref,
        artifact_refs=(bridge_artifact_ref,),
        outcome_or_verdict=verdict.value,
        source_pointer=f"evidence/reference-slice/{acceptance_id}.md",
        lineage_link_refs=tuple(
            ObjectRef(kind="lineage", object_id=link.link_id)
            for link in lineage_links
        ),
    )
    handoff_record = HandoffRecord(
        handoff_id=handoff_id,
        session_ref=ObjectRef(kind="session-state", object_id=session_state.session_id),
        snapshot_ref=snapshot_ref,
        source_ref=surface.source_node_ref,
        target_ref=surface.target_node_ref,
        scope="cross-pack-bridge",
        artifact_refs=(bridge_artifact_ref, *surface.source_artifact_refs),
        evidence_refs=(
            bridge_evidence_ref,
            *surface.supporting_evidence_refs,
            acceptance_evidence_ref,
        ),
        acceptance=verdict.value,
    )
    next_state = apply_action(
        session_state,
        route.session_action,
        summary=route.summary,
    )

    rework_request = None
    if route.needs_rework_request:
        rework_request = ReworkRequest(
            request_id=f"rework.{acceptance_id}",
            bridge_ref=bridge_artifact_ref,
            verdict=verdict,
            requested_from_pack=surface.source_pack,
            requested_by_pack=surface.target_pack,
            rationale=rationale,
            missing_items=missing_items,
            suggested_next_steps=suggested_next_steps,
        )

    return AcceptanceOutcome(
        verdict=verdict,
        route=route,
        next_state=next_state,
        acceptance_evidence=acceptance_evidence,
        handoff_record=handoff_record,
        lineage_links=lineage_links,
        rework_request=rework_request,
    )


def build_reference_bridge_walkthrough_fixture() -> BridgeWalkthrough:
    source_session_ref = ObjectRef(kind="session-state", object_id="session.product.demo")
    source_node_ref = ObjectRef(kind="node", object_id="product-insights.bridge-ready")
    target_node_ref = ObjectRef(kind="node", object_id="coding.bridge-intake")

    bridge_intent = ArtifactIntent(
        intent_id="intent.bridge.demo",
        session_ref=source_session_ref,
        source_node_ref=source_node_ref,
        artifact_role="spec-bridge",
        purpose="Bridge a product-insights result into coding intake.",
    )
    bridge_artifact = ArtifactDescriptor(
        artifact_id="artifact.bridge.demo",
        intent_ref=ObjectRef(kind="artifact-intent", object_id=bridge_intent.intent_id),
        artifact_role="spec-bridge",
        pack_id="product-insights",
        primary_format="markdown",
        locator="artifacts/product-insights/spec-bridge/spec-bridge--demo.md",
    )
    bridge_artifact_ref = _artifact_ref(bridge_artifact)
    bridge_evidence = EvidenceRecord(
        evidence_id="evidence.bridge.demo",
        evidence_type="bridge-evidence",
        session_ref=source_session_ref,
        node_ref=source_node_ref,
        artifact_refs=(bridge_artifact_ref,),
        outcome_or_verdict="bridge-ready",
        source_pointer="evidence/product-insights/bridge-evidence--demo.md",
    )
    surface = BridgeSurface(
        bridge_id="bridge.demo.product-to-coding",
        source_pack="product-insights",
        target_pack="coding",
        source_session_ref=source_session_ref,
        source_node_ref=source_node_ref,
        target_node_ref=target_node_ref,
        bridge_artifact=bridge_artifact,
        bridge_evidence=bridge_evidence,
        source_artifact_refs=(
            ObjectRef(kind="artifact", object_id="artifact.opportunity.demo"),
            ObjectRef(kind="artifact", object_id="artifact.concept.demo"),
            ObjectRef(kind="artifact", object_id="artifact.probe.demo"),
        ),
        supporting_evidence_refs=(
            ObjectRef(kind="evidence", object_id="evidence.source.demo"),
            ObjectRef(kind="evidence", object_id="evidence.review.demo"),
        ),
    )

    session_state = SessionState(
        session_id="session.coding.demo",
        intent_ref=ObjectRef(kind="session-intent", object_id="intent.coding.demo"),
        context_pointer_ref=ObjectRef(kind="context-pointer", object_id="context.coding.demo"),
        session_status=SessionStatus.HANDOFF_PENDING,
        current_pack="coding",
        current_node="coding.bridge-intake",
        summary="Waiting for a product-insights bridge verdict.",
    )
    snapshot_ref = ObjectRef(kind="session-snapshot", object_id="snapshot.coding.demo.handoff")
    accepted_path = accept_bridge(
        surface,
        session_state=session_state,
        snapshot_ref=snapshot_ref,
        acceptance_id="evidence.bridge.accepted.demo",
        handoff_id="handoff.bridge.accepted.demo",
        verdict=AcceptanceVerdict.ACCEPTED_WITH_GAPS,
        rationale="The bridge is actionable now, with a small verification gap carried forward.",
        missing_items=("expand verification coverage for the edge path",),
        suggested_next_steps=("track the verification gap in closeout",),
    )
    clarification_path = accept_bridge(
        surface,
        session_state=session_state,
        snapshot_ref=snapshot_ref,
        acceptance_id="evidence.bridge.clarification.demo",
        handoff_id="handoff.bridge.clarification.demo",
        verdict=AcceptanceVerdict.NEEDS_CLARIFICATION,
        rationale="The bridge still leaves scope ownership and unknown-risk handling unclear.",
        missing_items=("clarify scope boundary", "name the risk owner"),
        suggested_next_steps=("expand bridge evidence", "tighten non-goals in the bridge artifact"),
    )

    closeout_intent = ArtifactIntent(
        intent_id="intent.closeout.demo",
        session_ref=ObjectRef(kind="session-state", object_id=accepted_path.next_state.session_id),
        source_node_ref=ObjectRef(kind="node", object_id="coding.closeout"),
        artifact_role="closeout-summary",
        purpose="Capture why this coding slice can leave the active mainline.",
    )
    closeout_artifact = ArtifactDescriptor(
        artifact_id="artifact.closeout.demo",
        intent_ref=ObjectRef(kind="artifact-intent", object_id=closeout_intent.intent_id),
        artifact_role="closeout-summary",
        pack_id="coding",
        primary_format="markdown",
        locator="artifacts/coding/closeout/closeout-summary--demo.md",
    )
    closeout_artifact_ref = _artifact_ref(closeout_artifact)
    closeout_evidence = EvidenceRecord(
        evidence_id="evidence.closeout.demo",
        evidence_type="closeout-record",
        session_ref=ObjectRef(kind="session-state", object_id=accepted_path.next_state.session_id),
        node_ref=ObjectRef(kind="node", object_id="coding.closeout"),
        artifact_refs=(closeout_artifact_ref,),
        outcome_or_verdict="accepted-with-followups",
        source_pointer="evidence/coding/closeout-record--demo.md",
    )
    closeout_lineage = LineageLink(
        link_id="lineage.bridge.demo.closeout",
        link_type=LineageLinkType.DERIVED_FROM,
        source_ref=bridge_artifact_ref,
        target_ref=closeout_artifact_ref,
        rationale="The closeout summary must remain traceable to the bridge that started coding intake.",
    )

    return BridgeWalkthrough(
        bridge_surface=surface,
        accepted_path=accepted_path,
        clarification_path=clarification_path,
        closeout_artifact=closeout_artifact,
        closeout_evidence=closeout_evidence,
        closeout_lineage=closeout_lineage,
    )


def _artifact_ref(descriptor: ArtifactDescriptor) -> ObjectRef:
    return ObjectRef(kind="artifact", object_id=descriptor.artifact_id)


def _build_lineage_links(
    *,
    surface: BridgeSurface,
    acceptance_id: str,
) -> tuple[LineageLink, ...]:
    bridge_artifact_ref = _artifact_ref(surface.bridge_artifact)
    bridge_evidence_ref = ObjectRef(kind="evidence", object_id=surface.bridge_evidence.evidence_id)
    links: list[LineageLink] = []
    for index, source_ref in enumerate(surface.source_artifact_refs, start=1):
        links.append(
            LineageLink(
                link_id=f"lineage.{surface.bridge_id}.source.{index}",
                link_type=LineageLinkType.DERIVED_FROM,
                source_ref=source_ref,
                target_ref=bridge_artifact_ref,
                rationale="The bridge artifact is derived from explicit source-pack artifacts.",
            )
        )
    links.append(
        LineageLink(
            link_id=f"lineage.{surface.bridge_id}.evidence",
            link_type=LineageLinkType.DERIVED_FROM,
            source_ref=bridge_artifact_ref,
            target_ref=bridge_evidence_ref,
            rationale="Bridge evidence explains why the bridge artifact is ready for handoff.",
        )
    )
    links.append(
        LineageLink(
            link_id=f"lineage.{surface.bridge_id}.acceptance",
            link_type=LineageLinkType.HANDOFF_OF,
            source_ref=bridge_artifact_ref,
            target_ref=ObjectRef(kind="evidence", object_id=acceptance_id),
            rationale="Acceptance evidence records how the target pack handled the bridge.",
        )
    )
    return tuple(links)
