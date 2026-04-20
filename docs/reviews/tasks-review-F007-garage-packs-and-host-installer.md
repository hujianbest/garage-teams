# Tasks Review — F007 Garage Packs 与宿主安装器

- 评审对象: `docs/tasks/2026-04-19-garage-packs-and-host-installer-tasks.md`（草稿）
- 上游规格: `docs/features/F007-garage-packs-and-host-installer.md`（已批准）
- 上游设计: `docs/designs/2026-04-19-garage-packs-and-host-installer-design.md`（已批准 r2）
- 上游 approval evidence:
  - `docs/approvals/F007-spec-approval.md`
  - `docs/approvals/F007-design-approval.md`
- 上游 review 链路:
  - `docs/reviews/spec-review-F007-garage-packs-and-host-installer.md`
  - `docs/reviews/design-review-F007-garage-packs-and-host-installer.md`
- Workflow: profile=`coding`, mode=`auto-mode`, isolation=`in-place`, branch=`cursor/f007-packs-host-installer-fa86`
- Reviewer: hf-tasks-review subagent (independent)
- Date: 2026-04-19

---

## Precheck

| 项 | 结果 |
|----|------|
| 任务计划稳定可定位 | ✅ 单文件、`草稿` 状态、5 个任务 + 里程碑 + queue projection + 文件影响图齐 |
| 上游 spec approval evidence 可回读 | ✅ `F007-spec-approval.md` 引用 r2 review `通过`，0 critical / 0 important / 0 minor |
| 上游 design approval evidence 可回读 | ✅ `F007-design-approval.md` 引用 r2 review `通过`，7 条 r1 finding 全闭合 + N-1 carry-forward 单行清理 |
| route/stage/profile 一致 | ✅ task-progress.md `Current Stage: hf-tasks` / `Next Action: hf-tasks-review` / `Workflow Profile: coding` / `Execution Mode: auto-mode` |
| 无 USER-INPUT 阻塞证据冲突 | ✅ spec FR-701~710、NFR-701~704、CON-701~704、ADR-D7-1~5 在任务计划 §3 / §4 全部定位 |
| 触碰文件现实 | ✅ `cli.py` 当前 1759 行；任务计划承诺 `cli.py` 增量 ≤ 80 行，主要逻辑在新 `src/garage_os/adapter/installer/` 子包 |

Precheck 通过，进入正式审查。

---

## 多维评分（每维 0-10）

| ID | 维度 | 分 | 关键依据 |
|---|---|---|---|
| TR1 | 可执行性 | 9 | 5 个任务都是单一 commit 闭环；T3 接近上限（4 新模块 + 6 测试文件 + 22-28 用例），但通过 walking skeleton 起步 + decision-table 化 `_decide_action` 拆得动；无 "实现某模块" 式模糊任务。T1 是纯内容创建任务但 acceptance 都可 `ls`/`cat` 验证 |
| TR2 | 任务合同完整性 | 9 | 每任务都齐 目标 / Acceptance / 依赖 / Ready When / Selection Priority / Files / 测试设计种子 / Verify / 预期证据 / 完成条件；多数 acceptance 直接到字段断言级（`installed_hosts` 排序、`MANIFEST_SCHEMA_VERSION = 1`、`cursor.target_agent_path("any") == None` 等）|
| TR3 | 验证与测试设计种子 | 9 | T2-T5 都显式列出主行为 / 关键边界 / fail-first 点 + 具体 test 名（`test_get_adapter_returns_claude_install_adapter` / `test_install_packs_writes_skill_and_manifest` / `test_hosts_explicit_list` 等），T3 walking skeleton 与 D7 §13 测试矩阵一一对照；T1 因为是纯数据生成任务，verify 是 `cat` / `json.tool` / `rg` 三条命令，可接受但 fail-first 点为空 |
| TR4 | 依赖与顺序正确性 | 10 | T1→T2→T3→T4→T5 严格线性，§6 显式给出"为什么不并行"的三条理由（单 cycle / review 隔离 / fixture 顺序）；与设计 §15 任务规划准备度示意一致；无循环依赖；§3.3 显式声明性兜底（不修改 F001 host_adapter 等模块）|
| TR5 | 追溯覆盖 | 10 | §4 trace 表逐行覆盖 FR-701~710 / NFR-701~704 / CON-701~704，每条三栏（spec ID + design 锚点 + 任务 + 验证用例）；§3 文件影响图覆盖每任务的新增/修改/不修改三列，明显满足 design §3 / §9 模块边界声明 |
| TR6 | Router 重选就绪度 | 10 | §8 唯一规则（Selection Priority 最小 + Ready When 全部满足）→ 线性序列即明确；§9 队列投影 5 列表（Status/Priority/Ready/Owner/Notes）可冷读；§8 显式覆盖"被 review 打回"分支：任务回到 `active`，前置 evidence 不重做；router 可稳定重选 |

