# 财务格式和输出标准 — 完整的代理指南

> 本文档是代理将专业财务格式应用于 xlsx 文件时的完整参考手册。所有操作都针对“xl/styles.xml”的直接 XML 操作，而不使用 openpyxl。每个操作步骤都提供现成的 XML 片段。

---

## 1. 何时使用此路径

本文档（FORMAT路径）适用于以下两种场景：

**场景 A — 现有文件的专用格式**
用户提供现有的 xlsx 文件并请求应用或统一财务建模格式标准。起点是解压文件，审核现有的“styles.xml”，然后附加缺少的样式并批量更新单元格“s”属性。没有修改单元格值或公式。

**场景 B — 在创建/编辑后应用格式标准**
完成数据输入或公式编写后，最后一步将应用格式。此时，“styles.xml”可能来自minimal_xlsx模板（预定义了13个样式槽）或来自用户文件。无论哪种情况，都遵循“仅追加，绝不修改现有 xf 条目”的原则。

**不适用**：仅读取或分析文件内容（使用READ路径）；修改公式或数据（使用编辑路径）。

---

## 2. 财务格式语义系统

### 2.1 字体颜色=单元格角色（颜色=角色）

财务建模的主要约定：**字体颜色编码单元格的角色，而不是装饰**。审阅者可以通过查看颜色来确定哪些单元格是可调整参数以及哪些单元格是模型计算的结果。这是一个全行业的会议（随后是投资银行、四大银行和企业财务团队）。

|角色 |字体颜色 | AARRGBB |使用案例|
|------|------------|----------|----------|
|硬编码输入/假设 |蓝色| `000000FF` |增长率、贴现率、税率和其他用户可修改的参数|
|公式/计算结果|黑色| `00000000` |所有包含 `<f>` 元素的单元格 |
|同一工作簿跨表参考 |绿色| `00008000` |公式以“SheetName!”开头的单元格 |
|外部文件链接 |红色| `00FF0000` |公式包含“[FileName.xlsx]”的单元格（标记为脆弱链接）|
|标签/文字|黑色（默认）|主题色 |行标签、类别标题 |
|需要审查的关键假设|蓝色字体+黄色填充|字体`000000FF`/填充`00FFFF00` |暂定值，参数待确认 |

**决策树**：```
Does the cell contain a <f> element?
  +-- Yes -> Does the formula start with [FileName]?
  |           +-- Yes -> Red (external link)
  |           +-- No  -> Does the formula contain SheetName!?
  |                       +-- Yes -> Green (cross-sheet reference)
  |                       +-- No  -> Black (same-sheet formula)
  +-- No  -> Is the value a user-adjustable parameter?
              +-- Yes -> Blue (input/assumption)
              +-- No  -> Black default (label)
```**严格禁止**：蓝色字体+`<f>`元素共存（颜色角色矛盾——必须纠正）。

### 2.2 数字格式矩阵

|数据类型 |格式代码 | numFmtId |显示示例 |适用场景 |
|----------|----------|----------|------------------|------------------------|
|标准货币（整美元）| `$#,##0;($#,##0);"-"` | 164 | 164 $1,234 / ($1,234) / - |损益表、资产负债表金额行 |
|标准货币（以分计）| `$#,##0.00;($#,##0.00);"-"` | 169 | 169 $1,234.56 / ($1,234.56) / - |单价、详细成本 |
|千 (K) | `#,##0,"K"` | 171 | 171 1,234K |管理报告的简化显示 |
|百万 (M) | `#,##0,,"M"` | 172 | 172 1M |宏观层面的汇总行|
|百分比（1 位小数）| `0.0%` | 165 | 165 12.5% |增长率、毛利率|
|百分比（2 位小数）| `0.00%` | 170 | 170 12.50% | IRR，精确利率|
|倍数/估值乘数| `0.0x` | 166 | 166 8.5 倍 | EV/EBITDA、市盈率 |
|整数（千位分隔符）| `#,##0` | 167 | 167 12,345 | 12,345员工人数、单位数量 |
|年份| `0` | 1（内置，无需声明）| 2024 | 2024列标题年份，防止 2,024 |
|日期 | `年/月/日` | 14（内置，无需声明）| 2026 年 3 月 21 日 |时间表 |
|一般文字 |一般| 0（内置，无需声明）| — |标签行、单元格没有格式要求 |

numFmtId 169–172 是自定义格式，需要附加到在minimal_xlsx 模板中预定义的 4 种格式 (164–167) 之外。附加时，根据规则分配ID（参见第3.4节）。

