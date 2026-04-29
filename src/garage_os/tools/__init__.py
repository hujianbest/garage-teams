"""
Tool Registry and Gateway for garage-agent.

This module provides tool registration, discovery, and invocation capabilities.
Phase 1: ToolGateway records calls and returns mock results; actual execution
is delegated to the Skill Executor via the Host Adapter.
"""

from garage_os.tools.tool_registry import ToolRegistry
from garage_os.tools.tool_gateway import ToolGateway

__all__ = ["ToolRegistry", "ToolGateway"]
