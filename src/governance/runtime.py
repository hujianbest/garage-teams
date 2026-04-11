"""Governance rule evaluation and gate scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.records import GateDecision, GateVerdict, ObjectRef, PolicySet
from session.lifecycle import SessionAction


class GovernanceScope(StrEnum):
    GLOBAL = "global"
    CORE = "core"
    PACK = "pack"
    NODE = "node"


class GateType(StrEnum):
    ENTRY = "entry"
    TRANSITION = "transition"
    WRITE = "write"
    HANDOFF = "handoff"
    ARCHIVE = "archive"
    PROMOTION = "promotion"


_VERDICT_SEVERITY = {
    GateVerdict.ALLOW: 0,
    GateVerdict.HOLD: 1,
    GateVerdict.NEEDS_REVIEW: 2,
    GateVerdict.NEEDS_APPROVAL: 3,
    GateVerdict.NEEDS_EVIDENCE: 4,
    GateVerdict.BLOCK: 5,
}


@dataclass(slots=True, frozen=True)
class RuntimeContext:
    workspace_id: str
    session_id: str
    pack_id: str
    node_id: str
    action: SessionAction

    def tokens(self) -> set[str]:
        return {
            self.workspace_id,
            self.session_id,
            self.pack_id,
            self.node_id,
            self.action.value,
        }


@dataclass(slots=True, frozen=True)
class GovernanceRule:
    rule_id: str
    scope: GovernanceScope
    gate_type: GateType
    verdict: GateVerdict
    rationale: str
    applies_to: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()

    def matches(self, context: RuntimeContext, gate_type: GateType) -> bool:
        if self.gate_type != gate_type:
            return False
        if not self.applies_to:
            return True
        tokens = context.tokens()
        return all(token in tokens for token in self.applies_to)


@dataclass(slots=True, frozen=True)
class GateEvaluation:
    policy_set: PolicySet
    decision: GateDecision
    matched_rule_ids: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ReviewRecord:
    review_id: str
    action_ref: ObjectRef
    reviewer: str
    verdict: str
    notes: str
    missing: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class ApprovalRecord:
    approval_id: str
    action_ref: ObjectRef
    approver: str
    approved: bool
    notes: str = ""


class GovernanceRuntime:
    """Evaluate layered governance rules into a single gate decision."""

    def __init__(self, rules: tuple[GovernanceRule, ...] = ()) -> None:
        self._rules = rules

    def evaluate(self, context: RuntimeContext, gate_type: GateType) -> GateEvaluation:
        matched_rules = tuple(rule for rule in self._rules if rule.matches(context, gate_type))
        if not matched_rules:
            policy_set = PolicySet(
                policy_id=f"policy.{context.session_id}.{gate_type.value}",
                source_levels=("core",),
                scope=(context.session_id, context.pack_id, context.node_id),
                rule_refs=("default-allow",),
            )
            decision = GateDecision(
                decision_id=f"gate.{context.session_id}.{gate_type.value}",
                action_ref=ObjectRef(kind="action", object_id=context.action.value),
                policy_set_ref=ObjectRef(kind="policy-set", object_id=policy_set.policy_id),
                verdict=GateVerdict.ALLOW,
                rationale="No stricter governance rule matched the current context.",
            )
            return GateEvaluation(policy_set=policy_set, decision=decision, matched_rule_ids=())

        strongest = max(matched_rules, key=lambda rule: _VERDICT_SEVERITY[rule.verdict])
        scope_order = (
            GovernanceScope.GLOBAL,
            GovernanceScope.CORE,
            GovernanceScope.PACK,
            GovernanceScope.NODE,
        )
        policy_set = PolicySet(
            policy_id=f"policy.{context.session_id}.{gate_type.value}",
            source_levels=tuple(
                scope.value
                for scope in scope_order
                if any(rule.scope == scope for rule in matched_rules)
            ),
            scope=(context.session_id, context.pack_id, context.node_id),
            rule_refs=tuple(rule.rule_id for rule in matched_rules),
        )
        decision = GateDecision(
            decision_id=f"gate.{context.session_id}.{gate_type.value}",
            action_ref=ObjectRef(kind="action", object_id=context.action.value),
            policy_set_ref=ObjectRef(kind="policy-set", object_id=policy_set.policy_id),
            verdict=strongest.verdict,
            missing=tuple(
                item
                for rule in matched_rules
                if _VERDICT_SEVERITY[rule.verdict] == _VERDICT_SEVERITY[strongest.verdict]
                for item in rule.missing
            ),
            rationale=" | ".join(rule.rationale for rule in matched_rules),
        )
        return GateEvaluation(
            policy_set=policy_set,
            decision=decision,
            matched_rule_ids=tuple(rule.rule_id for rule in matched_rules),
        )

    def request_review(
        self,
        *,
        review_id: str,
        action_ref: ObjectRef,
        reviewer: str,
        verdict: str,
        notes: str,
        missing: tuple[str, ...] = (),
    ) -> ReviewRecord:
        return ReviewRecord(
            review_id=review_id,
            action_ref=action_ref,
            reviewer=reviewer,
            verdict=verdict,
            notes=notes,
            missing=missing,
        )

    def grant_approval(
        self,
        *,
        approval_id: str,
        action_ref: ObjectRef,
        approver: str,
        approved: bool,
        notes: str = "",
    ) -> ApprovalRecord:
        return ApprovalRecord(
            approval_id=approval_id,
            action_ref=action_ref,
            approver=approver,
            approved=approved,
            notes=notes,
        )
