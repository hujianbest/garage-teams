---
name: long-task-hotfix
description: "当存在 bugfix-request.json 时使用；校验、复现、根因分析，将用户报告的缺陷以 category=bugfix 特性入队，再链接到 Worker 进行 TDD 修复"
---

<EXTREMELY-IMPORTANT>
你正在使用 long-task-hotfix 技能。本技能处理用户在手工测试中发现的缺陷。

你的职责仅限：校验 → 复现 → 根因 → 入队 → 链接到 Worker。  
实际修复（TDD、质量门禁、ST、评审）由 Worker 流水线负责 — **不要在本技能中实现修复**。
</EXTREMELY-IMPORTANT>

## 步骤 1：声明

输出：「我正在使用 long-task-hotfix 技能。正在处理 bugfix-request.json。」

使用 TodoWrite 跟踪 8 个步骤的进度。

---

## 步骤 2：校验信号文件

执行：
```bash
python scripts/validate_bugfix_request.py bugfix-request.json
```

若校验失败：
- 清晰打印错误信息
- 使用 `AskUserQuestion` 请用户修正文件
- 用户回复后重新校验
- 校验通过前**不得**继续

---

## 步骤 3：摸底

按顺序阅读以下文件：
1. `bugfix-request.json` — 理解标题、描述、severity、feature_id、复现步骤
2. `feature-list.json` — 定位关联特性（若 `feature_id` 非空），阅读 `tech_stack`、`quality_gates`；确定下一个可用特性 `id`
3. `long-task-guide.md` — 环境激活命令
4. `env-guide.md`（若存在）— 服务启停命令
5. `task-progress.md` 中 `## Current State` — 近期会话历史
6. `git log --oneline -10` — 近期提交上下文

若 `feature_id` 非空：从 `feature-list.json` 读取关联特性条目以了解上下文（其 `ui` 字段、既有 `srs_trace`、`st_case_path`）。

---

## 步骤 4：复现

**目标**：在开展任何分析之前确认缺陷可复现。

1. 按 `long-task-guide.md` 激活环境
2. 若需要服务（由 `env-guide.md` 或 `long-task-guide.md` 判断）：使用 `env-guide.md` 中的 Start 命令启动；捕获启动输出的前 30 行；将 PID 记入 `task-progress.md`
3. 严格按 `bugfix-request.json` 中的 `reproduction_steps` 操作
4. 运行既有测试套件；记录当前失败的用例
5. 记录：实际执行的命令、实际输出、确认缺陷是否出现

**硬门禁 — 无法复现：**  
若无法复现缺陷：
- 在 `task-progress.md` 中记录尝试过程
- 停止本步骤中启动的所有服务（使用 `env-guide.md` 中的 Stop 命令）
- **不要**删除 `bugfix-request.json`
- 使用 `AskUserQuestion` 请求澄清（更细步骤、特定环境、样例数据等）
- **在此暂停直至复现得到确认**

---

## 步骤 5：根因分析

执行 `skills/long-task-work/references/systematic-debugging.md` 中的**四阶段系统化调试流程**：

**阶段 1 — 根因调查**：收集完整错误证据、找到最小复现、检查近期 git 变更、从入口到失败点追踪数据流。

**阶段 2 — 模式分析**：查找相似可用代码路径、对比上下文、检查依赖版本与配置值。

**阶段 3 — 假设与验证**：形成**一条**可检验的具体假设；做**一处**最小诊断性变更以证实或证伪；若错误则回到阶段 1。

**阶段 4 — 根因确认**：得到**一条**已确认的根因陈述。

**必填输出**：`"Root cause: [one-sentence statement]"`

**铁律**：根因确认前**不得**写入特性条目。若经过 3 次阶段 3 迭代仍无法确认根因，使用 `AskUserQuestion` 向用户索取更多上下文。

---

## 步骤 6：作为 bugfix 特性入队

向 `feature-list.json` 新增一条特性。确定下一个可用 `id`（max(既有 id) + 1）。

**新特性对象：**
```json
{
  "id": <next available>,
  "wave": <current max wave id>,
  "category": "bugfix",
  "title": "Fix: <title from bugfix-request.json>",
  "description": "<actual_behavior from bugfix-request.json> — Root cause: <confirmed root cause>",
  "priority": "<Critical|Major → 'high', Minor → 'medium', Cosmetic → 'low'>",
  "status": "failing",
  "srs_trace": ["<FR-xxx from linked feature, or new FR-xxx if unlinked>"],
  "dependencies": [<fixed_feature_id>],
  "ui": <copy from linked feature's ui field, or false if feature_id is null>,
  "deprecated": false,
  "deprecated_reason": null,
  "supersedes": null,
  "bug_severity": "<severity from bugfix-request.json>",
  "bug_source": "manual-testing",
  "fixed_feature_id": <feature_id from bugfix-request.json, or null>,
  "root_cause": "<confirmed root cause one-sentence>"
}
```

