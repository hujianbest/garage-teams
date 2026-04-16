"""
Existing Skills compatibility verification – Garage Agent OS T21.

Scans all AHE skill directories under packs/ and verifies structural
integrity:
  1. Every skill directory contains a SKILL.md file.
  2. SKILL.md is readable and non-empty (has front-matter or a title).
  3. references/ directory exists (warning if missing – not all skills
     carry one yet).
  4. evals/ directory exists (may be empty).
  5. A summary report is printed via pytest reporting.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]  # → /mnt/e/workspace/Garage

SKILL_PACK_DIRS: list[Path] = [
    REPO_ROOT / "packs" / "coding" / "skills",
    REPO_ROOT / "packs" / "product-insights" / "skills",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _discover_skill_dirs() -> list[Path]:
    """Return a sorted list of every ahe-* skill directory."""
    dirs: list[Path] = []
    for pack_dir in SKILL_PACK_DIRS:
        if not pack_dir.is_dir():
            continue
        for child in sorted(pack_dir.iterdir()):
            if child.is_dir() and child.name.startswith("ahe-"):
                dirs.append(child)
    return dirs


def _has_front_matter(text: str) -> bool:
    """Return True if *text* starts with a YAML front-matter block."""
    return text.lstrip().startswith("---")


def _has_markdown_title(text: str) -> bool:
    """Return True if *text* contains at least one ATX-style heading."""
    return bool(re.search(r"^#{1,6}\s+\S", text, re.MULTILINE))


# Discover once at module level so pytest can parametrize.
_SKILL_DIRS = _discover_skill_dirs()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def skill_report() -> dict:
    """Accumulate results for the final summary report."""
    return {
        "total": 0,
        "passed": 0,
        "warnings": [],
        "failures": [],
    }


# ---------------------------------------------------------------------------
# Parametrised per-skill tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "skill_dir",
    _SKILL_DIRS,
    ids=[d.name for d in _SKILL_DIRS],
)
def test_skill_has_skill_md(skill_dir: Path, skill_report: dict) -> None:
    """Each skill directory must contain a SKILL.md file."""
    skill_report["total"] += 1
    skill_md = skill_dir / "SKILL.md"
    assert skill_md.is_file(), f"{skill_dir.name}: SKILL.md is missing"
    skill_report["passed"] += 1


@pytest.mark.parametrize(
    "skill_dir",
    _SKILL_DIRS,
    ids=[d.name for d in _SKILL_DIRS],
)
def test_skill_md_readable_and_nonempty(skill_dir: Path, skill_report: dict) -> None:
    """SKILL.md must be readable and contain front-matter or a heading."""
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    assert len(text.strip()) > 0, f"{skill_dir.name}: SKILL.md is empty"

    has_content = _has_front_matter(text) or _has_markdown_title(text)
    assert has_content, (
        f"{skill_dir.name}: SKILL.md has neither YAML front-matter "
        f"nor a Markdown heading"
    )


@pytest.mark.parametrize(
    "skill_dir",
    _SKILL_DIRS,
    ids=[d.name for d in _SKILL_DIRS],
)
def test_skill_has_evals_dir(skill_dir: Path, skill_report: dict) -> None:
    """Each skill must have an evals/ directory (may be empty)."""
    evals_dir = skill_dir / "evals"
    assert evals_dir.is_dir(), f"{skill_dir.name}: evals/ directory is missing"


@pytest.mark.parametrize(
    "skill_dir",
    _SKILL_DIRS,
    ids=[d.name for d in _SKILL_DIRS],
)
def test_skill_has_references_dir(skill_dir: Path, skill_report: dict) -> None:
    """Each skill should have a references/ directory (soft check – warning)."""
    refs_dir = skill_dir / "references"
    if not refs_dir.is_dir():
        skill_report["warnings"].append(
            f"{skill_dir.name}: references/ directory is missing"
        )


# ---------------------------------------------------------------------------
# Aggregate / summary test
# ---------------------------------------------------------------------------

def test_skill_count_report(skill_report: dict) -> None:
    """Print a summary report and verify we found a reasonable number of skills.

    The expected count is around 23 (17 coding + 6 product-insights).
    We use a generous range to avoid brittle failures when skills are added.
    """
    total = skill_report["total"]
    passed = skill_report["passed"]

    report_lines = [
        "",
        "=" * 60,
        "T21 — Existing Skills Compatibility Report",
        "=" * 60,
        f"  Skills scanned : {total}",
        f"  Checks passed  : {passed}",
        f"  Warnings       : {len(skill_report['warnings'])}",
        f"  Failures       : {len(skill_report['failures'])}",
    ]

    if skill_report["warnings"]:
        report_lines.append("")
        report_lines.append("  Warnings:")
        for w in skill_report["warnings"]:
            report_lines.append(f"    ⚠  {w}")

    if skill_report["failures"]:
        report_lines.append("")
        report_lines.append("  Failures:")
        for f in skill_report["failures"]:
            report_lines.append(f"    ✗  {f}")

    report_lines.append("=" * 60)
    report_lines.append("")

    print("\n".join(report_lines))

    # Sanity: we expect at least 20 AHE skills across both packs
    assert total >= 20, (
        f"Expected at least 20 AHE skills, found only {total}. "
        f"Check that skill directories exist."
    )
