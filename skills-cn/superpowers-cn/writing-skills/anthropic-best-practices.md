# 技能撰写最佳实践

> 学习如何撰写 Claude 能够发现并有效使用的技能。

优秀的技能简洁、结构清晰，并经过真实使用验证。本指南提供实用的撰写决策，帮助你写出 Claude 能发现并有效使用的技能。

关于技能如何运作的概念背景，见 [Skills 概览](/en/docs/agents-and-tools/agent-skills/overview)。

## 核心原则

### 简洁是关键

[上下文窗口](https://platform.claude.com/docs/en/build-with-claude/context-windows)是一种公共资源。你的技能与 Claude 需要了解的其他一切共享上下文窗口，包括：

* 系统提示
* 对话历史
* 其他技能的元数据
* 用户的实际请求

并非技能中的每个 token 都会立即产生成本。启动时，只会预加载所有技能的元数据（name 与 description）。仅在技能变得相关时 Claude 才会读取 SKILL.md，并仅在需要时读取其他文件。然而，SKILL.md 仍应保持简洁：一旦加载，每个 token 都会与对话历史及其他上下文竞争。

**默认假设**：Claude 已经相当聪明

只补充 Claude 尚不具备的上下文。对每条信息都要追问：

* 「Claude 真的需要这段解释吗？」
* 「能否默认 Claude 已经知道这些？」
* 「这一段值得占用这些 token 吗？」

**好示例：简洁**（约 50 个 token）：

````markdown  theme={null}
## Extract PDF text

Use pdfplumber for text extraction:

```python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

**差示例：过于冗长**（约 150 个 token）：

```markdown  theme={null}
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but we
recommend pdfplumber because it's easy to use and handles most cases well.
First, you'll need to install it using pip. Then you can use the code below...
```

简洁版假定 Claude 已知 PDF 是什么以及库如何工作。

### 设定恰当的自由度

使具体程度与任务的脆弱性、可变性相匹配。

**高自由度**（基于文本的说明）：

适用于：

* 多种做法都成立
* 决策依赖上下文
* 由启发式引导做法

示例：

```markdown  theme={null}
## Code review process

1. Analyze the code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability and maintainability
4. Verify adherence to project conventions
```

**中等自由度**（伪代码或带参数的脚本）：

适用于：

* 存在首选模式
* 允许一定变化
* 配置影响行为

示例：

````markdown  theme={null}
## Generate report

Use this template and customize as needed:

```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data
    # Generate output in specified format
    # Optionally include visualizations
```
````

**低自由度**（特定脚本，参数很少或没有）：

适用于：

* 操作脆弱且易错
* 一致性至关重要
* 必须遵循特定顺序

示例：

````markdown  theme={null}
## Database migration

Run exactly this script:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
````

**类比**：把 Claude 想成在探路的机器人：

* **两侧是悬崖的窄桥**：只有一条安全路径。提供具体护栏与精确说明（低自由度）。示例：必须按严格顺序执行的数据库迁移。
* **无障碍的开阔地**：多条路都能成功。给大方向并信任 Claude 找最佳路线（高自由度）。示例：代码审查，最佳做法由上下文决定。

### 用你计划使用的所有模型进行测试

技能是对模型的补充，因此效果取决于底层模型。请用你打算搭配使用的每一个模型测试技能。

**按模型考虑的测试要点**：

* **Claude Haiku**（快、省）：技能是否提供足够指引？
* **Claude Sonnet**（均衡）：技能是否清晰高效？
* **Claude Opus**（强推理）：技能是否避免过度解释？

对 Opus 完美的说明可能对 Haiku 需要更多细节。若技能要在多个模型上使用，应力求说明对所有模型都好用。

## 技能结构

<Note>
  **YAML 页眉**：SKILL.md 的 frontmatter 支持两个字段：

  * `name` — 人类可读的技能名（最多 64 字符）
  * `description` — 单行说明技能做什么以及何时使用（最多 1024 字符）

  完整结构见 [Skills 概览](/en/docs/agents-and-tools/agent-skills/overview#skill-structure)。
</Note>

### 命名约定

使用一致的命名模式，便于引用与讨论。建议技能名采用**动名词形式**（动词 + -ing），以清楚描述技能提供的活动或能力。

**良好命名示例（动名词）**：

* "Processing PDFs"
* "Analyzing spreadsheets"
* "Managing databases"
* "Testing code"
* "Writing documentation"

**可接受的变体**：

* 名词短语："PDF Processing"、"Spreadsheet Analysis"
* 动作导向："Process PDFs"、"Analyze Spreadsheets"

**避免**：

* 模糊名："Helper"、"Utils"、"Tools"
* 过于泛化："Documents"、"Data"、"Files"
* 技能库内模式不一致

一致命名有助于：

* 在文档与对话中引用技能
* 一眼看出技能做什么
* 组织与搜索多个技能
* 维持专业、连贯的技能库

### 撰写有效的 description

`description` 字段用于技能发现，应同时说明技能**做什么**以及**何时**使用。

<Warning>
  **始终使用第三人称**。description 会注入系统提示，人称不一致会导致发现问题。

  * **好：** "Processes Excel files and generates reports"
  * **避免：** "I can help you process Excel files"
  * **避免：** "You can use this to process Excel files"
</Warning>

**要具体并包含关键词**。既要说明技能做什么，也要说明使用的具体触发条件/上下文。

每个技能只有一个 description 字段。它对技能选择至关重要：Claude 用它从可能 100+ 个可用技能中挑选。description 必须足够细致，让 Claude 知道何时选中本技能；SKILL.md 其余部分提供实现细节。

有效示例：

**PDF Processing 技能：**

```yaml  theme={null}
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**Excel Analysis 技能：**

```yaml  theme={null}
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
```

**Git Commit Helper 技能：**

```yaml  theme={null}
description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.
```

避免如下模糊 description：

```yaml  theme={null}
description: Helps with documents
```

```yaml  theme={null}
description: Processes data
```

```yaml  theme={null}
description: Does stuff with files
```

### 渐进式披露模式

SKILL.md 作为总览，按需指向详细材料，类似入职指南中的目录。渐进式披露如何运作，见概览中的 [How Skills work](/en/docs/agents-and-tools/agent-skills/overview#how-skills-work)。

**实践建议：**

* 为获得最佳性能，SKILL.md 正文保持在 500 行以内
* 接近该上限时将内容拆到单独文件
* 用下文模式组织说明、代码与资源

#### 可视化概览：从简单到复杂

基础技能可以仅从包含元数据与说明的 SKILL.md 开始：

<img src="https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=87782ff239b297d9a9e8e1b72ed72db9" alt="展示 YAML frontmatter 与 Markdown 正文的简单 SKILL.md 文件" data-og-width="2048" width="2048" data-og-height="1153" height="1153" data-path="images/agent-skills-simple-file.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?w=280&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=c61cc33b6f5855809907f7fda94cd80e 280w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?w=560&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=90d2c0c1c76b36e8d485f49e0810dbfd 560w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?w=840&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=ad17d231ac7b0bea7e5b4d58fb4aeabb 840w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?w=1100&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=f5d0a7a3c668435bb0aee9a3a8f8c329 1100w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?w=1650&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=0e927c1af9de5799cfe557d12249f6e6 1650w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-simple-file.png?w=2500&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=46bbb1a51dd4c8202a470ac8c80a893d 2500w" />

随着技能增长，可打包额外内容，仅在需要时由 Claude 加载：

<img src="https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=a5e0aa41e3d53985a7e3e43668a33ea3" alt="打包 reference.md、forms.md 等额外参考文件。" data-og-width="2048" width="2048" data-og-height="1327" height="1327" data-path="images/agent-skills-bundling-content.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?w=280&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=f8a0e73783e99b4a643d79eac86b70a2 280w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?w=560&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=dc510a2a9d3f14359416b706f067904a 560w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?w=840&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=82cd6286c966303f7dd914c28170e385 840w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?w=1100&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=56f3be36c77e4fe4b523df209a6824c6 1100w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?w=1650&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=d22b5161b2075656417d56f41a74f3dd 1650w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-bundling-content.png?w=2500&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=3dd4bdd6850ffcc96c6c45fcb0acd6eb 2500w" />

完整技能目录结构可能如下：

```
pdf/
├── SKILL.md              # Main instructions (loaded when triggered)
├── FORMS.md              # Form-filling guide (loaded as needed)
├── reference.md          # API reference (loaded as needed)
├── examples.md           # Usage examples (loaded as needed)
└── scripts/
    ├── analyze_form.py   # Utility script (executed, not loaded)
    ├── fill_form.py      # Form filling script
    └── validate.py       # Validation script
```

#### 模式 1：高层指南与引用

````markdown  theme={null}
---
name: PDF Processing
description: Extracts text and tables from PDF files, fills forms, and merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---

# PDF Processing

## Quick start

Extract text with pdfplumber:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

## Advanced features

**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
**Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
````

仅在需要时 Claude 才加载 FORMS.md、REFERENCE.md 或 EXAMPLES.md。

#### 模式 2：按领域组织

对跨多个领域的技能，按领域组织内容，避免加载无关上下文。用户问销售指标时，Claude 只需读销售相关 schema，不必读财务或市场数据。这样 token 占用低、上下文更聚焦。

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

````markdown SKILL.md theme={null}
# BigQuery Data Analysis

## Available datasets

**Finance**: Revenue, ARR, billing → See [reference/finance.md](reference/finance.md)
**Sales**: Opportunities, pipeline, accounts → See [reference/sales.md](reference/sales.md)
**Product**: API usage, features, adoption → See [reference/product.md](reference/product.md)
**Marketing**: Campaigns, attribution, email → See [reference/marketing.md](reference/marketing.md)

## Quick search

Find specific metrics using grep:

```bash
grep -i "revenue" reference/finance.md
grep -i "pipeline" reference/sales.md
grep -i "api usage" reference/product.md
```
````

#### 模式 3：按条件展开细节

展示基础内容，链接到进阶内容：

```markdown  theme={null}
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

仅在用户需要这些功能时 Claude 才读取 REDLINING.md 或 OOXML.md。

### 避免过深嵌套引用

当被引用文件再引用其他文件时，Claude 可能只部分读取。遇到嵌套引用时，Claude 可能用 `head -100` 等命令预览而非读全文件，导致信息不完整。

**引用深度距 SKILL.md 保持一层**。所有参考文件应能从 SKILL.md 直接链到，以便在需要时读完整文件。

**差示例：过深**：

```markdown  theme={null}
# SKILL.md
See [advanced.md](advanced.md)...

# advanced.md
See [details.md](details.md)...

# details.md
Here's the actual information...
```

**好示例：仅一层**：

```markdown  theme={null}
# SKILL.md

**Basic usage**: [instructions in SKILL.md]
**Advanced features**: See [advanced.md](advanced.md)
**API reference**: See [reference.md](reference.md)
**Examples**: See [examples.md](examples.md)
```

### 较长参考文件用目录组织

超过 100 行的参考文件应在顶部加目录。这样即使部分预览，Claude 也能看到信息全貌。

**示例**：

```markdown  theme={null}
# API Reference

## Contents
- Authentication and setup
- Core methods (create, read, update, delete)
- Advanced features (batch operations, webhooks)
- Error handling patterns
- Code examples

## Authentication and setup
...

## Core methods
...
```

随后 Claude 可按需读全文或跳到具体节。

关于该基于文件的架构如何实现渐进式披露，见下文高级章节中的 [Runtime environment](#runtime-environment)。

## 工作流与反馈环

### 对复杂任务使用工作流

把复杂操作拆成清晰、顺序的步骤。对工作流特别复杂的，提供清单供 Claude 复制到回复中并逐项勾选。

**示例 1：研究综合工作流**（无代码的技能）：

````markdown  theme={null}
## Research synthesis workflow

Copy this checklist and track your progress:

```
Research Progress:
- [ ] Step 1: Read all source documents
- [ ] Step 2: Identify key themes
- [ ] Step 3: Cross-reference claims
- [ ] Step 4: Create structured summary
- [ ] Step 5: Verify citations
```

**Step 1: Read all source documents**

Review each document in the `sources/` directory. Note the main arguments and supporting evidence.

**Step 2: Identify key themes**

Look for patterns across sources. What themes appear repeatedly? Where do sources agree or disagree?

**Step 3: Cross-reference claims**

For each major claim, verify it appears in the source material. Note which source supports each point.

**Step 4: Create structured summary**

Organize findings by theme. Include:
- Main claim
- Supporting evidence from sources
- Conflicting viewpoints (if any)

**Step 5: Verify citations**

Check that every claim references the correct source document. If citations are incomplete, return to Step 3.
````

该示例展示工作流如何用于不需要代码的分析任务。清单模式适用于任何复杂多步流程。

**示例 2：PDF 表单填写工作流**（含代码的技能）：

````markdown  theme={null}
## PDF form filling workflow

Copy this checklist and check off items as you complete them:

```
Task Progress:
- [ ] Step 1: Analyze the form (run analyze_form.py)
- [ ] Step 2: Create field mapping (edit fields.json)
- [ ] Step 3: Validate mapping (run validate_fields.py)
- [ ] Step 4: Fill the form (run fill_form.py)
- [ ] Step 5: Verify output (run verify_output.py)
```

**Step 1: Analyze the form**

Run: `python scripts/analyze_form.py input.pdf`

This extracts form fields and their locations, saving to `fields.json`.

**Step 2: Create field mapping**

Edit `fields.json` to add values for each field.

**Step 3: Validate mapping**

Run: `python scripts/validate_fields.py fields.json`

Fix any validation errors before continuing.

**Step 4: Fill the form**

Run: `python scripts/fill_form.py input.pdf fields.json output.pdf`

**Step 5: Verify output**

Run: `python scripts/verify_output.py output.pdf`

If verification fails, return to Step 2.
````

清晰步骤可防止 Claude 跳过关键校验。清单有助于 Claude 与你跟踪多步工作流进度。

### 实现反馈环

**常见模式**：运行校验器 → 修复错误 → 重复

该模式能显著提升输出质量。

**示例 1：风格指南符合性**（无代码的技能）：

```markdown  theme={null}
## Content review process

1. Draft your content following the guidelines in STYLE_GUIDE.md
2. Review against the checklist:
   - Check terminology consistency
   - Verify examples follow the standard format
   - Confirm all required sections are present
3. If issues found:
   - Note each issue with specific section reference
   - Revise the content
   - Review the checklist again
4. Only proceed when all requirements are met
5. Finalize and save the document
```

这展示用参考文档而非脚本的校验环。「校验器」即 STYLE\_GUIDE.md，Claude 通过阅读与比对完成检查。

**示例 2：文档编辑流程**（含代码的技能）：

```markdown  theme={null}
## Document editing process

1. Make your edits to `word/document.xml`
2. **Validate immediately**: `python ooxml/scripts/validate.py unpacked_dir/`
3. If validation fails:
   - Review the error message carefully
   - Fix the issues in the XML
   - Run validation again
4. **Only proceed when validation passes**
5. Rebuild: `python ooxml/scripts/pack.py unpacked_dir/ output.docx`
6. Test the output document
```

校验环可尽早发现错误。

## 内容准则

### 避免时效性信息

不要包含会很快过时的信息：

**差示例：强时效**（将变为错误）：

```markdown  theme={null}
If you're doing this before August 2025, use the old API.
After August 2025, use the new API.
```

**好示例**（使用「旧模式」小节）：

```markdown  theme={null}
## Current method

Use the v2 API endpoint: `api.example.com/v2/messages`

## Old patterns

<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>

The v1 API used: `api.example.com/v1/messages`

This endpoint is no longer supported.
</details>
```

「旧模式」小节提供历史背景而不打乱正文。

### 使用一致术语

选定一种说法并在技能中通篇使用：

**好 — 一致**：

* Always "API endpoint"
* Always "field"
* Always "extract"

**差 — 不一致**：

* Mix "API endpoint", "URL", "API route", "path"
* Mix "field", "box", "element", "control"
* Mix "extract", "pull", "get", "retrieve"

一致性有助于 Claude 理解与遵循说明。

## 常见模式

### 模板模式

提供输出格式模板。严格程度与需求匹配。

**严格要求**（如 API 响应或数据格式）：

````markdown  theme={null}
## Report structure

ALWAYS use this exact template structure:

```markdown
# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data
- Finding 3 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```
````

**灵活指引**（需要变通时）：

````markdown  theme={null}
## Report structure

Here is a sensible default format, but use your best judgment based on the analysis:

```markdown
# [Analysis Title]

## Executive summary
[Overview]

## Key findings
[Adapt sections based on what you discover]

## Recommendations
[Tailor to the specific context]
```

Adjust sections as needed for the specific analysis type.
````

### 示例模式

对输出质量依赖「看到示例」的技能，像常规提示那样提供输入/输出对：

````markdown  theme={null}
## Commit message format

Generate commit messages following these examples:

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly in reports
Output:
```
fix(reports): correct date formatting in timezone conversion

Use UTC timestamps consistently across report generation
```

**Example 3:**
Input: Updated dependencies and refactored error handling
Output:
```
chore: update dependencies and refactor error handling

- Upgrade lodash to 4.17.21
- Standardize error response format across endpoints
```

Follow this style: type(scope): brief description, then detailed explanation.
````

示例比单靠描述更能帮 Claude 理解期望风格与细节程度。

### 条件工作流模式

引导 Claude 通过决策点：

```markdown  theme={null}
## Document modification workflow

1. Determine the modification type:

   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow:
   - Use docx-js library
   - Build document from scratch
   - Export to .docx format

3. Editing workflow:
   - Unpack existing document
   - Modify XML directly
   - Validate after each change
   - Repack when complete
```

<Tip>
  若工作流变大、步骤变多，可拆到单独文件，并让 Claude 按当前任务读取对应文件。
</Tip>

## 评估与迭代

### 先建评估

**在撰写大量文档之前先创建评估。**这样技能解决的是真实问题，而不是空想需求。

**评估驱动开发：**

1. **识别缺口**：在无技能情况下让 Claude 做代表性任务。记录具体失败或缺失上下文
2. **创建评估**：构建三个场景检验这些缺口
3. **建立基线**：衡量无技能时 Claude 的表现
4. **写最少说明**：只写够填补缺口并通过评估的内容
5. **迭代**：运行评估，对照基线改进

这样确保你在解决实际问题，而非臆测可能永不出现的需求。

**评估结构**：

```json  theme={null}
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF file and save it to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Successfully reads the PDF file using an appropriate PDF processing library or command-line tool",
    "Extracts text content from all pages in the document without missing any pages",
    "Saves the extracted text to a file named output.txt in a clear, readable format"
  ]
}
```

<Note>
  该示例展示带简单评分细则的数据驱动评估。我们目前不提供内置方式运行这些评估；用户可自行搭建评估系统。评估是衡量技能有效性的事实来源。
</Note>

### 与 Claude 迭代开发技能

最有效的技能开发过程包含 Claude 本身。用一个 Claude 实例（「Claude A」）创建将被其他实例（「Claude B」）使用的技能。Claude A 帮你设计与精炼说明，Claude B 在真实任务中测试。可行是因为 Claude 模型既懂如何写有效的代理说明，也懂代理需要哪些信息。

**创建新技能：**

1. **无技能完成一次任务**：与 Claude A 用常规提示协作解决问题。过程中你会自然提供上下文、偏好与流程知识。注意你反复提供了哪些信息。

2. **识别可复用模式**：任务完成后，找出哪些上下文对未来类似任务仍有价值。

   **示例**：若你做过 BigQuery 分析，可能提供过表名、字段定义、过滤规则（如「始终排除测试账号」）和常见查询模式。

3. **请 Claude A 创建技能**：「创建一个技能，捕捉我们刚用的 BigQuery 分析模式。包含表 schema、命名约定以及过滤测试账号的规则。」

   <Tip>
     Claude 模型原生理解技能格式与结构。无需特殊系统提示或「写技能」技能也能让 Claude 帮你建技能。直接请它创建技能，它会生成带合适 frontmatter 与正文的 SKILL.md。
   </Tip>

4. **审阅简洁性**：检查 Claude A 是否加了多余解释。可要求：「删掉关于胜率含义的解释——Claude 已经知道。」

5. **改进信息架构**：请 Claude A 更有效组织内容。例如：「把表 schema 放到单独参考文件里，我们以后可能加更多表。」

6. **在类似任务上测试**：让 Claude B（加载技能的新实例）做相关用例。观察是否找到正确信息、是否正确应用规则、是否成功完成任务。

7. **根据观察迭代**：若 Claude B 吃力或遗漏，带着具体现象回到 Claude A：「用这份技能时，Q4 忘了按日期过滤。要不要加一节讲日期过滤模式？」

**迭代现有技能：**

改进技能时沿用同一层次模式，在以下之间交替：

* **与 Claude A 协作**（帮助精炼技能的「专家」）
* **与 Claude B 测试**（用技能做真实工作的代理）
* **观察 Claude B 的行为**并把洞见带回 Claude A

1. **在真实工作流中使用技能**：给 Claude B（已加载技能）真实任务，而非测验场景

2. **观察 Claude B 的行为**：记录其吃力、成功或意外选择之处

   **观察示例**：「我要区域销售报表时，Claude B 写了查询但忘了过滤测试账号，尽管技能里写了这条规则。」

3. **回到 Claude A 改进**：分享当前 SKILL.md 并描述观察。可问：「区域报表时 Claude B 忘了过滤测试账号。技能提到了过滤，是不是不够显眼？」

4. **审阅 Claude A 的建议**：可能建议重组以突出规则、用更强措辞如「MUST filter」替代「always filter」，或重构工作流一节。

5. **应用并测试**：按 Claude A 的改进更新技能，再在类似请求上与 Claude B 复测

6. **随使用重复**：遇到新场景时继续观察-精炼-测试循环。每轮基于真实代理行为而非假设改进技能。

**收集团队反馈：**

1. 与队友分享技能并观察使用方式
2. 询问：技能是否在预期时激活？说明是否清晰？缺什么？
3. 纳入反馈，弥补你自己使用模式中的盲区

**为何有效**：Claude A 理解代理需求，你提供领域专长，Claude B 通过真实使用暴露缺口，迭代精炼基于观察到的行为而非假设。

### 观察 Claude 如何浏览技能

迭代技能时，留意 Claude 实际使用方式。注意：

* **意外的浏览顺序**：Claude 是否按你未预料的顺序读文件？可能说明结构不如你想的直观
* **遗漏关联**：Claude 是否未跟到重要文件的引用？链接可能需要更明确或更显眼
* **过度依赖某些节**：若反复读同一文件，考虑是否应放进主 SKILL.md
* **被忽略的内容**：若从不打开打包文件，可能多余或主说明中信号不足

基于这些观察而非假设迭代。元数据中的 `name` 与 `description` 尤其关键；Claude 用它们判断是否针对当前任务触发技能。务必清楚说明技能做什么、何时该用。

## 应避免的反模式

### 避免 Windows 风格路径

即使在 Windows 上，文件路径也始终使用正斜杠：

* ✓ **好**：`scripts/helper.py`、`reference/guide.md`
* ✗ **避免**：`scripts\helper.py`、`reference\guide.md`

Unix 风格路径在各平台可用；Windows 风格路径在 Unix 上会出错。

### 避免提供过多选项

除非必要，不要罗列多种做法：

````markdown  theme={null}
**Bad example: Too many choices** (confusing):
"You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image, or..."

**Good example: Provide a default** (with escape hatch):
"Use pdfplumber for text extraction:
```python
import pdfplumber
```

For scanned PDFs requiring OCR, use pdf2image with pytesseract instead."
````

## 高级：含可执行代码的技能

以下章节针对包含可执行脚本的技能。若你的技能仅有 Markdown 说明，可跳到 [Checklist for effective Skills](#checklist-for-effective-skills)。

### 解决问题，不要甩锅

为技能写脚本时，应处理错误情况，而不是把问题甩给 Claude。

**好示例：显式处理错误**：

```python  theme={null}
def process_file(path):
    """Process a file, creating it if it doesn't exist."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        # Create file with default content instead of failing
        print(f"File {path} not found, creating default")
        with open(path, 'w') as f:
            f.write('')
        return ''
    except PermissionError:
        # Provide alternative instead of failing
        print(f"Cannot access {path}, using default")
        return ''
```

**差示例：甩给 Claude**：

```python  theme={null}
def process_file(path):
    # Just fail and let Claude figure it out
    return open(path).read()
```

配置参数也应有依据并写清文档，避免「巫毒常数」（Ousterhout 定律）。若你都不知正确取值，Claude 如何确定？

**好示例：自解释**：

```python  theme={null}
# HTTP requests typically complete within 30 seconds
# Longer timeout accounts for slow connections
REQUEST_TIMEOUT = 30

# Three retries balances reliability vs speed
# Most intermittent failures resolve by the second retry
MAX_RETRIES = 3
```

**差示例：魔法数字**：

```python  theme={null}
TIMEOUT = 47  # Why 47?
RETRIES = 5   # Why 5?
```

### 提供实用脚本

即便 Claude 能写脚本，预制脚本仍有优势：

**实用脚本的好处**：

* 比生成代码更可靠
* 节省 token（不必把代码塞进上下文）
* 节省时间（无需现生成代码）
* 多次使用保持一致

<img src="https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=4bbc45f2c2e0bee9f2f0d5da669bad00" alt="将可执行脚本与说明文件一并打包" data-og-width="2048" width="2048" data-og-height="1154" height="1154" data-path="images/agent-skills-executable-scripts.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?w=280&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=9a04e6535a8467bfeea492e517de389f 280w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?w=560&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=e49333ad90141af17c0d7651cca7216b 560w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?w=840&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=954265a5df52223d6572b6214168c428 840w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?w=1100&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=2ff7a2d8f2a83ee8af132b29f10150fd 1100w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?w=1650&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=48ab96245e04077f4d15e9170e081cfb 1650w, https://mintcdn.com/anthropic-claude-docs/4Bny2bjzuGBK7o00/images/agent-skills-executable-scripts.png?w=2500&fit=max&auto=format&n=4Bny2bjzuGBK7o00&q=85&s=0301a6c8b3ee879497cc5b5483177c90 2500w" />

上图展示可执行脚本如何与说明文件配合。说明文件（如 forms.md）引用脚本，Claude 可执行脚本而无需把其全文加载进上下文。

**重要区分**：在说明中写清 Claude 应：

* **执行脚本**（最常见）：「运行 `analyze_form.py` 以提取字段」
* **作为参考阅读**（复杂逻辑时）：「见 `analyze_form.py` 中的字段提取算法」

多数实用脚本优先执行，更可靠、更高效。脚本执行细节见下文 [Runtime environment](#runtime-environment)。

**示例**：

````markdown  theme={null}
## Utility scripts

**analyze_form.py**: Extract all form fields from PDF

```bash
python scripts/analyze_form.py input.pdf > fields.json
```

Output format:
```json
{
  "field_name": {"type": "text", "x": 100, "y": 200},
  "signature": {"type": "sig", "x": 150, "y": 500}
}
```

**validate_boxes.py**: Check for overlapping bounding boxes

```bash
python scripts/validate_boxes.py fields.json
# Returns: "OK" or lists conflicts
```

**fill_form.py**: Apply field values to PDF

```bash
python scripts/fill_form.py input.pdf fields.json output.pdf
```
````

### 使用视觉分析

当输入可渲染为图像时，可让 Claude 对其做分析：

````markdown  theme={null}
## Form layout analysis

1. Convert PDF to images:
   ```bash
   python scripts/pdf_to_images.py form.pdf
   ```

2. Analyze each page image to identify form fields
3. Claude can see field locations and types visually
````

<Note>
  此例中，你需要自行编写 `pdf_to_images.py` 脚本。
</Note>

Claude 的视觉能力有助于理解版式与结构。

### 创建可验证的中间产物

Claude 做复杂、开放式任务时可能出错。「计划-校验-执行」模式通过让 Claude 先用结构化格式写计划、再用脚本校验、最后执行，从而尽早捕获错误。

**示例**：设想请 Claude 按电子表格更新 PDF 中 50 个表单字段。无校验时，可能引用不存在的字段、产生冲突值、漏掉必填字段或错误应用更新。

**解法**：采用上文 PDF 表单工作流，但增加中间文件 `changes.json`，在应用变更前先校验。流程为：分析 → **生成计划文件** → **校验计划** → 执行 → 验证。

**该模式为何有效：**

* **尽早发现错误**：校验在应用变更前发现问题
* **机器可验证**：脚本提供客观验证
* **计划可逆**：Claude 可迭代计划而不动原件
* **便于调试**：错误信息指向具体问题

**适用场景**：批量操作、破坏性变更、复杂校验规则、高风险操作。

**实现提示**：校验脚本应输出详尽、具体的错误信息，例如「未找到字段 'signature_date'。可用字段：customer_name、order_total、signature_date_signed」，以便 Claude 修复。

### 包依赖

技能在代码执行环境中运行，受平台限制：

* **claude.ai**：可从 npm、PyPI 安装包并从 GitHub 拉取
* **Anthropic API**：无网络访问，运行时不能安装包

在 SKILL.md 中列出所需包，并在 [code execution tool documentation](/en/docs/agents-and-tools/tool-use/code-execution-tool) 中核实其可用性。

### 运行时环境

技能在具备文件系统访问、bash 命令与代码执行能力的代码执行环境中运行。该架构的概念说明见概览中的 [The Skills architecture](/en/docs/agents-and-tools/agent-skills/overview#the-skills-architecture)。

**对你撰写方式的影响：**

**Claude 如何访问技能：**

1. **元数据预加载**：启动时，所有技能 YAML 页眉中的 name 与 description 会加载进系统提示
2. **文件按需读取**：需要时 Claude 用 bash Read 等工具从文件系统读取 SKILL.md 及其他文件
3. **脚本高效执行**：实用脚本可通过 bash 执行，无需把全文载入上下文；仅脚本输出消耗 token
4. **大文件无上下文惩罚**：参考文件、数据或文档在实际读取前不占用上下文 token

* **路径很重要**：Claude 像浏览文件系统一样浏览技能目录。使用正斜杠（`reference/guide.md`），不用反斜杠
* **文件名要有描述性**：用能体现内容的名称，如 `form_validation_rules.md`，而非 `doc2.md`
* **为可发现性组织目录**：按领域或功能划分
  * 好：`reference/finance.md`、`reference/sales.md`
  * 差：`docs/file1.md`、`docs/file2.md`
* **打包完整资源**：可包含完整 API 文档、大量示例、大型数据集；访问前无上下文惩罚
* **确定性操作用脚本**：写 `validate_form.py`，而不是让 Claude 临时生成校验代码
* **写清执行意图**：
  * 「运行 `analyze_form.py` 提取字段」（执行）
  * 「见 `analyze_form.py` 中的提取算法」（当参考读）
* **测试文件访问模式**：用真实请求验证 Claude 能否浏览你的目录结构

**示例：**

```
bigquery-skill/
├── SKILL.md (overview, points to reference files)
└── reference/
    ├── finance.md (revenue metrics)
    ├── sales.md (pipeline data)
    └── product.md (usage analytics)
```

用户问收入时，Claude 读 SKILL.md，看到 `reference/finance.md` 的引用，再调用 bash 只读该文件。sales.md 与 product.md 仍在文件系统上，在需要前占用零上下文 token。这种基于文件的模型使渐进式披露成为可能；Claude 可导航并仅为每项任务选择性加载所需内容。

技术架构完整说明见 Skills 概览中的 [How Skills work](/en/docs/agents-and-tools/agent-skills/overview#how-skills-work)。

### MCP 工具引用

若技能使用 MCP（Model Context Protocol）工具，始终使用完全限定工具名，以免出现「找不到工具」错误。

**格式**：`ServerName:tool_name`

**示例**：

```markdown  theme={null}
Use the BigQuery:bigquery_schema tool to retrieve table schemas.
Use the GitHub:create_issue tool to create issues.
```

其中：

* `BigQuery` 与 `GitHub` 为 MCP 服务器名
* `bigquery_schema` 与 `create_issue` 为各服务器内的工具名

无服务器前缀时，Claude 可能无法定位工具，尤其在多个 MCP 服务器并存时。

### 不要假定工具已安装

不要假定包默认可用：

````markdown  theme={null}
**Bad example: Assumes installation**:
"Use the pdf library to process the file."

**Good example: Explicit about dependencies**:
"Install required package: `pip install pypdf`

Then use it:
```python
from pypdf import PdfReader
reader = PdfReader("file.pdf")
```"
````

## 技术说明

### YAML 页眉要求

SKILL.md 页眉仅含 `name`（最多 64 字符）与 `description`（最多 1024 字符）。完整结构见 [Skills overview](/en/docs/agents-and-tools/agent-skills/overview#skill-structure)。

### Token 预算

为获得最佳性能，SKILL.md 正文保持在 500 行以内。超出时请用前述渐进式披露模式拆文件。架构细节见 [Skills overview](/en/docs/agents-and-tools/agent-skills/overview#how-skills-work)。

## 有效技能检查清单

分享技能前请核实：

### 核心质量

* [ ] Description 具体且含关键词
* [ ] Description 同时说明技能做什么与何时使用
* [ ] SKILL.md 正文少于 500 行
* [ ] 更多细节在单独文件中（若需要）
* [ ] 无强时效信息（或放在「旧模式」小节）
* [ ] 全文术语一致
* [ ] 示例具体，非抽象
* [ ] 文件引用仅一层深
* [ ] 渐进式披露使用得当
* [ ] 工作流步骤清晰

### 代码与脚本

* [ ] 脚本解决问题而非甩给 Claude
* [ ] 错误处理明确、有用
* [ ] 无「巫毒常数」（取值均有依据）
* [ ] 所需包已在说明中列出并核实可用
* [ ] 脚本有清晰文档
* [ ] 无 Windows 风格路径（均为正斜杠）
* [ ] 关键操作含校验/验证步骤
* [ ] 质量关键任务含反馈环

### 测试

* [ ] 至少创建三项评估
* [ ] 已在 Haiku、Sonnet、Opus 上测试
* [ ] 已在真实使用场景测试
* [ ] 已纳入团队反馈（如适用）

## 下一步

<CardGroup cols={2}>
  <Card title="Get started with Agent Skills" icon="rocket" href="/en/docs/agents-and-tools/agent-skills/quickstart">
    创建你的第一个技能
  </Card>

  <Card title="Use Skills in Claude Code" icon="terminal" href="/en/docs/claude-code/skills">
    在 Claude Code 中创建与管理技能
  </Card>

  <Card title="Use Skills with the API" icon="code" href="/en/api/skills-guide">
    通过 API 上传并以编程方式使用技能
  </Card>
</CardGroup>
