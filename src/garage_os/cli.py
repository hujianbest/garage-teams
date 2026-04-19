"""Command-line interface for Garage OS."""

import argparse
import json
import time
from pathlib import Path
from typing import Optional, Sequence

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
from garage_os.types import SessionState


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
        elif args.knowledge_command == "list":
            _knowledge_list(root)
        else:
            print("Knowledge command requires 'search' or 'list' subcommand")
            return 1
        return 0

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