**内置格式 ID 不需要在 `<numFmts>` 中声明**（ID 0–163 内置于 Excel/LibreOffice 中；只需引用 `<xf>` 中的 numFmtId）：

| numFmtId |格式代码 |描述 |
|----------|------------|-------------|
| 0 |一般|通用格式|
| 1 | `0` |整数，无千位分隔符（多年来一直使用此 ID）|
| 3 | `#,##0` |千位分隔的整数（无小数） |
| 9 | `0%` |百分比整数 |
| 10 | 10 `0.00%` |保留两位小数的百分比 |
| 14 | 14 `年/月/日` |短日期 |

### 2.3 负数显示标准

财务报告对负数有两种主流惯例 - 选择一种并在整个工作簿中**保持一致性**：

**括号风格（投资银行标准，建议用于外部交付成果）**```
Positive: $1,234    Negative: ($1,234)    Zero: -
formatCode: $#,##0;($#,##0);"-"
```**红色减号样式（适合内部运营分析报告）**```
Positive: $1,234    Negative: -$1,234 (red)
formatCode: $#,##0;[Red]-$#,##0;"-"
```规则：一旦确定了样式，就在整个工作簿中维护它。请勿在同一工作簿中混合使用两种负数显示样式。

### 2.4 零值显示标准

在金融模型中，“0”和“无数据”具有不同的语义，并且应该在视觉上有所区别：

|场景|推荐显示器 |格式代码第三段 |
|----------|--------------------|--------------------------|
|稀疏矩阵（大多数行都有零值周期）|破折号`-` | `"-"` |
|数量很重要（零本身就有意义）| `0` | `0` 或省略 |
|占位符行（明确为空）|留空 |不要写入单元格 |

四段格式语法：`正格式;负格式;零值格式;文本格式`

零作为破折号：`$#,##0;($#,##0);"-"`
零保留为 0：`#,##0;(#,##0);0`

---

## 3. styles.xml 手术操作

### 3.1 审核现有样式：了解 cellXfs 间接引用链

单元格的“s”属性指向“cellXfs”中的位置索引（从 0 开始），“cellXfs”中的每个“<xf>”条目通过“fontId”、“fillId”、“borderId”和“numFmtId”引用其各自的定义库。

参考链图：```
Cell <c s="6">
    | Look up cellXfs by 0-based index
cellXfs[6] -> numFmtId="164" fontId="2" fillId="0" borderId="0"
    |            |               |          |
numFmts         fonts[2]      fills[0]   borders[0]
id=164          color=00000000  (no fill)  (no border)
$#,##0...       black
```审核步骤：

**步骤 1**：读取 `<numFmts>` 并记录所有声明的自定义格式及其 ID：```xml
<numFmts count="4">
  <numFmt numFmtId="164" formatCode="$#,##0;($#,##0);&quot;-&quot;"/>
  <numFmt numFmtId="165" formatCode="0.0%"/>
  <numFmt numFmtId="166" formatCode="0.0x"/>
  <numFmt numFmtId="167" formatCode="#,##0"/>
</numFmts>
```记录：当前最大自定义numFmtId = 167，下一个可用ID = 168。

**步骤 2**：读取 `<fonts>` 并通过基于 0 的索引列出每个 `<font>` 及其颜色和样式：```
fontId=0 -> No explicit color (theme default black)
fontId=1 -> color rgb="000000FF" (blue, input role)
fontId=2 -> color rgb="00000000" (black, formula role)
fontId=3 -> color rgb="00008000" (green, cross-sheet reference role)
fontId=4 -> <b/> + color rgb="00000000" (bold black, header)
```**步骤 3**：读取 `<fills>` 并确认 fills[0] 和 fills[1] 是规范规定的保留条目（切勿删除）：```
fillId=0 -> patternType="none" (spec-mandated)
fillId=1 -> patternType="gray125" (spec-mandated)
fillId=2 -> Yellow highlight (if present)
```**步骤 4**：读取 `<cellXfs>` 并按基于 0 的索引及其组合列出每个 `<xf>` 条目：```
index 0 -> numFmtId=0,   fontId=0, fillId=0 -> Default style
index 1 -> numFmtId=0,   fontId=1, fillId=0 -> Blue font general (input)
index 5 -> numFmtId=164, fontId=1, fillId=0 -> Blue font currency (currency input)
index 6 -> numFmtId=164, fontId=2, fillId=0 -> Black font currency (currency formula)
...
```**步骤5**：验证所有计数属性是否与实际元素数量匹配（计数不匹配将导致Excel拒绝打开文件）。

### 3.2 安全追加新样式（黄金法则：仅追加，切勿修改现有 xf）

