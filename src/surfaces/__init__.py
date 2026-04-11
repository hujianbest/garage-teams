"""File-backed workspace surfaces for artifacts, evidence, sessions, and archives."""

from .filebacked import (
    ArtifactRoute,
    FileBackedSurfaceManager,
    SurfaceKind,
    materialize_markdown,
)

__all__ = [
    "ArtifactRoute",
    "FileBackedSurfaceManager",
    "SurfaceKind",
    "materialize_markdown",
]
