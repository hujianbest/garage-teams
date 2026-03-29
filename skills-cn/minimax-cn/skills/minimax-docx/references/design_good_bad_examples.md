# 好的文档设计与坏的文档设计 — 具体的 OpenXML 示例

并排参考显示了常见的设计错误及其修复方法，并提供了准确的 OpenXML 参数值。使用它可以直观地了解文档看起来是专业的还是业余的。

格式：每次比较首先显示 **BAD** 版本（错误），然后显示 **GOOD** 版本（修复），并带有 OpenXML 标记和简短说明。

---

## 1. 字体大小灾难

### 1a。没有等级制度——一切都大小相同

**不好：正文=12pt，H1=12pt 粗体**```
┌──────────────────────────────────┐
│ INTRODUCTION                     │  ← 12pt bold... same visual weight
│ This is the body text of the     │  ← 12pt regular
│ report. It discusses findings    │
│ from the quarterly review.       │
│ METHODOLOGY                      │  ← Where does the section start?
│ We collected data from three     │
│ sources across the enterprise.   │
└──────────────────────────────────┘
```
```xml
<!-- H1: bold but same size as body — no visual separation -->
<w:rPr><w:b/><w:sz w:val="24"/></w:rPr>
<!-- Body -->
<w:rPr><w:sz w:val="24"/></w:rPr>
```**好：模块化比例 - body=11pt，H3=13pt，H2=16pt，H1=20pt**```
┌──────────────────────────────────┐
│                                  │
│ Introduction                     │  ← 20pt, clearly a title
│                                  │
│ This is the body text of the     │  ← 11pt, comfortable reading size
│ report. It discusses findings    │
│ from the quarterly review.       │
│                                  │
│ Methodology                      │  ← 20pt, section break is obvious
│                                  │
│ We collected data from three     │
│ sources across the enterprise.   │
└──────────────────────────────────┘
```
```xml
<!-- H1: 20pt = w:sz 40 -->
<w:rPr><w:rFonts w:ascii="Calibri Light"/><w:sz w:val="40"/></w:rPr>
<!-- H2: 16pt = w:sz 32 -->
<w:rPr><w:rFonts w:ascii="Calibri Light"/><w:sz w:val="32"/></w:rPr>
<!-- H3: 13pt = w:sz 26, bold -->
<w:rPr><w:rFonts w:ascii="Calibri"/><w:b/><w:sz w:val="26"/></w:rPr>
<!-- Body: 11pt = w:sz 22 -->
<w:rPr><w:rFonts w:ascii="Calibri"/><w:sz w:val="22"/></w:rPr>
```**为什么更好：** 清晰的大小级数（每步大约 1.25 倍的比率）让读者无需阅读任何单词即可立即识别结构。

---

### 1b。对比太强烈——儿童读物的外观

**不好：H1=28pt，主体=10pt（比率 2.8x）**```
┌──────────────────────────────────┐
│                                  │
│ QUARTERLY REPORT                 │  ← 28pt, dominates the page
│                                  │
│ This is body text set very small │  ← 10pt, straining to read
│ and the contrast with the title  │
│ makes it feel like a poster.     │
└──────────────────────────────────┘
```
```xml
<w:rPr><w:b/><w:sz w:val="56"/></w:rPr>  <!-- 28pt heading -->
<w:rPr><w:sz w:val="20"/></w:rPr>         <!-- 10pt body -->
```**好：H1=20pt，主体=11pt（比率~1.8x）**```xml
<w:rPr><w:sz w:val="40"/></w:rPr>  <!-- 20pt heading -->
<w:rPr><w:sz w:val="22"/></w:rPr>  <!-- 11pt body -->
```**为什么更好：** 标题与正文的比例在 1.5 倍和 2.0 倍之间，读起来是“结构化”而不是“喊叫”。

---

## 2. 间隔犯罪

### 2a。文本墙 - 无段落或行间距

