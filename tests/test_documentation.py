"""Documentation lint checks for garage-agent user-facing docs.

Keeps the user guide and README content in sync with the CLI behavior
contracts described by delivered feature cycles. Tests are deliberately
lightweight token-based checks; if the guide is restructured, update the
expected tokens here too.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_GUIDE = REPO_ROOT / "docs" / "guides" / "garage-agent-user-guide.md"


def test_user_guide_memory_review_documents_both_abandon_paths() -> None:
    """User guide must explain --action=abandon vs --action=accept --strategy=abandon (FR-403c)."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "abandon",
        "without publication attempt",
        "due to conflict",
        "--action abandon",
        "--strategy abandon",
        "conflict_strategy=abandon",
    ):
        assert token in content, (
            f"expected user guide to mention '{token}'; not found"
        )


def test_developer_guide_has_been_retired() -> None:
    """garage-agent now keeps one user guide and no separate developer guide."""
    retired_paths = (
        REPO_ROOT / "docs" / "guides" / "garage-os-user-guide.md",
        REPO_ROOT / "docs" / "guides" / "garage-os-developer-guide.md",
    )
    for path in retired_paths:
        assert not path.exists(), f"retired guide path should not exist: {path}"


# F005 / NFR-505: user guide must document the new knowledge / experience CRUD
# subcommands; READMEs must list them in the CLI command summary.

README_EN = REPO_ROOT / "README.md"
README_ZH = REPO_ROOT / "README.zh-CN.md"


def test_user_guide_documents_knowledge_authoring_cli() -> None:
    """User guide must contain a Knowledge authoring (CLI) section covering all 7 new subcommands."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "Knowledge authoring (CLI)",
        "garage knowledge add",
        "garage knowledge edit",
        "garage knowledge show",
        "garage knowledge delete",
        "garage experience add",
        "garage experience show",
        "garage experience delete",
        "cli:knowledge-add",
        "cli:knowledge-edit",
        "cli:experience-add",
    ):
        assert token in content, f"expected user guide to mention '{token}'; not found"


def test_user_guide_uses_garage_agent_branding() -> None:
    """User-facing guide must use garage-agent as the product name."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "# garage-agent 使用手册",
        "本地优先的 Agent 能力之家",
        "Python package",
        "garage-os",
        "CLI 命令",
        "garage",
    ):
        assert token in content, (
            f"expected user guide to mention branding token '{token}'; not found"
        )
    assert "Garage OS 用户指南" not in content
    assert "Garage OS 是什么" not in content


def test_readmes_list_new_cli_subcommands() -> None:
    """Both READMEs must list the 7 new CLI subcommands in the CLI summary."""
    for readme in (README_EN, README_ZH):
        content = readme.read_text(encoding="utf-8")
        for token in (
            "knowledge add",
            "knowledge edit",
            "knowledge show",
            "knowledge delete",
            "experience add",
            "experience show",
            "experience delete",
        ):
            assert token in content, (
                f"expected {readme.name} to list CLI command '{token}'; not found"
            )


# F006 / NFR-605: user guide must document the 3 new recall + graph subcommands;
# READMEs must list them in the CLI command summary.


def test_user_guide_documents_recall_and_knowledge_graph() -> None:
    """User guide must contain an Active recall and knowledge graph section
    covering all 3 new F006 subcommands."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "Active recall and knowledge graph",
        "garage recommend",
        "garage knowledge link",
        "garage knowledge graph",
        "cli:knowledge-link",
        "Outgoing edges:",
        "Incoming edges:",
    ):
        assert token in content, f"expected user guide to mention '{token}'; not found"


def test_readmes_list_f006_cli_subcommands() -> None:
    """Both READMEs must list the 3 new F006 CLI subcommands."""
    for readme in (README_EN, README_ZH):
        content = readme.read_text(encoding="utf-8")
        for token in (
            "recommend",
            "knowledge link",
            "knowledge graph",
        ):
            assert token in content, (
                f"expected {readme.name} to list CLI command '{token}'; not found"
            )


# F014 / FR-1402: AGENTS.md must document the new recall workflow CLI subcommand.

def test_agents_md_mentions_workflow_recall_cli() -> None:
    """F014: AGENTS.md must mention `garage recall workflow` CLI."""
    agents_md = REPO_ROOT / "AGENTS.md"
    content = agents_md.read_text(encoding="utf-8")
    for token in (
        "recall workflow",
        "Workflow Recall (F014)",
        "WorkflowRecallHook",
        "step 3.5",
    ):
        assert token in content, (
            f"expected AGENTS.md to mention F014 token '{token}'; not found"
        )


def test_user_guide_documents_f013_f014_user_flows() -> None:
    """User guide must cover the F013-A and F014 user-facing commands."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "Skill Mining",
        "garage skill suggest",
        "garage skill promote",
        "garage status",
        "Workflow Recall",
        "garage recall workflow",
        "--json",
        "--rebuild-cache",
    ):
        assert token in content, (
            f"expected user guide to mention F013/F014 token '{token}'; not found"
        )


def test_user_guide_documents_pack_lifecycle_and_anonymize_export() -> None:
    """User guide must cover F011/F012 pack lifecycle and anonymized export commands."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "Pack Lifecycle",
        "garage pack install",
        "garage pack ls",
        "garage pack update",
        "garage pack uninstall",
        "garage pack publish",
        "garage knowledge export --anonymize",
        "~/.garage/anonymize-patterns.txt",
    ):
        assert token in content, (
            f"expected user guide to mention lifecycle token '{token}'; not found"
        )


def test_user_guide_documents_skill_mining_and_workflow_recall() -> None:
    """User guide must cover current F013-A and F014 user-facing commands."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "pattern → skill",
        "garage skill suggest",
        "garage skill promote",
        "skill-mining-config",
        "Workflow Recall",
        "garage recall workflow",
        "--rebuild-cache",
        "workflow-recall",
    ):
        assert token in content, (
            f"expected user guide to mention current CLI token '{token}'; not found"
        )


def test_readmes_are_synced_to_f014_cli_surface() -> None:
    """Both READMEs must reflect F013-A/F014 in the quick user-facing surface."""
    for readme in (README_EN, README_ZH):
        content = readme.read_text(encoding="utf-8")
        for token in (
            "F014",
            "skill suggest",
            "skill promote",
            "recall workflow",
        ):
            assert token in content, (
                f"expected {readme.name} to mention F014-era token '{token}'; not found"
            )


# F007 / FR-710: user guide must document the Pack & Host Installer.

def test_user_guide_documents_pack_and_host_installer() -> None:
    """User guide must contain a 'Pack & Host Installer' section (FR-710)."""
    content = USER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "Pack & Host Installer",
        "garage init --hosts",
        ".garage/config/host-installer.json",
        "claude",
        "opencode",
        "cursor",
        "--force",
        "Skipped",
        "locally modified",
    ):
        assert token in content, (
            f"expected user guide to mention '{token}'; not found (F007 FR-710)"
        )


def test_packs_readme_documents_directory_contract() -> None:
    """packs/README.md must explain the directory contract (FR-701 + design D7 §11.3)."""
    packs_readme = REPO_ROOT / "packs" / "README.md"
    assert packs_readme.is_file(), "packs/README.md missing (F007 FR-701)"
    content = packs_readme.read_text(encoding="utf-8")
    for token in (
        "pack.json",
        "schema_version",
        "skills",
        "agents",
        "garage init",
    ):
        assert token in content, (
            f"expected packs/README.md to mention '{token}'; not found"
        )
