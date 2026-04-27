"""F016 T2 tests: ingest from-reviews / from-git-log / from-style-template + dedup + dry-run + strict."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.memory_activation.ingest import (
    _build_commit_record,
    _build_review_record,
    _existing_commit_shas,
    _existing_review_paths,
    _extract_lessons_from_review,
    _generate_exp_id,
    _parse_review_filename,
    ingest_from_git_log,
    ingest_from_reviews,
    ingest_from_style_template,
)
from garage_os.storage.file_storage import FileStorage
from garage_os.types import KnowledgeType


def _setup(tmp_path: Path) -> tuple[Path, ExperienceIndex, KnowledgeStore]:
    garage_dir = tmp_path / ".garage"
    storage = FileStorage(garage_dir)
    return garage_dir, ExperienceIndex(storage), KnowledgeStore(storage)


# T2.1
class TestParseReviewFilename:
    def test_standard_pattern(self) -> None:
        path = Path("spec-review-f012-r1-2026-04-25.md")
        parts = _parse_review_filename(path)
        assert parts is not None
        assert parts["type"] == "spec"
        assert parts["feature"] == "012"
        assert parts["round"] == "1"

    def test_without_round(self) -> None:
        path = Path("traceability-review-f015.md")
        parts = _parse_review_filename(path)
        assert parts is not None
        assert parts["type"] == "traceability"
        assert parts["round"] == "1"  # default

    def test_invalid_pattern_returns_none(self) -> None:
        assert _parse_review_filename(Path("random-name.md")) is None
        assert _parse_review_filename(Path("F012-spec-r1.md")) is None  # uppercase F not matched


# T2.2
class TestExtractLessonsFromReview:
    def test_extracts_recommendations_section(self) -> None:
        text = (
            "# Spec Review\n\n"
            "## Findings\n\nSome finding text\n\n"
            "## Recommendations for r2\n\n"
            "1. First item\n"
            "2. Second item\n"
            "3. Third item\n"
            "4. Fourth item\n\n"
            "## 通过条件\n\nstuff\n"
        )
        lessons = _extract_lessons_from_review(text)
        assert lessons == ["First item", "Second item", "Third item"]

    def test_handles_bulleted_recommendations(self) -> None:
        text = (
            "## Recommendations\n\n"
            "- Bullet item 1\n"
            "- Bullet item 2\n"
        )
        lessons = _extract_lessons_from_review(text)
        assert lessons == ["Bullet item 1", "Bullet item 2"]

    def test_no_section_returns_empty(self) -> None:
        text = "## Some Other Section\n\nNo recommendations here."
        assert _extract_lessons_from_review(text) == []


# T2.3
class TestIngestFromReviewsHappy:
    def test_ingest_2_reviews_creates_2_records(self, tmp_path: Path) -> None:
        garage_dir, ei, _ = _setup(tmp_path)
        reviews_dir = tmp_path / "docs" / "reviews"
        reviews_dir.mkdir(parents=True)
        (reviews_dir / "spec-review-f012-r1-2026-04-25.md").write_text(
            "## Recommendations\n\n1. Fix Cr-1\n2. Fix Cr-2\n", encoding="utf-8",
        )
        (reviews_dir / "design-review-f013-r1-2026-04-26.md").write_text(
            "## Recommendations for r2\n\n- Apply Im-1 r2\n", encoding="utf-8",
        )

        result = ingest_from_reviews(reviews_dir, ei, tmp_path)
        assert result.written == 2
        assert result.skipped == 0
        assert result.dry_run is False
        records = ei.list_records()
        assert len(records) == 2
        # Lowercase problem_domain
        problem_domains = sorted(r.problem_domain for r in records)
        assert problem_domains == ["f012", "f013"]


# T2.4
class TestIngestFromReviewsDedup:
    def test_dedup_skips_existing(self, tmp_path: Path) -> None:
        garage_dir, ei, _ = _setup(tmp_path)
        reviews_dir = tmp_path / "docs" / "reviews"
        reviews_dir.mkdir(parents=True)
        path = reviews_dir / "spec-review-f012-r1-2026-04-25.md"
        path.write_text("## Recommendations\n\n1. x\n", encoding="utf-8")

        # First ingest: writes 1
        first = ingest_from_reviews(reviews_dir, ei, tmp_path)
        assert first.written == 1

        # Second ingest: skip 1 (dedup via review_path anchor)
        second = ingest_from_reviews(reviews_dir, ei, tmp_path)
        assert second.written == 0
        assert second.skipped == 1
        # ExperienceIndex still has only 1 record
        assert len(ei.list_records()) == 1


# T2.5
class TestIngestFromReviewsDryRun:
    def test_dry_run_no_write(self, tmp_path: Path) -> None:
        garage_dir, ei, _ = _setup(tmp_path)
        reviews_dir = tmp_path / "docs" / "reviews"
        reviews_dir.mkdir(parents=True)
        (reviews_dir / "spec-review-f012-r1.md").write_text("## Recommendations\n\n- x\n")

        result = ingest_from_reviews(reviews_dir, ei, tmp_path, dry_run=True)
        assert result.dry_run is True
        assert result.written == 1  # would-write count
        assert ei.list_records() == []


# T2.6
class TestIngestFromReviewsStrict:
    def test_strict_raises_on_unparseable(self, tmp_path: Path) -> None:
        garage_dir, ei, _ = _setup(tmp_path)
        reviews_dir = tmp_path / "docs" / "reviews"
        reviews_dir.mkdir(parents=True)
        # Bad filename pattern (uppercase F)
        (reviews_dir / "Bad-Review-F012-r1.md").write_text("x")

        with pytest.raises(ValueError, match="Cannot parse"):
            ingest_from_reviews(reviews_dir, ei, tmp_path, strict=True)

    def test_non_strict_skips_unparseable(self, tmp_path: Path) -> None:
        garage_dir, ei, _ = _setup(tmp_path)
        reviews_dir = tmp_path / "docs" / "reviews"
        reviews_dir.mkdir(parents=True)
        (reviews_dir / "Bad-Review-F012-r1.md").write_text("x")
        (reviews_dir / "spec-review-f012-r1-2026-04-25.md").write_text(
            "## Recommendations\n\n- x\n"
        )

        result = ingest_from_reviews(reviews_dir, ei, tmp_path, strict=False)
        assert result.written == 1
        assert result.skipped == 1
        assert result.errors and "Cannot parse" in result.errors[0]


# T2.7
class TestIngestFromGitLog:
    def _setup_git_repo(self, tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)
        # Create commits with f-prefixed messages
        for i, prefix in enumerate(["f013(t1): foo + hf-specify", "f014(t2): bar + hf-design", "feat: regular commit"]):
            (repo / f"file-{i}.txt").write_text(f"v{i}")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", prefix], cwd=repo, check=True)
        return repo

    def test_ingest_3_commits(self, tmp_path: Path) -> None:
        repo = self._setup_git_repo(tmp_path)
        garage_dir = tmp_path / ".garage"
        ei = ExperienceIndex(FileStorage(garage_dir))

        result = ingest_from_git_log(repo, ei, limit=10)
        assert result.written == 3

        records = ei.list_records()
        problem_domains = sorted(r.problem_domain for r in records)
        # 2 commits with f-prefix, 1 with no prefix → unknown
        assert "f013" in problem_domains
        assert "f014" in problem_domains
        assert "unknown" in problem_domains

        # Check skill_ids extracted
        f013 = next(r for r in records if r.problem_domain == "f013")
        assert "hf-specify" in f013.skill_ids
        f014 = next(r for r in records if r.problem_domain == "f014")
        assert "hf-design" in f014.skill_ids

    def test_dedup_via_commit_sha(self, tmp_path: Path) -> None:
        repo = self._setup_git_repo(tmp_path)
        garage_dir = tmp_path / ".garage"
        ei = ExperienceIndex(FileStorage(garage_dir))

        # First ingest writes 3
        first = ingest_from_git_log(repo, ei, limit=10)
        assert first.written == 3

        # Second ingest skips all 3 (same SHAs)
        second = ingest_from_git_log(repo, ei, limit=10)
        assert second.written == 0
        assert second.skipped == 3


# T2.8
class TestIngestFromStyleTemplate:
    def test_ingest_python_template(self, tmp_path: Path) -> None:
        garage_dir, _, ks = _setup(tmp_path)
        # Use real packs_root
        repo_root = Path(__file__).resolve().parent.parent.parent
        packs_root = repo_root / "packs"

        result = ingest_from_style_template(packs_root, "python", ks)
        assert result.written >= 5  # python template has ≥ 5 entries
        assert result.skipped == 0
        # Verify entries
        entries = ks.list_entries(knowledge_type=KnowledgeType.STYLE)
        assert len(entries) >= 5
        # All entries should have lang tag
        assert all("python" in e.tags for e in entries)

    def test_dedup_skips_existing_topic(self, tmp_path: Path) -> None:
        garage_dir, _, ks = _setup(tmp_path)
        repo_root = Path(__file__).resolve().parent.parent.parent
        packs_root = repo_root / "packs"

        first = ingest_from_style_template(packs_root, "python", ks)
        second = ingest_from_style_template(packs_root, "python", ks)
        assert second.written == 0
        assert second.skipped == first.written

    def test_unsupported_lang_returns_error(self, tmp_path: Path) -> None:
        garage_dir, _, ks = _setup(tmp_path)
        result = ingest_from_style_template(tmp_path / "packs", "rust", ks)
        assert result.written == 0
        assert result.errors is not None and "not found" in result.errors[0]

    def test_strict_raises_on_missing(self, tmp_path: Path) -> None:
        garage_dir, _, ks = _setup(tmp_path)
        with pytest.raises(ValueError, match="not found"):
            ingest_from_style_template(tmp_path / "packs", "rust", ks, strict=True)


# T2.9
class TestGenerateExpId:
    def test_format(self) -> None:
        now = datetime(2026, 4, 27, 12, 0, 0)
        eid = _generate_exp_id("commit", "abc123", now)
        assert eid.startswith("exp-20260427-")
        suffix = eid.rsplit("-", 1)[1]
        assert len(suffix) == 6
        assert all(c in "0123456789abcdef" for c in suffix)