**不好：单行间距，段落之间 0pt**```
┌──────────────────────────────────┐
│The findings indicate a strong    │
│correlation between training hours│
│and performance metrics.          │
│Further analysis revealed that    │  ← No gap — where does the new
│departments with higher budgets   │     paragraph start?
│achieved better outcomes in all   │
│measured categories.              │
└──────────────────────────────────┘
```
```xml
<w:pPr>
  <w:spacing w:line="240" w:lineRule="auto"/>  <!-- 1.0 spacing (240/240) -->
  <w:spacing w:after="0"/>                     <!-- no paragraph gap -->
</w:pPr>
```**良好：1.15 倍行距，每段后 8 磅**```
┌──────────────────────────────────┐
│The findings indicate a strong    │
│correlation between training      │  ← Slightly more air between lines
│hours and performance metrics.    │
│                                  │  ← 8pt gap signals new paragraph
│Further analysis revealed that    │
│departments with higher budgets   │
│achieved better outcomes in all   │
│measured categories.              │
└──────────────────────────────────┘
```
```xml
<w:pPr>
  <w:spacing w:line="276" w:lineRule="auto"/>  <!-- 1.15x (276/240) -->
  <w:spacing w:after="160"/>                   <!-- 8pt = 160 twips -->
</w:pPr>
```**为什么更好：** 行距给每条行呼吸的空间；段落间距将想法分开，而不浪费完整的空行。

---

### 2b。浮动标题 - 上方和下方相同的空间

**不好：标题前 12 点和标题后 12 点**```
┌──────────────────────────────────┐
│ ...end of previous section.      │
│                                  │  ← 12pt gap
│ Section Two                      │  ← Heading floats in the middle
│                                  │  ← 12pt gap
│ Start of section two content.    │
└──────────────────────────────────┘
```
```xml
<w:pPr>
  <w:spacing w:before="240" w:after="240"/>  <!-- 12pt both sides -->
</w:pPr>
```**好：标题前 24 点，标题后 8 点**```
┌──────────────────────────────────┐
│ ...end of previous section.      │
│                                  │
│                                  │  ← 24pt gap — clear section break
│ Section Two                      │  ← Heading is close to its content
│                                  │  ← 8pt gap
│ Start of section two content.    │
└──────────────────────────────────┘
```
```xml
<w:pPr>
  <w:spacing w:before="480" w:after="160"/>  <!-- 24pt before, 8pt after -->
</w:pPr>
```**为什么更好：** 邻近原则：标题属于其后面的文本，因此上方的空间较多，下方的空间较少，将其锚定到其内容。

---

### 2c。浪费的间隙——到处都有巨大的间距

**不好：每段后 24pt，包括正文**```
┌──────────────────────────────────┐
│ First paragraph of text here.    │
│                                  │
│                                  │  ← 24pt gap after every paragraph
│                                  │
│ Second paragraph of text here.   │
│                                  │
│                                  │
│                                  │
│ Third paragraph.                 │  ← Document looks mostly white space
└──────────────────────────────────┘
```
```xml
<w:spacing w:after="480"/>  <!-- 24pt = 480 twips after every paragraph -->
```**好：比例间距 - 主体 = 8 pt，H2 = 6 pt 之后，H1 = 10 pt **```xml
<!-- Body paragraph -->
<w:spacing w:after="160"/>   <!-- 8pt after body -->
<!-- H1 -->
<w:spacing w:before="480" w:after="200"/>  <!-- 24pt before, 10pt after -->
<!-- H2 -->
<w:spacing w:before="320" w:after="120"/>  <!-- 16pt before, 6pt after -->
```**为什么更好：** 间距应根据元素角色而变化，创造视觉节奏而不是均匀的间隙。

---

## 3. 保证金错误

### 3a。狭窄的边距 - 文本跑到边缘

