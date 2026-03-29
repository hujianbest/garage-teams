---
name: long-task-ats
description: "当存在设计文档但不存在 ATS 文档与 feature-list.json 时使用 — 生成全局验收测试策略，将每条需求映射到带类别约束的验收场景"
---

# 验收测试策略（ATS）生成

以已批准 SRS、Design 及 UCD（若适用）为输入。产出全局验收测试策略文档，将每条需求映射到带**必选测试类别**的验收场景 — 约束下游 feature-st（经 srs_trace 推导测试用例）。

**开始时宣告：**「我正在使用 long-task-ats 技能生成验收测试策略（ATS）。」

<HARD-GATE>
在 ATS 文档获批之前，不得调用任何实现技能、编写任何代码、搭建任何项目、运行 init_project.py 或采取任何实现动作。此规则适用于**所有**项目，无论其看似多简单。
</HARD-GATE>

## 为何需要 ATS

若无全局验收测试策略，各特性 ST 用例易出现：
- 类别失衡（FUNC/BNDRY 过重，SEC/PERF/UI 近乎为零）
- NFR 测试方法在 feature-st 阶段临时决定
- 跨特性集成场景在 ST 过晚才暴露
- 完全缺失基于风险的测试优先级

ATS 将这些决策前置，使 Init 与 feature-st 有具体、可审计的约束。

## 规模指南

| 项目规模 | 特性数 | ATS 深度 |
|---|---|---|
| Tiny | 1–5 | **跳过独立 ATS** — 在设计文档测试策略小节（第 7 节）内嵌简化映射表；路由检测无 `*-ats.md` 且 ≤5 特性 → 自动跳过至 Init |
| Small | 5–15 | 轻量独立 ATS — 仅第 1–3 节（范围、映射表、类别策略）；跳过第 4–6 节 |
| Medium | 15–50 | 完整 ATS 文档 — 全部 6 节 |
| Large | 50–200+ | 完整 ATS + 按子系统的详细集成矩阵 + 风险热力图 |

**Tiny 项目自动跳过规则**：若设计文档已存在且 SRS 中功能需求（FR-xxx）≤ 5 条，本技能将 ATS 映射表嵌入设计文档测试策略小节，并创建极简 `docs/plans/*-ats.md` 存根，仅引用该小节。路由随后检测到 ATS 存根并继续 Init。

## 检查清单

你必须为每一步创建 TodoWrite 任务并按顺序完成：

### 1. 阅读输入文档

1. 从 `docs/plans/*-srs.md` 读取已批准 SRS
2. 从 `docs/plans/*-design.md` 读取已批准设计文档
3. 从 `docs/plans/*-ucd.md` 读取已批准 UCD（若存在 — 仅 UI 项目）
4. 检查自定义 ATS 模板：
   - 若用户指定模板路径 → 读取并校验
   - 否则 → 使用 `docs/templates/ats-template.md` 默认模板
5. 检查自定义 ATS 示例：
   - 若用户指定示例路径 → 读取该文件 — 适配风格、语言与详略
6. 检查自定义 ATS 评审模板：
   - 若用户指定评审模板路径 → 读取供第 8 步使用
   - 否则 → 使用 `docs/templates/ats-review-template.md` 默认评审模板

### 2. 提取全部需求

从 SRS 提取完整列表：
- **FR-xxx**：功能需求 — 含验收标准（Given/When/Then）
- **NFR-xxx**：非功能需求 — 含可度量阈值
- **IFR-xxx**：接口需求 — 含协议与数据格式
- **CON-xxx**：约束 — 硬限制
- **ASM-xxx**：假设 — 隐含前提

统计 FR-xxx 数量。若 ≤ 5，应用上文 **Tiny 项目自动跳过** 规则。

### 3. 生成需求 → 验收场景映射

对每条 FR/NFR/IFR，生成一条或多条验收场景，附：