无任何关键维度 < 6。

---

## 发现项

- [minor][LLM-FIXABLE][TR3] **F-1 — T1 缺 fail-first 点的显式表达**：T1 测试设计种子写的是"人工 review + 后续 T3 `test_pack_discovery.py` 会消费这些工件作为 fixture（read 验证）"。T1 是纯内容生成任务（5 个新文件），没有"先写 RED 测试再 GREEN"的天然路径，task plan 也未对此做显式说明。建议在 hf-test-driven-dev 阶段把 T1 的 verify 三条命令本身视为"伪 fail-first"——即在文件落盘前 `cat` 命令应失败，落盘后通过；或在 §5 T1 显式注一行"T1 无 RED 阶段，verify-as-test"。不阻塞通过。

- [minor][LLM-FIXABLE][TR3] **F-2 — `marker.inject` 二次注入幂等性未在 T3 acceptance 单列**：design §10.4 表说明 `inject(content, pack_id, source_kind)` 在 SKILL.md 强制 front matter、在 agent.md 容错插入。但 spec FR-708 验收 #1 暗含"标记块的存在不应导致 SKILL.md front matter 解析失败"——意味着对已含 `installed_by: garage` 的源（例如用户从 `.claude/skills/` 拷回 `packs/`）二次 `inject` 应当幂等不重复追加。T3 acceptance 写的是 "强制源含 front matter（否则 MalformedFrontmatterError）→ 注入两字段"，但未指明若源已有 `installed_by` 是否覆写 / 跳过 / append。design §10.4 表也未明确这点。建议在 hf-test-driven-dev 阶段的 `test_marker.py` 补一条 `test_idempotent_reinjection` 用例，断言"二次 inject 同 pack_id 字面相等"；若行为是覆写，则与 design §10.2 `UPDATE_FROM_SOURCE` 决策相容。属于实现阶段顺手补，不阻塞通过。

- [minor][LLM-FIXABLE][TR2] **F-3 — T2 Ready When 表述与"功能上独立可并行"略有歧义**：T2 description 写"无（与 T1 无强依赖；可与 T1 并行，但 §8 选择规则将 T1 排在前确保单线推进）"，但 Ready When 写"T1 完成（保持单线推进，避免 review 时双任务交叉）"。两处措辞不矛盾但需要读者跳跃理解。建议把 description 行的"无"改为"功能上无；本计划选择线性，Ready When = T1 完成"。Minor，hf-tasks 可在 approval 后顺手清理或留到下次 retro。

- [minor][LLM-FIXABLE][TR5] **F-4 — FR-710 / CON-704 仅由 "人工 review" 验证**：§4 trace 表 FR-710 与 CON-704 验证用例列为 "人工 review（review 阶段）"。这本身不违规（spec 验收 #1 是"5 分钟内回答 3 个问题"，本质是冷读测试），但 task plan 未指明谁在哪个阶段做这次冷读（是 hf-test-review 还是 hf-traceability-review？）。建议在 T5 acceptance 末尾或 §7 完成定义中明确"FR-710 验收由 hf-traceability-review 阶段执行 5 分钟冷读，作为 review 通过条件之一"。不阻塞通过。

