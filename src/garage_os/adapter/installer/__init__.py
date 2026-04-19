"""Garage host installer subpackage.

Implements the F007 spec / D7 design contract for installing Garage-bundled
``packs/`` content into host-specific directories (Claude Code / OpenCode /
Cursor) of the cwd project at ``garage init`` time.

This subpackage lives under ``src/garage_os/adapter/`` to satisfy the
spec CON-701 mandate:

    "本 cycle 的 host adapter 注册表与三个 first-class adapter 实现必须放在
     ``src/garage_os/adapter/`` 下 ..."

Public symbols are re-exported here so callers (CLI, tests) only need:

    from garage_os.adapter.installer import install_packs, HostInstallAdapter, ...
"""

from __future__ import annotations

# T2 ships only the registry + adapters; T3 will add manifest/marker/pipeline.
from garage_os.adapter.installer.host_registry import (
    HOST_REGISTRY,
    HostInstallAdapter,
    UnknownHostError,
    get_adapter,
    list_host_ids,
    resolve_hosts_arg,
)

__all__ = [
    "HOST_REGISTRY",
    "HostInstallAdapter",
    "UnknownHostError",
    "get_adapter",
    "list_host_ids",
    "resolve_hosts_arg",
]
