# T003: Garage Memory 自动知识提取与经验推荐任务计划

- 状态: 草稿
- 主题: F003 — Garage Memory（自动知识提取与经验推荐）
- 关联规格: `docs/features/F003-garage-memory-auto-extraction.md`
- 关联设计: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
- 关联审批:
  - `docs/approvals/F003-spec-approval.md`
  - `docs/approvals/F003-design-approval.md`

---

## 1. 概述

本任务计划把 F003 设计拆成 9 个可独立验证的工程任务，目标是在不破坏现有 `knowledge / experience / CLI` 链路的前提下，补齐：

1. memory 候选层与确认层
2. session 归档后的自动提取流程
3. 已确认候选的正式发布
4. 任务开始前的主动推荐

所有任务都遵循以下边界：

- 保持 workspace-first，不引入外部数据库、常驻服务、Web UI
- 自动提取只能生成候选，不得绕过用户直接发布
- 正式知识仍沿用现有 `KnowledgeStore` / `ExperienceIndex`
- 推荐只消费正式发布态，不消费未确认候选

---

## 2. 里程碑

| 里程碑 | 目标 | 任务数 | 退出标准 |
|--------|------|--------|----------|
| M1: Memory 基础契约 | 建立 memory 类型、目录、批次/候选/确认存储契约 + 开关契约 | 2 | 候选层文件契约与开关配置可写可读 |
| M2: 提取与发布主链 | 打通 session archive -> candidate batch -> confirm -> publish -> conflict handling | 4 | 最薄发布主链可跑通 |
| M3: 主动推荐与 CLI 面 | 打通默认主动推荐与 CLI-first 确认入口 | 3 | 新任务开始前能看到推荐，候选可通过 CLI 处理 |

---

## 3. 文件 / 工件影响图

### 3.1 新增源码模块（预期）

```text
src/garage_os/
├── memory/
│   ├── __init__.py
│   ├── types.py
│   ├── candidate_store.py
│   ├── signal_builder.py
│   ├── extraction_orchestrator.py
│   ├── conflict_detector.py
│   ├── publisher.py
│   └── recommendation_service.py
```

### 3.2 预期修改的现有模块

| 文件 | 影响类型 | 说明 |
|------|---------|------|
| `src/garage_os/types/__init__.py` | 修改 | 扩展正式发布态 traceability 字段 |
| `src/garage_os/cli.py` | 修改 | 增加 `garage memory review` 与执行前推荐展示 |
| `src/garage_os/runtime/session_manager.py` | 修改 | 在 archive 后触发 memory extraction orchestrator |
| `src/garage_os/runtime/skill_executor.py` | 修改 | 构造 recommendation context 并默认主动推荐 |
| `src/garage_os/knowledge/knowledge_store.py` | 修改 | 支持发布态 traceability 字段 |
| `src/garage_os/knowledge/experience_index.py` | 修改 | 支持 `experience_summary` 发布态字段 |

### 3.3 预期新增测试

| 文件 | 说明 |
|------|------|
| `tests/memory/test_candidate_store.py` | 候选批次/候选/确认记录存储 |
| `tests/memory/test_extraction_orchestrator.py` | archive 后自动提取主链 |
| `tests/memory/test_publisher.py` | candidate -> published knowledge/experience |
| `tests/memory/test_recommendation_service.py` | 主动推荐打分与降级 |
| `tests/test_cli.py` | 扩展 memory review / recommendation 展示 |
| `tests/integration/test_e2e_workflow.py` | 扩展最薄 memory 闭环 |

---

## 4. 需求与设计追溯

| 规格 / 设计锚点 | 覆盖任务 |
|----------------|----------|
| `FR-301` 自动触发知识提取；设计 9.1A 输入证据契约 | T2, T3 |
| `FR-302a` / `FR-302b` 四类候选与自描述追溯 | T1, T2 |
| `FR-303` / `FR-303a` 确认门禁、5 条上限、批量拒绝、延后处理 | T1, T4, T6 |
| `FR-304` 相似知识冲突处理 | T4, T5 |
| `FR-305` / `FR-306` 主动推荐与 `match_reasons` | T7, T8 |
| `FR-307` 失败降级 | T3, T8 |
| 设计 11.4 发布态 traceability / confirmation 契约 | T4, T5 |
| 设计 9.8 CLI-first canonical surface | T6, T7 |

