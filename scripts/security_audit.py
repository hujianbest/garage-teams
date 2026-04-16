#!/usr/bin/env python3
"""Security Audit Script for Garage Agent OS (T19).

Performs four security checks:
  1. Sensitive-data scan in .garage/ (API key / password / token patterns)
  2. .gitignore coverage for .env, *.key, credentials.*
  3. ToolGateway rejection rate for non-whitelisted tools (must be 100%)
  4. session.json credential-free verification

Exit code 0 when all checks pass, 1 on failure.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GARAGE_DIR = PROJECT_ROOT / ".garage"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"

# Patterns that indicate leaked secrets in text files.
SENSITIVE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"(?i)api[_\-]?key\s*[:=]\s*['\"]?\S{8,}"),
    re.compile(r"(?i)secret[_\-]?key\s*[:=]\s*['\"]?\S{8,}"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?\S{4,}"),
    re.compile(r"(?i)token\s*[:=]\s*['\"]?\S{8,}"),
    re.compile(r"(?i)bearer\s+\S{16,}"),
    re.compile(r"(?i)private[_\-]?key\s*[:=]\s*['\"]?\S{16,}"),
    re.compile(r"(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[:=]\s*\S{8,}"),
    re.compile(r"(?i)credentials\s*[:=]\s*['\"]?\S{8,}"),
]

# Gitignore entries that MUST be present.
REQUIRED_GITIGNORE_ENTRIES = [
    ".env",
    "*.key",
    "credentials.*",
]

# Whitelist used to verify ToolGateway behaviour.
TOOL_WHITELIST = ["read_file", "search_files", "list_dir"]

# Non-whitelisted tools used for rejection-rate verification.
NON_WHITELISTED_TOOLS = [
    "rm_rf",
    "shell_exec",
    "delete_database",
    "format_disk",
    "sudo",
    "netcat_reverse_shell",
]

# Credential-like keys that must NOT appear in session.json.
CREDENTIAL_KEY_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"(?i)api[_\-]?key"),
    re.compile(r"(?i)password"),
    re.compile(r"(?i)secret"),
    re.compile(r"(?i)token"),
    re.compile(r"(?i)private[_\-]?key"),
    re.compile(r"(?i)credentials"),
]

# ---------------------------------------------------------------------------
# Check 1: Sensitive data scan
# ---------------------------------------------------------------------------


def scan_sensitive_data(garage_dir: Path) -> Tuple[bool, List[str]]:
    """Scan .garage/ for files containing sensitive patterns.

    Returns (passed, findings).
    """
    findings: List[str] = []

    if not garage_dir.exists():
        return True, [f"⚠ {garage_dir} does not exist — skipping scan."]

    text_extensions = {".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".cfg", ".ini"}
    for filepath in garage_dir.rglob("*"):
        if not filepath.is_file():
            continue
        if filepath.suffix not in text_extensions:
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            for pat in SENSITIVE_PATTERNS:
                m = pat.search(line)
                if m:
                    rel = filepath.relative_to(PROJECT_ROOT)
                    findings.append(
                        f"  {rel}:{lineno} — matches pattern '{pat.pattern[:40]}…': {m.group()}"
                    )

    passed = len(findings) == 0
    return passed, findings


# ---------------------------------------------------------------------------
# Check 2: .gitignore coverage
# ---------------------------------------------------------------------------


def verify_gitignore(gitignore_path: Path) -> Tuple[bool, List[str]]:
    """Verify required entries exist in .gitignore.

    Returns (passed, issues).
    """
    issues: List[str] = []

    if not gitignore_path.exists():
        return False, [f"✗ .gitignore not found at {gitignore_path}"]

    content = gitignore_path.read_text(encoding="utf-8")
    lines = [l.strip() for l in content.splitlines()]

    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry not in lines:
            issues.append(f"  Missing required entry: {entry}")

    passed = len(issues) == 0
    return passed, issues


# ---------------------------------------------------------------------------
# Check 3: ToolGateway rejection rate
# ---------------------------------------------------------------------------


def verify_tool_gateway_rejection() -> Tuple[bool, List[str]]:
    """Verify that ToolGateway rejects 100% of non-whitelisted tools.

    Returns (passed, details).
    """
    # Import inline so the script can be run independently.
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from garage_os.tools.tool_gateway import ToolGateway  # type: ignore[import-untyped]

    details: List[str] = []
    gw = ToolGateway(whitelist=TOOL_WHITELIST)

    denied_count = 0
    for tool_id in NON_WHITELISTED_TOOLS:
        allowed = gw.check_permission(tool_id)
        if not allowed:
            denied_count += 1
        else:
            details.append(f"  ✗ Non-whitelisted tool '{tool_id}' was ALLOWED")

    total = len(NON_WHITELISTED_TOOLS)
    rate = denied_count / total * 100 if total else 0
    passed = denied_count == total

    details.append(
        f"  Rejection rate: {denied_count}/{total} ({rate:.1f}%)"
    )
    return passed, details


# ---------------------------------------------------------------------------
# Check 4: session.json credential-free
# ---------------------------------------------------------------------------


def scan_session_json_for_credentials() -> Tuple[bool, List[str]]:
    """Find session.json files under .garage/ and verify they contain no credentials.

    Returns (passed, findings).
    """
    findings: List[str] = []

    for session_file in GARAGE_DIR.rglob("session.json"):
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"  ⚠ Cannot parse {session_file}: {exc}")
            continue

        # Recursively check all dict keys.
        _check_dict_keys(data, str(session_file.relative_to(PROJECT_ROOT)), findings)

    if not findings:
        # No session.json files found is also a pass — nothing to leak.
        pass

    passed = len(findings) == 0
    return passed, findings


def _check_dict_keys(
    obj: object, path: str, findings: List[str], _depth: int = 0
) -> None:
    """Recursively check dict keys for credential-like names."""
    if _depth > 20:
        return  # safety guard
    if isinstance(obj, dict):
        for key, value in obj.items():
            for pat in CREDENTIAL_KEY_PATTERNS:
                if pat.search(str(key)):
                    findings.append(f"  {path} → key '{key}' matches credential pattern")
                    break
            _check_dict_keys(value, f"{path}.{key}", findings, _depth + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_dict_keys(item, f"{path}[{i}]", findings, _depth + 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_audit() -> bool:
    """Execute all checks and print a report. Returns True if all pass."""
    checks = [
        ("1. Sensitive-data scan (.garage/)", scan_sensitive_data, GARAGE_DIR),
        ("2. .gitignore coverage", verify_gitignore, GITIGNORE_PATH),
        ("3. ToolGateway rejection rate", verify_tool_gateway_rejection, None),
        ("4. session.json credential-free", scan_session_json_for_credentials, None),
    ]

    all_passed = True
    print("=" * 60)
    print("  Garage Agent OS — Security Audit (T19)")
    print("=" * 60)

    for title, fn, arg in checks:
        print(f"\n► {title}")
        if arg is not None:
            passed, details = fn(arg)
        else:
            passed, details = fn()

        status = "PASS ✓" if passed else "FAIL ✗"
        print(f"  {status}")
        for line in details:
            print(line)

        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    overall = "ALL CHECKS PASSED ✓" if all_passed else "SOME CHECKS FAILED ✗"
    print(f"  {overall}")
    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    ok = run_audit()
    sys.exit(0 if ok else 1)
