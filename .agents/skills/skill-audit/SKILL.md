---
name: skill-audit
description: 适用于需要对照 skill-anatomy.md 做 AHE skill 合规审查的场景。检查 description 分类器语义、方法论可追溯性、章节结构、references/ 一致性。不适用于首次创建 skill 或纯精简优化（→ skill-optimization）。
---

# Skill Audit — AHE Skill 合规审查

对照 `docs/principles/skill-anatomy.md` 对已有 AHE skill 做系统性合规检查，识别并修复不符合项。

与 `skill-optimization` 的区别：optimization 聚焦精简（臃肿 → 精简 + references/），audit 聚焦合规（现有内容是否满足 anatomy 原则）。

## When to Use

适用：
- skill 已完成精简优化，需要验证是否符合 anatomy 标准
- skill 的 description 被质疑触发不准确
- skill 声明了方法论但不确定是否有据可依
- skill 缺少方法论声明，需要查找并补齐
- 定期质量巡检

不适用 → 改用：
- skill 臃肿需要精简 → `skill-optimization`
- 首次创建新 skill → 按 `docs/principles/skill-anatomy.md` 直接写
- 需要 Claude Code 代工 → `claude-code`

## Workflow

### 1. 加载标准

读取项目的 skill anatomy 标准：
- `docs/principles/skill-anatomy.md` — 必读
- `AGENTS.md` — 项目路径约定

### 2. 基线采集

对目标 skill 执行：
- 读取 SKILL.md 全文
- 读取 references/ 目录下所有文件
- 读取 evals/README.md 和 evals/evals.json（如存在）
- 记录：总行数、总字符数、估算 tokens、章节结构

### 3. 逐项检查（20 项清单）

用以下清单逐项判定 PASS / PARTIAL / FAIL：

**Frontmatter（5 项）：**

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 1 | name 与目录名一致 | 完全匹配 |
| 2 | name 格式合规 | 字母/数字/连字符, 1-64 字符 |
| 3 | description 是分类器 | 只含触发条件/反向边界/reroute，不含功能摘要 |
| 4 | description 使用祈使句 | Use when / 适用于 / Not for / 不适用于 开头 |
| 5 | description 前置触发场景 | 截断时优先丢失尾部而非头部 |

**正文结构（10 项）：**

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 6 | description + intro < 1500 chars | 合计字符数 |
| 7 | H1 开场 1-2 句 | 只写职责和非目标 |
| 8 | When to Use 完整 | 正向/反向/direct invoke/邻接边界 |
| 9 | 与相邻 skill 区别显式 | 至少区分最易混淆的邻接节点 |
| 10 | Workflow 编号步骤 | 有编号、有决策点 |
| 11 | Workflow 先读最少证据 | 第一步是读取而非执行 |
| 12 | Output Contract 明确 | 写什么/写哪/状态同步/next action |
| 13 | 路径可迁移 | 无写死的 repo-local 路径 |
| 14 | Red Flags 存在 | 运行时 stop sign |
| 15 | Reference Guide 存在 | 表格指向 references/ |

**质量预算（2 项）：**

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 16 | Verification 存在 | 退出条件 checklist |
| 17 | SKILL.md < 500 行 / < 5000 tokens | 量化预算 |

**evals（1 项）：**

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 18 | evals/ 结构完整 | README.md + evals.json，高风险 skill 至少 2-3 case |

**方法论（2 项）：**

| # | 检查项 | 判定标准 |
|---|--------|----------|
| 19 | 方法论名称准确 | 未把自定义裁剪误标为标准实现 |
| 20 | 方法论有来源 + 落地步骤映射 | 表格含来源列 + 落地步骤列 |

### 4. Description 深度检查

这是最常见的 FAIL 点，需要单独展开分析：

**分类器语义判定规则：**

| 内容类型 | 应在 description | 应在 H1 开场段 |
|----------|-----------------|---------------|
| 触发条件（"尚无已批准规格"） | ✅ | ❌ |
| 反向边界（"不适用于已有批准规格"） | ✅ | ❌ |
| reroute 线索（"→ ahe-design"） | ✅ | ❌ |
| 功能描述（"澄清需求并起草规格"） | ❌ | ✅ |
| 方法论名（"使用 EARS/BDD"） | ❌ | 按需 |
| 流程步骤 | ❌ | ❌ |

**修复模板：**