**切勿修改现有的 `<xf>` 条目**。修改将影响所有已引用该索引的单元格，从而破坏现有格式。仅在末尾添加新条目。

附加新样式的完整原子操作序列（必须执行所有 5 个步骤）：

**步骤 1**：确定是否需要新的 `<numFmt>`

内置格式 (ID 0–163) 跳过此步骤。自定义格式附加到 `<numFmts>` 的末尾：```xml
<numFmts count="5">  <!-- count +1 -->
  <!-- Keep existing entries unchanged -->
  <numFmt numFmtId="164" formatCode="$#,##0;($#,##0);&quot;-&quot;"/>
  <numFmt numFmtId="165" formatCode="0.0%"/>
  <numFmt numFmtId="166" formatCode="0.0x"/>
  <numFmt numFmtId="167" formatCode="#,##0"/>
  <!-- Newly appended -->
  <numFmt numFmtId="168" formatCode="$#,##0.00;($#,##0.00);&quot;-&quot;"/>
</numFmts>
```**步骤 2**：确定是否需要新的 `<font>`

检查现有字体是否已包含匹配的颜色+样式组合。如果没有，请附加到 `<fonts>` 的末尾：```xml
<fonts count="6">  <!-- count +1 -->
  <!-- Keep existing entries unchanged -->
  ...
  <!-- Newly appended: red font (external link role), new fontId = 5 -->
  <font>
    <sz val="11"/>
    <name val="Calibri"/>
    <color rgb="00FF0000"/>
  </font>
</fonts>
```新fontId = 追加前的计数值（原count=5时，新fontId=5）。

**步骤 3**：确定是否需要新的 `<fill>`

如果需要新的背景颜色，请附加到 `<fills>` 的末尾（注意：决不能修改 fills[0] 和 fills[1]）：```xml
<fills count="4">  <!-- count +1 -->
  <fill><patternFill patternType="none"/></fill>       <!-- 0: spec-mandated -->
  <fill><patternFill patternType="gray125"/></fill>    <!-- 1: spec-mandated -->
  <fill>                                               <!-- 2: yellow highlight -->
    <patternFill patternType="solid">
      <fgColor rgb="00FFFF00"/>
      <bgColor indexed="64"/>
    </patternFill>
  </fill>
  <!-- Newly appended: light gray fill (projection period distinction), new fillId = 3 -->
  <fill>
    <patternFill patternType="solid">
      <fgColor rgb="00D3D3D3"/>
      <bgColor indexed="64"/>
    </patternFill>
  </fill>
</fills>
```**步骤 4**：在“<cellXfs>”末尾附加新的“<xf>”组合```xml
<cellXfs count="14">  <!-- count +1 -->
  <!-- Keep existing entries 0-12 unchanged -->
  ...
  <!-- Newly appended index=13: currency with cents formula (black font + numFmtId=168) -->
  <xf numFmtId="168" fontId="2" fillId="0" borderId="0" xfId="0"
      applyFont="1" applyNumberFormat="1"/>
</cellXfs>
```新样式索引=追加前的计数值（原计数=13时，新索引=13）。

**第五步**：记录新的风格索引；随后将工作表 XML 中相应单元格的“s”属性设置为此值。

### 3.3 AARRGGBB 颜色格式说明

OOXML 的 `rgb` 属性使用 **8 位十六进制 AARRGBB** 格式（不是 HTML 的 6 位 RRGGBB）：```
AA  RR  GG  BB
|   |   |   |
Alpha Red Green Blue
```- Alpha 通道：`00` = 完全不透明（正常使用值）； `FF` = 完全透明（不可见，切勿使用此）
- 金融颜色标准始终使用“00”作为 Alpha 前缀

|颜色 | AARRGBB |对应角色|
|--------|----------|--------------------|
|蓝色（输入）| `000000FF` |硬编码假设 |
|黑色（配方）| `00000000` |计算结果|
|绿色（跨表参考）| `00008000` |同一工作簿跨工作表 |
|红色（外部链接）| `00FF0000` |对其他文件的引用 |
|黄色（需审核填写）| `00FFFF00` |关键假设亮点 |
|浅灰色（投影期填充）| `00D3D3D3` |区分历史时期与预测时期|
|白色| `00FFFFFF` |纯白色填充|

**常见错误**：将HTML格式`#0000FF`误写为`FF0000FF`（Alpha=FF使颜色完全透明不可见）。正确格式：`000000FF`。

