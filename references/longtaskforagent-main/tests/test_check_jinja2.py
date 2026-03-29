#!/usr/bin/env python3
"""Unit tests for check_jinja2.py"""

import os
import subprocess
import sys

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_jinja2.py")


def run_checker(env_overrides=None, extra_args=None):
    """Run check_jinja2.py, return (exit_code, stdout, stderr)."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    cmd = [sys.executable, SCRIPT_PATH]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
    return result.returncode, result.stdout, result.stderr


class TestCheckJinja2:
    def test_jinja2_available(self):
        """When jinja2 is installed, exit 0 and report AVAILABLE."""
        code, stdout, _ = run_checker()
        assert code == 0
        assert "AVAILABLE" in stdout

    def test_quiet_mode_suppresses_output(self):
        """--quiet suppresses output on success."""
        code, stdout, _ = run_checker(extra_args=["--quiet"])
        assert code == 0
        assert stdout.strip() == ""

    def test_missing_jinja2_function_result(self):
        """When jinja2 import fails, check_jinja2() reports not available."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from check_jinja2 import check_jinja2
        from unittest.mock import patch

        # Simulate ImportError by patching builtins.__import__
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def blocked_import(name, *args, **kwargs):
            if name == "jinja2":
                raise ImportError("blocked by test")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked_import):
            result = check_jinja2()

        assert result["available"] is False
        assert result["version"] is None
        assert "not found" in result["detail"]


class TestCheckJinja2Function:
    """Test the check_jinja2() function directly."""

    def test_function_returns_dict(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from check_jinja2 import check_jinja2
        result = check_jinja2()
        assert isinstance(result, dict)
        assert "available" in result
        assert "version" in result
        assert "detail" in result

    def test_function_available_when_installed(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from check_jinja2 import check_jinja2
        result = check_jinja2()
        # jinja2 is installed in our test environment
        assert result["available"] is True
        assert result["version"] is not None
