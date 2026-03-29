# 从头开始构建新的 xlsx

使用 XML 方法创建新的、生产质量的 xlsx 文件。永远不要使用 openpyxl
用于写作。切勿对 Python 计算值进行硬编码 — 每个派生数字都必须是
实时 Excel 公式。

---

## 何时使用此路径

当用户需要时使用此文档：
- 一个尚不存在的全新Excel文件
- 生成的报告、财务模型或数据表
- 任何“创建/构建/生成/制作”请求

如果用户提供要修改的现有文件，请切换到“edit.md”。

---

## 不可协商的规则

在接触任何文件之前，请内化以下四个规则：

1. **公式第一**：每个计算值（`SUM`、增长率、比率、小计等）
   必须写为“<f>SUM(B2:B9)</f>”，而不是硬编码的“<v>5000</v>”。硬编码
   当源数据发生变化时，数字就会过时。仅原始输入和假设参数
   可能是硬编码值。

2. **无需openpyxl进行写入**：整个文件是通过直接编辑XML构建的。蟒蛇
   只允许用于读取/分析（`pandas.read_excel()`）和运行助手
   脚本（`xlsx_pack.py`、`formula_check.py`）。

3. **样式编码含义**：蓝色字体=用户输入/假设。黑色字体=公式
   结果。绿色字体 = 跨表参考。有关全彩色系统，请参阅“format.md”
   和风格索引表。

4. **交付前验证**：运行 `formula_check.py` 并修复之前的所有错误
   将文件交给用户。

---

## 完整的创作流程

### 第 1 步——写作前计划

在接触任何 XML 之前在纸上定义完整的结构：

- **表格**：名称、顺序、目的（例如假设/模型/摘要）
- **每张纸的布局**：哪些行是标题、输入、公式、总计
- **字符串库存**：收集您在共享字符串中需要的所有文本标签
- **样式选择**：每列需要什么数字格式（货币、%、整数、年份）
- **跨工作表链接**：哪些工作表从其他工作表提取数据

此规划步骤可防止将字符串添加到共享字符串的昂贵循环
中途并重新计算所有指数。

---

### 步骤 2 — 复制最小模板```bash
cp -r SKILL_DIR/templates/minimal_xlsx/ /tmp/xlsx_work/
```该模板为您提供了完整、有效的 7 个文件 xlsx 框架：```
/tmp/xlsx_work/
├── [Content_Types].xml        ← MIME type registry
├── _rels/
│   └── .rels                  ← root relationship (points to workbook.xml)
└── xl/
    ├── workbook.xml            ← sheet list and calc settings
    ├── styles.xml              ← 13 pre-built financial style slots
    ├── sharedStrings.xml       ← text string table (starts empty)
    ├── _rels/
    │   └── workbook.xml.rels  ← maps rId → file paths
    └── worksheets/
        └── sheet1.xml          ← one empty sheet
```复制后，重命名工作表并添加内容。不要从头开始创建文件 -
始终从模板开始。

---

### 步骤 3 — 配置工作表结构

#### 单页练习册

该模板已有一个名为“Sheet1”的工作表。只需更改“名称”属性即可
在`xl/workbook.xml`中：```xml
<sheets>
  <sheet name="Revenue Model" sheetId="1" r:id="rId1"/>
</sheets>
```单页工作簿不需要更改其他文件。

#### 多页工作簿

四个文件必须保持同步。按以下顺序完成它们：

**重要 — rId 冲突规则**：在模板的“workbook.xml.rels”中，ID
`rId1`、`rId2` 和 `rId3` 已被占用：
- `rId1` → `worksheets/sheet1.xml`
- `rId2` → `styles.xml`
- `rId3` → `sharedStrings.xml`

新的工作表条目必须从“rId4”开始并向上计数。

**文件 1（共 4 个）- `xl/workbook.xml`**（工作表列表）：```xml
<sheets>
  <sheet name="Assumptions" sheetId="1" r:id="rId1"/>
  <sheet name="Model"       sheetId="2" r:id="rId4"/>
  <sheet name="Summary"     sheetId="3" r:id="rId5"/>
