# CJK Typography & Mixed-Script Guide

Rules for Chinese, Japanese, and Korean text in DOCX documents.

## Table of Contents

1. [Font Selection](#font-selection)
2. [Font Size Names (CJK)](#font-size-names)
3. [RunFonts Mapping](#runfonts-mapping)
4. [Punctuation & Line Breaking](#punctuation--line-breaking)
5. [Paragraph Indentation](#paragraph-indentation)
6. [Line Spacing for CJK](#line-spacing)
7. [Chinese Government Standard (GB/T 9704)](#gbt-9704)
8. [Mixed CJK + Latin Best Practices](#mixed-script)
9. [OpenXML Quick Reference](#openxml-quick-reference)

---

## Font Selection

### Recommended CJK Fonts

| Language | Serif (正文) | Sans (标题) | Notes |
|----------|-------------|-------------|-------|
| **Simplified Chinese** | 宋体 (SimSun) | 微软雅黑 (Microsoft YaHei) | YaHei for screen, SimSun for print |
| **Simplified Chinese** | 仿宋 (FangSong) | 黑体 (SimHei) | Government documents |
| **Traditional Chinese** | 新细明体 (PMingLiU) | 微软正黑体 (Microsoft JhengHei) | Taiwan standard |
| **Japanese** | MS 明朝 (MS Mincho) | MS ゴシック (MS Gothic) | Classic pairing |
| **Japanese** | 游明朝 (Yu Mincho) | 游ゴシック (Yu Gothic) | Modern, Windows 10+ |
| **Korean** | 바탕 (Batang) | 맑은 고딕 (Malgun Gothic) | Standard pairing |

### Government Document Fonts (公文)

| Element | Font | Size |
|---------|------|------|
| 标题 (title) | 小标宋 (FZXiaoBiaoSong-B05S) | 二号 (22pt) |
| 一级标题 | 黑体 (SimHei) | 三号 (16pt) |
| 二级标题 | 楷体_GB2312 (KaiTi_GB2312) | 三号 (16pt) |
| 三级标题 | 仿宋_GB2312 加粗 | 三号 (16pt) |
| 正文 (body) | 仿宋_GB2312 (FangSong_GB2312) | 三号 (16pt) |
| 附注/页码 | 宋体 (SimSun) | 四号 (14pt) |

---

## Font Size Names

CJK uses named sizes. Map to points and `w:sz` half-point values:

| 字号 | Points | `w:sz` | Common Use |
|------|--------|--------|------------|
| 初号 | 42pt | 84 | Display title |
| 小初 | 36pt | 72 | Large title |
| 一号 | 26pt | 52 | Chapter heading |
| 小一 | 24pt | 48 | Major heading |
| 二号 | 22pt | 44 | Document title (公文) |
| 小二 | 18pt | 36 | Western H1 equivalent |
| 三号 | 16pt | 32 | CJK heading / 公文 body |
| 小三 | 15pt | 30 | Sub-heading |
| 四号 | 14pt | 28 | CJK subheading |
| 小四 | 12pt | 24 | Standard body (CJK) |
| 五号 | 10.5pt | 21 | Compact CJK body |
| 小五 | 9pt | 18 | Footnotes |
| 六号 | 7.5pt | 15 | Fine print |

---

## RunFonts Mapping

OpenXML uses four font slots to handle multilingual text:```xml
<w:rFonts
  w:ascii="Calibri"        <!-- Latin characters (U+0000–U+007F) -->
  w:hAnsi="Calibri"        <!-- Latin extended, Greek, Cyrillic -->
  w:eastAsia="SimSun"      <!-- CJK Unified Ideographs, Kana, Hangul -->
  w:cs="Arial"             <!-- Arabic, Hebrew, Thai, Devanagari -->
/>
```**单词的字符分类逻辑：**

1. 字符在 CJK 范围内 → 使用 `w:eastAsia` 字体
2. 字符在复杂脚本范围内 → 使用 `w:cs` 字体
3. 字符是基本拉丁语 (ASCII) → 使用 `w:ascii` 字体
4. 其他一切 → 使用 `w:hAnsi` 字体

**关键**：`w:eastAsia` 是设置 CJK 字体的**唯一**方法。仅设置 `w:ascii` 不会影响 CJK 字符。单次运行中的混合文本会在字符级别自动切换字体 - 无需单独运行。

### 文档默认值```xml
<w:docDefaults>
  <w:rPrDefault>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="SimSun" w:cs="Arial" />
      <w:sz w:val="22" />
      <w:szCs w:val="22" />
      <w:lang w:val="en-US" w:eastAsia="zh-CN" />
    </w:rPr>
  </w:rPrDefault>
</w:docDefaults>
````w:lang w:eastAsia` 帮助 Word 解析不明确的字符（例如，CJK 和拉丁语之间共享的标点符号）。

---

## 标点符号和换行

### 全角与半角

CJK 文本使用全角标点符号：

|类型 |中日韩 |拉丁语 |
|------|-----|--------|
|期间 | 。(U+3002) | 。 |
|逗号| ，(U+FF0C) 、(U+3001) | , |
|冒号 | ：(U+FF1A) | : |
|分号 | ；(U+FF1B) | ; |
|行情 | 「」『』或「」」| “”'' |
|括号| （）(U+FF08/09) | ()|

在混合文本中，使用**周围语言上下文**的标点符号样式。

### OpenXML 控件```xml
<w:pPr>
  <w:adjustRightInd w:val="true" />   <!-- Adjust right indent for CJK punctuation -->
  <w:snapToGrid w:val="true" />        <!-- Align to document grid -->
  <w:kinsoku w:val="true" />           <!-- Enable CJK line breaking rules -->
  <w:overflowPunct w:val="true" />     <!-- Allow punctuation to overflow margins -->
</w:pPr>
```### Kinsoku 规则 (禁则处理)

防止某些字符出现在行的开头或结尾：
- **不能开始一行**:`）」』】〉》。、，！？；：`和右括号
- **不能结束一行**: `（「『【<<``和左括号

当启用“w:kinsoku”时，Word 会自动应用这些。

### 断线

- CJK 字符可以在**任意两个字符**之间断开（不需要单词边界）
- CJK 文本中的拉丁单词仍然遵循单词边界打破
- `w:wordWrap w:val="false"` 启用 CJK 风格的中断（在任何地方中断）

---

## 段落缩进

###中文标准：2字符缩进

中文正文通常使用 2 个字符的首行缩进：```xml
<w:ind w:firstLineChars="200" />  <!-- 200 = 2 characters × 100 -->
```优于具有固定 DXA 的“w:firstLine”，因为“firstLineChars”随字体大小缩放。

|缩进|价值|
|--------|--------|
| 1 个字符 | `w:firstLineChars="100"` |
| 2 个字符 | `w:firstLineChars="200"` |
| 3 个字符 | `w:firstLineChars="300"` |

---

## 行距

- 在相同磅值下，CJK 字符比拉丁字符高
- 默认的“1.0”行距对于 CJK 文本可能会感觉局促
- 推荐：中日韩+拉丁语混合为“1.15–1.5”，公文为“1.0”，固定 28 磅

### 自动间距```xml
<w:pPr>
  <w:autoSpaceDE w:val="true"/>  <!-- auto space between CJK and Latin -->
  <w:autoSpaceDN w:val="true"/>  <!-- auto space between CJK and numbers -->
</w:pPr>
```自动在 CJK 和非 CJK 字符之间添加约 ¼ em 的间距。 **建议：始终启用。**

---

## GB/T 9704

中国政府文件标准（党政机关公文格式）。这些是**严格的要求**，而不是建议。

### 页面设置

|参数|价值| OpenXML |
|------------|---------|---------|
|页面尺寸| A4（210×297毫米）|宽度=11906，高度=16838 |
|上边距| 37毫米| 2098 DXA |
|下边距| 35毫米| 1984 年 DXA |
|左边距| 28毫米| 1588 DXA |
|右边距| 26毫米|第 1474 章
|字符/行 | 28 | 28 |
|行/页 | 22 | 22 |
|行间距|固定 28pt | `line="560"` lineRule="精确" |

### 文档结构```
┌─────────────────────────────────┐
│     发文机关标志 (红头)           │  ← 小标宋 or 红色大字
│     ══════════════════ (红线)    │  ← Red #FF0000, 2pt
├─────────────────────────────────┤
│  发文字号: X机发〔2025〕X号      │  ← 仿宋 三号, centered
│                                 │
│  标题 (Title)                   │  ← 小标宋 二号, centered
│                                 │     可分多行，回行居中
│  主送机关:                      │  ← 仿宋 三号
│                                 │
│  正文 (Body)...                 │  ← 仿宋_GB2312 三号
│  一、一级标题                    │  ← 黑体 三号
│  （一）二级标题                  │  ← 楷体 三号
│  1. 三级标题                    │  ← 仿宋 三号 加粗
│  (1) 四级标题                   │  ← 仿宋 三号
│                                 │
│  附件: 1. xxx                   │  ← 仿宋 三号
│                                 │
│  发文机关署名                    │  ← 仿宋 三号
│  成文日期                       │  ← 仿宋 三号, 小写中文数字
├─────────────────────────────────┤
│  ══════════════════ (版记线)     │
│  抄送: xxx                      │  ← 仿宋 四号
│  印发机关及日期                   │  ← 仿宋 四号
└─────────────────────────────────┘
```### 编号系统```
一、        ← 黑体 (SimHei), no indentation
（一）      ← 楷体 (KaiTi), indented 2 chars
1.          ← 仿宋加粗 (FangSong Bold), indented 2 chars
(1)         ← 仿宋 (FangSong), indented 2 chars
```### 颜色

|元素|颜色 |要求 |
|--------|--------|-------------|
|所有正文 |黑色 #000000 |强制|
| 红头（机构名称）|红色#FF0000 |强制|
| 红线（分隔符）|红色#FF0000 |强制|
| 公章（公章）|红色|强制|

### 页码

- 位置：底部中心
- 格式：`-X-`（破折号-数字-破折号）
- 字体：宋体四号 (SimSun 14pt, `sz="28"`)
- 封面上没有页码（如果有）

---

## 混合脚本

### 字体大小和谐

在相同磅值下，CJK 字符看起来比拉丁字符大。补偿：

- 如果主体是 Calibri 11pt，则与 11pt 的 CJK 配对（尺寸相同 — CJK 看起来稍大，但可以接受）
- 如果需要精确的视觉匹配，CJK 可以设置小 0.5–1pt
- 在实践中，相同的点大小是标准的 - 不要过度优化

### 粗体和斜体

- **中文/日文没有真正的斜体。** 单词合成了看起来很差的倾斜
- 在 CJK 文本中使用**粗体**强调
- 使用行为号（强调点）进行传统强调：在 RunProperties 上`<w:em w:val="dot"/>`

---

## OpenXML 快速参考

### 设置东亚字体（C#）```csharp
new Run(
    new RunProperties(
        new RunFonts { EastAsia = "SimSun", Ascii = "Calibri", HighAnsi = "Calibri" },
        new FontSize { Val = "32" }  // 三号 = 16pt = sz 32
    ),
    new Text("这是正文内容")
);
```### 文档默认值 (C#)```csharp
new DocDefaults(new RunPropertiesDefault(new RunPropertiesBaseStyle(
    new RunFonts {
        Ascii = "Calibri", HighAnsi = "Calibri",
        EastAsia = "Microsoft YaHei"
    },
    new Languages { Val = "en-US", EastAsia = "zh-CN" }
)));
```### 公文 Style Definitions (C#)```csharp
// Title style — 小标宋 二号 centered
new Style(
    new StyleName { Val = "GongWen Title" },
    new BasedOn { Val = "Normal" },
    new StyleRunProperties(
        new RunFonts { EastAsia = "FZXiaoBiaoSong-B05S" },
        new FontSize { Val = "44" },  // 二号 = 22pt
        new Bold()
    ),
    new StyleParagraphProperties(
        new Justification { Val = JustificationValues.Center },
        new SpacingBetweenLines { Line = "560", LineRule = LineSpacingRuleValues.Exact }
    )
) { Type = StyleValues.Paragraph, StyleId = "GongWenTitle" };

// Body style — 仿宋_GB2312 三号
new Style(
    new StyleName { Val = "GongWen Body" },
    new StyleRunProperties(
        new RunFonts { EastAsia = "FangSong_GB2312", Ascii = "FangSong_GB2312" },
        new FontSize { Val = "32" }  // 三号 = 16pt
    ),
    new StyleParagraphProperties(
        new SpacingBetweenLines { Line = "560", LineRule = LineSpacingRuleValues.Exact }
    )
) { Type = StyleValues.Paragraph, StyleId = "GongWenBody" };
```### Emphasis Dots (着重号)```csharp
new RunProperties(new Emphasis { Val = EmphasisMarkValues.Dot });
```### 东亚文本布局```xml
<!-- Snap to grid (align CJK chars to character grid) -->
<w:snapToGrid w:val="true"/>

<!-- Two-lines-in-one (双行合一) -->
<w:eastAsianLayout w:id="1" w:combine="true"/>

<!-- Vertical text in a cell -->
<w:textDirection w:val="tbRl"/>
```
