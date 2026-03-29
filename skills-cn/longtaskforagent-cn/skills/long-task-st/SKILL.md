---
name: long-task-st
description: "当 feature-list.json 中全部特性均为 passing 时使用 — 发布前执行综合系统测试，对齐 IEEE 829 与 ISTQB 最佳实践"
---

# 系统测试（ST）— 发布前跨特性与全系统验证

全部特性实现完毕且均为 passing 后，执行跨特性与全系统测试。各特性的 ST 用例（功能、边界、UI、安全）已在各 Worker 周期经 `long-task-feature-st` 执行。本阶段聚焦**单特性测试无法覆盖**的内容：跨特性交互、多特性 E2E 工作流、全系统 NFR 验证、兼容性与探索性测试。

**开始时宣告：**「我正在使用 long-task-st skill。全部特性已通过 — 开始进行跨特性系统测试。」

**核心原则：** 单特性 ST 证明各特性满足需求；系统测试证明**整体**在特性边界上协同工作。

<HARD-GATE>
不得跳过任何适用测试类别。「Go」判定须对**本项目适用的每一类**都有证据。「大概没问题」不是证据。
</HARD-GATE>

## 检查清单

**必须**为每一步创建 TodoWrite 任务并按顺序完成：

### 1. ST 就绪门禁

```bash
python scripts/check_st_readiness.py feature-list.json
```

- 全部特性 `"status": "passing"` — 若有 failing，改调 `long-task:long-task-work`
- SRS 存在（`docs/plans/*-srs.md`）；Design 存在（`docs/plans/*-design.md`）
- 若项目有配置：按 `long-task-guide.md` 激活环境；若使用文件型配置，运行检查前须已加载
- **启动 ST 运行时服务**：按 `env-guide.md` 启动（纯 CLI/库可跳过）
  - 读 `env-guide.md` — 使用「Start All Services」；每条命令重定向输出：
    ```bash
    [start command] > /tmp/svc-<slug>-start.log 2>&1 &
    sleep 3
    head -30 /tmp/svc-<slug>-start.log
    ```
  - 从前 30 行提取 PID 与端口
  - 执行 `env-guide.md` 中「Verify Services Running」— 须通过后方可继续
  - 若启动失败：查日志、诊断根因；尝试修正命令（端口冲突、环境变量、缺依赖）；确认可用命令后**更新 `env-guide.md`**（Services 表 + Start）；若修复 >2 步，抽成 `scripts/svc-<slug>-start.sh` 并在 env-guide.md 引用；再通过 `AskUserQuestion` 告知用户
  - **记录**：PID 与端口写入 `task-progress.md` — 第 11 步清理必需
- 读 `feature-list.json` — 注意 `tech_stack`、`quality_gates`、`constraints[]`、`assumptions[]`
- 读 SRS — 提取全部 FR-xxx、NFR-xxx、IFR-xxx、CON-xxx；读 Stakeholders、User Personas、Glossary
- 读 Design — 提取架构、API 设计、测试策略（§9）、第三方依赖（§8）
- 若有 UI 特性：读 UCD（`docs/plans/*-ucd.md`）
- 读 `task-progress.md` — 会话历史

### 2. ST 计划

创建 `docs/plans/YYYY-MM-DD-st-plan.md`，包含：

#### 2a. 测试范围

| 类别 | 适用条件 | 可跳过条件 |
|----------|-------------|-----------|
| Regression | 总是适用 | 从不跳过 |
| Integration | 存在 2 个以上共享数据/状态/API 的特性 | 单个孤立特性 |
| E2E Scenarios | SRS 含多步骤用户工作流 | 纯库/工具类项目 |
| Performance | SRS 含响应时间 / 吞吐目标类 NFR-xxx | 无性能类 NFR |
| Security | 存在安全 NFR，或项目处理用户输入 / 鉴权 / 外部数据 | 孤立离线工具 |
| Compatibility | SRS 指定平台 / 浏览器 / 运行时目标 | 单平台 CLI 工具 |
| Exploratory | 总是适用 | 从不跳过 |

#### 2b. 需求可追溯矩阵（RTM）

将**每条** SRS 需求映射到 ST 测试方法。引用 Worker 第 9 步产出的各特性测试用例文档：

