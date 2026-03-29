#!/usr/bin/env python3
"""
Unit tests for validate_retrospective_record.py
"""

import os
import subprocess
import sys

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "validate_retrospective_record.py")

VALID_RECORD = """\
---
date: "2026-03-24"
phase: worker
trigger_skill: long-task-tdd
category: skill-gap
severity: critical
classification: systemic
target_skill_file: skills/long-task-tdd/SKILL.md
target_section: Red-Green-Refactor
---

## User Feedback

The TDD skill failed to detect flaky tests.

## Root Cause Analysis

The skill does not re-run tests to confirm determinism.

## Suggested Improvement

Add a mandatory re-run step after Green phase.
"""


def run_validator(content):
    """Run validate_retrospective_record.py with given content, return (exit_code, stdout, stderr)."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


def test_valid_record():
    code, stdout, _ = run_validator(VALID_RECORD)
    assert code == 0, f"Expected exit 0: {stdout}"
    assert "VALID" in stdout


def test_valid_with_skill_output_instead_of_feedback():
    content = VALID_RECORD.replace("## User Feedback", "## Skill Output")
    code, stdout, _ = run_validator(content)
    assert code == 0, f"Expected exit 0: {stdout}"


def test_valid_with_both_feedback_and_output():
    content = VALID_RECORD.replace(
        "## User Feedback",
        "## User Feedback\n\nSome feedback.\n\n## Skill Output"
    )
    code, stdout, _ = run_validator(content)
    assert code == 0, f"Expected exit 0: {stdout}"


def test_missing_frontmatter():
    content = "# No frontmatter\n\nJust a plain markdown file."
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "frontmatter" in stdout.lower()


def test_missing_date():
    content = VALID_RECORD.replace('date: "2026-03-24"\n', "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "date" in stdout.lower()


def test_missing_phase():
    content = VALID_RECORD.replace("phase: worker\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "phase" in stdout.lower()


def test_missing_trigger_skill():
    content = VALID_RECORD.replace("trigger_skill: long-task-tdd\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "trigger_skill" in stdout.lower()


def test_missing_category():
    content = VALID_RECORD.replace("category: skill-gap\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "category" in stdout.lower()


def test_missing_severity():
    content = VALID_RECORD.replace("severity: critical\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "severity" in stdout.lower()


def test_missing_classification():
    content = VALID_RECORD.replace("classification: systemic\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "classification" in stdout.lower()


def test_missing_target_skill_file():
    content = VALID_RECORD.replace("target_skill_file: skills/long-task-tdd/SKILL.md\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "target_skill_file" in stdout.lower()


def test_missing_target_section():
    content = VALID_RECORD.replace("target_section: Red-Green-Refactor\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "target_section" in stdout.lower()


def test_invalid_category():
    content = VALID_RECORD.replace("category: skill-gap", "category: bad-category")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "category" in stdout.lower()
    assert "bad-category" in stdout


def test_invalid_severity():
    content = VALID_RECORD.replace("severity: critical", "severity: blocker")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "severity" in stdout.lower()
    assert "blocker" in stdout


def test_invalid_classification():
    content = VALID_RECORD.replace("classification: systemic", "classification: recurring")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "classification" in stdout.lower()
    assert "recurring" in stdout


def test_invalid_phase():
    content = VALID_RECORD.replace("phase: worker", "phase: design")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "phase" in stdout.lower()
    assert "design" in stdout


def test_trigger_skill_bad_prefix():
    content = VALID_RECORD.replace("trigger_skill: long-task-tdd", "trigger_skill: my-skill")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "trigger_skill" in stdout.lower()
    assert "long-task-" in stdout


def test_missing_required_body_section_root_cause():
    content = VALID_RECORD.replace("## Root Cause Analysis", "## Something Else")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "Root Cause Analysis" in stdout


def test_missing_required_body_section_suggested_improvement():
    content = VALID_RECORD.replace("## Suggested Improvement", "## Other Section")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "Suggested Improvement" in stdout


def test_missing_feedback_and_output():
    content = VALID_RECORD.replace("## User Feedback", "## Context")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "User Feedback" in stdout or "Skill Output" in stdout


def test_file_not_found():
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/file.md"],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "not found" in result.stdout.lower() or "not found" in result.stderr.lower()


def test_empty_file():
    code, stdout, _ = run_validator("")
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "empty" in stdout.lower()


def test_multiple_errors():
    # Remove category, severity, and classification — plus bad phase
    content = VALID_RECORD.replace("category: skill-gap\n", "")
    content = content.replace("severity: critical\n", "")
    content = content.replace("classification: systemic\n", "")
    code, stdout, _ = run_validator(content)
    assert code != 0, f"Expected non-zero: {stdout}"
    # Should report at least 3 errors
    assert "3 error" in stdout or "4 error" in stdout or "5 error" in stdout


def test_valid_all_phases():
    for phase in ["worker", "st", "hotfix", "increment"]:
        content = VALID_RECORD.replace("phase: worker", f"phase: {phase}")
        code, stdout, _ = run_validator(content)
        assert code == 0, f"Expected exit 0 for phase '{phase}': {stdout}"


def test_valid_all_categories():
    for cat in ["skill-gap", "missing-rule", "false-assumption", "template-defect", "process-gap"]:
        content = VALID_RECORD.replace("category: skill-gap", f"category: {cat}")
        code, stdout, _ = run_validator(content)
        assert code == 0, f"Expected exit 0 for category '{cat}': {stdout}"


def test_valid_all_severities():
    for sev in ["critical", "important", "minor"]:
        content = VALID_RECORD.replace("severity: critical", f"severity: {sev}")
        code, stdout, _ = run_validator(content)
        assert code == 0, f"Expected exit 0 for severity '{sev}': {stdout}"


def test_valid_all_classifications():
    for cls in ["systemic", "one-off"]:
        content = VALID_RECORD.replace("classification: systemic", f"classification: {cls}")
        code, stdout, _ = run_validator(content)
        assert code == 0, f"Expected exit 0 for classification '{cls}': {stdout}"


if __name__ == "__main__":
    tests = [
        test_valid_record,
        test_valid_with_skill_output_instead_of_feedback,
        test_valid_with_both_feedback_and_output,
        test_missing_frontmatter,
        test_missing_date,
        test_missing_phase,
        test_missing_trigger_skill,
        test_missing_category,
        test_missing_severity,
        test_missing_classification,
        test_missing_target_skill_file,
        test_missing_target_section,
        test_invalid_category,
        test_invalid_severity,
        test_invalid_classification,
        test_invalid_phase,
        test_trigger_skill_bad_prefix,
        test_missing_required_body_section_root_cause,
        test_missing_required_body_section_suggested_improvement,
        test_missing_feedback_and_output,
        test_file_not_found,
        test_empty_file,
        test_multiple_errors,
        test_valid_all_phases,
        test_valid_all_categories,
        test_valid_all_severities,
        test_valid_all_classifications,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
