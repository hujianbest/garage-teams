#!/usr/bin/env python3
"""
Unit tests for check_configs.py
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_configs.py")


def run_checker(feature_data, feature_id=None, env_overrides=None, dotenv_path=None):
    """Run check_configs.py with given data, return (exit_code, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(feature_data, f, indent=2)
        f.flush()
        tmp_path = f.name

    try:
        cmd = [sys.executable, SCRIPT_PATH, tmp_path]
        if feature_id is not None:
            cmd.extend(["--feature", str(feature_id)])
        if dotenv_path is not None:
            cmd.extend(["--dotenv", dotenv_path])

        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(tmp_path)


def test_no_required_configs():
    """No required_configs key should exit 0."""
    data = {"project": "test", "features": []}
    code, stdout, _ = run_checker(data)
    assert code == 0, f"Expected 0: {stdout}"


def test_empty_required_configs():
    """Empty required_configs array should exit 0."""
    data = {"project": "test", "required_configs": [], "features": []}
    code, stdout, _ = run_checker(data)
    assert code == 0, f"Expected 0: {stdout}"


def test_env_config_present():
    """Env config with variable set should pass."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "Test Key", "type": "env", "key": "TEST_CHECK_CONFIG_VAR",
             "description": "Test", "required_by": [1]}
        ],
        "features": [{"id": 1}]
    }
    code, stdout, _ = run_checker(data, env_overrides={"TEST_CHECK_CONFIG_VAR": "some-value"})
    assert code == 0, f"Expected 0 when env var is set: {stdout}"


def test_env_config_missing():
    """Env config with variable not set should fail."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "Missing Key", "type": "env", "key": "DEFINITELY_NOT_SET_XYZ_12345",
             "description": "Test", "required_by": [1], "check_hint": "Set it!"}
        ],
        "features": [{"id": 1}]
    }
    # Ensure the variable is not set
    env = os.environ.copy()
    env.pop("DEFINITELY_NOT_SET_XYZ_12345", None)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode != 0, f"Expected non-zero: {result.stdout}"
        assert "MISSING" in result.stdout
        assert "Set it!" in result.stdout
    finally:
        os.unlink(tmp_path)


def test_file_config_present():
    """File config pointing to an existing non-empty file should pass."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as cfg:
        cfg.write("db_host: localhost\n")
        cfg_path = cfg.name

    try:
        data = {
            "project": "test",
            "required_configs": [
                {"name": "DB Config", "type": "file", "path": cfg_path,
                 "description": "Test", "required_by": [1]}
            ],
            "features": [{"id": 1}]
        }
        code, stdout, _ = run_checker(data)
        assert code == 0, f"Expected 0 when file exists: {stdout}"
    finally:
        os.unlink(cfg_path)


def test_file_config_missing():
    """File config pointing to non-existent file should fail."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "Missing File", "type": "file", "path": "/nonexistent/path/xyz.yml",
             "description": "Test", "required_by": [1], "check_hint": "Create it!"}
        ],
        "features": [{"id": 1}]
    }
    code, stdout, _ = run_checker(data)
    assert code != 0, f"Expected non-zero: {stdout}"
    assert "MISSING" in stdout


def test_feature_filter():
    """--feature flag should only check configs for that feature."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "Config A", "type": "env", "key": "DEFINITELY_NOT_SET_A_98765",
             "description": "For feature 1", "required_by": [1]},
            {"name": "Config B", "type": "env", "key": "TEST_FILTER_CONFIG_B",
             "description": "For feature 2", "required_by": [2]}
        ],
        "features": [{"id": 1}, {"id": 2}]
    }
    # Check for feature 2 only — Config A (feature 1) should not cause failure
    env = os.environ.copy()
    env.pop("DEFINITELY_NOT_SET_A_98765", None)
    env["TEST_FILTER_CONFIG_B"] = "set"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path, "--feature", "2"],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 0, f"Expected 0 for feature 2 with its config set: {result.stdout}"
    finally:
        os.unlink(tmp_path)


def test_mixed_present_and_missing():
    """Mix of present and missing configs should fail with details."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as cfg:
        cfg.write("content\n")
        cfg_path = cfg.name

    try:
        data = {
            "project": "test",
            "required_configs": [
                {"name": "Good File", "type": "file", "path": cfg_path,
                 "description": "Present", "required_by": [1]},
                {"name": "Bad Env", "type": "env", "key": "DEFINITELY_NOT_SET_XYZ_MIX",
                 "description": "Missing", "required_by": [1]}
            ],
            "features": [{"id": 1}]
        }
        env = os.environ.copy()
        env.pop("DEFINITELY_NOT_SET_XYZ_MIX", None)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f, indent=2)
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, SCRIPT_PATH, tmp_path],
                capture_output=True, text=True, env=env
            )
            assert result.returncode != 0
            assert "PRESENT" in result.stdout
            assert "MISSING" in result.stdout
        finally:
            os.unlink(tmp_path)
    finally:
        os.unlink(cfg_path)