</sheets>
```工作表名称中的特殊字符：
- XML 中的 `&` → `&amp;`：`<sheet name="P&amp;L" .../>`
- 最多 31 个字符
- 禁止：`/ \ ？ * [ ] :`
- 带有空格的工作表名称需要在公式引用中使用单引号：`'Q1 Data'!B5`

**文件 2，共 4 个 — `xl/_rels/workbook.xml.rels`**（ID → 文件映射）：```xml
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings"
    Target="sharedStrings.xml"/>
  <Relationship Id="rId4"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId5"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet3.xml"/>
</Relationships>
```**文件 3，共 4 个 — `[Content_Types].xml`**（MIME 类型声明）：```xml
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
```**文件 4（共 4 个）- 创建新的工作表 XML 文件**

将“sheet1.xml”复制到“sheet2.xml”和“sheet3.xml”，然后清除“<sheetData>”内容：```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet
  xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews>
    <sheetView workbookViewId="0"/>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="15" x14ac:dyDescent="0.25"
    xmlns:x14ac="http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac"/>
  <sheetData>
    <!-- Data rows go here -->
  </sheetData>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>
```**同步清单** — 每次添加工作表时，请验证所有四个工作表是否一致：

|检查 |验证什么 |
|--------|----------------|
| `workbook.xml` |新的`<sheet name =“...”sheetId =“N”r：id =“rIdX”/>`存在 |
| `workbook.xml.rels` |新的 `<Relationship Id="rIdX" ... Target="worksheets/sheetN.xml"/>` 存在 |
| `[Content_Types].xml` |新的 `<Override PartName="/xl/worksheets/sheetN.xml" .../>` 存在 |
|文件系统 | `xl/worksheets/sheetN.xml` 文件确实存在 |

---

### 步骤 4 — 填充共享字符串

所有文本值（标题、行标签、类别名称、用户将读取的任何字符串）
必须存储在“xl/sharedStrings.xml”中。单元格通过从 0 开始的索引来引用它们。

**推荐的工作流程**：首先收集您需要的所有文本，一次编写完整的表格，
然后在编写工作表 XML 时填写索引。这避免了中途重新计算指数。```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
     count="10" uniqueCount="10">
  <si><t>Item</t></si>                  <!-- index 0 -->
  <si><t>FY2023A</t></si>               <!-- index 1 -->
  <si><t>FY2024E</t></si>               <!-- index 2 -->
  <si><t>FY2025E</t></si>               <!-- index 3 -->
  <si><t>YoY Growth</t></si>            <!-- index 4 -->
  <si><t>Revenue</t></si>               <!-- index 5 -->
  <si><t>Cost of Goods Sold</t></si>    <!-- index 6 -->
  <si><t>Gross Profit</t></si>          <!-- index 7 -->
  <si><t>EBITDA</t></si>                <!-- index 8 -->
  <si><t>Net Income</t></si>            <!-- index 9 -->
</sst>
```**属性规则**：
- `uniqueCount` = `<si>` 元素的数量（表中的唯一字符串）
- `count` = 整个工作簿中对字符串的单元格引用总数
  （如果“Revenue”出现在 3 张中，则计数为 `uniqueCount + 2`）
- 对于每个字符串出现一次的新文件，“count == uniqueCount”
- 两个属性都必须准确 - 错误的值会在某些 Excel 版本中触发警告

**特殊字符转义**：```xml
<si><t>R&amp;D Expenses</t></si>          <!-- & must be &amp; -->
<si><t>Revenue &lt; Target</t></si>        <!-- < must be &lt; -->
<si><t xml:space="preserve">  (note)  </t></si>  <!-- preserve leading/trailing spaces -->
```**帮助脚本**：使用`shared_strings_builder.py`生成完整的
来自简单字符串列表的“sharedStrings.xml”：```bash
python3 SKILL_DIR/scripts/shared_strings_builder.py \
  "Item" "FY2024" "FY2025" "Revenue" "Gross Profit" \
  > /tmp/xlsx_work/xl/sharedStrings.xml