```markdown
| Req ID | Requirement | Feature ST Status | System ST Category | ATS Categories | Test Approach | Priority |
|--------|-------------|-------------------|--------------------|----------------|---------------|----------|
| FR-001 | ... | docs/test-cases/feature-1-xxx.md (PASS) | E2E | FUNC,BNDRY,SEC | Scenario: ... | High |
| NFR-001 | ... | docs/test-cases/feature-5-xxx.md (PASS) | Performance | PERF | Load test: ... | Critical |
| IFR-001 | ... | N/A (cross-feature) | Integration | FUNC,BNDRY | Contract test: ... | High |
```

每条 FR-xxx、NFR-xxx、IFR-xxx 须出现在 RTM 中。无测试方法的需求 = **缺口**。

**ATS 合规门禁**（若存在 ATS 文档）：
```bash
python scripts/check_ats_coverage.py docs/plans/*-ats.md --feature-list feature-list.json --strict
```
须退出 0。任一 ATS 类别缺口 = 须在进入下步前处理的发现项。

#### 2c. 进入 / 退出准则

**进入**（须**全部**成立）：全部特性 passing、环境已就绪、所需配置齐全。

**退出**（「Go」须**全部**成立）：回归/集成/E2E 均通过、NFR 阈值均有**实测**证据且达标、无未关闭 Critical/Major 缺陷、RTM 需求覆盖 100%、**若存在 ATS：`check_ats_coverage.py --strict` 退出 0**。

#### 2d. 基于风险的优先级

1. 关键路径 — 核心用户工作流、最高业务影响
2. 集成边界 — 跨特性数据流、API 契约
3. NFR 阈值 — 性能、安全（技术风险最高）
4. 边界场景 — 边界条件、错误恢复
5. 兼容性 — 平台/浏览器差异

### 3. 回归测试

1. 按 `long-task-guide.md` 运行**完整**项目测试套件
2. 确认**全部**通过 — 零失败、零错误
3. 确认行/分支覆盖率满足**项目级**阈值
4. 检查新增告警、弃用提示、依赖冲突
5. 任一失败 → **停止** — 属回归。须先诊断再继续。

**记录：** 总用例数、通过/失败、行/分支覆盖率相对阈值。

### 3b. 全量变异回归

运行**全代码库**变异测试。Worker 周期中按特性变异在活跃特性数 > `mutation_full_threshold` 时可能仅用特性范围测试；本步用**完整**套件验证全项目变异分。

1. 从 `long-task-guide.md` 取得 `mutation_full` 命令
2. 运行全量变异（全部源文件、全部测试）
3. 确认：变异分 >= `feature-list.json` 中 `quality_gates.mutation_score_min`
4. 若有幸存变异体：
   - 分析：等价变异（文档化 + 跳过）vs 真实缺口（补测试 → Major 级缺陷）
   - 若低于阈值 → 视为回归缺陷（Major）
5. 记录：变异分、杀死/幸存/总数、所用命令

详见 `references/st-recipes.md` 中「Full Mutation Regression」各工具命令与结果解读。

**记录：** 变异分相对阈值、幸存数量、工具输出摘要。

### 4. 集成测试

测跨特性交互。读 `references/st-recipes.md` 了解语言相关模式与真实/契约测试分类。

**术语**（详见 st-recipes.md §1）：
- **契约测试** = 基于 mock，校验调用签名 — 仅作补充，**不足**以替代集成验证
- **集成测试** = 真实服务，校验真实数据流 — **每个边界**所必需

<HARD-GATE>
每个**内部**跨特性边界**必须**至少有一条**真实**集成测试（真实 DB、HTTP、文件系统）。契约测试（mock）**不满足**本门禁。

对外部第三方边界：先通过 `AskUserQuestion` 请用户提供测试凭证或沙箱。**仅当**用户确认无法提供凭证时，方可仅用契约测试 — 须在 ST 计划中将用户确认记入 Mock Authorization 列。
</HARD-GATE>

对每对共享数据、状态或 API 边界的特性：
- **数据流**：特性 A 产出 → 特性 B 消费 → 端到端校验数据完整性；共享 DB/状态一致
- **API 契约**：模块间内部调用 — 校验请求/响应 schema；错误传播；版本兼容
- **依赖链**：遍历 `feature-list.json` 中 `dependencies[]`；按依赖顺序验证；测每条依赖边

**分类表**（纳入 ST 计划）：

| Boundary | Features | Type | Real Tests | Contract Tests | Mock Authorization | Status |
|----------|----------|------|-----------|----------------|-------------------|--------|
| shared DB | F1 → F3 | Internal | 2 | 1 | N/A | PASS |
| REST API | F2 → F4 | Internal | 1 | 0 | N/A | PASS |
| GitHub API | F5 → ext | External | 1 | 0 | N/A (user provided token) | PASS |
| Stripe API | F7 → ext | External | 0 | 2 | User confirmed no sandbox | PASS |

