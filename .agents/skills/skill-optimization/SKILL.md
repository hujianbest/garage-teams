---
name: skill-optimization
description: 优化 Hermes skills 的结构化流程。适用于已有 skill 过于臃肿、需要参考外部高质量 skill 进行精简和补全的场景。
---

# Skill 优化流程

将臃肿的 skill（所有内容内联在 SKILL.md）重构为精简 SKILL.md + references/ 按需加载的模式。

## 优化步骤

### 1. 基线评估

- 记录当前 SKILL.md 行数和总行数（含 references）
- 列出当前结构（所有 ## 和 ### 标题）
- 确认是否有 references/ 目录及其内容

### 2. 研究外部参考 skills

两步搜索策略：

**本地搜索（已安装的 skills）：**
- `find ~/.agents/skills/ -name "SKILL.md" | xargs grep -l "关键词"`
- `find ~/.hermes/skills/ -name "SKILL.md" | xargs grep -l "关键词"`

**外部搜索（在线 skills 仓库）：**
- 加载 `find-skills` skill，用关键词搜索在线 skill 仓库中的高质量 skills
- 外部 skills 通常结构更成熟，是很好的参考来源

**筛选标准：**
- 同名或同领域 skill 优先
- 结构精简（SKILL.md < 200 行 + references/ 按需加载）的 skill 是最佳参考
- 记录参考 skill 的结构：SKILL.md 行数 + references/ 行数 + 总行数

### 3. 差异分析（双方向）

**冗余识别（要删的）：**
- 找到说了同一件事的多个章节（三重重复最常见：A说了、B说了、C也说了）
- 找到可以合并到一处的小节
- 找到过于详细的示例/模板（适合拆到 references/）

**缺失识别（要补的）：**
- 参考skill有而当前skill没有的概念/章节
- 参考skill使用了 references/ 按需加载而当前skill全部内联的内容

### 4. 制定重构计划

输出三列清单：
- DELETE：要删除的章节 + 原因
- EXTRACT：要拆到 references/ 的内容 + 目标文件名
- ADD：要新增的内容 + 来源

确认目标行数：SKILL.md 目标 ~120-200 行，详细内容走 references/。

### 5. 执行重构

1. 创建 references/ 目录
2. 逐一创建 references/ 文件（先做这步，SKILL.md 需要引用它们）
3. 重写 SKILL.md（精简主体，用 Reference Guide 表格指向 references/）
4. 验证：行数统计、结构完整性（标题编号连续、引用无断裂）

### 6. 提交

```
git add <skill-path>/
git commit -m "refactor(<skill-name>): 精简 SKILL.md X→Y 行，拆 N 个 references

删除冗余章节：...
新增 references/ 按需加载：...
..."
```

## Reference Guide 模式

精简后的 SKILL.md 应包含 Reference Guide 表格，格式：

```markdown
## Reference Guide

按需加载详细参考内容：

| 主题 | Reference | 加载时机 |
|------|-----------|---------|
| ... | `references/xxx.md` | ...时 |
```

## 常见冗余模式

- **三重重复**：Overview + Quality Bar + Verification 说同一件事 → 合并到 Verification
- **Constraints 散落**：MUST DO / Common Rationalizations / Red Flags 有重叠 → 保留 MUST DO + Red Flags
- **模板内联**：ADR模板、检查清单、表格格式全部内联 → 拆到 references/
- **Contract 重复**：Standalone Contract 和 When to Use 的负面列表重叠 → 合并到 When to Use

## 方法论审计模式（适用于 AHE 及声明了方法论来源的 skills）

当 skill 在 Methodology 章节声明了业界方法论（如 EARS、BDD、MoSCoW、INVEST 等），需要额外做一轮方法论准确性审查。

### 审查清单

1. **名称准确性**：声明的方法论名称是否准确？是否把自定义裁剪误标为标准实现？
   - 例：FR/NFR/CON/IFR/ASM/EXC 不是 IEEE 830 的标准分类，不应标注为 "IEEE 830 Requirement Taxonomy"
2. **来源可追溯**：每个方法论是否标注了原始来源（作者、年份、论文/标准/书籍）？
3. **落地步骤映射**：方法论是否与 Workflow 中的具体步骤有对应关系？还是只列了名字没说在哪用？
4. **references/ 一致性**：references/ 文件中使用方法论技术时，是否也标注了出处？还是只用了技术但没说是哪个方法论？
5. **缺失识别**：是否有在 workflow 中实际使用但未在 Methodology 中声明的方法论？

### 修复模式

- 修正不准确的标注：用"参考 X 思想，经项目化裁剪"替代直接标注为标准实现
- Methodology 章节改为表格，增加"来源"和"落地步骤"列
- Workflow 步骤标题增加方法论标注（如 "步骤 3 — Socratic Elicitation"）
- references/ 文件的章节标题增加方法论出处（如 "Statement Patterns (EARS — Mavin et al., REFSQ 2009)"）
- Verification 检查点增加方法论相关的验证项

## 批量优化模式（适用于同族 skills）

当需要优化一组结构相似的同族 skills（如 AHE 系列 17 个 skills），使用以下加速流程：

### 前提条件

- 已完成至少 2-3 个 skills 的单独优化，掌握了通用冗余模式
- 同族 skills 共享相同的结构模板（相同章节名、相同冗余点）

### 批量流程

1. **样本分析**：单独优化前 2-3 个，确认通用 DELETE/EXTRACT 模式
2. **并行读取**：用 `delegate_task(tasks=[...])` 并行读取 3 批 skills（每批 3 个）
3. **批量写入**：用 `execute_code` 在一次调用中 `write_file` 多个 SKILL.md
4. **单独提交 vs 批量提交**：
   - 前 5-8 个 skills 逐个 git commit（方便回滚和追踪）
   - 剩余 skills 一次性 `git commit`（确认模式稳定后）
5. **更新 todo list**：每完成一批更新 `todo` tool

### AHE 系列通用删除清单

以下章节在所有 AHE skills 中都是冗余的，统一删除：

| 章节 | 冗余原因 |
|------|---------|
| Overview | 和 intro 段重复 |
| Standalone Contract | 和 When to Use 负面列表重复 |
| Chain Contract | 和 intro/Writing 模式说明重复 |
| Quality Bar | 和 Workflow 自检步骤 + Verification 重复 |
| Inputs / Required Artifacts | 路径/模板细节拆到 references |
| Common Rationalizations | 编码在 Hard Gates + Red Flags 中 |

保留的章节：frontmatter、intro、When to Use、Hard Gates、Workflow（压缩）、Output Contract（压缩）、Red Flags、Reference Guide（新增）、Verification。

### 性能数据

- 17 个 skills (~5600 行) → ~1681 行，减少 ~70%
- 前 8 个单独优化约 1.5 小时，后 9 个批量优化约 10 分钟
