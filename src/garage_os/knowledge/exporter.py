"""F012-D T4: knowledge export --anonymize (FR-1211..1213 + ADR-D12-5 r2).

Mixed-strategy export (per ADR-D12-5 + spec-review-r1 Mi-5 fix):
- (a) ``KnowledgeStore.list_entries()`` for metadata index (id / topic / tags / type / date)
- (b) ``filesystem read .garage/knowledge/<kind>/<id>.md`` for raw markdown bytes
  (preserves YAML front matter byte-level; only body is anonymized)

ANONYMIZE_RULES = 7 categories:
- 5 categories 1:1 with SENSITIVE_RULES (password, api_key, secret, token, private_key)
- 2 categories specific to anonymize: email, sha1_hash
"""

from __future__ import annotations

import os
import re
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.storage.file_storage import FileStorage


# F012 ADR-D12-5 r2 + spec FR-1212: 7 categories
# 5 base shared with SENSITIVE_RULES (pack_install.py, T3); 2 anonymize-specific (email, sha1_hash).
ANONYMIZE_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("email",
     re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
     "<REDACTED:email>"),
    ("password",
     re.compile(r'(?P<key>["\']?password["\']?\s*[:=]\s*)\S+', re.IGNORECASE),
     r"\g<key><REDACTED>"),
    ("api_key",
     re.compile(r'(?P<key>["\']?api[_-]?key["\']?\s*[:=]\s*)\S+', re.IGNORECASE),
     r"\g<key><REDACTED>"),
    ("secret",
     re.compile(r'(?P<key>["\']?secret["\']?\s*[:=]\s*)\S+', re.IGNORECASE),
     r"\g<key><REDACTED>"),
    ("token",
     re.compile(r'(?P<key>["\']?token["\']?\s*[:=]\s*)\S+', re.IGNORECASE),
     r"\g<key><REDACTED>"),
    ("sha1_hash",
     re.compile(r"\b[a-f0-9]{40}\b"),
     "<REDACTED:sha1>"),
    ("private_key",
     re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----",
                re.DOTALL),
     "-----REDACTED-----"),
]


