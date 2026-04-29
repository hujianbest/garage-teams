"""
garage-agent core package - Phase 1 implementation

A file-first, host-agnostic agent runtime with knowledge management.

This package provides the core runtime for garage-agent, including:
- Session management and state machine
- Knowledge storage and experience indexing
- Tool registry and gateway
- Host adapter abstraction layer
"""

__version__ = "0.1.0"
__author__ = "Garage Contributors"

from garage_os.types import (
    SessionState,
    ArtifactReference,
    KnowledgeEntry,
    ExperienceRecord,
)

__all__ = [
    "__version__",
    "__author__",
    "SessionState",
    "ArtifactReference",
    "KnowledgeEntry",
    "ExperienceRecord",
]
