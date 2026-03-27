---
name: long-task-ucd
description: "当存在 SRS 文档但不存在 UCD 文档、设计文档与 feature-list.json 时使用 — 基于已批准 SRS 生成含文生图提示的 UI 组件设计（UCD）风格指南"
---

# UI 组件设计（UCD）风格指南生成

以已批准 SRS 为输入。分析 UI 相关需求，定义视觉风格方向，产出含文生图模型提示的 UCD 风格指南 — 使所有前端特性共享统一视觉语言。

<HARD-GATE>
在已向用户展示 UCD 风格指南并获得批准之前，不得调用任何设计技能、实现技能、编写任何代码、搭建任何项目或采取任何实现动作。此规则适用于**所有**含 UI 特性的项目。
</HARD-GATE>

## 本阶段何时适用

在 SRS 批准**之后**、设计**之前**运行。适用于：
- 已批准 SRS 含 UI 相关功能需求（FR-xxx，含面向用户的界面、页面或组件）
- `docs/plans/` 中尚无 UCD 文档（`*-ucd.md`）

**若 SRS 无 UI 特性**：宣告「SRS 中未检测到 UI 特性 — 跳过 UCD 阶段」，并立即通过 `long-task:long-task-design` 链接至设计。

## 检查清单

你必须为下列每一项创建 TodoWrite 任务并按顺序完成：

1. **阅读已批准 SRS** — 自 `docs/plans/*-srs.md`
2. **提取 UI 范围** — 识别全部 UI 相关需求与用户画像
3. **定义视觉风格方向** — 提出 2–3 种风格选项与情绪板
4. **生成组件级提示** — 各 UI 组件类型的文生图提示
5. **生成页面级提示** — 各关键页面/屏幕的文生图提示
6. **定义风格令牌** — 色板、字体、间距、图标风格
7. **展示并批准 UCD** — 非平凡项目按小节进行
8. **保存 UCD 文档** — `docs/plans/YYYY-MM-DD-<topic>-ucd.md` 并提交
9. **转入设计** — **必选子技能：** 调用 `long-task:long-task-design`

**终态为调用 long-task-design。** 不得调用任何其他技能。

## 第 1 步：阅读 SRS 并提取 UI 范围

1. 从 `docs/plans/*-srs.md` 读取已批准 SRS
2. 提取与 UI 相关的输入：
   - **用户画像** — 技术水平、无障碍需求、设备偏好
   - **含 UI 的功能需求** — 界面、页面、表单、仪表盘、数据可视化
   - **NFR 易用性** — 无障碍标准（WCAG 等级）、响应断点、国际化
   - **约束** — 品牌规范、平台限制、浏览器支持
   - **接口需求** — 外部 UI 组件、需对接的设计系统
3. 建立 **UI 清单** — 列出 SRS 隐含的全部不同屏幕/页面/组件类型
4. 若 SRS 对 UI 细节不足 → 通过 `AskUserQuestion` 询问用户后再继续

## 第 2 步：定义视觉风格方向

向用户展示 **2–3 种视觉风格选项**：

```markdown
## 风格 A：[名称]（例如：“简洁商务”、“大胆现代”、“柔和极简”）
**氛围**：[1-2 句描述整体视觉感受]
**色彩方向**：[主色倾向——暖/冷/中性，高/低对比]
**字体方向**：[衬线/无衬线，几何/人文，疏密程度]
**布局方向**：[卡片式/列表式，紧凑/留白，固定/流式]
**目标画像匹配**：[最适合哪些 SRS 用户画像]
**参考风格**：[参考的既有设计语言——Material、Ant、Apple HIG 等]

## 风格 B：[名称]
...

## 推荐：风格 [X]
**原因**：[为何它最符合 SRS 中的用户画像、约束和 NFR]
```

等待用户选择或给出方向。纳入反馈后再继续。

## 第 3 步：生成风格令牌

定义锚定整个风格体系的具体设计令牌：

### 3.1 色板

```markdown
| Token | Hex | 用途 | 对比度 |
|-------|-----|-------|----------------|
| --color-primary | #XXXXXX | 主操作、链接、激活状态 | >= 4.5:1 on white |
| --color-primary-hover | #XXXXXX | 主色 hover 状态 | |
| --color-secondary | #XXXXXX | 次操作、强调色 | >= 4.5:1 on white |
| --color-bg-primary | #XXXXXX | 主背景 | |
| --color-bg-secondary | #XXXXXX | 卡片/区块背景 | |
| --color-text-primary | #XXXXXX | 正文文本 | >= 4.5:1 on bg-primary |
| --color-text-secondary | #XXXXXX | 说明、提示文本 | >= 3:1 on bg-primary |
| --color-success | #XXXXXX | 成功状态 | |
| --color-warning | #XXXXXX | 警告状态 | |
| --color-error | #XXXXXX | 错误状态、危险操作 | |
| --color-border | #XXXXXX | 默认边框 | |
```

