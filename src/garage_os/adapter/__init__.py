"""
Host adapter abstraction layer for garage-agent.

This module provides the protocol interface and concrete implementations
for host environment adapters. The adapter pattern decouples garage-agent
from specific host environments (e.g., Claude Code, Cursor, etc.),
allowing the runtime to remain host-agnostic.
"""

from garage_os.adapter.host_adapter import HostAdapterProtocol
from garage_os.adapter.claude_code_adapter import ClaudeCodeAdapter

__all__ = ["HostAdapterProtocol", "ClaudeCodeAdapter"]
