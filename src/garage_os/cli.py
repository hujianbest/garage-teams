"""Command-line interface for Garage OS."""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence

from garage_os.adapter.claude_code_adapter import ClaudeCodeAdapter

# F004 § 11.5: stable stdout markers for the two CLI abandon paths so users
# (and downstream agents) can grep the audit log to differentiate intent.
# - NO_PUB:    --action=abandon, dropped before any publication attempt.
# - CONFLICT:  --action=accept --strategy=abandon, dropped because publisher
#              detected a real conflict with already-published knowledge.
MEMORY_REVIEW_ABANDONED_NO_PUB = (
    "Candidate '{cid}' abandoned without publication attempt"
)
MEMORY_REVIEW_ABANDONED_CONFLICT = (
    "Candidate '{cid}' abandoned due to conflict with published knowledge"
)

# F005 § 9.5 / NFR-504: stable stdout / stderr markers for the CLI
# authoring path (`garage knowledge add|edit|show|delete` and
# `garage experience add|show|delete`). All CLI handlers MUST format their
# success / failure output via these constants so that downstream Agents
# can grep-match without parsing prose.
KNOWLEDGE_ADDED_FMT = "Knowledge entry '{eid}' added"
KNOWLEDGE_EDITED_FMT = "Knowledge entry '{eid}' edited (version {version})"
KNOWLEDGE_DELETED_FMT = "Knowledge entry '{eid}' deleted"
KNOWLEDGE_NOT_FOUND_FMT = "Knowledge entry '{eid}' not found"
KNOWLEDGE_ALREADY_EXISTS_FMT = (
    "Entry with id '{eid}' already exists; "
    "pass --id to override or change inputs"
)
EXPERIENCE_ADDED_FMT = "Experience record '{rid}' added"
EXPERIENCE_DELETED_FMT = "Experience record '{rid}' deleted"
EXPERIENCE_NOT_FOUND_FMT = "Experience record '{rid}' not found"
EXPERIENCE_ALREADY_EXISTS_FMT = (
    "Experience record with id '{rid}' already exists; "
    "pass --id to override or change inputs"
)
EXPERIENCE_READ_ERR_FMT = "Failed to read experience record '{rid}': {err}"

ERR_NO_GARAGE = "No .garage/ directory found. Run 'garage init' first."
ERR_CONTENT_AND_FILE_MUTEX = "--content and --from-file are mutually exclusive"
ERR_ADD_REQUIRES_CONTENT = "add requires --content or --from-file"
ERR_FILE_NOT_FOUND_FMT = "File not found: {path}"
ERR_EDIT_REQUIRES_FIELD = (
    "edit requires at least one of --topic / --tags / --content / "
    "--from-file / --status"
)

# F005 § ADR-503: the `cli:` namespace prefix is reserved for source markers
# written by the CLI authoring path. Any artifact / source_artifact value
# starting with `cli:` MUST come from this CLI; publisher-path values MUST NOT
# start with `cli:`. Tests grep on this prefix to assert provenance.
CLI_SOURCE_KNOWLEDGE_ADD = "cli:knowledge-add"
CLI_SOURCE_KNOWLEDGE_EDIT = "cli:knowledge-edit"
CLI_SOURCE_EXPERIENCE_ADD = "cli:experience-add"

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.memory.candidate_store import CandidateStore
from garage_os.memory.extraction_orchestrator import load_memory_config
from garage_os.memory.publisher import KnowledgePublisher
from garage_os.memory.recommendation_service import (
    RecommendationContextBuilder,
    RecommendationService,
)
from garage_os.runtime.session_manager import SessionManager
from garage_os.storage import FileStorage
from garage_os.types import (
    ExperienceRecord,
    KnowledgeEntry,
    KnowledgeType,
    SessionState,
)


# Sub-directories to create under .garage/
GARAGE_DIRS = [
    "config/tools",
    "contracts",
    "knowledge/.metadata",
    "knowledge/decisions",
    "knowledge/patterns",
    "knowledge/solutions",
    "experience/records",
    "memory/candidates/batches",
    "memory/candidates/items",
    "memory/confirmations",
    "sessions/active",
    "sessions/archived",
]

GARAGE_README = """# .garage/ — Garage OS Runtime Data

This directory contains all runtime data for Garage OS.

- **config/**: Platform and adapter configurations
- **contracts/**: Interface contracts
- **knowledge/**: Knowledge entries (decisions, patterns, solutions)
- **experience/**: Experience records
- **memory/**: Candidate drafts, review batches, and confirmation records
- **sessions/**: Active and archived sessions
"""

DEFAULT_PLATFORM_CONFIG = {
    "schema_version": 1,
    "platform_name": "Garage Agent OS",
    "stage": 1,
    "storage_mode": "artifact-first",
    "host_type": "claude-code",
    "session_timeout_seconds": 7200,
    "max_active_sessions": 1,
    "knowledge_indexing": "manual",
    "memory": {
        "extraction_enabled": False,
        "recommendation_enabled": False,
    },
}

