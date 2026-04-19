# Tasks Review — F005 Garage Knowledge Authoring CLI

- 评审目标: `docs/tasks/2026-04-19-garage-knowledge-authoring-cli-tasks.md`
- 关联规格: `docs/features/F005-garage-knowledge-authoring-cli.md`（已批准；`docs/approvals/F005-spec-approval.md`）
- 关联设计: `docs/designs/2026-04-19-garage-knowledge-authoring-cli-design.md`（已批准；`docs/approvals/F005-design-approval.md`）
- Workflow Profile: `standard`；Execution Mode: `auto`；Workspace Isolation: `in-place`
- Reviewer: hf-tasks-review subagent
- 日期: 2026-04-19

---

## 1. Precheck

| 项 | 状态 | 证据 |
|----|------|------|
| 任务计划稳定可定位 | ✅ | `docs/tasks/2026-04-19-garage-knowledge-authoring-cli-tasks.md` 草稿落盘 |
| 上游 spec approval 可回读 | ✅ | `docs/approvals/F005-spec-approval.md`（Round 2 通过） |
| 上游 design approval 可回读 | ✅ | `docs/approvals/F005-design-approval.md`（Round 1 通过 + 4 minor 内联收敛） |
| route/stage/profile 一致 | ✅ | `task-progress.md` Stage `hf-tasks`、Profile `standard`、Mode `auto`、Next Action `hf-tasks-review` |
| 任务边界与设计 §2.4 一致 | ✅ | 仅触碰 `cli.py` + `tests/test_cli.py` + `tests/test_documentation.py` + 用户指南 / 双 README |

→ Precheck 通过，进入正式评审。

---

## 2. 多维评分

| ID | 维度 | 分数 | 说明 |
|----|------|------|------|
| `TR1` | 可执行性 | 8/10 | 6 个任务边界清晰；T1 略偏大（含 handler + 2 helper + 6 个常量 + 9 项 acceptance），但仍在单 commit 闭环内，且 OT-501 已显式裁决 ID helper 独立单测 |
| `TR2` | 任务合同完整性 | 9/10 | 每任务都有 Acceptance / Files / Verify / 完成条件 / 依赖 / Risk；测试设计种子直接锚到 D005 §13.2 用例编号 |
| `TR3` | 验证与测试设计种子 | 9/10 | §13.2 用例 1-30 与各任务 Acceptance 条目一一映射；fail-first 点明确（NFR-503 smoke、CRUD 闭环、source-marker 跨命令断言） |
| `TR4` | 依赖与顺序正确性 | 8/10 | T2/T3/T4 依赖 T1（helper / 常量复用），T5 依赖 T4，T6 依赖 T1-T5；§1 + §6 双图无循环；T1 完成后 T2/T3/T4 同时 ready 但无显式 Selection Priority（见 finding F-1） |
| `TR5` | 追溯覆盖 | 10/10 | §4 矩阵覆盖 FR-501~510 / NFR-501~505 / CON-501~505 / ADR-501~503 / §10.2.1 / §13.2 用例 1-30；无 orphan task |
| `TR6` | Router 重选就绪度 | 7/10 | 依赖图清晰、退出标准可机判（pytest + grep），但缺 F004 §6.1/6.2 风格的"queue projection 表 + 唯一 Current Active Task 选择规则"；多个 ready 任务时 router 需靠 §1 / §6 的图自行推断顺序（见 finding F-1） |

任一关键维度均 ≥ 7/10，无低于 6/10 项 → 不触发 `不得通过` 红线。

---

## 3. Checklist 详查

### 3.1 可执行性（TR1）

- 每任务可单独 RED → GREEN → REFACTOR：✅
- 无"实现某模块"式空话：✅（每任务列出具体 handler 名 + 常量名）
- T1 体量较大但已切出 helper（`_generate_entry_id` / `_resolve_content`），OT-501 显式承诺 ID helper 独立单测，避免只能通过 add 路径间接验证
- 已通过 `cli.py` 实查（727 行 + ~7 handler 函数 + 模块顶层常量风格已建立）确认任务"在 `cli.py` 单文件加 7 handler"是工程现实

### 3.2 任务合同完整性（TR2）