- 所有对比度至少满足 WCAG AA（正文 4.5:1，大字号 3:1）
- 若 SRS 要求 WCAG AAA，须为 7:1 / 4.5:1

### 3.2 字体阶梯

```markdown
| Token | 字体族 | 尺寸 | 字重 | 行高 | 用途 |
|-------|-------------|------|--------|-------------|-------|
| --font-heading-1 | [family] | [size] | [weight] | [lh] | 页面标题 |
| --font-heading-2 | [family] | [size] | [weight] | [lh] | 区块标题 |
| --font-heading-3 | [family] | [size] | [weight] | [lh] | 卡片标题 |
| --font-body | [family] | [size] | [weight] | [lh] | 正文 |
| --font-body-small | [family] | [size] | [weight] | [lh] | 注释、提示 |
| --font-label | [family] | [size] | [weight] | [lh] | 表单标签、按钮 |
| --font-code | [family] | [size] | [weight] | [lh] | 代码片段 |
```

### 3.3 间距与版式

```markdown
| Token | 值 | 用途 |
|-------|-------|-------|
| --space-xs | [value] | 紧凑型内边距 |
| --space-sm | [value] | 默认内边距 |
| --space-md | [value] | 区块间距 |
| --space-lg | [value] | 页面区块外边距 |
| --space-xl | [value] | 大型布局断点 |
| --radius-sm | [value] | 按钮、输入框 |
| --radius-md | [value] | 卡片 |
| --radius-lg | [value] | 弹窗、对话框 |
| --shadow-sm | [value] | 轻微层级感 |
| --shadow-md | [value] | 卡片、下拉层 |
| --shadow-lg | [value] | 弹窗、遮罩层 |
```

### 3.4 图标与图像

```markdown
- **图标风格**：[描边/填充/双色] [圆角/锐角] [线宽]
- **图标库**：[推荐库及版本，例如 Lucide Icons 0.263.0]
- **插画风格**：[扁平/等距/3D/手绘] [色彩处理方式]
- **摄影处理**：[若适用——滤镜、叠加、裁剪规则]
```

## 第 4 步：生成组件级提示

对清单中每种 UI 组件类型，生成可供生成式图像模型（Midjourney、DALL-E、Stable Diffusion 等）使用的 **文生图提示**。

### 提示结构

每个组件提示遵循：

```markdown
### Component: [组件名称]
**SRS Trace**: [FR-xxx, NFR-xxx]
**Variants**: [列出变体——default、hover、active、disabled、error、loading]

#### Base Prompt
> [详细的文生图提示，描述该组件在已批准风格中的视觉外观。应包含：布局结构、按名称引用的色彩 token、字体 token、间距、边框处理、阴影、状态指示。需明确比例、对齐方式与视觉层级。]

#### Variant Prompts
> **Hover 状态**：[相对基础提示的差异]
> **Error 状态**：[相对基础提示的差异]
> **Loading 状态**：[相对基础提示的差异]
> **Dark mode**（若适用）：[相对基础提示的差异]

#### Style Constraints
- [约束 1——例如：“为满足触控目标，按钮高度必须正好为 40px”]
- [约束 2——例如：“错误文本必须显示在输入框下方，不能用 tooltip”]
```

### 必选组件类型

至少为以下类型生成提示（仅当 UI 清单中确实不存在时可跳过）：

| 类别 | 组件 |
|----------|-----------|
| **Navigation** | Header/navbar, sidebar, breadcrumb, tabs, pagination |
| **Input** | 文本输入框、文本域、下拉选择、复选框、单选框、开关、日期选择器 |
| **Action** | Primary button, secondary button, icon button, link button, FAB |
| **Feedback** | Alert/toast, modal/dialog, progress bar, skeleton loader, empty state |
| **Data Display** | Table, card, list item, badge/tag, avatar, tooltip |
| **Layout** | Page shell, form layout, grid/masonry, divider |

## 第 5 步：生成页面级提示

对 UI 清单中每个关键页面/屏幕，生成 **整页文生图提示**。

### 页面提示结构

```markdown
### Page: [页面名称]
**SRS Trace**: [FR-xxx]
**User Persona**: [该页面的主要用户画像]
**Entry Points**: [用户如何进入该页面]

#### 布局说明
[描述页面布局：页头位置、内容区、侧边栏（若有）、页脚。说明网格结构以及关键断点下的响应式行为。]

#### Full-Page Prompt
> [完整页面的详细文生图提示。引用第 4 步中已定义的组件名称。描述空间关系、视觉层级、内容流向与关键交互；若适用，补充移动端/平板端的响应式说明。]

#### Key Interactions
- [交互 1——例如：“点击表格行后，在右侧打开详情面板”]
- [交互 2——例如：“表单在 blur 时校验，并显示行内错误提示”]

#### Responsive Behavior
- **Desktop (>= 1024px)**：[布局说明]
- **Tablet (768-1023px)**：[布局变化]
- **Mobile (< 768px)**：[布局变化]
```

