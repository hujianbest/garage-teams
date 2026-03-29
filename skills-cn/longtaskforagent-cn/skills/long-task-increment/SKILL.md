---
name: long-task-increment
description: "当存在 increment-request.json 时使用；收集增量需求、执行影响分析、更新设计并拆解新功能"
---

# 增量需求开发

在已运行中的项目中新增需求、修改既有需求或废弃功能。所有变更回写到既有 SRS/Design/UCD 文档（通过 git 历史追踪），新功能以 wave 元数据追加到 `feature-list.json`。

**开始时声明：**「我正在使用 long-task-increment 技能。在收集新需求之前，让我先了解当前项目状态。」

## 前置条件

- 已存在 `feature-list.json`（项目已完成初始化）
- 项目根目录存在 `increment-request.json`（由用户创建的信号文件）

## 检查清单

你必须为每一步创建 TodoWrite 任务并按顺序完成：

### 1. 摸底

- 阅读 `increment-request.json` — 理解本次增量的原因与范围
- 阅读 `feature-list.json` — 掌握全部特性、状态、wave 历史、约束与假设
- 阅读已批准的 SRS（`docs/plans/*-srs.md`）— 当前需求基线
- 阅读已批准的设计（`docs/plans/*-design.md`）— 当前架构
- 若存在：阅读 ATS 文档（`docs/plans/*-ats.md`）— 当前测试策略基线
- 若为 UI 项目：阅读 UCD 风格指南（`docs/plans/*-ucd.md`）
- 若存在：阅读延期待办（`docs/plans/*-deferred.md`）— 可拾取的已预采集需求（对已有完整 EARS + 验收标准的条目跳过重复采集）
- 阅读 `task-progress.md` — 会话历史
- 执行 `git log --oneline -10` — 近期上下文
- 确定当前 wave 编号：`max(所有特性的 wave) + 1`（若无 wave 字段则默认为 1）

### 2. 增量需求采集

以结构化采集方式收集新增/变更需求（与 Phase 0a 同等严格）：

1. 使用 `AskUserQuestion` 分轮采集需求（每轮 2–4 个相关问题）
2. 对每条需求套用 EARS 模板：
   - **Ubiquitous**：The system shall...
   - **Event-driven**：When \<trigger\>, the system shall...
   - **State-driven**：While \<state\>, the system shall...
   - **Unwanted behavior**：If \<condition\>, then the system shall...
   - **Optional**：Where \<feature\>, the system shall...
3. 分配唯一 ID，在既有 SRS 基础上延续（例如最后一条 FR 为 FR-020，则新 ID 从 FR-021 起）
4. 为每条编写 Given/When/Then 验收标准
5. 按 8 项质量属性校验：Correct, Unambiguous, Complete, Consistent, Ranked, Verifiable, Modifiable, Traceable
6. 将变更归入三类：
   - **New**：全新的 FR/NFR 需求
   - **Modified**：对既有 FR/NFR 的修改（注明被修改的原始 ID）
   - **Deprecated**：不再需要的需求（注明被移除的 ID）

**产出**：结构化的新增/修改/废弃需求列表，含 ID、EARS 表述与验收标准。

### 3. 影响分析

将新需求与既有特性集对比：

1. 对每条 **new** 需求 → 识别其依赖的既有特性（若有）
2. 对每条 **modified** 需求 → 识别 `srs_trace` 引用原需求 ID 的既有特性；这些特性需重新验证
3. 对每条 **deprecated** 需求 → 识别实现该需求的特性；这些特性将标记为废弃
4. 检查依赖链影响 — 若某被修改特性被其他特性依赖，后者也可能需重新验证

**产出**：向用户展示影响矩阵以供批准：

```
| Change | Type | Affected Features | Action |
|--------|------|-------------------|--------|
| FR-021 | New | (none) | Add feature(s) |
| FR-005 (modified) | Modified | Feature 5, Feature 8 | Reset to failing, update srs_trace |
| FR-012 (deprecated) | Deprecated | Feature 12 | Mark deprecated |
```

**硬门禁**：用户必须批准影响矩阵后方可继续。

### 4. 设计修订

**就地**更新既有设计文档中与本次变更相关的章节：

1. 阅读 `docs/plans/*-design.md`
2. 对 **new** 需求：
   - 新增 Key Feature Design 小节（4.N+1），含类图、时序图、流程图
   - 若新特性有依赖，更新 Dependency Chain（11.3）
   - 在 Task Decomposition（11.2）中更新优先级
   - 将新的第三方依赖加入依赖表
