"""F016: Memory Activation.

Top-level package that activates the F003-F015 memory pipeline on the user's
workspace by providing:

- ``memory enable`` / ``disable`` / ``status`` CLI surface for explicit
  control of ``platform.json memory.extraction_enabled``
- ``memory ingest`` paths to backfill historical data into ExperienceIndex +
  KnowledgeStore (from review verdicts, git log, STYLE templates)
- ``garage init`` interactive prompt + ``--no-memory`` flag (Cr-1 r2: does NOT
  overload existing ``--yes`` semantics)

Reads + writes via F004 store API (``ExperienceIndex.store`` /
``KnowledgeStore.store``) — does NOT modify F003-F015 method signatures
(CON-1601).
"""

from garage_os.memory_activation.types import IngestSummary, MemoryStatus

__all__ = ["IngestSummary", "MemoryStatus"]