**说明：**
- `dependencies`：若 `fixed_feature_id` 非空则设为 `[fixed_feature_id]`（确保 Worker 先处理原特性再处理本修复）；若为 null 则设为 `[]`
- `ui`：若 `feature_id` 非空则使用关联特性的 `ui` 字段；否则 `false`
- `wave`：使用 `feature-list.json` 中 `waves` 数组的当前最大 wave id
- **ATS 提示**：若 `fixed_feature_id` 非空且存在 ATS 文档（`docs/plans/*-ats.md`），在 ATS 映射表中查找关联特性的需求。将 `srs_trace` 设为包含关联特性的需求 ID，以便下游 feature-st 从 SRS 验收标准推导所需测试用例

添加后执行校验：
```bash
python scripts/validate_features.py feature-list.json
```

继续前须修复所有校验错误。

---

## 步骤 7：更新 task-progress.md

在当前 `## Current State` 内容之后追加一条 hotfix 会话条目：

```markdown
## Hotfix Session — YYYY-MM-DD: <bug title>
- **Severity**: <severity>
- **Bugfix Feature ID**: #<new id>
- **Fixed Feature**: #<fixed_feature_id> <feature title> (or "Unlinked")
- **Root Cause**: <one sentence>
- **Status**: Enqueued — Worker will handle TDD/Quality/ST/Review
```

同时更新 `## Current State` 标题以反映新的 failing 特性。

---

## 步骤 8：收尾

1. 使用 `env-guide.md` 中的 Stop 命令停止步骤 4 中启动的服务；确认已停止
2. 删除 `bugfix-request.json`（**最终不可逆操作** — 仅在步骤 6、7 完成且 `validate_features.py` 通过后执行）
3. 打印：
   ```
   Bug #<id> enqueued as category=bugfix feature.
   Title: Fix: <title>
   Severity: <severity>
   Root cause: <one sentence>
   Worker will handle: TDD → Quality → ST → Review
   ```
4. 链接至：`long-task:long-task-work`

---

## 关键规则

- **任何动作前先校验信号文件** — 校验器通过后方可进入步骤 3
- **先复现再分析** — 「无法复现」是有效记录结果；不得在未复现时跳到根因
- **入队前根因须已确认** — 四阶段系统化调试为强制要求；禁止猜测后入队
- **信号文件最后删除** — 删除为最终不可逆动作；须先通过 `validate_features.py`
- **若同时存在 `bugfix-request.json` 与 `increment-request.json`**：先完整处理本 hotfix；**不要**删除 `increment-request.json`；留待下一会话处理
- **链接到 Worker 前须停掉所有服务** — 复现时启动的服务必须停止；Worker 自行管理服务生命周期
- **本技能不实现修复** — TDD/Quality/ST/Review 归 Worker；本技能仅校验、诊断与入队
- **此处禁止随意改代码** — 不要在本技能中写测试或修代码；那是 Worker 的职责

## 危险信号

以下想法表示**停** — 你在自我合理化：

| 想法 | 事实 |
|---------|---------|
| 「代码里已经能看出 bug，我直接修」 | 先走完根因四阶段；再入队；由 Worker 修复 |
| 「我已知根因，跳过阶段 1–3」 | 四个阶段均为强制；记录过程可避免错误假设 |
| 「复现不了但我清楚原因」 | 无法复现 = 停止；记入 task-progress.md；询问用户 |
| 「跳过 feature-list.json，直接修」 | 每次修复必须在 feature-list.json 中可追溯，category=bugfix |
| 「信号文件有错但意图清楚」 | 校验器必须通过；请用户修正文件 |
| 「先删信号文件再收拾」 | 信号文件删除是验证一切之后的**最后**一步 |
| 「修复很简单，Worker 流水线太重」 | Worker 保证回归测试、覆盖率、ST 用例与评审 — 均为必需 |

## 集成

本技能由 `using-long-task` 路由器在项目根存在 `bugfix-request.json` 时调用（优先级最高 — 高于 increment）。本技能完成后：
- `bugfix-request.json` 已删除
- `feature-list.json` 中新增一条 `category: "bugfix"` 且 `status: "failing"` 的特性
- 路由器下一次检测：`feature-list.json` 存在 failing 特性 → `long-task-work`
- Worker 接管该 bugfix 特性并执行完整 TDD → Quality → ST → Review 流水线