**不好：周围有 0.5 英寸的边距**```
┌────────────────────────────────────────────────┐
│Text starts almost at the paper edge and runs   │
│all the way across making extremely long lines  │
│that are hard to track from end back to start.  │
│The eye loses its place on every line return.   │
└────────────────────────────────────────────────┘
```
```xml
<w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/>
<!-- 720 twips = 0.5in — line length ~7.5in on letter paper -->
```**良好：1 英寸边距（标准）**```xml
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
<!-- 1440 twips = 1.0in — line length ~6.5in, ideal for 11pt body -->
```**为什么更好：** 最佳行长度是 60-75 个字符。在 11 磅口径、6.5 英寸宽度下，每行大约可容纳 70 个字符。

---

### 3b。边距过度填充——看起来内容被隐藏了

**不好：短文档上的页边距为 2 英寸**```xml
<w:pgMar w:top="2880" w:right="2880" w:bottom="2880" w:left="2880"/>
<!-- 2880 twips = 2.0in — only 4.5in of text width, looks padded -->
```**良好：1 英寸标准，或 1.25 英寸正式文件**```xml
<!-- Standard -->
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
<!-- Formal / bound documents with gutter -->
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1800" w:gutter="0"/>
<!-- 1800 twips = 1.25in left for binding margin -->
```**为什么更好：** 页边距应该框定内容，而不是压倒内容。 1-1.25 英寸几乎适用于所有商业和学术文档。

---

## 4. 桌子丑陋

### 4a。监狱网格——每个牢房都有完整的边框

**不好：每个单元格的四个边都有 1pt 边框**```
┌───────┬───────┬───────┬───────┐
│ Name  │ Dept  │ Score │ Grade │
├───────┼───────┼───────┼───────┤
│ Alice │ Eng   │ 92    │ A     │
├───────┼───────┼───────┼───────┤
│ Bob   │ Sales │ 85    │ B     │
├───────┼───────┼───────┼───────┤
│ Carol │ Eng   │ 78    │ C+    │
└───────┴───────┴───────┴───────┘
```
```xml
<w:tcBorders>
  <w:top w:val="single" w:sz="4" w:color="000000"/>
  <w:left w:val="single" w:sz="4" w:color="000000"/>
  <w:bottom w:val="single" w:sz="4" w:color="000000"/>
  <w:right w:val="single" w:sz="4" w:color="000000"/>
</w:tcBorders>
```**好：三线表（三线表）——顶部厚，表头底部中等，表格底部厚**```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← 1.5pt top border
  Name    Dept    Score   Grade
──────────────────────────────────  ← 0.75pt header separator
  Alice   Eng     92      A
  Bob     Sales   85      B
  Carol   Eng     78      C+
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← 1.5pt bottom border
```
```xml
<!-- Top border of header row cells -->
<w:top w:val="single" w:sz="12" w:color="000000"/>    <!-- 1.5pt -->
<w:left w:val="nil"/><w:right w:val="nil"/>
<w:bottom w:val="single" w:sz="6" w:color="000000"/>  <!-- 0.75pt -->

<!-- Data row cells: no left/right/top borders -->
<w:top w:val="nil"/><w:left w:val="nil"/><w:right w:val="nil"/>
<w:bottom w:val="nil"/>

<!-- Last row bottom border -->
<w:bottom w:val="single" w:sz="12" w:color="000000"/> <!-- 1.5pt -->
```**为什么更好：** 去除内边框让眼睛可以自由地扫描数据。三条线提供了没有视觉混乱的结构。

---

### 4b。文本接触边框 - 无单元格填充

**坏：单元格边距为零**```
┌──────────┬──────────┐
│Name      │Department│  ← Text cramped against borders
├──────────┼──────────┤
│Alice     │Engineering│
└──────────┴──────────┘
```
```xml
<w:tcMar>
  <w:top w:w="0" w:type="dxa"/>
  <w:start w:w="0" w:type="dxa"/>
  <w:bottom w:w="0" w:type="dxa"/>
  <w:end w:w="0" w:type="dxa"/>
</w:tcMar>
```**良好：0.08 英寸垂直，0.12 英寸水平填充**```xml
<w:tcMar>
  <w:top w:w="115" w:type="dxa"/>      <!-- ~0.08in = 115 twips -->
  <w:start w:w="173" w:type="dxa"/>    <!-- ~0.12in = 173 twips -->
  <w:bottom w:w="115" w:type="dxa"/>
  <w:end w:w="173" w:type="dxa"/>
</w:tcMar>
```**为什么更好：** 填充为单元格内的文本提供了呼吸空间，使每个值更易于阅读。

