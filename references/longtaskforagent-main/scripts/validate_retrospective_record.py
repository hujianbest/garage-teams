#!/usr/bin/env python3
"""
Validate retrospective record markdown structure.

Checks:
- Valid markdown with YAML frontmatter (--- delimited)
- Required frontmatter fields present with correct types
- category is one of the allowed enum values
- severity is one of the allowed enum values
- classification is one of the allowed enum values
- Required sections present in the body

Usage:
    python validate_retrospective_record.py <path/to/record.md>

Exit codes:
    0 — valid
    1 — invalid (errors printed to stdout)
"""

import sys


VALID_PHASES = {"worker", "st", "hotfix", "increment"}
VALID_CATEGORIES = {"skill-gap", "missing-rule", "false-assumption", "template-defect", "process-gap"}
VALID_SEVERITIES = {"critical", "important", "minor"}
VALID_CLASSIFICATIONS = {"systemic", "one-off"}

REQUIRED_FIELDS = [
    "date",
    "phase",
    "trigger_skill",
    "category",
    "severity",
    "classification",
    "target_skill_file",
    "target_section",
]


def _parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body) or (None, "") if no frontmatter found.
    """
    lines = content.split("\n")

    # First line must be ---
    if not lines or lines[0].strip() != "---":
        return None, ""

    # Find the closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, ""

    # Parse key: value pairs
    frontmatter = {}
    for line in lines[1:end_idx]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon_idx = line.find(":")
        if colon_idx == -1:
            continue
        key = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        frontmatter[key] = value

    body = "\n".join(lines[end_idx + 1:])
    return frontmatter, body


def validate(path: str) -> list[str]:
    """Validate retrospective record markdown. Returns list of errors."""
    errors = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return [f"File not found: {path}"]

    if not content.strip():
        return ["File is empty"]

    frontmatter, body = _parse_frontmatter(content)

    if frontmatter is None:
        return ["Missing or malformed YAML frontmatter (must be delimited by --- lines)"]

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(f"Missing required frontmatter field: '{field}'")
        elif not frontmatter[field].strip():
            errors.append(f"'{field}' must not be empty")

    # Check phase enum
    phase = frontmatter.get("phase", "").strip()
    if phase and phase not in VALID_PHASES:
        errors.append(
            f"'phase' must be one of {sorted(VALID_PHASES)}, got '{phase}'"
        )

    # Check trigger_skill prefix
    trigger_skill = frontmatter.get("trigger_skill", "").strip()
    if trigger_skill and not trigger_skill.startswith("long-task-"):
        errors.append(
            f"'trigger_skill' must start with 'long-task-', got '{trigger_skill}'"
        )

    # Check category enum
    category = frontmatter.get("category", "").strip()
    if category and category not in VALID_CATEGORIES:
        errors.append(
            f"'category' must be one of {sorted(VALID_CATEGORIES)}, got '{category}'"
        )

    # Check severity enum
    severity = frontmatter.get("severity", "").strip()
    if severity and severity not in VALID_SEVERITIES:
        errors.append(
            f"'severity' must be one of {sorted(VALID_SEVERITIES)}, got '{severity}'"
        )

    # Check classification enum
    classification = frontmatter.get("classification", "").strip()
    if classification and classification not in VALID_CLASSIFICATIONS:
        errors.append(
            f"'classification' must be one of {sorted(VALID_CLASSIFICATIONS)}, got '{classification}'"
        )

    # Check required body sections
    body_lines = body.split("\n")
    headings = [line.strip() for line in body_lines if line.strip().startswith("## ")]
    heading_titles = [h[3:].strip() for h in headings]

    has_feedback_or_output = any(
        title in ("User Feedback", "Skill Output") for title in heading_titles
    )
    if not has_feedback_or_output:
        errors.append(
            "Missing required section: '## User Feedback' or '## Skill Output' (at least one required)"
        )

    if "Root Cause Analysis" not in heading_titles:
        errors.append("Missing required section: '## Root Cause Analysis'")

    if "Suggested Improvement" not in heading_titles:
        errors.append("Missing required section: '## Suggested Improvement'")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_retrospective_record.py <path/to/record.md>")
        sys.exit(1)

    errors = validate(sys.argv[1])

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("VALID — retrospective record structure OK")
        sys.exit(0)


if __name__ == "__main__":
    main()
