#!/usr/bin/env python3
"""
Unit tests for check_devtools.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_devtools.py")


def run_checker(feature_data, feature_id=None, env_overrides=None):
    """Run check_devtools.py with given data, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(feature_data, f, indent=2)
        f.flush()
        tmp_path = f.name

    try:
        cmd = [sys.executable, SCRIPT_PATH, tmp_path]
        if feature_id is not None:
            cmd.extend(["--feature", str(feature_id)])

        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


def test_no_ui_features_skips():
    """No UI features should exit 0 and skip the check."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "core", "title": "Backend API",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["Step 1"], "dependencies": []}
        ]
    }
    code, stdout, _ = run_checker(data)
    assert code == 0, f"Expected 0 for no UI features: {stdout}"
    assert "skipped" in stdout.lower() or "no ui features" in stdout.lower()


def test_no_features_at_all_skips():
    """Empty features array should exit 0."""
    data = {"project": "test", "features": []}
    code, stdout, _ = run_checker(data)
    assert code == 0, f"Expected 0 for empty features: {stdout}"


def test_ui_feature_detected():
    """UI feature should be listed in output."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "frontend", "title": "Login Page",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["[devtools] verify login form"], "dependencies": [],
             "ui": True, "ui_entry": "/login"}
        ]
    }
    code, stdout, _ = run_checker(data)
    # Whether it passes or fails depends on Chrome being available,
    # but the output should list the UI feature
    assert "Login Page" in stdout, f"Should list UI feature: {stdout}"


def test_feature_filter_only_checks_target():
    """--feature should only consider the targeted feature."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "frontend", "title": "Login Page",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["[devtools] verify login form"], "dependencies": [],
             "ui": True},
            {"id": 2, "category": "core", "title": "Backend API",
             "description": "B", "priority": "high", "status": "failing",
             "verification_steps": ["Step 1"], "dependencies": []}
        ]
    }
    # Feature 2 is not a UI feature, so check should skip
    code, stdout, _ = run_checker(data, feature_id=2)
    assert code == 0, f"Expected 0 for non-UI feature filter: {stdout}"
    assert "no ui features" in stdout.lower() or "skipped" in stdout.lower()


def test_env_hint_detected():
    """Setting CHROME_DEVTOOLS_MCP_PORT should make detection succeed."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "frontend", "title": "Dashboard",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["[devtools] verify dashboard"], "dependencies": [],
             "ui": True}
        ]
    }
    code, stdout, _ = run_checker(data, env_overrides={"CHROME_DEVTOOLS_MCP_PORT": "9222"})
    assert code == 0, f"Expected 0 when CHROME_DEVTOOLS_MCP_PORT is set: {stdout}"
    assert "AVAILABLE" in stdout


def test_env_hint_remote_debugging_port():
    """Setting CHROME_REMOTE_DEBUGGING_PORT should also work."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "frontend", "title": "Settings",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["[devtools] verify settings page"], "dependencies": [],
             "ui": True}
        ]
    }
    code, stdout, _ = run_checker(data, env_overrides={"CHROME_REMOTE_DEBUGGING_PORT": "9222"})
    assert code == 0, f"Expected 0 when CHROME_REMOTE_DEBUGGING_PORT is set: {stdout}"
    assert "AVAILABLE" in stdout


def test_ui_false_not_counted():
    """Features with ui=false should not be counted as UI features."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "frontend", "title": "Static Page",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["Step 1"], "dependencies": [],
             "ui": False}
        ]
    }
    code, stdout, _ = run_checker(data)
    assert code == 0, f"Expected 0 for ui=false: {stdout}"


def test_ui_absent_not_counted():
    """Features without ui field should not be counted as UI features."""
    data = {
        "project": "test",
        "features": [
            {"id": 1, "category": "core", "title": "API",
             "description": "A", "priority": "high", "status": "failing",
             "verification_steps": ["Step 1"], "dependencies": []}
        ]
    }
    code, stdout, _ = run_checker(data)
    assert code == 0, f"Expected 0 when ui field absent: {stdout}"


def test_invalid_json_fails():
    """Invalid JSON file should fail gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json{{{")
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "ERROR" in result.stdout or "error" in result.stderr.lower()
    finally:
        os.unlink(tmp_path)


def test_nonexistent_file_fails():
    """Nonexistent file should fail gracefully."""
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, "/nonexistent/path.json"],
        capture_output=True, text=True
    )
    assert result.returncode != 0


if __name__ == "__main__":
    tests = [
        test_no_ui_features_skips,
        test_no_features_at_all_skips,
        test_ui_feature_detected,
        test_feature_filter_only_checks_target,
        test_env_hint_detected,
        test_env_hint_remote_debugging_port,
        test_ui_false_not_counted,
        test_ui_absent_not_counted,
        test_invalid_json_fails,
        test_nonexistent_file_fails,
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
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
