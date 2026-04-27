"""F016 T2: ``ingest.py`` — backfill ExperienceRecord + KnowledgeEntry from
existing repository artifacts (review verdicts / git log / STYLE templates).

Per spec FR-1602 + ADR-D16-3..5:

- ``ingest_from_reviews(reviews_dir, exp_index, ...)`` scans markdown files
  matching ``<type>-review-f<NNN>-r<R>-<date>.md`` pattern, parses
  ``Recommendations`` section for lessons_learned, dedupes via
  ``source_evidence_anchors[].review_path``.
- ``ingest_from_git_log(repo_dir, exp_index, *, limit=50)`` runs
  ``git log --oneline -<limit>``, extracts ``f<NNN>`` problem_domain and
  ``hf-*`` skill_ids from commit messages, dedupes via ``commit_sha``.
- ``ingest_from_style_template(packs_root, lang, knowledge_store, ...)``
  loads template via ``templates.parse_style_template`` and writes
  ``KnowledgeEntry(type=KnowledgeType.STYLE)`` records, dedupes via topic
  uniqueness.

All paths support ``--dry-run`` (no write) and ``--strict`` (raise on parse
failure rather than skip + log).
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import IO

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.memory_activation.templates import parse_style_template, template_path
from garage_os.memory_activation.types import IngestSummary
from garage_os.types import ExperienceRecord, KnowledgeEntry, KnowledgeType

# ADR-D16-4 review filename pattern: e.g. spec-review-f012-r1-2026-04-25.md
_REVIEW_FILENAME_RE = re.compile(
    r"^(?P<type>spec|design|test|code|traceability|regression|completion)"
    r"-(?P<phase>review|gate)"
    r"-f(?P<feature>\d+)"
    r"(?:-r(?P<round>\d+))?"
    r"(?:-(?P<date>\d{4}-\d{2}-\d{2}))?"
    r"\.md$"
)

# Match top-level "## Recommendations" / "## Recommendations for r2" sections
# and capture the body up to the next ## section
_RECOMMENDATIONS_SECTION_RE = re.compile(
    r"^##\s+Recommendations(?:\s+for\s+r\d+)?\s*$"
    r"\n(.+?)"
    r"(?=\n##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)

# Match list items in Recommendations (numbered or bulleted)
_RECOMMENDATION_ITEM_RE = re.compile(
    r"^(?:[-*]|\d+\.)\s+(.+?)\s*$",
    re.MULTILINE,
)

# ADR-D16-5 git log pattern
_COMMIT_PROBLEM_DOMAIN_RE = re.compile(r"^(f\d+)\(", re.IGNORECASE)
_COMMIT_HF_SKILL_RE = re.compile(r"\b(hf-[a-z]+(?:-[a-z]+)*)\b")


def _generate_exp_id(task_type: str, summary: str, now: datetime) -> str:
    """Replicate F005 ``_generate_experience_id`` pattern for ingest record_ids.

    Mi-2 r2: use ``exp-<yyyymmdd>-<6 hex>`` pattern, NOT F013-A's ``sg-`` pattern.
    """
    timestamp = now.replace(microsecond=0).isoformat()
    digest_input = f"{task_type}\n{summary}\n{timestamp}".encode("utf-8")
    short = hashlib.sha256(digest_input).hexdigest()[:6]
    return f"exp-{now.strftime('%Y%m%d')}-{short}"


def _err(stderr: IO[str] | None) -> IO[str]:
    return stderr if stderr is not None else sys.stderr


# ---------- review verdict parser ----------


def _parse_review_filename(path: Path) -> dict | None:
    """Parse review filename; return dict with type/feature/round/date or None."""
    m = _REVIEW_FILENAME_RE.match(path.name)
    if not m:
        return None
    return {
        "type": m.group("type"),
        "phase": m.group("phase"),
        "feature": m.group("feature"),
        "round": m.group("round") or "1",
        "date": m.group("date"),
    }


def _extract_lessons_from_review(text: str, max_count: int = 3) -> list[str]:
    """Extract first ``max_count`` recommendation items from a review verdict body."""
    section_match = _RECOMMENDATIONS_SECTION_RE.search(text)
    if not section_match:
        return []
    section = section_match.group(1)
    items = _RECOMMENDATION_ITEM_RE.findall(section)
    return [item.strip()[:200] for item in items[:max_count]]


def _build_review_record(
    path: Path,
    parts: dict,
    garage_root: Path,
    *,
    now: datetime,
) -> ExperienceRecord:
    """Build an ExperienceRecord from a review verdict file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    lessons = _extract_lessons_from_review(text)
    rel_path = str(path.relative_to(garage_root)) if path.is_absolute() else str(path)
    feature_id = f"f{parts['feature']}"  # Im-3 r2 lowercase
    review_type = parts["type"]
    summary = f"{review_type} review verdict for {feature_id} r{parts['round']}"
    return ExperienceRecord(
        record_id=_generate_exp_id("review-verdict", rel_path, now),
        task_type="review-verdict",
        skill_ids=[f"hf-{review_type}-review"],
        tech_stack=[],
        domain="review",
        problem_domain=feature_id,
        outcome="success",
        duration_seconds=0,
        complexity="medium",
        session_id=f"review-{feature_id}-r{parts['round']}",
        artifacts=[rel_path],
        key_patterns=[review_type, parts["phase"]],
        lessons_learned=lessons,
        source_evidence_anchors=[{
            "review_path": rel_path,
            "review_type": review_type,
            "round": int(parts["round"]),
        }],
        created_at=now,
        updated_at=now,
    )


