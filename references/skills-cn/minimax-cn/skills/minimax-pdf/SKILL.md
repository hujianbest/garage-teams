---
名称：极小极大-pdf
描述：>
  当视觉质量和设计标识对 PDF 很重要时，请使用此技能。
  CREATE（从头开始生成）：“制作 PDF”、“生成报告”、“撰写提案”、
  “创建简历”、“精美的 PDF”、“专业文档”、“封面页”、
  “精美的 PDF”、“客户就绪文档”。
  FILL（填写表单字段）：“填写表单”、“填写此 PDF”、
  “填写表单字段”、“将值写入 PDF”、“此 PDF 有哪些字段”。
  REFORMAT（将设计应用于现有文档）：“重新格式化此文档”，“应用我们的样式”，
  “将此 Markdown/文本转换为 PDF”、“使此文档看起来不错”、“重新设置此 PDF 的样式”。
  该技能使用基于标记的设计系统：颜色、排版和间距是派生的
  从文档类型到每个页面的流程。输出已准备好打印。
  当外观很重要时，而不只是需要任何 PDF 输出时，更喜欢使用此技能。
许可证：麻省理工学院
元数据：
  版本：“1.0”
  类别：文档生成
---

# 极小极大-pdf

三项任务。一项技能。

## 在任何 CREATE 或 REFORMAT 工作之前阅读 `design/design.md`。

---

## 路由表

|用户意图 |路线 |使用的脚本 |
|---|---|---|
|从头开始生成新的 PDF | **创建** | `palette.py` → `cover.py` → `render_cover.js` → `render_body.py` → `merge.py` |
|填写/完成现有 PDF 中的表单字段 | **填充** | `fill_inspect.py` → `fill_write.py` |
|重新格式化/重新设计现有文档的样式 | **重新格式化** | `reformat_parse.py` → 然后完整的 CREATE 管道 |

**规则：** 当在 CREATE 和 REFORMAT 之间有疑问时，询问用户是否有现有文档可以开始。如果是 → 重新格式化。如果没有 → 创建。

---

## 路线 A：创建

完整流程 — 内容 → 设计标记 → 封面 → 正文 → 合并 PDF。```bash
bash scripts/make.sh run \
  --title "Q3 Strategy Review" --type proposal \
  --author "Strategy Team" --date "October 2025" \
  --accent "#2D5F8A" \
  --content content.json --out report.pdf
```**文档类型：** `报告` · `提案` · `简历` · `作品集` · `学术` · `一般` · `最小` · `条纹` · `对角线` · `框架` · `社论` · `杂志` · `暗室` · `终端` · `海报`

|类型 |封面图案|视觉识别|
|---|---|---|
| `报告` | `全出血` |暗背景、点网格、Playfair 显示 |
| `提案` | `分裂` |左面板+右几何，Syne |
| `简历` | `印刷` |超大首字，DM Serif 显示 |
| `投资组合` | `大气` |近乎黑色的放射状光芒，弗朗西斯 |
| `学术` | `印刷` |浅色背景、古典衬线、EB Garamond |
| `一般` | `全出血` |深色石板色，服装 |
| `最小` | `最小` |白色 + 单 8px 强调条，Cormorant Garamond |
| `条纹` | `条纹` | 3 个大胆的水平色带，Barlow Condensed |
| `对角线` | `对角线` | SVG 斜切，深色/浅色两半，蒙特塞拉特 |
| `框架` | `框架` |镶边、角饰、鸬鹚|
| `社论` | `社论` |幽灵字母，全大写标题，Bebas Neue |
| `杂志` | `杂志` |暖奶油背景，居中堆栈，英雄图像，Playfair 显示 |
| `暗室` | `暗室` |海军背景、居中堆栈、灰度图像、Playfair 显示 |
| `终端` | `终端` |近黑色、网格线、等宽、霓虹绿 |
| `海报` | `海报` |白色背景，厚侧边栏，超大标题，Barlow Condensed |

覆盖额外内容（通过“--abstract”、“--cover-image”注入代币）：
- `--abstract "text"` — 封面上的抽象文本块（杂志/暗室）
- `--cover-image "url"` — 英雄图片 URL/路径（杂志、暗室、海报）

**颜色覆盖 - 始终根据文档内容选择这些：**
- `--accent "#HEX"` — 覆盖强调色； `accent_lt` 是通过淡化为白色而自动派生的
- `--cover-bg "#HEX"` — 覆盖封面背景颜色

**强调颜色选择指南：**

您对强调色拥有创意权威。从文档的语义上下文（标题、行业、目的、受众）中选择它，而不是从通用的“安全”选择中选择。重音符号出现在章节规则、标注栏、表格标题和封面上：它承载着文档的视觉标识。