---

### 4c。不可见标题 - 标题行与数据样式相同

**不好：标题行与数据无法区分**```xml
<!-- Header cell run properties — identical to data -->
<w:rPr><w:sz w:val="22"/></w:rPr>
```**好：粗体标题文本，微妙的背景填充，底部边框**```xml
<!-- Header cell run properties -->
<w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="333333"/></w:rPr>

<!-- Header cell shading -->
<w:tcPr>
  <w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>  <!-- light gray bg -->
  <w:tcBorders>
    <w:bottom w:val="single" w:sz="8" w:color="666666"/>  <!-- 1pt separator -->
  </w:tcBorders>
</w:tcPr>

<!-- Mark row as header (repeats on page break) -->
<w:trPr><w:tblHeader/></w:trPr>
```**为什么更好：** 独特的标题样式可以让读者立即找到列的含义，尤其是在跨页的长表格中。 `w:tblHeader` 元素确保标题行在每个页面上重复。

---

## 5. 字体配对失败

### 5a。视觉混乱——字体太多

**不好：一个文档中有 4 种以上字体**```xml
<!-- H1 in Impact -->
<w:rPr><w:rFonts w:ascii="Impact"/><w:sz w:val="40"/></w:rPr>
<!-- H2 in Georgia -->
<w:rPr><w:rFonts w:ascii="Georgia"/><w:sz w:val="32"/></w:rPr>
<!-- Body in Verdana -->
<w:rPr><w:rFonts w:ascii="Verdana"/><w:sz w:val="22"/></w:rPr>
<!-- Captions in Courier New -->
<w:rPr><w:rFonts w:ascii="Courier New"/><w:sz w:val="18"/></w:rPr>
```**好：一种具有粗细变化的字体系列，或两个互补的系列**```xml
<!-- H1: Calibri Light (thin weight of Calibri family) -->
<w:rPr><w:rFonts w:ascii="Calibri Light"/><w:sz w:val="40"/></w:rPr>
<!-- H2: Calibri Light -->
<w:rPr><w:rFonts w:ascii="Calibri Light"/><w:sz w:val="32"/></w:rPr>
<!-- Body: Calibri (regular weight) -->
<w:rPr><w:rFonts w:ascii="Calibri"/><w:sz w:val="22"/></w:rPr>
<!-- Captions: Calibri -->
<w:rPr><w:rFonts w:ascii="Calibri"/><w:sz w:val="18"/></w:rPr>
```**为什么更好：** 限制为一两个字体系列可以创建视觉连贯性。根据大小和重量而变化，而不是根据字体而变化。

---

### 5b。不匹配的个性——Comic Sans 遇见 Times New Roman

**不好：**```xml
<w:rPr><w:rFonts w:ascii="Comic Sans MS"/><w:sz w:val="36"/></w:rPr>  <!-- heading -->
<w:rPr><w:rFonts w:ascii="Times New Roman"/><w:sz w:val="24"/></w:rPr> <!-- body -->
```**好：具有兼容字符的字体**```xml
<w:rPr><w:rFonts w:ascii="Calibri Light"/><w:sz w:val="36"/></w:rPr>   <!-- heading -->
<w:rPr><w:rFonts w:ascii="Calibri"/><w:sz w:val="22"/></w:rPr>          <!-- body -->
```**为什么更好：** 配对字体应具有相似的正式程度和几何特征。 Comic Sans 很有趣/非正式； Times New Roman 是正式/传统的。他们发生冲突。

---

### 5c。一切都大胆——没有什么引人注目