def _existing_review_paths(exp_index: ExperienceIndex) -> set[str]:
    """Collect ``review_path`` values from existing records' source_evidence_anchors."""
    out: set[str] = set()
    for record in exp_index.list_records():
        for anchor in (record.source_evidence_anchors or []):
            if isinstance(anchor, dict):
                rp = anchor.get("review_path")
                if rp:
                    out.add(str(rp))
    return out


def ingest_from_reviews(
    reviews_dir: Path,
    exp_index: ExperienceIndex,
    garage_root: Path,
    *,
    dry_run: bool = False,
    strict: bool = False,
    stderr: IO[str] | None = None,
) -> IngestSummary:
    """Ingest review verdict markdown files as ExperienceRecord."""
    err = _err(stderr)
    errors: list[str] = []
    if not reviews_dir.is_dir():
        msg = f"Reviews dir not found: {reviews_dir}"
        if strict:
            raise ValueError(msg)
        print(msg, file=err)
        return IngestSummary(source="reviews", written=0, skipped=0, dry_run=dry_run, errors=[msg])

    existing_paths = _existing_review_paths(exp_index)
    written_count = 0
    skipped_count = 0
    now = datetime.now()

    for path in sorted(reviews_dir.glob("*.md")):
        rel_path = str(path.relative_to(garage_root)) if path.is_absolute() else str(path)
        if rel_path in existing_paths:
            skipped_count += 1
            continue
        parts = _parse_review_filename(path)
        if parts is None:
            msg = f"Cannot parse review filename: {path.name}"
            if strict:
                raise ValueError(msg)
            errors.append(msg)
            skipped_count += 1
            continue
        record = _build_review_record(path, parts, garage_root, now=now)
        if not dry_run:
            try:
                exp_index.store(record)
                written_count += 1
            except Exception as exc:
                msg = f"Failed to store {path.name}: {exc}"
                if strict:
                    raise
                errors.append(msg)
                skipped_count += 1
        else:
            written_count += 1  # would-write count

    return IngestSummary(
        source="reviews",
        written=written_count,
        skipped=skipped_count,
        dry_run=dry_run,
        errors=errors or None,
    )


# ---------- git log parser ----------


def _build_commit_record(
    sha: str,
    message: str,
    *,
    now: datetime,
) -> ExperienceRecord:
    """Build an ExperienceRecord from a git log line."""
    pd_match = _COMMIT_PROBLEM_DOMAIN_RE.search(message)
    problem_domain = pd_match.group(1).lower() if pd_match else "unknown"
    skill_ids = sorted(set(_COMMIT_HF_SKILL_RE.findall(message)))
    return ExperienceRecord(
        record_id=_generate_exp_id("commit", sha, now),
        task_type="commit",
        skill_ids=skill_ids,
        tech_stack=[],
        domain="git",
        problem_domain=problem_domain,
        outcome="success",
        duration_seconds=0,
        complexity="low",
        session_id=f"commit-{sha[:7]}",
        artifacts=[],
        key_patterns=[],
        lessons_learned=[],
        source_evidence_anchors=[{
            "commit_sha": sha,
            "commit_message": message[:200],
        }],
        created_at=now,
        updated_at=now,
    )