### 3.4 numFmtId 分配规则```
ID 0-163    -> Excel/LibreOffice built-in formats, no declaration needed in <numFmts>, reference directly in <xf>
ID 164+     -> Custom formats, must be explicitly declared as <numFmt> elements in <numFmts>
```分配新 ID 的规则：
1. 读取当前`<numFmts>`中所有`numFmtId`属性值
2.取最大值+1作为下一个自定义格式ID
3、不要重复使用已有的ID；不要跳过数字

imals_xlsx 模板预定义了 ID：164、165、166、167。下一个可用的 ID 是 168。

---

## 4. 预定义样式索引完整参考表（13 个槽位）

以下是在minimal_xlsx模板的“styles.xml”中预定义的13个样式槽（cellXfs索引0-12），可以直接在sheet XML中的单元格“s”属性中引用：

|索引 |语义角色|字体颜色 |填写| numFmtId |格式显示|典型用途|
|--------|--------------|------------|------|---------|----------------|-------------|
| **0** |默认样式 |主题黑|无 | 0 |一般|不需要特殊格式的单元格|
| **1** |输入/假设（一般） |蓝色`000000FF` |无 | 0 |一般|文本类型假设、标志 |
| **2** |公式/计算结果（一般）|黑色`00000000` |无 | 0 |一般|文本连接公式、非数值计算 |
| **3** |跨表参考（一般）|绿色`00008000` |无 | 0 |一般|从跨工作表中提取的值（通用格式）|
| **4** |标题（粗体）|大胆的黑色|无 | 0 |一般|行/列标题 |
| **5** |货币输入|蓝色`000000FF` |无 | 164 | 164 $1,234 / ($1,234) / - |假设区域中的输入量 |
| **6** |货币公式|黑色`00000000` |无 | 164 | 164 $1,234 / ($1,234) / - |模型区域中的金额计算（收入、EBITDA）|
| **7** |百分比输入 |蓝色`000000FF` |无 | 165 | 165 12.5% |假设区域中的速率输入（增长率、毛利率假设）|
| **8** |百分比公式|黑色`00000000` |无 | 165 | 165 12.5% |模型区费率计算（实际毛利率）|
| **9** |整数（逗号）输入 |蓝色`000000FF` |无 | 167 | 167 12,345 | 12,345假设区域中的数量输入（员工人数）|
| **10** |整数（逗号）公式 |黑色`00000000` |无 | 167 | 167 12,345 | 12,345模型区的数量计算 |
| **11** |输入年份 |蓝色`000000FF` |无 | 1 | 2024 | 2024列标题年份（无千位分隔符）|
| **12** |关键假设亮点 |蓝色`000000FF` |黄色`00FFFF00` | 0 |一般|关键参数待审核或确认|

**选型指南**：
- 确定“输入”与“公式” -> 选择奇数（输入/蓝色）或偶数（公式/黑色）配对插槽
- 确定数据类型->选择对应的货币(5/6)/百分比(7/8)/整数(9/10)/年份(11)槽
- 需要数字格式的跨表参考 -> 附加新的绿色 + 数字格式组合（参见第 5.4 节）
- 参数待审核 -> 索引 12

---

## 5. 假设分离原则：XML 级实现

### 5.1 结构设计

假设分离原则： **输入假设集中在专用区域（表或块）；模型计算区域仅包含公式，没有硬编码值**。

推荐结构：```
Workbook sheet layout
  sheet 1 "Assumptions"  -> All blue-font cells (style 1/5/7/9/11/12)
  sheet 2 "Model"        -> All black or green-font cells (style 2/3/4/6/8/10)
```简单模型的同表分区方法：```
Rows 1-5:   [Assumptions block - blue font]
Row 6:      [Empty row separator]
Rows 7+:    [Model block - black/green font formulas referencing assumptions area]
```### 5.2 假设区域 XML 示例```xml
<!-- Assumptions sheet (sheet1.xml) example -->

<!-- Row 1: Block title -->
<row r="1">
  <c r="A1" s="4" t="inlineStr"><is><t>Model Assumptions</t></is></c>
</row>

<!-- Row 2: Growth rate assumption - blue font percentage input, s="7" -->
<row r="2">
  <c r="A2" t="inlineStr"><is><t>Revenue Growth Rate</t></is></c>
  <c r="B2" s="7"><v>0.08</v></c>
</row>

<!-- Row 3: Gross margin assumption - blue font percentage input, s="7" -->
<row r="3">
  <c r="A3" t="inlineStr"><is><t>Gross Margin</t></is></c>
  <c r="B3" s="7"><v>0.65</v></c>
</row>

<!-- Row 4: Base revenue - blue font currency input, s="5" -->
<row r="4">
  <c r="A4" t="inlineStr"><is><t>Base Revenue (Year 0)</t></is></c>
  <c r="B4" s="5"><v>1000000</v></c>
