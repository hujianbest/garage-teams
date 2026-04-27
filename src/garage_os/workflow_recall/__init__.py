"""F014: Workflow Recall.

Top-level package that consumes ExperienceIndex (read-only) to recall
historical (task_type, problem_domain) -> skill_ids sequence patterns,
emitting WorkflowAdvisory hints into hf-workflow-router's step 3.5
handoff block (advisory only — does not change authoritative routing).

Modules:
- ``types``: ``RecallResult`` + ``WorkflowAdvisory`` dataclass
- ``cache``: ``.garage/workflow-recall/{cache,last-indexed}.json`` CRUD + atomic write
- ``path_recaller`` (T2): clustering + sequence Counter + threshold gating
- ``pipeline`` (T3): ``WorkflowRecallHook.invalidate`` + status summary

Reads from F004 ``ExperienceIndex.list_records`` (read-only, INV-F14-1);
writes only to ``.garage/workflow-recall/`` (INV-F14-2).
"""

from garage_os.workflow_recall.types import RecallResult, WorkflowAdvisory

__all__ = ["RecallResult", "WorkflowAdvisory"]
