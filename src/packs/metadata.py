from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from continuity import GrowthTarget


class PackMetadataError(ValueError):
    """Raised when a pack-local metadata surface cannot be parsed."""


def _require_mapping(value: Any, *, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PackMetadataError(f"Expected {context} to be an object.")
    return value


def _require_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise PackMetadataError(f"Expected field {key!r} to be a non-empty string.")
    return value


def _string_tuple(data: Mapping[str, Any], key: str, *, required: bool) -> tuple[str, ...]:
    value = data.get(key)
    if value is None:
        if required:
            raise PackMetadataError(f"Missing required field {key!r}.")
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise PackMetadataError(f"Expected field {key!r} to be a list of non-empty strings.")
    return tuple(value)


@dataclass(slots=True, frozen=True)
class PackContinuityCandidateFamily:
    candidate_family_id: str
    target: GrowthTarget
    source_evidence_types: tuple[str, ...]
    node_refs: tuple[str, ...]
    summary: str
    rationale: str
    preferred_governance_actions: tuple[str, ...] = ()
    disallowed_without: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PackContinuityCandidateFamily":
        data = dict(_require_mapping(raw, context="candidate family"))
        try:
            target = GrowthTarget(_require_str(data, "target"))
        except ValueError as exc:
            raise PackMetadataError(f"Unsupported continuity target {data.get('target')!r}.") from exc
        return cls(
            candidate_family_id=_require_str(data, "candidateFamilyId"),
            target=target,
            source_evidence_types=_string_tuple(data, "sourceEvidenceTypes", required=True),
            node_refs=_string_tuple(data, "nodeRefs", required=False),
            summary=_require_str(data, "summary"),
            rationale=_require_str(data, "rationale"),
            preferred_governance_actions=_string_tuple(
                data,
                "preferredGovernanceActions",
                required=False,
            ),
            disallowed_without=_string_tuple(data, "disallowedWithout", required=False),
        )


@dataclass(slots=True, frozen=True)
class PackContinuityMap:
    pack_id: str
    contract_version: str
    candidate_families: tuple[PackContinuityCandidateFamily, ...]
    blocked_patterns: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PackContinuityMap":
        data = dict(_require_mapping(raw, context="continuity map"))
        families_raw = data.get("candidateFamilies")
        if not isinstance(families_raw, list):
            raise PackMetadataError("Expected field 'candidateFamilies' to be a list.")
        return cls(
            pack_id=_require_str(data, "packId"),
            contract_version=_require_str(data, "contractVersion"),
            candidate_families=tuple(
                PackContinuityCandidateFamily.from_mapping(item)
                for item in families_raw
            ),
            blocked_patterns=_string_tuple(data, "blockedPatterns", required=False),
        )


def load_pack_continuity_map(
    pack_root: Path,
    *,
    relative_path: str = "continuity/candidates.json",
) -> PackContinuityMap:
    target = pack_root / relative_path
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PackMetadataError(f"Missing pack continuity map at {target}.") from exc
    except json.JSONDecodeError as exc:
        raise PackMetadataError(f"Invalid JSON in pack continuity map at {target}.") from exc
    return PackContinuityMap.from_mapping(_require_mapping(raw, context="continuity map"))