```或者以交互方式从每行列出一个字符串的文件中：```bash
python3 SKILL_DIR/scripts/shared_strings_builder.py --file strings.txt \
  > /tmp/xlsx_work/xl/sharedStrings.xml
```---

### 步骤 5 — 写入工作表数据

编辑每个“xl/worksheets/sheetN.xml”。将空的“<sheetData>”替换为行
和细胞。

#### 单元 XML 剖析```
<c r="B5" t="s" s="4">
      ↑     ↑    ↑
   address  type  style index (from cellXfs in styles.xml)

  <v>3</v>
     ↑
  value (for t="s": sharedStrings index; for numbers: the number itself)
```#### 数据类型参考

|数据| `t` 属性 | XML 示例 |笔记|
|------|---------|-------------|--------|
|共享字符串（文本）| `s` | `<c r="A1" t="s" s="4"><v>0</v></c>` | `<v>` = 共享字符串索引 |
|数量 |省略| `<c r="B2" s="5"><v>1000000</v></c>` |默认类型，省略`t` |
|百分比（十进制）|省略| `<c r="C2" s="7"><v>0.125</v></c>` | 12.5% 存储为 0.125 |
|布尔 | `b` | `<c r="D1" t="b"><v>1</v></c>` | 1=真，0=假 |
|公式|省略| `<c r="B4" s="2"><f>SUM(B2:B3)</f><v></v></c>` | `<v>` 留空 |
|交叉表公式|省略| `<c r="C1" s="3"><f>假设！B2</f><v></v></c>` |使用 s=3（绿色）|

#### 完整的工作表数据示例```xml
<cols>
  <col min="1" max="1" width="26" customWidth="1"/>   <!-- A: label column -->
  <col min="2" max="5" width="14" customWidth="1"/>   <!-- B-E: data columns -->
</cols>
<sheetData>

  <!-- Row 1: headers (style 4 = bold header) -->
  <row r="1" ht="18" customHeight="1">
    <c r="A1" t="s" s="4"><v>0</v></c>   <!-- "Item" -->
    <c r="B1" t="s" s="4"><v>1</v></c>   <!-- "FY2023A" -->
    <c r="C1" t="s" s="4"><v>2</v></c>   <!-- "FY2024E" -->
    <c r="D1" t="s" s="4"><v>3</v></c>   <!-- "FY2025E" -->
    <c r="E1" t="s" s="4"><v>4</v></c>   <!-- "YoY Growth" -->
  </row>

  <!-- Row 2: Revenue — actual value (input) + formula (computed) -->
  <row r="2">
    <c r="A2" t="s" s="1"><v>5</v></c>    <!-- "Revenue", blue input label -->
    <c r="B2" s="5"><v>85000000</v></c>   <!-- FY2023A actual: $85M, currency input -->
    <c r="C2" s="6"><f>B2*(1+Assumptions!C3)</f><v></v></c>   <!-- formula, currency -->
    <c r="D2" s="6"><f>C2*(1+Assumptions!D3)</f><v></v></c>
    <c r="E2" s="8"><f>D2/C2-1</f><v></v></c>   <!-- YoY growth, percentage formula -->
  </row>

  <!-- Row 3: Gross Profit -->
  <row r="3">
    <c r="A3" t="s" s="2"><v>7</v></c>    <!-- "Gross Profit", black formula label -->
    <c r="B3" s="6"><f>B2*Assumptions!B4</f><v></v></c>
    <c r="C3" s="6"><f>C2*Assumptions!C4</f><v></v></c>
    <c r="D3" s="6"><f>D2*Assumptions!D4</f><v></v></c>
    <c r="E3" s="8"><f>D3/C3-1</f><v></v></c>
  </row>

  <!-- Row 5: SUM total row -->
  <row r="5">
    <c r="A5" t="s" s="4"><v>8</v></c>    <!-- "EBITDA" -->
    <c r="B5" s="6"><f>SUM(B2:B4)</f><v></v></c>
    <c r="C5" s="6"><f>SUM(C2:C4)</f><v></v></c>
    <c r="D5" s="6"><f>SUM(D2:D4)</f><v></v></c>
    <c r="E5" s="8"><f>D5/C5-1</f><v></v></c>
  </row>