**不好：正文、标题、说明文字等均采用粗体**```xml
<w:rPr><w:b/><w:sz w:val="40"/></w:rPr>  <!-- heading: bold -->
<w:rPr><w:b/><w:sz w:val="22"/></w:rPr>  <!-- body: also bold -->
<w:rPr><w:b/><w:sz w:val="18"/></w:rPr>  <!-- caption: still bold -->
```**好：粗体仅用于标题和关键术语**```xml
<w:rPr><w:b/><w:sz w:val="40"/></w:rPr>   <!-- H1: bold -->
<w:rPr><w:sz w:val="32"/></w:rPr>          <!-- H2: size alone is enough -->
<w:rPr><w:sz w:val="22"/></w:rPr>          <!-- body: regular weight -->
<w:rPr><w:b/><w:sz w:val="22"/></w:rPr>    <!-- key term inline: bold -->
<w:rPr><w:sz w:val="18"/></w:rPr>          <!-- caption: regular, small -->
```**为什么更好：** 当一切都被强调时，什么都没有被强调。粗体应该是一个信号，而不是默认值。

---

## 6. 颜色滥用

### 6a。彩虹标题

**不好：每个标题级别都有不同的明亮颜色**```xml
<w:rPr><w:color w:val="FF0000"/><w:sz w:val="40"/></w:rPr>  <!-- H1: red -->
<w:rPr><w:color w:val="00AA00"/><w:sz w:val="32"/></w:rPr>  <!-- H2: green -->
<w:rPr><w:color w:val="0000FF"/><w:sz w:val="26"/></w:rPr>  <!-- H3: blue -->
```**好：标题采用单一强调色，正文采用黑色或深灰色**```xml
<!-- All headings use the same muted accent -->
<w:rPr><w:color w:val="1F4E79"/><w:sz w:val="40"/></w:rPr>  <!-- H1: dark blue -->
<w:rPr><w:color w:val="1F4E79"/><w:sz w:val="32"/></w:rPr>  <!-- H2: same blue -->
<w:rPr><w:color w:val="1F4E79"/><w:sz w:val="26"/></w:rPr>  <!-- H3: same blue -->
<!-- Body in near-black -->
<w:rPr><w:color w:val="333333"/><w:sz w:val="22"/></w:rPr>
```**为什么更好：** 单一的强调色建立了品牌一致性。多种鲜艳的颜色争夺注意力，看起来不专业。

---

### 6b。低对比度 - 白底浅灰色

**不好：白色背景上的#CCCCCC 文本**```xml
<w:rPr><w:color w:val="CCCCCC"/></w:rPr>
<!-- Contrast ratio: ~1.6:1 — fails WCAG AA (minimum 4.5:1) -->
```**好：#333333 白色文字**```xml
<w:rPr><w:color w:val="333333"/></w:rPr>
<!-- Contrast ratio: ~12:1 — passes WCAG AAA -->
```**为什么更好：** 足够的对比度不仅仅是可访问性要求；而且是可访问性要求。它使每个人都更容易阅读文本，尤其是印刷文档。

---

### 6c。明亮的正文

**不好：正文颜色饱和**```xml
<w:rPr><w:color w:val="0066FF"/><w:sz w:val="22"/></w:rPr>  <!-- blue body text -->
```**好：仅为标题和内联重音保留颜色**```xml
<!-- Body: neutral dark -->
<w:rPr><w:color w:val="333333"/><w:sz w:val="22"/></w:rPr>
<!-- Hyperlink: color is functional here -->
<w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr>
```**为什么更好：** 彩色正文会导致长时间阅读时眼睛疲劳。为需要引起注意的元素（标题、链接、警告）保留颜色。

---

## 7. 列表格式问题

### 7a。页边空白处的项目符号 — 无缩进

**不好：列表项从左边距开始**```
┌──────────────────────────────────┐
│Here is a paragraph of text.     │
│• First item                      │  ← Bullet at margin, no indent
│• Second item                     │
│• Third item                      │
│Next paragraph continues here.    │
└──────────────────────────────────┘
```
```xml
<w:pPr>
  <w:ind w:left="0" w:hanging="0"/>
