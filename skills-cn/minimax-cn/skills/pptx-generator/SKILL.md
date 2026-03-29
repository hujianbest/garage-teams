---
名称： pptx 生成器
描述：“生成、编辑和阅读 PowerPoint 演示文稿。使用 PptxGenJS 从头开始创建（封面、目录、内容、章节分隔符、摘要幻灯片），通过 XML 工作流程编辑现有 PPTX，或使用 markitdown 提取文本。触发器：PPT、PPTX、PowerPoint、演示文稿、幻灯片、幻灯片、幻灯片。”
许可证：麻省理工学院
元数据：
  版本：“1.0”
  类别：生产力
  来源：
    - https://gitbrent.github.io/PptxGenJS/
    - https://github.com/microsoft/markitdown
---

# PPTX 生成器和编辑器

## 概述

该技能可以处理所有 PowerPoint 任务：阅读/分析现有演示文稿、通过 XML 操作编辑基于模板的演示文稿，以及使用 PptxGenJS 从头开始创建演示文稿。它包括完整的设计系统（调色板、字体、风格配方）以及每种幻灯片类型的详细指南。

## 快速参考

|任务|方法|
|------|----------|
|阅读/分析内容 | `python -m markitdown 演示文稿.pptx` |
|编辑或从模板创建 |请参阅[编辑演示文稿](references/editing.md) |
|从头开始创建 |请参阅下面的[从头开始创建](#creating-from-scratch-workflow) |

|项目 |价值|
|------|--------|
| **尺寸** | 10" x 5.625" (LAYOUT_16x9) | 10" x 5.625" (LAYOUT_16x9) |
| **颜色** |不带 # 的 6 字符十六进制（例如 `"FF0000"`）|
| **英文字体** | Arial（默认）或批准的替代方案 |
| **中文字体** |微软雅黑|
| **页面徽章位置** | x：9.3 英寸，y：5.1 英寸 |
| **主题键** | `主要`、`次要`、`重音`、`浅色`、`背景` |
| **形状** |矩形、椭圆形、直线、圆形_矩形 |
| **图表** |条形图、线形图、饼图、甜甜圈图、散点图、气泡图、雷达 |

## 参考文件

|文件 |内容 |
|------|----------|
| [幻灯片类型.md](参考文献/幻灯片类型.md) | 5 种幻灯片页面类型（封面、目录、章节分隔符、内容、摘要）+ 附加布局模式 |
| [设计系统.md](参考文献/设计系统.md) |调色板、字体参考、风格配方（锐利/柔和/圆形/丸状）、版式和间距 |
| [编辑.md](参考/编辑.md) |基于模板的编辑工作流程、XML 操作、格式化规则、常见陷阱 |
| [pitfalls.md](参考文献/pitfalls.md) | QA 流程、常见错误、关键 PptxGenJS 陷阱 |
| [pptxgenjs.md](参考文献/pptxgenjs.md) |完整的 PptxGenJS API 参考 |

---

## 阅读内容```bash
# Text extraction
python -m markitdown presentation.pptx
```---

## 从头开始创建 — 工作流程

**当没有可用的模板或参考演示时使用。**

### 第 1 步：研究和要求

搜索以了解用户需求——主题、受众、目的、语气、内容深度。

### 第 2 步：选择调色板和字体

使用[调色板参考](references/design-system.md#color-palette-reference) 选择与主题和受众相匹配的调色板。使用[字体参考](references/design-system.md#font-reference) 选择字体配对。

### 第 3 步：选择设计风格

使用[风格食谱](references/design-system.md#style-recipes) 选择与演示基调相匹配的视觉风格（锐利、柔和、圆润或圆粒）。

### 第 4 步：计划幻灯片大纲

将 **每张幻灯片** 准确分类为 [5 种页面类型](references/slide-types.md) 之一。规划每张幻灯片的内容和布局。确保视觉多样性——不要在幻灯片中重复相同的布局。

### 步骤 5：生成 Slide JS 文件

在 `slides/` 目录中为每张幻灯片创建一个 JS 文件。每个文件必须导出一个同步的`createSlide(pres, theme)`函数。请遵循 [幻灯片输出格式](#slide-output-format) 以及 [slide-types.md](references/slide-types.md) 中特定于类型的指南。使用子代理（如果可用）同时生成最多 5 张幻灯片。

**告诉每个子代理：**
1. 文件命名： `slides/slide-01.js`、`slides/slide-02.js` 等。
2. 图片放入：`slides/imgs/`
3.最终的PPTX进入：`slides/output/`
4. 尺寸：10" x 5.625" (LAYOUT_16x9)
5. 字体：中文 = Microsoft YaHei，英文 = Arial（或认可的替代字体）
6. 颜色：6 个字符的十六进制，不带 #（例如 `"FF0000"`）
7. 必须使用主题对象契约（参见[主题对象契约](#theme-object-contract)）
8. 必须遵循[PptxGenJS API参考](references/pptxgenjs.md)

### 步骤 6：编译成最终的 PPTX

创建 `slides/compile.js` 来组合所有幻灯片模块：```javascript
// slides/compile.js
const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

const theme = {
  primary: "22223b",    // dark color for backgrounds/text
  secondary: "4a4e69",  // secondary accent
  accent: "9a8c98",     // highlight color
  light: "c9ada7",      // light accent
  bg: "f2e9e4"          // background color
};

for (let i = 1; i <= 12; i++) {  // adjust count as needed
  const num = String(i).padStart(2, '0');
  const slideModule = require(`./slide-${num}.js`);
  slideModule.createSlide(pres, theme);
}

pres.writeFile({ fileName: './output/presentation.pptx' });
```运行：`cd幻灯片&&节点compile.js`

### 第 7 步：质量检查（必填）

请参阅 [QA 流程](references/pitfalls.md#qa-process)。

### 输出结构```
slides/
├── slide-01.js          # Slide modules
├── slide-02.js
├── ...
├── imgs/                # Images used in slides
└── output/              # Final artifacts
    └── presentation.pptx
```---

## 幻灯片输出格式

每张幻灯片都是一个**完整的、可运行的JS文件**：```javascript
// slide-01.js
const pptxgen = require("pptxgenjs");

const slideConfig = {
  type: 'cover',
  index: 1,
  title: 'Presentation Title'
};

// MUST be synchronous (not async)
function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg };

  slide.addText(slideConfig.title, {
    x: 0.5, y: 2, w: 9, h: 1.2,
    fontSize: 48, fontFace: "Arial",
    color: theme.primary, bold: true, align: "center"
  });

  return slide;
}

