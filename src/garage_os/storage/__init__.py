"""
Storage infrastructure for garage-agent.

This module provides file storage, atomic writes, and file locking capabilities.
"""

from garage_os.storage.file_storage import FileStorage
from garage_os.storage.atomic_writer import AtomicWriter
from garage_os.storage.front_matter import FrontMatterParser

__all__ = ["FileStorage", "AtomicWriter", "FrontMatterParser"]
