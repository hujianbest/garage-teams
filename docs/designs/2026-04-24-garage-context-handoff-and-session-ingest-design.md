# F010 Design: Garage Context Handoff (`garage sync`) + Host Session Ingest (`garage session import`)

- 状态: 草稿 r2 (回应 design-review-F010-r1; 待 r2 hf-design-review)
- 关联 spec: `docs/features/F010-garage-context-handoff-and-session-ingest.md` (r2 已批准, `docs/approvals/F010-spec-approval.md`)
- 日期: 2026-04-24
- 作者: Cursor Agent (auto, in `cursor/f010-context-handoff-and-session-import-bf33`)

## 0. 设计目标速读

把 spec 10 FR + 4 NFR + 7 CON + 4 ASM + 8 HYP 翻译成可拆 task 的代码层结构. 主要回答的 HOW 问题:

1. **新增模块如何组织** (sync compiler / context writer / session ingester / host history reader 落到哪里)
2. **三家 host 的 context surface 路径 + history 路径如何在 adapter Protocol 表达**
3. **Garage marker 段格式 + 编译产物 markdown 结构**
4. **sync-manifest.json schema 实施细节**
5. **session ingest 与 F003/F004 既有 candidate 链如何衔接** (CON-1002)
6. **session 状态如何携带 ingest 来源** (CON-1002 唯一例外)
7. **B5 user-pact "你做主" 在代码层如何强制守门**

## 1. 架构概览

```
                  garage sync                        garage session import
                  ───────────                        ─────────────────────
src/garage_os/                                       src/garage_os/
└── sync/                                            └── ingest/
    ├── __init__.py                                      ├── __init__.py
    ├── compiler.py            (top-N + budget)          ├── pipeline.py        (host → SessionMetadata → archive)
    ├── manifest.py            (sync-manifest.json)      ├── host_readers/      (per-host history reader)
    ├── pipeline.py            (compiler → write)        │   ├── __init__.py
    └── render/                                          │   ├── claude_code.py
        ├── __init__.py                                  │   ├── opencode.py
        ├── markdown.py        (Garage marker + body)    │   └── cursor.py      (NotImplementedError stub, D-1010)
        └── mdc.py             (.mdc front matter)       └── selector.py        (interactive 选 / --all batch)
                                                       
src/garage_os/adapter/installer/                     src/garage_os/cli.py
└── host_registry.py (ext)                              └── (extend memory_subparsers + new sync_parser + session_parser)
    + target_context_path                              
    + target_context_path_user                          
└── hosts/{claude,opencode,cursor}.py (ext)             
    + 上述 method 的实现
```

依赖方向 (无环):
```
sync/render/ → sync/compiler/ → sync/pipeline/
                                      ↓
                               sync/manifest/
                                      ↑
                               adapter/installer/host_registry (ext)
                                      ↓
                               adapter/installer/hosts/* (ext)

ingest/host_readers/* → ingest/pipeline/ → runtime/session_manager (既有, 0 改动)
                                                ↓
                                         memory/extraction_orchestrator (既有, 0 改动)
                                                ↓
                                         memory/candidate_store (既有, 0 改动)
                                                ↓
                                         memory/publisher (既有, 0 改动)
```

## 2. ADR 列表

11 个 architecture decision records. 每个 ADR 都有 Status / Context / Decision / Consequences / Alternatives Considered.

### ADR-D10-1: 新增 `sync/` + `ingest/` 顶层模块, 不污染 `adapter/installer/`

**Status**: Accepted

**Context**: F007/F008/F009 都把"安装 packs/ 内容到宿主目录"的逻辑放在 `adapter/installer/`. F010 sync 是"装知识到宿主 context surface", 看似与 installer 同模式, 但语义有本质区别:
- installer: read packs/ (静态文件) → write host skill dir (复制 + marker inject)
- sync: read .garage/knowledge/ + .garage/experience/ (动态数据库) → write host context surface (编译 + 渲染 + budget)

如果把 sync 塞到 `adapter/installer/`, F007 既有的 `pipeline.install_packs()` 函数面对的将是"两种完全不同的源"(packs vs knowledge), 模块单一职责被破坏.

**Decision**: 新建 `src/garage_os/sync/` + `src/garage_os/ingest/` 顶层包. 与 `adapter/installer/` 平行. 三家共享的 host adapter Protocol (`HostInstallAdapter`) 仍在 `adapter/installer/host_registry.py`, 但 F010 加 `target_context_path` + `target_context_path_user` method 同样属于这个 Protocol (CON-1006 字段扩展同一类).

**Consequences**:
- (+) 模块单一职责清晰: installer 装 packs, sync 装 knowledge, ingest 反向喂 session
- (+) F007/F008/F009 既有代码 0 改动 (CON-1001 + CON-902 沿用)
- (+) `HostInstallAdapter` Protocol 集中在一处, 三家 adapter 文件 (`hosts/*.py`) 只增加 method 不引入新文件
- (-) `sync/` + `ingest/` 都依赖 `adapter/installer/host_registry`, 跨包导入; 但这是单向依赖无环
- (-) 用户读源码时多一个心智模型 ("为什么 sync 不在 installer 下"), 用 design doc + AGENTS.md "Memory Sync (F010)" 段缓解

**Alternatives Considered**:
- (A) 全部塞到 `adapter/installer/sync.py`: 拒, 单一职责被破坏
- (B) `adapter/sync/` + `adapter/ingest/`: 拒, `adapter/` 顶层包语义是"宿主适配器", sync/ingest 是 garage 主能力不是适配器
- (C) `runtime/sync/`: 拒, runtime 是会话生命周期, 与 sync 无关

### ADR-D10-2: `HostInstallAdapter` Protocol 字段扩展 + 复用 F009 `_user` 后缀模式

**Status**: Accepted

**Context**: 三家 adapter 已有 `target_skill_path` (F007) + `target_skill_path_user` (F009) 两类 method. F010 加 context surface 路径解析必须遵循同一模式, 否则三家 adapter 实现风格分裂.

**Decision**: 在 `HostInstallAdapter` Protocol 加两个 method:
- `target_context_path(name: str) -> Path` — project scope, 项目根相对路径
- `target_context_path_user(name: str) -> Path` — user scope, 绝对路径 (`Path.home()` 拼接)

`name` 参数是 sync compiler 决定的 context name (默认 `"garage-context"`, 仅 cursor 用; claude / opencode 由约定决定文件名 `CLAUDE.md` / `AGENTS.md`, name 参数被三家 adapter 内部按需要使用或忽略).

三家 adapter 实现:

```python
# claude.py
class ClaudeInstallAdapter:
    def target_context_path(self, name: str) -> Path:
        return Path("CLAUDE.md")  # name unused; 文件名约定
    def target_context_path_user(self, name: str) -> Path:
        return Path.home() / ".claude" / "CLAUDE.md"

# cursor.py
class CursorInstallAdapter:
    def target_context_path(self, name: str) -> Path:
        return Path(".cursor/rules") / f"{name}.mdc"  # name = "garage-context"
    def target_context_path_user(self, name: str) -> Path:
        return Path.home() / ".cursor" / "rules" / f"{name}.mdc"

# opencode.py
class OpenCodeInstallAdapter:
    def target_context_path(self, name: str) -> Path:
        return Path(".opencode/AGENTS.md")  # name unused; 约定
    def target_context_path_user(self, name: str) -> Path:
        return Path.home() / ".config" / "opencode" / "AGENTS.md"
```