## 第 6 步：展示并批准 UCD

非平凡项目按小节展示：

1. **视觉风格方向** — 情绪、色彩倾向、字体方向
2. **风格令牌** — 色板、字体阶梯、间距、图标
3. **组件提示** — 先生成一两个代表性组件供批准，再生成其余
4. **页面提示** — 关键页面供批准

每节展示后等待反馈，修改后再进下一节。

**简单项目**（< 3 个 UI 页面）：所有小节合并为一次批准。

## 第 7 步：保存 UCD 文档

将已批准 UCD 风格指南保存至 `docs/plans/YYYY-MM-DD-<topic>-ucd.md`。

文档结构：

```markdown
# <Project Name> — UCD Style Guide

**Date**: YYYY-MM-DD
**Status**: Approved
**SRS Reference**: docs/plans/YYYY-MM-DD-<topic>-srs.md

## 1. Visual Style Direction
[Chosen style, rationale]

## 2. Style Tokens
### 2.1 Color Palette
### 2.2 Typography Scale
### 2.3 Spacing & Layout
### 2.4 Iconography & Imagery

## 3. Component Prompts
### 3.1 [Component Name]
...

## 4. Page Prompts
### 4.1 [Page Name]
...

## 5. Style Rules & Constraints
[Cross-cutting rules: accessibility, animation, responsive, dark mode]
```

## 第 8 步：转入设计

UCD 文档保存并提交后：

1. 总结设计阶段所需关键输入：
   - **来自 SRS**：功能需求、NFR、约束
   - **来自 UCD**：风格令牌、组件目录、页面版式 → 影响设计文档中 UI/UX 小节与前端架构
2. **必选子技能：** 调用 `long-task:long-task-design` 开始设计

## UCD 阶段规模

| 项目规模 | UI 页面数 | 深度 |
|---|---|---|
| Tiny | 1–3 | 风格令牌 + 3–5 个核心组件提示 + 页面提示；单次批准 |
| Small | 3–8 | 完整风格令牌 + 所用组件的组件提示 + 全部页面提示 |
| Medium | 8–20 | 完整 UCD，含全部组件变体 + 响应式页面提示 |
| Large | 20+ | 完整 UCD + 交互状态矩阵 + 动效规约 + 深色模式变体 |

## 红旗

| 自我合理化 | 正确应对 |
|---|---|
| 「UI 简单，跳过 UCD」 | 再简单的 UI 也需要一致风格 — 跑轻量 UCD |
| 「实现时再定样式」 | 临时样式会导致跨特性视觉不一致 |
| 「用户会选 UI 库，够了」 | UI 库需要配置 — UCD 提供这些取值 |
| 「风格令牌过早」 | 现在定义比跨 20 个组件 retrofit 便宜 |
| 「直接用 Material/Ant 默认」 | 默认可作为起点，但必须文档化为明确选择 |
| 「SRS 没提颜色」 | SRS 定义 WHAT；UCD 定义视觉 HOW；UI 项目两者都要 |

## 提示撰写规则

1. **具体而非笼统** — 「圆角卡片、8px 圆角、1px solid #E5E7EB 描边、16px 内边距、白底、0 2px 4px rgba(0,0,0,0.05) 阴影」优于「好看的卡片」
2. **引用令牌而非裸值** — 提示中用令牌名，设计变更可传导：「按钮填充使用 --color-primary」
3. **写清空间关系** — 「图标 16px，距标签文字左侧 8px，垂直居中」
4. **描述状态，非仅默认** — 每个交互元素需 hover、active、disabled、error
5. **写明响应意图** — 各断点下组件/页面如何变化
6. **锚定 SRS 画像** — 提示应服务已定义用户类型（如移动优先用户需更大触摸目标）

## 集成

**由…调用：** using-long-task（存在 SRS、无 UCD、无设计、无 feature-list.json — 且 SRS 含 UI 特性）或 long-task-requirements（第 11 步链接至此）  
**需要：** `docs/plans/*-srs.md` 处已批准 SRS  
**链接至：** long-task-design（UCD 批准后）  
**产出：** `docs/plans/YYYY-MM-DD-<topic>-ucd.md`  
**被引用：**  
- long-task-design（UI/UX 小节引用 UCD 风格令牌与组件目录）  
- long-task-work（前端特性引用 UCD 保持一致性）  
- Inline Check（Worker 第 10 步对 UCD 令牌做 grep）
