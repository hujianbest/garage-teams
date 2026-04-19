"""Unit tests for garage_os.adapter.installer.host_registry.

F007 T2 — covers FR-707 (host adapter registry + resolve_hosts_arg) by acceptance:

- HOST_REGISTRY contains exactly the three first-class hosts: claude / opencode / cursor
- list_host_ids() returns ASCII-sorted ids
- get_adapter("notarealtool") raises UnknownHostError with supported list in message
- resolve_hosts_arg("all") expands to full sorted list
- resolve_hosts_arg("none") returns []
- resolve_hosts_arg("claude,cursor") returns sorted list
- resolve_hosts_arg with unknown member raises UnknownHostError
"""

from __future__ import annotations

import pytest

from garage_os.adapter.installer.host_registry import (
    HOST_REGISTRY,
    UnknownHostError,
    get_adapter,
    list_host_ids,
    resolve_hosts_arg,
)


class TestHostRegistry:
    """FR-707: host adapter registry contract."""

    def test_registry_contains_three_first_class_hosts(self) -> None:
        assert set(HOST_REGISTRY.keys()) == {"claude", "opencode", "cursor"}

    def test_list_host_ids_is_ascii_sorted(self) -> None:
        assert list_host_ids() == ["claude", "cursor", "opencode"]

    def test_get_adapter_returns_claude_install_adapter(self) -> None:
        adapter = get_adapter("claude")
        assert adapter.host_id == "claude"

    def test_get_adapter_returns_cursor_install_adapter(self) -> None:
        adapter = get_adapter("cursor")
        assert adapter.host_id == "cursor"

    def test_get_adapter_returns_opencode_install_adapter(self) -> None:
        adapter = get_adapter("opencode")
        assert adapter.host_id == "opencode"

    def test_get_adapter_unknown_raises_with_supported_list(self) -> None:
        with pytest.raises(UnknownHostError) as exc_info:
            get_adapter("notarealtool")
        msg = str(exc_info.value)
        assert "notarealtool" in msg
        # Supported hosts must be enumerated in the error so users can self-correct.
        assert "claude" in msg
        assert "cursor" in msg
        assert "opencode" in msg


class TestResolveHostsArg:
    """FR-702/707: --hosts argument resolution."""

    def test_all_expands_to_sorted_full_list(self) -> None:
        assert resolve_hosts_arg("all") == ["claude", "cursor", "opencode"]

    def test_none_returns_empty_list(self) -> None:
        assert resolve_hosts_arg("none") == []

    def test_comma_list_returns_sorted_dedup(self) -> None:
        # Output is sorted (ADR-D7 stable order); duplicates are de-duped.
        assert resolve_hosts_arg("cursor,claude") == ["claude", "cursor"]
        assert resolve_hosts_arg("claude,claude") == ["claude"]

    def test_comma_list_with_whitespace_is_trimmed(self) -> None:
        assert resolve_hosts_arg("claude, cursor ") == ["claude", "cursor"]

    def test_unknown_member_raises(self) -> None:
        with pytest.raises(UnknownHostError) as exc_info:
            resolve_hosts_arg("claude,notarealtool")
        assert "notarealtool" in str(exc_info.value)

    def test_empty_string_returns_empty_list(self) -> None:
        # Matches "none" semantics; user passing --hosts "" should not crash.
        assert resolve_hosts_arg("") == []