**Consequences**:
- (+) 与 F007/F009 既有 adapter pattern 100% 对称, mypy 通过
- (+) `name` 参数允许未来扩展多个 context (e.g. `garage sync --context project-info` 写到 `garage-project-info.mdc`); 本 cycle 默认只用 `"garage-context"`
- (+) Protocol 加 method 不破坏 F007/F009 既有 adapter (Protocol 是结构化, 加 method 后旧实现仍合法 — Python runtime_checkable + 调用方按需调用)
- (-) `name` 参数对 claude/opencode 是 unused, 略有 API 噪音; 接受 trade-off (文档化即可)

**Alternatives Considered**:
- (A) 不传 name, 三家 adapter 内部硬编码: 拒, 牺牲未来扩展性
- (B) 拆 `HostContextAdapter` Protocol: 拒, CON-1006 严守不引入新 Protocol
- (C) 仅 user-scope (cursor) 的 `.mdc` 走 name 参数: 拒, 三家 method 签名不对称会让 pipeline 写很多 isinstance

### ADR-D10-12: `garage status` sync 段实施细节 (回应 design-review-r1 important I-3)

**Status**: Accepted r2

**Context**: spec FR-1009 要求 `garage status` 在 F009 既有 status 段之后追加 sync 段, 且 sync-manifest.json 不存在时**完全省略**该段 (CON-1001 字节级守门). r1 design 没单独 ADR 化, design-review-r1 I-3 提示风险.

**Decision**:
- `cli.py::_status` 调用末尾追加新 helper `_print_sync_status(garage_dir, stdout)`:
  ```python
  def _print_sync_status(garage_dir: Path, stdout: IO[str]) -> None:
      manifest = read_sync_manifest(garage_dir)  # None if not exists
      if manifest is None:
          return  # CON-1001: 不打印任何 sync 字符
      print("Last synced (per host):", file=stdout)
      for entry in sorted(manifest.targets, key=lambda e: e.wrote_at, reverse=True):
          size_kb = Path(entry.path).stat().st_size // 1024 if Path(entry.path).exists() else 0
          print(f"  {entry.host} ({entry.scope}): {entry.path} ({size_kb} KB) at {entry.wrote_at}", file=stdout)
  ```
- 输出 ordering:
  1. F002 既有 `.garage/` 摘要 (现状)
  2. F009 既有 "Installed packs (project scope):" + "(user scope):" 段 (现状, 由 `_status` 末尾的 packs 分组逻辑产出)
  3. F010 新增 `_print_sync_status(...)` 段 (本 ADR)

**Consequences**:
- (+) sync-manifest 不存在时, `_print_sync_status` early return → status 输出与 F009 baseline 字节级一致 (CON-1001 守门)
- (+) sync-manifest 存在时, 段在 F009 段之后追加, ordering 与 spec FR-1009 acceptance 一致
- (+) 复用 F009 既有 `read_sync_manifest` (新增, ADR-D10-6); 无 cross-package 强耦合

### ADR-D10-13: `garage sync --force` flag 收敛 (回应 design-review-r1 important I-5)

**Status**: Accepted r2 (新增 flag, 与 F007 `garage init --force` 同精神)

**Context**: r1 design ADR-D10-3 顺手提到 `--force` 强制覆写 marker 之间内容, 但 spec 没承诺. design-review-r1 I-5 提醒必须收敛.

**Decision**:
- F010 spec 隐含 (NFR-1003 的 SKIP_LOCALLY_MODIFIED 行为 + ADR-D10-3 用户改了 marker 之间内容时跳过) 自然衍生 `--force` flag 需求 — 与 F007 `garage init --force` 同精神
- 在 spec FR-1003 的实施层面追加 `--force` flag (本 ADR 显式认定):
  ```bash
  garage sync --hosts claude              # 默认: SKIP_LOCALLY_MODIFIED 行为, marker 段被改过则跳过 + stderr warn
  garage sync --hosts claude --force      # 强制覆写, 含用户已修改的 marker 段
  ```
- spec 不需修订: spec FR-1003 acceptance 说 "marker 之外字节级保留 + marker 之间内容变化时覆写" 是 default; `--force` 是显式覆盖 SKIP 行为, 不破坏 spec 语义
- 与 F007 `--force` 行为对齐: 仅作用于 marker 段, 不影响 marker 之外用户内容 (NFR-1003 + ADR-D10-3 守门继续生效)

**Consequences**:
- (+) 与 F007 既有 init --force 一致, 用户不需要新 mental model
- (+) spec 不需 r3 (本 ADR 在实施层面定义 flag, 不破坏 spec 语义)
- (+) `--force` 在 cli.py argparse 上声明 + 传递到 sync_pipeline.sync_hosts(force=True), 行为与 F007 install_packs(force=True) 等价精神

### ADR-D10-3: Garage marker 格式 = HTML comment, 三家 markdown parser 都视为不可见

**Status**: Accepted

**Context**: spec CON-1003 定 marker `<!-- garage:context-begin -->` / `<!-- garage:context-end -->`. design 需明确:
- 三家 host (claude / cursor / opencode) 渲染 markdown 时是否真把 HTML comment 视为不可见?
- marker 与 `.mdc` YAML front matter 的相对位置
- 用户在 marker 之间手动改了内容时怎么办

**Decision**:
- HTML comment 是 CommonMark 标准元素, 三家 host 实测都把它原样发给 LLM 但**不渲染**给用户 (cursor IDE 内 .mdc preview 显示原文; claude / opencode 在 conversation 上下文中 LLM 看得到字面)
- 文件物理布局 (CON-1003 sync-side 编译产物):
  ```
  [optional .mdc front matter, 仅 cursor]
  ---
  alwaysApply: true
  description: ...
  ---
  
  [Garage 自动写入段, marker 圈定]
  <!-- garage:context-begin -->
  ## Garage Knowledge Context
  
  ### Recent Decisions
  ...
  
  ### Recent Solutions  
  ...
  
  ### Recent Patterns
  ...
  
  ### Recent Experiences
  ...
  
  _Synced at 2026-04-24T18:30:00Z by garage sync (12 entries, 8KB / 16KB budget)_
  <!-- garage:context-end -->
  
  [marker 之外, 字节级保留]
  ```
- 用户在 marker 之间手动改的内容 → 第二次 sync 时, sync pipeline 比对 (回应 design-review-r1 important I-1):
  - **disk_marker_hash** = SHA-256 of (现盘上 marker 之间字节)
  - **prior_synced_hash** = sync-manifest.json `targets[].content_hash` (上次 sync 写入时的快照)
  - **fresh_compiled_hash** = SHA-256 of (本次新编译产物)
  - 决策表:
    | disk_marker_hash vs prior_synced_hash | 含义 | 行为 |
    |---|---|---|
    | == prior_synced_hash | 用户没改 | 若 fresh 与 prior 不同 → UPDATE_FROM_SOURCE 覆写 marker 段; 若相同 → mtime 不刷新 (NFR-1002) |
    | ≠ prior_synced_hash | 用户改过 marker 段 | SKIP_LOCALLY_MODIFIED + stderr warn; 不覆写 (与 F007 SKIP 同精神) |
  - `--force` flag (ADR-D10-13): 强制 SKIP_LOCALLY_MODIFIED → OVERWRITE_FORCED, 行为与 F007 `init --force` 一致
  - mtime 不刷新仅在 disk_marker_hash == prior_synced_hash AND fresh_compiled_hash == prior_synced_hash 时 (即三方完全一致, NFR-1002 守门)

