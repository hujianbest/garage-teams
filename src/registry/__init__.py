"""Registry discovery and indexing for Garage pack contracts."""

from .discovery import (
    PackBundle,
    RegistryIndex,
    RegistryLoadError,
    build_registry,
    discover_pack_bundle,
    discover_pack_bundles,
)

__all__ = [
    "PackBundle",
    "RegistryIndex",
    "RegistryLoadError",
    "build_registry",
    "discover_pack_bundle",
    "discover_pack_bundles",
]