</sheetData>
```#### 列宽和冻结窗格

列宽位于“<sheetData>”之前**，冻结窗格位于“<sheetView>”内部：```xml
<!-- Inside <sheetViews><sheetView ...> — freeze the header row -->
<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>

<!-- Before <sheetData> — set column widths -->
<cols>
  <col min="1" max="1" width="28" customWidth="1"/>
  <col min="2" max="8" width="14" customWidth="1"/>
</cols>
```---

### 步骤 6 — 应用样式

该模板的“xl/styles.xml”有 13 个预构建的语义样式槽（索引 0–12）。
**阅读 `format.md` 了解完整的样式索引表、颜色系统以及如何添加新样式。**

最常见插槽的快速参考：

| `s` |角色 |示例|
|-----|------|---------|
| 4 |标题（粗体）|列/行标题 |
| 5 / 6 |货币输入（蓝色）/公式（黑色）| `$#,##0` |
| 7 / 8 |百分比输入/公式| `0.0%` |
| 11 | 11年份（无逗号）| 2024 年不是 2,024 |

设计原则：蓝色=人设此。黑色 = Excel 计算此值。绿色 = 跨页。

如果您需要的样式不在 13 个预构建槽中，请按照“format.md”第 3.2 节中的仅附加过程进行操作。

---

### 步骤 7 — 配方食谱

#### XML 公式语法提醒

XML 中的公式**没有前导 `=`**：```xml
<!-- Excel UI: =SUM(B2:B9)   →   XML: -->
<c r="B10" s="6"><f>SUM(B2:B9)</f><v></v></c>
```#### 基本聚合```xml
<c r="B10" s="6"><f>SUM(B2:B9)</f><v></v></c>
<c r="B11" s="6"><f>AVERAGE(B2:B9)</f><v></v></c>
<c r="B12" s="10"><f>COUNT(B2:B9)</f><v></v></c>
<c r="B13" s="10"><f>COUNTA(A2:A100)</f><v></v></c>
<c r="B14" s="6"><f>MAX(B2:B9)</f><v></v></c>
<c r="B15" s="6"><f>MIN(B2:B9)</f><v></v></c>
```#### 财务计算```xml
<!-- YoY growth rate: current / prior - 1 -->
<c r="E5" s="8"><f>D5/C5-1</f><v></v></c>

<!-- Gross profit: revenue × gross margin -->
<c r="B6" s="6"><f>B4*B3</f><v></v></c>

<!-- EBITDA margin: EBITDA / Revenue -->
<c r="B9" s="8"><f>B8/B4</f><v></v></c>

<!-- Suppress #DIV/0! when denominator may be zero -->
<c r="E5" s="8"><f>IF(C5=0,0,D5/C5-1)</f><v></v></c>

<!-- NPV and IRR (cash flows in B2:B7, discount rate in B1) -->
<c r="C1" s="6"><f>NPV(B1,B3:B7)+B2</f><v></v></c>
<c r="C2" s="8"><f>IRR(B2:B7)</f><v></v></c>
```#### 跨表参考```xml
<!-- No spaces in name: no quotes needed -->
<c r="B3" s="3"><f>Assumptions!B5</f><v></v></c>

<!-- Space in sheet name: single quotes required -->
<c r="B3" s="3"><f>'Q1 Data'!B5</f><v></v></c>