3. 对 **modified** 需求：
   - **就地**更新对应 Key Feature Design 小节（4.N）
   - 按需更新时序/流程图
4. 对 **deprecated** 需求：
   - 在对应设计小节增加 `[DEPRECATED - Wave N]` 标记
   - **不要**删除该小节（保留历史上下文）
5. 分节征得用户批准
6. 以描述性信息提交设计更新的 Git commit：
   ```
   docs: update design for wave N — <brief scope>

   New: FR-021 (feature title), FR-022 (feature title)
   Modified: FR-005 (what changed)
   Deprecated: FR-012 (reason)
   ```

### 4b. ATS 修订

若无 ATS 文档（`docs/plans/*-ats.md`），**跳过本步**。

**就地**更新既有 ATS 文档中与受影响需求相关的部分：

1. 阅读 `docs/plans/*-ats.md`
2. 对 **new** 需求：
   - 在映射表中新增行：需求 ID、场景、所需类别
   - 应用类别分配规则（所有 FR 为 FUNC+BNDRY；输入/鉴权加 +SEC；ui:true 加 +UI；带指标的 NFR 加 +PERF）
   - 更新覆盖率统计表（2.4 节）
   - 若有新 NFR：在 NFR Test Method Matrix（4 节）增行
   - 若有新的跨特性交互：在 Integration Scenarios（5 节）增行
3. 对 **modified** 需求：
   - **就地**更新对应映射表行（场景、类别）
   - 若阈值变化则调整 NFR 测试方法
   - 若数据流变化则更新集成场景
4. 对 **deprecated** 需求：
   - 在对应映射表行增加 `[DEPRECATED - Wave N]` 标记
   - **不要**删除该行（保留可追溯性）
   - 更新覆盖率统计（总额中排除已废弃行）
5. 若风险画像变化，更新 Risk-Driven Test Priority 小节
6. 征得用户对 ATS 变更的批准
7. Git commit：
   ```
   docs: update ATS for wave N — <brief scope>

   New: <req_ids added>
   Modified: <req_ids changed>
   Deprecated: <req_ids deprecated>
   ```
8. **ATS 复审检查**：若 ATS 变更影响超过 3 行映射表，或引入此前不存在的测试类别，询问用户是否需在继续前复审。若需要，向用户说明变更与理由以供批准。

### 5. UCD 修订（仅 UI 项目）

若项目无 UI 特性且新需求均不涉及 UI，**跳过本步**。

1. 阅读 `docs/plans/*-ucd.md`
2. 对新 UI 需求：
   - 为新 UI 组件增加 component prompts
   - 为新页面增加 page prompts
   - 若设计语言需扩展则更新 style tokens
3. 对修改的 UI 需求：
   - **就地**更新对应 component/page prompts
4. 对废弃的 UI 需求：
   - 在对应 prompts 上增加 `[DEPRECATED - Wave N]` 标记
5. 征得用户批准
6. Git commit：
   ```
   docs: update UCD style guide for wave N — <brief scope>
   ```

### 6. SRS 更新与特性拆解

更新 SRS 并拆解为特性：

**6a. 就地更新 SRS：**

1. 阅读 `docs/plans/*-srs.md`
2. 对 **new** 需求：
   - 追加到相应章节（Functional Requirements、NFR 等）
   - 保持 ID 连续
3. 对 **modified** 需求：
   - **就地**更新需求正文
   - 增加变更注释：`<!-- Wave N: Modified YYYY-MM-DD — <reason> -->`
4. 对 **deprecated** 需求：
   - 以 `[DEPRECATED - Wave N: <reason>]` 前缀标记
   - **不要**删除（保留可追溯性）
5. 若存在则更新 Traceability Matrix
6. Git commit：
   ```
   docs: update SRS for wave N — <brief scope>

   Added: FR-021, FR-022
   Modified: FR-005
   Deprecated: FR-012
   ```

**6b. 拆解为特性：**

1. **新特性**：追加到 `feature-list.json` 的 `features[]`：
   - `id`：max(既有 ID) + 1（持续递增）
   - `wave`：当前 wave 编号 N
   - `status`：`"failing"`
   - `srs_trace`：新 SRS 需求 ID 数组（例如 `["FR-021"]`）
   - `verification_steps`：可选 — 来自新验收标准（Given/When/Then）
   - `dependencies`：按需引用既有特性 ID
   - `ui`、`ui_entry`：按需设置