def test_dotenv_loads_env_vars():
    """--dotenv flag should load env vars from .env file, making configs pass."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "API Key", "type": "env", "key": "DOTENV_TEST_API_KEY_ABC",
             "description": "Test API key", "required_by": [1]}
        ],
        "features": [{"id": 1}]
    }
    # Create a .env file with the required variable
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as dotenv:
        dotenv.write("# Test dotenv\nDOTENV_TEST_API_KEY_ABC=my-secret-key\n")
        dotenv_path = dotenv.name

    # Ensure the env var is NOT set in the process environment
    env = os.environ.copy()
    env.pop("DOTENV_TEST_API_KEY_ABC", None)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path, "--dotenv", dotenv_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 0, f"Expected 0 with dotenv: {result.stdout}"
        assert "Loaded 1 variable" in result.stdout
    finally:
        os.unlink(tmp_path)
        os.unlink(dotenv_path)


def test_dotenv_missing_file_ignored():
    """--dotenv pointing to non-existent file should not crash."""
    data = {"project": "test", "required_configs": [], "features": []}
    code, stdout, _ = run_checker(data, dotenv_path="/nonexistent/.env")
    assert code == 0, f"Expected 0: {stdout}"


def test_dotenv_quoted_values():
    """--dotenv should handle single-quoted, double-quoted, and unquoted values."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "Key A", "type": "env", "key": "DOTENV_TEST_QUOTED_A",
             "description": "Double-quoted", "required_by": [1]},
            {"name": "Key B", "type": "env", "key": "DOTENV_TEST_QUOTED_B",
             "description": "Single-quoted", "required_by": [1]},
            {"name": "Key C", "type": "env", "key": "DOTENV_TEST_QUOTED_C",
             "description": "Unquoted", "required_by": [1]}
        ],
        "features": [{"id": 1}]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as dotenv:
        dotenv.write('DOTENV_TEST_QUOTED_A="double-val"\n')
        dotenv.write("DOTENV_TEST_QUOTED_B='single-val'\n")
        dotenv.write("DOTENV_TEST_QUOTED_C=plain-val\n")
        dotenv_path = dotenv.name

    env = os.environ.copy()
    for k in ("DOTENV_TEST_QUOTED_A", "DOTENV_TEST_QUOTED_B", "DOTENV_TEST_QUOTED_C"):
        env.pop(k, None)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path, "--dotenv", dotenv_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 0, f"Expected 0 with quoted dotenv: {result.stdout}"
        assert "Loaded 3 variable" in result.stdout
    finally:
        os.unlink(tmp_path)
        os.unlink(dotenv_path)


def test_dotenv_comments_and_blanks():
    """--dotenv should skip comments and blank lines."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "Key X", "type": "env", "key": "DOTENV_TEST_COMMENT_X",
             "description": "Test", "required_by": [1]}
        ],
        "features": [{"id": 1}]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as dotenv:
        dotenv.write("# This is a comment\n")
        dotenv.write("\n")
        dotenv.write("   \n")
        dotenv.write("DOTENV_TEST_COMMENT_X=works\n")
        dotenv.write("# Another comment\n")
        dotenv_path = dotenv.name

    env = os.environ.copy()
    env.pop("DOTENV_TEST_COMMENT_X", None)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path, "--dotenv", dotenv_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode == 0, f"Expected 0: {result.stdout}"
        assert "Loaded 1 variable" in result.stdout
    finally:
        os.unlink(tmp_path)
        os.unlink(dotenv_path)


def test_missing_env_shows_dotenv_key():
    """Missing env config should show .env key in output."""
    data = {
        "project": "test",
        "required_configs": [
            {"name": "API Key", "type": "env", "key": "MISSING_KEY_FOR_DOTENV_TEST",
             "description": "Test", "required_by": [1]}
        ],
        "features": [{"id": 1}]
    }
    env = os.environ.copy()
    env.pop("MISSING_KEY_FOR_DOTENV_TEST", None)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_PATH, tmp_path],
            capture_output=True, text=True, env=env
        )
        assert result.returncode != 0
        assert ".env key: MISSING_KEY_FOR_DOTENV_TEST" in result.stdout
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    tests = [
        test_no_required_configs,
        test_empty_required_configs,
        test_env_config_present,
        test_env_config_missing,
        test_file_config_present,
        test_file_config_missing,
        test_feature_filter,
        test_mixed_present_and_missing,
        test_dotenv_loads_env_vars,
        test_dotenv_missing_file_ignored,
        test_dotenv_quoted_values,
        test_dotenv_comments_and_blanks,
        test_missing_env_shows_dotenv_key,
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