|背景 |建议的口音范围 |
|---|---|
|法律/合规/财务|深海军蓝`#1C3A5E`、木炭色`#2E3440`、板岩色`#3D4C5E` |
|医疗保健/医疗|青绿色`#2A6B5A`，冷绿色`#3A7D6A` |
|技术/工程|钢蓝色`#2D5F8A`，靛蓝色`#3D4F8A` |
|环境/可持续发展|森林`#2E5E3A`，橄榄色`#4A5E2A` |
|创意/艺术/文化|勃艮第`#6B2A35`，李子`#5A2A6B`，赤土色`#8A3A2A` |
|学术/研究|深青色`#2A5A6B`，图书馆蓝`#2A4A6B` |
|企业/中立|板岩`#3D4A5A`，石墨`#444C56` |
|豪华/高级|暖黑色`#1A1208`，深古铜色`#4A3820` |

**规则：** 选择深思熟虑的设计师会为此特定文档选择的颜色 - 而不是该类型的默认颜色。柔和、不饱和的色调效果最佳；避免生动的初选。如有疑问，请选择颜色更深、更中性的颜色。

**content.json 块类型：**

|块|用途 |关键领域 |
|---|---|---|
| `h1` |章节标题 + 重音规则 | `文本` |
| `h2` |小节标题 | `文本` |
| `h3` |子小节（粗体）| `文本` |
| `身体` |合理的段落；支持 `<b>` `<i>` 标记 | `文本` |
| `子弹` |无序列表项（• 前缀） | `文本` |
| `编号` |有序列表项 - 非编号块上的计数器自动重置 | `文本` |
| `标注` |突出显示的洞察框带有强调左栏 | `文本` |
| `表` |数据表 — 重音标题、交替行色调 | `headers`、`rows`、`col_widths`？、`caption`？ |
| `图像` |嵌入图像缩放至列宽 | `路径`/`src`，`标题`？ |
| `图` |带有自动编号“图 N：”标题的图像 | `路径`/`src`，`标题`？ |
| `代码` |带有重音左边框的等宽代码块 | “文本”、“语言”？ |
| `数学` |显示数学 — 通过 matplotlib mathtext 的 LaTeX 语法 | ‘文本’、‘标签’？、‘标题’？ |
| `图表` |使用 matplotlib 渲染的条形图/折线图/饼图 | `chart_type`、`labels`、`datasets`、`title`？、`x_label`？、`y_label`？、`caption`？、`figure`？ |
| `流程图` |通过 matplotlib 绘制节点 + 边的流程图 | `节点`、`边`、`标题`？、`图`？ |
| `参考书目` |带有悬挂缩进的编号参考列表 | `项目` [{id, text}]，`标题`？ |
| `分隔线` |强调色全角标尺| — |
| `标题` |小静音标签| `文本` |
| `分页符` |强制创建新页面 | — |
| `垫片` |垂直空白 | `pt`（默认 12）|**图表/流程图模式：**```json
{"type":"chart","chart_type":"bar","labels":["Q1","Q2","Q3","Q4"],
 "datasets":[{"label":"Revenue","values":[120,145,132,178]}],"caption":"Q results"}

{"type":"flowchart",
 "nodes":[{"id":"s","label":"Start","shape":"oval"},
          {"id":"p","label":"Process","shape":"rect"},
          {"id":"d","label":"Valid?","shape":"diamond"},
          {"id":"e","label":"End","shape":"oval"}],
 "edges":[{"from":"s","to":"p"},{"from":"p","to":"d"},
          {"from":"d","to":"e","label":"Yes"},{"from":"d","to":"p","label":"No"}]}

{"type":"bibliography","items":[
  {"id":"1","text":"Author (Year). Title. Publisher."}]}
```---

## 路线 B：填充

填写现有 PDF 中的表单字段，无需更改布局或设计。```bash
# Step 1: inspect
python3 scripts/fill_inspect.py --input form.pdf

# Step 2: fill
python3 scripts/fill_write.py --input form.pdf --out filled.pdf \
  --values '{"FirstName": "Jane", "Agree": "true", "Country": "US"}'
```|字段类型|值格式 |
|---|---|
| `文本` |任何字符串 |
| `复选框` | `"true"` 或 `"false"` |
| `下拉菜单` |必须与检查输出中的选择值匹配 |
| `收音机` |必须匹配单选值（通常以“/”开头）|

始终首先运行“fill_inspect.py”以获取准确的字段名称。

---

## 路线 C：重新格式化

解析现有文档 → content.json → CREATE pipeline。```bash
bash scripts/make.sh reformat \
  --input source.md --title "My Report" --type report --out output.pdf
```**支持的输入格式：** `.md` `.txt` `.pdf` `.json`

---

## 环境```bash
bash scripts/make.sh check   # verify all deps
bash scripts/make.sh fix     # auto-install missing deps
bash scripts/make.sh demo    # build a sample PDF
```|工具|使用者 |安装 |
|---|---|---|
| Python 3.9+ |所有 `.py` 脚本 |系统|
| `报告实验室` | `render_body.py` | `pip install reportlab` |
| `pypdf` |填充、合并、重新格式化 | `pip 安装 pypdf` |
| Node.js 18+ | `render_cover.js` |系统|
| `剧作家` + Chromium | `render_cover.js` | `npm install -g playwright && npx playwright 安装 chromium` |