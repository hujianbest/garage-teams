"""
Tests for HostAdapterProtocol and ClaudeCodeAdapter.

Test design seeds:
  1) invoke_skill correctly passes parameters
  2) read_file through the adapter
  3) write_file through the adapter
  4) get_repository_state returns git status
  5) Mock adapter swap proves host-agnosticism
  6) Error propagation / conversion
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from garage_os.adapter.claude_code_adapter import (
    AdapterError,
    ClaudeCodeAdapter,
    SkillExecutionError,
    SkillNotFoundError,
)
from garage_os.adapter.host_adapter import HostAdapterProtocol


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with basic structure."""
    # .agents/skills/demo-skill/SKILL.md
    skill_dir = tmp_path / ".agents" / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Demo Skill\nA test skill.", encoding="utf-8"
    )

    # A sample file for reading
    (tmp_path / "hello.txt").write_text("Hello, world!", encoding="utf-8")

    return tmp_path


@pytest.fixture()
def adapter(workspace: Path) -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter(workspace)


# ---------------------------------------------------------------------------
# 1) invoke_skill correctly passes parameters
# ---------------------------------------------------------------------------


class TestInvokeSkill:
    def test_invoke_skill_returns_success(self, adapter: ClaudeCodeAdapter) -> None:
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["claude", "-p", "prompt"],
                returncode=0,
                stdout="skill output",
                stderr="",
            )
            result = adapter.invoke_skill(
                "demo-skill",
                params={"key": "value", "count": 42},
            )
        assert result["success"] is True
        assert result["output"] == "skill output"
        assert result["exit_code"] == 0

    def test_invoke_skill_default_params(self, adapter: ClaudeCodeAdapter) -> None:
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["claude", "-p", "prompt"],
                returncode=0,
                stdout="ok",
                stderr="",
            )
            result = adapter.invoke_skill("demo-skill")
        assert result["success"] is True

    def test_invoke_skill_not_found(self, adapter: ClaudeCodeAdapter) -> None:
        with pytest.raises(SkillNotFoundError, match="nonexistent-skill"):
            adapter.invoke_skill("nonexistent-skill")

    def test_invoke_skill_error_is_adapter_error(self, adapter: ClaudeCodeAdapter) -> None:
        """SkillNotFoundError should be a subclass of AdapterError."""
        with pytest.raises(AdapterError):
            adapter.invoke_skill("nope")


# ---------------------------------------------------------------------------
# 2) read_file through the adapter
# ---------------------------------------------------------------------------


class TestReadFile:
    def test_read_existing_file(self, adapter: ClaudeCodeAdapter, workspace: Path) -> None:
        content = adapter.read_file("hello.txt")
        assert content == "Hello, world!"

    def test_read_with_absolute_path(self, adapter: ClaudeCodeAdapter, workspace: Path) -> None:
        abs_path = workspace / "hello.txt"
        content = adapter.read_file(abs_path)
        assert content == "Hello, world!"

    def test_read_file_not_found(self, adapter: ClaudeCodeAdapter) -> None:
        with pytest.raises(FileNotFoundError):
            adapter.read_file("does_not_exist.txt")


# ---------------------------------------------------------------------------
# 3) write_file through the adapter
# ---------------------------------------------------------------------------


class TestWriteFile:
    def test_write_new_file(self, adapter: ClaudeCodeAdapter, workspace: Path) -> None:
        result_path = adapter.write_file("output.txt", "written content")
        assert Path(result_path).exists()
        assert Path(result_path).read_text(encoding="utf-8") == "written content"

    def test_write_creates_parent_dirs(
        self, adapter: ClaudeCodeAdapter, workspace: Path
    ) -> None:
        adapter.write_file("deep/nested/dir/file.txt", "deep")
        assert (workspace / "deep" / "nested" / "dir" / "file.txt").read_text() == "deep"

    def test_write_overwrites_existing(
        self, adapter: ClaudeCodeAdapter, workspace: Path
    ) -> None:
        adapter.write_file("hello.txt", "overwritten")
        assert adapter.read_file("hello.txt") == "overwritten"


# ---------------------------------------------------------------------------
# 4) get_repository_state returns git status
# ---------------------------------------------------------------------------


def _init_git(workspace: Path) -> None:
    """Initialise a minimal git repo in *workspace*."""
    subprocess.run(["git", "init"], cwd=str(workspace), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(workspace), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(workspace), check=True, capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=str(workspace), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(workspace), check=True, capture_output=True,
    )


