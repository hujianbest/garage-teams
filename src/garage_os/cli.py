"""Command-line interface for Garage OS."""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from garage_os.adapter.claude_code_adapter import ClaudeCodeAdapter
from garage_os.adapter.installer import (
    ConflictingSkillError,
    InvalidPackError,
    MalformedFrontmatterError,
    ManifestMigrationError,
    PackManifestMismatchError,
    UnknownHostError,
    UnknownScopeError,
    UserHomeNotFoundError,
    install_packs,
    list_host_ids,
    read_manifest,
    resolve_hosts_arg,
)
from garage_os.adapter.installer.interactive import (
    prompt_hosts,
    prompt_scopes_per_host,
)

# F004 § 11.5: stable stdout markers for the two CLI abandon paths so users
# (and downstream agents) can grep the audit log to differentiate intent.
# - NO_PUB:    --action=abandon, dropped before any publication attempt.
# - CONFLICT:  --action=accept --strategy=abandon, dropped because publisher
#              detected a real conflict with already-published knowledge.
MEMORY_REVIEW_ABANDONED_NO_PUB = (
    "Candidate '{cid}' abandoned without publication attempt"
)
MEMORY_REVIEW_ABANDONED_CONFLICT = (
    "Candidate '{cid}' abandoned due to conflict with published knowledge"
)

# F005 § 9.5 / NFR-504: stable stdout / stderr markers for the CLI
# authoring path (`garage knowledge add|edit|show|delete` and
# `garage experience add|show|delete`). All CLI handlers MUST format their
# success / failure output via these constants so that downstream Agents
# can grep-match without parsing prose.
KNOWLEDGE_ADDED_FMT = "Knowledge entry '{eid}' added"
KNOWLEDGE_EDITED_FMT = "Knowledge entry '{eid}' edited (version {version})"
KNOWLEDGE_DELETED_FMT = "Knowledge entry '{eid}' deleted"
KNOWLEDGE_NOT_FOUND_FMT = "Knowledge entry '{eid}' not found"
KNOWLEDGE_ALREADY_EXISTS_FMT = (
    "Entry with id '{eid}' already exists; "
    "pass --id to override or change inputs"
)
EXPERIENCE_ADDED_FMT = "Experience record '{rid}' added"
EXPERIENCE_DELETED_FMT = "Experience record '{rid}' deleted"
EXPERIENCE_NOT_FOUND_FMT = "Experience record '{rid}' not found"
EXPERIENCE_ALREADY_EXISTS_FMT = (
    "Experience record with id '{rid}' already exists; "
    "pass --id to override or change inputs"
)
EXPERIENCE_READ_ERR_FMT = "Failed to read experience record '{rid}': {err}"

ERR_NO_GARAGE = "No .garage/ directory found. Run 'garage init' first."
ERR_CONTENT_AND_FILE_MUTEX = "--content and --from-file are mutually exclusive"
ERR_ADD_REQUIRES_CONTENT = "add requires --content or --from-file"
ERR_FILE_NOT_FOUND_FMT = "File not found: {path}"
ERR_EDIT_REQUIRES_FIELD = (
    "edit requires at least one of --topic / --tags / --content / "
    "--from-file / --status"
)

# F005 § ADR-503: the `cli:` namespace prefix is reserved for source markers
# written by the CLI authoring path. Any artifact / source_artifact value
# starting with `cli:` MUST come from this CLI; publisher-path values MUST NOT
# start with `cli:`. Tests grep on this prefix to assert provenance.
CLI_SOURCE_KNOWLEDGE_ADD = "cli:knowledge-add"
CLI_SOURCE_KNOWLEDGE_EDIT = "cli:knowledge-edit"
CLI_SOURCE_EXPERIENCE_ADD = "cli:experience-add"
# F006 § FR-607 / ADR-503 延伸: handler `_knowledge_link` 写入 entry 时强制
# 覆写 source_artifact 为该值，让审计层面"手工建图动作"与"add/edit/publisher
# 路径"完全可分。
CLI_SOURCE_KNOWLEDGE_LINK = "cli:knowledge-link"

# F007 § 6 FR-709 / NFR-704: stable stdout / stderr markers for the
# `garage init --hosts ...` host installer path. Mirrors the F005
# `KNOWLEDGE_*_FMT` pattern so downstream Agents / tests can grep-match.
#
# Format-string ownership map (consolidated per F007 hf-code-review F-2):
# - INSTALLED_FMT, ERR_PACK_INVALID_FMT, ERR_MARKER_FAILED_FMT,
#   ERR_HOST_FILE_FAILED_FMT are CLI-emitted and live here.
# - ERR_UNKNOWN_HOST_FMT lives in
#   garage_os.adapter.installer.host_registry (built into UnknownHostError);
#   the CLI re-prints the exception message verbatim.
# - WARN_LOCALLY_MODIFIED_FMT, WARN_OVERWRITE_FORCED_FMT, MSG_NO_PACKS_FMT
#   live in garage_os.adapter.installer.pipeline (pipeline emits them
#   directly to stderr/stdout during install).
INSTALLED_FMT = (
    "Installed {n_skills} skills, {n_agents} agents into hosts: {hosts}"
)
ERR_PACK_INVALID_FMT = "Invalid pack: {detail}"
ERR_MARKER_FAILED_FMT = "SKILL.md marker injection failed: {detail}"
ERR_HOST_FILE_FAILED_FMT = "Failed to write host file: {detail}"

# F006 § 9.5 / NFR-604: stable stdout / stderr markers for the recall + graph
# CLI surface (`garage recommend`, `garage knowledge link`, `garage knowledge
# graph`).
RECOMMEND_NO_RESULTS_FMT = (
    "No matching knowledge or experience for query: '{query}'"
)
KNOWLEDGE_LINKED_FMT = "Linked '{src}' -> '{dst}' ({kind})"
KNOWLEDGE_LINK_ALREADY_FMT = "Already linked '{src}' -> '{dst}' ({kind})"
ERR_LINK_FROM_AMBIGUOUS_FMT = (
    "Knowledge entry id '{eid}' is ambiguous; found in types {types}. "
    "Rename one of the entries to disambiguate."
)
GRAPH_OUTGOING_HEADER = "Outgoing edges:"
GRAPH_INCOMING_HEADER = "Incoming edges:"
GRAPH_EDGE_NONE = "  (none)"
KNOWLEDGE_GRAPH_NODE_FMT = "[{type}] {topic}"

from garage_os.knowledge.experience_index import ExperienceIndex
from garage_os.knowledge.knowledge_store import KnowledgeStore
from garage_os.memory.candidate_store import CandidateStore
from garage_os.memory.extraction_orchestrator import load_memory_config
from garage_os.memory.publisher import KnowledgePublisher
from garage_os.memory.recommendation_service import (
    RecommendationContextBuilder,
    RecommendationService,
)
from garage_os.runtime.session_manager import SessionManager
from garage_os.storage import FileStorage
from garage_os.types import (
    ExperienceRecord,
    KnowledgeEntry,
    KnowledgeType,
    SessionState,
)


# Sub-directories to create under .garage/
GARAGE_DIRS = [
    "config/tools",
    "contracts",
    "knowledge/.metadata",
    "knowledge/decisions",
    "knowledge/patterns",
    "knowledge/solutions",
    "experience/records",
    "memory/candidates/batches",
    "memory/candidates/items",
    "memory/confirmations",
    "sessions/active",
    "sessions/archived",
]

GARAGE_README = """# .garage/ — Garage OS Runtime Data

This directory contains all runtime data for Garage OS.

- **config/**: Platform and adapter configurations
- **contracts/**: Interface contracts
- **knowledge/**: Knowledge entries (decisions, patterns, solutions)
- **experience/**: Experience records
- **memory/**: Candidate drafts, review batches, and confirmation records
- **sessions/**: Active and archived sessions
"""

DEFAULT_PLATFORM_CONFIG = {
    "schema_version": 1,
    "platform_name": "Garage Agent OS",
    "stage": 1,
    "storage_mode": "artifact-first",
    "host_type": "claude-code",
    "session_timeout_seconds": 7200,
    "max_active_sessions": 1,
    "knowledge_indexing": "manual",
    "memory": {
        "extraction_enabled": False,
        "recommendation_enabled": False,
    },
}

DEFAULT_HOST_ADAPTER_CONFIG = {
    "schema_version": 1,
    "host_type": "claude-code",
    "interaction_mode": "file-system",
    "capabilities": {
        "session_state_api": False,
        "file_read_write": True,
        "memory_auto_load": True,
        "subprocess": True,
    },
}