**每个内部边界最低要求：**
- ≥1 条真实测试，经真实共享资源写入/读出
- 若真实服务无法启动：边界为 **BLOCKED**（非跳过）— 经 env-guide.md 诊断

**外部边界协议：**
1. 用 `AskUserQuestion` 索取测试凭证/沙箱
2. 用户提供 → 编写真实集成测试（优先）
3. 用户确认无法提供 → 使用契约测试；在 Mock Authorization 列记录
4. 未经用户确认不得默认 mock 可接受

将集成测试写在 `tests/integration/` 或 `tests/st/`。为每条测试打标签：
```python
# Integration: Feature A → Feature B (shared DB) [Real]
def test_feature_a_data_consumed_by_feature_b():
    ...

# Contract: Feature C → External API [Contract]
def test_external_api_response_shape():
    ...
```

按边界运行并记录结果。

### 4b. 全链路冒烟测试

在 E2E 场景测试前，至少验证一条贯穿全系统的完整数据流路径。可发现单边界测试遗漏的集成问题。

<HARD-GATE>
至少**一条**冒烟测试须走真实端到端数据路径（输入 → 处理 → 存储 → 读取 → 输出），且**仅**使用真实服务，**无** mock。
</HARD-GATE>

1. 识别**关键路径** — 系统中最重要的一条数据流（如「创建实体 → 存储 → 查询 → 返回」）
2. 编写一条冒烟测试：
   - 从外部输入开始（API、CLI、UI）
   - 经过全部中间处理
   - 写入真实存储（若适用）
   - 读出并校验持久化结果
   - **仅**真实服务 — 无 mock
3. 对第 1 步已启动的服务运行冒烟测试
4. 若失败 → **Critical** 级缺陷 — E2E 前须先诊断

**规模：**
| 项目规模 | 冒烟测试数 |
|---|---|
| Tiny (1-5 features) | 1 条关键路径 |
| Small (5-15) | 1-2 条关键路径 |
| Medium (15-50) | 2-3 条关键路径 |
| Large (50+) | 3-5 条覆盖主要子系统的关键路径 |

**记录：** 冒烟描述、所用真实服务、通过/失败、执行证据。

### 5. 跨特性 E2E 场景测试

测**跨多个特性**的完整用户工作流（来自 SRS 验收标准）。单特性场景已由单特性 ST 覆盖。

对 SRS Stakeholders 中每个用户画像：
- 提取**跨越特性边界**的主工作流
- 构建跨多特性的 E2E 场景（主路径 + 错误恢复）
- 每场景：初始状态 → 执行工作流 → 校验中间与最终状态 → 清理

每场景：设初始状态、逐步执行、校验中间与最终结果、清理。

**UI E2E**（仅当存在 `"ui": true` 特性）：使用 Chrome DevTools MCP — `navigate_page`、`take_snapshot`、`click`/`fill`/`press_key`、`take_screenshot`、`list_console_messages`、`list_network_requests`。

E2E 测试写在 `tests/e2e/` 或 `tests/st/`。运行并记录结果。

### 6. 全系统 NFR 验证

单特性 NFR 已在特性级 ST 处理。本步侧重**全系统聚合** NFR 测量。对 SRS 中每条 NFR-xxx，用**实测数据**验证 — 非估算。

- **性能**：在预期负载下测 p50/p95/p99；吞吐；内存/CPU/磁盘 I/O。工具见 `references/st-recipes.md`。记录：实测值 vs SRS 阈值。
- **安全**：输入校验审计（SQL、XSS、命令注入、路径穿越）；认证/会话/越权；依赖漏洞扫描（npm audit、pip-audit 等）；OWASP Top 10；代码/日志中的密钥。记录：每项检查 PASS/FAIL 与证据。
- **可扩展性**（若 SRS 有负载目标）：在 1x、2x、5x 预期负载下压测；测劣化曲线；定位瓶颈。
- **可靠性**：错误处理信息是否可理解；依赖不可用时是否优雅降级；错误条件下是否损坏数据。

### 7. 兼容性测试

若 SRS 未规定平台/浏览器/运行时目标则跳过。

- **跨浏览器**（仅 UI）：在目标浏览器跑 E2E；截图比对视觉一致性；检查浏览器特有控制台错误
- **跨平台**：在各目标 OS 构建/安装/跑全量测试；校验路径、换行、权限等平台行为
- **运行时版本**：对各目标运行时版本跑全量测试；校验无版本相关 API 问题

