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
