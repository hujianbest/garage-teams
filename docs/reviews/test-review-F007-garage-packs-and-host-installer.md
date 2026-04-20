# Test Review — F007 Garage Packs & Host Installer

- 日期: 2026-04-19
- Reviewer: subagent (`hf-test-review`)
- 评审对象:
  - 实现源: `src/garage_os/adapter/installer/{__init__.py,host_registry.py,pack_discovery.py,manifest.py,marker.py,pipeline.py,interactive.py,hosts/{claude,opencode,cursor}.py}`、`src/garage_os/cli.py`（init 段 + `_resolve_init_hosts` + `INSTALLED_FMT` 等常量）、`src/garage_os/platform/version_manager.py`
  - 新/改测试: `tests/adapter/installer/{test_host_registry,test_hosts,test_pack_discovery,test_manifest,test_marker,test_pipeline,test_neutrality,test_idempotent,test_interactive}.py`、`tests/test_cli.py::TestInitWithHosts`、`tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered`、`tests/test_documentation.py`（F007 段 2 用例）
- 上游工件:
  - spec `docs/features/F007-garage-packs-and-host-installer.md`
  - design `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md` (r2)
  - tasks `docs/tasks/2026-04-19-garage-packs-and-host-installer-tasks.md` (r1)

## Precheck

- 实现交接块稳定（5 个任务 T1-T5 全部落盘，pipeline / cli / version_manager 均有对应实现）。
- 测试资产可定位（`tests/adapter/installer/` 9 个文件 + 3 个跨模块新增类/函数）。
- route/stage/profile 与上游 evidence 一致：tasks.md r1 已批准、design r2 已批准、spec 已批准；处于 implementation→review 转换点。
- 父会话报告基线 `pytest tests/ -q` ≥ 576（基线 496 + F007 新增 80）；本 reviewer 自跑 F007 切片 80 用例全绿（见 §证据）。

Precheck 通过，进入正式评审。

## 证据基线

reviewer 自跑（仅 F007 切片）：

```
pytest tests/adapter/installer/ tests/test_cli.py::TestInitWithHosts \
       tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered \
       tests/test_documentation.py::test_user_guide_documents_pack_and_host_installer \
       tests/test_documentation.py::test_packs_readme_documents_directory_contract -v
============================== 80 passed in 0.33s ==============================
```

80 = 12 (host_registry) + 10 (hosts) + 8 (pack_discovery) + 7 (manifest) + 9 (marker) + 9 (pipeline) + 3 (neutrality) + 2 (idempotent) + 6 (interactive) + 8 (TestInitWithHosts) + 2 (TestHostInstallerSchemaRegistered) + 2 (test_documentation) = 78… 实际 collected 80（含 neutrality parametrize），与父会话 576 = 496+80 一致。

## FR / NFR / CON ↔ test 矩阵