记录：各平台/浏览器 PASS/FAIL 矩阵。

### 8. 探索性测试

基于 Charter、限时会话，发现脚本测不到的问题。

每个主要特性域一个 Charter：
```
Charter: Explore [feature area]
         with [technique: stress/edge/abuse/workflow variation]
         to discover [bugs/usability issues/undocumented behavior]
```

每个 Charter：限时 15–30 分钟；凭直觉尝试异常输入、非常规顺序、快速操作；实时记录观察（Bug / Question / Note 附严重程度）。

全部 Charter 后：汇总发现；与 RTM 对照查需求缺口；新缺陷进入分诊队列。

### 9. 缺陷分诊

若第 3–8 步**发现任何**缺陷：

| 严重程度 | 定义 | 处理动作 |
|----------|-----------|--------|
| **Critical** | 系统崩溃、数据丢失、安全漏洞 | 阻塞发布——立即修复 |
| **Major** | 核心流程损坏、NFR 阈值未达标 | 阻塞发布——发布前修复 |
| **Minor** | 非核心功能受影响，但存在绕行方案 | 记录——立即修复或延期（与用户决定） |
| **Cosmetic** | 视觉/文案问题，无功能影响 | 记录——延期到下个版本 |

**逃逸分析** — 每条缺陷标注本应在何处被拦截：

| Escaped From | 含义 | 系统性动作 |
|---|---|---|
| Unit | 本应在 TDD 阶段被拦截 | 补充单元测试，并复查同类覆盖缺口 |
| Feature-ST | 单特性验收测试存在缺口 | 通过 increment skill 补加测试用例 |
| Mock-Leaked | mock 测试通过，但真实集成失败 | 用真实集成测试替换 mock 测试 |
| Integration | 跨特性边界未被测试 | 为该边界补加集成测试 |
| Spec | 需求不清晰或缺失 | 通过 increment skill 澄清 SRS |

缺陷表须含「Escaped From」列：

| # | 严重程度 | Escaped From | 类别 | 描述 | 状态 | 修复引用 |
|---|----------|-------------|----------|-------------|--------|---------|

**修复循环**（存在 Critical/Major 时）：
1. 在 `feature-list.json` 将受影响特性标为 `"status": "failing"`；在 `task-progress.md` 记录
2. 调用 `long-task:long-task-work` 修复
3. 修复后：重跑受影响的 ST 类别（非完整 ST）
4. 回到分诊 — 直至无 Critical/Major

Minor/Cosmetic 延期：在 ST 报告中记录严重程度、描述、变通办法。

### 10. ST 报告

撰写前确认：每条 SRS 需求在 RTM 中；每条 NFR 有达标实测值；每个适用类别有结果；全部缺陷已分类。

生成 `docs/plans/YYYY-MM-DD-st-report.md`，含：
1. **执行摘要（Executive Summary）** — 1–3 句：总体质量与发布建议
2. **需求追溯矩阵（Requirements Traceability Matrix）** — 完整 RTM（含 Feature ST 状态、System ST 类别、ATS 类别、结果、证据）；覆盖计数（X/Y，Z%）；缺口列表；ATS 合规检查结果（`check_ats_coverage.py --strict` 输出）
3. **测试执行汇总（Test Execution Summary）** — 表：类别、运行数、通过、失败、跳过、备注（对应 2a 每行一行）；末行 **Real Test Cases** — 汇总各特性 ST 文档（`docs/test-cases/feature-*.md`）中 Real Test Case Execution Summary 的 `Real` 计数（total / passed / failed）
4. **缺陷汇总（Defect Summary）** — 表：严重程度、**escaped from**、类别、描述、状态（已修/延期）、修复引用；合计；未关闭 Critical/Major 数（Go 须为 0）；若 ≥2 条缺陷同源「Escaped From」，在 Risk Assessment 标为系统性缺口
5. **质量指标（Quality Metrics）** — 行/分支覆盖率 vs 阈值、**全量变异分** vs 阈值（来自 3b）、总用例数；真实用例：total / passed / failed（自全部 `docs/test-cases/feature-*.md` 汇总）
6. **风险评估（Risk Assessment）** — 残余风险：可能性、影响、缓解
7. **建议（Recommendations）** — 发布后监控、已知限制、改进建议

### 11. 持久化