class TestGetRepositoryState:
    def test_returns_git_state(self, adapter: ClaudeCodeAdapter, workspace: Path) -> None:
        """Init a git repo in workspace and verify state keys."""
        _init_git(workspace)

        state = adapter.get_repository_state()
        assert "branch" in state
        assert "commit" in state
        assert "dirty" in state
        assert "status" in state
        # A fresh commit with no changes should not be dirty
        assert state["dirty"] is False
        # Commit should be a non-empty hex string
        assert len(state["commit"]) >= 7

    def test_detects_dirty_state(self, adapter: ClaudeCodeAdapter, workspace: Path) -> None:
        """After writing a new untracked file, dirty should be True."""
        _init_git(workspace)

        # Create an untracked file
        adapter.write_file("untracked.txt", "I am new")
        state = adapter.get_repository_state()
        assert state["dirty"] is True

    def test_git_not_available_raises_runtime_error(
        self, adapter: ClaudeCodeAdapter, workspace: Path
    ) -> None:
        """If git subprocess fails, a RuntimeError should be raised."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            with pytest.raises(RuntimeError, match="git is not available"):
                adapter.get_repository_state()


# ---------------------------------------------------------------------------
# 5) Mock adapter swap — proves host-agnosticism
# ---------------------------------------------------------------------------


class MockAdapter:
    """A lightweight mock that satisfies HostAdapterProtocol."""

    def __init__(self, file_store: dict[str, str] | None = None) -> None:
        self._store: dict[str, str] = file_store or {}
        self._invocations: list[dict[str, Any]] = []

    def invoke_skill(
        self, skill_name: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._invocations.append({"skill": skill_name, "params": params})
        return {"status": "success", "result": f"mock-{skill_name}"}

    def read_file(self, path: str | Path) -> str:
        key = str(path)
        if key not in self._store:
            raise FileNotFoundError(key)
        return self._store[key]

    def write_file(self, path: str | Path, content: str) -> str:
        self._store[str(path)] = content
        return str(path)

    def get_repository_state(self) -> dict[str, Any]:
        return {
            "branch": "mock-branch",
            "commit": "abc123",
            "dirty": False,
            "status": "",
        }


class TestHostAgnosticism:
    def test_mock_satisfies_protocol(self) -> None:
        """MockAdapter should be recognised as a HostAdapterProtocol."""
        assert isinstance(MockAdapter(), HostAdapterProtocol)

    def test_claude_code_satisfies_protocol(
        self, adapter: ClaudeCodeAdapter
    ) -> None:
        """ClaudeCodeAdapter should satisfy the protocol."""
        assert isinstance(adapter, HostAdapterProtocol)

    def test_runtime_can_swap_adapter(self, workspace: Path) -> None:
        """Demonstrate that runtime code can use either adapter interchangeably."""

        def run_workflow(adapter: HostAdapterProtocol) -> dict[str, Any]:
            adapter.write_file("log.txt", "step 1 done")
            state = adapter.get_repository_state()
            return {"logged": True, "branch": state["branch"]}

        # With mock
        mock = MockAdapter()
        result_mock = run_workflow(mock)
        assert result_mock == {"logged": True, "branch": "mock-branch"}

        # With real adapter — write succeeds, verify file on disk
        real = ClaudeCodeAdapter(workspace)
        real.write_file("log.txt", "step 1 done")
        assert (workspace / "log.txt").read_text() == "step 1 done"


# ---------------------------------------------------------------------------
# 6) Error propagation / conversion
# ---------------------------------------------------------------------------


class TestErrorPropagation:
    def test_adapter_error_hierarchy(self) -> None:
        assert issubclass(SkillNotFoundError, AdapterError)
        assert issubclass(SkillExecutionError, AdapterError)

    def test_read_file_propagates_file_not_found(self, adapter: ClaudeCodeAdapter) -> None:
        with pytest.raises(FileNotFoundError):
            adapter.read_file("no_such_file.md")

    def test_invoke_skill_manifest_read_failure(
        self, adapter: ClaudeCodeAdapter, workspace: Path
    ) -> None:
        """If SKILL.md exists but is unreadable, SkillExecutionError is raised."""
        skill_dir = workspace / ".agents" / "skills" / "demo-skill"
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.exists()

        # Patch read_text to raise OSError
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            with pytest.raises(SkillExecutionError, match="Failed to read skill manifest"):
                adapter.invoke_skill("demo-skill")

    def test_git_subprocess_error_raises_runtime(self, adapter: ClaudeCodeAdapter) -> None:
        """A CalledProcessError from git should be wrapped in RuntimeError."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            with pytest.raises(RuntimeError, match="Failed to query repository state"):
                adapter.get_repository_state()


# ---------------------------------------------------------------------------
# 7) Subprocess-based invoke_skill tests
# ---------------------------------------------------------------------------


class TestInvokeSkillSubprocess:
    """Tests for the real subprocess-based invoke_skill implementation."""

    def test_invoke_skill_calls_subprocess(self, adapter: ClaudeCodeAdapter) -> None:
        """Verify subprocess.run is called with correct arguments."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["claude", "-p", "prompt"],
                returncode=0,
                stdout="result",
                stderr="",
            )
            adapter.invoke_skill("demo-skill", params={"x": 1})

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0][0] == "claude"
        assert call_args[0][0][1] == "-p"
        # The prompt should contain skill content and params
        prompt = call_args[0][0][2]
        assert "# Demo Skill" in prompt
        assert '"x": 1' in prompt
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["timeout"] == 300

    def test_invoke_skill_success(self, adapter: ClaudeCodeAdapter) -> None:
        """Successful execution returns correct dict."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["claude", "-p", "prompt"],
                returncode=0,
                stdout="hello from claude",
                stderr="",
            )
            result = adapter.invoke_skill("demo-skill")

        assert result == {
            "output": "hello from claude",
            "exit_code": 0,
            "success": True,
        }

    def test_invoke_skill_failure(self, adapter: ClaudeCodeAdapter) -> None:
        """Non-zero exit code raises SkillExecutionError."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["claude", "-p", "prompt"],
                returncode=1,
                stdout="",
                stderr="something went wrong",
            )
            with pytest.raises(SkillExecutionError, match="failed with exit code 1"):
                adapter.invoke_skill("demo-skill")

    def test_invoke_skill_timeout(self, adapter: ClaudeCodeAdapter) -> None:
        """TimeoutExpired raises SkillExecutionError."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["claude", "-p", "prompt"], timeout=300
            )
            with pytest.raises(SkillExecutionError, match="timed out"):
                adapter.invoke_skill("demo-skill")

    def test_invoke_skill_not_found(
        self, adapter: ClaudeCodeAdapter
    ) -> None:
        """Missing skill file raises SkillNotFoundError (no subprocess call)."""
        with patch("garage_os.adapter.claude_code_adapter.subprocess.run") as mock_run:
            with pytest.raises(SkillNotFoundError, match="missing-skill"):
                adapter.invoke_skill("missing-skill")
        # subprocess.run should never be called
        mock_run.assert_not_called()
