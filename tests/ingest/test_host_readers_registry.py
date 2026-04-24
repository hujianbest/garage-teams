"""F010 T5: HOST_READERS registry + HOST_ID_ALIASES tests.

Covers ADR-D10-11 + INV-F10-10.
"""

from __future__ import annotations

import pytest

from garage_os.ingest.host_readers import (
    HOST_ID_ALIASES,
    HOST_READERS,
    resolve_host_id,
)


class TestHostReadersRegistry:
    """ADR-D10-11: HOST_READERS independent from F007 HOST_REGISTRY."""

    def test_three_canonical_host_ids_present(self) -> None:
        assert set(HOST_READERS.keys()) == {"claude-code", "opencode", "cursor"}

    def test_each_reader_has_host_id_attribute(self) -> None:
        for canonical_id, reader_cls in HOST_READERS.items():
            instance = reader_cls()
            assert getattr(instance, "host_id", None) == canonical_id


class TestHostIdAliases:
    """ADR-D10-11: alias bridge claude → claude-code."""

    def test_claude_resolves_to_claude_code(self) -> None:
        assert resolve_host_id("claude") == "claude-code"

    def test_canonical_resolves_to_self(self) -> None:
        assert resolve_host_id("claude-code") == "claude-code"
        assert resolve_host_id("opencode") == "opencode"
        assert resolve_host_id("cursor") == "cursor"

    def test_case_insensitive_resolution(self) -> None:
        assert resolve_host_id("Claude") == "claude-code"
        assert resolve_host_id("OPENCODE") == "opencode"

    def test_unknown_raises_value_error(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            resolve_host_id("nonexistent-host")
        assert "Unknown host" in str(exc_info.value)
        assert "claude-code" in str(exc_info.value)  # error enumerates supported


class TestRegistryAliasConsistency:
    """All HOST_ID_ALIASES values must be in HOST_READERS keys."""

    def test_alias_targets_all_in_registry(self) -> None:
        for alias, canonical in HOST_ID_ALIASES.items():
            assert canonical in HOST_READERS, (
                f"alias {alias} → {canonical} but {canonical} not in HOST_READERS"
            )
