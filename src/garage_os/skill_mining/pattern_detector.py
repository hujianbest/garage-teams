"""F013-A T2: ``PatternDetector`` — cluster KnowledgeEntry + ExperienceRecord
into (problem_domain, tag-bucket) groups; emit SkillSuggestion when N is reached
(FR-1301 + ADR-D13-4 dual-source problem_domain_key).

Read-only on KnowledgeStore + ExperienceIndex (INV-F13-3).
Writes only to ``.garage/skill-suggestions/proposed/`` via ``SuggestionStore``.

Performance budget (CON-1303): 1000 + 1000 entries < 5s on local SSD.
Algorithm is O(N + M) cluster + O(K log K) sort by score where K = number of
distinct (domain, tag-bucket) buckets.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.skill_mining.suggestion_store import SuggestionStore
from garage_os.skill_mining.types import SkillSuggestion, SkillSuggestionStatus
from garage_os.types import ExperienceRecord, KnowledgeEntry

DEFAULT_THRESHOLD = 5
DEFAULT_EXPIRY_DAYS = 30


@dataclass
class ClusterEvidence:
    """In-memory cluster of (domain, tag_bucket) hits before promotion to SkillSuggestion."""

    problem_domain_key: str
    tag_bucket: tuple[str, ...]
    entry_ids: list[str]
    record_ids: list[str]
    session_ids: set[str]
    max_timestamp: datetime


def extract_problem_domain_key(item: ExperienceRecord | KnowledgeEntry) -> str | None:
    """ADR-D13-4 r2: dual-source extraction.

    - ``ExperienceRecord`` → top-level ``problem_domain`` field (F004 schema)
    - ``KnowledgeEntry`` → ``front_matter["problem_domain"]`` first; fallback to
      ``topic.split()[0]`` (first whitespace-delimited token); ``None`` if both empty
      (Im-3 修订: skip-not-bucket).
    """
    if isinstance(item, ExperienceRecord):
        key = (item.problem_domain or "").strip()
        return key or None
    if isinstance(item, KnowledgeEntry):
        key = item.front_matter.get("problem_domain") if item.front_matter else None
        if key:
            return str(key).strip() or None
        topic = (item.topic or "").strip()
        if topic:
            first_token = topic.split()[0]
            return first_token or None
        return None
    return None


def extract_tag_bucket(item: ExperienceRecord | KnowledgeEntry) -> tuple[str, ...]:
    """Take first 2 tags (alpha-sorted) for cluster bucketing.

    - ``ExperienceRecord`` → ``key_patterns[:2]``
    - ``KnowledgeEntry`` → ``tags[:2]``
    """
    if isinstance(item, ExperienceRecord):
        raw = item.key_patterns or []
    elif isinstance(item, KnowledgeEntry):
        raw = item.tags or []
    else:
        return ()
    cleaned = [str(t).strip() for t in raw if str(t).strip()]
    cleaned.sort()
    return tuple(cleaned[:2])


def _session_id_for(item: ExperienceRecord | KnowledgeEntry) -> str | None:
    if isinstance(item, ExperienceRecord):
        return item.session_id or None
    if isinstance(item, KnowledgeEntry):
        return item.source_session
    return None


def _timestamp_for(item: ExperienceRecord | KnowledgeEntry) -> datetime:
    if isinstance(item, ExperienceRecord):
        return item.created_at
    if isinstance(item, KnowledgeEntry):
        return item.date
    return datetime.now()


def cluster_items(
    items: Iterable[ExperienceRecord | KnowledgeEntry],
) -> list[ClusterEvidence]:
    """Group items by (problem_domain_key, tag_bucket); skip items where key is None."""
    buckets: dict[tuple[str, tuple[str, ...]], ClusterEvidence] = {}
    for item in items:
        key = extract_problem_domain_key(item)
        if key is None:
            continue  # Im-3 修订: skip-not-bucket
        bucket = extract_tag_bucket(item)
        cluster_key = (key, bucket)
        ts = _timestamp_for(item)
        sid = _session_id_for(item)
        if cluster_key not in buckets:
            buckets[cluster_key] = ClusterEvidence(
                problem_domain_key=key,
                tag_bucket=bucket,
                entry_ids=[],
                record_ids=[],
                session_ids=set(),
                max_timestamp=ts,
            )
        c = buckets[cluster_key]
        if isinstance(item, ExperienceRecord):
            c.record_ids.append(item.record_id)
        elif isinstance(item, KnowledgeEntry):
            c.entry_ids.append(item.id)
        if sid:
            c.session_ids.add(sid)
        if ts > c.max_timestamp:
            c.max_timestamp = ts
    return list(buckets.values())


def compute_score(c: ClusterEvidence) -> float:
    """Spec FR-1301 score formula.

    ``score = log10(N+1) + 0.3 * unique_session_count + 0.5 * (max_ts.days_since_epoch / 1000)``

    N is total evidence (entries + records), counted before session de-dup.
    """
    n = len(c.entry_ids) + len(c.record_ids)
    days_since_epoch = (c.max_timestamp - datetime(1970, 1, 1)).days
    return math.log10(n + 1) + 0.3 * len(c.session_ids) + 0.5 * (days_since_epoch / 1000)


def _normalize_for_match(s: str) -> str:
    return re.sub(r"[\s_-]+", "-", s.strip().lower())


def already_covered_by_skill(
    cluster: ClusterEvidence,
    packs_root: Path,
) -> bool:
    """Check whether an existing ``packs/<pack>/skills/<skill>/SKILL.md``
    already covers this (problem_domain_key, tag_bucket).

    Heuristic (FR-1301 边界 D-13-1): substring match between
    ``problem_domain_key`` (normalized) and any SKILL.md frontmatter ``name``.
    Conservative — false negatives (re-suggest) preferred over false positives
    (silent skip of a real candidate).
    """
    if not packs_root.is_dir():
        return False
    needle = _normalize_for_match(cluster.problem_domain_key)
    if not needle:
        return False
    for skill_md in packs_root.glob("*/skills/*/SKILL.md"):
        try:
            head = skill_md.read_text(encoding="utf-8", errors="replace")[:1024]
        except OSError:
            continue
        # parse frontmatter `name:` field
        m = re.search(r"^name:\s*(.+?)\s*$", head, re.MULTILINE)
        if not m:
            continue
        name_norm = _normalize_for_match(m.group(1))
        if needle and needle in name_norm:
            return True
    return False


def _short_description(cluster: ClusterEvidence) -> str:
    """Generate a ≥ 50-char description from cluster evidence (FR-1303 stub).

    The full template is built by ``template_generator``; this is a brief used
    on the SkillSuggestion record itself (suggestion list table cell).
    """
    tags_part = ", ".join(cluster.tag_bucket) or "(none)"
    base = (
        f"适用于 problem_domain '{cluster.problem_domain_key}' "
        f"+ tags [{tags_part}] 在 {len(cluster.session_ids)} 次会话出现的重复模式. "
        f"不适用于其它 domain."
    )
    return base


def _suggested_name(cluster: ClusterEvidence) -> str:
    """Derive a stable, lowercase, hyphenated skill name from the cluster key."""
    key_norm = _normalize_for_match(cluster.problem_domain_key)
    if cluster.tag_bucket:
        tag_norm = "-".join(_normalize_for_match(t) for t in cluster.tag_bucket if t)
        if tag_norm and tag_norm not in key_norm:
            return f"{key_norm}-{tag_norm}"
    return key_norm or "unnamed-skill"


def detect_and_write(
    knowledge_store: KnowledgeStore,
    experience_index: ExperienceIndex,
    suggestion_store: SuggestionStore,
    packs_root: Path,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    suggested_pack: str = "garage",
    now: datetime | None = None,
) -> list[SkillSuggestion]:
    """Run a full pattern-detection pass.

    Steps:
    1. Read all entries + records (read-only)
    2. Cluster by (problem_domain_key, tag_bucket)
    3. Filter: ``len(unique session_ids) >= threshold``
    4. Filter: ``not already_covered_by_skill``
    5. De-dup against existing suggestions whose status ∈ {proposed, accepted,
       promoted, rejected} for the same cluster (expired allows regeneration)
    6. Write new suggestions to ``proposed/``

    Returns the list of new suggestions written.
    """
    now = now or datetime.now()
    entries = knowledge_store.list_entries()
    records = experience_index.list_records()
    clusters = cluster_items(list(entries) + list(records))

    # Build a set of (domain, tag_bucket) already covered by an existing
    # non-expired suggestion (de-dup key)
    covered_keys: set[tuple[str, tuple[str, ...]]] = set()
    for status in (
        SkillSuggestionStatus.PROPOSED,
        SkillSuggestionStatus.ACCEPTED,
        SkillSuggestionStatus.PROMOTED,
        SkillSuggestionStatus.REJECTED,
    ):
        for s in suggestion_store.list_by_status(status):
            covered_keys.add((s.problem_domain_key, tuple(s.tag_bucket)))

    new_suggestions: list[SkillSuggestion] = []
    for c in clusters:
        if len(c.session_ids) < threshold:
            continue
        if (c.problem_domain_key, c.tag_bucket) in covered_keys:
            continue
        if already_covered_by_skill(c, packs_root):
            continue
        sg_id = suggestion_store.generate_id(now)
        suggestion = SkillSuggestion(
            id=sg_id,
            suggested_name=_suggested_name(c),
            suggested_description=_short_description(c),
            problem_domain_key=c.problem_domain_key,
            tag_bucket=list(c.tag_bucket),
            evidence_entries=list(c.entry_ids),
            evidence_records=list(c.record_ids),
            suggested_pack=suggested_pack,
            score=compute_score(c),
            status=SkillSuggestionStatus.PROPOSED,
            created_at=now,
            expires_at=now + timedelta(days=expiry_days),
        )
        suggestion_store.write(suggestion)
        new_suggestions.append(suggestion)
    new_suggestions.sort(key=lambda s: s.score, reverse=True)
    return new_suggestions