def _find_garage_root(start: Optional[Path] = None) -> Path:
    """Find the project root by searching upward for .garage/ or pyproject.toml.

    Falls back to current working directory.
    """
    current = start or Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".garage").is_dir():
            return parent
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


def _init(
    garage_root: Path,
    *,
    hosts_arg: Optional[str] = None,
    yes: bool = False,
    force: bool = False,
    scope: str = "project",
) -> int:
    """Create the .garage/ directory structure under garage_root.

    F002 contract preserved: when called without any host installer args
    (no ``hosts_arg`` / ``yes`` / TTY prompt → empty hosts) and no packs/
    present, output is byte-equal to the legacy ``Initialized Garage OS in
    <path>`` line (CON-702).

    F007 extension: when ``hosts_arg`` is provided OR a TTY user selects
    one or more hosts, also installs ``packs/<pack-id>/`` content into the
    host-specific directories (e.g. ``.claude/skills/``).

    F009 extension: ``scope`` 参数 (default "project", CON-901 等价 F007/F008
    行为). per-host scope override via ``--hosts <host>:<scope>`` 语法被
    ``_resolve_init_hosts`` 解析后 override 全局 ``scope`` 默认.
    """
    garage_dir = garage_root / ".garage"
    garage_dir.mkdir(parents=True, exist_ok=True)

    for subdir in GARAGE_DIRS:
        (garage_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Write README if not present
    readme_path = garage_dir / "README.md"
    if not readme_path.exists():
        readme_path.write_text(GARAGE_README.strip() + "\n", encoding="utf-8")

    platform_config_path = garage_dir / "config" / "platform.json"
    if not platform_config_path.exists():
        platform_config_path.write_text(
            json.dumps(DEFAULT_PLATFORM_CONFIG, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    host_adapter_config_path = garage_dir / "config" / "host-adapter.json"
    if not host_adapter_config_path.exists():
        host_adapter_config_path.write_text(
            json.dumps(DEFAULT_HOST_ADAPTER_CONFIG, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Initialized Garage OS in {garage_dir}")

    # F007: optional host installer step. Returns early without touching any
    # host directory when the resolved host list is empty (CON-702).
    # F009: 同时返回 scopes_per_host (per-host scope override + 全局 --scope).
    try:
        hosts, scopes_per_host = _resolve_init_hosts(
            hosts_arg=hosts_arg, yes=yes, scope_default=scope
        )
    except UnknownHostError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UnknownScopeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not hosts:
        return 0

    try:
        summary = install_packs(
            workspace_root=garage_root,
            packs_root=garage_root / "packs",
            hosts=hosts,
            force=force,
            scopes_per_host=scopes_per_host,
        )
    except UnknownHostError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ConflictingSkillError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (InvalidPackError, PackManifestMismatchError) as exc:
        print(ERR_PACK_INVALID_FMT.format(detail=exc), file=sys.stderr)
        return 1
    except MalformedFrontmatterError as exc:
        print(ERR_MARKER_FAILED_FMT.format(detail=exc), file=sys.stderr)
        return 1
    except ManifestMigrationError as exc:
        print(f"Manifest migration failed: {exc}", file=sys.stderr)
        return 1
    except UserHomeNotFoundError as exc:
        print(f"Cannot determine user home directory: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(ERR_HOST_FILE_FAILED_FMT.format(detail=exc), file=sys.stderr)
        return 1

    print(
        INSTALLED_FMT.format(
            n_skills=summary.n_skills,
            n_agents=summary.n_agents,
            hosts=", ".join(summary.hosts),
        )
    )
    # F009 FR-909: 多 scope 时另起一行附加 scope 分布 (F007 grep 兼容硬约束:
    # 第二行 marker 字面不变, 附加段独立一行)
    scopes_used = set(scopes_per_host.values()) if scopes_per_host else set()
    if len(scopes_used) > 1:
        n_user = sum(1 for s in scopes_per_host.values() if s == "user")
        n_project = sum(1 for s in scopes_per_host.values() if s == "project")
        print(f"  ({n_user} user-scope hosts, {n_project} project-scope hosts)")
    return 0


def _resolve_init_hosts(
    *,
    hosts_arg: Optional[str],
    yes: bool,
    scope_default: str = "project",
) -> tuple[list[str], dict[str, str]]:
    """Determine which hosts to install into + per-host scope.

    F007/F008 行为 (CON-901): scope_default='project' 等价 F007/F008
    既有调用形态 (全部 host scope=project, 等价 install_packs 不传
    scopes_per_host).

    Resolution table (D7 §10.1 + F009 FR-901/902/903):
        --hosts <list>         → resolve_hosts_arg(<list>) → 解析 <host>:<scope>
                                  per-host override; 未带 :scope 的 host 用
                                  scope_default
        --yes (no --hosts)     → ([], {}) (equivalent to --hosts none, FR-702)
        no flags + TTY         → prompt_hosts → prompt_scopes_per_host
                                  (ADR-D9-5 candidate C 三个开关)
        no flags + non-TTY     → ([], {}) + stderr notice (FR-703 + FR-903 #4)

    Returns:
        (hosts, scopes_per_host): hosts 是 sorted host_id list;
        scopes_per_host 是 {host_id: scope} 映射, 默认 scope_default.
    """
    if hosts_arg is not None:
        # F009: 解析 <host>:<scope> 二元组
        parsed = resolve_hosts_arg(hosts_arg)
        hosts = [host_id for host_id, _ in parsed]
        scopes: dict[str, str] = {}
        for host_id, scope_override in parsed:
            scopes[host_id] = (
                scope_override if scope_override is not None else scope_default
            )
        return hosts, scopes
    if yes:
        return [], {}
    selected = prompt_hosts(list_host_ids(), stdin=sys.stdin, stderr=sys.stderr)
    if not selected:
        return [], {}
    # F009 ADR-D9-5 candidate C: 第二轮 scope 选择
    scopes_interactive = prompt_scopes_per_host(
        selected, stdin=sys.stdin, stderr=sys.stderr
    )
    return selected, scopes_interactive


def _status(garage_root: Path) -> None:
    """Read .garage/ and display statistics."""
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)

    # Count sessions using the real on-disk session layout:
    # sessions/<state>/<session_id>/session.json
    active_sessions = storage.list_files("sessions/active", "*/session.json")
    archived_sessions = storage.list_files("sessions/archived", "*/session.json")
    total_sessions = len(active_sessions) + len(archived_sessions)

    # Count knowledge entries
    decisions = storage.list_files("knowledge/decisions", "*.md")
    patterns = storage.list_files("knowledge/patterns", "*.md")
    solutions = storage.list_files("knowledge/solutions", "*.md")
    total_knowledge = len(decisions) + len(patterns) + len(solutions)

    # Count experience records
    experience_records = storage.list_files("experience/records", "*.json")
    total_experience = len(experience_records)

    # Find most recent experience
    recent_experience: Optional[str] = None
    if total_experience > 0:
        latest = max(experience_records, key=lambda p: p.stat().st_mtime)
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            recent_experience = (
                data.get("updated_at")
                or data.get("created_at")
                or data.get("timestamp")
                or str(latest)
            )
        except (json.JSONDecodeError, OSError):
            recent_experience = str(latest)

    has_data = total_sessions > 0 or total_knowledge > 0 or total_experience > 0

    if not has_data:
        print("No data")
        return

    print(f"Sessions: {total_sessions} (active: {len(active_sessions)}, archived: {len(archived_sessions)})")
    print(
        f"Knowledge entries: {total_knowledge} "
        f"(decisions: {len(decisions)}, patterns: {len(patterns)}, solutions: {len(solutions)})"
    )
    print(f"Experience records: {total_experience}")
    if recent_experience:
        print(f"Most recent experience: {recent_experience}")

    # F009 FR-908 + ADR-D9-7: 按 scope 分组打印 installed packs (nested bullets).
    # F008 兼容: manifest 不存在时跳过 (与既有 status 行为一致).
    try:
        manifest = read_manifest(garage_dir)
    except ManifestMigrationError:
        manifest = None
    if manifest is not None and manifest.files:
        # 按 scope 分组 → 每组按 host 子分组 → 计 skill / agent 数 + dst 前缀
        by_scope: dict[str, dict[str, dict[str, int]]] = {}
        for entry in manifest.files:
            scope = entry.scope
            host = entry.host
            kind_key = "skills" if "skills/" in entry.dst else "agents"
            by_scope.setdefault(scope, {}).setdefault(host, {"skills": 0, "agents": 0})
            by_scope[scope][host][kind_key] += 1

        # ADR-D9-7: 先 project, 再 user (固定顺序)
        for scope_label in ("project", "user"):
            if scope_label not in by_scope:
                continue
            print(f"Installed packs ({scope_label} scope):")
            for host in sorted(by_scope[scope_label].keys()):
                counts = by_scope[scope_label][host]
                line = f"  {host}: {counts['skills']} skills"
                if counts["agents"] > 0:
                    line += f", {counts['agents']} agents"
                print(line)

    # F010 ADR-D10-12: append sync status section after F009 packs section.
    # Early return inside _print_sync_status when sync-manifest.json does not exist
    # (CON-1001 fallback: status output stays byte-for-byte identical to F009 baseline
    # for users who never ran `garage sync`).
    _print_sync_status(garage_dir)


def _print_sync_status(garage_dir: Path) -> None:
    """F010 ADR-D10-12: print sync status section in `garage status` output.

    Early-return when sync-manifest.json does not exist (do not print any sync
    string). This guarantees CON-1001 byte-level compat with F009 baseline status
    output for users who never ran `garage sync`.
    """
    from garage_os.sync.manifest import SyncManifestMigrationError, read_sync_manifest

    try:
        manifest = read_sync_manifest(garage_dir)
    except SyncManifestMigrationError:
        manifest = None
    if manifest is None or not manifest.targets:
        return  # CON-1001 fallback

    print("Last synced (per host):")
    for entry in sorted(manifest.targets, key=lambda e: e.wrote_at, reverse=True):
        try:
            size_kb = Path(entry.path).stat().st_size // 1024 if Path(entry.path).exists() else 0
        except OSError:
            size_kb = 0
        print(f"  {entry.host} ({entry.scope}): {entry.path} ({size_kb} KB) at {entry.wrote_at}")


def _sync(
    garage_root: Path,
    *,
    hosts_arg: Optional[str],
    scope_default: str = "project",
    force: bool = False,
) -> int:
    """F010 _sync entry: orchestrate `garage sync` CLI."""
    from garage_os.sync.pipeline import sync_hosts as _sync_hosts_pipeline

    # Resolve hosts: default --hosts all when unspecified
    arg = hosts_arg if hosts_arg is not None else "all"
    try:
        parsed = resolve_hosts_arg(arg)
    except (UnknownHostError, UnknownScopeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    hosts = [host_id for host_id, _ in parsed]
    if not hosts:
        # 'none' or empty: nothing to do, exit 0 (与 F007 init none 同精神)
        print("No hosts to sync.")
        return 0

    scopes_per_host: dict[str, str] = {}
    for host_id, override in parsed:
        scopes_per_host[host_id] = override if override is not None else scope_default

    try:
        summary = _sync_hosts_pipeline(
            garage_root,
            hosts,
            scopes_per_host=scopes_per_host,
            force=force,
        )
    except (UnknownHostError, UnknownScopeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Cannot determine user home directory: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        return 1

    # FR-1008 stdout marker
    print(
        f"Synced {summary.knowledge_count} knowledge entries + "
        f"{summary.experience_count} experience records into hosts: "
        f"{', '.join(sorted(hosts))}"
    )
    if summary.n_hosts_skipped > 0:
        print(
            f"  ({summary.n_hosts_skipped} hosts skipped due to local modification; "
            f"use --force to override)"
        )
    return 0


def _session_import(
    garage_root: Path,
    *,
    from_host: str,
    all_flag: bool = False,
) -> int:
    """F010 _session_import entry: orchestrate `garage session import --from <host>`."""
    from garage_os.ingest.host_readers import HOST_READERS, resolve_host_id
    from garage_os.ingest.pipeline import import_conversations
    from garage_os.ingest.selector import prompt_select

    # Resolve canonical host_id (alias support: claude → claude-code)
    try:
        canonical_host = resolve_host_id(from_host)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    # Instantiate reader (catches NotImplementedError for cursor stub at use time)
    try:
        reader_cls = HOST_READERS[canonical_host]
        reader = reader_cls()
        # Probe via list_conversations to surface NotImplementedError early
        try:
            summaries = reader.list_conversations()
        except NotImplementedError as exc:
            print(
                f"{from_host} history import is not yet implemented: {exc}",
                file=sys.stderr,
            )
            return 1
    except KeyError:
        print(f"Unknown host: {from_host}", file=sys.stderr)
        return 1

    # Select conversations (interactive or --all)
    if all_flag:
        selected_ids = [s.conversation_id for s in summaries]
        if not selected_ids:
            print(f"No conversations found for {canonical_host}.")
            return 0
    else:
        selected_ids = prompt_select(summaries)
        if not selected_ids:
            return 0  # user cancel / non-TTY / no summaries (notice already in stderr)

    # Run import pipeline
    try:
        summary = import_conversations(
            garage_root,
            canonical_host,
            selected_ids,
            reader=reader,
        )
    except OSError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1

    # FR-1005/1006 stdout marker
    if summary.skipped > 0:
        print(
            f"Imported {summary.imported} conversations from {canonical_host} "
            f"({summary.skipped} skipped, batch-id: {summary.batch_id})"
        )
    else:
        print(
            f"Imported {summary.imported} conversations from {canonical_host} "
            f"(batch-id: {summary.batch_id})"
        )
    return 0


def _run(garage_root: Path, skill_name: str, timeout: int = 300) -> int:
    """Run a Garage skill and record the experience.

    Args:
        garage_root: Path to the project root
        skill_name: Name of the skill to invoke
        timeout: Timeout in seconds for Claude Code execution
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return 1

    storage = FileStorage(garage_dir)
    memory_config = load_memory_config(storage)

    # Create session manager and start a new session
    session_manager = SessionManager(storage)
    session = session_manager.create_session(
        pack_id=skill_name,
        topic=f"Run skill: {skill_name}",
        user_goals=[],
        constraints=[],
    )
    session_manager.update_session(
        session.session_id,
        state=SessionState.RUNNING,
        context_metadata={
            "domain": "general",
            "problem_domain": skill_name,
            "tags": [skill_name],
        },
    )

    # Create adapter and invoke the skill
    adapter = ClaudeCodeAdapter(garage_root, timeout=timeout)

    if memory_config["recommendation_enabled"]:
        recommendation_service = RecommendationService(
            KnowledgeStore(storage),
            ExperienceIndex(storage),
        )
        context_builder = RecommendationContextBuilder()
        repo_state = adapter.get_repository_state()
        recommendation_context = context_builder.build(
            skill_name=skill_name,
            params={},
            session_topic=session.topic,
            session_metadata=session.context.metadata,
            repo_state=repo_state,
            artifact_paths=[],
        )
        recommendations = recommendation_service.recommend(recommendation_context)
        if recommendations:
            print("Recommendations:")
            for item in recommendations[:3]:
                reasons = ", ".join(item["match_reasons"])
                print(f"  - {item['title']} [{item['entry_type']}] ({reasons})")

    start_time = time.time()
    outcome = "success"
    exit_code = 0
    output = ""

    return_code = 0

    try:
        result = adapter.invoke_skill(skill_name)
        output = result.get("output", "")
        exit_code = result.get("exit_code", 0)

        if not result.get("success", False):
            outcome = "failure"
            return_code = exit_code or 1
            session_manager.update_session(
                session.session_id, state=SessionState.FAILED
            )
            print(f"Skill '{skill_name}' failed with exit code {exit_code}")
            if output:
                print(output)
        else:
            session_manager.update_session(
                session.session_id, state=SessionState.COMPLETED
            )
            print(f"Skill '{skill_name}' completed successfully")
            if output:
                print(output)

    except Exception as e:
        outcome = "failure"
        return_code = 1
        session_manager.update_session(
            session.session_id, state=SessionState.FAILED
        )
        print(f"Error running skill '{skill_name}': {e}")

    duration_seconds = int(time.time() - start_time)

    # Record experience
    experience_index = ExperienceIndex(storage)
    from garage_os.types import ExperienceRecord

    experience_record = ExperienceRecord(
        record_id=f"exp-{session.session_id}",
        task_type="skill_execution",
        skill_ids=[skill_name],
        tech_stack=[],
        domain="general",
        problem_domain=skill_name,
        outcome=outcome,
        duration_seconds=duration_seconds,
        complexity="medium",
        session_id=session.session_id,
        artifacts=[],
        key_patterns=[],
        lessons_learned=[],
        pitfalls=[],
        recommendations=[],
    )

    try:
        experience_index.store(experience_record)
        print(f"Experience recorded: {experience_record.record_id}")
    except Exception as e:
        print(f"Warning: Failed to record experience: {e}")

    if session_manager.archive_session(session.session_id):
        print(f"Session archived: {session.session_id}")
    else:
        print(f"Warning: Failed to archive session: {session.session_id}")

    return return_code


def _knowledge_search(garage_root: Path, query: Optional[str]) -> None:
    """Search knowledge entries.

    Args:
        garage_root: Path to the project root
        query: Optional search query
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entries = knowledge_store.search(query=query)

    if not entries:
        if query:
            print(f"No knowledge entries matching '{query}'")
        else:
            print("No knowledge entries")
        return

    print(f"Found {len(entries)} knowledge entry(ies):\n")
    for entry in entries:
        print(f"  [{entry.type.value.upper()}] {entry.topic}")
        print(f"    ID: {entry.id}")
        print(f"    Date: {entry.date.strftime('%Y-%m-%d')}")
        if entry.tags:
            print(f"    Tags: {', '.join(entry.tags)}")
        print()


def _knowledge_list(garage_root: Path) -> None:
    """List all knowledge entries.

    Args:
        garage_root: Path to the project root
    """
    garage_dir = garage_root / ".garage"

    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entries = knowledge_store.list_entries()

    if not entries:
        print("No knowledge entries")
        return

    print(f"Total {len(entries)} knowledge entry(ies):\n")
    for entry in entries:
        print(f"  [{entry.type.value.upper()}] {entry.topic}")
        print(f"    ID: {entry.id}")
        print(f"    Date: {entry.date.strftime('%Y-%m-%d')}")
        if entry.tags:
            print(f"    Tags: {', '.join(entry.tags)}")
        print()


def _memory_review(
    garage_root: Path,
    batch_id: str,
    action: Optional[str] = None,
    candidate_id: Optional[str] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[str] = None,
    strategy: Optional[str] = None,
) -> int:
    """Show or apply actions to a candidate review batch on the CLI."""
    garage_dir = garage_root / ".garage"
    if not garage_dir.is_dir():
        print("No .garage/ directory found. Run 'garage init' first.")
        return 1

    storage = FileStorage(garage_dir)
    candidate_store = CandidateStore(storage)
    batch = candidate_store.retrieve_batch(batch_id)
    if batch is None:
        print(f"No candidate batch found for '{batch_id}'")
        return 1

    if action:
        knowledge_store = KnowledgeStore(storage)
        experience_index = ExperienceIndex(storage)
        publisher = KnowledgePublisher(candidate_store, knowledge_store, experience_index)
        confirmation_ref = f".garage/{candidate_store.CONFIRMATIONS_DIR}/{batch_id}.json"

        if action == "batch_reject":
            actions = [
                {"candidate_id": cid, "action": "reject"}
                for cid in batch["candidate_ids"]
            ]
            candidate_store.store_confirmation(
                {
                    "schema_version": "1",
                    "batch_id": batch_id,
                    "resolution": "batch_reject",
                    "actions": actions,
                    "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "surface": "cli",
                    "approver": "user",
                }
            )
            for cid in batch["candidate_ids"]:
                candidate_store.update_candidate(cid, {"status": "rejected"})
            batch["status"] = "rejected"
            candidate_store.store_batch(batch)
            print(f"Applied action 'batch_reject' to batch '{batch_id}'")
            return 0

        if action == "defer":
            candidate_store.store_confirmation(
                {
                    "schema_version": "1",
                    "batch_id": batch_id,
                    "resolution": "defer",
                    "actions": [],
                    "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "surface": "cli",
                    "approver": "user",
                }
            )
            for cid in batch["candidate_ids"]:
                candidate_store.update_candidate(cid, {"status": "deferred"})
            batch["status"] = "deferred"
            candidate_store.store_batch(batch)
            print(f"Applied action 'defer' to batch '{batch_id}'")
            return 0

        if candidate_id is None:
            print("Action requires --candidate-id")
            return 1

        if action == "show-conflicts":
            conflict = publisher.detect_conflicts(candidate_id)
            print(f"Conflict strategy: {conflict['strategy']}")
            print(f"Similar entries: {conflict['similar_entries']}")
            return 0

        if action not in {"accept", "edit_accept", "reject", "abandon"}:
            print(f"Unsupported action '{action}'")
            return 1

        edited_fields = None
        if action == "edit_accept":
            edited_fields = {}
            if title is not None:
                edited_fields["title"] = title
            if summary is not None:
                edited_fields["summary"] = summary
            if content is not None:
                edited_fields["content"] = content
            if tags is not None:
                edited_fields["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]

        if action in {"accept", "edit_accept"}:
            conflict = publisher.detect_conflicts(candidate_id)
            if conflict.get("similar_entries") and strategy is None:
                print(
                    "Similar published knowledge detected for this candidate. "
                    "Re-run with --strategy=coexist|supersede|abandon to confirm "
                    "how to handle the conflict (FR-304)."
                )
                print(f"Similar entries: {conflict['similar_entries']}")
                return 1

        candidate_store.store_confirmation(
            {
                "schema_version": "1",
                "batch_id": batch_id,
                "resolution": action,
                "actions": [{"candidate_id": candidate_id, "action": action}],
                "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "surface": "cli",
                "approver": "user",
                "conflict_strategy": strategy,
            }
        )

        publish_result = publisher.publish_candidate(
            candidate_id=candidate_id,
            action=action,
            confirmation_ref=confirmation_ref,
            edited_fields=edited_fields,
            conflict_strategy=strategy,
        )
        # F004 FR-403a / § 10.3: derive the candidate's new status from the
        # publisher result so that --action=accept --strategy=abandon ends
        # up in the same "abandoned" terminal state when (and only when) a
        # real conflict was detected and aborted publication.
        publisher_strategy = publish_result.get("conflict_strategy")
        new_status = {
            "accept": "published",
            "edit_accept": "published",
            "reject": "rejected",
            "abandon": "abandoned",
        }[action]
        if action in {"accept", "edit_accept"} and publisher_strategy == "abandon":
            new_status = "abandoned"
        candidate_store.update_candidate(candidate_id, {"status": new_status})
        # F004 FR-403b / § 11.5: emit a stable, distinct marker for each of
        # the two abandon flows so downstream readers can distinguish them
        # without parsing the confirmation file.
        if action == "abandon":
            print(MEMORY_REVIEW_ABANDONED_NO_PUB.format(cid=candidate_id))
        elif (
            action in {"accept", "edit_accept"}
            and publisher_strategy == "abandon"
        ):
            print(MEMORY_REVIEW_ABANDONED_CONFLICT.format(cid=candidate_id))
        else:
            print(
                f"Candidate '{candidate_id}' action '{action}' applied; "
                f"published_id={publish_result['published_id']}"
            )
        return 0

    print(f"Candidate Batch: {batch['batch_id']}")
    print(f"Status: {batch['status']}")
    print(f"Evaluation: {batch['evaluation_summary']}")
    print(f"Candidates: {len(batch['candidate_ids'])}")
    for candidate_id in batch["candidate_ids"]:
        candidate = candidate_store.retrieve_candidate(candidate_id)
        if candidate is None:
            continue
        print(f"  - {candidate['candidate_id']}: {candidate['title']} [{candidate['candidate_type']}]")
    return 0


# ---------------------------------------------------------------------------
# F005 Knowledge / Experience authoring CLI
# ---------------------------------------------------------------------------


def _now_default() -> datetime:
    """Default clock used by the CLI authoring path.

    Indirected so unit tests can monkeypatch ``cli._now_default`` to lock
    seconds, which is required to deterministically exercise the FR-508 ID
    collision branch (same topic + content + same second → second `add` is
    rejected, not silently overwritten).
    """
    return datetime.now()


def _parse_tags(raw: Optional[str]) -> list[str]:
    """Parse a comma-separated tag string into a list, dropping blanks."""
    if raw is None:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _resolve_content(
    content_arg: Optional[str],
    from_file_arg: Optional[Path],
    *,
    require_one: bool,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve the ``content`` field for `add` / `edit`.

    Returns ``(content, error)``. Three states matter:

    - ``(content, None)``: caller should use ``content`` as-is.
    - ``(None, error)``: caller must print ``error`` to stderr and exit 1.
    - ``(None, None)``: only possible when ``require_one=False`` (i.e. the
      `edit` path), meaning "the user did not pass either flag → leave
      the existing entry's content unchanged".

    The two CLI arguments ``--content`` and ``--from-file`` are mutually
    exclusive (FR-502 / FR-503).
    """
    if content_arg is not None and from_file_arg is not None:
        return None, ERR_CONTENT_AND_FILE_MUTEX
    if content_arg is None and from_file_arg is None:
        if require_one:
            return None, ERR_ADD_REQUIRES_CONTENT
        return None, None
    if content_arg is not None:
        return content_arg, None
    assert from_file_arg is not None
    if not from_file_arg.is_file():
        return None, ERR_FILE_NOT_FOUND_FMT.format(path=from_file_arg)
    return from_file_arg.read_text(encoding="utf-8"), None


def _generate_entry_id(
    knowledge_type: KnowledgeType,
    topic: str,
    content: str,
    now: datetime,
) -> str:
    """Generate a deterministic-with-time-salt ID for a knowledge entry.

    Implements FR-508 / ADR-502. Format: ``<type>-<YYYYMMDD>-<6 hex>`` where
    the 6 hex chars come from the SHA-256 of ``topic\\ncontent\\n<iso seconds>``.
    The timestamp is part of the input so that two `add` calls with the
    same topic + content but in different seconds produce distinct IDs;
    callers that want true determinism must pass an explicit ``--id``.
    """
    timestamp = now.replace(microsecond=0).isoformat()
    digest_input = f"{topic}\n{content}\n{timestamp}".encode("utf-8")
    short = hashlib.sha256(digest_input).hexdigest()[:6]
    return f"{knowledge_type.value}-{now.strftime('%Y%m%d')}-{short}"


def _generate_experience_id(task_type: str, summary: str, now: datetime) -> str:
    """Generate a deterministic-with-time-salt ID for an experience record.

    Mirrors :func:`_generate_entry_id` for the experience surface (FR-508
    experience branch). Format: ``exp-<YYYYMMDD>-<6 hex>``.
    """
    timestamp = now.replace(microsecond=0).isoformat()
    digest_input = f"{task_type}\n{summary}\n{timestamp}".encode("utf-8")
    short = hashlib.sha256(digest_input).hexdigest()[:6]
    return f"exp-{now.strftime('%Y%m%d')}-{short}"


def _require_garage(garage_root: Path) -> Optional[Path]:
    """Return the ``.garage/`` Path if it exists, else None.

    Caller should print ``ERR_NO_GARAGE`` to stderr and exit 1 when None.
    """
    garage_dir = garage_root / ".garage"
    return garage_dir if garage_dir.is_dir() else None


def _knowledge_add(
    garage_root: Path,
    *,
    knowledge_type: str,
    topic: str,
    content_arg: Optional[str],
    from_file: Optional[Path],
    tags_raw: Optional[str],
    explicit_id: Optional[str],
    now_provider: Callable[[], datetime] = _now_default,
) -> int:
    """Implement ``garage knowledge add`` (FR-501 / FR-502 / FR-508 / FR-509)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    content, err = _resolve_content(content_arg, from_file, require_one=True)
    if err is not None:
        print(err, file=sys.stderr)
        return 1
    assert content is not None

    ktype = KnowledgeType(knowledge_type)
    now = now_provider()
    eid = explicit_id or _generate_entry_id(ktype, topic, content, now)

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    if knowledge_store.retrieve(ktype, eid) is not None:
        print(KNOWLEDGE_ALREADY_EXISTS_FMT.format(eid=eid), file=sys.stderr)
        return 1

    entry = KnowledgeEntry(
        id=eid,
        type=ktype,
        topic=topic,
        date=now,
        tags=_parse_tags(tags_raw),
        content=content,
        status="active",
        version=1,
        source_artifact=CLI_SOURCE_KNOWLEDGE_ADD,
    )
    knowledge_store.store(entry)
    print(KNOWLEDGE_ADDED_FMT.format(eid=eid))
    return 0


def _knowledge_edit(
    garage_root: Path,
    *,
    knowledge_type: str,
    eid: str,
    topic: Optional[str],
    content_arg: Optional[str],
    from_file: Optional[Path],
    tags_raw: Optional[str],
    status: Optional[str],
) -> int:
    """Implement ``garage knowledge edit`` (FR-503 / FR-509 / CON-503)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    # FR-503: at least one mutable field must be supplied.
    if (
        topic is None
        and content_arg is None
        and from_file is None
        and tags_raw is None
        and status is None
    ):
        print(ERR_EDIT_REQUIRES_FIELD, file=sys.stderr)
        return 1

    content, err = _resolve_content(content_arg, from_file, require_one=False)
    if err is not None:
        print(err, file=sys.stderr)
        return 1

    ktype = KnowledgeType(knowledge_type)
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entry = knowledge_store.retrieve(ktype, eid)
    if entry is None:
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1

    # Selective overlay per design §10.2.1. Untouched fields keep their
    # current value; CLI never modifies entry.date or publisher metadata.
    if topic is not None:
        entry.topic = topic
    if content is not None:
        entry.content = content
    if tags_raw is not None:
        entry.tags = _parse_tags(tags_raw)
    if status is not None:
        entry.status = status
    entry.source_artifact = CLI_SOURCE_KNOWLEDGE_EDIT

    knowledge_store.update(entry)  # mutates entry.version += 1 in place
    print(KNOWLEDGE_EDITED_FMT.format(eid=eid, version=entry.version))
    return 0


def _knowledge_show(
    garage_root: Path,
    *,
    knowledge_type: str,
    eid: str,
) -> int:
    """Implement ``garage knowledge show`` (FR-504)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    ktype = KnowledgeType(knowledge_type)
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entry = knowledge_store.retrieve(ktype, eid)
    if entry is None:
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1

    # Human-readable front matter dump (key: value), then a blank line, then
    # the body. Includes derived fields version + source_artifact (OD-504).
    tags_str = ", ".join(entry.tags) if entry.tags else ""
    print(f"id: {entry.id}")
    print(f"type: {entry.type.value}")
    print(f"topic: {entry.topic}")
    print(f"date: {entry.date.isoformat()}")
    print(f"tags: {tags_str}")
    print(f"status: {entry.status}")
    print(f"version: {entry.version}")
    if entry.source_artifact is not None:
        print(f"source_artifact: {entry.source_artifact}")
    print("")
    print(entry.content)
    return 0


def _knowledge_delete(
    garage_root: Path,
    *,
    knowledge_type: str,
    eid: str,
) -> int:
    """Implement ``garage knowledge delete`` (FR-505)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    ktype = KnowledgeType(knowledge_type)
    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    if not knowledge_store.delete(ktype, eid):
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1
    print(KNOWLEDGE_DELETED_FMT.format(eid=eid))
    return 0


def _experience_add(
    garage_root: Path,
    *,
    task_type: str,
    skills: list[str],
    domain: str,
    outcome: str,
    duration: int,
    complexity: str,
    summary: str,
    explicit_id: Optional[str],
    problem_domain: Optional[str],
    tech: Optional[list[str]],
    tags_raw: Optional[str],
    now_provider: Callable[[], datetime] = _now_default,
) -> int:
    """Implement ``garage experience add`` (FR-506 / FR-508 experience / FR-509)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    now = now_provider()
    rid = explicit_id or _generate_experience_id(task_type, summary, now)

    storage = FileStorage(garage_dir)
    experience_index = ExperienceIndex(storage)

    if experience_index.retrieve(rid) is not None:
        print(EXPERIENCE_ALREADY_EXISTS_FMT.format(rid=rid), file=sys.stderr)
        return 1

    record = ExperienceRecord(
        record_id=rid,
        task_type=task_type,
        skill_ids=list(skills),
        tech_stack=list(tech) if tech else [],
        domain=domain,
        problem_domain=problem_domain or task_type,
        outcome=outcome,
        duration_seconds=duration,
        complexity=complexity,
        session_id="",
        artifacts=[CLI_SOURCE_EXPERIENCE_ADD],
        key_patterns=_parse_tags(tags_raw),
        lessons_learned=[summary],
        pitfalls=[],
        recommendations=[],
        created_at=now,
        updated_at=now,
    )
    experience_index.store(record)
    print(EXPERIENCE_ADDED_FMT.format(rid=rid))
    return 0


def _experience_show(garage_root: Path, *, rid: str) -> int:
    """Implement ``garage experience show`` (FR-507a).

    Reads the on-disk JSON file directly (instead of going through
    :py:meth:`ExperienceIndex.retrieve`) because we want to display the raw
    persisted shape — including the ``cli:experience-add`` source marker
    in ``artifacts[0]`` and any future fields that may not yet be on the
    ``ExperienceRecord`` dataclass. This keeps `show` fully forward
    compatible with schema additions on disk while still routing all
    *writes* through the public ``ExperienceIndex`` API (see
    ``_experience_add`` / ``_experience_delete``).
    """
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    record_path = garage_dir / "experience" / "records" / f"{rid}.json"
    if not record_path.is_file():
        print(EXPERIENCE_NOT_FOUND_FMT.format(rid=rid), file=sys.stderr)
        return 1

    try:
        data = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(EXPERIENCE_READ_ERR_FMT.format(rid=rid, err=exc), file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def _experience_delete(garage_root: Path, *, rid: str) -> int:
    """Implement ``garage experience delete`` (FR-507b)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    storage = FileStorage(garage_dir)
    experience_index = ExperienceIndex(storage)
    if not experience_index.delete(rid):
        print(EXPERIENCE_NOT_FOUND_FMT.format(rid=rid), file=sys.stderr)
        return 1
    print(EXPERIENCE_DELETED_FMT.format(rid=rid))
    return 0


# ---------------------------------------------------------------------------
# F006 Recall & Knowledge Graph CLI
# ---------------------------------------------------------------------------


def _resolve_knowledge_entry_unique(
    knowledge_store: "KnowledgeStore",
    eid: str,
) -> tuple[Optional[KnowledgeEntry], list[str]]:
    """Locate a knowledge entry by id across all 3 type directories.

    Returns ``(entry, types_hit)`` where:

    - ``types_hit == []``  → not found anywhere; ``entry`` is None
    - ``types_hit == ["<one>"]`` → unique hit; ``entry`` is the matched entry
    - ``len(types_hit) > 1`` → ambiguous (user has cross-type duplicate IDs);
      ``entry`` is the first hit (caller should NOT use it; treat as error per
      FR-605 / ADR-603)

    Iteration order follows the ``KnowledgeType`` enum order (decision →
    pattern → solution) so that ambiguous reports list types deterministically.
    """
    types_hit: list[str] = []
    first_hit: Optional[KnowledgeEntry] = None
    for ktype in KnowledgeType:
        entry = knowledge_store.retrieve(ktype, eid)
        if entry is not None:
            types_hit.append(ktype.value)
            if first_hit is None:
                first_hit = entry
    return first_hit, types_hit


def _recommend_experience(
    records: list[ExperienceRecord],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    """Score experience records against a query-shaped context (FR-602).

    Returns items in the same shape as
    :py:meth:`RecommendationService.recommend` so the two halves can be merged
    by the CLI handler. Score=0 entries are dropped. Weights are spec-anchored
    (see F006 §6 FR-602): domain / problem_domain hits = 0.8, task_type /
    tech_stack / key_patterns hits = 0.6, lessons_learned text hits = 0.4.

    This helper deliberately lives in cli.py instead of
    :py:mod:`garage_os.memory.recommendation_service` to keep CON-605 intact
    (the ``recommend()`` algorithm and `garage run` path remain unchanged).
    """
    domain = (context.get("domain") or "").lower()
    problem_domain = (context.get("problem_domain") or "").lower()
    tag_tokens = [str(tag).lower() for tag in context.get("tags", []) if tag]

    results: list[dict[str, Any]] = []
    for record in records:
        score = 0.0
        reasons: list[str] = []

        if domain and domain == (record.domain or "").lower():
            score += 0.8
            reasons.append(f"domain:{record.domain}")

        if problem_domain and problem_domain == (record.problem_domain or "").lower():
            score += 0.8
            reasons.append(f"problem_domain:{record.problem_domain}")

        task_type_lower = (record.task_type or "").lower()
        for token in tag_tokens:
            if token and token in task_type_lower:
                score += 0.6
                reasons.append(f"task_type:{record.task_type}")
                break  # at most one task_type reason per record

        tech_lower = [t.lower() for t in (record.tech_stack or []) if t]
        for token in tag_tokens:
            for tech in tech_lower:
                if token == tech:
                    score += 0.6
                    reasons.append(f"tech:{tech}")
                    break

        patterns_lower = [p.lower() for p in (record.key_patterns or []) if p]
        for token in tag_tokens:
            for pat in patterns_lower:
                if token == pat:
                    score += 0.6
                    reasons.append(f"pattern:{pat}")
                    break

        lessons_text = " ".join(record.lessons_learned or []).lower()
        for token in tag_tokens:
            if token and token in lessons_text:
                score += 0.4
                reasons.append(f"lesson-text:{token}")

        if score <= 0:
            continue

        title = (
            record.lessons_learned[0]
            if record.lessons_learned
            else record.task_type
        )
        results.append(
            {
                "entry_id": record.record_id,
                "entry_type": "experience",
                "title": title,
                "score": score,
                "match_reasons": reasons,
                "source_session": record.session_id or None,
            }
        )
    return results


def _print_recommendation_block(item: dict[str, Any]) -> None:
    """Print one recommendation result block in the canonical CLI format."""
    type_label = item["entry_type"].upper()
    title = item.get("title") or ""
    print(f"[{type_label}] {title}")
    print(f"  ID: {item['entry_id']}")
    print(f"  Score: {item['score']:.2f}")
    reasons = item.get("match_reasons") or []
    print(f"  Match: {', '.join(reasons) if reasons else '(none)'}")
    source_session = item.get("source_session")
    if source_session:
        print(f"  Source: {source_session}")
    print("")


def _recommend(
    garage_root: Path,
    *,
    query: str,
    tags: Optional[list[str]],
    domain: Optional[str],
    top: int,
) -> int:
    """Implement ``garage recommend <query>`` (FR-601 / FR-602 / FR-603)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)
    experience_index = ExperienceIndex(storage)

    builder = RecommendationContextBuilder()
    context = builder.build_from_query(query, tags=tags, domain=domain)

    service = RecommendationService(knowledge_store, experience_index)
    knowledge_results = service.recommend(context)
    experience_results = _recommend_experience(
        experience_index.list_records(), context
    )

    merged = list(knowledge_results) + list(experience_results)
    merged.sort(key=lambda item: item["score"], reverse=True)
    if top > 0:
        merged = merged[:top]

    if not merged:
        print(RECOMMEND_NO_RESULTS_FMT.format(query=query))
        return 0

    for item in merged:
        _print_recommendation_block(item)
    return 0


def _knowledge_link(
    garage_root: Path,
    *,
    src: str,
    dst: str,
    kind: str,
) -> int:
    """Implement ``garage knowledge link`` (FR-604 / FR-605 / FR-607)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entry, types_hit = _resolve_knowledge_entry_unique(knowledge_store, src)
    if not types_hit:
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=src), file=sys.stderr)
        return 1
    if len(types_hit) > 1:
        print(
            ERR_LINK_FROM_AMBIGUOUS_FMT.format(eid=src, types=types_hit),
            file=sys.stderr,
        )
        return 1
    assert entry is not None  # types_hit length == 1

    if kind == "related-task":
        target_field = entry.related_tasks
    else:
        target_field = entry.related_decisions

    already_linked = dst in target_field
    if not already_linked:
        target_field.append(dst)

    # FR-607: always overwrite source_artifact even on a no-op re-link so that
    # audit grep for "cli:knowledge-link" picks up every user-initiated link
    # action, not just the first one.
    entry.source_artifact = CLI_SOURCE_KNOWLEDGE_LINK
    knowledge_store.update(entry)  # version+=1 (CON-603)

    if already_linked:
        print(KNOWLEDGE_LINK_ALREADY_FMT.format(src=src, dst=dst, kind=kind))
    else:
        print(KNOWLEDGE_LINKED_FMT.format(src=src, dst=dst, kind=kind))
    return 0


def _knowledge_graph(garage_root: Path, *, eid: str) -> int:
    """Implement ``garage knowledge graph --id`` (FR-606)."""
    garage_dir = _require_garage(garage_root)
    if garage_dir is None:
        print(ERR_NO_GARAGE, file=sys.stderr)
        return 1

    storage = FileStorage(garage_dir)
    knowledge_store = KnowledgeStore(storage)

    entry, types_hit = _resolve_knowledge_entry_unique(knowledge_store, eid)
    if not types_hit:
        print(KNOWLEDGE_NOT_FOUND_FMT.format(eid=eid), file=sys.stderr)
        return 1
    if len(types_hit) > 1:
        print(
            ERR_LINK_FROM_AMBIGUOUS_FMT.format(eid=eid, types=types_hit),
            file=sys.stderr,
        )
        return 1
    assert entry is not None

    print(KNOWLEDGE_GRAPH_NODE_FMT.format(type=entry.type.value.upper(), topic=entry.topic))
    print(f"ID: {entry.id}")

    print(GRAPH_OUTGOING_HEADER)
    out_count = 0
    for target in entry.related_decisions:
        print(f"  -> {target} (related-decision)")
        out_count += 1
    for target in entry.related_tasks:
        print(f"  -> {target} (related-task)")
        out_count += 1
    if out_count == 0:
        print(GRAPH_EDGE_NONE)

    # Incoming edges: O(N) full-library scan, see ADR / NFR-603. KnowledgeStore
    # already swallows corrupt entries inside list_entries() (see
    # knowledge_store.py _rebuild_index try/except), so we don't add another
    # try/except here.
    print(GRAPH_INCOMING_HEADER)
    in_count = 0
    for other in knowledge_store.list_entries():
        if other.id == entry.id:
            continue
        if eid in other.related_decisions:
            print(f"  <- {other.id} (related-decision)")
            in_count += 1
        if eid in other.related_tasks:
            print(f"  <- {other.id} (related-task)")
            in_count += 1
    if in_count == 0:
        print(GRAPH_EDGE_NONE)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    # Create parent parser for common arguments
    path_parser = argparse.ArgumentParser(add_help=False)
    path_parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Project root path (default: auto-detect)",
    )

    parser = argparse.ArgumentParser(
        prog="garage",
        description="Garage OS — Agent Operating System CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser(
        "init", help="Initialize .garage/ directory structure", parents=[path_parser]
    )
    # F007 FR-702 / FR-703 / FR-706b: host installer flags.
    init_parser.add_argument(
        "--hosts",
        dest="init_hosts",
        default=None,
        help=(
            "Install Garage packs into the given hosts. Accepts 'all', "
            "'none', or a comma-separated list of host ids "
            "(e.g. 'claude,cursor'). Without this flag, an interactive "
            "prompt is shown on TTY; otherwise no hosts are installed."
        ),
    )
    init_parser.add_argument(
        "--yes",
        dest="init_yes",
        action="store_true",
        help=(
            "Skip the interactive host prompt. With no --hosts, this is "
            "equivalent to --hosts none (CI / scripted use)."
        ),
    )
    init_parser.add_argument(
        "--force",
        dest="init_force",
        action="store_true",
        help=(
            "Overwrite host files that have been locally modified since "
            "Garage installed them. Without this flag they are skipped "
            "and reported on stderr (FR-706b)."
        ),
    )
    # F009 FR-901: --scope flag (default 'project', CON-901 等价 F007/F008 行为).
    # per-host override 通过 --hosts <host>:<scope> 语法 (FR-902).
    init_parser.add_argument(
        "--scope",
        dest="init_scope",
        default="project",
        choices=["project", "user"],
        help=(
            "Install scope: 'project' (default; install to ./.{host}/skills/) "
            "or 'user' (install to ~/.{host}/skills/). Per-host override is "
            "available via --hosts <host>:<scope> syntax."
        ),
    )

    # status
    status_parser = subparsers.add_parser(
        "status", help="Show Garage OS status", parents=[path_parser]
    )

    # F010 sync (FR-1001/2/3/8 + ADR-D10-12/13)
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync Garage knowledge + experience to host context surfaces",
        parents=[path_parser],
    )
    sync_parser.add_argument(
        "--hosts",
        dest="sync_hosts_arg",
        default=None,
        help=(
            "Sync to the given hosts. Accepts 'all', 'none', or a comma-separated "
            "list (e.g. 'claude,cursor'). Per-host scope override: 'claude:user,cursor:project'. "
            "Without this flag, defaults to 'all' (sync all first-class hosts)."
        ),
    )
    sync_parser.add_argument(
        "--scope",
        dest="sync_scope",
        default="project",
        choices=["project", "user"],
        help=(
            "Default sync scope: 'project' (default; ./CLAUDE.md / ./.cursor/rules/garage-context.mdc / "
            "./.opencode/AGENTS.md) or 'user' (~/.claude/CLAUDE.md / ~/.cursor/rules/garage-context.mdc / "
            "~/.config/opencode/AGENTS.md). Per-host override via --hosts <host>:<scope>."
        ),
    )
    sync_parser.add_argument(
        "--force",
        dest="sync_force",
        action="store_true",
        help=(
            "Overwrite Garage marker block even if it has been locally modified. "
            "Without this flag, locally modified blocks are skipped + reported on stderr "
            "(ADR-D10-13, F007 init --force 同精神)."
        ),
    )

    # F010 session import (FR-1005/1006 + ADR-D10-7/8/9/10/11)
    session_parser = subparsers.add_parser(
        "session",
        help="Manage Garage sessions (F010: import host conversations)",
        parents=[path_parser],
    )
    session_subparsers = session_parser.add_subparsers(dest="session_command")
    import_parser = session_subparsers.add_parser(
        "import",
        help="Import host conversation history as Garage SessionState (triggers F003 candidate extraction)",
        parents=[path_parser],
    )
    import_parser.add_argument(
        "--from",
        dest="session_import_from",
        required=True,
        help=(
            "Host id to import from. Supported: claude (alias for claude-code), "
            "claude-code, opencode. cursor is deferred to F010 D-1010."
        ),
    )
    import_parser.add_argument(
        "--all",
        dest="session_import_all",
        action="store_true",
        help=(
            "Batch import ALL conversations without interactive prompt. "
            "Default: TTY interactive selection; non-TTY exits with notice."
        ),
    )

    # run
    run_parser = subparsers.add_parser("run", help="Run a Garage skill", parents=[path_parser])
    run_parser.add_argument(
        "skill_name",
        help="Name of the skill to run",
    )
    run_parser.add_argument(
        "--timeout", type=int, default=300,
        help="Timeout in seconds (default: 300)",
    )

    # F006: recommend (top-level; cross-domain active recall)
    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Pull ranked recall over knowledge + experience for a query",
        parents=[path_parser],
    )
    recommend_parser.add_argument(
        "query",
        help="Free-text query; whitespace-split into tokens for matching",
    )
    recommend_parser.add_argument(
        "--tag",
        dest="recommend_tags",
        action="append",
        default=None,
        help="Additional tag filter (repeatable)",
    )
    recommend_parser.add_argument(
        "--domain",
        dest="recommend_domain",
        default=None,
        help="Optional domain filter (e.g. platform)",
    )
    recommend_parser.add_argument(
        "--top",
        dest="recommend_top",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10)",
    )

    # knowledge
    knowledge_parser = subparsers.add_parser(
        "knowledge", help="Manage knowledge entries", parents=[path_parser]
    )
    knowledge_subparsers = knowledge_parser.add_subparsers(dest="knowledge_command")

    # knowledge search
    search_parser = knowledge_subparsers.add_parser(
        "search", help="Search knowledge entries", parents=[path_parser]
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Search query text"
    )

    # knowledge list
    list_parser = knowledge_subparsers.add_parser(
        "list", help="List all knowledge entries", parents=[path_parser]
    )

    # F005: knowledge add / edit / show / delete (CLI authoring path)
    add_parser = knowledge_subparsers.add_parser(
        "add", help="Add a knowledge entry", parents=[path_parser]
    )
    add_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type (decision / pattern / solution)",
    )
    add_parser.add_argument("--topic", required=True, help="Entry topic (non-empty)")
    add_parser.add_argument("--content", default=None, help="Entry content (mutex with --from-file)")
    add_parser.add_argument(
        "--from-file",
        dest="from_file",
        type=Path,
        default=None,
        help="Read content from file (mutex with --content)",
    )
    add_parser.add_argument("--tags", default=None, help="Comma-separated tags")
    add_parser.add_argument(
        "--id",
        dest="entry_id",
        default=None,
        help="Explicit entry id (default: derived per FR-508)",
    )

    edit_parser = knowledge_subparsers.add_parser(
        "edit", help="Edit a knowledge entry (selective overlay)", parents=[path_parser]
    )
    edit_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type",
    )
    edit_parser.add_argument(
        "--id", dest="entry_id", required=True, help="Entry id (required)"
    )
    edit_parser.add_argument("--topic", default=None, help="New topic")
    edit_parser.add_argument(
        "--content", default=None, help="New content (mutex with --from-file)"
    )
    edit_parser.add_argument(
        "--from-file",
        dest="from_file",
        type=Path,
        default=None,
        help="Read new content from file (mutex with --content)",
    )
    edit_parser.add_argument("--tags", default=None, help="New comma-separated tags (overwrite)")
    edit_parser.add_argument("--status", default=None, help="New status")

    show_parser = knowledge_subparsers.add_parser(
        "show", help="Show a single knowledge entry", parents=[path_parser]
    )
    show_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type",
    )
    show_parser.add_argument(
        "--id", dest="entry_id", required=True, help="Entry id"
    )

    delete_parser = knowledge_subparsers.add_parser(
        "delete", help="Delete a knowledge entry", parents=[path_parser]
    )
    delete_parser.add_argument(
        "--type",
        dest="entry_type",
        choices=[t.value for t in KnowledgeType],
        required=True,
        help="Knowledge type",
    )
    delete_parser.add_argument(
        "--id", dest="entry_id", required=True, help="Entry id"
    )

    # F006: knowledge link / graph (knowledge graph maintenance)
    link_parser = knowledge_subparsers.add_parser(
        "link",
        help="Link a knowledge entry to another id (related-decision / related-task)",
        parents=[path_parser],
    )
    link_parser.add_argument(
        "--from",
        dest="link_src",
        required=True,
        help="Source entry id (auto-resolved across all knowledge types)",
    )
    link_parser.add_argument(
        "--to",
        dest="link_dst",
        required=True,
        help="Target id (any string; not validated for existence)",
    )
    link_parser.add_argument(
        "--kind",
        dest="link_kind",
        choices=["related-decision", "related-task"],
        default="related-decision",
        help="Edge kind (default: related-decision)",
    )

    graph_parser = knowledge_subparsers.add_parser(
        "graph",
        help="Show 1-hop neighborhood (outgoing + incoming edges) for an entry",
        parents=[path_parser],
    )
    graph_parser.add_argument(
        "--id",
        dest="graph_id",
        required=True,
        help="Entry id (auto-resolved across all knowledge types)",
    )

    # F005: experience add / show / delete (CLI authoring path)
    experience_parser = subparsers.add_parser(
        "experience", help="Manage experience records", parents=[path_parser]
    )
    experience_subparsers = experience_parser.add_subparsers(dest="experience_command")

    exp_add_parser = experience_subparsers.add_parser(
        "add", help="Add an experience record", parents=[path_parser]
    )
    exp_add_parser.add_argument("--task-type", dest="task_type", required=True, help="Task type")
    exp_add_parser.add_argument(
        "--skill",
        dest="skills",
        action="append",
        required=True,
        help="Skill id (repeat for multiple)",
    )
    exp_add_parser.add_argument("--domain", required=True, help="Domain (e.g. platform)")
    exp_add_parser.add_argument(
        "--outcome",
        choices=["success", "failure", "partial"],
        required=True,
        help="Outcome",
    )
    exp_add_parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Duration in seconds",
    )
    exp_add_parser.add_argument(
        "--complexity",
        choices=["low", "medium", "high"],
        required=True,
        help="Complexity",
    )
    exp_add_parser.add_argument(
        "--summary",
        required=True,
        help="One-line summary (written to lessons_learned[0])",
    )
    exp_add_parser.add_argument(
        "--id",
        dest="record_id",
        default=None,
        help="Explicit record id (default: derived per FR-508)",
    )
    exp_add_parser.add_argument(
        "--problem-domain",
        dest="problem_domain",
        default=None,
        help="Problem domain (default: --task-type)",
    )
    exp_add_parser.add_argument(
        "--tech",
        dest="tech",
        action="append",
        default=None,
        help="Tech stack item (repeat for multiple)",
    )
    exp_add_parser.add_argument(
        "--tags",
        default=None,
        help="Comma-separated tags (written to key_patterns)",
    )

    exp_show_parser = experience_subparsers.add_parser(
        "show", help="Show a single experience record", parents=[path_parser]
    )
    exp_show_parser.add_argument(
        "--id", dest="record_id", required=True, help="Record id"
    )

    exp_delete_parser = experience_subparsers.add_parser(
        "delete", help="Delete an experience record", parents=[path_parser]
    )
    exp_delete_parser.add_argument(
        "--id", dest="record_id", required=True, help="Record id"
    )

    # memory
    memory_parser = subparsers.add_parser(
        "memory", help="Review memory candidate batches", parents=[path_parser]
    )
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")
    review_parser = memory_subparsers.add_parser(
        "review", help="Show candidate batch summary", parents=[path_parser]
    )
    review_parser.add_argument("batch_id", help="Candidate batch identifier")
    review_parser.add_argument(
        "--action",
        choices=[
            "accept",
            "edit_accept",
            "reject",
            "batch_reject",
            "defer",
            "abandon",
            "show-conflicts",
        ],
        default=None,
        help="Optional review action to apply",
    )
    review_parser.add_argument(
        "--candidate-id",
        default=None,
        help="Candidate identifier for single-candidate actions",
    )
    review_parser.add_argument("--title", default=None, help="Edited title for edit_accept")
    review_parser.add_argument("--summary", default=None, help="Edited summary for edit_accept")
    review_parser.add_argument("--content", default=None, help="Edited content for edit_accept")
    review_parser.add_argument("--tags", default=None, help="Comma-separated tags for edit_accept")
    review_parser.add_argument(
        "--strategy",
        choices=["coexist", "supersede", "abandon"],
        default=None,
        help="Conflict resolution strategy when accept hits similar published knowledge (FR-304)",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the Garage OS CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "init":
        root = args.path if args.path else Path.cwd()
        return _init(
            root,
            hosts_arg=args.init_hosts,
            yes=args.init_yes,
            force=args.init_force,
            scope=args.init_scope,
        )

    if args.command == "status":
        root = args.path if args.path else _find_garage_root()
        _status(root)
        return 0

    if args.command == "sync":
        root = args.path if args.path else Path.cwd()
        return _sync(
            root,
            hosts_arg=args.sync_hosts_arg,
            scope_default=args.sync_scope,
            force=args.sync_force,
        )

    if args.command == "session":
        if args.session_command == "import":
            root = args.path if args.path else _find_garage_root()
            return _session_import(
                root,
                from_host=args.session_import_from,
                all_flag=args.session_import_all,
            )
        # Unknown session subcommand → show help
        session_parser.print_help()
        return 1

    if args.command == "run":
        root = args.path if args.path else _find_garage_root()
        return _run(root, args.skill_name, timeout=args.timeout)

    if args.command == "recommend":
        root = args.path if args.path else _find_garage_root()
        return _recommend(
            root,
            query=args.query,
            tags=args.recommend_tags,
            domain=args.recommend_domain,
            top=args.recommend_top,
        )

    if args.command == "knowledge":
        root = args.path if args.path else _find_garage_root()
        if args.knowledge_command == "search":
            _knowledge_search(root, args.query)
            return 0
        if args.knowledge_command == "list":
            _knowledge_list(root)
            return 0
        if args.knowledge_command == "add":
            return _knowledge_add(
                root,
                knowledge_type=args.entry_type,
                topic=args.topic,
                content_arg=args.content,
                from_file=args.from_file,
                tags_raw=args.tags,
                explicit_id=args.entry_id,
            )
        if args.knowledge_command == "edit":
            return _knowledge_edit(
                root,
                knowledge_type=args.entry_type,
                eid=args.entry_id,
                topic=args.topic,
                content_arg=args.content,
                from_file=args.from_file,
                tags_raw=args.tags,
                status=args.status,
            )
        if args.knowledge_command == "show":
            return _knowledge_show(
                root,
                knowledge_type=args.entry_type,
                eid=args.entry_id,
            )
        if args.knowledge_command == "delete":
            return _knowledge_delete(
                root,
                knowledge_type=args.entry_type,
                eid=args.entry_id,
            )
        if args.knowledge_command == "link":
            return _knowledge_link(
                root,
                src=args.link_src,
                dst=args.link_dst,
                kind=args.link_kind,
            )
        if args.knowledge_command == "graph":
            return _knowledge_graph(root, eid=args.graph_id)
        print(
            "Knowledge command requires one of: "
            "search, list, add, edit, show, delete, link, graph",
            file=sys.stderr,
        )
        return 1

    if args.command == "experience":
        root = args.path if args.path else _find_garage_root()
        if args.experience_command == "add":
            return _experience_add(
                root,
                task_type=args.task_type,
                skills=args.skills,
                domain=args.domain,
                outcome=args.outcome,
                duration=args.duration,
                complexity=args.complexity,
                summary=args.summary,
                explicit_id=args.record_id,
                problem_domain=args.problem_domain,
                tech=args.tech,
                tags_raw=args.tags,
            )
        if args.experience_command == "show":
            return _experience_show(root, rid=args.record_id)
        if args.experience_command == "delete":
            return _experience_delete(root, rid=args.record_id)
        print(
            "Experience command requires one of: add, show, delete",
            file=sys.stderr,
        )
        return 1

    if args.command == "memory":
        root = args.path if args.path else _find_garage_root()
        if args.memory_command == "review":
            return _memory_review(
                root,
                args.batch_id,
                action=args.action,
                candidate_id=args.candidate_id,
                title=args.title,
                summary=args.summary,
                content=args.content,
                tags=args.tags,
                strategy=args.strategy,
            )
        print("Memory command requires 'review' subcommand")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