- [minor][LLM-FIXABLE][TR2] **F-5 — T4 manual smoke 没有 fallback 计划**：T4 verify 写"manual smoke（hf-test-driven-dev 阶段执行）：在 `/tmp/f007-smoke/` 临时目录跑 `garage init --hosts all`"。这是良好的端到端验证，但若 cursor cloud agent 在 sandbox 中不能产生真实 `/tmp/` 目录或 `garage init` CLI 在子进程不可达，该 smoke 会被 skip。建议在 hf-test-driven-dev 阶段先用 `subprocess.run` 在 pytest 内做等价 smoke（已有 F005 `tests/test_cli.py::TestInitWithHosts` 同模式可借鉴），如真无法跑 manual 则有自动化回退。属于实现阶段决策，不阻塞通过。

---

## 缺失或薄弱项

- 上述 5 条均为 minor LLM-FIXABLE，可在 hf-test-driven-dev 阶段（测试设计种子展开时）一并吸收，不需要回 hf-tasks 重写。
- 任务计划遵循 F005 / F006 task plan 的同模式（每任务 inline 测试用例清单 + queue projection 表 + 文件影响图），符合 standard / coding profile 惯例；不强制每任务额外列 TestDesignApproval 段。
- §10 风险表显式覆盖 R2 (Cursor surface)、`_init` 签名扩展、pytest baseline 偏差、pre-existing mypy/ruff、SKILL.md front matter 兼容、跨 pack 冲突无 production fixture 6 项，与 design §18 与 spec §11 / §10 假设链对齐。

---

## 结论

**通过**

理由：

1. 6 个评审维度均 ≥ 9/10，全部高于通过阈值 6，TR4 / TR5 / TR6 均 10/10。
2. INVEST 全部满足：每任务 Independent（依赖图清晰，T2-T5 严格序列化）、Negotiable（线性化是显式选择并给出三条理由）、Valuable（每任务对应 spec FR/NFR/CON 一段或多段验收）、Estimable（Files / 测试用例数预估 / cli.py 增量上限均给出）、Small（每任务触碰文件 ≤ §3 表枚举的范围；T3 是上限但有 walking skeleton 起步）、Testable（acceptance 直接到字段 / stdout / exit-code / `pathlib.Path` 字面值）。
3. 追溯矩阵 §4 覆盖 FR-701~710 / NFR-701~704 / CON-701~704 / ADR-D7-1~5 / 设计 §10 / §11 / §13 全部锚点；无 orphan task；§3 文件影响图（新增 + 修改 + 不修改三列）覆盖所有任务变更，与 design §9 模块职责表交叉一致。
4. 依赖图正确无环；queue projection 表与 §8 active task 选择规则唯一，router 在任意单任务完成 / review 打回 / 用户 override 三种场景下均有明确重选路径。
5. 5 条 minor finding 全部 LLM-FIXABLE 且可在 hf-test-driven-dev 阶段（测试设计展开 / fixture 实现）顺手吸收，不影响计划本身可执行性，也不引入超出 spec/design 已批准 scope 的工作。
6. 所有任务声明性边界与 design §2 / §17 一致：F001 `HostAdapterProtocol` 零变更、F002 `garage init` CON-702 兼容、F003-F006 知识/经验/记忆/召回管道完全未触、不引入新 PyPI 依赖。

---

## 下一步

`任务真人确认`（auto-mode 下 reviewer 设 `needs_human_confirmation=true`，由编排层在 approval step 写 approval record；通过后可进入 `hf-test-driven-dev` 起 T1 — `packs/` 目录契约 + 占位 pack + 双层 README）。

---

## 记录位置

- 本评审记录: `docs/reviews/tasks-review-F007-garage-packs-and-host-installer.md`

---

## 交接说明

- `任务真人确认`：本结论为 `通过`；auto-mode 下编排层在 approval step 写 approval record（建议路径 `docs/approvals/F007-tasks-approval.md`），随后进入 `hf-test-driven-dev` 实现 T1（packs/garage/ 占位 pack + `pack.json` + `packs/README.md` + `packs/garage/README.md` + `garage-hello` SKILL.md + `garage-sample-agent.md`）。
- 5 条 minor finding 在 hf-test-driven-dev 阶段的测试设计展开里顺手吸收即可，无需回 `hf-tasks`。
- 不发起 `reroute_via_router`（无 route/stage/profile/上游证据冲突）。
