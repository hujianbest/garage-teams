"""Tests for scripts/check_mcp_providers.py"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from check_mcp_providers import (
    format_install_guidance,
    get_required_servers,
    read_registered_servers,
)


# ---------------------------------------------------------------------------
# get_required_servers
# ---------------------------------------------------------------------------

class TestGetRequiredServers:
    def test_extracts_servers(self):
        bindings = {
            "mcp_servers": {
                "acme_ci": {"command": "npx", "args": ["-y", "@acme/ci-mcp"]},
                "acme_browser": {"command": "npx", "args": ["-y", "@acme/browser-mcp"]},
            }
        }
        servers = get_required_servers(bindings)
        names = [s["name"] for s in servers]
        assert "acme_ci" in names
        assert "acme_browser" in names

    def test_empty_mcp_servers(self):
        bindings = {"mcp_servers": {}}
        assert get_required_servers(bindings) == []

    def test_missing_mcp_servers_key(self):
        bindings = {}
        assert get_required_servers(bindings) == []

    def test_server_fields_preserved(self):
        bindings = {
            "mcp_servers": {
                "my_server": {
                    "command": "python",
                    "args": ["-m", "my_mcp"],
                    "env": {"TOKEN": "abc"},
                    "availability_probe": "my_server__ping",
                }
            }
        }
        servers = get_required_servers(bindings)
        assert len(servers) == 1
        s = servers[0]
        assert s["name"] == "my_server"
        assert s["command"] == "python"
        assert s["args"] == ["-m", "my_mcp"]
        assert s["env"] == {"TOKEN": "abc"}
        assert s["availability_probe"] == "my_server__ping"


# ---------------------------------------------------------------------------
# read_registered_servers
# ---------------------------------------------------------------------------

class TestReadRegisteredServers:
    def test_reads_claude_json_format(self, tmp_path):
        cfg = tmp_path / "claude.json"
        cfg.write_text(json.dumps({
            "mcpServers": {
                "chrome-devtools": {"command": "npx", "args": []},
                "context7": {"command": "cmd", "args": []},
            }
        }), encoding="utf-8")
        registered = read_registered_servers(cfg)
        assert "chrome-devtools" in registered
        assert "context7" in registered

    def test_reads_opencode_format(self, tmp_path):
        cfg = tmp_path / "settings.json"
        cfg.write_text(json.dumps({
            "opencode.mcpServers": {
                "acme_ci": {},
                "acme_browser": {},
            }
        }), encoding="utf-8")
        registered = read_registered_servers(cfg)
        assert "acme_ci" in registered
        assert "acme_browser" in registered

    def test_returns_empty_on_invalid_json(self, tmp_path):
        cfg = tmp_path / "bad.json"
        cfg.write_text("not valid json", encoding="utf-8")
        assert read_registered_servers(cfg) == set()

    def test_returns_empty_when_no_mcp_keys(self, tmp_path):
        cfg = tmp_path / "empty.json"
        cfg.write_text(json.dumps({"someOtherKey": {}}), encoding="utf-8")
        assert read_registered_servers(cfg) == set()

    def test_merges_both_formats(self, tmp_path):
        cfg = tmp_path / "both.json"
        cfg.write_text(json.dumps({
            "mcpServers": {"server_a": {}},
            "opencode.mcpServers": {"server_b": {}},
        }), encoding="utf-8")
        registered = read_registered_servers(cfg)
        assert "server_a" in registered
        assert "server_b" in registered


# ---------------------------------------------------------------------------
# format_install_guidance
# ---------------------------------------------------------------------------

class TestFormatInstallGuidance:
    def test_lists_missing_servers(self):
        missing = [
            {"name": "acme_ci", "command": "npx", "args": ["-y", "@acme/ci-mcp"]},
            {"name": "acme_browser", "command": "npx", "args": ["-y", "@acme/browser-mcp"]},
        ]
        output = format_install_guidance(missing)
        assert "acme_ci" in output
        assert "acme_browser" in output
        assert "NOT CONFIGURED" in output

    def test_includes_claude_add_commands(self):
        missing = [
            {"name": "my_server", "command": "npx", "args": ["-y", "@org/my-mcp"]},
        ]
        output = format_install_guidance(missing)
        assert "claude mcp add my_server" in output
        assert "@org/my-mcp" in output

    def test_includes_opencode_note(self):
        missing = [{"name": "x", "command": "npx", "args": []}]
        output = format_install_guidance(missing)
        assert "OpenCode" in output


# ---------------------------------------------------------------------------
# check_providers integration (using tmp files)
# ---------------------------------------------------------------------------

class TestCheckProviders:
    def test_all_registered_returns_empty_missing(self, tmp_path):
        from check_mcp_providers import check_providers

        bindings_file = tmp_path / "tool-bindings.json"
        bindings_file.write_text(json.dumps({
            "mcp_servers": {
                "acme_ci": {"command": "npx", "args": ["-y", "@acme/ci"]},
            }
        }), encoding="utf-8")

        claude_cfg = tmp_path / "claude.json"
        claude_cfg.write_text(json.dumps({
            "mcpServers": {"acme_ci": {"command": "npx", "args": []}}
        }), encoding="utf-8")

        # Monkey-patch find_claude_config to return our tmp file
        import check_mcp_providers as mod
        original = mod.find_claude_config
        mod.find_claude_config = lambda: (claude_cfg, str(claude_cfg))
        try:
            ok, missing, label = check_providers(str(bindings_file))
            assert len(missing) == 0
            assert len(ok) == 1
            assert ok[0]["name"] == "acme_ci"
        finally:
            mod.find_claude_config = original

    def test_unregistered_server_in_missing(self, tmp_path):
        from check_mcp_providers import check_providers

        bindings_file = tmp_path / "tool-bindings.json"
        bindings_file.write_text(json.dumps({
            "mcp_servers": {
                "acme_ci": {"command": "npx", "args": []},
                "acme_browser": {"command": "npx", "args": []},
            }
        }), encoding="utf-8")

        claude_cfg = tmp_path / "claude.json"
        claude_cfg.write_text(json.dumps({
            "mcpServers": {"acme_ci": {}}
        }), encoding="utf-8")

        import check_mcp_providers as mod
        original = mod.find_claude_config
        mod.find_claude_config = lambda: (claude_cfg, str(claude_cfg))
        try:
            ok, missing, _ = check_providers(str(bindings_file))
            assert len(ok) == 1
            assert len(missing) == 1
            assert missing[0]["name"] == "acme_browser"
        finally:
            mod.find_claude_config = original

    def test_no_servers_declared_returns_empty(self, tmp_path):
        from check_mcp_providers import check_providers

        bindings_file = tmp_path / "tool-bindings.json"
        bindings_file.write_text(json.dumps({
            "version": 1,
            "mcp_servers": {},
        }), encoding="utf-8")

        ok, missing, _ = check_providers(str(bindings_file))
        assert ok == []
        assert missing == []

    def test_missing_bindings_file_raises(self, tmp_path):
        from check_mcp_providers import check_providers

        with pytest.raises(FileNotFoundError):
            check_providers(str(tmp_path / "nonexistent.json"))