2. **被修改的特性**：对每个受影响的既有特性：
   - 将 `status` 设回 `"failing"`（需重新实现/验证）
   - 更新 `srs_trace` 以反映修订后的需求 ID
   - 若存在则可选更新 `verification_steps`
   - 可选将 `wave` 设为 N（标记修改发生时间）

3. **被废弃的特性**：对每个被废弃特性：
   - 设置 `deprecated: true`
   - 设置 `deprecated_reason: "<reason>"`
   - `status` 保持原样（不计入各类统计）

4. **替代特性**（废弃 + 新替代同时存在时）：
   - 新特性设置 `supersedes: <deprecated_feature_id>`

5. 更新根级 `waves[]` 数组：
   ```json
   {
     "id": N,
     "date": "YYYY-MM-DD",
     "description": "Brief description from increment-request.json"
   }
   ```

6. 若有新 CON/ASM 项则更新 `constraints[]`、`assumptions[]`

7. 若需要新配置则更新 `required_configs[]`

8. 校验：
   ```bash
   python scripts/validate_features.py feature-list.json
   ```

### 7. 更新辅助文件

按需更新支撑文件：

- **`long-task-guide.md`**：若引入新工具、框架或模式 → 重新生成或更新相关章节；用 `python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json` 再校验
- **`init.sh` / `init.ps1`**：若增加新依赖 → 更新引导脚本（保持幂等）
- **`.env.example`**：若新增 `env` 类型的 `required_configs` → 追加模板行（无论项目实际配置格式如何，此为环境变量参考模板）
- **`scripts/check_configs.py`**：若新增 `required_configs` → 重新生成或更新项目专属检查器以包含新配置

### 8. 收尾

1. 删除 `increment-request.json`（信号文件已消费）
2. 最终校验：
   ```bash
   python scripts/validate_features.py feature-list.json
   ```
3. 提交全部变更的 Git commit：
   ```
   feat: increment wave N — <scope from increment-request.json>

   New features: <ids>
   Modified features: <ids>
   Deprecated features: <ids>
   Total features: X (Y active, Z deprecated)
   ```
4. 更新 `task-progress.md`：
   - 更新 `## Current State` 标题：进度计数（X/Y 个活跃特性通过）、最近事件（Increment Wave M、日期）、下一步（首个 failing 特性）
   - 追加会话条目：
     ```
     ## Session N — Increment Wave M
     - **Date**: YYYY-MM-DD
     - **Phase**: Increment
     - **Scope**: <from increment-request.json>
     - **Changes**: Added N features, modified M features, deprecated K features
     - **Documents updated**: SRS, Design, [UCD]
     ```
5. 在 `RELEASE_NOTES.md` 的 `[Unreleased]` 小节中更新
6. 提交进度类文件的 Git commit：
   ```
   chore: update progress for increment wave N
   ```

路由器将检测到 `feature-list.json` 中的 failing 特性并自动路由到 Worker 阶段。

## 关键规则

- **先影响分析再改任何东西** — 未弄清波及范围前不得修改特性
- **每阶段需用户批准** — 影响矩阵、设计修订、SRS 更新均需明确批准
- **文档就地更新** — 不要另建增量专用文件；直接更新既有 SRS/Design/UCD；审计轨迹由 git 历史提供
- **ID 连续** — 新特性 ID 始终从 max(既有) 递增；永不复用已废弃 ID
- **Wave 追踪** — 每个新增/修改的特性使用当前 wave 编号
- **废弃特性不可恢复** — 一旦废弃不得取消废弃；应新建特性替代
- **一信号一增量** — 在完全处理完一份 increment-request.json 之前不接受下一份

## 危险信号

| 自我合理化 | 正确做法 |
|---|---|
| 「我直接把特性写进 JSON 就行」 | 使用本技能做可追踪、可审计的变更。 |
| 「现有测试仍通过，不必再验」 | 被修改的特性必须重置为 failing。 |
| 「设计以后再补」 | 设计修订在特性拆解**之前**完成。 |
| 「改动很小，跳过影响分析」 | 影响分析能发现隐藏依赖。 |
| 「我单独建一份 SRS」 | 就地更新主 SRS；历史由 git 记录。 |

## 集成

**由谁调用：** using-long-task（当存在 increment-request.json 时）  
**读取：** SRS、Design、ATS、UCD、feature-list.json、increment-request.json  
**写入：** SRS（就地）、Design（就地）、ATS（就地）、UCD（就地）、feature-list.json（追加/修改）  
**链接至：** long-task-work（增量完成后，由路由器检测到 failing 特性）
