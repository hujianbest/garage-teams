"""
Host Adapter Protocol for garage-agent.

Defines the abstract interface that all host adapters must implement.
This protocol enables host-agnostic operation — the runtime depends on
this interface, not on any specific host environment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HostAdapterProtocol(Protocol):
    """Protocol defining the contract between garage-agent and its host environment.

    Every host adapter must implement these four core operations:
    - invoke_skill: Execute a named skill with parameters
    - read_file: Read file content from the workspace
    - write_file: Write content to a file in the workspace
    - get_repository_state: Retrieve the current git/repository status

    This protocol uses typing.Protocol so that any class satisfying
    the method signatures is implicitly compatible (structural typing).
    """

    def invoke_skill(
        self,
        skill_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke a named skill with the given parameters.

        Args:
            skill_name: Identifier of the skill to invoke.
            params: Optional keyword arguments forwarded to the skill.

        Returns:
            A dict containing at minimum a ``"status"`` key (``"success"`` or
            ``"error"``) and any skill-specific output under ``"result"``.

        Raises:
            SkillNotFoundError: If the skill does not exist.
            SkillExecutionError: If the skill execution fails.
        """
        ...

    def read_file(self, path: str | Path) -> str:
        """Read and return the text content of a file.

        Args:
            path: File path relative to the workspace root (or absolute
                  if the adapter accepts it).

        Returns:
            The UTF-8 decoded file content.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
        """
        ...

    def write_file(self, path: str | Path, content: str) -> str:
        """Write text content to a file, creating parent dirs as needed.

        Args:
            path: File path relative to the workspace root (or absolute).
            content: Text content to write (UTF-8).

        Returns:
            A confirmation message or the path that was written.

        Raises:
            PermissionError: If the file cannot be written.
        """
        ...

    def get_repository_state(self) -> dict[str, Any]:
        """Return the current repository/git state.

        The returned dict typically includes:
        - ``"branch"``: current branch name
        - ``"status"``: short git status output (e.g. staged/unstaged files)
        - ``"commit"``: current HEAD commit hash
        - ``"dirty"``: boolean indicating uncommitted changes

        Returns:
            Dictionary describing the current repository state.

        Raises:
            RuntimeError: If git information cannot be obtained.
        """
        ...