</w:pPr>
```**良好：0.25 英寸左侧缩进，带有子弹悬挂缩进**```
┌──────────────────────────────────┐
│Here is a paragraph of text.     │
│   • First item                   │  ← Indented, clearly a list
│   • Second item                  │
│   • Third item                   │
│Next paragraph continues here.    │
└──────────────────────────────────┘
```
```xml
<w:pPr>
  <w:ind w:left="360" w:hanging="360"/>  <!-- 0.25in = 360 twips -->
  <w:numPr>
    <w:ilvl w:val="0"/>
    <w:numId w:val="1"/>
  </w:numPr>
</w:pPr>
```对于嵌套列表，每层增加 360 缇：```xml
<!-- Level 1 -->
<w:ind w:left="720" w:hanging="360"/>   <!-- 0.5in left -->
<!-- Level 2 -->
<w:ind w:left="1080" w:hanging="360"/>  <!-- 0.75in left -->
```**为什么更好：** 缩进在视觉上将列表与正文分开，并使嵌套级别清晰。

---

### 7b。以完整段落间距列出项目

**不好：列表项与正文段落具有相同的 8-10 磅间距**```
┌──────────────────────────────────┐
│   • First item                   │
│                                  │  ← 10pt gap — looks like separate
│   • Second item                  │     paragraphs, not a list
│                                  │
│   • Third item                   │
└──────────────────────────────────┘
```
```xml
<w:spacing w:after="200"/>  <!-- 10pt after each list item -->
```**好：列表项之间的间距很小（2-4pt）**```
┌──────────────────────────────────┐
│   • First item                   │
│   • Second item                  │  ← 2pt gap — cohesive list
│   • Third item                   │
└──────────────────────────────────┘
```
```xml
<w:spacing w:after="40" w:line="276" w:lineRule="auto"/>  <!-- 2pt after -->
<!-- Or 4pt: -->
<w:spacing w:after="80"/>
```**为什么更好：** 紧密间距的组将项目作为一个单元列出，符合读者期望列表的行为方式。

---

## 8. 页眉/页脚问题

### 8a。标题文本太大 - 与正文竞争

**不好：标题为 12pt，与正文相同**```
┌──────────────────────────────────┐
│ Quarterly Report - Q3 2025       │  ← 12pt header, same as body
│──────────────────────────────────│
│ Introduction                     │
│ This is the body text...         │  ← 12pt body — header distracts
└──────────────────────────────────┘
```
```xml
<!-- Header paragraph -->
<w:rPr><w:sz w:val="24"/></w:rPr>  <!-- 12pt, same as body -->
```**好：标题为 9 磅，灰色，微妙**```
┌──────────────────────────────────┐
│ Quarterly Report - Q3 2025       │  ← 9pt, gray — present but quiet
│──────────────────────────────────│
│ Introduction                     │
│ This is the body text...         │  ← Body stands out as primary
└──────────────────────────────────┘
```
```xml
<!-- Header paragraph -->
<w:rPr>
  <w:sz w:val="18"/>                <!-- 9pt -->
  <w:color w:val="808080"/>         <!-- medium gray -->
</w:rPr>
<w:pPr>
  <w:pBdr>
    <w:bottom w:val="single" w:sz="4" w:color="D9D9D9"/>  <!-- subtle separator -->
  </w:pBdr>