- Git 提交 ST 产物（`*-st-plan.md`、`*-st-report.md`、测试文件）
- 校验：`python scripts/validate_features.py feature-list.json`
- **清理（强制）**：停止第 1 步启动的服务
  - 读 `env-guide.md`「Stop All Services」— 优先按 PID（`task-progress.md`）终止，或按端口兜底
  - 若 stop 失败：试端口兜底；确认可用命令后**更新 `env-guide.md`** Stop；若 >2 步，抽成 `scripts/svc-<slug>-stop.sh` 并在 env-guide.md 引用
  - 执行「Verify Services Stopped」— 端口须无响应
  - **记录清理结果**于 `task-progress.md`

### 12.5 回顾报告（条件执行）

```bash
python scripts/check_retrospective_readiness.py
```

若退出 0（有记录）**且** `feature-list.json` 中 `retro_authorized` 为 `true`：
- 调用 `long-task:long-task-retrospective`
- 完成后再进入 Verdict

若退出 1（无记录）或 `retro_authorized` 缺失/false → 跳过，直接进入 Verdict。

### 12. 判定

通过 `AskUserQuestion` 向用户展示 ST 报告摘要与 Go/No-Go 建议：
- **Go**：退出准则全满足、无未关闭 Critical/Major、RTM 100% 覆盖
- **Conditional-Go**：Minor/Cosmetic 已记录延期、关键路径已验证
- **No-Go**：存在 Critical/Major、NFR 未达标或 RTM 有缺口

### 13. Finalize（Go / Conditional-Go 时）

若判定为 Go 或 Conditional-Go：
- 调用 `long-task:long-task-finalize`
- 完成后再结束会话

若 No-Go → 跳过（回到 Worker 修复；最终 Go 后再 Finalize）。

## 按项目规模伸缩 ST

| 项目规模 | 特性数 | ST 深度 |
|---|---|---|
| Tiny (1-5) | 1-5 features | Regression + lightweight integration + 1 smoke test + 2-3 E2E scenarios + 1-2 exploratory charters |
| Small (5-15) | 5-15 features | Full regression + integration per shared boundary + 1-2 smoke tests + E2E per persona + NFR spot-checks + 3-5 charters |
| Medium (15-50) | 15-50 features | Full regression + systematic integration + 2-3 smoke tests + comprehensive E2E + full NFR + compatibility matrix + 5-10 charters |
| Large (50+) | 50+ features | Full regression + integration test suite + 3-5 smoke tests + E2E automation + full NFR load testing + full compatibility + security audit + 10+ charters |

## 关键规则

- **先过就绪门禁** — failing 特性不得开 ST
- **判定须基于证据** — 每个 PASS 须有实测证据；「看起来还行」不算
- **RTM 须完整** — 每条 SRS 需求须在 RTM；缺口即发现项
- **NFR 阈值为硬门禁** — 实测须达到 SRS 阈值，非「差不多」
- **严重程度不可协商** — Critical/Major 阻塞发布
- **ST 中发现的缺陷均须修复** — 前端、后端、集成不限；无「不是我代码」豁免
- **修复后须复测** — 勿假设修复有效；重跑受影响类别
- **Real 用例须全部通过** — ST 报告中 Real Test Cases 行任一 `Real` 失败均为未关闭缺陷，阻塞 Go
- **探索性测试强制** — 脚本无法覆盖一切
- **先写 ST 报告再判定** — 先文档化再决策
- **ST 期间不增新特性** — 测的是当前集成系统现状
- **ATS 类别有约束力** — 若存在 ATS，`check_ats_coverage.py --strict` 须 0；必选类别须有覆盖
- **每边界须真实集成测试** — 内部边界 ≥1 真实测试；外部边界 mock 前须用户确认
- **全链路冒烟强制** — E2E 场景前须至少验证一条真实端到端数据路径
- **须做缺陷逃逸分析** — 每条缺陷按「Escaped From」分类，识别系统性测试缺口

## 集成

**调用方：** `using-long-task`（存在 feature-list.json 且全部 passing），或 `long-task-work`（第 12 步且无剩余 failing 特性）  
**读取：** `feature-list.json`、`docs/plans/*-srs.md`、`*-design.md`、`*-ucd.md`（若有 UI）、`docs/test-cases/feature-*.md`（来自 `long-task-feature-st` 的单特性 ST）、`task-progress.md`、项目配置文件（若适用）  
**可调用：** `long-task:long-task-work`（发现 Critical/Major → 修复循环）、`long-task:long-task-finalize`（Go/Conditional-Go 之后）  
**产出：** `docs/plans/YYYY-MM-DD-st-plan.md`、`docs/plans/YYYY-MM-DD-st-report.md`  
**按需读取（Read 工具，非 Skill 工具）：** `references/st-recipes.md`