<!-- Ampersand in sheet name (XML-escaped in workbook.xml, but in formula: literal &) -->
<c r="B3" s="3"><f>'R&amp;D'!B5</f><v></v></c>

<!-- Cross-sheet range: SUM of a range in another sheet -->
<c r="B10" s="6"><f>SUM(Data!C2:C1000)</f><v></v></c>

<!-- 3D reference: sum same cell across multiple sheets -->
<c r="B5" s="6"><f>SUM(Jan:Dec!B5)</f><v></v></c>
```跨表公式单元格应使用 `s="3"`（绿色）来表示数据来源。

#### 共享公式（相同的模式在列中重复）

当许多连续单元格共享相同的公式结构且仅包含行号时
更改时，使用共享公式来保持 XML 紧凑：```xml
<!-- D2: defines the shared group (si="0", ref="D2:D11") -->
<c r="D2" s="8"><f t="shared" ref="D2:D11" si="0">C2/B2-1</f><v></v></c>

<!-- D3 through D11: reference the same group, no formula text needed -->
<c r="D3" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D4" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D5" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D6" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D7" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D8" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D9" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D10" s="8"><f t="shared" si="0"/><v></v></c>
<c r="D11" s="8"><f t="shared" si="0"/><v></v></c>
```Excel 自动调整相对引用（D3 计算“C3/B3-1”等）。
如果您有多个共享公式组，请分配连续的“si”值（0、1、2、...）。

#### 绝对引用```xml
<!-- $B$2 locks to that cell when the formula is copied -->
<c r="C5" s="8"><f>B5/$B$2</f><v></v></c>
````$` 字符不需要 XML 转义——按字面意思写。

#### 查找公式```xml
<!-- VLOOKUP: exact match (last arg 0) -->
<c r="C5" s="6"><f>VLOOKUP(A5,Assumptions!A:C,2,0)</f><v></v></c>

<!-- INDEX/MATCH: more flexible -->
<c r="C5" s="6"><f>INDEX(B:B,MATCH(A5,A:A,0))</f><v></v></c>

<!-- XLOOKUP (Excel 2019+) -->
<c r="C5" s="6"><f>XLOOKUP(A5,A:A,B:B)</f><v></v></c>
```---

### 第 8 步 — 打包和验证

**包装**：```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ /path/to/output.xlsx
````xlsx_pack.py` 将：
1. 检查根目录下是否存在“[Content_Types].xml”
2. 解析每个 `.xml` 和 `.rels` 文件的格式良好 — 如果失败则中止
3. 创建正确压缩的 ZIP 存档

**验证**：```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/output.xlsx
````formula_check.py` 将：
1. 扫描每个单元格中的 `<c t="e">` 条目（缓存的错误值）——所有 7 种错误类型
2. 从每个“<f>”公式中提取工作表名称引用
3. 验证每个引用的工作表是否存在于“workbook.xml”中

在交付前修复所有报告的错误。退出代码 0 = 可以安全交付。

---

## 交付前检查表

在将文件交给用户之前运行此列表：

- [ ] `formula_check.py` 报告 0 个错误
- [ ] 每个计算单元格都有“<f>”——而不仅仅是带有数字的“<v>”
- [ ] `sharedStrings.xml` `count` 和 `uniqueCount` 匹配实际的 `<si>` 计数
- [ ] 每个单元的“s”属性值都在“0”到“cellXfs count - 1”范围内
- [ ] `workbook.xml` 中的每个工作表在 `workbook.xml.rels` 中都有一个匹配的条目
- [ ] 每个“worksheets/sheetN.xml”文件在“[Content_Types].xml”中都有一个匹配的“<Override>”
- [ ] 年份列使用 `s="11"` （格式为 `0`，无千位分隔符）
- [ ] 跨表参考公式使用 `s="3"`（绿色字体）
- [ ] 假设输入使用 `s="1"` 或 `s="5"` 或 `s="7"` （蓝色字体）

---

## 常见错误和修复

|错误|症状|修复 |
|---------|---------|-----|
|公式有前导 `=` |单元格将 `=SUM(...)` 显示为文本 |从 `<f>` 内容中删除 `=` |
|共享字符串“count”未更新 | Excel 警告或空白单元格 |计算 `<si>` 元素的数量，更新 `count` 和 `uniqueCount` |
|风格索引超出范围 |文件损坏/Excel修复|确保 `s` < `cellXfs count`；如果需要，追加新的 `<xf>` |
|新工作表 rId 与 styles/sharedStrings rId 冲突 |纸张丢失或样式丢失 |新工作表使用 rId4、rId5、...（rId1-3 在模板中保留）|
|工作表名称在 XML 中未转义“&” | XML 解析错误 |在`workbook.xml`名称属性中使用`&amp;`
|跨工作表引用带空格、不带引号的工作表 | `#REF!` 错误 |将工作表名称用单引号引起来：`'工作表名称'!B5` |
|跨工作表引用不存在的工作表 | `#REF!` 错误 |检查“workbook.xml”工作表列表与公式 |
|数字存储为文本 (`t="s"`) |左对齐，无法求和 |从数字单元格中删除“t”属性 |
|年份显示为 `2,024` |可读性问题 |使用`s =“11”`（numFmtId = 1，格式`0`）|
|硬编码 Python 结果而不是公式 | “死表”——不会更新 |将 `<v>N</v>` 替换为 `<f> 公式</f><v></v>` |

