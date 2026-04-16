"""Command-line interface for Garage OS."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from garage_os.storage import FileStorage


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


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="garage",
        description="Garage OS — Agent Operating System CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize .garage/ directory structure")
    init_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Project root path (default: auto-detect)",
    )

    # status
    status_parser = subparsers.add_parser("status", help="Show Garage OS status")
    status_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Project root path (default: auto-detect)",
    )

    # run — placeholder
    subparsers.add_parser("run", help="Run a Garage skill (not yet implemented)")

    # knowledge — placeholder
    subparsers.add_parser("knowledge", help="Manage knowledge entries (not yet implemented)")

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
        print("Run command is not yet implemented.")
        return 0

    if args.command == "knowledge":
        print("Knowledge command is not yet implemented.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