def load_user_extra_rules() -> list[tuple[str, re.Pattern[str], str]]:
    """Read ``~/.garage/anonymize-patterns.txt`` for additional regex rules.

    File format: one regex per line; lines starting with ``#`` are comments.
    Each user rule replaces with ``<REDACTED:user>``.
    """
    rules_file = Path.home() / ".garage" / "anonymize-patterns.txt"
    if not rules_file.is_file():
        return []
    extra: list[tuple[str, re.Pattern[str], str]] = []
    for i, line in enumerate(rules_file.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            pattern = re.compile(stripped)
        except re.error:
            continue  # skip invalid regex
        extra.append((f"user_rule_{i}", pattern, "<REDACTED:user>"))
    return extra


@dataclass
class ExportSummary:
    """F012-D FR-1211: returned by export_anonymized."""
    entry_count: int
    rule_hit_counts: dict[str, int]  # rule_name -> count
    output_path: Path | None  # None on dry-run
    skipped: bool = False  # always False (dry-run still returns ExportSummary)


def _split_front_matter(content: str) -> tuple[str, str]:
    """Split a markdown file's YAML front matter from body.

    Returns (front_matter_block_with_delimiters, body). If no front matter,
    returns ("", content).
    """
    if not content.startswith("---\n"):
        return ("", content)
    # Find closing ---
    rest = content[4:]
    end_idx = rest.find("\n---\n")
    if end_idx == -1:
        return ("", content)
    front = "---\n" + rest[: end_idx + 5]  # include "\n---\n"
    body = rest[end_idx + 5:]
    return (front, body)


def _anonymize_body(body: str, rules: list[tuple[str, re.Pattern[str], str]],
                    hit_counts: dict[str, int]) -> str:
    """Apply all anonymize rules to body; mutate hit_counts in place."""
    for rule_name, pattern, replacement in rules:
        new_body, n = pattern.subn(replacement, body)
        if n > 0:
            hit_counts[rule_name] = hit_counts.get(rule_name, 0) + n
        body = new_body
    return body


def export_anonymized(
    workspace_root: Path,
    *,
    output_dir: Path | None = None,
    dry_run: bool = False,
    stderr: IO[str] | None = None,
) -> ExportSummary:
    """F012-D FR-1211..1213: export ``.garage/knowledge/`` to anonymized tarball.

    - Default output_dir: ``~/.garage/exports/`` (workspace-外, 防止 git 误 commit; Mi-3 fix)
    - When user passes ``output_dir`` inside workspace_root and ``.gitignore`` lacks
      ``exports/``, emit stderr warn (Mi-3).
    - dry_run: print rule hit summary + entry count, no tarball write.
    """
    err = stderr if stderr is not None else sys.stderr

    if output_dir is None:
        output_dir = Path.home() / ".garage" / "exports"
    else:
        # Mi-3 warn if inside workspace and .gitignore doesn't exclude
        try:
            output_dir.resolve().relative_to(workspace_root.resolve())
            # Inside workspace
            gitignore = workspace_root / ".gitignore"
            ignore_text = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
            output_basename = output_dir.name
            if output_basename and output_basename not in ignore_text:
                print(
                    f"WARNING: output dir '{output_dir}' is inside workspace and "
                    f"'.gitignore' does not contain '{output_basename}/'; "
                    "anonymized tarball may be accidentally committed.",
                    file=err,
                )
        except ValueError:
            pass  # output_dir is outside workspace

    # Mixed strategy: KnowledgeStore for metadata count, filesystem for body
    storage = FileStorage(workspace_root / ".garage")
    knowledge_store = KnowledgeStore(storage)
    entries = knowledge_store.list_entries()
    entry_count = len(entries)

    rules = list(ANONYMIZE_RULES) + load_user_extra_rules()
    hit_counts: dict[str, int] = {}

    if dry_run:
        # Dry-run: scan all knowledge .md files, report counts, no tarball
        for kind_dir_name in ("decisions", "patterns", "solutions", "style"):
            kind_dir = workspace_root / ".garage" / "knowledge" / kind_dir_name
            if not kind_dir.is_dir():
                continue
            for md_file in kind_dir.glob("*.md"):
                content = md_file.read_text(encoding="utf-8", errors="replace")
                front, body = _split_front_matter(content)
                _anonymize_body(body, rules, hit_counts)  # mutates hit_counts
        total_hits = sum(hit_counts.values())
        print(
            f"DRY RUN: would export {entry_count} entries; "
            f"{total_hits} sensitive matches would be redacted across {len(hit_counts)} rule(s)",
            file=err,
        )
        for rule, n in sorted(hit_counts.items()):
            print(f"  {rule}: {n} matches", file=err)
        return ExportSummary(
            entry_count=entry_count,
            rule_hit_counts=hit_counts,
            output_path=None,
        )

    # Real export: write tarball
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
    safe_ts = timestamp.replace(":", "")  # filename-safe
    tarball_path = output_dir / f"knowledge-{safe_ts}.tar.gz"

    with tempfile.TemporaryDirectory(prefix="garage-export-staging-") as staging:
        staging_root = Path(staging) / "knowledge-export"
        staging_root.mkdir()

        # Per-kind: copy + anonymize body, preserve front matter
        for kind_dir_name in ("decisions", "patterns", "solutions", "style"):
            kind_dir = workspace_root / ".garage" / "knowledge" / kind_dir_name
            if not kind_dir.is_dir():
                continue
            staging_kind = staging_root / kind_dir_name
            staging_kind.mkdir()
            for md_file in kind_dir.glob("*.md"):
                content = md_file.read_text(encoding="utf-8", errors="replace")
                front, body = _split_front_matter(content)
                anonymized_body = _anonymize_body(body, rules, hit_counts)
                (staging_kind / md_file.name).write_text(
                    front + anonymized_body, encoding="utf-8",
                )

        # Write manifest.json
        manifest = {
            "export_at": timestamp,
            "entry_count": entry_count,
            "kinds": [d.name for d in staging_root.iterdir() if d.is_dir()],
            "rule_hit_counts": hit_counts,
            "anonymize_rules": [name for name, _, _ in rules],
        }
        import json
        (staging_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # Tar it up
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(staging_root, arcname="knowledge-export")

    return ExportSummary(
        entry_count=entry_count,
        rule_hit_counts=hit_counts,
        output_path=tarball_path,
    )
