"""Documentation lint checks for F004 v1.1.

Keeps user-guide and developer-guide content in sync with the publisher /
SessionManager / CLI behavior contracts described in the F004 spec and
design. Tests are deliberately lightweight token-based checks; if the
guides are restructured, update the expected tokens here too.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_GUIDE = REPO_ROOT / "docs" / "guides" / "garage-os-user-guide.md"
DEVELOPER_GUIDE = REPO_ROOT / "docs" / "guides" / "garage-os-developer-guide.md"


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


def test_developer_guide_documents_publication_identity_generator() -> None:
    """Developer guide must describe PublicationIdentityGenerator + version semantics (NFR-401)."""
    content = DEVELOPER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "PublicationIdentityGenerator",
        "derive_knowledge_id",
        "derive_experience_id",
        "version",
        "update",
        "PRESERVED_FRONT_MATTER_KEYS",
        "self-conflict",
    ):
        assert token in content, (
            f"expected developer guide to mention '{token}'; not found"
        )


def test_developer_guide_documents_memory_extraction_error_json_schema() -> None:
    """Developer guide must describe memory-extraction-error.json schema (CON-404)."""
    content = DEVELOPER_GUIDE.read_text(encoding="utf-8")
    for token in (
        "memory-extraction-error.json",
        "schema_version",
        "phase",
        "orchestrator_init",
        "enablement_check",
        "extraction",
    ):
        assert token in content, (
            f"expected developer guide to mention '{token}'; not found"
        )


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
