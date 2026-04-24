"""Discover Garage-bundled packs from ``packs/`` directory.

Implements F007 FR-701 + design D7 §11.3 / §9.

A *pack* is a top-level subdirectory of ``packs/`` containing:

- ``pack.json`` — schema (schema_version=1, pack_id, version, description,
  skills[], agents[]); ``pack_id`` MUST equal the directory name and the
  ``skills[]`` / ``agents[]`` arrays MUST match the on-disk
  ``skills/<id>/SKILL.md`` and ``agents/<id>.md`` files (mismatch is a hard
  error, not a warning, so authors notice immediately).
- ``skills/<skill-id>/SKILL.md`` — 0..N skill source files
- ``agents/<agent-id>.md`` — 0..N agent source files
- ``README.md`` — human-readable; existence enforced by hf-traceability-review,
  not at discover time (so dev workflows can iterate without docs blocking).

Discovery never reads SKILL.md / agent.md content; the install pipeline
defers that to ``marker.inject`` time so this module stays a thin
metadata-only walker.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PACK_MANIFEST_FILENAME = "pack.json"
SKILLS_SUBDIR = "skills"
AGENTS_SUBDIR = "agents"
SKILL_FILENAME = "SKILL.md"


class InvalidPackError(ValueError):
    """Raised when a pack directory exists but pack.json is missing or malformed."""


class PackManifestMismatchError(ValueError):
    """Raised when pack.json's skills[]/agents[] don't match disk contents.

    This is a hard error rather than a warning so authors can't accidentally
    publish a pack whose declared contents don't match reality.
    """


@dataclass(frozen=True)
class Pack:
    """In-memory representation of one ``packs/<pack-id>/`` directory.

    Construction goes through ``discover_packs`` — direct instantiation in
    tests should pass already-validated values.
    """

    pack_id: str
    version: str
    schema_version: int
    description: str
    skills: list[str]
    agents: list[str]
    pack_root: Path

    def skill_source_path(self, skill_id: str) -> Path:
        return self.pack_root / SKILLS_SUBDIR / skill_id / SKILL_FILENAME

    def agent_source_path(self, agent_id: str) -> Path:
        return self.pack_root / AGENTS_SUBDIR / f"{agent_id}.md"


def discover_packs(packs_root: Path) -> list[Pack]:
    """Walk ``packs_root`` and return all valid Packs in pack_id-sorted order.

    Behavior:

    - missing or empty ``packs_root`` → ``[]`` (FR-704 acceptance #3)
    - per pack: validate pack.json schema, cross-check skills/agents arrays
      against on-disk files, fail fast on any inconsistency
    """
    if not packs_root.exists() or not packs_root.is_dir():
        return []

    packs: list[Pack] = []
    for entry in sorted(packs_root.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        # Skip dotfiles like .DS_Store dirs.
        if entry.name.startswith("."):
            continue
        # Skip non-pack directories (no pack.json). packs/ may hold WIP trees
        # or auxiliary folders without tripping the whole installer.
        if not (entry / PACK_MANIFEST_FILENAME).is_file():
            continue
        packs.append(_load_pack(entry))
    return packs


def _load_pack(pack_root: Path) -> Pack:
    """Load and validate a single pack directory."""
    manifest_path = pack_root / PACK_MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise InvalidPackError(
            f"Missing {PACK_MANIFEST_FILENAME} in pack directory: {pack_root}"
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidPackError(
            f"Invalid JSON in {manifest_path}: {exc}"
        ) from exc

    declared_id: str | None = manifest.get("pack_id")
    if declared_id != pack_root.name:
        raise InvalidPackError(
            f"pack.json pack_id={declared_id!r} does not match directory name "
            f"{pack_root.name!r} (pack_root={pack_root})"
        )

    declared_skills: list[str] = list(manifest.get("skills", []))
    declared_agents: list[str] = list(manifest.get("agents", []))

    disk_skills = _scan_disk_skills(pack_root)
    disk_agents = _scan_disk_agents(pack_root)

    if sorted(declared_skills) != sorted(disk_skills):
        raise PackManifestMismatchError(
            f"pack.json skills[]={declared_skills} does not match disk skills="
            f"{disk_skills} in {pack_root}; update pack.json or fix disk."
        )
    if sorted(declared_agents) != sorted(disk_agents):
        raise PackManifestMismatchError(
            f"pack.json agents[]={declared_agents} does not match disk agents="
            f"{disk_agents} in {pack_root}; update pack.json or fix disk."
        )

    return Pack(
        pack_id=pack_root.name,
        version=str(manifest.get("version", "0.0.0")),
        schema_version=int(manifest.get("schema_version", 1)),
        description=str(manifest.get("description", "")),
        skills=sorted(declared_skills),
        agents=sorted(declared_agents),
        pack_root=pack_root,
    )


def _scan_disk_skills(pack_root: Path) -> list[str]:
    """Return skill_ids that exist on disk under ``skills/<id>/SKILL.md``."""
    skills_dir = pack_root / SKILLS_SUBDIR
    if not skills_dir.is_dir():
        return []
    return [
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / SKILL_FILENAME).is_file()
    ]


def _scan_disk_agents(pack_root: Path) -> list[str]:
    """Return agent_ids that exist on disk under ``agents/<id>.md``."""
    agents_dir = pack_root / AGENTS_SUBDIR
    if not agents_dir.is_dir():
        return []
    return [
        entry.stem
        for entry in agents_dir.iterdir()
        if entry.is_file() and entry.suffix == ".md"
    ]
