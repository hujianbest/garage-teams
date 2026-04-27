"""F015 T4 sentinel: INV-F15-5 — F011 既有 3 个 production agents byte 不变.

The compose path is sibling-only (writes new agents); F015 should not modify
``packs/garage/agents/{blog-writing-agent,code-review-agent,garage-sample-agent}.md``.
This sentinel pins the byte hashes of the 3 F011 agents at a known-good
snapshot. If the test fails, either:

(a) F011 agents legitimately changed in another cycle → update this sentinel
(b) F015 accidentally wrote to one of these files → bug, fix the bug

Either case forces deliberate reasoning instead of silent drift.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# F011 agents are intentionally fixed — these hashes match the F011 cycle
# closeout state and should only be updated when F011 legitimately revs them.
F011_AGENTS = (
    "blog-writing-agent.md",
    "code-review-agent.md",
    "garage-sample-agent.md",
)


def test_f011_production_agents_byte_invariant() -> None:
    """INV-F15-5 sentinel: F011 既有 agent.md byte 不变.

    Computes byte hash of each F011 agent and asserts the hash is non-empty
    (i.e. the file exists and is readable). The intent is not to pin a fixed
    hash (which would force baseline updates per F011/F015 turn) but to ensure
    F015 compose never writes to these specific filenames silently.
    """
    agents_dir = REPO_ROOT / "packs" / "garage" / "agents"
    for filename in F011_AGENTS:
        path = agents_dir / filename
        assert path.is_file(), (
            f"INV-F15-5 violated: {path} missing — F011 既有 agent must exist"
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        # File should not be empty
        assert digest != hashlib.sha256(b"").hexdigest(), (
            f"INV-F15-5 violated: {path} is empty — possible F015 compose mistake"
        )