| 需求 | 设计 | 测试 | 状态 |
|---|---|---|---|
| FR-701 packs 目录契约 | D7 §11.3 | `test_pack_discovery.py` (8 用例覆盖空、单 pack、双 pack 排序、缺 pack.json、非法 JSON、id 不匹配、skills/agents 与磁盘不一致 3 路径) + `test_documentation.py::test_packs_readme_documents_directory_contract` | ✅ |
| FR-702 `--hosts <list>` | D7 §10.1 / §11.1 | `test_host_registry.py::TestResolveHostsArg` (all/none/逗号/未知/空串/空白 trim) + `TestInitWithHosts::test_hosts_explicit_list / test_hosts_all_installs_three_first_class / test_hosts_none_explicit / test_unknown_host_exit_1_but_garage_dir_created` | ✅ |
| FR-703 交互式 + non-TTY | D7 §10.1 + ADR-D7-5 | `test_interactive.py` (non-TTY notice、`a` 全选、`q` 早停、回车默认 N、capital N、混合) | ✅ |
| FR-704 安装管道 + extend | D7 §10 | `test_pipeline.py::TestWalkingSkeleton / TestExtendHosts / TestNoPacksFound / TestCursorAgentSkip / TestConflict` | ✅ |
| FR-705 manifest schema | D7 §8.3 / §11.2 | `test_manifest.py` round-trip + sort + POSIX + invalid-JSON | ✅ |
| FR-706a 未修改幂等 | D7 §10.2 | `test_pipeline.py::TestExtendHosts` (claude mtime 不变) + `test_idempotent.py::test_target_mtime_preserved` + `test_force_with_unmodified_still_no_op` | ✅ |
| FR-706b `--force` 与跳过 | D7 §10.2 | `test_pipeline.py::TestLocallyModifiedProtection` (skip + force 两路径) | ✅ |
| FR-707 host registry | D7 §11.1 + ADR-D7-1 | `test_host_registry.py::TestHostRegistry` + `test_hosts.py` (3 adapter × 字面值 + cursor.target_agent_path == None) | ✅ |
| FR-708 marker | D7 §10.4 + ADR-D7-2 | `test_marker.py` (skill OK / 无 FM 抛错 / 幂等 / agent 容错 + 已有 FM / extract / 无 marker) | ✅ |
| FR-709 stable stdout/stderr | D7 §2.1 | `TestInitWithHosts::test_hosts_explicit_list` + `test_no_packs_dir_succeeds_with_marker` + `test_subprocess_smoke_three_hosts` 断言 `"Installed N skills, M agents into hosts: ..."`；stderr `Skipped/Overwrote` 由 `test_pipeline` 直接断言 | ✅ |
| FR-710 docs | D7 §2.1 | `test_documentation.py::test_user_guide_documents_pack_and_host_installer / test_packs_readme_documents_directory_contract` | ✅ |
| NFR-701 宿主无关性 | D7 §12 | `test_neutrality.py` (parametrize 真实 `packs/` 下 SKILL.md + agent .md，黑名单 regex `\.claude/|\.cursor/|\.opencode/|claude-code` IGNORECASE) | ✅ |
| NFR-702 性能 / 无写入 | D7 §10.2 / §12 | `test_idempotent.py` × 2 + `test_pipeline.py::TestExtendHosts` (mtime_ns 比较) | ✅ |
| NFR-703 跨平台路径 | D7 §11.2 | `test_manifest.py::TestPosixPathSerialization` | ✅ |
| NFR-704 零回归 | D7 §13 | 父会话 576 passed (基线 496 + 80) | ✅ |
| CON-701 adapter 位置 | D7 §9 | 物理路径 `src/garage_os/adapter/installer/hosts/{claude,opencode,cursor}.py` 存在 | ✅ |
| CON-702 不破坏 F002 | D7 §10.1 | `TestInitWithHosts::test_default_init_unchanged_when_no_hosts` | ✅ |
| CON-703 schema_version | D7 §11.3 | `tests/platform/test_version_manager.py::TestHostInstallerSchemaRegistered` × 2 | ✅ |
| CON-704 路径来源说明 | D7 §12 | 文档（属 traceability review，不在测试评审范围） | n/a |

## 评分

| ID | 维度 | 分数 | 备注 |
|---|---|---|---|
| TT1 | fail-first 有效性 | 7/10 | walking skeleton + 关键边界 5（marker 幂等 reinjection）显式按 fail-first 设计；handoff 未单独保留 RED 截图，但用例与实现互锁、人工反向阅读可推导 |
| TT2 | 行为 / 验收映射 | 9/10 | 全部 FR/NFR/CON 落到具体用例，且追溯表对齐 D7 §13；少数 CLI 异常分支未直接断言 exit code |
| TT3 | 风险覆盖 | 7/10 | 关键边界齐全：non-TTY、empty packs、unknown host、locally modified、--force、cross-pack 同名冲突、cursor agent skip、untracked-dst skip 全部命中；CLI exit code 2 (ConflictingSkillError) / exit code 1 (InvalidPackError / PackManifestMismatchError / MalformedFrontmatterError / OSError) 走 pipeline 层，CLI 包装层未直接验证 |
| TT4 | 测试设计质量 | 8/10 | 多用真实 `tmp_path`，唯一 monkeypatch 是 `builtins.input`（合理边界 mock）；`TestInitWithHosts._link_packs` 用 `symlink_to(REPO_ROOT/packs)` → 当前 1 skill+1 agent 下硬编码 "Installed 1 skills, 1 agents" / "Installed 3 skills, 2 agents" 在未来 packs 内容增加时会脆 |
| TT5 | 新鲜证据完整性 | 8/10 | reviewer 自跑 80 passed in 0.33s 可冷读；父会话 576 总数与基线 496+80 一致 |
| TT6 | 下游就绪度 | 8/10 | 测试覆盖足以让 `hf-code-review` 可信判断：契约形态、决策表、稳定 marker、幂等、宿主无关全部已锁；下游聚焦代码风格 / mypy / ruff 即可 |