---

## 5. 任务拆解

### T1. 建立 memory 类型与候选/确认存储契约

- 目标: 新增 memory 子模块的类型与存储层，支持 `CandidateBatch`、`CandidateDraft`、`ConfirmationRecord` 的读写。
- Acceptance:
  - `.garage/memory/candidates/batches/`、`.garage/memory/candidates/items/`、`.garage/memory/confirmations/` 可被初始化并读写
  - `CandidateDraft` 只能属于 `decision / pattern / solution / experience_summary`
  - 单批次候选数上限可被存储层校验
- 依赖: -
- Ready When: F003 spec/design approval 已完成
- 初始队列状态: ready
- Selection Priority: P1
- Files / 触碰工件:
  - `src/garage_os/memory/types.py`
  - `src/garage_os/memory/candidate_store.py`
  - `src/garage_os/memory/__init__.py`
  - `tests/memory/test_candidate_store.py`
- 测试设计种子:
  1. 正常写入一个 batch + 两个 candidate
  2. 候选类型非法时拒绝写入
  3. 候选数超过 5 时拒绝进入待确认队列
- Verify:
  - `uv run pytest tests/memory/test_candidate_store.py -q`
- 预期证据:
  - 候选批次/候选/确认记录测试通过
- 完成条件:
  - memory 基础 schema 与存储读写稳定可用

### T2. 实现输入证据组装与四类候选生成

- 目标: 基于设计 9.1A 的三层证据来源实现 `MemorySignalBuilder` 与 `CandidateGenerator`，生成四类候选并附带优先级和 `match_reasons`。
- Acceptance:
  - 支持 `session metadata / archived artifacts / experience records` 三层输入来源
  - 能生成四类候选并裁剪到最多 5 条
  - 能区分 `no_evidence / evaluated_no_candidate / evaluated_with_candidates`
- 依赖: T1
- Ready When: T1=done
- 初始队列状态: pending
- Selection Priority: P1
- Files / 触碰工件:
  - `src/garage_os/memory/signal_builder.py`
  - `src/garage_os/memory/extraction_orchestrator.py`
  - `tests/memory/test_extraction_orchestrator.py`
- 测试设计种子:
  1. 有最小证据 -> 生成至少 1 条候选
  2. 无证据 -> 写 `no_evidence`
  3. 有证据但全被过滤 -> 写 `evaluated_no_candidate`
- Verify:
  - `uv run pytest tests/memory/test_extraction_orchestrator.py -q`
- 预期证据:
  - 三种提取结果分支都有测试覆盖
- 完成条件:
  - 候选生成与结果判定契约闭合

### T3. 在 session archive 后自动触发 memory extraction

- 目标: 把 memory extraction orchestrator 接到 `SessionManager.archive_session()` 之后，做到提取失败不阻塞 session 归档。
- Acceptance:
  - session archive 成功后自动触发一次 extraction
  - extraction 异常时 session 仍 archived
  - extraction summary 能被记录到 memory batch / 日志工件
- 依赖: T2
- Ready When: T2=done
- 初始队列状态: pending
- Selection Priority: P1
- Files / 触碰工件:
  - `src/garage_os/runtime/session_manager.py`
  - `src/garage_os/memory/extraction_orchestrator.py`
  - `tests/runtime/test_session_manager.py`
  - `tests/memory/test_extraction_orchestrator.py`
- 测试设计种子:
  1. archive 后自动创建 batch
  2. orchestrator 抛错 -> archive 仍成功
  3. 无证据 session -> 生成 `no_evidence` batch
- Verify:
  - `uv run pytest tests/runtime/test_session_manager.py tests/memory/test_extraction_orchestrator.py -q`
- 预期证据:
  - session archive 与 extraction 解耦验证通过
- 完成条件:
  - archive -> extraction 主链打通且有失败降级

### T4. 实现 memory feature flag / 配置开关契约

