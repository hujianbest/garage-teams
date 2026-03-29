# 文档排版的设计原则

为什么某些印刷选择看起来不错——感知和心理
专业文档设计背后的原因。用它来做出判断
当没有提供确切的规格时。

## 目录

1. [留白空间&呼吸室](#1-white-space--breathing-room)
2. [对比度与比例](#2-对比度--比例)
3. [邻近与分组](#3-邻近--分组)
4. [对齐与网格](#4-对齐--网格)
5.【重复与一致性】(#5-重复--一致性)
6. [视觉层次结构和流程](#6-视觉层次结构--流程)

---

## 1. 留白空间和呼吸空间

### 为什么它有效

人眼不会连续阅读。它跳起来，注视着
小词串。空白为这些注视提供了着陆区
并为读者的余光提供了一个“框架”，使每个文本块
感觉可以管理。当一页纸挤满边缘时，每看一眼都会得到更多
文本超出了工作记忆的缓冲能力，引发疲劳和回避。

关于内容密度的研究一致表明：

- **60-70% 的内容覆盖率** 感觉舒适且专业。
- **80%+** 开始感觉密集和官僚。
- **90%+** 感到压抑——读者不自觉地匆忙或跳过。
- **低于 50%** 感觉浪费或自命不凡（除非是故意的，比如诗歌）。

更大的利润也带有文化信号。学术和豪华文件的使用
宽裕的边距（1.25-1.5 英寸）。内部备忘录和草稿使用范围更窄
边距（0.75-1.0 英寸）。页边距的宽度告诉读者有多关心
在他们读到一个字之前就进入了文档。

行距有直接的生理基础：眼睛必须回溯到
每个换行符之后下一行的开始。如果线条太近，眼睛
“滑”到错误的路线上。如果距离太远，眼睛就会失去知觉
连续性。最佳位置是字体大小的 120-145%。

**经验法则：如有疑问，请添加更多空间，而不是更少。**

### 好例子```
Margins: 1 inch (1440 twips) all sides for business documents.
Line spacing: 1.15 (276 twips at 240 twips-per-line = 115%).
Paragraph spacing after: 8pt (160 twips) between body paragraphs.
```

```xml
<!-- Page margins: 1 inch = 1440 twips on all sides -->
<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"
         w:header="720" w:footer="720" w:gutter="0"/>

<!-- Body paragraph: 1.15 line spacing, 8pt after -->
<w:pPr>
  <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
</w:pPr>
```这会生成一个内容占据大约 65% 区域的页面。的
读者可以看到清晰的顶部/底部呼吸空间，并且段落清晰
不会感到断开连接。```
  Page layout (good):
  +----------------------------------+
  |           1" margin              |
  |   +------------------------+    |
  |   | Heading                |    |
  |   |                        |    |
  |   | Body text here with    |    |
  |   | comfortable spacing    |    |
  |   | between lines.         |    |
  |   |                        |    |  <- visible gap between paragraphs
  |   | Another paragraph of   |    |
  |   | body text follows.     |    |
  |   |                        |    |
  |   +------------------------+    |
  |           1" margin              |
  +----------------------------------+
```### 坏例子```xml
<!-- Cramped margins: 0.5 inch = 720 twips -->
<w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"
         w:header="360" w:footer="360" w:gutter="0"/>

<!-- No paragraph spacing, single line spacing -->
<w:pPr>
  <w:spacing w:after="0" w:line="240" w:lineRule="auto"/>
</w:pPr>
```这占据了页面的 85% 左右。文本从边到边运行，没有视觉休息站。
读者看到的是一面文字墙。```
  Page layout (bad):
  +----------------------------------+
  | Heading                          |
  | Body text crammed right up to    |
  | the margins with no spacing      |
  | between lines or paragraphs.     |
  | Another paragraph starts here    |
  | and the reader cannot tell where |
  | one idea ends and another begins |
  | because everything blurs into a  |
  | single dense block of text.      |
  +----------------------------------+
```### 快速测试

1. 在文档查看器中缩小至 50%。如果你看不到清晰的“通道”
   文本块之间有白色，间距太紧。
2. 打印测试页。将其保持在一臂的距离。文本区域应该看起来像
   一个漂浮在白色中的矩形，不填满页面。
3. 检查：正文的行距值是否至少为 264（`w:line` 为 1.1x）
   文字？如果是 240（单），则对于超过 10pt 的任何内容都太紧。

---

## 2. 对比度和比例

### 为什么它有效

大脑通过相对差异而不是绝对差异来处理视觉层次
尺寸。 11 磅正文上方的 20 磅标题可以清晰地传达“这很重要”
信号。但如果每个标题都是 20pt，每个子标题都是 19pt，那么大脑
无法区分它们——它们合并到同一层。

关键的见解是**模块化比例**：字体大小以一致的方式增长
比率。这反映了自然比例并且感觉和谐
音程这样做的原因。

常见的音阶及其特征：

|比率|名称 |人物 |进展示例（从 11 点开始）|
|--------------------|----------------|---------------------------------|--------------------------------|
| 1.200 | 1.200小三度|微妙、精致 | 11 → 13.2 → 15.8 → 19.0 |
| 1.250 | 1.250大三度 |平衡、专业| 11 → 13.75 → 17.2 → 21.5 |
| 1.333 | 1.333完美第四 |实力雄厚、权威 | 11 → 14.7 → 19.5 → 26.0 |
| 1.414 | 1.414增强型 4 号 |戏剧性的演示风格 | 11 → 15.6 → 22.0 → 31.1 |

对于大多数商业文档，1.25（大三度）效果最佳：```
Body  = 11pt  (w:sz="22")
H3    = 13pt  (w:sz="26")   -- 11 * 1.25 ≈ 13.75, round to 13
H2    = 16pt  (w:sz="32")   -- 13 * 1.25 ≈ 16.25, round to 16
H1    = 20pt  (w:sz="40")   -- 16 * 1.25 = 20
```除了尺寸之外，**重量对比**还可以在不消耗垂直方向的情况下创建层次结构
空间。常规 (400) 与粗体 (700) 在任何尺寸下均可见。半粗体 (600) 与
常规是微妙的，最好避免，除非您也改变尺寸或颜色。

**色彩对比**增加了第三个维度。深蓝色标题 (#1F3864) 反对
较柔和的深灰色正文文本 (#333333) 表示“标题”，而不需要巨大的文本
尺寸跳跃。纯黑色 (#000000) 正文文本在白色上比必要的更粗糙
背景 - #333333 或 #2D2D2D 减少眩光而不损失易读性。

### 好例子```xml
<!-- H1: 20pt, bold, dark navy -->
<w:rPr>
  <w:b/>
  <w:sz w:val="40"/>
  <w:color w:val="1F3864"/>
</w:rPr>

<!-- H2: 16pt, bold, dark navy -->
<w:rPr>
  <w:b/>
  <w:sz w:val="32"/>
  <w:color w:val="1F3864"/>
</w:rPr>

<!-- H3: 13pt, bold, dark navy -->
<w:rPr>
  <w:b/>
  <w:sz w:val="26"/>
  <w:color w:val="1F3864"/>
</w:rPr>

<!-- Body: 11pt, regular, dark gray -->
<w:rPr>
  <w:sz w:val="22"/>
  <w:color w:val="333333"/>
</w:rPr>
```

```
  Visual hierarchy (good):

  [████████████████████]        <- H1: 20pt bold navy (clearly dominant)
                                   (generous space)
  [██████████████]              <- H2: 16pt bold navy (distinct step down)
                                   (moderate space)
  [████████████]                <- H3: 13pt bold navy (smaller but still bold)
  [░░░░░░░░░░░░░░░░░░░░░░]    <- Body: 11pt regular gray
  [░░░░░░░░░░░░░░░░░░░░░░]
  [░░░░░░░░░░░░░░░░░░░░░░]
```每个楼层在视觉上都与其相邻楼层不同。您可以识别
即使在余光中也存在等级制度。

### 坏例子```xml
<!-- H1: 14pt bold black -->
<w:rPr>
  <w:b/>
  <w:sz w:val="28"/>
  <w:color w:val="000000"/>
</w:rPr>

<!-- H2: 13pt bold black -->
<w:rPr>
  <w:b/>
  <w:sz w:val="26"/>
  <w:color w:val="000000"/>
</w:rPr>

<!-- H3: 12pt bold black -->
<w:rPr>
  <w:b/>
  <w:sz w:val="24"/>
  <w:color w:val="000000"/>
</w:rPr>

<!-- Body: 12pt regular black -->
<w:rPr>
  <w:sz w:val="24"/>
  <w:color w:val="000000"/>
</w:rPr>
```问题：
- H3（12pt 粗体）和 body（12pt 常规）仅在粗细上有所不同——太微妙了。
- H1 (14pt) 到 H2 (13pt) 是 1pt 步长——在阅读距离内不可见。
- 一切都是纯黑色，因此颜色不提供区分信号。
- 级别之间的比率约为 1.07，太平坦了。

### 快速测试

1. **斜视测试**：模糊你的眼睛或从屏幕上退后一步。你可以吗
   计算标题级别的数量？如果两个级别合并，它们的对比度
   是不够的。
2. **比率检查**：将每个标题大小除以下一个较小的大小。如果有的话
   比率低于 1.15，水平看起来会过于相似。
3. **颜色检查**：当您扫视时，标题是否与正文不同
   在页面上？如果所有东西都是相同的颜色，那么你就完全依赖
   尺寸/重量，这将您的层次结构限制为约 3 个有效级别。

---

## 3. 邻近度和分组

### 为什么它有效

格式塔接近原则：靠近的物品会被感知
因为属于同一组。在文档排版中，这意味着标题
必须**接近它引入的内容**而不是它上面的内容。

如果一个标题在两个段落之间的距离相等，那么它看起来就是孤立的——
读者的眼睛不知道它是属于上面的文字还是下面的文字。修复
不对称间距：**标题前的空间较大，标题后的空间较小**。

建议的比例为 2:1 或 3:1（前空格：后空格）。

同样的原则也适用于：
- **列出项目**：项目之间的间距应小于项目之间的间距
  段落。列表中的项目是一个组，并且应该在视觉上聚集。
- **标题**：图形标题应靠近其图形，而不是浮动
  在图和下一段之间的中间。
- **表格标题**：标题靠近表格上方，有更多空间
  将标题与前面的文本分开。

### 好例子```xml
<!-- H2: 18pt before, 6pt after (3:1 ratio) -->
<w:pPr>
  <w:pStyle w:val="Heading2"/>
  <w:spacing w:before="360" w:after="120"/>
</w:pPr>

<!-- Body paragraph: 0pt before, 8pt after -->
<w:pPr>
  <w:spacing w:before="0" w:after="160"/>
</w:pPr>

<!-- List item: 0pt before, 2pt after (tight grouping) -->
<w:pPr>
  <w:pStyle w:val="ListParagraph"/>
  <w:spacing w:before="0" w:after="40"/>
</w:pPr>
```

```
  Proximity (good):

  ...end of previous section text.
                                        <- 18pt gap (w:before="360")
  ## Section Heading
                                        <- 6pt gap (w:after="120")
  First paragraph of new section
  continues here with content.
                                        <- 8pt gap (w:after="160")
  Second paragraph follows.

  The heading clearly "belongs to" the text below it.
```

```
  List grouping (good):

  Consider these factors:
    - First item                        <- 2pt gap between items
    - Second item                       <- items cluster as a group
    - Third item
                                        <- 8pt gap after list
  The next paragraph starts here.
```### 坏例子```xml
<!-- H2: 12pt before, 12pt after (1:1 ratio -- orphaned heading) -->
<w:pPr>
  <w:pStyle w:val="Heading2"/>
  <w:spacing w:before="240" w:after="240"/>
</w:pPr>

<!-- List item: same spacing as body (10pt after) -->
<w:pPr>
  <w:pStyle w:val="ListParagraph"/>
  <w:spacing w:before="0" w:after="200"/>
</w:pPr>
```

```
  Proximity (bad):

  ...end of previous section text.
                                        <- 12pt gap
  ## Section Heading
                                        <- 12pt gap (same!)
  First paragraph of new section.

  The heading floats between sections. It is unclear what it belongs to.
```

```
  List grouping (bad):

  Consider these factors:
                                        <- 10pt gap
    - First item
                                        <- 10pt gap (same as paragraphs)
    - Second item
                                        <- 10pt gap
    - Third item
                                        <- 10pt gap
  Next paragraph.

  The list does not feel like a group. Each item looks like a
  separate paragraph that happens to have a bullet.
```### 快速测试

1. **覆盖测试**：覆盖标题文字。只看空白处，
   你能说出标题属于哪个文本块吗？如果上面的间隙
   和以下是相等的，答案是“否”。
2. **数字检查**：标题上的“w:before”应至少是“w:after”的 2 倍。
   常见的良好值：before=360 / after=120，或before=240 / after=80。
3. **列表检查**：列表项上的`w:after`应小于一半
   正文段落上的“w:after”。如果正文使用 160，则列表项应使用
   40-60。

---

## 4. 对齐和网格

### 为什么它有效

对齐会产生看不见的线条，眼睛可以沿着页面向下移动。当
元素共享相同的左边缘，读者可以感知到顺序和意图。
当元素稍微未对齐（偏离几缇）时，页面看起来
即使读者无法有意识地找出原因，也很草率。

**左对齐与对齐：**

- **左对齐**（右对齐）最适合英语和其他拉丁文字
  语言。不均匀的右边缘实际上有助于阅读，因为每一行
  具有独特的轮廓，使眼睛更容易找到下一行。
  对齐的文本会导致字间距不均匀，从而产生分散注意力的“河流”
  白色垂直穿过段落。

- **对齐** 最适合 CJK 文本。中文、日文和韩文字符
  在设计上是等宽的——每个单元都占据不可见网格中的相同单元格。
  理由完美地保留了这个网格。 CJK 文本中断处右侧参差不齐
  网格，看起来不整洁。

**缩进规则：** 使用首行缩进或段落间距来分隔
段落——绝不是两者兼而有之。它们具有相同的目的（标记段落
边界）。两者同时使用会浪费空间并造成视觉卡顿。

- 西方惯例：段落间距（无缩进）更现代。
- CJK 约定：首行缩进 2 个字符是标准的。
- 学术惯例：传统的第一行缩进 0.5 英寸。

### 好例子```xml
<!-- English body: left-aligned, paragraph spacing, no indent -->
<w:pPr>
  <w:jc w:val="left"/>
  <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
  <!-- No w:ind firstLine -->
</w:pPr>

<!-- CJK body: justified, first-line indent 2 chars, no paragraph spacing -->
<w:pPr>
  <w:jc w:val="both"/>
  <w:spacing w:after="0" w:line="360" w:lineRule="auto"/>
  <w:ind w:firstLineChars="200"/>
</w:pPr>

<!-- Tab stops creating aligned columns -->
<w:pPr>
  <w:tabs>
    <w:tab w:val="left" w:pos="2880"/>   <!-- 2 inches -->
    <w:tab w:val="right" w:pos="9360"/>  <!-- 6.5 inches (right margin) -->
  </w:tabs>
</w:pPr>
```

```
  English paragraph separation (good -- spacing, no indent):

  This is the first paragraph with some text
  that wraps to a second line naturally.

  This is the second paragraph. The gap above
  clearly marks the boundary.


  CJK paragraph separation (good -- indent, no spacing):

  　　第一段正文内容从这里开始，使用两个字符
  的首行缩进来标记段落边界。
  　　第二段紧跟其后，没有段间距，但首行缩进
  清晰地标识了新段落的开始。
```### 坏例子```xml
<!-- English body: justified (creates word-spacing rivers) -->
<w:pPr>
  <w:jc w:val="both"/>
  <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
  <w:ind w:firstLine="720"/>  <!-- BOTH indent AND spacing: redundant -->
</w:pPr>

<!-- CJK body: left-aligned (breaks character grid) -->
<w:pPr>
  <w:jc w:val="left"/>
  <w:spacing w:after="200" w:line="276" w:lineRule="auto"/>
  <!-- No indent, using spacing instead -- unidiomatic for CJK -->
</w:pPr>
```问题：
- 带有窄列的对齐英文文本会产生不均匀的单词间隙。
- 同时使用首行缩进和段落间距是多余的。
- 左对齐 CJK 打破了 CJK 读者期望的字符网格。
- 基于间距的分隔的 CJK 看起来像翻译后的西方布局。

### 快速测试

1. **河流测试**：在合理的英文文本中，眯着眼睛寻找垂直
   白色条纹贯穿段落。如果您看到它们，请切换到
   左对齐或增加列宽。
2. **双重信号检查**：文档是否同时使用首行缩进和
   段落间距？如果是，请删除一个。选择 CJK/学术缩进，
   现代西部片的间距。
3. **制表符对齐**：如果您对列使用制表符，则所有制表符都跨过
   文件使用相同的位置吗？不一致的制表位会产生锯齿状
   看不见的网格线。

---

## 5. 重复和一致性

### 为什么它有效

一致性是一种信任信号。当读者看到每个 H2 看起来都一样时，
每个表格都遵循相同的模式，每个页码都位于相同的位置
当他们发现时，他们会不自觉地相信这份文件是经过精心制作的。单个
不一致——一张 H2 是 15pt 而不是 14pt，一张表格有不同的
边界——破坏了这种信任并使读者质疑内容。

一致性还可以减少认知负担。一旦读者学会了“大胆的深蓝色
= 章节标题，”他们不再花精力去识别结构
并完全专注于内容。每一个不一致都迫使他们重新评估：
“这是一种不同类型的标题，还是有人忘记应用
风格？”

实现规则很简单：**使用命名样式，而不是直接格式化。**
如果将 Heading2 定义为一种样式并将其应用到任何地方，那么一致性就是
自动。如果您手动设置每个标题的字体大小、粗体和颜色
就个人而言，不一致是不可避免的。

### 好例子```xml
<!-- Define styles once in styles.xml -->
<w:style w:type="paragraph" w:styleId="Heading2">
  <w:name w:val="heading 2"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:pPr>
    <w:keepNext/>
    <w:keepLines/>
    <w:spacing w:before="360" w:after="120"/>
    <w:outlineLvl w:val="1"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:asciiTheme="majorHAnsi" w:hAnsiTheme="majorHAnsi"/>
    <w:b/>
    <w:sz w:val="32"/>
    <w:color w:val="1F3864"/>
  </w:rPr>
</w:style>

<!-- Apply consistently: every H2 references the style -->
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading2"/>
    <!-- No direct formatting overrides -->
  </w:pPr>
  <w:r><w:t>Market Analysis</w:t></w:r>
</w:p>
```使用表格样式时，定义一次并为每个表格引用它：```xml
<!-- All tables reference the same style -->
<w:tblPr>
  <w:tblStyle w:val="GridTable4Accent1"/>
  <w:tblW w:w="0" w:type="auto"/>
</w:tblPr>
```### 坏例子```xml
<!-- First H2: manually formatted -->
<w:p>
  <w:pPr>
    <w:spacing w:before="360" w:after="120"/>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:b/>
      <w:sz w:val="32"/>
      <w:color w:val="1F3864"/>
    </w:rPr>
    <w:t>Market Analysis</w:t>
  </w:r>
</w:p>

<!-- Second H2: slightly different (16pt instead of 16pt?  No, 15pt!) -->
<w:p>
  <w:pPr>
    <w:spacing w:before="240" w:after="160"/>  <!-- different spacing! -->
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:b/>
      <w:sz w:val="30"/>   <!-- 15pt instead of 16pt! -->
      <w:color w:val="2E74B5"/>  <!-- different shade of blue! -->
    </w:rPr>
    <w:t>Financial Overview</w:t>
  </w:r>
</w:p>
```问题：
- 没有样式参考——一切都是直接格式化。
- 第二个 H2 具有不同的尺寸（30 与 32）、颜色和间距。
- 如果有 20 个标题，每个标题的漂移可能略有不同。
- 稍后更改设计意味着单独编辑每个标题。

### 快速测试

1. **风格审核**：每个段落是否都引用了`w:pStyle`？如果你发现
   仅直接格式化而没有样式的段落，这是一致性
   风险。
2. **搜索差异**：在 XML 中搜索所有使用的 `w:sz` 值
   `w:b`（粗体）。如果您发现本应相同的东西却有三种不同的尺寸
   标题级别存在不一致。
3. **表格检查**：文档中的所有表格引用是否相同
   `w:tblStyle`?如果某些表格具有手动边框定义，而其他表格则具有手动边框定义
   使用样式，文档会看起来不完整。
4. **页码**：检查页眉/页脚内容是否在
   默认节属性并由所有节继承，不重新定义
   每个部分不一致。

---

## 6. 视觉层次和流程

### 为什么它有效

精心设计的文档会引导读者的视线沿着可预测的路径：
标题位于顶部，副标题位于其下方，章节标题作为路标，正文
作为主要内容，脚注和标题作为支持细节。这个流程
镜子阅读优先——最重要的信息是最直观的
突出。

层次结构中的每个级别都必须与其相邻级别**可区分
级别**。 H1 与正文不同还不够； H1还必须
与 H2 明显不同，H2 与 H3 明显不同。如果任意两个相邻级别太
类似地，等级制度也会在那时崩溃。

有效的层次结构使用**多个同时信号**：

|水平|尺寸|重量 |颜色 |上方间距 |
|----------|---------|---------|---------|---------------|
|标题 | 26点|大胆| #1F3864 | 0（顶部）|
|字幕| 15分|常规| #4472C4 | 4分|
| H1 | 20点|大胆| #1F3864 | 24点|
| H2 | 16点|大胆| #1F3864 | 18点|
| H3 | 13点|大胆| #1F3864 | 12点|
|身体| 11点|常规| #333333 | 0分|
|标题| 9分|斜体 | #666666 | 4分|
|脚注| 9分|常规| #666666 | 0分|

注意每个级别在至少两个维度上与其相邻级别有何不同
（尺寸+重量，或尺寸+颜色，或重量+款式）。单维
差异是脆弱的，可能会被忽视。

**分节符**在长文档中创造节奏。每个之前有一个分页符
主要部分（H1）给读者一个心理重置。各节内保持一致
标题+正文模式创建了可预测的节奏，使文档变得很长
不那么吓人。

### 好例子```xml
<!-- Title: large, bold, navy, centered -->
<w:style w:type="paragraph" w:styleId="Title">
  <w:pPr>
    <w:jc w:val="center"/>
    <w:spacing w:after="80"/>
  </w:pPr>
  <w:rPr>
    <w:b/>
    <w:sz w:val="52"/>
    <w:color w:val="1F3864"/>
  </w:rPr>
</w:style>

<!-- Subtitle: medium, regular weight, lighter blue, centered -->
<w:style w:type="paragraph" w:styleId="Subtitle">
  <w:pPr>
    <w:jc w:val="center"/>
    <w:spacing w:after="320"/>
  </w:pPr>
  <w:rPr>
    <w:sz w:val="30"/>
    <w:color w:val="4472C4"/>
  </w:rPr>
</w:style>

<!-- H1: page break before, large bold navy -->
<w:style w:type="paragraph" w:styleId="Heading1">
  <w:pPr>
    <w:pageBreakBefore/>
    <w:keepNext/>
    <w:keepLines/>
    <w:spacing w:before="480" w:after="160"/>
    <w:outlineLvl w:val="0"/>
  </w:pPr>
  <w:rPr>
    <w:b/>
    <w:sz w:val="40"/>
    <w:color w:val="1F3864"/>
  </w:rPr>
</w:style>

<!-- Caption: small, italic, gray -->
<w:style w:type="paragraph" w:styleId="Caption">
  <w:pPr>
    <w:spacing w:before="80" w:after="200"/>
  </w:pPr>
  <w:rPr>
    <w:i/>
    <w:sz w:val="18"/>
    <w:color w:val="666666"/>
  </w:rPr>
</w:style>
```

```
  Visual flow (good):

  +----------------------------------+
  |                                  |
  |     ANNUAL REPORT 2025           |  <- Title: 26pt bold navy centered
  |     Acme Corporation             |  <- Subtitle: 15pt regular blue
  |                                  |
  |                                  |
  +----------------------------------+

  +----------------------------------+
  |                                  |
  |  1. Executive Summary            |  <- H1: 20pt bold navy (page break)
  |                                  |
  |  Body text introducing the       |  <- Body: 11pt regular gray
  |  main findings of the year.      |
  |                                  |
  |  1.1 Revenue Highlights          |  <- H2: 16pt bold navy
  |                                  |
  |  Revenue grew by 23% year        |  <- Body
  |  over year, driven by...         |
  |                                  |
  |  Figure 1: Revenue Growth        |  <- Caption: 9pt italic gray
  |                                  |
  +----------------------------------+

  Each level is immediately identifiable. The eye flows naturally
  from title -> heading -> body -> caption.
```### 坏例子```xml
<!-- All headings same color as body, minimal size difference -->
<w:style w:type="paragraph" w:styleId="Heading1">
  <w:rPr>
    <w:b/>
    <w:sz w:val="28"/>       <!-- 14pt -- only 3pt above body -->
    <w:color w:val="000000"/> <!-- same color as body -->
  </w:rPr>
</w:style>

<!-- Caption same size as body, not italic -->
<w:style w:type="paragraph" w:styleId="Caption">
  <w:rPr>
    <w:sz w:val="22"/>        <!-- same 11pt as body! -->
    <w:color w:val="000000"/> <!-- same color as body -->
  </w:rPr>
</w:style>

<!-- No page breaks between major sections -->
<!-- H1 has no pageBreakBefore, keepNext, or keepLines -->
```问题：
- 14 点处的 H1 距离 11 点处的身体太近（比率 1.27——可以接受）
  隔离但搭配黑色配色机身，层次感较弱）。
- 标题与正文无法区分。
- 没有分页符意味着主要部分相互渗透，没有分页符
  visual rhythm.
- 一切都是黑色的，因此颜色提供零层次信号。

### 快速测试

1. **斜视测试**：看整页时模糊你的眼睛。你
   应该看到 3-4 个不同的灰色“权重级别”。 If the page looks like
   单一的色调，层次结构过于扁平。
2. **扫描测试**：快速翻页。 Can you identify section
   每页不到一秒的边界？如果是，则视觉层次结构为
   工作。如果页面模糊在一起，则需要在 H1 处进行更强的区分。
3. **相邻级别测试**：对于每个标题级别，检查其是否不同
   从下一个级别开始，至少涉及以下两项：尺寸、重量、颜色、款式（斜体）。
   单维差异消失了。
4. **节奏测试**：在超过10页的文档中，主要部分（H1）开始吗
   on new pages?如果没有，长文档会感觉像是无差别的
   流。将 `w:pageBreakBefore` 添加到 Heading1。

---

## 摘要：决策清单

当您不确定排版选择时，请进行以下检查：

|原理|问题 | If No... |
|------------|----------|----------|
| White Space |页面是否至少有 30% 的空白？ |增加边距或间距 |
| Contrast |我可以通过眯眼来计算标题级别吗？ |增加尺寸比率（目标 1.25 倍）|
| Proximity |每个标题是否明确属于其下方的文本？ |前留空格 > 后留空格 (2:1) |
|对齐|英文左对齐、CJK 对齐吗？ | Switch alignment mode |
| Repetition |所有同级元素都使用相同的样式吗？ |用样式替换直接格式|
| Hierarchy |我可以在一定距离内查看文档结构吗？ |添加更多差异化信号 |

**当两个原则发生冲突时，请按以下顺序确定优先顺序：**

1. **可读性**（空白、行间距）——始终获胜
2. **层次结构**（对比、比例）——读者必须找到他们需要的东西
3. **一致性**（重复）——建立信任
4. **美观**（对齐、分组）——画龙点睛