- 每任务的"完成时必须为真"清晰：
  - T1: `decision-<id>.md` 含 8 项 front matter 字段 + stdout 含 ADDED_FMT + exit 0
  - T2: `version` 单调 +1 + selective overlay + publisher 元数据不被污染
  - T3: show 含 `version` / `source_artifact` derived 字段；delete 后 retrieve 返回 None
  - T4: `.json` 含 7 项字段 + `artifacts=["cli:experience-add"]` + `problem_domain` 默认 = `task_type`
  - T5: 中央索引 `.garage/knowledge/.metadata/index.json` 不再含 `exp-1`
  - T6: 7 条 docs grep + cross-cutting 断言 + smoke + 全 suite passed
- Files 段精确到 `src/garage_os/cli.py` / `tests/test_cli.py` 等具体路径

### 3.3 验证与测试设计种子（TR3）

- 测试设计种子直接对照 D005 §13.2 用例 1-30；每任务的"对应设计 §13.2 用例 N, M, …"反向锚点齐全
- fail-first 点：collision (T1 用例 7)、edit selective (T2 用例 9)、index pruned (T5 用例 23)、CRUD 闭环 (T6 用例 30)、smoke (T6 用例 29)
- monkeypatch 风险点显式标注（T1 Risk："建议 helper 接受 `now: datetime` 参数 … 避免 patch `cli.datetime`"）
- 没有"补测试""自行验证"这类空泛表述

### 3.4 依赖与顺序正确性（TR4）

- §1 与 §6 双图一致：T1 → {T2, T3, T4} → {T5} → T6
- T2 依赖 T1（`_resolve_content` + `ERR_CONTENT_AND_FILE_MUTEX`）
- T3 依赖 T1（基本框架 + `ERR_NO_GARAGE`）
- T4 依赖 T1（ID helper 命名约定 / `ERR_NO_GARAGE`）
- T5 依赖 T4（先有 add 才能测 show / delete）
- T6 依赖 T1-T5（全 suite 回归门）
- 无循环依赖、无顺序反转
- ⚠️ 当 T1 完成时 T2/T3/T4 同时 ready，task plan 缺显式 Selection Priority 表（F004 §6.1 / §6.2 的标准做法），router 重选时无唯一规则；详见 finding F-1

### 3.5 追溯覆盖（TR5）

- §4 矩阵 24 行，覆盖：
  - FR-501 / 502 / 503 / 504 / 505 / 506 / 507a / 507b / 508 / 509 / 510 — 全部映射到具体任务
  - NFR-501 / 502 / 503 / 504 / 505 — 全部映射，含 cross-cutting (T6) 与各任务承担份
  - CON-501 / 502 / 503 / 504 / 505 — 全部映射，含 CON-503 v1.1 不变量延伸（T2）+ CON-505 字节级一致断言（T1）
  - ADR-501（单文件）/ ADR-502（秒精度）/ ADR-503（cli: 前缀）— 全部映射
  - 设计 §10.2.1 edit 字段覆写表 → T2（含 publisher 元数据保护断言）
  - 设计 §13.2 用例 1-30 → 全覆盖
- 无 orphan task

### 3.6 Router 重选就绪度（TR6）

- 退出标准可机器判定（pytest exit code + grep）✅
- 完成条件每任务清晰列出 ✅
- 缺：
  - 显式 "queue projection" 表（行：Task ID / Status / Depends On / Ready When / Selection Priority）
  - 唯一 Current Active Task 选择规则（如 F004 §6.1: "T1 与 T4 都 ready；T1 是 P1，T4 是 P2 → router 锁定 T1"）
  - router 重选触发点（如 F004 §6.2）
- 现状：依赖图与 §6 段落隐式表达"T1 → 任选 T2/T3/T4 → 完成 T4 后再 T5 → T6"，但当 T1 完成、T2/T3/T4 同时 ready 时缺 tie-breaker
- 影响：在 `auto` 模式下 router 通常会按文档出现顺序选择，但严格按 SKILL.md TA7（unstable active task）该补 explicit 规则

---

## 4. 发现项

### 4.1 阻塞 / 重要

无。

### 4.2 minor / LLM-FIXABLE