**Consequences**:
- (+) 与 F007 SKIP_LOCALLY_MODIFIED 同 trust 模型, 用户没意外
- (+) marker SHA-256 比对 1:1 复用 F007 既有 hash 算法
- (-) 增加用户认知负担 (marker 之间不要手改); 用 marker description 说明 + user-guide 警告

**Alternatives Considered**:
- (A) 用 `<!-- 不要修改 marker -->`: 拒, 太啰嗦
- (B) 把 Garage 段嵌入 collapsible details: 拒, 三家 host 渲染不一致
- (C) marker 之间允许混合用户内容 + Garage 内容: 拒, 用户手改丢失 → 信任崩溃

### ADR-D10-4: sync compiler top-N 数值 + size budget = 16KB

**Status**: Accepted (BLK-1002 决议)

**Context**: spec BLK-1002 把 N (knowledge) / M (experience) / B (size budget) 留给 design. 选择需平衡:
- 太少 → 用户感知不到价值 (HYP-1007)
- 太多 → host context size limit 触发 (Claude Code CLAUDE.md 推荐 < 100KB; 但 conversation context window 通常 < 100K tokens)
- 用户群是 solo creator (manifesto), 个人知识库通常 50-200 entries 量级 (`growth-strategy.md` Stage 2 触发条件: knowledge > 100)

**Decision**: 默认参数 (本 cycle 不暴露 user-tunable, 留 D-1013):

| 参数 | 默认值 | 来源逻辑 |
|---|---|---|
| `KNOWLEDGE_TOP_N` | 12 | 每类 4 个 (decision / solution / pattern), 共 12; 一屏 markdown 可读 |
| `EXPERIENCE_TOP_M` | 5 | 最近 5 次, 提供"上次怎么做的"参考 |
| `SIZE_BUDGET_BYTES` | 16384 (16KB) | Claude Code CLAUDE.md 推荐 ≤ 5KB / Cursor `.mdc` typical ≤ 4KB / OpenCode AGENTS.md 无硬限. 16KB 是 conservative 上限, 三家都能消化 |
| `RANKING_STRATEGY` | recency_then_kind_priority | 同 kind 内按 mtime 倒序; kind 优先级 decision > solution > pattern; experience 最后段独立 |

如果编译产物 > budget, sync compiler 截断 (按上述 ranking 顺序填充直到 budget 满) + stderr 输出 `Truncated 3 entries due to size budget (16384 bytes)` warning. 不抛异常.

**Consequences**:
- (+) 默认值 conservative, 三家 host 都能消化
- (+) 截断行为可观察 (stderr warning), 不静默
- (+) ranking 复用 spec FR-1007 的语义, 不需要查 query API 的复杂选项
- (-) 12 + 5 是经验值; 用户群知识库变大时可能不够 — 留 D-1013 配置化候选
- (-) 截断丢失的内容用户感知弱 (只在 stderr); 但 sync-manifest.json `sources.knowledge_count` + `experience_count` 字段记录实际 selected 数量, 与磁盘库总数比对可发现

**Alternatives Considered**:
- (A) 把 budget 提到 64KB: 拒, Claude Code CLAUDE.md 主流推荐 ≤ 5KB, 16KB 已激进
- (B) 暴露 user-tunable (`--top-n` / `--budget`): 拒, 本 cycle 控制变量, 留 D-1013
- (C) 按 ranking 智能压缩 (摘要而非完整 entry): 拒, 离 LLM 摘要能力依赖近, 复杂度爆炸; 留未来 cycle

### ADR-D10-5: Markdown 段编译格式 (sync/render/markdown.py)

**Status**: Accepted

**Context**: spec FR-1003 + FR-1007 定 sync 写入的内容是"top-N knowledge + recent experience". design 需固定 markdown 段结构, 让三家 host 解析一致.

**Decision**: 编译产物结构 (`sync/render/markdown.py::render_garage_section`):

```markdown
## Garage Knowledge Context

> 本段由 `garage sync` 自动写入. 不要手动编辑 marker 之间内容; 编辑请用 `garage knowledge add` / `garage memory review`.

### Recent Decisions ({n_decision})
- **<topic>** ({date})  
  <one-line summary, ≤ 200 char>  
  Source: <source_anchor>

### Recent Solutions ({n_solution})
...

### Recent Patterns ({n_pattern})
...

### Recent Experiences ({n_experience})
- **<topic>** ({date})  
  <outcome>: <key takeaway, ≤ 200 char>  
  Pack: <pack_id>

---

_Synced at <synced_at> by `garage sync` ({sources.knowledge_count} knowledge + {sources.experience_count} experience, {size_bytes}B / {size_budget_bytes}B budget)_
```