- 目标: 为自动提取与主动推荐补齐可关闭的配置契约，明确配置落点、runtime 读取点与关闭时的降级行为。
- Acceptance:
  - 存在统一的 memory 配置落点，可分别控制 extraction 与 recommendation 开关
  - extraction 关闭时，archive 后不触发候选提取且 session 主链不受影响
  - recommendation 关闭时，任务开始前不触发推荐查询
- 依赖: T1
- Ready When: T1=done
- 初始队列状态: pending
- Selection Priority: P1
- Files / 触碰工件:
  - `.garage/config/platform.json`
  - `src/garage_os/memory/extraction_orchestrator.py`
  - `src/garage_os/memory/recommendation_service.py`
  - `src/garage_os/runtime/session_manager.py`
  - `src/garage_os/runtime/skill_executor.py`
  - `tests/memory/test_extraction_orchestrator.py`
  - `tests/memory/test_recommendation_service.py`
- 测试设计种子:
  1. extraction 开关关闭 -> archive 后不创建 batch
  2. recommendation 开关关闭 -> 推荐查询完全跳过
  3. 两个开关关闭时现有 session / CLI 主链仍工作
- Verify:
  - `uv run pytest tests/memory/test_extraction_orchestrator.py tests/memory/test_recommendation_service.py -q`
- 预期证据:
  - 开关 on/off 行为测试通过
- 完成条件:
  - 开关契约、配置落点与降级行为全部可回读

### T5. 实现 candidate review / publish 主链

- 目标: 实现 `CandidateReviewService` 与 `KnowledgePublisher`，支持 accept / edit_accept / reject / batch_reject / defer，并把接受的候选发布为正式知识或扩展后的 `ExperienceRecord`。
- Acceptance:
  - 用户确认动作会生成 `ConfirmationRecord`
  - 已接受候选发布后具备 `confirmation_ref` 与 `source_evidence_anchor`
  - `experience_summary` 发布态落入扩展后的 `ExperienceRecord`
  - 未确认候选不得进入正式 knowledge / experience
- 依赖: T1, T2
- Ready When: T1=done AND T2=done
- 初始队列状态: pending
- Selection Priority: P1
- Files / 触碰工件:
  - `src/garage_os/memory/publisher.py`
  - `src/garage_os/memory/candidate_store.py`
  - `src/garage_os/knowledge/knowledge_store.py`
  - `src/garage_os/knowledge/experience_index.py`
  - `src/garage_os/types/__init__.py`
  - `tests/memory/test_publisher.py`
  - `tests/knowledge/test_knowledge_store.py`
  - `tests/knowledge/test_experience_index.py`
- 测试设计种子:
  1. accept decision candidate -> 正式 knowledge 带 traceability 字段
  2. accept experience_summary -> 正式 experience record 带 confirmation_ref
  3. edit_accept -> 发布内容与 confirmation record 中的最终内容一致
  4. reject / defer -> 不发布正式数据
- Verify:
  - `uv run pytest tests/memory/test_publisher.py tests/knowledge/test_knowledge_store.py tests/knowledge/test_experience_index.py -q`
- 预期证据:
  - confirm -> publish 全链路测试通过
- 完成条件:
  - 发布态 traceability / confirmation schema 正式落地

### T6. 实现相似知识冲突探测与发布策略

- 目标: 在发布前接入 `ConflictDetector`，对相似正式知识给出 `coexist / supersede / abandon` 建议，并保证 supersede 关系可回读。
- Acceptance:
  - 发布前能探测相似正式 knowledge
  - 选择 supersede 时能写回新旧条目关系
  - 选择 abandon 时不发布正式知识
- 依赖: T5
- Ready When: T5=done
- 初始队列状态: pending
- Selection Priority: P2
- Files / 触碰工件:
  - `src/garage_os/memory/conflict_detector.py`
  - `src/garage_os/memory/publisher.py`
  - `tests/memory/test_publisher.py`
- 测试设计种子:
  1. 相似 knowledge -> 返回三类建议之一
  2. supersede -> 新旧关系正确写回
  3. abandon -> 不产生正式发布
- Verify:
  - `uv run pytest tests/memory/test_publisher.py -q`
- 预期证据:
  - 相似项探测和 supersede 行为测试通过
- 完成条件:
  - 冲突处理契约与发布策略闭合

### T7. 增加 CLI-first 候选确认入口

