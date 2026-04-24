# F011 Design: STYLE 维度 + 2 production agents + `garage pack install`

- 状态: 草稿 (auto-approved)
- 关联 spec: `docs/features/F011-style-dimension-and-production-agents-and-pack-install.md`
- 日期: 2026-04-24

## 0. 设计目标

把 F011 spec 8 FR + 3 NFR + 5 CON 翻译成可拆 task 的代码层结构. 三 candidate 都是单领域改动:

- **A** (style): `types/__init__.py` enum + `knowledge/knowledge_store.py` TYPE_DIRECTORIES + `sync/compiler.py` kind_list + 测试
- **B** (agents): `packs/garage/agents/{code-review,blog-writing}-agent.md` + `packs/garage/pack.json` agents[] + `packs/garage/README.md` + INV-1 测试同步
- **C** (pack install): 新 `src/garage_os/adapter/installer/pack_install.py` 模块 + cli `garage pack install` / `garage pack ls` subcommand + pack.json schema 加 optional source_url

## 1. 架构概览

```
                  STYLE 维度 (A)               2 production agents (B)         garage pack install (C)
                  ─────────────              ─────────────────────             ─────────────────────
src/garage_os/                                packs/garage/                    src/garage_os/
├── types/__init__.py (ext)                   ├── pack.json (ext: agents++)    └── adapter/installer/
│   + KnowledgeType.STYLE                     ├── README.md (ext: agent table)     └── pack_install.py (NEW)
│                                              └── agents/                            (subprocess git clone +
├── knowledge/knowledge_store.py (ext)             ├── garage-sample-agent.md          discover + write to packs/)
│   + TYPE_DIRECTORIES[STYLE] = "knowledge/style"  ├── code-review-agent.md (NEW)
│                                              │   └── blog-writing-agent.md (NEW)  src/garage_os/cli.py (ext)
└── sync/compiler.py (ext)                                                          + pack_parser ('install' / 'ls')
    + kind_order += "style"                                                         + _pack_install / _pack_ls
    + kind_titles[style] = "Recent Style Preferences"
```

## 2. ADRs

### ADR-D11-1: A part — KnowledgeType.STYLE 加 enum 而非新 dataclass

不新增 StyleEntry 类; 复用 KnowledgeEntry 数据结构 (fields 相同). 仅扩 enum + TYPE_DIRECTORIES dict, 与 F003 既有 DECISION/PATTERN/SOLUTION 完全同模式. CON-1102 守门: 0 改动 KnowledgeEntry 字段.

### ADR-D11-2: A part — sync compiler 加 STYLE kind 同 ranking

per-kind top=4 (与 decision/solution/pattern 一致); section title 为 "Recent Style Preferences" (与 spec FR-1103 acceptance 字面对齐). order: decision > solution > pattern > **style** > experience.

### ADR-D11-3: B part — 2 个 agent 用 markdown body 描述 composition, 不 codify

agent.md 是文档级 hint, 不引入 agent runtime engine (那是宿主自己的事). body 用 markdown describe: "组合 hf-code-review skill + 用户 style entries 来做 PR review"; 由宿主在执行时 read body + 调对应 skill.

### ADR-D11-4: C part — `garage pack install` 用 `subprocess.run(["git", "clone", "--depth=1", url, dst])`

不引入 GitPython / dulwich 等库 (CON-1104 零依赖). 用 subprocess 调本机 git, 失败时 stderr + exit 1 (与 F007/F009/F010 错误处理同精神).

### ADR-D11-5: C part — `pack.json` schema_version 不升级, 加 optional `source_url` 向后兼容

旧 pack.json (无 source_url) 仍 valid. 与 F007 既有 pack_discovery 验证逻辑兼容 (`source_url` 不在 required fields list).

### ADR-D11-6: C part — `garage pack install` 装到 `<workspace>/packs/<pack-id>/` 不直接装到 host

与 `garage init --hosts ...` 解耦: install 是把 pack 物化到 workspace `packs/`; 用户后续跑 `garage init --hosts ...` 才装到 host (与既有用户 mental model 一致, 不引入新 install 路径).

### ADR-D11-7: C part — `garage pack ls` 输出格式与 F007 marker family 对齐

`Installed packs (N total):` + 每行 `<pack-id> v<version> [<source_url|"local">]`. 复用 F007 既有 `pack_discovery.discover_packs` 拿 packs list.

## 3. 测试矩阵

### INV
- INV-F11-1: `KnowledgeType.STYLE` 存在 + TYPE_DIRECTORIES 映射正确
- INV-F11-2: F010 sync compiler include STYLE kind, footer count 正确
- INV-F11-3: 2 个 agent.md 通过 F007 pack discovery + 装到 .claude/agents 与 .opencode/agent
- INV-F11-4: F008 `test_full_packs_install.py` INV-1 同步 (31 skills + 3 agents, manifest.files 增 4)
- INV-F11-5: `garage pack install file:///<dst>` 物化 + pack.json source_url 写入
- INV-F11-6: `garage pack ls` marker 与 F007 family 一致
- INV-F11-7: F010 baseline 825 → ≥ 825 (CON-1101 + INV-F10-2 sentinel 沿用)

### 测试文件
- `tests/knowledge/test_style_kind.py` (A)
- `tests/sync/test_compiler_style.py` (A)
- `tests/test_cli.py::TestKnowledgeAddStyle` (A)
- `tests/adapter/installer/test_garage_agents.py` (B + INV-F11-3)
- 既有 `tests/adapter/installer/test_full_packs_install.py` 同步 (B + INV-F11-4)
- `tests/adapter/installer/test_pack_install.py` (C)
- `tests/test_cli.py::TestPackInstallCommand + TestPackLsCommand` (C)

## 4. Commit 分组

| Task | 描述 |
|---|---|
| **T1** | A: KnowledgeType.STYLE + TYPE_DIRECTORIES + tests |
| **T2** | A: F010 sync compiler include STYLE + tests |
| **T3** | B: 2 agent.md + packs/garage/pack.json agents update + tests |
| **T4** | C: pack_install module + cli (install/ls) + pack.json source_url + tests |
| **T5** | docs sync (AGENTS / user-guide / RELEASE_NOTES F011 段) + finalize |

5 commits — 简单 cycle.