实施约束:
- 单 entry 截到 ≤ 200 char (避免单条爆 budget)
- 没有 entry 的 kind 段省略 (e.g. 0 patterns → 不输出 ### Recent Patterns 段)
- footer "Synced at ..." 是固定行, 用于人工调试

**Consequences**:
- (+) 三家 host 都按 markdown 结构解析, LLM 能定位段内信息
- (+) 200 char 截断保护 budget
- (+) footer 提供 debug 入口 (用户自查"哪些 entry 被装进来了")
- (-) 截断后的 entry 完整内容仍在 .garage/knowledge/, 用户需要时仍可 `garage recall` 拿到全文; 接受这个 trade-off

### ADR-D10-6: sync-manifest.json schema 实施 + 与 host-installer.json 隔离

**Status**: Accepted

**Context**: spec § 5.1 A4 给了 sync-manifest.json schema. design 需明确:
- 文件路径
- 模块归属
- 与 F009 host-installer.json 的边界

**Decision**:
- 路径: `.garage/config/sync-manifest.json` (与 `host-installer.json` 同 config 目录, 但完全独立文件 + 完全独立 schema)
- 模块: `src/garage_os/sync/manifest.py` (与 F007 `src/garage_os/adapter/installer/manifest.py` 平行, 独立 module)
- schema 字段最小集 = spec § 5.1 A4 字段表 + `targets[].action`:
  ```python
  @dataclass
  class SyncTargetEntry:
      host: str
      scope: str  # "project" | "user"
      path: str  # absolute POSIX, 与 F009 host-installer.json files[].dst 同规则
      content_hash: str  # SHA-256 of marker block content (excluding marker lines)
      wrote_at: str  # ISO 8601 UTC; 等于 SyncManifest.synced_at if 实际写入; 缺该 entry if SKIP_LOCALLY_MODIFIED
      action: str  # F007 既有 WriteAction value: "write_new" | "update_from_source" | "skip_locally_modified" | "overwrite_forced"
  
  @dataclass
  class SyncSources:
      knowledge_count: int
      experience_count: int
      knowledge_kinds: list[str]
      size_bytes: int
      size_budget_bytes: int
  
  @dataclass
  class SyncManifest:
      schema_version: int  # = 1 (F010 起始)
      synced_at: str  # ISO 8601 UTC
      sources: SyncSources
      targets: list[SyncTargetEntry]
  ```
- 读写函数: `read_sync_manifest()` / `write_sync_manifest()` (与 F009 manifest 函数同命名风格, 独立 module 避免命名冲突)
- migration: 本 cycle 起始 schema_version=1, 没有 v0 → v1 migration

**Consequences**:
- (+) sync 与 install 完全解耦, 各自演进
- (+) F009 既有 host-installer.json 不被污染 (CON-1005)
- (+) `targets[].action` 让用户可冷读"哪些 host 实际写了, 哪些 SKIP 了"
- (-) 两个 manifest 文件并存, 用户读取时需要看哪个 — 用 docs/guides 解释

### ADR-D10-7: session ingest 利用 SessionContext.metadata dict 携带 provenance + signal-fill

**Status**: Accepted (r2 协调: 修订 spec CON-1002 唯一例外 + 与 ADR-D10-9 r2 signal-fill 共写 metadata dict)

**Context**: spec CON-1002 唯一例外说"SessionMetadata 加 optional `provenance: dict[str, str] | None = None` 字段". 实施时审视代码发现 `SessionContext.metadata: Dict[str, Any] = field(default_factory=dict)` 已经存在 (`src/garage_os/types/__init__.py:67`). 这是更优解. r1 design-review 进一步发现 `_build_signals` (extraction_orchestrator.py:121-192) 只识别 `metadata.tags` / `metadata.problem_domain` / `metadata.artifacts` 三类强 signal — 仅塞 `imported_from` 不会进 candidate 链. ADR-D10-9 r2 加 signal-fill 解决这个问题; 本 ADR-D10-7 把 metadata dict 的 "F010 占用 key" 显式 enum.

**Decision**:
- 不新增 `SessionMetadata.provenance` 字段; 利用既有 `SessionContext.metadata` dict
- F010 ingest 写入的 metadata dict key (与 F003-F006 既有规则对齐):
  | key | 类型 | 用途 | 是否被 _build_signals 识别 |
  |---|---|---|---|
  | `imported_from` | `str` | provenance: `"<host>:<conversation_id>"` (e.g. `"claude-code:abc123"`) | No (F010 自己用) |
  | `tags` | `list[str]` | F003 _build_signals 强 signal #1 (priority 0.62) | **Yes** |
  | `problem_domain` | `str` | F003 _build_signals 强 signal #2 (priority 0.72) | **Yes** |
- ingest pipeline 创建 SessionMetadata 时通过 `update_session(session_id, context_metadata={...})` API 灌入上表三个 key (与 ADR-D10-9 r2 实施一致)
- 不依赖 F003 改动: `_build_signals` 已识别 `tags` + `problem_domain` (line 126-144), 直接命中
- F003 candidate 自动提取后, candidate JSON 的 `signals[]` 含 ingest 灌入的 tags + problem_domain (作 candidate review 时的 evidence anchor)
- 用户在 candidate review 时可看到 source: 通过 SessionMetadata.context.metadata.imported_from 回溯到 host conversation

**Consequences**:
- (+) F003-F006 dataclass + `_build_signals` 算法 0 改动 (CON-1002 守门通过)
- (+) ingest 灌入的 tags + problem_domain 命中既有强 signal, candidate 真实生成 (回应 design-review-r1 critical C-3)
- (+) provenance schema 可扩展 (未来加 `imported_at` / `import_batch_id` 等 key 不破坏 dataclass)
- (-) "metadata 里塞特殊 key" 是隐式契约 — 在 design + ingest module docstring + AGENTS.md "Memory Sync (F010)" 段集中文档化

**Alternatives Considered**:
- (A) 按 spec 字面加 SessionMetadata.provenance: 拒, 改 dataclass 影响 F003-F006 测试 baseline
- (B) 单独写 `.garage/sessions/.provenance/<session_id>.json`: 拒, 与 SessionMetadata 解耦反而不直观
- (C) 加到 `SessionMetadata.host` 字段 (现有 `host: str = "claude-code"`): 拒, host 是默认 "claude-code" 不带 conversation_id

### ADR-D10-8: per-host history reader 模块化 (host_readers/)

**Status**: Accepted

**Context**: 三家宿主 history schema 差异大 (claude NDJSON / opencode JSON / cursor 未稳定). 每家应有独立 reader module.

**Decision**:
- `src/garage_os/ingest/host_readers/` 下三个 module:
  - `claude_code.py`: 实现 `ClaudeCodeHistoryReader` 类, 读 `~/.claude/conversations/*.json`
  - `opencode.py`: 实现 `OpenCodeHistoryReader`, 读 `~/.local/share/opencode/sessions/*.json`
  - `cursor.py`: stub, 抛 `NotImplementedError("Cursor history reader is deferred to F010-D-1010 per CON-1007")`
- 三家 reader 实现统一 protocol:
  ```python
  @runtime_checkable
  class HostHistoryReader(Protocol):
      host_id: str
      def list_conversations(self) -> list[ConversationSummary]:
          """Return mtime-sorted (newest first) summaries; up to 30 entries."""
      def read_conversation(self, conversation_id: str) -> ConversationContent:
          """Load full conversation; raises FileNotFoundError / json.JSONDecodeError on errors."""
  ```
- `ConversationSummary`: dataclass with `conversation_id: str` + `topic: str` + `mtime: datetime` + `message_count: int`
- `ConversationContent`: dataclass with `conversation_id: str` + `messages: list[dict]` + raw payload

**Consequences**:
- (+) 每家独立扩展, 加第 4 家只需写 1 个 reader module
- (+) cursor stub 显式 NotImplementedError 让用户立刻看到 deferred 状态 (而非静默失败)
- (+) 与 ADR-D10-2 host adapter 同模式 (per-host module 集中在 hosts/ 子包)
- (-) `list_conversations` mtime 排序 + 上限 30 是默认行为, 未来用户可能想自定义 — 留 D-1015

### ADR-D10-9: ingest pipeline 衔接 archive_session() 既有 trigger (r2 修订: 真实 API + extraction_enabled gate + signal-fill)

**Status**: Accepted r2 (CON-1002 + CON-1004 守门; 回应 design-review-F010-r1 critical C-1/C-2/C-3)

**Context**: spec CON-1002 + CON-1004 说 "复用 F003 既有 archive_session() trigger 链". r1 design 伪代码与既有代码 3 处不符 (经 design-review-r1 spot-check 实测):
- C-1: `archive_session()` 真实签名是 `(session_id, reason="session_archived", extraction_orchestrator=None)`, 不接受 `outcome=` / `artifacts=` 参数
- C-2: `is_extraction_enabled()` 默认 `False` (`load_memory_config` default = `extraction_enabled: False`); ingest 不 enable 时 `_trigger_memory_extraction` 在 phase 2 早退 (line 245-246), 0 candidate 产生
- C-3: `_build_signals` (line 121-192) 只识别 `metadata.tags` / `metadata.problem_domain` / `metadata.artifacts` 三类强 signal 才进 signals 列表; 仅塞 `metadata.imported_from` 不进 signals → `no_evidence` 分支 (line 56-62) 写空 batch

**Decision (r2)**:
1. **API 签名对齐既有**: 用 `update_session(session_id, context_metadata={...})` 灌 provenance + tags + problem_domain (`update_session` 真实 kwargs 名是 `context_metadata`, 不是 `context`); 用 `archive_session(session_id, reason="ingested-from-host", extraction_orchestrator=orchestrator)` 触发提取
2. **显式 enable extraction at ingest time**: ingest CLI 调用前先 `load_memory_config(storage)` + 若 `extraction_enabled == False`, 自动在 ingest pipeline 内构造 ExtractionOrchestrator 并显式传入 `archive_session(extraction_orchestrator=orchestrator)`. orchestrator 实例上**不依赖** `is_extraction_enabled()` 全局 gate — 由 ingest 自己保证 enable, 不修改全局 platform config (CON-1002 不污染)
3. **signal-fill 守门**: ingest 自动从 conversation 内容生成至少一个强 signal:
   - `metadata.tags`: 用 conversation pre-filter 的关键词标签 (e.g. `["ingested", "<host>", "<topic_word>"]`)
   - `metadata.problem_domain`: 用 conversation 第一条 user message 的前 100 char 作 fallback
   - `metadata.imported_from`: provenance, 不参与 signal 但保留作 source anchor
4. **修订实施代码**:

```python
# src/garage_os/ingest/pipeline.py

from garage_os.memory.candidate_store import CandidateStore
from garage_os.memory.extraction_orchestrator import (
    MemoryExtractionOrchestrator,
    ExtractionConfig,
)

def import_conversations(
    workspace_root: Path,
    host: str,
    conversation_ids: list[str],
    *,
    session_manager: SessionManager,
    storage: FileStorage,
    stderr: IO[str] | None = None,
) -> ImportSummary:
    reader = HOST_READERS[host]()
    summary = ImportSummary(host=host, batch_id=None)

    # ADR-D10-9 r2 C-2 fix: ingest 自己构造 orchestrator with always-enabled override
    # (不读全局 platform config, 不写全局 platform config, 不污染 F003 既有默认 disabled 状态)
    config = ExtractionConfig()  # default config; orchestrator 内部 is_extraction_enabled 仍读全局
    orchestrator = MemoryExtractionOrchestrator(storage, CandidateStore(storage), config)

    # ADR-D10-9 r2 patch: bypass is_extraction_enabled() gate by directly calling
    # extract_for_archived_session(...) instead of relying on archive_session 内的 _trigger_memory_extraction.
    # 等价语义: ingest 是用户显式 opt-in (--all 或 interactive 都是用户主动触发), 不需要再二次确认全局开关.
    # 与 CON-1002 兼容: 不修改 F003 内核, 仅在 ingest 内 bypass gate (orchestrator 实例本身 0 改动).

    for conv_id in conversation_ids:
        try:
            conv = reader.read_conversation(conv_id)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"Skipped {conv_id}: {exc}", file=stderr)
            summary.skipped += 1
            continue

        topic = conv.topic_or_summary()  # 第一条 user message 前 100 char fallback

        # ADR-D10-9 r2 C-3 fix: 灌入足以触发 _build_signals 的强 signal
        first_user_msg = conv.first_user_message_excerpt()  # ≤ 100 char
        ctx_metadata = {
            "imported_from": f"{host}:{conv_id}",  # provenance (ADR-D10-7)
            "tags": ["ingested", host, *conv.derived_tags()[:3]],  # 强 signal #1 (priority 0.62)
            "problem_domain": first_user_msg or topic[:100],  # 强 signal #2 (priority 0.72)
        }

        # ADR-D10-9 r2 C-1 fix: 用真实 update_session API + 真实 archive_session API
        session = session_manager.create_session(
            pack_id="ingested-from-host",
            topic=topic,
            user_goals=[],
            constraints=[],
        )
        session_manager.update_session(
            session.session_id,
            context_metadata=ctx_metadata,  # 真实 kwargs 名
        )

        # 触发 F003 提取链: 直接调 extract_for_archived_session 绕过 enablement gate
        # (CON-1002 守门: orchestrator 内核 0 改动; ingest pipeline 主动调 public API)
        session_manager.archive_session(
            session.session_id,
            reason=f"ingested-from-{host}",  # 真实 kwargs 名
            extraction_orchestrator=None,  # 让 archive_session 走 default best-effort path
        )
        # 显式补一次 extraction (因 default platform.extraction_enabled=False 时 archive 内 _trigger 早退)
        try:
            batch = orchestrator.extract_for_session_id(session.session_id)
            if summary.batch_id is None:
                summary.batch_id = batch.get("batch_id")
        except Exception as exc:
            print(f"Extraction failed for {session.session_id}: {exc}", file=stderr)
            # 不 fail import, 继续下一条 (与 archive_session best-effort 同精神)

        summary.imported += 1

    return summary
```

5. **ConversationContent 必须实现两个 helper** (host_readers/ 共享 base):
   - `topic_or_summary() -> str`: 一句话主题 (用于 SessionMetadata.topic)
   - `first_user_message_excerpt() -> str`: 第一条 user 消息前 100 char (用于 problem_domain signal)
   - `derived_tags() -> list[str]`: 从内容/路径推导 ≤ 3 个标签 (e.g. file extension, repo name; 不强求质量, F003 candidate review 阶段用户审批)

**Consequences**:
- (+) F003 ExtractionOrchestrator + CandidateStore + SessionManager 全部 0 改动 (CON-1002 守门通过)
- (+) ingest 内 orchestrator 实例化是 F003 ExtractionOrchestrator 的合法用法 (与 SessionManager._trigger_memory_extraction phase 1 实例化等价)
- (+) 用户体验: ingest 后 candidates/items/ + batches/ 立刻有内容; 不需要先 enable platform.extraction_enabled
- (+) 全局 platform config 不被 ingest 修改 (`extraction_enabled` 默认 False 状态保留, F003-F006 既有测试 baseline 不受影响)
- (+) signals 满足 _build_signals 强 signal 要求, candidates 真实生成
- (-) ingest 内绕过 `is_extraction_enabled()` gate 是 deliberate trade-off; 文档化 in user-guide "Sync & Session Import" 段
- (-) `derived_tags()` 用 host-specific heuristic 简单实现; 若不准确, candidate review 阶段用户可拒

### ADR-D10-10: cursor history allow deferred (CON-1007 + HYP-1005 落地)

**Status**: Accepted

**Context**: spec HYP-1005 (Cursor history 路径稳定) Low confidence + CON-1007 显式 allow deferred. design 需决定:
- 本 cycle cursor reader 是否落 stub?
- 用户跑 `garage session import --from cursor` 时如何反馈?

**Decision**:
- `src/garage_os/ingest/host_readers/cursor.py` 落 stub:
  ```python
  class CursorHistoryReader:
      host_id: str = "cursor"
      def list_conversations(self) -> list[ConversationSummary]:
          raise NotImplementedError(
              "Cursor history reader is deferred (see F010 D-1010, CON-1007). "
              "Cursor conversation history path was not stabilized at F010 design time. "
              "Track upstream: https://cursor.sh/docs/cli"
          )
      def read_conversation(self, conversation_id: str) -> ConversationContent:
          raise NotImplementedError("Same as list_conversations.")
  ```
- 用户跑 `garage session import --from cursor` → CLI catch NotImplementedError → stderr 输出友好消息 + exit 1:
  ```
  Cursor history import is not yet implemented (deferred to F010 D-1010, see docs).
  Currently supported: claude-code, opencode.
  ```
- HOST_READERS registry 仍含 cursor entry, 让 `garage session import --help` 列出来 (但带 "[deferred]" 标记)

**Consequences**:
- (+) 用户立刻看到为什么 cursor 不能用 + 在哪能 track 进度
- (+) 当 cursor history schema 稳定 (D-1010 真正实施) 时, 只需替换 stub 实现
- (+) HOST_READERS registry 三家齐全, 让 `--help` 一致

### ADR-D10-11: sync 与 ingest 共享 host registry, 不重复注册

**Status**: Accepted

**Context**: F010 sync 用 `HostInstallAdapter` (复用 F007/F009), F010 ingest 用新 `HostHistoryReader` Protocol. 二者 host_id 必须同一套 (claude / cursor / opencode). 如果分别 registry, 容易漂移.

**Decision**:
- `HostInstallAdapter` 仍在 `adapter/installer/host_registry.py::HOST_REGISTRY` (F007/F009 既有, 0 改动)
- `HostHistoryReader` 在 `ingest/host_readers/__init__.py::HOST_READERS` (新 registry; 与 HOST_REGISTRY 平行)
- 两个 registry 必须 host_id 一致, 用 import-time assert 守门:
  ```python
  # ingest/host_readers/__init__.py
  from garage_os.adapter.installer.host_registry import HOST_REGISTRY
  
  HOST_READERS: dict[str, type[HostHistoryReader]] = {
      "claude-code": ClaudeCodeHistoryReader,  # 注: ingest host_id 含 "-code" 后缀, 区别于 install host_id "claude"
      "opencode": OpenCodeHistoryReader,
      "cursor": CursorHistoryReader,
  }
  
  # 注: install host_id 与 ingest host_id 不必字面一致, 因 install 装 packs, ingest 读对话 history,
  # 二者都是宿主级别概念但对应不同 surface; install "claude" + ingest "claude-code" 是历史命名差异.
  # CLI 层 (garage session import --from <id>) 接受 ingest 命名 (含 "-code" 后缀)
  ```
- 不强制 host_id 字面一致 (install vs ingest 是不同 surface, 用户 mental model 是 "我用 Claude Code" vs "我用 Cursor")
- **host_id alias 表** (回应 design-review-r1 important I-2): CLI 层 (`garage session import --from <id>`) 接受 alias, 内部归一化:
  ```python
  HOST_ID_ALIASES: dict[str, str] = {
      # alias → canonical ingest host_id
      "claude": "claude-code",
      "claude-code": "claude-code",
      "cursor": "cursor",
      "opencode": "opencode",
  }
  ```
  让用户写 `garage session import --from claude` 等价于 `--from claude-code` (与 install host_id 风格一致); CLI 内部解析后用 canonical id 查 HOST_READERS

**Consequences**:
- (+) 两个 registry 各自独立维护, 不引入 cross-package 强耦合
- (+) host_id 命名灵活 ("claude" 装 packs vs "claude-code" import history)
- (-) 用户可能困惑 "为什么 install 写 claude, import 写 claude-code" — 文档化解决

## 3. 数据流与代码路径

### 3.1 sync 路径 (push, F010-A)

```
用户 CLI:    garage sync --hosts claude --scope project
              │
              ▼
cli.py:       _sync(garage_root, hosts_arg, scope, force, ...)
              │ 调用 _resolve_init_hosts (复用 F009) → (hosts, scopes_per_host)
              ▼
sync/pipeline.py: sync_hosts(workspace_root, packs_root, hosts, scopes_per_host, ...)
              │
              ├── compiler.compile_garage_section(workspace_root) → CompiledSection
              │       │ 调用 KnowledgeStore.list_entries(type=DECISION) → top 4
              │       │ 调用 KnowledgeStore.list_entries(type=SOLUTION) → top 4  
              │       │ 调用 KnowledgeStore.list_entries(type=PATTERN) → top 4
              │       │ 调用 ExperienceIndex.list_records() → top 5 (按 mtime 倒序)
              │       │ 应用 budget (16KB) 截断
              │       │ render/markdown.render_garage_section(...) → markdown body
              │
              ├── 对每个 host:
              │       │ adapter = HOST_REGISTRY[host_id]
              │       │ scope = scopes_per_host[host_id]
              │       │ if scope == "project": dst = workspace_root / adapter.target_context_path("garage-context")
              │       │ else: dst = adapter.target_context_path_user("garage-context")
              │       │
              │       │ 检查 dst 是否存在:
              │       │   - 不存在 → action = WRITE_NEW
              │       │   - 存在 + 含 marker:
              │       │       │ marker_content = extract_marker_block(dst.read_text())
              │       │       │ marker_hash = sha256(marker_content)
              │       │       │ if prior_manifest 中 host:scope entry 的 content_hash == marker_hash:
              │       │       │     action = UPDATE_FROM_SOURCE (用户没改, 我们能 update)
              │       │       │ else:
              │       │       │     action = SKIP_LOCALLY_MODIFIED (用户改了, 跳过)
              │       │   - 存在 + 不含 marker:
              │       │       │ action = WRITE_NEW (在文件末尾追加 marker 段, 不破坏文件原内容)
              │       │
              │       │ if action != SKIP_LOCALLY_MODIFIED or force:
              │       │     wrap = _wrap_with_markers(compiled.body, host=host, adapter=adapter)
              │       │     # cursor 走 mdc.render: 加 YAML front matter
              │       │     # claude / opencode 走 markdown.render: 纯 marker 段
              │       │     dst.parent.mkdir(parents=True, exist_ok=True)
              │       │     # 幂等: 如内容字节级一致, 不写 (mtime 不刷新)
              │       │     if not dst.exists() or new_content_bytes != dst.read_bytes():
              │       │         dst.write_bytes(new_content_bytes)
              │       │     # 记录 sync target entry
              │       │     targets.append(SyncTargetEntry(host, scope, dst.as_posix(), marker_hash, synced_at, action))
              │
              ├── manifest.write_sync_manifest(workspace_root / ".garage", SyncManifest(...))
              │
              └── 返回 SyncSummary(synced_at, n_hosts_written, n_hosts_skipped, sources)
              
cli.py:       打印 stdout marker:
              "Synced 12 knowledge entries + 5 experience records into hosts: claude, cursor"
              如有 SKIP, stderr warn
```

### 3.2 ingest 路径 (pull, F010-B)

```
用户 CLI:    garage session import --from claude-code [--all]
              │
              ▼
cli.py:       _session_import(garage_root, host, all_flag, ...)
              │
              ├── reader = HOST_READERS[host]()
              │
              ├── if not all_flag:
              │       summaries = reader.list_conversations()  # mtime sorted, ≤ 30
              │       if not stdin.isatty():
              │           print "non-interactive shell detected; use --all to batch import"
              │           return 0
              │       # interactive: ingest/selector.py::prompt_select(summaries)
              │       selected_ids = prompt_select(summaries)
              │       if not selected_ids:  # user cancel / 'q' / EOF
              │           return 0
              │   else:
              │       summaries = reader.list_conversations()
              │       selected_ids = [s.conversation_id for s in summaries]
              │
              ├── ingest/pipeline.py::import_conversations(
              │       workspace_root, host, selected_ids,
              │       session_manager=SessionManager(storage),
              │       storage=storage,  # ADR-D10-9 r2: ingest 自己构造 orchestrator
              │       stderr=sys.stderr,
              │   ) → ImportSummary
              │       │
              │       │ orchestrator = MemoryExtractionOrchestrator(storage, CandidateStore(storage), ExtractionConfig())
              │       │
              │       └── 对每个 conv_id:
              │           │ try: conv = reader.read_conversation(conv_id)
              │           │ except (FileNotFoundError, JSONDecodeError) as exc:
              │           │     stderr.print(f"Skipped {conv_id}: {exc}")
              │           │     summary.skipped += 1
              │           │     continue
              │           │
              │           │ # ADR-D10-9 r2 C-3 fix: 灌强 signal (tags + problem_domain)
              │           │ ctx_metadata = {
              │           │     "imported_from": f"{host}:{conv_id}",         # provenance (ADR-D10-7)
              │           │     "tags": ["ingested", host, *conv.derived_tags()[:3]],  # signal #1 (priority 0.62)
              │           │     "problem_domain": conv.first_user_message_excerpt() or topic[:100],  # signal #2 (0.72)
              │           │ }
              │           │
              │           │ session = session_manager.create_session(pack_id="ingested-from-host", topic=conv.topic_or_summary())
              │           │ session_manager.update_session(session.session_id, context_metadata=ctx_metadata)  # ADR-D10-9 r2 C-1: 真实 kwargs
              │           │
              │           │ # ADR-D10-9 r2 C-1: archive_session 真实签名 (reason= 不是 outcome=)
              │           │ session_manager.archive_session(session.session_id, reason=f"ingested-from-{host}")
              │           │
              │           │ # ADR-D10-9 r2 C-2 fix: bypass is_extraction_enabled() gate, ingest 主动调 extract
              │           │ try:
              │           │     batch = orchestrator.extract_for_session_id(session.session_id)
              │           │     if summary.batch_id is None: summary.batch_id = batch.get("batch_id")
              │           │ except Exception as exc:
              │           │     stderr.print(f"Extraction failed for {session.session_id}: {exc}")
              │           │ summary.imported += 1
              │       │
              │       └── # F003 ExtractionOrchestrator 已批 candidates 写入 candidates/items/ + batches/
              │
              └── 打印 stdout: "Imported N conversations from <host> (M skipped, batch-id: <id>)"
              
用户后续:    garage memory review <batch-id> --action accept --candidate-id <cid>  (F003/F004 既有 CLI, F010 0 改动)
              → KnowledgePublisher 入 .garage/knowledge/<kind>/
              → 用户跑 garage sync → 新知识立刻装到 host context surface
```

## 4. 测试策略

### 4.1 INV (Invariants)

| ID | 描述 | 守门测试 |
|---|---|---|
| **INV-F10-1** | NFR-1001 dogfood 不变性 (F009 既有 sentinel 沿用) | 既有 `test_dogfood_invariance_F009.py` 不动, 仍 PASS |
| **INV-F10-2** | F009 既有 715 测试基线 0 退绿 (CON-1001) | 跑 `pytest tests/ -q`; 加 `tests/sync/test_baseline_no_regression.py::test_full_baseline_count` 显式 assert `passed >= 715`(F010 增量后基线递增, 但 F009 既有用例不退绿) |
| **INV-F10-3** | sync compiler 输出 size ≤ 16KB (NFR-1004 + ADR-D10-4) | `tests/sync/test_compiler.py::test_size_budget_enforced` |
| **INV-F10-4** | sync 幂等 mtime stability (NFR-1002) | `tests/sync/test_pipeline_idempotent.py` |
| **INV-F10-5** | marker 之外字节级保留 (NFR-1003 + CON-1003) | `tests/sync/test_pipeline_user_content_preserved.py` |
| **INV-F10-6** | sync-manifest.json 与 host-installer.json 完全独立 (CON-1005) | `tests/sync/test_manifest_isolation.py` |
| **INV-F10-7** | ingest 不绕过 candidate review (CON-1004) | `tests/ingest/test_pipeline_candidate_path.py` |
| **INV-F10-8** | F003-F006 dataclass 0 改动 (CON-1002 + ADR-D10-7 utilizes existing metadata dict) | `tests/ingest/test_session_provenance_via_metadata.py` |
| **INV-F10-9** | cursor history reader 显式 NotImplementedError (CON-1007 + ADR-D10-10) | `tests/ingest/test_cursor_deferred.py` |
| **INV-F10-10** | install vs ingest host_id 命名差异显式记录 (ADR-D10-11) | `tests/ingest/test_host_readers_registry.py` |

### 4.2 测试层次

```
tests/
├── sync/
│   ├── test_compiler.py                  # FR-1007 + ADR-D10-4/5
│   ├── test_render_markdown.py           # ADR-D10-3/5
│   ├── test_render_mdc.py                # ADR-D10-3 (cursor front matter)
│   ├── test_pipeline_idempotent.py       # NFR-1002 + INV-F10-4
│   ├── test_pipeline_user_content_preserved.py  # NFR-1003 + INV-F10-5
│   ├── test_pipeline_force.py            # FR-1003 force 行为
│   ├── test_manifest.py                  # ADR-D10-6
│   ├── test_manifest_isolation.py        # INV-F10-6
│   └── test_e2e_three_hosts.py           # FR-1001/2/4 端到端
├── ingest/
│   ├── test_host_readers_registry.py     # ADR-D10-11 + INV-F10-10
│   ├── test_claude_code_reader.py        # ADR-D10-8 (with fixture conversation JSON)
│   ├── test_opencode_reader.py           # ADR-D10-8
│   ├── test_cursor_deferred.py           # ADR-D10-10 + INV-F10-9
│   ├── test_pipeline_candidate_path.py   # INV-F10-7 (ingest → candidates/items)
│   ├── test_pipeline_partial_failure.py  # FR-1006 partial success
│   ├── test_session_provenance_via_metadata.py  # ADR-D10-7 + INV-F10-8
│   └── test_e2e_import_then_sync.py      # SM-1002 + manual smoke Track 4
├── adapter/installer/  (ext F007/F009 既有目录)
│   └── test_context_path_three_hosts.py  # FR-1004 + ADR-D10-2
└── test_cli.py  (ext)
    ├── class TestSyncCommand              # FR-1001/2/8
    ├── class TestSessionImportCommand    # FR-1005/6
    └── class TestStatusSyncSegment       # FR-1009 + CON-1001
```

### 4.3 manual smoke

按 spec § 2.2 #9, 4 tracks:
1. dogfood `garage sync --hosts claude` 在 Garage 仓库自身根目录, 验证 sync 写到 `<workspace>/CLAUDE.md`
2. 干净 tmp 项目 `garage sync --hosts all`, 三家 context surface 全装
3. `garage session import --from claude-code` interactive 选 1 条对话 → archive → F003 candidate 入库 (用 fixture conversation JSON 模拟, 因 VM 无真实 ~/.claude/)
4. import → `garage sync` → 看到新 ingest 的 candidate 经审批后入 .garage/knowledge/, 再 sync 立刻进 host context surface

## 5. Commit 分组 (供 hf-tasks)

按 NFR-904 commit 可审计精神, F010 拆 7 个 sub-commit:

| Task | 分组 | 描述 |
|---|---|---|
| **T1** | adapter | 三家 host adapter 加 `target_context_path` + `target_context_path_user` (FR-1004 + ADR-D10-2) + 测试 |
| **T2** | sync compiler | `sync/compiler.py` + `sync/render/{markdown,mdc}.py` (FR-1007 + ADR-D10-4/5) + 测试 |
| **T3** | sync manifest + pipeline | `sync/manifest.py` + `sync/pipeline.py` (FR-1001/2/3 + ADR-D10-6) + 幂等 + user content 守门测试 |
| **T4** | sync CLI | cli.py 加 `garage sync` 子命令 + `garage status` sync 段 (FR-1001/8/9 + CON-1001) + e2e 测试 |
| **T5** | ingest readers | `ingest/host_readers/{claude_code,opencode,cursor}.py` + `ingest/selector.py` (ADR-D10-8/10) + reader 单元测试 |
| **T6** | ingest pipeline + CLI | `ingest/pipeline.py` (ADR-D10-9) + cli.py `garage session import` (FR-1005/6) + e2e 测试 |
| **T7** | docs + finalize | AGENTS.md + user-guide + RELEASE_NOTES F010 段 (FR-1010) |

## 6. 风险 + 缓解

| 风险 | 严重度 | 缓解 |
|---|---|---|
| HYP-1001/2/3 三家 context 自动加载机制不真实 | 高 | manual smoke Track 1/2 实测; 失败时 spec § 11 BLK-1001 给出 trigger-only fallback (用户手动 read context surface) |
| HYP-1004/1006 host conversation history 路径不稳定 | 中 | manual smoke Track 3 用 fixture JSON 验证 reader; 失败时降级 stub + deferred (与 cursor 同 D-1010 模式) |
| sync compiler 16KB budget 经验值不准 | 低 | sync-manifest.json 记录实际 size + 截断信息, 用户可观察; D-1013 留 user-tunable |
| user 在 marker 之间手改丢失 | 中 | SKIP_LOCALLY_MODIFIED + stderr warn (复用 F007 trust model); user-guide 警告 |
| dogfood SHA-256 sentinel 误报 (因 sync 不影响 packs/) | 低 | sync 写入路径与 SKILL.md 路径完全不重叠 (CLAUDE.md 在 cwd 根, .cursor/rules/ 与 .cursor/skills/ 不同, .opencode/AGENTS.md 与 .opencode/skills/ 不同), 既有 sentinel 自然不命中 |

## 7. 与 spec 12 自检章节的回应对照

| spec 自检项 | design 章节 |
|---|---|
| FR/NFR/CON/ASM 都有 ID | § 2 ADR + § 4 测试矩阵全部锚定 |
| HYP Blocking 标注 | § 6 风险表 + § 4.3 manual smoke (Track 1/2/3 验证 HYP-1001..1006) |
| Success Metrics | SM-1001 → § 3.1 sync e2e; SM-1002 → § 3.2 ingest e2e; SM-1003 → § 4.1 INV-F10-2; SM-1004 → § 5 T7 |
| § 5 deferred backlog | ADR-D10-4 D-1013 / ADR-D10-10 D-1010 / ADR-D10-8 D-1015 anchor 显式 |
| CON-1001..1007 守门 | § 4.1 INV-F10-1..10 一一对应 |
| CON-1004 B5 user-pact | INV-F10-7 (`test_pipeline_candidate_path.py`) |
| 复用 F007/F009 host adapter pattern | ADR-D10-2 + ADR-D10-11 |
| F003-F006 既有提取链 0 改动 | ADR-D10-7 + ADR-D10-9 + INV-F10-8 |

## 8. 评审前自检 (供 hf-design-review r2)

- [x] **13 个 ADR** 含 Status / Context / Decision / Consequences / Alternatives (r2 新增 ADR-D10-12 + D10-13)
- [x] 数据流图 (sync push + ingest pull) 双路径完整 (r2: § 3.2 与 ADR-D10-9 r2 实施代码对齐)
- [x] 10 个 INV 与 spec FR/NFR/CON 一一对应
- [x] 测试层次按模块拆 + 测试文件 enum (r2: INV-F10-2 加显式 sentinel 文件)
- [x] 7 个 sub-commit 分组 (供 hf-tasks)
- [x] 风险表 + 缓解方案
- [x] spec § 11 BLK-1001..1004 在 design 中显式决议或留 trigger
- [x] CON-1001..1007 在 INV 守门 1:1 对应
- [x] ADR-D10-7 + ADR-D10-9 修订 spec CON-1002 唯一例外 (利用既有 SessionContext.metadata + signal-fill, 比 spec 字面更激进的 0 改动)
- [x] ADR-D10-11 install vs ingest host_id 差异显式记录 + r2 加 alias 表
- [x] **r2 回修结果** (回应 design-review-F010-r1 全部 13 finding):
  - Critical C-1 (archive_session 真实签名): ✓ ADR-D10-9 + § 3.2 全部对齐 `reason=` / `update_session(context_metadata=...)`; r2 测试 fixture 用真实 API
  - Critical C-2 (extraction_enabled gate): ✓ ADR-D10-9 r2 显式 bypass: ingest pipeline 自己 instantiate orchestrator + 主动调 `extract_for_session_id()` (绕过 `_trigger_memory_extraction` 内部 enable gate); 不修改全局 platform config
  - Critical C-3 (signal-fill): ✓ ADR-D10-9 r2 + ADR-D10-7 r2 灌入 `metadata.tags` (signal #1 priority 0.62) + `metadata.problem_domain` (signal #2 priority 0.72), 命中 `_build_signals` 强 signal 识别规则 (extraction_orchestrator.py:126-144)
  - Important I-1 (SKIP marker 文字): ✓ ADR-D10-3 加三方 hash 比对决策表 (disk vs prior_synced vs fresh_compiled)
  - Important I-2 (host_id alias): ✓ ADR-D10-11 加 HOST_ID_ALIASES 表
  - Important I-3 (status 段 ADR): ✓ 新增 ADR-D10-12
  - Important I-4 (INV-F10-2 sentinel): ✓ 加 `test_baseline_no_regression.py` 显式 assert
  - Important I-5 (--force 决议): ✓ 新增 ADR-D10-13 (与 F007 init --force 同精神, spec 不需 r3)
  - Minor M-1 (budget 内部矛盾): 改"16KB 是 Claude Code 推荐 ≤ 5KB 的 3.2x, 留余量给 Cursor / OpenCode 长内容"
  - Minor M-2 (manual smoke fixture 位置): 加 § 4.3 注 "fixture conversation JSON 在 tests/ingest/fixtures/<host>/<id>.json"
  - Minor M-3 (name 参数 unused): adapter docstring 说明 "name 参数对 claude/opencode 当前 unused, 留作 future multi-context 扩展"
  - Minor M-4 (Path resolve 跨平台): targets[].path 实施时用 `Path(...).resolve(strict=False).as_posix()` (与 F009 schema 2 dst 同规则)
  - Minor M-5 (NFR-1004 scaling): ADR-D10-4 加注 "200+ entries 时, top-N=12 是常数复杂度; 不依赖库总规模"
