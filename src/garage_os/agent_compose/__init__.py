"""F015: Agent Compose.

Top-level package that reads SKILL.md frontmatter + KnowledgeStore STYLE entries
and composes them into an agent.md draft (the half-automatic agent build path,
sibling of F013-A skill mining template_generator).

Modules:
- ``types``: ``AgentDraft`` + ``ComposeResult`` dataclass
- ``template_generator``: agent.md draft string (skill-anatomy-aligned 7-section)
- ``composer`` (T2): main compose logic (read SKILL.md + STYLE + assemble)
- ``pipeline`` (T3): status summary

Reads from F008 ``packs/<id>/skills/<skill>/SKILL.md`` (frontmatter only) +
F011 ``KnowledgeStore.list_entries(knowledge_type=KnowledgeType.STYLE)`` (read-only,
INV-F15-1); writes only to ``packs/<target>/agents/<name>.md`` via the CLI
promote path (INV-F15-2). Does not touch ``packs/<id>/pack.json`` (INV-F15-3,
CON-1503).
"""

from garage_os.agent_compose.types import AgentDraft, ComposeResult

__all__ = ["AgentDraft", "ComposeResult"]
