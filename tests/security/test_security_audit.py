"""Tests for security audit (T19)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pytest

from scripts.security_audit import (
    REQUIRED_GITIGNORE_ENTRIES,
    scan_sensitive_data,
    verify_gitignore,
    verify_tool_gateway_rejection,
    scan_session_json_for_credentials,
    CREDENTIAL_KEY_PATTERNS,
)

from garage_os.tools.tool_gateway import ToolGateway
