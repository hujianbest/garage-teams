"""Command-line interface for Garage OS."""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from garage_os.storage import FileStorage
from garage_os.storage.file_storage import FileStorage
from garage_os.adapter.claude_code_adapter import ClaudeCodeAdapter
from garage_os.runtime.session_manager import SessionManager
from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
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
    "sessions/active",
    "sessions/archived",
]

GARAGE_README = """# .garage/ — Garage OS Runtime Data

This directory contains all runtime data for Garage OS.

- **config/**: Platform and adapter configurations
- **contracts/**: Interface contracts
- **knowledge/**: Knowledge entries (decisions, patterns, solutions)
- **experience/**: Experience records
- **sessions/**: Active and archived sessions
"""


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

    print(f"Initialized Garage OS in {garage_dir}")


def _status(garage_root: Path) -> None:
    """Read .garage/ and display statistics."""
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)

    # Count sessions
    active_sessions = storage.list_files("sessions/active", "*.json")
    archived_sessions = storage.list_files("sessions/archived", "*.json")
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
            recent_experience = data.get("timestamp", str(latest))
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


def _run(garage_root: Path, skill_name: str, timeout: int = 300) -> None:
    """Run a Garage skill and record the experience.

    Args:
        garage_root: Path to the project root
        skill_name: Name of the skill to invoke
        timeout: Timeout in seconds for Claude Code execution
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)

    # Create session manager and start a new session
    session_manager = SessionManager(storage)
    session = session_manager.create_session(
        pack_id=skill_name,
        topic=f"Run skill: {skill_name}",
        user_goals=[],
        constraints=[],
    )

    # Create adapter and invoke the skill
    adapter = ClaudeCodeAdapter(garage_root, timeout=timeout)

    start_time = time.time()
    outcome = "success"
    exit_code = 0
    output = ""

    try:
        result = adapter.invoke_skill(skill_name)
        output = result.get("output", "")
        exit_code = result.get("exit_code", 0)

        if not result.get("success", False):
            outcome = "failure"
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
        _run(root, args.skill_name, timeout=args.timeout)
        return 0

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

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