</w:pPr>
```**为什么更好：** 标题是参考信息，而不是主要内容。它们应该清晰易读，但在视觉上是从属的。

---

### 8b。长文档上没有页码

**不好：20 页的文档，没有页码**```xml
<!-- Footer section: empty or missing -->
```**好：页脚中的页码，右对齐或居中**```xml
<!-- Footer paragraph with page number field -->
<w:p>
  <w:pPr>
    <w:jc w:val="center"/>
    <w:rPr><w:sz w:val="18"/><w:color w:val="808080"/></w:rPr>
  </w:pPr>
  <w:r>
    <w:rPr><w:sz w:val="18"/><w:color w:val="808080"/></w:rPr>
    <w:fldChar w:fldCharType="begin"/>
  </w:r>
  <w:r>
    <w:instrText> PAGE </w:instrText>
  </w:r>
  <w:r>
    <w:fldChar w:fldCharType="separate"/>
  </w:r>
  <w:r>
    <w:t>1</w:t>
  </w:r>
  <w:r>
    <w:fldChar w:fldCharType="end"/>
  </w:r>
</w:p>
```**为什么更好：** 页码对于任何超过 3 页的文档中的导航至关重要。读者需要参考特定页面，印刷文档需要排序机制。

---

## 9. CJK 特定错误

### 9a。使用斜体强调中文

**不好：斜体应用于中文文本**```xml
<w:rPr>
  <w:i/>
  <w:rFonts w:eastAsia="SimSun"/>
  <w:sz w:val="24"/>
</w:rPr>
```CJK 字形没有真正的斜体形式。渲染器应用了看起来破碎且丑陋的合成倾斜——角色看起来笨拙地倾斜。

**好：使用粗体或强调点（可执行号）来强调中文**```xml
<!-- Option A: Bold emphasis -->
<w:rPr>
  <w:b/>
  <w:rFonts w:eastAsia="SimHei"/>  <!-- Switch to bold-capable font -->
  <w:sz w:val="24"/>
</w:rPr>

<!-- Option B: Emphasis marks (dots under characters) -->
<w:rPr>
  <w:em w:val="dot"/>
  <w:rFonts w:eastAsia="SimSun"/>
  <w:sz w:val="24"/>
</w:rPr>
```**为什么更好：** 中国的印刷术有其自己的强调传统。粗体和强调点是原生 CJK 惯例；斜体是拉丁文字概念，无法翻译。

---

### 9b。汉字拉丁字体

**错误：仅设置 ASCII 字体，未指定 EastAsia 字体**```xml
<w:rPr>
  <w:rFonts w:ascii="Arial"/>  <!-- No eastAsia attribute -->
  <w:sz w:val="24"/>
</w:rPr>
<!-- Word falls back to a random font. Chinese characters may render
     with wrong metrics, inconsistent stroke widths, or missing glyphs. -->
```**好：显式 EastAsia 字体和 ASCII 字体**```xml
<w:rPr>
  <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei"/>
  <w:sz w:val="22"/>
</w:rPr>
```对于正式/学术中文文件：```xml
<w:rPr>
  <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"
            w:eastAsia="SimSun"/>
  <w:sz w:val="24"/>  <!-- 小四 12pt -->
</w:rPr>
```**为什么更好：** 设置 `w:eastAsia` 可确保中文字符以专为 CJK 字形设计的字体呈现，并具有正确的笔划宽度、间距和度量。

---

### 9c。密集 CJK 文本的英文行距

**不好：中文正文的行间距为 1.15 倍**```xml
<w:spacing w:line="276" w:lineRule="auto"/>  <!-- 1.15x — too tight for CJK -->
```CJK 字符比拉丁字母更高、更密。在 1.15 倍下，中文文本行显得局促且难以阅读。

**好的：1.5 倍行距或固定 28pt，CJK 正文为 12pt（小四）**```xml
<!-- Option A: 1.5x proportional -->
<w:spacing w:line="360" w:lineRule="auto"/>  <!-- 360/240 = 1.5x -->

