"""F015 T3: ``compute_status_summary`` for ``garage status`` integration.

FR-1505 + Im-2 r2: Always emits "Agent compose: <pack> has N agents" line per
first-class pack. Does NOT include "last compose: <ts>" suffix (Im-2 r2: do not
depend on optional cache.json).

INV-F15-2 + INV-F15-3: read-only on packs/<id>/agents/*.md (does not write or
modify).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# First-class packs in F011/F012/F013-A repository convention.
# Listed for status display; status section iterates only those that exist
# under packs/ on disk.
FIRST_CLASS_PACKS = ("garage", "coding", "writing", "search")


@dataclass
class AgentComposeStatus:
    """Per-pack agent count returned by ``compute_status_summary``."""

    counts_by_pack: dict[str, int] = field(default_factory=dict)
    """Map: pack_id → count of *.md files in packs/<pack>/agents/."""

    metadata_lines: list[str] = field(default_factory=list)
    """Always emitted; one line per pack with an agents/ dir.
    Format: 'Agent compose: <pack> has N agents'.
    """


def compute_status_summary(packs_root: Path) -> AgentComposeStatus:
    """Walk ``packs/<id>/agents/`` for first-class packs; produce status lines.

    Returns ``AgentComposeStatus`` with per-pack counts. When a first-class
    pack does not have an ``agents/`` dir, it is silently skipped (RSK-1501
    is satisfied because at least one of the first-class packs almost always
    has agents/, e.g. garage).
    """
    counts: dict[str, int] = {}
    lines: list[str] = []
    if not packs_root.is_dir():
        return AgentComposeStatus(counts_by_pack={}, metadata_lines=[])
    for pack_id in FIRST_CLASS_PACKS:
        agents_dir = packs_root / pack_id / "agents"
        if not agents_dir.is_dir():
            continue
        agent_count = sum(1 for _ in agents_dir.glob("*.md"))
        counts[pack_id] = agent_count
        lines.append(f"Agent compose: {pack_id} has {agent_count} agents")
    return AgentComposeStatus(counts_by_pack=counts, metadata_lines=lines)