DEFAULT_HOST_ADAPTER_CONFIG = {
    "schema_version": 1,
    "host_type": "claude-code",
    "interaction_mode": "file-system",
    "capabilities": {
        "session_state_api": False,
        "file_read_write": True,
        "memory_auto_load": True,
        "subprocess": True,
    },
}


def _find_garage_root(start: Optional[Path] = None) -> Path:
    """Find the project root by searching upward for .garage/ or pyproject.toml.

    Falls back to current working directory.
    """
    current = start or Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".garage").is_dir():
            return parent
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


def _init(garage_root: Path) -> None:
    """Create the .garage/ directory structure under garage_root.

    Idempotent: does nothing for already-existing directories/files.
    """
    garage_dir = garage_root / ".garage"
    garage_dir.mkdir(parents=True, exist_ok=True)

    for subdir in GARAGE_DIRS:
        (garage_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Write README if not present
    readme_path = garage_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(GARAGE_README.strip() + "\n", encoding="utf-8")

    platform_config_path = garage_dir / "config" / "platform.json"
    if not platform_config_path.exists():
        platform_config_path.write_text(
            json.dumps(DEFAULT_PLATFORM_CONFIG, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    host_adapter_config_path = garage_dir / "config" / "host-adapter.json"
    if not host_adapter_config_path.exists():
        host_adapter_config_path.write_text(
            json.dumps(DEFAULT_HOST_ADAPTER_CONFIG, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Initialized Garage OS in {garage_dir}")


def _status(garage_root: Path) -> None:
    """Read .garage/ and display statistics."""
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)

    # Count sessions using the real on-disk session layout:
    # sessions/<state>/<session_id>/session.json
    active_sessions = storage.list_files("sessions/active", "*/session.json")
    archived_sessions = storage.list_files("sessions/archived", "*/session.json")
    total_sessions = len(active_sessions) + len(archived_sessions)

    # Count knowledge entries
    decisions = storage.list_files("knowledge/decisions", "*.md")
    patterns = storage.list_files("knowledge/patterns", "*.md")
    solutions = storage.list_files("knowledge/solutions", "*.md")
    total_knowledge = len(decisions) + len(patterns) + len(solutions)

    # Count experience records
    experience_records = storage.list_files("experience/records", "*.json")
    total_experience = len(experience_records)

    # Find most recent experience
    recent_experience: Optional[str] = None
    if total_experience > 0:
        latest = max(experience_records, key=lambda p: p.stat().st_mtime)
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            recent_experience = (
                data.get("updated_at")
                or data.get("created_at")
                or data.get("timestamp")
                or str(latest)
            )
        except (json.JSONDecodeError, OSError):
            recent_experience = str(latest)

    has_data = total_sessions > 0 or total_knowledge > 0 or total_experience > 0

    if not has_data:
        print("No data")
        return

    print(f"Sessions: {total_sessions} (active: {len(active_sessions)}, archived: {len(archived_sessions)})")
    print(
        f"Knowledge entries: {total_knowledge} "
        f"(decisions: {len(decisions)}, patterns: {len(patterns)}, solutions: {len(solutions)})"
    )
    print(f"Experience records: {total_experience}")
    if recent_experience:
        print(f"Most recent experience: {recent_experience}")


def _run(garage_root: Path, skill_name: str, timeout: int = 300) -> int:
    """Run a Garage skill and record the experience.

    Args:
        garage_root: Path to the project root
        skill_name: Name of the skill to invoke
        timeout: Timeout in seconds for Claude Code execution
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return 1

    storage = FileStorage(garage_dir)
    memory_config = load_memory_config(storage)

    # Create session manager and start a new session
    session_manager = SessionManager(storage)
    session = session_manager.create_session(
        pack_id=skill_name,
        topic=f"Run skill: {skill_name}",
        user_goals=[],
        constraints=[],
    )
    session_manager.update_session(
        session.session_id,
        state=SessionState.RUNNING,
        context_metadata={
            "domain": "general",
            "problem_domain": skill_name,
            "tags": [skill_name],
        },
    )

    # Create adapter and invoke the skill
    adapter = ClaudeCodeAdapter(garage_root, timeout=timeout)

    if memory_config["recommendation_enabled"]:
        recommendation_service = RecommendationService(
            KnowledgeStore(storage),
            ExperienceIndex(storage),
        )
        context_builder = RecommendationContextBuilder()
        repo_state = adapter.get_repository_state()
        recommendation_context = context_builder.build(
            skill_name=skill_name,
            params={},
            session_topic=session.topic,
            session_metadata=session.context.metadata,
            repo_state=repo_state,
            artifact_paths=[],
        )
        recommendations = recommendation_service.recommend(recommendation_context)
        if recommendations:
            print("Recommendations:")
            for item in recommendations[:3]:
                reasons = ", ".join(item["match_reasons"])
                print(f"  - {item['title']} [{item['entry_type']}] ({reasons})")

    start_time = time.time()
    outcome = "success"
    exit_code = 0
    output = ""

    return_code = 0

    try:
        result = adapter.invoke_skill(skill_name)
        output = result.get("output", "")
        exit_code = result.get("exit_code", 0)

        if not result.get("success", False):
            outcome = "failure"
            return_code = exit_code or 1
            session_manager.update_session(
                session.session_id, state=SessionState.FAILED
            )
            print(f"Skill '{skill_name}' failed with exit code {exit_code}")
            if output:
                print(output)
        else:
            session_manager.update_session(
                session.session_id, state=SessionState.COMPLETED
            )
            print(f"Skill '{skill_name}' completed successfully")
            if output:
                print(output)

    except Exception as e:
        outcome = "failure"
        return_code = 1
        session_manager.update_session(
            session.session_id, state=SessionState.FAILED
        )
        print(f"Error running skill '{skill_name}': {e}")

    duration_seconds = int(time.time() - start_time)

    # Record experience
    experience_index = ExperienceIndex(storage)
    from garage_os.types import ExperienceRecord

    experience_record = ExperienceRecord(
        record_id=f"exp-{session.session_id}",
        task_type="skill_execution",
        skill_ids=[skill_name],
        tech_stack=[],
        domain="general",
        problem_domain=skill_name,
        outcome=outcome,
        duration_seconds=duration_seconds,
        complexity="medium",
        session_id=session.session_id,
        artifacts=[],
        key_patterns=[],
        lessons_learned=[],
        pitfalls=[],
        recommendations=[],
    )

    try:
        experience_index.store(experience_record)
        print(f"Experience recorded: {experience_record.record_id}")
    except Exception as e:
        print(f"Warning: Failed to record experience: {e}")

    if session_manager.archive_session(session.session_id):
        print(f"Session archived: {session.session_id}")
    else:
        print(f"Warning: Failed to archive session: {session.session_id}")

    return return_code


def _knowledge_search(garage_root: Path, query: Optional[str]) -> None:
    """Search knowledge entries.

    Args:
        garage_root: Path to the project root
        query: Optional search query
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entries = knowledge_store.search(query=query)

    if not entries:
        if query:
            print(f"No knowledge entries matching '{query}'")
        else:
            print("No knowledge entries")
        return

    print(f"Found {len(entries)} knowledge entry(ies):\n")
    for entry in entries:
        print(f"  [{entry.type.value.upper()}] {entry.topic}")
        print(f"    ID: {entry.id}")
        print(f"    Date: {entry.date.strftime('%Y-%m-%d')}")
        if entry.tags:
            print(f"    Tags: {', '.join(entry.tags)}")
        print()


def _knowledge_list(garage_root: Path) -> None:
    """List all knowledge entries.

    Args:
        garage_root: Path to the project root
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entries = knowledge_store.list_entries()

    if not entries:
        print("No knowledge entries")
        return

    print(f"Total {len(entries)} knowledge entry(ies):\n")
    for entry in entries:
        print(f"  [{entry.type.value.upper()}] {entry.topic}")
        print(f"    ID: {entry.id}")
        print(f"    Date: {entry.date.strftime('%Y-%m-%d')}")
        if entry.tags:
            print(f"    Tags: {', '.join(entry.tags)}")
        print()


def _memory_review(
    garage_root: Path,
    batch_id: str,
    action: Optional[str] = None,
    candidate_id: Optional[str] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[str] = None,
    strategy: Optional[str] = None,
) -> int:
    """Show or apply actions to a candidate review batch on the CLI."""
    garage_dir = garage_root / ".garage"
    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return 1

    storage = FileStorage(garage_dir)
    candidate_store = CandidateStore(storage)
    batch = candidate_store.retrieve_batch(batch_id)
    if batch is None:
        print(f"No candidate batch found for '{batch_id}'")
        return 1

    if action:
        knowledge_store = KnowledgeStore(storage)
        experience_index = ExperienceIndex(storage)
        publisher = KnowledgePublisher(candidate_store, knowledge_store, experience_index)
        confirmation_ref = f".garage/{candidate_store.CONFIRMATIONS_DIR}/{batch_id}.json"

        if action == "batch_reject":
            actions = [
                {"candidate_id": cid, "action": "reject"}
                for cid in batch["candidate_ids"]
            ]
            candidate_store.store_confirmation(
                {
                    "schema_version": "1",
                    "batch_id": batch_id,
                    "resolution": "batch_reject",
                    "actions": actions,
                    "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "surface": "cli",
                    "approver": "user",
                }
            )
            for cid in batch["candidate_ids"]:
                candidate_store.update_candidate(cid, {"status": "rejected"})
            batch["status"] = "rejected"
            candidate_store.store_batch(batch)
            print(f"Applied action 'batch_reject' to batch '{batch_id}'")
            return 0

        if action == "defer":
            candidate_store.store_confirmation(
                {
                    "schema_version": "1",
                    "batch_id": batch_id,
                    "resolution": "defer",
                    "actions": [],
                    "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "surface": "cli",
                    "approver": "user",
                }
            )
            for cid in batch["candidate_ids"]:
                candidate_store.update_candidate(cid, {"status": "deferred"})
            batch["status"] = "deferred"
            candidate_store.store_batch(batch)
            print(f"Applied action 'defer' to batch '{batch_id}'")
            return 0

        if candidate_id is None:
            print("Action requires --candidate-id")
            return 1

        if action == "show-conflicts":
            conflict = publisher.detect_conflicts(candidate_id)
            print(f"Conflict strategy: {conflict['strategy']}")
            print(f"Similar entries: {conflict['similar_entries']}")
            return 0

        if action not in {"accept", "edit_accept", "reject", "abandon"}:
            print(f"Unsupported action '{action}'")
            return 1

        edited_fields = None
        if action == "edit_accept":
            edited_fields = {}
            if title is not None:
                edited_fields["title"] = title
            if summary is not None:
                edited_fields["summary"] = summary
            if content is not None:
                edited_fields["content"] = content
            if tags is not None:
                edited_fields["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]

        if action in {"accept", "edit_accept"}:
            conflict = publisher.detect_conflicts(candidate_id)
            if conflict.get("similar_entries") and strategy is None:
                print(
                    "Similar published knowledge detected for this candidate. "
                    "Re-run with --strategy=coexist|supersede|abandon to confirm "
                    "how to handle the conflict (FR-304)."
                )
                print(f"Similar entries: {conflict['similar_entries']}")
                return 1

        candidate_store.store_confirmation(
            {
                "schema_version": "1",
                "batch_id": batch_id,
                "resolution": action,
                "actions": [{"candidate_id": candidate_id, "action": action}],
                "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "surface": "cli",
                "approver": "user",
                "conflict_strategy": strategy,
            }
        )

        publish_result = publisher.publish_candidate(
            candidate_id=candidate_id,
            action=action,
            confirmation_ref=confirmation_ref,
            edited_fields=edited_fields,
            conflict_strategy=strategy,
        )
        # F004 FR-403a / § 10.3: derive the candidate's new status from the
        # publisher result so that --action=accept --strategy=abandon ends
        # up in the same "abandoned" terminal state when (and only when) a
        # real conflict was detected and aborted publication.
        publisher_strategy = publish_result.get("conflict_strategy")
        new_status = {
            "accept": "published",
            "edit_accept": "published",
            "reject": "rejected",
            "abandon": "abandoned",
        }[action]
        if action in {"accept", "edit_accept"} and publisher_strategy == "abandon":
            new_status = "abandoned"
        candidate_store.update_candidate(candidate_id, {"status": new_status})
        # F004 FR-403b / § 11.5: emit a stable, distinct marker for each of
        # the two abandon flows so downstream readers can distinguish them
        # without parsing the confirmation file.
        if action == "abandon":
            print(MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid=candidate_id))
        elif (
            action in {"accept", "edit_accept"}
            and publisher_strategy == "abandon"
        ):
            print(MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid=candidate_id))
        else:
            print(
                f"Candidate '{candidate_id}' action '{action}' applied; "
                f"published_id={publish_result['published_id']}"
            )
        return 0

    print(f"Candidate Batch: {batch['batch_id']}")
    print(f"Status: {batch['status']}")
    print(f"Evaluation: {batch['evaluation_summary']}")
    print(f"Candidates: {len(batch['candidate_ids'])}")
    for candidate_id in batch["candidate_ids"]:
        candidate = candidate_store.retrieve_candidate(candidate_id)
        if candidate is None:
            continue
        print(f"  - {candidate['candidate_id']}: {candidate['title']} [{candidate['candidate_type']}]")
    return 0


# ---------------------------------------------------------------------------
# F005 Knowledge / Experience authoring CLI
# ---------------------------------------------------------------------------


def _now_default() -> datetime:
    """Default clock used by the CLI authoring path.

    Indirected so unit tests can monkeypatch ``cli._now_default`` to lock
    seconds, which is required to deterministically exercise the FR-508 ID
    collision branch (same topic + content + same second → second `add` is
    rejected, not silently overwritten).
    """
    return datetime.now()


def _parse_tags(raw: Optional[str]) -> list[str]:
    """Parse a comma-separated tag string into a list, dropping blanks."""
    if raw is None:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _resolve_content(
    content_arg: Optional[str],
    from_file_arg: Optional[Path],
    *,
    require_one: bool,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve the ``content`` field for `add` / `edit`.

    Returns ``(content, error)``. Three states matter:

    - ``(content, None)``: caller should use ``content`` as-is.
    - ``(None, error)``: caller must print ``error`` to stderr and exit 1.
    - ``(None, None)``: only possible when ``require_one=False`` (i.e. the
      `edit` path), meaning "the user did not pass either flag → leave
      the existing entry's content unchanged".

    The two CLI arguments ``--content`` and ``--from-file`` are mutually
    exclusive (FR-502 / FR-503).
    """
    if content_arg is not None and from_file_arg is not None:
        return None, ERR_CONTENT_AND_FILE_MUTEX
    if content_arg is None and from_file_arg is None:
        if require_one:
            return None, ERR_ADD_REQUIRES_CONTENT
        return None, None
    if content_arg is not None:
        return content_arg, None
    assert from_file_arg is not None
    if not from_file_arg.is_file():
        return None, ERR_FILE_NOT_FOUND_FMT.format(path=from_file_arg)
    return from_file_arg.read_text(encoding="utf-8"), None


def _generate_entry_id(
    knowledge_type: KnowledgeType,
    topic: str,
    content: str,
    now: datetime,
) -> str:
    """Generate a deterministic-with-time-salt ID for a knowledge entry.

    Implements FR-508 / ADR-502. Format: ``<type>-<YYYYMMDD>-<6 hex>`` where
    the 6 hex chars come from the SHA-256 of ``topic\\ncontent\\n<iso seconds>``.
    The timestamp is part of the input so that two `add` calls with the
    same topic + content but in different seconds produce distinct IDs;
    callers that want true determinism must pass an explicit ``--id``.
    """
    timestamp = now.replace(microsecond=0).isoformat()
    digest_input = f"{topic}\n{content}\n{timestamp}".encode("utf-8")
    short = hashlib.sha256(digest_input).hexdigest()[:6]
    return f"{knowledge_type.value}-{now.strftime('%Y%m%d')}-{short}"


def _generate_experience_id(task_type: str, summary: str, now: datetime) -> str:
    """Generate a deterministic-with-time-salt ID for an experience record.

    Mirrors :func:`_generate_entry_id` for the experience surface (FR-508
    experience branch). Format: ``exp-<YYYYMMDD>-<6 hex>``.
    """
    timestamp = now.replace(microsecond=0).isoformat()
    digest_input = f"{task_type}\n{summary}\n{timestamp}".encode("utf-8")
    short = hashlib.sha256(digest_input).hexdigest()[:6]
    return f"exp-{now.strftime('%Y%m%d')}-{short}"


def _require_garage(garage_root: Path) -> Optional[Path]:
    """Return the ``.garage/`` Path if it exists, else None.

    Caller should print ``ERR_NO_GARAGE`` to stderr and exit 1 when None.
    """
    garage_dir = garage_root / ".garage"
    return garage_dir if garage_dir.is_dir() else None


def _knowledge_add(
    garage_root: Path,
    *,
    knowledge_type: str,
    topic: str,
    content_arg: Optional[str],
    from_file: Optional[Path],
    tags_raw: Optional[str],
    explicit_id: Optional[str],
    now_provider: Callable[[], datetime] = _now_default,
) -> int:
    """Implement ``garage knowledge add`` (FR-501 / FR-502 / FR-508 / FR-509)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    content, err = _resolve_content(content_arg, from_file, require_one=True)
    if err is not None:
        print(err, file=sys.stderr)
        return 1
    assert content is not None

    ktype = KnowledgeType(knowledge_type)
    now = now_provider()
    eid = explicit_id or _generate_entry_id(ktype, topic, content, now)

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    if knowledge_store.retrieve(ktype, eid) is not None:
        print(KNOWLEDGE_ALREADY_EXISTS_FMT.format(eid=eid), file=sys.stderr)
        return 1

    entry = KnowledgeEntry(
        id=eid,
        type=ktype,
        topic=topic,
        date=now,
        tags=_parse_tags(tags_raw),
        content=content,
        status="active",
        version=1,
        source_artifact=CLI_SOURCE_KNOWLEDGE_ADD,
    )
    knowledge_store.store(entry)
    print(KNOWLEDGE_ADDED_FMT.format(eid=eid))
    return 0


def _knowledge_edit(
    garage_root: Path,
    *,
    knowledge_type: str,
    eid: str,
    topic: Optional[str],
    content_arg: Optional[str],
    from_file: Optional[Path],
    tags_raw: Optional[str],
    status: Optional[str],
) -> int:
    """Implement ``garage knowledge edit`` (FR-503 / FR-509 / CON-503)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    # FR-503: at least one mutable field must be supplied.
    if (
        topic is None
        and content_arg is None
        and from_file is None
        and tags_raw is None
        and status is None
    ):
        print(ERR_EDIT_REQUIRES_FIELD, file=sys.stderr)
        return 1

    content, err = _resolve_content(content_arg, from_file, require_one=False)
    if err is not None:
        print(err, file=sys.stderr)
        return 1

    ktype = KnowledgeType(knowledge_type)
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entry = knowledge_store.retrieve(ktype, eid)
    if entry is None:
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1

    # Selective overlay per design §10.2.1. Untouched fields keep their
    # current value; CLI never modifies entry.date or publisher metadata.
    if topic is not None:
        entry.topic = topic
    if content is not None:
        entry.content = content
    if tags_raw is not None:
        entry.tags = _parse_tags(tags_raw)
    if status is not None:
        entry.status = status
    entry.source_artifact = CLI_SOURCE_KNOWLEDGE_EDIT

    knowledge_store.update(entry)  # mutates entry.version += 1 in place
    print(KNOWLEDGE_EDITED_FMT.format(eid=eid, version=entry.version))
    return 0


def _knowledge_show(
    garage_root: Path,
    *,
    knowledge_type: str,
    eid: str,
) -> int:
    """Implement ``garage knowledge show`` (FR-504)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    ktype = KnowledgeType(knowledge_type)
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entry = knowledge_store.retrieve(ktype, eid)
    if entry is None:
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1

    # Human-readable front matter dump (key: value), then a blank line, then
    # the body. Includes derived fields version + source_artifact (OD-504).
    tags_str = ", ".join(entry.tags) if entry.tags else ""
    print(f"id: {entry.id}")
    print(f"type: {entry.type.value}")
    print(f"topic: {entry.topic}")
    print(f"date: {entry.date.isoformat()}")
    print(f"tags: {tags_str}")
    print(f"status: {entry.status}")
    print(f"version: {entry.version}")
    if entry.source_artifact is not None:
        print(f"source_artifact: {entry.source_artifact}")
    print("")
    print(entry.content)
    return 0


def _knowledge_delete(
    garage_root: Path,
    *,
    knowledge_type: str,
    eid: str,
) -> int:
    """Implement ``garage knowledge delete`` (FR-505)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    ktype = KnowledgeType(knowledge_type)
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    if not knowledge_store.delete(ktype, eid):
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1
    print(KNOWLEDGE_DELETED_FMT.format(eid=eid))
    return 0


def _experience_add(
    garage_root: Path,
    *,
    task_type: str,
    skills: list[str],
    domain: str,
    outcome: str,
    duration: int,
    complexity: str,
    summary: str,
    explicit_id: Optional[str],
    problem_domain: Optional[str],
    tech: Optional[list[str]],
    tags_raw: Optional[str],
    now_provider: Callable[[], datetime] = _now_default,
) -> int:
    """Implement ``garage experience add`` (FR-506 / FR-508 experience / FR-509)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    now = now_provider()
    rid = explicit_id or _generate_experience_id(task_type, summary, now)

    storage = FileStorage(garage_dir)
    experience_index = ExperienceIndex(storage)

    if experience_index.retrieve(rid) is not None:
        print(EXPERIENCE_ALREADY_EXISTS_FMT.format(rid=rid), file=sys.stderr)
        return 1

    record = ExperienceRecord(
        record_id=rid,
        task_type=task_type,
        skill_ids=list(skills),
        tech_stack=list(tech) if tech else [],
        domain=domain,
        problem_domain=problem_domain or task_type,
        outcome=outcome,
        duration_seconds=duration,
        complexity=complexity,
        session_id="",
        artifacts=[CLI_SOURCE_EXPERIENCE_ADD],
        key_patterns=_parse_tags(tags_raw),
        lessons_learned=[summary],
        pitfalls=[],
        recommendations=[],
        created_at=now,
        updated_at=now,
    )
    experience_index.store(record)
    print(EXPERIENCE_ADDED_FMT.format(rid=rid))
    return 0


def _experience_show(garage_root: Path, *, rid: str) -> int:
    """Implement ``garage experience show`` (FR-507a).

    Reads the on-disk JSON file directly (instead of going through
    :py:meth:`ExperienceIndex.retrieve`) because we want to display the raw
    persisted shape — including the ``cli:experience-add`` source marker
    in ``artifacts[0]`` and any future fields that may not yet be on the
    ``ExperienceRecord`` dataclass. This keeps `show` fully forward
    compatible with schema additions on disk while still routing all
    *writes* through the public ``ExperienceIndex`` API (see
    ``_experience_add`` / ``_experience_delete``).
    """
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    record_path = garage_dir / "experience" / "records" / f"{rid}.json"
    if not record_path.is_file():
        print(EXPERIENCE_NOT_FOUND_FMT.format(rid=rid), file=sys.stderr)
        return 1

    try:
        data = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(EXPERIENCE_READ_ERR_FMT.format(rid=rid, err=exc), file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def _experience_delete(garage_root: Path, *, rid: str) -> int:
    """Implement ``garage experience delete`` (FR-507b)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    storage = FileStorage(garage_dir)
    experience_index = ExperienceIndex(storage)
    if not experience_index.delete(rid):
        print(EXPERIENCE_NOT_FOUND_FMT.format(rid=rid), file=sys.stderr)
        return 1
    print(EXPERIENCE_DELETED_FMT.format(rid=rid))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    # Create parent parser for common arguments
    path_parser = argparse.ArgumentParser(add_help=False)
    path_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Project root path (default: auto-detect)",
    )

    parser = argparse.ArgumentParser(
        prog="garage",
        description="Garage OS — Agent Operating System CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser(
        "init", help="Initialize .garage/ directory structure", parents=[path_parser]
    )

    # status
    status_parser = subparsers.add_parser(
        "status", help="Show Garage OS status", parents=[path_parser]
    )

    # run
    run_parser = subparsers.add_parser("run", help="Run a Garage skill", parents=[path_parser])
    run_parser.add_argument(
        "skill_name",
        help="Name of the skill to run",
    )
    run_parser.add_argument(
        "--timeout", type=int, default=300,
        help="Timeout in seconds (default: 300)",
    )

    # knowledge
    knowledge_parser = subparsers.add_parser(
        "knowledge", help="Manage knowledge entries", parents=[path_parser]
    )
    knowledge_subparsers = knowledge_parser.add_subparsers(dest="knowledge_command")

    # knowledge search
    search_parser = knowledge_subparsers.add_parser(
        "search", help="Search knowledge entries", parents=[path_parser]
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Search query text"
    )

    # knowledge list
    list_parser = knowledge_subparsers.add_parser(
        "list", help="List all knowledge entries", parents=[path_parser]
    )

    # F005: knowledge add / edit / show / delete (CLI authoring path)
    add_parser = knowledge_subparsers.add_parser(
        "add", help="Add a knowledge entry", parents=[path_parser]
    )
    add_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type (decision / pattern / solution)",
    )
    add_parser.add_argument("--topic", required=True, help="Entry topic (non-empty)")
    add_parser.add_argument("--content", default=None, help="Entry content (mutex with --from-file)")
    add_parser.add_argument(
        "--from-file",
        dest="from_file",
        type=Path,
        default=None,
        help="Read content from file (mutex with --content)",
    )
    add_parser.add_argument("--tags", default=None, help="Comma-separated tags")
    add_parser.add_argument(
        "--id",
        dest="entry_id",
        default=None,
        help="Explicit entry id (default: derived per FR-508)",
    )

    edit_parser = knowledge_subparsers.add_parser(
        "edit", help="Edit a knowledge entry (selective overlay)", parents=[path_parser]
    )
    edit_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type",
    )
    edit_parser.add_argument(
        "--id", dest="entry_id", required=True, help="Entry id (required)"
    )
    edit_parser.add_argument("--topic", default=None, help="New topic")
    edit_parser.add_argument(
        "--content", default=None, help="New content (mutex with --from-file)"
    )
    edit_parser.add_argument(
        "--from-file",
        dest="from_file",
        type=Path,
        default=None,
        help="Read new content from file (mutex with --content)",
    )
    edit_parser.add_argument("--tags", default=None, help="New comma-separated tags (overwrite)")
    edit_parser.add_argument("--status", default=None, help="New status")

    show_parser = knowledge_subparsers.add_parser(
        "show", help="Show a single knowledge entry", parents=[path_parser]
    )
    show_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type",
    )
    show_parser.add_argument(
        "--id", dest="entry_id", required=True, help="Entry id"
    )

    delete_parser = knowledge_subparsers.add_parser(
        "delete", help="Delete a knowledge entry", parents=[path_parser]
    )
    delete_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type",
    )
    delete_parser.add_argument(
        "--id", dest="entry_id", required=True, help="Entry id"
    )

    # F005: experience add / show / delete (CLI authoring path)
    experience_parser = subparsers.add_parser(
        "experience", help="Manage experience records", parents=[path_parser]
    )
    experience_subparsers = experience_parser.add_subparsers(dest="experience_command")

    exp_add_parser = experience_subparsers.add_parser(
        "add", help="Add an experience record", parents=[path_parser]
    )
    exp_add_parser.add_argument("--task-type", dest="task_type", required=True, help="Task type")
    exp_add_parser.add_argument(
        "--skill",
        dest="skills",
        action="append",
        required=True,
        help="Skill id (repeat for multiple)",
    )
    exp_add_parser.add_argument("--domain", required=True, help="Domain (e.g. platform)")
    exp_add_parser.add_argument(
        "--outcome",
        choices=["success", "failure", "partial"],
        required=True,
        help="Outcome",
    )
    exp_add_parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Duration in seconds",
    )
    exp_add_parser.add_argument(
        "--complexity",
        choices=["low", "medium", "high"],
        required=True,
        help="Complexity",
    )
    exp_add_parser.add_argument(
        "--summary",
        required=True,
        help="One-line summary (written to lessons_learned[0])",
    )
    exp_add_parser.add_argument(
        "--id",
        dest="record_id",
        default=None,
        help="Explicit record id (default: derived per FR-508)",
    )
    exp_add_parser.add_argument(
        "--problem-domain",
        dest="problem_domain",
        default=None,
        help="Problem domain (default: --task-type)",
    )
    exp_add_parser.add_argument(
        "--tech",
        dest="tech",
        action="append",
        default=None,
        help="Tech stack item (repeat for multiple)",
    )
    exp_add_parser.add_argument(
        "--tags",
        default=None,
        help="Comma-separated tags (written to key_patterns)",
    )

    exp_show_parser = experience_subparsers.add_parser(
        "show", help="Show a single experience record", parents=[path_parser]
    )
    exp_show_parser.add_argument(
        "--id", dest="record_id", required=True, help="Record id"
    )

    exp_delete_parser = experience_subparsers.add_parser(
        "delete", help="Delete an experience record", parents=[path_parser]
    )
    exp_delete_parser.add_argument(
        "--id", dest="record_id", required=True, help="Record id"
    )

    # memory
    memory_parser = subparsers.add_parser(
        "memory", help="Review memory candidate batches", parents=[path_parser]
    )
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")
    review_parser = memory_subparsers.add_parser(
        "review", help="Show candidate batch summary", parents=[path_parser]
    )
    review_parser.add_argument("batch_id", help="Candidate batch identifier")
    review_parser.add_argument(
        "--action",
        choices=[
            "accept",
            "edit_accept",
            "reject",
            "batch_reject",
            "defer",
            "abandon",
            "show-conflicts",
        ],
        default=None,
        help="Optional review action to apply",
    )
    review_parser.add_argument(
        "--candidate-id",
        default=None,
        help="Candidate identifier for single-candidate actions",
    )
    review_parser.add_argument("--title", default=None, help="Edited title for edit_accept")
    review_parser.add_argument("--summary", default=None, help="Edited summary for edit_accept")
    review_parser.add_argument("--content", default=None, help="Edited content for edit_accept")
    review_parser.add_argument("--tags", default=None, help="Comma-separated tags for edit_accept")
    review_parser.add_argument(
        "--strategy",
        choices=["coexist", "supersede", "abandon"],
        default=None,
        help="Conflict resolution strategy when accept hits similar published knowledge (FR-304)",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the Garage OS CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "init":
        root = args.path if args.path else Path.cwd()
        _init(root)
        return 0

    if args.command == "status":
        root = args.path if args.path else _find_garage_root()
        _status(root)
        return 0

    if args.command == "run":
        root = args.path if args.path else _find_garage_root()
        return _run(root, args.skill_name, timeout=args.timeout)

    if args.command == "knowledge":
        root = args.path if args.path else _find_garage_root()
        if args.knowledge_command == "search":
            _knowledge_search(root, args.query)
            return 0
        if args.knowledge_command == "list":
            _knowledge_list(root)
            return 0
        if args.knowledge_command == "add":
            return _knowledge_add(
                root,
                knowledge_type=args.entry_type,
                topic=args.topic,
                content_arg=args.content,
                from_file=args.from_file,
                tags_raw=args.tags,
                explicit_id=args.entry_id,
            )
        if args.knowledge_command == "edit":
            return _knowledge_edit(
                root,
                knowledge_type=args.entry_type,
                eid=args.entry_id,
                topic=args.topic,
                content_arg=args.content,
                from_file=args.from_file,
                tags_raw=args.tags,
                status=args.status,
            )
        if args.knowledge_command == "show":
            return _knowledge_show(
                root,
                knowledge_type=args.entry_type,
                eid=args.entry_id,
            )
        if args.knowledge_command == "delete":
            return _knowledge_delete(
                root,
                knowledge_type=args.entry_type,
                eid=args.entry_id,
            )
        print(
            "Knowledge command requires one of: "
            "search, list, add, edit, show, delete",
            file=sys.stderr,
        )
        return 1

    if args.command == "experience":
        root = args.path if args.path else _find_garage_root()
        if args.experience_command == "add":
            return _experience_add(
                root,
                task_type=args.task_type,
                skills=args.skills,
                domain=args.domain,
                outcome=args.outcome,
                duration=args.duration,
                complexity=args.complexity,
                summary=args.summary,
                explicit_id=args.record_id,
                problem_domain=args.problem_domain,
                tech=args.tech,
                tags_raw=args.tags,
            )
        if args.experience_command == "show":
            return _experience_show(root, rid=args.record_id)
        if args.experience_command == "delete":
            return _experience_delete(root, rid=args.record_id)
        print(
            "Experience command requires one of: add, show, delete",
            file=sys.stderr,
        )
        return 1

    if args.command == "memory":
        root = args.path if args.path else _find_garage_root()
        if args.memory_command == "review":
            return _memory_review(
                root,
                args.batch_id,
                action=args.action,
                candidate_id=args.candidate_id,
                title=args.title,
                summary=args.summary,
                content=args.content,
                tags=args.tags,
                strategy=args.strategy,
            )
        print("Memory command requires 'review' subcommand")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
