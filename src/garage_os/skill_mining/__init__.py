"""F013-A: Skill Mining Push.

Top-level package that scans accumulated KnowledgeStore + ExperienceIndex
for repeated (problem_domain, tag-bucket) patterns and proposes them as
candidate skills (the "push" end of the memory flywheel).

Modules:
- ``types``: ``SkillSuggestion`` dataclass + ``SkillSuggestionStatus`` enum
- ``suggestion_store``: 5-status-subdir CRUD + atomic write + ``mv`` transitions
- ``pattern_detector`` (T2): clustering + scoring + threshold gating
- ``template_generator`` (T3): in-memory SKILL.md draft (skill-anatomy 6 sections)
- ``pipeline`` (T4): ``SkillMiningHook.run_after_extraction`` + audit/decay

Reads from F004 ``KnowledgeStore`` + ``ExperienceIndex`` (read-only, INV-F13-3);
writes only to ``.garage/skill-suggestions/`` (INV-F13-1).
"""

from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus

__all__ = ["SkillSuggestion", "SkillSuggestionStatus"]