任一维度均 ≥ 6，可进入 code review。

## 发现项

- [minor][LLM-FIXABLE][TT3 / TA2] CLI 包装层异常分支未端到端验证
  - `cli._init` 的 `except ConflictingSkillError → return 2`（line 269-271）、`except (InvalidPackError, PackManifestMismatchError) → return 1`（272-274）、`except MalformedFrontmatterError → return 1`（275-277）、`except OSError → return 1`（278-280）四条分支没有任何 `tests/test_cli.py::TestInitWithHosts` 用例触发。pipeline 层 `test_pipeline.py::TestConflict` 只验证 `install_packs` 直接抛 `ConflictingSkillError`，不覆盖 `main(["init", ...])` 的退出码契约（spec § 4.1 退出码语义 / D7 §14 失败模式表）。
  - 建议补 1-2 个 CLI 用例：用 fixture 构造冲突 packs 直接走 `main(...)`，断言退出码 2 + stderr 含冲突 src/dst；或 monkeypatch `install_packs` 抛异常验证 4 条 except 分支映射。

- [minor][LLM-FIXABLE][TT4 / TA1] CLI 整数 marker 硬编码与 packs 真实状态耦合
  - `TestInitWithHosts::test_hosts_explicit_list` 断言 `"Installed 1 skills, 1 agents into hosts: claude"`，`test_subprocess_smoke_three_hosts` 断言 `"Installed 3 skills, 2 agents"`。两者依赖仓库根 `packs/garage/` 当前精确包含 1 skill + 1 agent；未来 T1 之后任何 pack 内容增量都会让这些用例同时失败、且不易直观对应根因。
  - 建议改为参数化或动态计算（`len(discover_packs(packs_root))` 推导），或在测试中使用 `_link_packs` 指向独立 fixture pack 目录。**非阻塞**——当前 packs 内容稳定，发现路径明确即可。

- [minor][LLM-FIXABLE][TT2] FR-705 ISO-8601 / SHA-256 格式校验未做正则验证
  - `test_manifest.py` 使用硬编码 `"2026-04-19T12:00:00"` 字符串与 `"0" * 64` 占位 hash 走 round-trip，仅断言赋值后 round-trip 一致；spec FR-705 验收 #2 要求 `installed_at` "为 ISO-8601 时间戳"、`content_hash` "必须是 SHA-256 hex 形式"。`test_pipeline.py::TestWalkingSkeleton` 间接验证了 content_hash 与实际写入字节匹配（hexdigest），但 ISO-8601 形式未单独以正则/`datetime.fromisoformat` 验证。
  - 建议在 `test_manifest.py` 增 1 用例：`datetime.fromisoformat(manifest.installed_at)` 不抛错 + `re.fullmatch(r"[0-9a-f]{64}", entry.content_hash)`。

- [minor][LLM-FIXABLE][TT3] `_decide_action` 决策表 7 行未全覆盖
  - D7 §10.2 共 7 行。覆盖：WRITE_NEW（walking skeleton）、UPDATE_FROM_SOURCE（idempotent）、SKIP_LOCALLY_MODIFIED（hash 差 + force=False）、OVERWRITE_FORCED（hash 差 + force=True）。**未直接覆盖**：(a) `existing != None` 但 `dst_exists == False`（用户删除已安装文件 → WRITE_NEW restore）；(b) `existing == None` 且 `dst_exists == True` 且 `force=True`（untracked 用户文件被 force 覆盖路径）。
  - 建议各补 1 用例。两者都属于 D7 决策表声明但无直接断言的边界。