// Standalone preview - use slide-specific filename
if (require.main === module) {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';
  const theme = {
    primary: "22223b",
    secondary: "4a4e69",
    accent: "9a8c98",
    light: "c9ada7",
    bg: "f2e9e4"
  };
  createSlide(pres, theme);
  pres.writeFile({ fileName: "slide-01-preview.pptx" });
}

module.exports = { createSlide, slideConfig };
```---

## 主题对象契约（强制）

编译脚本传递带有这些**精确键**的主题对象：

|关键|目的|示例|
|-----|---------|---------|
| `主题.primary` |最深的颜色，标题| `"22223b"` |
| `主题.次要` |深色口音，正文 | `"4a4e69"` |
| `主题.口音` |中音口音| `“9a8c98”` |
| `主题.light` |浅色口音 | `"c9ada7"` |
| `主题.bg` |背景颜色| `"f2e9e4"` |

**切勿使用其他键名称**，例如“背景”、“文本”、“静音”、“最暗”、“最亮”。

---

## 页码徽章（必需）

所有幻灯片**除封面外**必须在右下角包含页码徽章。

- **位置**：x：9.3 英寸，y：5.1 英寸
- 仅显示当前数字（例如“3”或“03”），而不是“3/12”
- 使用调色板颜色，保持微妙

### 圆形徽章（默认）```javascript
slide.addShape(pres.shapes.OVAL, {
  x: 9.3, y: 5.1, w: 0.4, h: 0.4,
  fill: { color: theme.accent }
});
slide.addText("3", {
  x: 9.3, y: 5.1, w: 0.4, h: 0.4,
  fontSize: 12, fontFace: "Arial",
  color: "FFFFFF", bold: true,
  align: "center", valign: "middle"
});
```### 药丸徽章```javascript
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 9.1, y: 5.15, w: 0.6, h: 0.35,
  fill: { color: theme.accent },
  rectRadius: 0.15
});
slide.addText("03", {
  x: 9.1, y: 5.15, w: 0.6, h: 0.35,
  fontSize: 11, fontFace: "Arial",
  color: "FFFFFF", bold: true,
  align: "center", valign: "middle"
});
```---

## 依赖关系

- `pip install "markitdown[pptx]"` — 文本提取
- `npm install -g pptxgenjs` — 从头开始创建
- `npm install -g React-icons React React-dom Sharp` — 图标（可选）