- **F-1** `[minor][LLM-FIXABLE][TR6/TA7]` 缺"queue projection 表 + 唯一 Current Active Task 选择规则"
  - 现象: §1 / §6 用 mermaid-like 图表达依赖，但当 T1 完成、T2/T3/T4 同时 ready 时无显式 Selection Priority / Ready When；router 重选触发点也无段落（对照 F004 §6.1 / §6.2 的 standard 做法）
  - 影响: standard profile 下不致命（图本身可推断顺序），但 router 需靠图理解而非表格回读，存在 TA7 风险
  - 建议: 在 §6 后追加一段 `Task ID | Status | Depends On | Ready When | Selection Priority` 表 + "唯一 Current Active Task 选择规则" 1 段（参考 F004 §6.1 / §6.2 的最小模板）；不必增加新约束，仅把现有图的隐含顺序显式化（如 P1 = T1, P2 = T2, P3 = T3, P4 = T4, P5 = T5, P6 = T6）
  - 非阻塞通过：当前图 + 段落已能让 router 在 auto 下不卡壳（默认按 §6 dependency 图推进），但补完后 TR6 提分到 9-10

- **F-2** `[minor][LLM-FIXABLE][TR1/TA1]` T1 体量略大
  - 现象: T1 包含 1 个 handler + 2 个 helper（ID + content）+ 6 个常量 + 9 条 acceptance（含 collision / mutex / not-found / explicit-id 等多个分支）
  - 影响: 单任务 commit 体量较 T2~T5 偏大；已通过测试设计种子拆解可控
  - 建议: 不必拆，只需在 T1 描述里显式列出"helper 单元测试与 add handler 集成测试分两组 commit"作为实现提示（OT-501 已部分回应）；或将 `_generate_entry_id` 单测拆出小节（仍同任务）
  - 非阻塞通过：T1 acceptance 已分点列清，实现期可自然消化

- **F-3** `[minor][LLM-FIXABLE][TR2]` T6 acceptance 集合较密
  - 现象: T6 同时承担文档 grep（7 条）+ cross-cutting CLI help 断言（3 条）+ CRUD 闭环测试（1 条）+ smoke test（1 条）+ source-marker 跨命令断言（1 条）+ 全 suite 回归门
  - 影响: 完成判定可机器化（pytest passed + git diff + grep），但若任一断言挂起会拖延整轮收尾
  - 建议: 不必拆，但实现期可分 commit（docs commit + tests commit），或在 T6 acceptance 段把 5 类断言显式标号（A, B, C, D, E）便于按子项追踪
  - 非阻塞通过：当前结构已可执行，仅作风格优化建议

### 4.3 USER-INPUT

无。所有 finding 均 LLM-FIXABLE，且不影响业务范围或 spec/design 既已批准的边界。

---

## 5. 缺失 / 薄弱项

- 缺 "queue projection 表" 与 "唯一 Current Active Task 选择规则" 段（F-1）
- T6 5 类断言可考虑显式标号便于追踪（F-3，可选）

---

## 6. 结论

**通过**。

理由:
1. 6 个任务全部 INVEST 合格（Independent 依赖图清晰、Estimable 1-2 commit 内可消化、Small 边界限于 cli.py + 文档 + 测试、Testable 锚到 §13.2 用例 1-30）
2. 全部 FR / NFR / CON / ADR / 设计 §10.2.1 / 设计 §13.2 用例 1-30 均映射到任务
3. 依赖链无环、无顺序反转、关键路径合理（M1 → M2 → M3 与 T1 → … → T6 一致）
4. 完成判定全部可机器化（pytest exit code + grep）
5. F-1 / F-2 / F-3 三条 minor LLM-FIXABLE 均不阻塞，可在进入实现前由 author 单 commit 内联收敛或延后到下一 cycle

按 standard profile 阈值，TR1-TR5 全部 ≥ 8/10，TR6 = 7/10（非 critical），无任何 < 6/10 红线。

下一步: `任务真人确认`（auto mode 下父会话写 approval record 后即解锁 `hf-test-driven-dev`）。

---

## 7. 记录位置

`docs/reviews/tasks-review-F005-knowledge-authoring-cli.md`

---

## 8. 交接说明

- 父会话: 写 `docs/approvals/F005-tasks-approval.md`（auto-mode policy approver）后，进入 `hf-test-driven-dev` 实施 T1
- 建议在 approval 同 commit 内联收敛 F-1（补 §6 queue projection 表 + 唯一 Active Task 选择规则）；F-2 / F-3 可仅作为实现提示保留
- `reroute_via_router=false`；本评审不涉及 route / stage / profile / 上游证据冲突
