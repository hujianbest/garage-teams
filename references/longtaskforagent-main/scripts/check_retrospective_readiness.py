#!/usr/bin/env python3
"""
Check if retrospective records exist for reporting.

Checks:
- docs/retrospectives/ directory exists
- Contains .md files (excluding reported/ subdirectory)

Usage:
    python check_retrospective_readiness.py [--retro-dir docs/retrospectives]

Exit codes:
    0 — records found (ready for retrospective)
    1 — no records found
"""

import argparse
import glob
import os
import sys


def check_readiness(retro_dir: str = "docs/retrospectives") -> dict:
    """
    Check whether retrospective records exist for reporting.

    Args:
        retro_dir: Path to the retrospectives directory.

    Returns:
        dict with keys:
            ready: bool
            record_count: int
            record_paths: list[str]
            issues: list[str]
    """
    result = {
        "ready": False,
        "record_count": 0,
        "record_paths": [],
        "issues": [],
    }

    if not os.path.isdir(retro_dir):
        result["issues"].append(f"Directory does not exist: {retro_dir}")
        return result

    # List .md files in top-level directory only (exclude subdirectories like reported/)
    md_files = sorted(glob.glob(os.path.join(retro_dir, "*.md")))

    result["record_count"] = len(md_files)
    result["record_paths"] = md_files

    if len(md_files) == 0:
        result["issues"].append("No retrospective records found.")
        return result

    result["ready"] = True
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Check retrospective readiness"
    )
    parser.add_argument(
        "--retro-dir",
        default="docs/retrospectives",
        help="Path to retrospectives directory (default: docs/retrospectives)",
    )
    args = parser.parse_args()

    result = check_readiness(args.retro_dir)

    if result["ready"]:
        print(f"Retrospective records: {result['record_count']}")
        sys.exit(0)
    else:
        print("No retrospective records found.")
        for issue in result["issues"]:
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