- 目标: 为第一版实现 canonical surface：`garage memory review <batch-id>`，支持查看候选、逐条处理、整批拒绝和延后处理。
- Acceptance:
  - CLI 可读取 pending / deferred batch
  - 支持 accept / edit_accept / reject / batch_reject / defer
  - CLI 操作调用的是统一 `CandidateReviewService`
- 依赖: T5
- Ready When: T5=done
- 初始队列状态: pending
- Selection Priority: P2
- Files / 触碰工件:
  - `src/garage_os/cli.py`
  - `src/garage_os/memory/candidate_store.py`
  - `tests/test_cli.py`
- 测试设计种子:
  1. `garage memory review <batch-id>` 能展示候选摘要
  2. batch_reject 后所有候选为 rejected
  3. defer 后 batch 仍可后续继续处理
- Verify:
  - `uv run pytest tests/test_cli.py -q`
- 预期证据:
  - CLI review 命令测试转绿
- 完成条件:
  - 第一版 canonical review surface 可用

### T8. 实现主动推荐服务、上下文构造与 `garage run` 展示路径

- 目标: 实现 `RecommendationContextBuilder` 与 `RecommendationService`，并把默认主动推荐真正接到 `garage run` 的 CLI canonical surface，在执行前输出推荐摘要。
- Acceptance:
  - 可按 `skill_name / params / session metadata / repository state` 构造 context
  - richer context 缺失时降级为 `skill_name_only`
  - 推荐只消费正式 knowledge / experience
  - `garage run <skill>` 在推荐开启时会于执行前展示一次推荐摘要
- 依赖: T4, T5
- Ready When: T4=done AND T5=done
- 初始队列状态: pending
- Selection Priority: P2
- Files / 触碰工件:
  - `src/garage_os/memory/recommendation_service.py`
  - `src/garage_os/runtime/skill_executor.py`
  - `src/garage_os/cli.py`
  - `tests/memory/test_recommendation_service.py`
  - `tests/runtime/test_skill_executor.py`
  - `tests/test_cli.py`
- 测试设计种子:
  1. rich context -> 返回带 `match_reasons` 的推荐
  2. skill_name_only -> 返回低置信度推荐并标记降级原因
  3. `garage run <skill>` 在执行前展示推荐摘要
  4. 推荐关闭 -> 完全跳过且不影响执行
- Verify:
  - `uv run pytest tests/memory/test_recommendation_service.py tests/runtime/test_skill_executor.py tests/test_cli.py -q`
- 预期证据:
  - 主动推荐、降级逻辑与 CLI 摘要展示测试通过
- 完成条件:
  - 推荐服务能被运行时稳定调用，且 CLI canonical surface 真正可见

### T9. 打通最薄端到端闭环并补回归验证

- 目标: 验证完整薄路径：archive -> candidate batch -> CLI review -> publish -> next run recommendation。
- Acceptance:
  - 一条最薄 E2E 流水线可在测试中跑通
  - memory feature 打开时新增链路可用
  - memory feature 关闭时现有 CLI / knowledge / experience 主链不回归
- 依赖: T3, T6, T7, T8
- Ready When: T3=done AND T6=done AND T7=done AND T8=done
- 初始队列状态: pending
- Selection Priority: P3
- Files / 触碰工件:
  - `tests/integration/test_e2e_workflow.py`
  - `tests/test_cli.py`
  - `tests/knowledge/test_integration.py`
- 测试设计种子:
  1. 归档后生成候选 -> CLI 接受一条 -> 正式发布
  2. 下一次执行前看到主动推荐
  3. 关闭推荐/提取开关 -> 现有链路仍通过
- Verify:
  - `uv run pytest tests/integration/test_e2e_workflow.py tests/test_cli.py tests/knowledge/test_integration.py -q`
- 预期证据:
  - 最薄闭环与兼容性回归都通过
- 完成条件:
  - F003 最薄可运行闭环具备新鲜证据

---

## 6. 依赖与关键路径

### 6.1 依赖图

```text
T1 -> T2 -> T3 -> T9
  \-> T4 -> T8 -> T9
        \-> T5 -> T6 -> T9
              \-> T7 -> T9
```

### 6.2 关键路径