```markdown
| Req ID | 需求摘要 | 验收场景 | 必须类别 | 优先级 | 备注 |
|--------|---------|---------|---------|--------|------|
| FR-001 | 用户登录 | 正常登录/错误密码/账户锁定/会话过期 | FUNC,BNDRY,SEC | Critical | 处理用户输入→SEC必选 |
| NFR-001 | 响应时间<200ms | P95延迟/并发负载/降级/冷启动 | PERF | High | 阈值: P95<200ms @100并发 |
| FR-010 | 搜索结果页 | 搜索/空结果/分页/排序/筛选 | FUNC,BNDRY,UI | High | ui:true→UI必选 |
```

**类别分配规则：**

| 条件 | 必须类别 |
|------|---------|
| 所有 FR | FUNC + BNDRY（至少） |
| 处理用户输入/认证/授权/外部数据 | + SEC |
| 对应 `ui: true` 的 feature | + UI |
| 关联 NFR-xxx 且有性能指标 | + PERF |

### 4. 定义测试类别策略

对每个测试类别说明策略：

- **FUNC**：每条 FR 至少一条 happy path + 一条 error path 场景
- **BNDRY**：每条 FR 的边界值分析与等价类划分要求
- **SEC**：输入校验（SQL 注入、XSS、路径穿越）、认证绕过、授权提升、数据泄露
- **PERF**：NFR 指标阈值 + 负载场景 + 工具说明 + 通过准则
- **UI**：Chrome DevTools MCP 交互链 — navigate → interact → verify → 三层检测

### 5. NFR 测试方法矩阵

对每条带可度量阈值的 NFR-xxx：

```markdown
| NFR ID | 测试方法 | 工具 | 通过标准 | 负载参数 | 关联 feature |
|--------|---------|------|---------|---------|-------------|
| NFR-001 | Load test | k6/locust/ab | P95 < 200ms | 100 concurrent, 60s ramp | Feature 15, 16 |
| NFR-002 | Memory profiling | tracemalloc/heapdump | RSS < 512MB | 10K records | Feature 8 |
```

### 6. 跨特性集成场景

识别跨多条特性的关键数据流路径：

```markdown
| 场景 ID | 场景描述 | 涉及 Features | 数据流路径 | 验证要点 | ST 阶段覆盖 |
|---------|---------|--------------|-----------|---------|------------|
| INT-001 | 用户注册→登录→首次操作 | F1, F2, F5 | POST /register → POST /login → GET /dashboard | 会话传递、数据一致性 | System ST |
```

### 7. 风险驱动测试优先级

按需求评估风险并分配测试深度：

```markdown
| 风险区域 | 风险级别 | 影响范围 | 测试深度 | 依据 |
|---------|---------|---------|---------|------|
| 用户认证 | High | 全系统 | 深度 (SEC+FUNC+BNDRY) | 安全边界 |
| 数据导入 | Medium | Feature 3-5 | 标准 (FUNC+BNDRY) | 数据完整性 |
```

### 8. 按小节请用户批准

与设计技能相同模式，逐节向用户展示并请批准：

1. 需求→场景映射表（第 3 步）
2. 测试类别策略（第 4 步）
3. NFR 测试方法矩阵（第 5 步）— 若无带指标的 NFR 则跳过
4. 跨特性集成场景（第 6 步）
5. 风险驱动优先级（第 7 步）

每节展示后等待反馈，修改后再继续。

**Small 项目**（5–15 特性）：合并为 2 次批准：(a) 映射表 + 类别，(b) 其余全部。

### 9. 子代理评审

派发 ATS 评审子代理做独立质量评审：

```
Agent(
  subagent_type="general-purpose",
  prompt="""
  You are an independent ATS reviewer.
  Read the reviewer prompt at: agents/ats-reviewer.md
  Read the review template at: {review_template_path}

  ## Input Documents
  - ATS document (draft): {ats_content}
  - SRS document: {srs_path} — read it
  - Design document: {design_path} — read it
  - UCD document (if applicable): {ucd_path} — read it

  ## Task
  Execute all review dimensions defined in the review template.
  Output a structured review report.
  Do NOT suggest improvements beyond defect identification.
  Do NOT read any implementation code — this is a requirements-level review.
  """
)
```

**隔离保证：**
- 子代理**仅**读取 ATS + SRS + Design + UCD + 评审模板
- 子代理**不**读取实现代码或测试代码
- 子代理**不**修改任何文件 — 仅返回结构化报告
- 主技能处理报告并决定修复

