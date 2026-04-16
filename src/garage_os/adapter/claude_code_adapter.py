"""
Claude Code Adapter — Phase 1 file-system-based implementation.

Claude Code does not expose a public session-state API. The only reliable
cross-session communication channel is the file system. This adapter
implements HostAdapterProtocol using pure file-system operations (reads,
writes, and subprocess calls to ``git``) to fulfil the contract.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class AdapterError(Exception):
    """Base exception for adapter-level errors."""


class SkillNotFoundError(AdapterError):
    """Raised when the requested skill does not exist."""


class SkillExecutionError(AdapterError):
    """Raised when a skill execution fails."""


class ClaudeCodeAdapter:
    """Host adapter backed by the local file system.

    This is the Phase 1 concrete adapter for the Claude Code environment.
    All interactions are mediated through file I/O and ``git`` CLI calls.

    Args:
        workspace_root: Absolute path to the project workspace directory.
    """

    def __init__(self, workspace_root: str | Path, timeout: int = 300) -> None:
        self._workspace_root = Path(workspace_root).resolve()
        self._timeout = timeout

    # -- Public API ----------------------------------------------------------

    @property
    def workspace_root(self) -> Path:
        """Return the resolved workspace root path."""
        return self._workspace_root

    def invoke_skill(
        self,
        skill_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke a skill by reading its SKILL.md and calling the claude CLI.

        Locates the skill manifest (``.agents/skills/<name>/SKILL.md``), reads
        it, builds a prompt that includes the skill content and workspace
        information, then executes the ``claude`` CLI via subprocess.

        Args:
            skill_name: Name of the skill directory under ``.agents/skills/``.
            params: Optional parameters forwarded to the skill.

        Returns:
            Dict with keys ``"output"``, ``"exit_code"``, and ``"success"``.

        Raises:
            SkillNotFoundError: If the skill directory or SKILL.md is missing.
            SkillExecutionError: If the subprocess fails or times out.
        """
        params = params or {}
        skill_dir = self._workspace_root / ".agents" / "skills" / skill_name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            raise SkillNotFoundError(
                f"Skill not found: {skill_name} "
                f"(expected {skill_md})"
            )

        try:
            content = skill_md.read_text(encoding="utf-8")
        except OSError as exc:
            raise SkillExecutionError(
                f"Failed to read skill manifest for '{skill_name}': {exc}"
            ) from exc

        # Build prompt from skill content, params and workspace info
        prompt = (
            f"Working directory: {self._workspace_root}\n"
            f"Skill: {skill_name}\n\n"
            f"{content}"
        )
        if params:
            prompt += f"\n\nParameters: {json.dumps(params)}"

        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SkillExecutionError(
                f"Skill '{skill_name}' timed out after {self._timeout}s"
            ) from exc
        except FileNotFoundError as exc:
            raise SkillExecutionError(
                f"claude CLI not found: {exc}"
            ) from exc

        if result.returncode != 0:
            raise SkillExecutionError(
                f"Skill '{skill_name}' failed with exit code "
                f"{result.returncode}: {result.stderr.strip()}"
            )

        return {
            "output": result.stdout,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }

    def read_file(self, path: str | Path) -> str:
        """Read file content from the workspace.

        Args:
            path: Absolute path or path relative to the workspace root.

        Returns:
            UTF-8 decoded content of the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file is not readable.
        """
        target = self._resolve_path(path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {target}")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str | Path, content: str) -> str:
        """Write content to a file, creating parent directories as needed.

        Args:
            path: Absolute path or path relative to the workspace root.
            content: Text content to write.

        Returns:
            The absolute path of the written file (as a string).

        Raises:
            PermissionError: If the file cannot be written.
        """
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return str(target)

    def get_repository_state(self) -> dict[str, Any]:
        """Query git for the current repository state.

        Returns:
            Dict with keys ``branch``, ``commit``, ``dirty``, and ``status``.

        Raises:
            RuntimeError: If git commands cannot be executed.
        """
        try:
            branch = self._git(
                ["rev-parse", "--abbrev-ref", "HEAD"],
            ).strip()

            commit = self._git(
                ["rev-parse", "HEAD"],
            ).strip()

            status = self._git(
                ["status", "--porcelain"],
            ).strip()

            dirty = bool(status)

            return {
                "branch": branch,
                "commit": commit,
                "dirty": dirty,
                "status": status,
            }
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"git is not available: {exc}"
            ) from exc
        except subprocess.SubprocessError as exc:
            raise RuntimeError(
                f"Failed to query repository state: {exc}"
            ) from exc

    # -- Internal helpers ----------------------------------------------------

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve *path* against the workspace root.

        If *path* is already absolute it is used as-is; otherwise it is
        resolved relative to ``self._workspace_root``.
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return self._workspace_root / p

    def _git(self, args: list[str]) -> str:
        """Run a ``git`` subprocess in the workspace root.

        Returns:
            stdout as a string.

        Raises:
            subprocess.CalledProcessError: If git exits non-zero.
        """
        result = subprocess.run(
            ["git", *args],
            cwd=str(self._workspace_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