</row>

<!-- Row 5: Key assumption (pending review) - blue font yellow fill, s="12" -->
<row r="5">
  <c r="A5" t="inlineStr"><is><t>Terminal Growth Rate</t></is></c>
  <c r="B5" s="12"><v>0.03</v></c>
</row>
```### 5.3 模型区域 XML 示例（引用假设区域）```xml
<!-- Model sheet (sheet2.xml) example -->

<!-- Row 1: Column headers (years) - bold header, s="4"; year cells, s="11" -->
<row r="1">
  <c r="A1" s="4" t="inlineStr"><is><t>Metric</t></is></c>
  <c r="B1" s="11"><v>2024</v></c>
  <c r="C1" s="11"><v>2025</v></c>
  <c r="D1" s="11"><v>2026</v></c>
</row>

<!-- Row 2: Revenue row -->
<row r="2">
  <c r="A2" t="inlineStr"><is><t>Revenue</t></is></c>
  <!-- B2: Base year revenue, cross-sheet reference from Assumptions, green, s="3" (general format) -->
  <!-- If currency format is needed, append new style s="13" (see Section 5.4) -->
  <c r="B2" s="3"><f>Assumptions!B4</f><v></v></c>
  <!-- C2, D2: Next year revenue = prior year * (1 + growth rate), black font currency formula, s="6" -->
  <c r="C2" s="6"><f>B2*(1+Assumptions!B2)</f><v></v></c>
  <c r="D2" s="6"><f>C2*(1+Assumptions!B2)</f><v></v></c>
</row>

<!-- Row 3: Gross profit row - black font currency formula, s="6" -->
<row r="3">
  <c r="A3" t="inlineStr"><is><t>Gross Profit</t></is></c>
  <c r="B3" s="6"><f>B2*Assumptions!B3</f><v></v></c>
  <c r="C3" s="6"><f>C2*Assumptions!B3</f><v></v></c>
  <c r="D3" s="6"><f>D2*Assumptions!B3</f><v></v></c>
</row>

<!-- Row 4: Gross margin row - black font percentage formula, s="8" -->
<row r="4">
  <c r="A4" t="inlineStr"><is><t>Gross Margin %</t></is></c>
  <c r="B4" s="8"><f>B3/B2</f><v></v></c>
  <c r="C4" s="8"><f>C3/C2</f><v></v></c>
  <c r="D4" s="8"><f>D3/D2</f><v></v></c>