### 10. 处理评审报告

解析子代理评审报告：

1. **0 个 Major 缺陷** → PASS → 进入第 11 步
2. **存在 Major 缺陷** → 按缺陷描述修复 ATS → 重跑第 9 步（最多 2 轮评审）
3. **第三轮仍 FAIL** → 通过 `AskUserQuestion` 向用户展示完整报告：
   - 展示全部剩余 Major 缺陷
   - 选项：手工修复 / 接受已知缺口 / 终止
   - 若用户接受缺口：在 ATS 页脚记录缺口

### 11. 保存 ATS 文档

1. 将已批准 ATS 保存至 `docs/plans/YYYY-MM-DD-<topic>-ats.md`
2. 将最终评审报告追加为附录小节
3. Git 提交：
   ```
   docs: add acceptance test strategy (ATS)

   Maps N requirements to acceptance scenarios
   Categories: FUNC, BNDRY, SEC, PERF, UI
   Reviewed: [PASS / CONDITIONAL PASS with N gaps]
   ```

### 12. 转入 Initializer

ATS 文档保存并提交后：

1. 总结 Initializer 所需关键输入：
   - **来自 SRS**：需求、验收标准 → 特性
   - **来自 Design**：技术栈、架构 → 项目骨架
   - **来自 ATS**：类别约束 → feature-st 用例类别要求（经 srs_trace）
2. **必选子技能：** 调用 `long-task:long-task-init` 搭建项目

## 与设计文档测试策略的边界

**设计文档**（第 7 节，Testing Strategy）描述 *方法*：
- 将使用哪些测试类型（单元、集成、E2E）
- 哪些工具与框架（pytest、k6、Chrome DevTools MCP）
- 覆盖率目标（行 90%、分支 80%、变异 80%）

**ATS 文档**描述 *详细映射*：
- 哪条具体需求对应哪些具体测试类别
- 带确切阈值与负载参数的 NFR 测试方法
- 跨特性集成场景
- 风险驱动的测试深度

设计文档测试策略小节在 ATS 存在后**应**引用 ATS：
```markdown
See `docs/plans/YYYY-MM-DD-<topic>-ats.md` for detailed requirement-to-test-category mapping.
```

## 关键规则

- **需求驱动**：映射表每行追溯到具体 SRS 需求 ID
- **无孤儿需求**：每条 FR/NFR/IFR 必须出现在映射表
- **类别分配可审计**：每个必选类别有文档化理由
- **评审强制**：保存前须运行 ATS 评审子代理 — 不可跳过
- **规模适用**：Tiny（≤5 FR）跳过独立 ATS；见规模指南
- **批准后不可变**：变更 ATS 须通过 `long-task-increment` 技能（ATS 修订步骤）

## 红旗

| 自我合理化 | 正确应对 |
|---|---|
| 「SRS 已有验收标准，ATS 多余」 | SRS 是业务准则；ATS 将其映射到测试类别 |
| 「feature-st 再定测试类别」 | 临时分配易导致 SEC/PERF 缺口 |
| 「项目太小不需要 ATS」 | 查规模指南 — Tiny 自动跳过；Small 用轻量 ATS |
| 「NFR 测试到 ST 再定」 | NFR 测试方法须事先规定工具与阈值 |
| 「评审小题大做」 | 独立评审能发现作者遗漏的覆盖缺口 |

## 集成

**由…调用：** using-long-task（存在设计、无 ATS、无 feature-list.json）或 long-task-design（第 6 步）  
**需要：** `docs/plans/*-srs.md` 已批准 SRS；`docs/plans/*-design.md` 已批准 Design；可选 `docs/plans/*-ucd.md` 已批准 UCD  
**链接至：** long-task-init（ATS 批准后）  
**产出：** `docs/plans/YYYY-MM-DD-<topic>-ats.md`  
**下游消费者：**  
- `long-task-init` — 读取 ATS 按类别分配设置 `ui` 标志  
- `long-task-feature-st` — 读取 ATS 强制执行类别要求（经 srs_trace 查找）  
- `long-task-st` — 以 ATS 为 RTM 验证基线  
- `long-task-increment` — 需求变更时原地更新 ATS