<!-- Option B: Fixed 28pt (standard for 小四/12pt CJK body) -->
<w:spacing w:line="560" w:lineRule="exact"/>  <!-- 28pt = 560 twips -->
```For 公文 (government documents) at 三号/16pt body:```xml
<w:spacing w:line="580" w:lineRule="exact"/>  <!-- 29pt fixed line spacing -->
```**为什么更好：** CJK 字符占据整个全角，没有上升/下降提供自然间隙。额外的行距补偿，提高了密集文本块的可读性。

---

## 10. 文档整体感觉

### 学生作业与专业文档

**不好：“学生作业”——每个设置都是Word的默认设置，没有刻意的选择**```xml
<!-- Default everything: Calibri 11pt, no heading styles, 1.08 spacing -->
<w:rPr><w:rFonts w:ascii="Calibri"/><w:sz w:val="22"/></w:rPr>
<w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr>
<!-- Headings: just bold body text, no style applied -->
<w:rPr><w:b/><w:sz w:val="22"/></w:rPr>
<!-- No section breaks, no headers/footers, no page numbers -->
<!-- Tables with default full grid borders -->
<!-- No intentional color or spacing variations -->
```**好：各个层面的有意设计**```xml
<!-- Theme fonts defined -->
<w:rFonts w:asciiTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi"/>

<!-- H1: Calibri Light 20pt, dark blue, generous spacing -->
<w:pPr>
  <w:pStyle w:val="Heading1"/>
  <w:spacing w:before="480" w:after="200"/>
</w:pPr>
<w:rPr>
  <w:rFonts w:ascii="Calibri Light"/>
  <w:color w:val="1F4E79"/>
  <w:sz w:val="40"/>
</w:rPr>

<!-- H2: Calibri Light 16pt, same blue -->
<w:pPr>
  <w:pStyle w:val="Heading2"/>
  <w:spacing w:before="320" w:after="120"/>
</w:pPr>
<w:rPr>
  <w:rFonts w:ascii="Calibri Light"/>
  <w:color w:val="1F4E79"/>
  <w:sz w:val="32"/>
</w:rPr>

<!-- Body: Calibri 11pt, dark gray, 1.15 spacing, 8pt after -->
<w:pPr>
  <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
</w:pPr>
<w:rPr>
  <w:rFonts w:ascii="Calibri"/>
  <w:color w:val="333333"/>
  <w:sz w:val="22"/>
</w:rPr>

<!-- Tables: three-line style, padded cells, repeated headers -->
<!-- Headers/footers: 9pt gray with page numbers -->
<!-- Margins: 1in all around -->
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
```**为什么更好：** 专业文档源于对所有设计维度的深思熟虑、一致选择。每个元素都强化了相同的视觉语言。读者可能不会有意识地注意到好的排版，但他们会感受到可信度和可读性的差异。

---

## 快速参考：安全默认值

为大多数西方商业文件提供专业结果的价值观备忘单：

|元素|价值| OpenXML |
|--------|--------|---------|
|正文字体|口径 11 点 | `w:sz="22"` |
| H1 | Calibri 轻 20pt | `w:sz="40"` |
| H2 | Calibri 轻 16pt | `w:sz="32"` |
| H3 | Calibri 13pt 粗体 | `w:sz="26"`、`w:b` |
|机身颜色| #333333 | `w:color="333333"` |
|标题颜色 | #1F4E79 | `w:color="1F4E79"` |
|行间距| 1.15 倍 | `w:line="276" w:lineRule="auto"` |
| | 之后的段落间距8分| `w:after="160"` |
| H1间距| 24 点之前，10 点之后 | `w：之前 =“480” w：之后 =“200”` |
| H2间距|前 16 点，后 6 点 | `w:before="320" w:after="120"` |
|利润 | 1 周围 | `w:pgMar` 全部 `"1440"` |
|表格单元格填充 | 0.08 英寸/0.12 英寸 | `w:w="115"` / `w:w="173"` |
|页眉/页脚尺寸 | 9pt 灰色 | `w:sz="18" w:color="808080"` |
|列表缩进|每级 0.25 英寸 | `w:left="360" w:hanging="360"` |
|列表项间距 | 2 分后 | `w:after="40"` |

对于 CJK 文档，调整：正文字体为 SimSun/YaHei，行间距为 1.5 倍（`w:line="360"`），并在所有 `w:rFonts` 上设置 `w:eastAsia`。