---

## 列字母参考

|校号 |信|校号 |信|校号 |信|
|--------|--------|--------|--------|--------|--------|
| 1 |一个 | 26 | 26 Z| 27 | 27 AA |
| 28 | 28 AB | 52 | 52 AZ | 53 | 53学士 |
| 54 | 54 BB | 78 | 78 BZ | 79 | 79加州 |

Python 转换（以编程方式构建公式时使用）：```python
def col_letter(n: int) -> str:
    """Convert 1-based column number to Excel letter (A, B, ..., Z, AA, AB, ...)."""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result

def col_number(s: str) -> int:
    """Convert Excel column letter to 1-based number."""
    n = 0
    for c in s.upper():
        n = n * 26 + (ord(c) - 64)
    return n
```---

## 典型场景演练

### 场景 A — 三年财务模型（单页）

布局：第 1-12 行 = 假设（蓝色输入）/第 14-30 行 = 模型（黑色公式）。```xml
<!-- sharedStrings.xml (excerpt) -->
<sst count="8" uniqueCount="8">
  <si><t>Metric</t></si>           <!-- 0 -->
  <si><t>FY2023A</t></si>          <!-- 1 -->
  <si><t>FY2024E</t></si>          <!-- 2 -->
  <si><t>FY2025E</t></si>          <!-- 3 -->
  <si><t>Revenue Growth</t></si>   <!-- 4 -->
  <si><t>Gross Margin</t></si>     <!-- 5 -->
  <si><t>Revenue</t></si>          <!-- 6 -->
  <si><t>Gross Profit</t></si>     <!-- 7 -->
</sst>

<!-- sheet1.xml (excerpt) -->
<sheetData>
  <!-- Header -->
  <row r="1">
    <c r="A1" t="s" s="4"><v>0</v></c>
    <c r="B1" t="s" s="4"><v>1</v></c>
    <c r="C1" t="s" s="4"><v>2</v></c>
    <c r="D1" t="s" s="4"><v>3</v></c>
  </row>
  <!-- Assumptions (rows 2-3) -->
  <row r="2">
    <c r="A2" t="s" s="1"><v>4</v></c>    <!-- "Revenue Growth", blue -->
    <c r="B2" s="7"><v>0</v></c>          <!-- FY2023A: n/a, 0% placeholder -->
    <c r="C2" s="7"><v>0.12</v></c>       <!-- FY2024E: 12.0% input -->
    <c r="D2" s="7"><v>0.15</v></c>       <!-- FY2025E: 15.0% input -->
  </row>
  <row r="3">
    <c r="A3" t="s" s="1"><v>5</v></c>    <!-- "Gross Margin", blue -->
    <c r="B3" s="7"><v>0.45</v></c>
    <c r="C3" s="7"><v>0.46</v></c>
    <c r="D3" s="7"><v>0.47</v></c>
  </row>
  <!-- Model (rows 14-15) -->
  <row r="14">
    <c r="A14" t="s" s="2"><v>6</v></c>      <!-- "Revenue", black -->
    <c r="B14" s="5"><v>85000000</v></c>     <!-- actual, currency input -->
    <c r="C14" s="6"><f>B14*(1+C2)</f><v></v></c>
    <c r="D14" s="6"><f>C14*(1+D2)</f><v></v></c>
  </row>
  <row r="15">
    <c r="A15" t="s" s="2"><v>7</v></c>      <!-- "Gross Profit", black -->
    <c r="B15" s="6"><f>B14*B3</f><v></v></c>
    <c r="C15" s="6"><f>C14*C3</f><v></v></c>
    <c r="D15" s="6"><f>D14*D3</f><v></v></c>
  </row>
</sheetData>
```### 场景 B — 数据 + 摘要（两张）

