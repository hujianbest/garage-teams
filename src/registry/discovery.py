"""Pack contract discovery and registry indexing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from contracts import (
    ArtifactContract,
    ContractParseError,
    ContractValidationError,
    EvidenceContract,
    HostAdapterContract,
    PackManifest,
    RoleContract,
    WorkflowNodeContract,
    validate_contract_version,
    validate_extensions,
)


class RegistryLoadError(ValueError):
    """Raised when discovery or indexing fails."""


@dataclass(slots=True, frozen=True)
class PackBundle:
    root: Path
    manifest: PackManifest
    roles: tuple[RoleContract, ...] = ()
    nodes: tuple[WorkflowNodeContract, ...] = ()
    artifacts: tuple[ArtifactContract, ...] = ()
    evidence: tuple[EvidenceContract, ...] = ()
    hosts: tuple[HostAdapterContract, ...] = ()


@dataclass(slots=True)
class RegistryIndex:
    packs: dict[str, PackManifest] = field(default_factory=dict)
    roles: dict[str, RoleContract] = field(default_factory=dict)
    nodes: dict[str, WorkflowNodeContract] = field(default_factory=dict)
    artifacts: dict[str, ArtifactContract] = field(default_factory=dict)
    evidence: dict[str, EvidenceContract] = field(default_factory=dict)
    hosts: dict[str, HostAdapterContract] = field(default_factory=dict)

    def register_bundle(self, bundle: PackBundle) -> None:
        manifest = bundle.manifest
        _ensure_unique(self.packs, manifest.pack_id, "pack")
        validate_contract_version(manifest.contract_version)
        validate_extensions(manifest.extensions)

        role_ids = {contract.role_id for contract in bundle.roles}
        node_ids = {contract.node_id for contract in bundle.nodes}
        artifact_roles = {contract.artifact_role for contract in bundle.artifacts}
        known_artifact_roles = set(self.artifacts) | artifact_roles

        missing_roles = sorted(set(manifest.role_refs) - role_ids)
        missing_nodes = sorted(set(manifest.node_refs) - node_ids)
        missing_entries = sorted(set(manifest.entry_node_refs) - node_ids)
        missing_artifacts = sorted(set(manifest.supported_artifact_roles) - known_artifact_roles)
        if missing_roles:
            raise RegistryLoadError(f"Pack {manifest.pack_id!r} references missing roles: {missing_roles}.")
        if missing_nodes:
            raise RegistryLoadError(f"Pack {manifest.pack_id!r} references missing nodes: {missing_nodes}.")
        if missing_entries:
            raise RegistryLoadError(
                f"Pack {manifest.pack_id!r} references missing entry nodes: {missing_entries}."
            )
        if missing_artifacts:
            raise RegistryLoadError(
                f"Pack {manifest.pack_id!r} references missing artifact roles: {missing_artifacts}."
            )

        for role in bundle.roles:
            self._register_role(role, node_ids=node_ids, pack_id=manifest.pack_id)
        for node in bundle.nodes:
            self._register_node(node, artifact_roles=known_artifact_roles, pack_id=manifest.pack_id)
        for artifact in bundle.artifacts:
            validate_contract_version(artifact.contract_version)
            validate_extensions(artifact.extensions)
            existing = self.artifacts.get(artifact.artifact_role)
            if existing is not None and existing != artifact:
                raise RegistryLoadError(
                    f"Artifact role {artifact.artifact_role!r} was already registered with a different contract."
                )
            self.artifacts.setdefault(artifact.artifact_role, artifact)
        for evidence in bundle.evidence:
            _ensure_unique(self.evidence, evidence.evidence_type, "evidence contract")
            validate_contract_version(evidence.contract_version)
            validate_extensions(evidence.extensions)
            missing_lineage = not evidence.lineage_links
            if missing_lineage:
                raise RegistryLoadError(
                    f"Evidence contract {evidence.evidence_type!r} must declare lineageLinks."
                )
            self.evidence[evidence.evidence_type] = evidence
        for host in bundle.hosts:
            _ensure_unique(self.hosts, host.adapter_id, "host adapter")
            validate_contract_version(host.contract_version)
            validate_extensions(host.extensions)
            self.hosts[host.adapter_id] = host

        self.packs[manifest.pack_id] = manifest

    def _register_role(self, role: RoleContract, *, node_ids: set[str], pack_id: str) -> None:
        _ensure_unique(self.roles, role.role_id, "role")
        validate_contract_version(role.contract_version)
        validate_extensions(role.extensions)
        if role.pack_id != pack_id:
            raise RegistryLoadError(
                f"Role {role.role_id!r} declares packId {role.pack_id!r}, expected {pack_id!r}."
            )
        missing_nodes = sorted(set(role.triggerable_nodes) - node_ids)
        if missing_nodes:
            raise RegistryLoadError(
                f"Role {role.role_id!r} references missing triggerable nodes: {missing_nodes}."
            )
        self.roles[role.role_id] = role

    def _register_node(
        self,
        node: WorkflowNodeContract,
        *,
        artifact_roles: set[str],
        pack_id: str,
    ) -> None:
        _ensure_unique(self.nodes, node.node_id, "node")
        validate_contract_version(node.contract_version)
        validate_extensions(node.extensions)
        if node.pack_id != pack_id:
            raise RegistryLoadError(
                f"Node {node.node_id!r} declares packId {node.pack_id!r}, expected {pack_id!r}."
            )
        missing_inputs = sorted(set(node.input_artifact_roles) - artifact_roles)
        missing_outputs = sorted(set(node.output_artifact_roles) - artifact_roles)
        if missing_inputs:
            raise RegistryLoadError(
                f"Node {node.node_id!r} references missing input artifact roles: {missing_inputs}."
            )
        if missing_outputs:
            raise RegistryLoadError(
                f"Node {node.node_id!r} references missing output artifact roles: {missing_outputs}."
            )
        self.nodes[node.node_id] = node


def _ensure_unique(index: dict[str, object], key: str, label: str) -> None:
    if key in index:
        raise RegistryLoadError(f"Duplicate {label} id {key!r}.")


def _load_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryLoadError(f"Missing contract file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryLoadError(f"Invalid JSON in contract file: {path}") from exc
    if not isinstance(payload, dict):
        raise RegistryLoadError(f"Expected top-level object in contract file: {path}")
    return payload


def _parse_many(paths: Iterable[Path], parser: object) -> tuple[object, ...]:
    parsed: list[object] = []
    for path in sorted(paths):
        try:
            parsed.append(parser(_load_json(path)))
        except (ContractParseError, ContractValidationError) as exc:
            raise RegistryLoadError(f"Failed to parse contract file {path}: {exc}") from exc
    return tuple(parsed)


def discover_pack_bundle(pack_root: Path) -> PackBundle | None:
    contracts_root = pack_root / "contracts"
    manifest_path = contracts_root / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        manifest = PackManifest.from_mapping(_load_json(manifest_path))
    except ContractParseError as exc:
        raise RegistryLoadError(f"Failed to parse manifest {manifest_path}: {exc}") from exc

    return PackBundle(
        root=pack_root,
        manifest=manifest,
        roles=_parse_many((contracts_root / "roles").glob("*.json"), RoleContract.from_mapping),  # type: ignore[arg-type]
        nodes=_parse_many((contracts_root / "nodes").glob("*.json"), WorkflowNodeContract.from_mapping),  # type: ignore[arg-type]
        artifacts=_parse_many((contracts_root / "artifacts").glob("*.json"), ArtifactContract.from_mapping),  # type: ignore[arg-type]
        evidence=_parse_many((contracts_root / "evidence").glob("*.json"), EvidenceContract.from_mapping),  # type: ignore[arg-type]
        hosts=_parse_many((contracts_root / "hosts").glob("*.json"), HostAdapterContract.from_mapping),  # type: ignore[arg-type]
    )


def discover_pack_bundles(pack_roots: Iterable[Path]) -> tuple[PackBundle, ...]:
    bundles: list[PackBundle] = []
    for pack_root in pack_roots:
        bundle = discover_pack_bundle(pack_root)
        if bundle is not None:
            bundles.append(bundle)
    return tuple(bundles)


def build_registry(pack_roots: Iterable[Path]) -> RegistryIndex:
    registry = RegistryIndex()
    for bundle in discover_pack_bundles(pack_roots):
        registry.register_bundle(bundle)
    return registry