关键路径建议：`T1 -> T2 -> T5 -> T8 -> T9`

原因：

- T1/T2 定义候选与证据 contract，是后续所有实现的根
- T5 决定正式发布态 schema
- T8 决定主动推荐与 `garage run` 展示主链
- T9 汇总最薄端到端验证证据

---

## 7. 完成定义与验证策略

### 7.1 里程碑完成定义

| 里程碑 | 完成定义 | 验证方式 |
|--------|---------|---------|
| M1 | memory 候选层 schema 与存储读写通过 | 单元测试 |
| M2 | archive -> extract -> confirm -> publish 主链通过 | 单元 + 集成测试 |
| M3 | CLI-first review + active recommendation + E2E 闭环通过 | CLI 测试 + E2E |

### 7.2 F003 实现完成定义

满足以下条件才可视为进入实现完成候选：

1. 9 个任务均完成
2. 最薄闭环测试有 fresh evidence
3. 提取失败不阻塞 session 的降级路径已验证
4. 推荐只消费正式发布态的约束已验证
5. memory feature 关闭时现有链路不回归

---

## 8. 当前活跃任务选择规则

1. 首个活跃任务固定为 **T1**，因为 memory 类型与存储契约是所有后续任务的最上游依赖。
2. 当且仅当存在一个 `ready` 任务时，将其锁定为 `Current Active Task`。
3. 若同时出现多个同优先级 `ready` 任务，停止自动推进并回到 `hf-workflow-router`。
4. 关键路径上的 `ready` 任务优先于非关键路径任务。
5. 未完成 approval step 前，不把任何实现任务写入 `task-progress.md` 的权威活跃任务。

---

## 9. 任务队列投影视图 / Task Board Path

```markdown
# Task Board

- Source Task Plan: docs/tasks/2026-04-18-garage-memory-auto-extraction-tasks.md
- Current Active Task: T1

## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority | Milestone |
|---------|--------|------------|------------|-------------------|-----------|
| T1 | done | - | spec/design/tasks approval 已完成 | P1 | M1 |
| T2 | done | T1 | T1=done | P1 | M1 |
| T3 | done | T2 | T2=done | P1 | M2 |
| T4 | done | T1 | T1=done | P1 | M1 |
| T5 | done | T1,T2 | T1=done AND T2=done | P1 | M2 |
| T6 | done | T5 | T5=done | P2 | M2 |
| T7 | done | T5 | T5=done | P2 | M3 |
| T8 | done | T4,T5 | T4=done AND T5=done | P2 | M3 |
| T9 | done | T3,T6,T7,T8 | T3=done AND T6=done AND T7=done AND T8=done | P3 | M3 |
```

---

## 10. 风险与顺序说明

### 10.1 高风险任务

| 任务 | 风险 | 缓解 |
|------|------|------|
| T2 | 证据来源与现有 session reality 不匹配 | 先以现有 session metadata / archived artifacts / experiences 为最小合同，不假设 transcript 必存在 |
| T4 | 开关契约没有稳定配置落点，导致 on/off 回归失真 | 先把 extraction/recommendation flag 落到统一配置与 runtime 读取点 |
| T5 | 发布态 traceability 字段破坏现有 schema | 用向后兼容扩展字段，补 targeted 测试 |
| T8 | 推荐上下文过度依赖 richer context，导致主链脆弱 | 设计 `skill_name_only` 降级路径，并显式覆盖 `garage run` 展示路径 |
| T9 | E2E 过于复杂导致信号不清 | 只验证最薄闭环，不把所有边界混进一条测试 |

### 10.2 顺序说明

- T1/T2 必须最先做，先稳定 memory contract，再谈提取与推荐
- T4 要尽早落地，因为 feature flag / 开关契约决定 extraction 与 recommendation 的 on/off 验证路径
- T5 在 T2 后优先于 T7/T8，因为确认发布 schema 是 review/publish/recommend 的共同基座
- T7/T8 可并行，但都依赖 T5；其中 T8 还依赖 T4 的开关契约
- T9 最后执行，收集 fresh E2E evidence

---

**文档状态**：已按计划完成实现，质量链收尾中

**下一步**：消费实现交接块与 fresh verification evidence，进入剩余质量链 / 完成门禁