</row>
```### 5.4 附加“绿色+数字格式”组合

预定义索引3为绿色字体+通用格式。如果跨表引用涉及货币金额，则必须附加具有数字格式的绿色样式：```xml
<!-- Append at the end of <cellXfs> in styles.xml (assuming current count=13, new index=13) -->
<!-- index 13: cross-sheet reference + currency format (green font + $#,##0) -->
<xf numFmtId="164" fontId="3" fillId="0" borderId="0" xfId="0"
    applyFont="1" applyNumberFormat="1"/>
<!-- Update count to 14 -->
```添加后，跨表参考货币单元格使用 `s="13"`。

---

## 6. 完整的操作流程

### 6.1 工作流程概述```
[Existing xlsx or file after CREATE/EDIT]
        |
  Step 1: Unpack (extract to temporary directory)
        |
  Step 2: Audit styles.xml (review existing styles, build index mapping table)
        |
  Step 3: Audit sheet XML (identify cells needing formatting and their semantic roles)
        |
  Step 4: Append missing styles (numFmt -> font -> fill -> xf, update counts)
        |
  Step 5: Batch-update the s attribute of each cell in the sheet XML
        |
  Step 6: XML validity + style reference integrity verification
        |
  Step 7: Pack (recompress as xlsx)
```### 6.2 第 1 步 — 拆包```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_fmt/
```如果脚本不可用，请手动解压：```bash
mkdir -p /tmp/xlsx_fmt && cp input.xlsx /tmp/xlsx_fmt/input.xlsx
cd /tmp/xlsx_fmt && unzip input.xlsx -d unpacked/
```### 6.3 步骤 2 — 审核 styles.xml

按3.1节方法执行。快速检查minimal_xlsx模板初始状态：
- `<cellXfs count="13">` 和 `<numFmts count="4">` -> 模板初始状态，所有 13 个预定义插槽都可以直接使用
- 否则 -> 需要对现有索引映射进行完整审查

### 6.4 步骤 3 — 审核表 XML，构建格式计划

读取“xl/worksheets/sheet*.xml”并评估每个单元格：
1.它是否包含“<f>”元素（公式）？ -> 需要黑/绿/红款式
2.它是一个硬编码的数字参数吗？ -> 需要蓝色风格
3. 数据类型是货币/百分比/整数/年份吗？ -> 选择对应的数字格式槽位
4. 是标题吗？ -> 粗体样式（索引 4）

构建格式化映射表：`{单元格坐标：目标样式索引}`

### 6.5 第 4 步 — 附加样式

按照3.2节的原子操作顺序执行。添加每个组件后立即更新相应的计数属性。

### 6.6 步骤 5 — 批量更新 Cell 属性```xml
<!-- Before formatting: no style -->
<c r="B5"><v>0.08</v></c>

<!-- After formatting: growth rate assumption, blue font percentage, s="7" -->
<c r="B5" s="7"><v>0.08</v></c>
```

```xml
<!-- Before formatting: formula without style -->
<c r="C10"><f>B10*(1+Assumptions!B2)</f><v></v></c>

<!-- After formatting: currency formula, black font, s="6" -->
<c r="C10" s="6"><f>B10*(1+Assumptions!B2)</f><v></v></c>
```对于相同类型的连续行，可以使用行级默认样式来减少重复：```xml
<!-- Entire row uses style=6, only override for exception cells -->
<row r="5" s="6" customFormat="1">
  <c r="A5" s="0" t="inlineStr"><is><t>Operating Income</t></is></c>  <!-- Text overridden to default -->
  <c r="B5"><f>B3-B4</f><v></v></c>   <!-- Inherits row-level s=6 -->
  <c r="C5"><f>C3-C4</f><v></v></c>
</row>
```### 6.7 第 6 步 — 验证```bash
# XML validity verification is handled automatically by xlsx_pack.py, no need to manually run xmllint
# The pack script validates styles.xml and sheet XML legality before packaging; it aborts and reports on errors

# Style audit (optional, audit the entire unpacked directory after formatting is complete)
python3 SKILL_DIR/scripts/style_audit.py /tmp/xlsx_fmt/unpacked/

# Formula error static scan (must specify a single .xlsx file, does not accept directories)
# Pack first, then scan:
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_fmt/unpacked/ /tmp/output.xlsx
python3 SKILL_DIR/scripts/formula_check.py /tmp/output.xlsx
```手动样式参考完整性检查：```bash
# Find the maximum s attribute value in the sheet XML
grep -o 's="[0-9]*"' /tmp/xlsx_fmt/unpacked/xl/worksheets/sheet1.xml \
  | grep -o '[0-9]*' | sort -n | tail -1

# Compare with the cellXfs count attribute (max s value must be < count)
grep 'cellXfs count' /tmp/xlsx_fmt/unpacked/xl/styles.xml
```### 6.8 第 7 步 — 打包```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_fmt/unpacked/ output.xlsx
```如果脚本不可用，请手动打包：```bash
cd /tmp/xlsx_fmt/unpacked/
zip -r ../output.xlsx . -x "*.DS_Store"
```---

## 7. 格式完整性检查表

交货前验证每件物品：

### 颜色角色一致性
- [ ] 所有包含 `<f>` 元素的数字单元格：fontId 对应黑色（公式）或绿色（跨表引用）
- [ ] 所有硬编码的数值都是用户可调整的参数：fontId 对应于蓝色（输入）
- [ ] 跨表引用（公式包含 `SheetName!`）：fontId 对应绿色
- [ ] 外部文件引用（公式包含 `[FileName.xlsx]`）：fontId 对应于红色
- [ ] 没有单元格同时包含`<f>`元素并使用蓝色字体（颜色角色矛盾）

### 数字格式正确性
- [ ] 年份列：numFmtId="1"（`0` 格式），显示为 2024 年而不是 2,024
- [ ] 货币行：numFmtId="164" 或变体，负数显示为 ($1,234) 而不是 -$1,234
- [ ] 百分比行：以小数形式存储的值 (0.08 = 8%)，格式 numFmtId="165"，显示为 8.0%
- [ ] 零值：在稀疏矩阵中显示为“-”而不是“0”（formatCode 第三段包含“-”）
- [ ] 多行（EV/EBITDA 等）：numFmtId="166"（`0.0x` 格式）
- [ ] 负数显示样式在整个工作簿中保持一致（括号或红色减号）

### styles.xml 结构完整性
- [ ] `<numFmts count>` = `<numFmt>` 元素的实际数量
- [ ] `<fonts count>` = `<font>` 元素的实际数量
- [ ] `<fills count>` = `<fill>` 元素的实际数量（包括规范规定的 fills[0] 和 fills[1]）
- [ ] `<cellXfs count>` = `<xf>` 元素的实际数量
- [ ] fills[0] 是 `patternType="none"`，fills[1] 是 `patternType="gray125"` （规范强制）
- [ ] 所有 `<xf>` 引用的 fontId / fillId / borderId 均在其各自集合的有效范围内
- [ ] 所有单元`s`属性值<`cellXfs count`（无越界引用）

### 假设分离验证
- [ ] 假设区域/工作表中没有黑色字体数字单元格（黑色数字 = 公式，不应出现在假设中）
- [ ] 模型区域/工作表中没有蓝色字体非年份数字单元格（蓝色数字=硬编码，应该在假设中）
- [ ] 模型区的输入参数通过公式引用假设区，而不是直接复制值

### 公式和格式链接
- [ ] 所有带有 `<f>` 元素的单元格都具有显式的 `s` 属性（不得使用默认 style=0，其字体颜色不是显式黑色）
- [ ] SUM 摘要行：样式使用黑色字体+相应的数字格式（例如，s=“6”表示货币摘要）
- [ ] 百分比公式：以小数形式存储的值，格式为“0.0%”；在应用百分比格式之前不要将值乘以 100

### 视觉层次结构
- [ ] 标题行（年份/指标名称）：style=4（粗体黑色）
- [ ] 摘要行（总计/EBITDA/净利润）：粗体 + 相应的数字格式（如果需要，请附加样式）
- [ ] 单位描述行（例如，“$ 千”）：使用 style=0 或 style=2（不需要蓝色）

---

## 8. 禁止行为（你不能做的事情）

- **不要修改现有的`<xf>`条目**：这将批量更改引用该索引的所有单元格的样式
- **不要删除 fills[0] 和 fills[1]**：OOXML 规范要求；删除导致文件损坏
- **不要修改单元格值或公式**：FORMAT路径仅更改样式，而不更改内容
- **不要使用 openpyxl 进行格式化**：openpyxl 在保存时重写整个 styles.xml，丢失不支持的功能
- **不要应用全局覆盖样式**：不要用单一样式覆盖整个工作簿；按语义角色精确分配
- **不要在 Alpha 通道中写入 FF**： `rgb="FF0000FF"` 使颜色完全透明；正确的格式是 `rgb="000000FF"`

---

## 9. 常见错误和修复

### 错误 1：年份显示为 2,024

原因：年份单元格的“s”属性使用带有千位分隔符的格式（例如，numFmtId="3" 或 numFmtId="167"）。```xml
<!-- Incorrect -->
<c r="B1" s="9"><v>2024</v></c>

<!-- Fix: Change to s="11" (numFmtId="1", format 0) -->
<c r="B1" s="11"><v>2024</v></c>
```### 错误 2：百分比显示为 800%（值乘以 100）

原因：8% 存储为“<v>8</v>”而不是“<v>0.08</v>”。 Excel 的“%”格式会自动将值乘以 100 进行显示。```xml
<!-- Incorrect -->
<c r="B2" s="7"><v>8</v></c>

<!-- Fix: Value must be stored in decimal form -->
<c r="B2" s="7"><v>0.08</v></c>
```### 错误 3：附加样式后文件损坏而不更新计数

原因：附加了“<font>”或“<xf>”元素，但计数属性未更新； Excel 使用旧计数读取超出范围。

修复：附加每个元素后立即更新相应的计数：```xml
<!-- After appending the 6th font, count must be changed from 5 to 6 -->
<fonts count="6">
  ...
</fonts>
```###错误4：蓝色字体+公式（颜色角色矛盾）

原因：公式单元格错误地使用了输入样式（例如，货币输入为 s=“5”）。```xml
<!-- Incorrect: Formula cell uses blue input style -->
<c r="C5" s="5"><f>B5*1.08</f><v></v></c>

<!-- Fix: Change formula cell to corresponding black formula style (5->6, 7->8, 9->10) -->
<c r="C5" s="6"><f>B5*1.08</f><v></v></c>
```### 错误 5：AARRGBB 颜色缺少 Alpha（仅 6 位数字）```xml
<!-- Incorrect: 6-digit format, behavior depends on implementation, usually causes wrong color -->
<color rgb="0000FF"/>

<!-- Fix: Always use 8-digit AARRGGBB, Alpha fixed at 00 -->
<color rgb="000000FF"/>
```### 错误 6：修改现有 xf（影响引用该索引的所有单元格）

原因：直接修改cellXfs中第N个`<xf>`的属性，导致所有`s="N"`的cell被批量修改。

修复：保持现有条目不变，在末尾追加一个新条目，并且仅将需要新样式的单元格的“s”属性更改为新索引：```xml
<!-- Incorrect: Modified the existing xf at index=6 -->
<xf numFmtId="164" fontId="2" fillId="0" borderId="0" xfId="0"
    applyFont="1" applyNumberFormat="1" applyAlignment="1">
  <alignment horizontal="right"/>  <!-- New attribute added, affects ALL cells already using s="6" -->
</xf>

<!-- Fix: Append new index (when original count=13, new index=13), only change the s attribute of cells needing right alignment -->
<!-- Keep index=6 as-is -->
<xf numFmtId="164" fontId="2" fillId="0" borderId="0" xfId="0"
    applyFont="1" applyNumberFormat="1" applyAlignment="1">
  <alignment horizontal="right"/>
</xf>  <!-- New index=13 -->
```---

## 10. 财务模型结构约定

### 10.1 标题行

- 粗体字体（对应于该技能模板中的样式索引4）
- 年份列：使用数字格式“0”（numFmtId="1"，无千位分隔符）以防止 2024 显示为 2,024
- 单位描述行可以添加在标题下方：灰色或斜体文本，例如“$数千”或“收入的%”

### 10.2 行类型标准

|行类型 |款式推荐|示例|
|----------|---------------------|---------|
|类别标题行 |粗体，可选填充颜色 | “收入” |
|行项目行 |普通款式| “产品A”、“产品B” |
|小计行|粗体+上边框| “总收入” |
|操作公制行 |普通款式| “毛利率%” |
|分隔行 |空行 | （空）|

### 10.3 多年模型栏布局```
Col A: Label column          (width 28, left-aligned text, s="4" for headers or s="0" for labels)
Col B: FY2022 Actual         (width 12, year header s="11", data cells styled by semantic role)
Col C: FY2023 Actual
Col D: FY2024E               (forecast period - can use light gray fill fillId=3 to differentiate)
Col E: FY2025E
Col F: FY2026E
```### 10.4 跨工作表参考模式

从假设表传递到模型表的参数的完整 XML 示例：```xml
<!-- Assumptions sheet, cell B5: 8% growth rate, blue percentage input -->
<c r="B5" s="7"><v>0.08</v></c>

<!-- Model sheet, cell C10: references assumption area growth rate, green percentage formula -->
<!-- Requires appending index=13: green + percentage format (fontId=3, numFmtId=165) -->
<c r="C10" s="13"><f>Assumptions!B5</f><v></v></c>
```---

## 11. 假设类别

在假设区域（假设表或假设块）中，按以下标准顺序组织假设，以便于审查和维护：

1. **收入假设**：增长率、定价、销量
2. **成本假设**：毛利率、固定/可变成本比率
3. **营运资金**：DSO（应付款周转天数）、DPO（应付账款周转天数）、库存天数
4. **资本支出 (CapEx)**：占收入或绝对金额的百分比
5. **融资假设**：利率、债务偿还时间表
6. **税收及其他**：有效税率、折旧和摊销（D&A）

---

## 12. 审计跟踪最佳实践

- 使用 `s="12"`（蓝色字体 + 黄色填充突出显示）标记需要审核或待更改的单元格，使审核者立即可见
- 在敏感性分析行或单独的敏感性选项卡中，显示关键假设 +/-1% 变化对结果的影响
- **不要隐藏包含假设的行**：假设行必须对审阅者可见；不要使用 `hidden="1"` 属性
- 在假设区域顶部或专用单元格中记下“最后更新”日期，记录模型的最后修改时间

---

## 13. 交付前清单（通用财务模型清单）

在输出最终文件之前，请确认每一项：

- [ ] 公式行不包含硬编码值（可以使用“formula_check.py”扫描打包的“.xlsx”文件）
- [ ] 年份列显示为 2024 年而不是 2,024 （numFmtId="1"，格式 `0`）
- [ ] 负数显示为 (1,234) 而不是 -1,234（对于外部交付的财务报告使用括号样式）
- [ ] 零值在稀疏行中显示为“-”，而不是“0”（formatCode 第三段是“”-“”）
- [ ] 增长率和百分比存储为小数 (0.08 = 8%)，格式为 `0.0%`
- [ ] 所有跨工作表引用单元格均使用绿色字体（样式索引 3 或附加的绿色 + 数字格式组合）
- [ ] 假设块和模型块明显分开（不同的工作表或同一工作表内由空行分隔）
- [ ] 摘要行使用“SUM()”公式，而不是手动硬编码总计
- [ ] 余额验证：汇总行=各自行项目的总和（可以在模型末尾添加检查行进行验证）