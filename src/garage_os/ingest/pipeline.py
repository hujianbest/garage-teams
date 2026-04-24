"""F010 ingest pipeline: orchestrate host conversation → SessionState → F003 candidate.

Implements ADR-D10-7 + ADR-D10-9 r2 (signal-fill + bypass extraction_enabled gate).

Real F003-F006 API anchors (per design ADR-D10-9 r2 + tasks T6 acceptance):
- ``session_manager.update_session(session_id, context_metadata={...})`` — kwarg
  is ``context_metadata`` per ``runtime/session_manager.py:108-155``
- ``session_manager.archive_session(session_id, reason=...)`` — kwarg is ``reason``
  per ``session_manager.py:157``
- ``orchestrator.extract_for_archived_session_id(session_id)`` — method per
  ``memory/extraction_orchestrator.py:114``

Signal-fill (ADR-D10-9 r2 C-3 fix): write ``metadata.tags`` (signal #1 priority 0.62)
+ ``metadata.problem_domain`` (signal #2 priority 0.72) so candidates actually
materialize through ``_build_signals`` (extraction_orchestrator.py:126-144).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from garage_os.ingest.host_readers import HOST_READERS
from garage_os.ingest.types import HostHistoryReader
from garage_os.memory.candidate_store import CandidateStore
from garage_os.memory.extraction_orchestrator import (
    ExtractionConfig,
    MemoryExtractionOrchestrator,
)
from garage_os.runtime.session_manager import SessionManager
from garage_os.storage.file_storage import FileStorage


@dataclass
class ImportSummary:
    host: str
    imported: int = 0
    skipped: int = 0
    batch_id: str | None = None


def import_conversations(
    workspace_root: Path,
    host: str,  # canonical ingest host_id (already alias-resolved by CLI)
    conversation_ids: list[str],
    *,
    session_manager: SessionManager | None = None,
    storage: FileStorage | None = None,
    reader: HostHistoryReader | None = None,
    stderr: IO[str] | None = None,
) -> ImportSummary:
    """Import host conversations as Garage SessionMetadata + trigger F003 extraction.

    Args:
        workspace_root: project root containing .garage/
        host: canonical ingest host_id ('claude-code' / 'opencode' / 'cursor')
        conversation_ids: which conversations to import (CLI gathers via selector)
        session_manager: optional (testing); default builds from storage
        storage: optional (testing); default FileStorage(workspace_root / .garage)
        reader: optional (testing); default HOST_READERS[host]()
        stderr: optional stderr stream

    Returns:
        ImportSummary with imported / skipped / batch_id
    """
    err = stderr if stderr is not None else sys.stderr
    if storage is None:
        storage = FileStorage(workspace_root / ".garage")
    if session_manager is None:
        session_manager = SessionManager(storage)
    if reader is None:
        reader_cls = HOST_READERS[host]
        reader = reader_cls()

    # ADR-D10-9 r2 C-2 fix: ingest constructs orchestrator + calls extract directly
    # to bypass _trigger_memory_extraction's is_extraction_enabled() gate (which
    # defaults to False and would silently no-op).
    orchestrator = MemoryExtractionOrchestrator(
        storage, CandidateStore(storage), ExtractionConfig()
    )

    summary = ImportSummary(host=host)

    for conv_id in conversation_ids:
        try:
            conv = reader.read_conversation(conv_id)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
            print(f"Skipped {conv_id}: {exc}", file=err)
            summary.skipped += 1
            continue

        # ADR-D10-9 r2 C-3 fix: signal-fill (tags + problem_domain hit _build_signals strong signals)
        first_user_msg = conv.first_user_message_excerpt(max_chars=100)
        topic = conv.topic_or_summary()
        ctx_metadata = {
            "imported_from": f"{host}:{conv_id}",  # ADR-D10-7 provenance key
            "tags": ["ingested", host, *conv.derived_tags()[:3]],
            "problem_domain": first_user_msg or topic[:100],
        }

        # ADR-D10-9 r2 C-1 fix: real API names (verified against session_manager.py:108/157)
        session = session_manager.create_session(
            pack_id="ingested-from-host",
            topic=topic,
            user_goals=[],
            constraints=[],
        )
        session_manager.update_session(
            session.session_id,
            context_metadata=ctx_metadata,  # real kwarg name
        )
        session_manager.archive_session(
            session.session_id,
            reason=f"ingested-from-{host}",  # real kwarg name
        )
        # Bypass extraction_enabled gate: ingest is explicit user opt-in
        try:
            batch = orchestrator.extract_for_archived_session_id(session.session_id)
            if summary.batch_id is None:
                summary.batch_id = batch.get("batch_id") if isinstance(batch, dict) else None
        except Exception as exc:
            print(
                f"Extraction failed for session {session.session_id}: {exc}",
                file=err,
            )
            # Best-effort; do not fail import (与 archive_session best-effort 同精神)

        summary.imported += 1

    return summary