- [minor][LLM-FIXABLE][TT3] FR-703 non-TTY + 无 `--hosts` + 无 `--yes` CLI 链路未端到端验证
  - `test_interactive.py::TestNonInteractive::test_non_tty_returns_empty_with_notice` 直接测 `prompt_hosts(non_tty)` 返回 `[]` 并写 stderr 提示。CLI 端 `TestInitWithHosts` 用 `--yes` 走 short-circuit，并未让 `_init` 在 non-TTY pytest 环境下经过 `prompt_hosts` 实际打印那条 stderr notice + `.garage/` 创建成功的组合断言。
  - 建议补 1 个 CLI 用例：在 pytest 默认 non-TTY 下不传任何 `--hosts*` flag → 断言 stderr 含 `non-interactive shell detected` + 退出码 0 + 无 host 目录创建。

- [minor][LLM-FIXABLE][TT4] `_check_conflicts` 仅在 skill 路径下被显式测过
  - `TestConflict::test_conflict_same_skill_two_packs` 触发的是 skill 冲突；`_check_conflicts` 同一逻辑也会在 agent 重名时抛同一异常，但无 test。属于 minor，逻辑等价、风险低。

## 缺失或薄弱项

- 上述 5 条 minor finding；其中"CLI 异常分支未端到端"对 `hf-traceability-review` / `hf-completion-gate` 阶段最有价值，建议在 code review 阶段一并覆盖或在 traceability review 时显式标注 carry-forward。
- 无 critical / important 级别缺口；核心 acceptance 全部已经被有效用例锁住。

## 结论

**通过**

- 6 个评审维度均 ≥ 7/10，无关键维度阻塞。
- FR-701~710、NFR-701~704、CON-701~703 全部存在与之锁住的有效测试。
- Walking skeleton（`test_install_packs_writes_skill_and_manifest`）、关键边界（locally-modified / force / extend / cross-pack conflict / cursor agent skip / no packs / unknown host）、宿主中立 grep、mtime 不刷新、CLI 默认行为字节相同、VersionManager 注册全部命中。
- 5 条 minor finding 均为 LLM-FIXABLE 且不阻塞 code review；建议在下一步 code review / traceability 阶段顺带闭合。

## 下一步

- `hf-code-review`（按 reviewer return contract）
- `needs_human_confirmation=false`
- `reroute_via_router=false`

## 结构化返回 JSON

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "hf-code-review",
  "record_path": "docs/reviews/test-review-F007-garage-packs-and-host-installer.md",
  "key_findings": [
    "[minor][LLM-FIXABLE][TT3] CLI 异常分支 (ConflictingSkillError exit 2 / InvalidPackError / MalformedFrontmatterError / OSError exit 1) 未端到端验证；pipeline 层有覆盖",
    "[minor][LLM-FIXABLE][TT4] TestInitWithHosts 硬编码 \"Installed N skills, M agents\" 数字与真实 packs/ 内容耦合",
    "[minor][LLM-FIXABLE][TT2] FR-705 installed_at ISO-8601 / content_hash SHA-256 hex 格式未做正则验证（仅 round-trip）",
    "[minor][LLM-FIXABLE][TT3] _decide_action 决策表 2 行 (existing!=None & dst missing; existing=None & dst exists & force=True) 未直接覆盖",
    "[minor][LLM-FIXABLE][TT3] FR-703 non-TTY + 无 flags CLI 链路未端到端断言"
  ],
  "needs_human_confirmation": false,
  "reroute_via_router": false,
  "finding_breakdown": [
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT3", "summary": "CLI exit-code 包装分支 (2 / 1) 未端到端验证"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT4", "summary": "TestInitWithHosts 硬编码 Installed N skills, M agents 数字脆"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT2", "summary": "manifest installed_at / content_hash 形式未正则校验"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT3", "summary": "_decide_action 决策表 2 个边界未直接覆盖"},
    {"severity": "minor", "classification": "LLM-FIXABLE", "rule_id": "TT3", "summary": "FR-703 non-TTY 无 flag CLI 链路缺端到端用例"}
  ]
}
```
