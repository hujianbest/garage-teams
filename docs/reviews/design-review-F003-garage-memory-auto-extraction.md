# 设计评审记录：F003 Garage Memory 自动知识提取与经验推荐

- 评审对象: `docs/designs/2026-04-18-garage-memory-auto-extraction-design.md`
- 关联规格: `docs/features/F003-garage-memory-auto-extraction.md`
- 关联批准记录: `docs/approvals/F003-spec-approval.md`
- 评审日期: 2026-04-18
- 评审角色: 独立 reviewer subagent

## Precheck

- 已存在稳定可定位的设计草稿，且 `task-progress.md` 明确当前处于 `hf-design`、待执行 `hf-design-review`。
- 已批准规格可回读，`docs/approvals/F003-spec-approval.md` 与规格状态一致。
- route / stage / profile / approval evidence 无冲突，本次 design review 合法进入正式评审。

## 结论

需修改

这份设计方向正确，且总体与 Garage 现有代码现实兼容：它没有凭空重起体系，而是以新增 `memory` 编排层的方式复用现有 `KnowledgeStore`、`ExperienceIndex`、`SessionManager`、`SkillExecutor` 等模块；workspace-first、用户确认先于发布、候选与正式知识分层这些边界也都守住了。

但当前版本仍有 3 个 approval 前应补齐的设计空洞，集中在“输入证据契约”“发布后的可追溯契约”“执行前推荐触发上下文”三处。这些问题不属于需求漂移，也不需要 reroute，但会直接把接口和任务规划的闭环压力转嫁给后续 `hf-tasks` / 实现阶段，因此结论为 **需修改**，下一步回到 `hf-design` 做定向修订。

## 维度评分

| 维度 | 评分 | 评语 |
|------|------|------|
| `D1` 需求覆盖与追溯 | 8/10 | 规格到模块的追溯总体完整，FR-301~FR-307 与 NFR-301/302/304 均有显式承接。 |
| `D2` 架构一致性 | 8/10 | 逻辑组件、主流程、职责边界清楚，且选定方案与现有 `garage_os` 分层基本一致。 |
| `D3` 决策质量与 trade-offs | 9/10 | 至少比较了 A/B/C 三个候选方案，trade-off、选型理由和后果清晰，可冷读。 |
| `D4` 约束与 NFR 适配 | 6/10 | 用户确认、workspace-first、失败降级已吸收，但发布后的 traceability / schema 演进契约未闭合。 |
| `D5` 接口与任务规划准备度 | 6/10 | 批次、候选、流程都已成型，但提取输入证据与推荐触发输入这两个关键接口仍留给下游猜。 |
| `D6` 测试准备度与隐藏假设 | 7/10 | 有验证路径、测试层次和失败模式，但高风险输入假设尚未充分显式化到契约层。 |

## 发现项

- [important][LLM-FIXABLE][D5] 自动提取的输入证据契约未闭合。设计多次声明 `MemorySignalBuilder` / `MemoryExtractionOrchestrator` 会读取 session transcript、artifact、experience 作为提取证据，但正文没有把“这些证据具体存在哪里、最小必需字段是什么、缺失时如何判定”为明确 contract 写出来。现有代码里 `SessionManager` 持久化的 `session.json` 只有基础 metadata，`artifacts` 也未形成稳定证据面；`KnowledgeIntegration.extract_from_session()` 目前更是直接吃调用方传入的 `experience_data`。如果这里不补 contract，`hf-tasks` 无法稳定拆出 `MemorySignalBuilder`、证据读取器和失败降级逻辑。

- [important][LLM-FIXABLE][D4] “已确认后如何保持全链路可追溯”在正式数据契约里还没落地，尤其是 `experience_summary`。设计要求候选和已发布知识都能回溯到 session、artifact、evidence anchor 与 confirmation action，也写了 `KnowledgePublisher` 会更新 `confirmation reference`；但正文并未把这个字段落到正式 `KnowledgeEntry` / `ExperienceRecord` 的 schema 变化上。当前代码现实中，`KnowledgeEntry` 只有 `source_session` / `source_artifact`，`ExperienceRecord` 只有 `session_id` / `artifacts`，都不足以表达确认动作引用。若不补齐，FR-302b、FR-303、NFR-301、CON-303 在发布态会失真。

- [important][LLM-FIXABLE][D5] 主动推荐的触发输入与首版交互入口仍不够收口。设计选择在 `SkillExecutor.execute_skill()` 开始阶段默认触发推荐，并按 skill、domain、problem_domain、key_patterns、artifact tags 做启发式匹配；但现有 `SkillExecutor` 现实只有 `skill_name + params` 的浅层输入，正文没有定义这些 richer context 从哪里构造、缺失时如何降级，也没有把首版“确认/展示入口”明确收敛到一个 canonical surface（CLI、宿主对话面、文件 inbox 仍是并列描述）。这会让推荐接口和确认接口在任务规划时缺少稳定切入点。

## 薄弱或缺失的设计点

- 现有 `artifact_board_sync.py` 已经实现了 artifact-first 一致性协议，说明“文件真相优先”不是空想；设计若补齐 memory 证据 contract，应尽量沿用这种“显式比较 + 日志记录”的现实风格，而不是另起一套隐式机制。
- 方案对比、失败模式、批次上限、冲突检测、defer / batch reject 等核心治理动作已经足够清楚，不建议大改架构，只需定向补 contract。
- `experience_summary` 不必强行升级成新的正式 `KnowledgeType`，但必须把“发布态落盘结构 + traceability 字段 + recommendation 消费方式”写成稳定契约。

## 下一步

- `需修改`：`hf-design`

建议作者只做一轮定向修订，重点补齐：

1. 自动提取输入证据的最小 contract（来源、字段、缺失记录、失败降级）。
2. 发布后正式数据的 traceability / confirmation schema，特别是 `experience_summary`。
3. 推荐触发输入和首版确认/展示入口的 canonical 接口约束。

## 记录位置

- `docs/reviews/design-review-F003-garage-memory-auto-extraction.md`

## 交接说明

- 本次评审不是 workflow blocker，不需要 `hf-workflow-router`。
- 设计的总体方向可保留；修改重点是 closing contracts，而不是重写架构。
- 修订完成后，可再次提交 design review；只有在这些 contract 闭合后，才适合进入后续 approval step。
