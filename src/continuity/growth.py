"""Continuity candidate detection and GrowthProposal promotion scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.records import EvidenceRecord, ObjectRef


class GrowthTarget(StrEnum):
    MEMORY = "memory"
    SKILL = "skill"
    RUNTIME_UPDATE = "runtime-update"


class GrowthProposalStatus(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under-review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"


class ForbiddenPromotionPathError(ValueError):
    """Raised when a prohibited continuity promotion path is requested."""


@dataclass(slots=True, frozen=True)
class ContinuityCandidate:
    candidate_id: str
    workspace_id: str
    target: GrowthTarget
    summary: str
    rationale: str
    source_evidence_refs: tuple[ObjectRef, ...]
    source_artifact_refs: tuple[ObjectRef, ...] = ()


@dataclass(slots=True, frozen=True)
class GrowthProposal:
    proposal_id: str
    workspace_id: str
    target: GrowthTarget
    summary: str
    rationale: str
    source_evidence_refs: tuple[ObjectRef, ...]
    source_artifact_refs: tuple[ObjectRef, ...]
    risk_level: str
    suggested_governance_actions: tuple[str, ...]
    status: GrowthProposalStatus = GrowthProposalStatus.DRAFT


@dataclass(slots=True, frozen=True)
class MemoryEntry:
    entry_id: str
    workspace_id: str
    content: str
    source_proposal_ref: ObjectRef


@dataclass(slots=True, frozen=True)
class SkillAsset:
    skill_id: str
    workspace_id: str
    summary: str
    source_proposal_ref: ObjectRef


@dataclass(slots=True, frozen=True)
class RuntimeUpdate:
    update_id: str
    workspace_id: str
    summary: str
    source_proposal_ref: ObjectRef


@dataclass(slots=True, frozen=True)
class PromotionDecision:
    decision_id: str
    proposal_ref: ObjectRef
    accepted: bool
    rationale: str
    target: GrowthTarget


class GrowthEngine:
    """Minimal growth engine that insists on evidence-first promotion."""

    def candidate_from_evidence(
        self,
        *,
        workspace_id: str,
        candidate_id: str,
        target: GrowthTarget,
        summary: str,
        rationale: str,
        evidence: EvidenceRecord,
    ) -> ContinuityCandidate:
        return ContinuityCandidate(
            candidate_id=candidate_id,
            workspace_id=workspace_id,
            target=target,
            summary=summary,
            rationale=rationale,
            source_evidence_refs=(ObjectRef(kind="evidence", object_id=evidence.evidence_id),),
            source_artifact_refs=evidence.artifact_refs,
        )

    def draft_proposal(
        self,
        *,
        proposal_id: str,
        candidate: ContinuityCandidate,
        risk_level: str,
        suggested_governance_actions: tuple[str, ...],
    ) -> GrowthProposal:
        return GrowthProposal(
            proposal_id=proposal_id,
            workspace_id=candidate.workspace_id,
            target=candidate.target,
            summary=candidate.summary,
            rationale=candidate.rationale,
            source_evidence_refs=candidate.source_evidence_refs,
            source_artifact_refs=candidate.source_artifact_refs,
            risk_level=risk_level,
            suggested_governance_actions=suggested_governance_actions,
        )

    def apply_decision(
        self,
        *,
        decision_id: str,
        proposal: GrowthProposal,
        accepted: bool,
        rationale: str,
    ) -> tuple[PromotionDecision, MemoryEntry | SkillAsset | RuntimeUpdate | None]:
        decision = PromotionDecision(
            decision_id=decision_id,
            proposal_ref=ObjectRef(kind="growth-proposal", object_id=proposal.proposal_id),
            accepted=accepted,
            rationale=rationale,
            target=proposal.target,
        )
        if not accepted:
            return decision, None

        proposal_ref = ObjectRef(kind="growth-proposal", object_id=proposal.proposal_id)
        if proposal.target == GrowthTarget.MEMORY:
            return decision, MemoryEntry(
                entry_id=f"memory.{proposal.proposal_id}",
                workspace_id=proposal.workspace_id,
                content=proposal.summary,
                source_proposal_ref=proposal_ref,
            )
        if proposal.target == GrowthTarget.SKILL:
            return decision, SkillAsset(
                skill_id=f"skill.{proposal.proposal_id}",
                workspace_id=proposal.workspace_id,
                summary=proposal.summary,
                source_proposal_ref=proposal_ref,
            )
        return decision, RuntimeUpdate(
            update_id=f"runtime-update.{proposal.proposal_id}",
            workspace_id=proposal.workspace_id,
            summary=proposal.summary,
            source_proposal_ref=proposal_ref,
        )

    def forbid_session_promotion(self) -> None:
        raise ForbiddenPromotionPathError(
            "Session -> Memory/Skill promotion is forbidden; promote through evidence and GrowthProposal instead."
        )