def _existing_commit_shas(exp_index: ExperienceIndex) -> set[str]:
    out: set[str] = set()
    for record in exp_index.list_records():
        for anchor in (record.source_evidence_anchors or []):
            if isinstance(anchor, dict):
                sha = anchor.get("commit_sha")
                if sha:
                    out.add(str(sha))
    return out


def ingest_from_git_log(
    repo_dir: Path,
    exp_index: ExperienceIndex,
    *,
    limit: int = 50,
    dry_run: bool = False,
    strict: bool = False,
    stderr: IO[str] | None = None,
) -> IngestSummary:
    """Ingest recent git commits as ExperienceRecord (one per commit)."""
    err = _err(stderr)
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{limit}"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        msg = f"git log failed: {exc}"
        if strict:
            raise
        print(msg, file=err)
        return IngestSummary(source="git-log", written=0, skipped=0, dry_run=dry_run, errors=[msg])

    existing_shas = _existing_commit_shas(exp_index)
    written_count = 0
    skipped_count = 0
    errors: list[str] = []
    now = datetime.now()

    for line in result.stdout.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            skipped_count += 1
            continue
        sha, message = parts
        if sha in existing_shas:
            skipped_count += 1
            continue
        record = _build_commit_record(sha, message, now=now)
        if not dry_run:
            try:
                exp_index.store(record)
                written_count += 1
            except Exception as exc:
                msg = f"Failed to store commit {sha}: {exc}"
                if strict:
                    raise
                errors.append(msg)
                skipped_count += 1
        else:
            written_count += 1

    return IngestSummary(
        source="git-log",
        written=written_count,
        skipped=skipped_count,
        dry_run=dry_run,
        errors=errors or None,
    )


# ---------- STYLE template ingest ----------


def _existing_style_topics(knowledge_store: KnowledgeStore) -> set[str]:
    out: set[str] = set()
    for entry in knowledge_store.list_entries(knowledge_type=KnowledgeType.STYLE):
        out.add(entry.topic)
    return out


def ingest_from_style_template(
    packs_root: Path,
    lang: str,
    knowledge_store: KnowledgeStore,
    *,
    dry_run: bool = False,
    strict: bool = False,
    stderr: IO[str] | None = None,
) -> IngestSummary:
    """Ingest STYLE template entries into KnowledgeStore (KnowledgeType.STYLE)."""
    err = _err(stderr)
    path = template_path(packs_root, lang)
    if not path.is_file():
        msg = f"Style template not found: {path}"
        if strict:
            raise ValueError(msg)
        print(msg, file=err)
        return IngestSummary(
            source=f"style-template:{lang}",
            written=0, skipped=0, dry_run=dry_run, errors=[msg],
        )

    template_entries = parse_style_template(path)
    if not template_entries:
        msg = f"No parseable entries in {path}"
        if strict:
            raise ValueError(msg)
        print(msg, file=err)
        return IngestSummary(
            source=f"style-template:{lang}",
            written=0, skipped=0, dry_run=dry_run, errors=[msg],
        )

    existing_topics = _existing_style_topics(knowledge_store)
    written_count = 0
    skipped_count = 0
    errors: list[str] = []
    now = datetime.now()

    for topic, content in template_entries:
        if topic in existing_topics:
            skipped_count += 1
            continue
        # Use F005 entry id pattern but for STYLE
        digest_input = f"{topic}\n{content}\n{now.replace(microsecond=0).isoformat()}".encode("utf-8")
        short = hashlib.sha256(digest_input).hexdigest()[:6]
        entry_id = f"style-{now.strftime('%Y%m%d')}-{short}"
        entry = KnowledgeEntry(
            id=entry_id,
            type=KnowledgeType.STYLE,
            topic=topic,
            date=now,
            tags=[lang, "style-template"],
            content=content,
            source_artifact=f"cli:memory-ingest:style-template:{lang}",
        )
        if not dry_run:
            try:
                knowledge_store.store(entry)
                written_count += 1
            except Exception as exc:
                msg = f"Failed to store STYLE entry '{topic}': {exc}"
                if strict:
                    raise
                errors.append(msg)
                skipped_count += 1
        else:
            written_count += 1

    return IngestSummary(
        source=f"style-template:{lang}",
        written=written_count,
        skipped=skipped_count,
        dry_run=dry_run,
        errors=errors or None,
    )