将 description 重构为 `适用于 <触发条件1>、<触发条件2>、或<触发条件3>。不适用于<反向边界1>（→ <reroute目标>）、<反向边界2>（→ <reroute目标>）。`

### 5. 方法论可追溯性检查

这是方法论审查的核心步骤。分两种情况处理：

#### 5A. 已有 Methodology 声明的 skill

1. **名称准确性**：声明的方法论是否准确？
   - 常见错误：把自定义分类/模板直接标注为某个标准名
   - 修复：用"参考 X 思想，经项目化裁剪"替代

2. **来源可追溯**：每个方法论是否标注了原始来源（作者/年份/论文/标准）？
   - 要求：每个方法论至少能通过名称+作者在网络上找到原始出处
   - 不确定时，用网络搜索验证方法论名称和来源是否准确

3. **落地步骤映射**：方法论是否与 Workflow 步骤有对应？还是只列了名字？

4. **references/ 一致性**：references/ 文件中使用方法论技术时，章节标题是否也标注了出处？

5. **缺失识别**：workflow 中实际使用但未在 Methodology 声明的方法论？

#### 5B. 缺少 Methodology 声明的 skill

如果 skill 没有 Methodology 章节，必须执行以下步骤：

1. **分析 skill 的 workflow**：识别 skill 实际使用的核心技术和方法
   - 例如：结构化检查清单、分类器语义、Given-When-Then、EARS 句式、ADR 等

2. **网络搜索相关方法论**：对识别出的每种技术，搜索其学术或工业来源
   - 搜索关键词示例：`structured walkthrough software review`、`EARS requirements notation`、`Given When Then BDD`、`Architecture Decision Records`
   - 目标：找到原始提出者（作者/组织）、提出年份、原始论文或标准文档

3. **验证方法论的准确性**：
   - 搜索结果是否与 skill 中使用的方式一致？
   - 是否存在更准确的名称？（例如：不是 "code review" 而是 "Fagan Inspection"）
   - 是否是自定义裁剪而非标准实现？如果是，标注 "adapted" 或 "参考 X 思想"

4. **补齐 Methodology 章节**：在 SKILL.md 的 H1 开场段之后、When to Use 之前插入 Methodology 章节
   - 格式：方法论名（来源，adapted？）+ 一句话说明本 skill 如何使用它
   - 示例：`**Checklist-Based Review (NASA/SEI)**: 使用结构化检查清单覆盖关键质量维度，防止评审者凭印象遗漏系统性问题。`

5. **注意事项**：
   - 不要把自定义做法标注为标准方法论名
   - 不要发明不存在的方法论
   - 搜索不到可靠来源的，标注为"项目化实践"而非标准名
   - 每个方法论至少能通过名称在搜索引擎上找到 2 个独立来源

### 6. 输出审查报告

格式：

```
=== <skill-name> 审查报告 ===
总计: X PASS, Y PARTIAL, Z FAIL

FAIL 项:
  #N <检查项>: <具体问题>
     当前: ...
     应改为: ...

PARTIAL 项:
  #N <检查项>: <具体问题>
     当前: ... (部分满足)
     建议: ...

方法论检查:
  [有/无] Methodology 章节
  [已验证/需查找] 来源准确性
  [需要查找的方法论列表]

无需修改的项: (列出 PASS 项编号)
```

### 7. 执行修复并提交

对 FAIL 和 PARTIAL 项逐个修复，每修复一组相关项做一次 git commit：

```
git commit -m "fix(<skill-name>): <修复摘要>

<列出具体修改项>"
```

方法论补齐应单独提交：

```
git commit -m "fix(<skill-name>): add Methodology section with verified sources"
```

## Red Flags

- description 开头是功能描述而非触发条件
- Methodology 只列名字没有来源
- Methodology 把自定义做法标注为标准名
- Workflow 步骤不标注使用的方法论
- references/ 文件使用技术但不标注方法论出处
- 验证清单不检查方法论相关项
- 缺少 Methodology 但 workflow 明显使用了可追溯的方法论

## Verification

- [ ] 20 项清单全部 PASS 或 PARTIAL（无 FAIL）
- [ ] description 纯分类器语义（无功能摘要）
- [ ] 方法论已声明且名称准确 + 有来源 + 有落地映射
- [ ] 缺少方法论的 skill 已通过网络查找补齐
- [ ] 修改已 git commit