“Summary”工作表使用跨表公式从“Data”中提取（绿色，“s=3”）：```xml
<!-- Summary/sheet2.xml sheetData excerpt -->
<sheetData>
  <row r="1">
    <c r="A1" t="s" s="4"><v>0</v></c>   <!-- "Metric" -->
    <c r="B1" t="s" s="4"><v>1</v></c>   <!-- "Value" -->
  </row>
  <row r="2">
    <c r="A2" t="s" s="0"><v>2</v></c>   <!-- "Total Revenue" -->
    <c r="B2" s="3"><f>SUM(Data!C2:C10000)</f><v></v></c>
  </row>
  <row r="3">
    <c r="A3" t="s" s="0"><v>3</v></c>   <!-- "Deal Count" -->
    <c r="B3" s="3"><f>COUNTA(Data!A2:A10000)</f><v></v></c>
  </row>
  <row r="4">
    <c r="A4" t="s" s="0"><v>4</v></c>   <!-- "Avg Deal Size" -->
    <c r="B4" s="3"><f>IF(B3=0,0,B2/B3)</f><v></v></c>
  </row>
</sheetData>
```### 场景 C — 多部门整合

“合并”工作表对多个部门工作表中的相同单元格进行求和：```xml
<!-- Consolidated/sheet4.xml — summing across Dept_Eng and Dept_Mkt -->
<sheetData>
  <row r="5">
    <c r="A5" t="s" s="2"><v>0</v></c>
    <!-- No spaces in sheet names → no quotes needed -->
    <c r="B5" s="3"><f>Dept_Engineering!B5+Dept_Marketing!B5</f><v></v></c>
  </row>
  <row r="6">
    <c r="A6" t="s" s="2"><v>1</v></c>
    <c r="B6" s="3"><f>SUM(Dept_Engineering!B6,Dept_Marketing!B6)</f><v></v></c>
  </row>
</sheetData>
```---

## 你绝对不能做的事

- 不要使用 openpyxl 或任何 Python 库来编写最终的 xlsx 文件
- 不要对任何计算值进行硬编码 - 对每个派生数字使用“<f>”公式
- 在未先运行 `formula_check.py` 的情况下请勿交付
- 不要将单元格的 `s` 属性设置为 >= `cellXfs count` 的值
- 不要修改`styles.xml`中现有的`<xf>`条目——只添加新条目
- 在未更新所有四个同步点（workbook.xml、
  workbook.xml.rels，[Content_Types].xml，实际的 .xml 文件）
- 不要分配与 rId1、rId2 或 rId3 重叠的新工作表 rId（保留
  对于模板中的sheet1、样式、sharedStrings）