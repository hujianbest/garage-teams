# 对现有 xlsx 进行微创编辑

对现有 xlsx 文件进行精确的外科手术更改，同时保留您不接触的所有内容：样式、宏、数据透视表、图表、迷你图、命名范围、数据验证、条件格式和所有其他嵌入内容。

---

## 1. 何时使用此路径

每当任务涉及**修改现有 xlsx 文件**时，请使用编辑（解包 → XML 编辑 → 打包）路径：

- 模板填充——用值或公式填充指定的输入单元格
- 数据更新 — 替换实时文件中过时的数字、文本或日期
- 内容更正——修复错误的值、损坏的公式或错误的标签
- 将新数据行添加到现有表中
- 重命名工作表
- 将新样式应用于特定单元格

不要使用此路径从头开始创建全新的工作簿。为此，请参阅“create.md”。

---

## 2. 为什么现有文件禁止 openpyxl 往返

openpyxl `load_workbook()` 后跟 `workbook.save()` 是对任何包含高级功能的文件的**破坏性操作**。库默默地删除它不理解的内容：

|特色| openpyxl 行为 |后果|
|--------|--------------------|-------------|
| VBA 宏 (`vbaProject.bin`) |彻底放弃|所有自动化都消失了；文件另存为“.xlsx”而不是“.xlsm” |
|数据透视表 (`xl/pivotTables/`) |掉落 |互动分析被破坏 |
|切片机|掉落 |过滤器 UI 丢失 |
|迷你图 (`<sparklineGroups>`) |掉落 |单元格内的迷你图表消失了 |
|图表格式详细信息 |部分丢失|系列颜色、自定义轴可能会恢复 |
|打印区域/分页符|有时会迷失|打印布局更改 |
|自定义 XML 部件 |掉落 |第三方数据绑定已损坏 |
|与主题相关的颜色 |可能会去主题化|颜色转换为绝对颜色，打破主题切换 |

即使在没有这些功能的“普通”文件上，openpyxl 也可以规范 Excel 所依赖的 XML 中的空格、更改命名空间声明或重置“calcMode”标志。

**规则是绝对的：切勿为了重新保存而使用 openpyxl 打开现有文件。**

XML 直接编辑方法是安全的，因为它对原始字节进行操作。您只需更改您触摸的节点。其他一切都与原始字节等效。

---

## 3. 标准操作流程

### 第 1 步 — 拆包```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/
```该脚本解压缩 xlsx，漂亮地打印每个 XML 和“.rels”文件，并打印关键文件的分类清单，并在检测到高风险内容时发出警告（VBA、数据透视表、图表）。

在继续之前请仔细阅读打印输出。如果脚本报告“xl/vbaProject.bin”或“xl/pivotTables/”，请遵循第 7 节中的约束。

### 第 2 步 — 侦察

在接触任何东西之前先绘制结构图。

**识别工作表名称及其 XML 文件：**```
xl/workbook.xml  →  <sheet name="Revenue" sheetId="1" r:id="rId1"/>
xl/_rels/workbook.xml.rels  →  <Relationship Id="rId1" Target="worksheets/sheet1.xml"/>
```名为“Revenue”的工作表位于“xl/worksheets/sheet1.xml”中。在编辑工作表之前始终解析此映射。

**了解共享字符串表：**```bash
# Count existing entries in xl/sharedStrings.xml
grep -c "<si>" /tmp/xlsx_work/xl/sharedStrings.xml
```该表中的每个文本单元格都使用从零开始的索引。在附加之前了解当前计数。

**了解样式表：**```bash
# Count existing cellXfs entries
grep -c "<xf " /tmp/xlsx_work/xl/styles.xml
```新样式的插槽附加在现有插槽之后。第一个新槽的索引 = 当前计数。

**扫描目标工作表中的高风险 XML 区域：**

编辑之前在目标“sheet*.xml”中查找这些元素：

- `<mergeCell>` — 合并单元格范围；行/列插入会改变这些
- `<conditionalFormatting>` — 条件范围；行/列插入会改变这些
- `<dataValidations>` — 验证范围；行/列插入会改变这些
- `<tableParts>` — 表定义；表内的行插入需要更新“<tableColumn>”
- `<sparklineGroups>` — 迷你图；保留而不修改

### 步骤 3 — 将意图映射到最少的 XML 更改

在写入单个字符之前，请生成一份明确列出哪些 XML 节点发生变化的书面列表。这可以防止范围蔓延。

|用户意图 |要更改的文件 |要更改的节点 |
|------------------------|----------------|-----------------|
|更改单元格的数值 | `xl/worksheets/sheetN.xml` |目标 `<c>` 内的 `<v>` |
|更改单元格的文本 | `xl/sharedStrings.xml`（追加）+ `xl/worksheets/sheetN.xml` |新建 `<si>`，更新单元格 `<v>` 索引 |
|更改单元格的公式 | `xl/worksheets/sheetN.xml` |目标“<c>”内的“<f>”文本 |
|在底部添加新数据行 | `xl/worksheets/sheetN.xml` + 可能是 `xl/sharedStrings.xml` |追加 `<row>` 元素 |
|对单元格应用新样式 | `xl/styles.xml` + `xl/worksheets/sheetN.xml` |在 `<cellXfs>` 中附加 `<xf>`，更新 `<c>` 上的 `s` 属性 |
|重命名工作表 | `xl/workbook.xml` | “<sheet>”元素上的“name”属性 |
|重命名工作表（使用跨工作表公式）| `xl/workbook.xml` + 所有 `xl/worksheets/*.xml` | `name` 属性 + `<f>` 引用旧名称的文本 |

### 步骤 4 — 执行更改

使用编辑工具。编辑最小值。切勿重写整个文件。

有关每种操作类型的精确 XML 模式，请参阅第 4 节。

### 步骤 5 — 级联检查

在发生任何移动行或列位置的更改后，审核所有受影响的 XML 区域。参见第 5 节。

### 第 6 步 — 打包和验证```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
python3 SKILL_DIR/scripts/formula_check.py output.xlsx
```包脚本在创建 ZIP 之前验证 XML 的格式正确性。在打包之前修复任何报告的解析错误。打包后，运行“formula_check.py”以确认没有引入公式错误。

---

## 4. 用于常见编辑的精确 XML 模式

### 4.1 更改数字单元格值

在工作表 XML 中找到“<c r="B5">”元素并替换“<v>”文本。

**前：**```xml
<c r="B5">
  <v>1000</v>
</c>
```**之后（新值 1500）：**```xml
<c r="B5">
  <v>1500</v>
</c>
```规则：
- 不要添加或删除 `s` 属性（样式），除非显式更改样式。
- 不要添加 `t` 属性 — 数字省略 `t` 或使用 `t="n"`。
- 不要更改“r”属性（单元格引用）。

---

### 4.2 更改文本单元格值

文本单元格通过索引 (`t="s"`) 引用共享字符串表。您无法在不影响使用相同索引的所有其他单元格的情况下就地编辑字符串。安全的方法是附加一个新条目。

**之前 — 共享字符串文件 (`xl/sharedStrings.xml`)：**```xml
<sst count="4" uniqueCount="4">
  <si><t>Revenue</t></si>
  <si><t>Cost</t></si>
  <si><t>Margin</t></si>
  <si><t>Old Label</t></si>
</sst>
```**之后 - 追加新字符串，增加计数：**```xml
<sst count="5" uniqueCount="5">
  <si><t>Revenue</t></si>
  <si><t>Cost</t></si>
  <si><t>Margin</t></si>
  <si><t>Old Label</t></si>
  <si><t>New Label</t></si>
</sst>
```新字符串位于索引 4（从零开始）。

**之前 — 工作表 XML 中的单元格：**```xml
<c r="A7" t="s">
  <v>3</v>
</c>
```**之后-指向新索引：**```xml
<c r="A7" t="s">
  <v>4</v>
</c>
```规则：
- 切勿修改或删除现有的“<si>”条目。仅追加。
- `count` 和 `uniqueCount` 必须一起递增。
- 如果新字符串包含“&”、“<”或“>”，则转义它们：“&amp;”、“<”、“>”。
- 如果字符串有前导或尾随空格，请将“xml:space="preserve"”添加到“<t>”：```xml
  <si><t xml:space="preserve">  indented text  </t></si>
  ```---

### 4.3 更改公式

公式存储在“<f>”元素中**没有前导“=”**（与您在 Excel UI 中键入的内容不同）。

**前：**```xml
<c r="C10">
  <f>SUM(C2:C9)</f>
  <v>4800</v>
</c>
```**之后（扩展范围）：**```xml
<c r="C10">
  <f>SUM(C2:C11)</f>
  <v></v>
</c>
```规则：
- 更改公式时将“<v>”清除为空字符串。缓存的值现在已过时。
- 不要向公式单元格添加 `t="s"` 或任何类型属性。 “t”属性不存在或使用结果类型值，而不是公式标记。
- 跨工作表引用使用 `SheetName!CellRef`。如果工作表名称包含空格，请用单引号引起来：`'Q1 Data'!B5`。
- `<f>` 文本不得包含前导的 `=`。

**之前（将硬编码值转换为实时公式）：**```xml
<c r="D15">
  <v>95000</v>
</c>
```**后：**```xml
<c r="D15">
  <f>SUM(D2:D14)</f>
  <v></v>
</c>
```---

### 4.4 添加新数据行

附加在“<sheetData>”内最后一个“<row>”元素之后。 OOXML 中的行号从 1 开始，并且必须是连续的。

**之前（最后一行是第 10 行）：**```xml
  <row r="10">
    <c r="A10" t="s"><v>3</v></c>
    <c r="B10"><v>2023</v></c>
    <c r="C10"><v>88000</v></c>
    <c r="D10"><f>C10*1.1</f><v></v></c>
  </row>
</sheetData>
```**之后（附加新的第 11 行）：**```xml
  <row r="10">
    <c r="A10" t="s"><v>3</v></c>
    <c r="B10"><v>2023</v></c>
    <c r="C10"><v>88000</v></c>
    <c r="D10"><f>C10*1.1</f><v></v></c>
  </row>
  <row r="11">
    <c r="A11" t="s"><v>4</v></c>
    <c r="B11"><v>2024</v></c>
    <c r="C11"><v>96000</v></c>
    <c r="D11"><f>C11*1.1</f><v></v></c>
  </row>
</sheetData>
```规则：
- 行内的每个“<c>”必须将“r”设置为正确的单元格地址（例如“A11”）。
- 文本单元格需要 `t="s"` 和 `<v>` 中的共享字符串索引。数字单元格省略“t”。
- 公式单元格使用“<f>”和空的“<v>”。
- 如果您想要匹配样式，请复制上面行中的“s”属性。不要发明“styles.xml”中不存在的样式索引。
- 如果工作表包含 `<dimension>` 元素（例如，`<dimension ref="A1:D10"/>`），请更新它以包含新行：`<dimension ref="A1:D11"/>`。
- 如果工作表包含引用表的“<tableparts>”，请更新相应“xl/tables/tableN.xml”文件中表的“ref”属性。

---

### 4.5 添加新列

将新的“<c>”元素附加到每个现有的“<row>”，并更新“<cols>”部分（如果存在）。

**之前（行有 A–C 列）：**```xml
<cols>
  <col min="1" max="3" width="14" customWidth="1"/>
</cols>
<sheetData>
  <row r="1">
    <c r="A1" t="s"><v>0</v></c>
    <c r="B1" t="s"><v>1</v></c>
    <c r="C1" t="s"><v>2</v></c>
  </row>
  <row r="2">
    <c r="A2"><v>100</v></c>
    <c r="B2"><v>200</v></c>
    <c r="C2"><v>300</v></c>
  </row>
</sheetData>
```**之后（添加 D 列）：**```xml
<cols>
  <col min="1" max="3" width="14" customWidth="1"/>
  <col min="4" max="4" width="14" customWidth="1"/>
</cols>
<sheetData>
  <row r="1">
    <c r="A1" t="s"><v>0</v></c>
    <c r="B1" t="s"><v>1</v></c>
    <c r="C1" t="s"><v>2</v></c>
    <c r="D1" t="s"><v>5</v></c>
  </row>
  <row r="2">
    <c r="A2"><v>100</v></c>
    <c r="B2"><v>200</v></c>
    <c r="C2"><v>300</v></c>
    <c r="D2"><f>A2+B2+C2</f><v></v></c>
  </row>
</sheetData>
```规则：
- 在末尾添加一列（在最后一个现有列之后）是安全的 - 现有公式引用不会发生变化。
- 在中间插入一列会将所有列向右移动，这需要与行插入相同的级联更新（参见第 5 节）。
- 更新“<dimension>”元素（如果存在）。

---

### 4.6 修改或添加样式

样式使用多级间接引用链。阅读“ooxml-cheatsheet.md”以获取完整链。关键规则：**仅添加新条目，绝不修改现有条目**。

**场景：** 添加尚不存在的蓝色字体样式（用于硬编码输入单元格）。

**第 1 步 — 检查 `xl/styles.xml` 中是否已存在匹配的字体：**```xml
<!-- Look inside <fonts> for an existing blue font -->
<font>
  <color rgb="000000FF"/>
  <!-- other attributes -->
</font>
```如果找到，请记下其索引（“<fonts>”列表中从零开始的位置）。如果没有找到，请追加。

**第 2 步 — 如果需要，附加新字体：**

之前：```xml
<fonts count="3">
  <font>...</font>   <!-- index 0 -->
  <font>...</font>   <!-- index 1 -->
  <font>...</font>   <!-- index 2 -->
</fonts>
```后：```xml
<fonts count="4">
  <font>...</font>   <!-- index 0 -->
  <font>...</font>   <!-- index 1 -->
  <font>...</font>   <!-- index 2 -->
  <font>
    <b/>
    <sz val="11"/>
    <color rgb="000000FF"/>
    <name val="Calibri"/>
  </font>             <!-- index 3 (new) -->
</fonts>
```**步骤 3 — 在 `<cellXfs>` 中附加新的 `<xf>`：**

之前：```xml
<cellXfs count="5">
  <xf .../>   <!-- index 0 -->
  <xf .../>   <!-- index 1 -->
  <xf .../>   <!-- index 2 -->
  <xf .../>   <!-- index 3 -->
  <xf .../>   <!-- index 4 -->
</cellXfs>
```后：```xml
<cellXfs count="6">
  <xf .../>   <!-- index 0 -->
  <xf .../>   <!-- index 1 -->
  <xf .../>   <!-- index 2 -->
  <xf .../>   <!-- index 3 -->
  <xf .../>   <!-- index 4 -->
  <xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0"
      applyFont="1"/>   <!-- index 5 (new) -->
</cellXfs>
```**第 4 步 — 适用于目标细胞：**

之前：```xml
<c r="B3">
  <v>0.08</v>
</c>
```后：```xml
<c r="B3" s="5">
  <v>0.08</v>
</c>
```规则：
- 切勿删除或重新排序“<fonts>”、“<fills>”、“<borders>”、“<cellXfs>”中的现有条目。
- 附加时始终更新“count”属性。
- 新的 `cellXfs` 索引 = 附加之前的旧 `count` 值（从零开始：如果 count 为 5，则新索引为 5）。
- 自定义“numFmt”ID 必须为 164 或以上。 ID 0–163 是内置的，不得重新声明。
- 如果所需的样式已存在于文件中的其他位置（在类似的单元格上），请重用其“s”索引，而不是创建重复项。

---

### 4.7 重命名工作表

**只有“xl/workbook.xml”需要更改** - 除非跨表公式引用旧名称。

**之前（`xl/workbook.xml`）：**```xml
<sheet name="Sheet1" sheetId="1" r:id="rId1"/>
```**后：**```xml
<sheet name="Revenue" sheetId="1" r:id="rId1"/>
```**如果任何工作表中的任何公式引用旧名称，也更新它们：**

之前（`xl/worksheets/sheet2.xml`）：```xml
<c r="B5"><f>Sheet1!C10</f><v></v></c>
```后：```xml
<c r="B5"><f>Revenue!C10</f><v></v></c>
```如果新名称包含空格：```xml
<c r="B5"><f>'Q1 Revenue'!C10</f><v></v></c>
```扫描所有工作表 XML 文件以查找旧名称：```bash
grep -r "Sheet1!" /tmp/xlsx_work/xl/worksheets/
```规则：
- `.rels` 文件和 `[Content_Types].xml` 不需要更改 — 它们引用 XML 文件路径，而不是工作表名称。
- `sheetId` 不得更改；它是一个稳定的内部标识符。
- 公式引用中的工作表名称区分大小写。

---

## 5. 高风险操作——级联效应

### 5.1 在中间插入一行

在位置 N 插入一行会将 N 处的所有行向下移动。每个 XML 文件中对这些行的每个引用都必须更新。

**要检查和更新的文件：**

| XML 区域 |更新什么 |示例班次|
|------------|----------------|---------------|
|工作表 `<row r="...">` 属性 |增加所有行的行号 >= N | `r="7"` → `r="8"` |
|这些行中的所有 `<c r="...">` |增加单元格地址中的行号 | `r="A7"` → `r="A8"` |
|任何工作表中的所有“<f>”公式文本 |移动绝对行引用 >= N | `B7` → `B8` |
| `<mergeCell ref="...">` |移动起始行和结束行 | `A7:C7` → `A8:C8` |
| `<conditionalFormatting sqref="...">` |换挡范围| `A5:D20` → `A5:D21` |
| `<dataValidations sqref="...">` |换挡范围| `B6:B50` → `B7:B51` |
| `xl/charts/chartN.xml` 数据源范围 | Shift 系列范围 | `工作表 1!$B$5:$B$20` → `工作表 1!$B$6:$B$21` |
| `xl/pivotTables/*.xml` 源范围 |移动源数据范围 |处理时要格外小心 — 请参阅第 7 节 |
| `<尺寸参考=“...”>` |扩展以包含新范围 | `A1:D20` → `A1:D21` |
| `xl/tables/tableN.xml` `ref` 属性 |扩展表格边界| `A1:D20` → `A1:D21` |

**不要尝试在大型文件或公式较多的文件中手动插入行。** 请改用专用的移位脚本：```bash
# Insert 1 row at row 5: all rows 5 and below shift down by 1
python3 SKILL_DIR/scripts/xlsx_shift_rows.py /tmp/xlsx_work/ insert 5 1

# Delete 1 row at row 8: all rows 9 and above shift up by 1
python3 SKILL_DIR/scripts/xlsx_shift_rows.py /tmp/xlsx_work/ delete 8 1
```该脚本一次性更新：`<row r="...">` 属性、`<c r="...">` 单元格地址、每个工作表中的所有 `<f>` 公式文本、`<mergeCell>` 范围、`<conditionalFormatting sqref="...">`、`<dataValidation sqref="...">`、`<dimension ref="...">`、`xl/tables/` 中的表格 `ref` 属性、`xl/charts/` 中的图表系列范围，以及`xl/pivotCaches/` 中的数据透视缓存源范围。

**运行shift脚本后，始终重新打包并验证：**```bash
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
python3 SKILL_DIR/scripts/formula_check.py output.xlsx
```**脚本未更新的内容（手动查看）：**
- `xl/workbook.xml` `<defineNames>` 中的命名范围 — 检查并更新它们是否引用移位的行。
- 公式内的结构化表引用（`Table[@Column]`）。
- `xl/externalLinks/` 中的外部工作簿链接。

### 5.2 在中间插入一列

与行插入相同的级联逻辑，但针对列。公式（“B”、“$C”等）以及合并单元格区域、条件格式区域和图表数据源中的列引用都需要更新。

列字母移动更难安全地实现自动化。尽可能首选**在末尾附加列**。

### 5.3 删除行或列

删除比插入更危险，因为任何引用已删除行或列的公式都将变成“#REF!”。删除前：

1. 搜索所有“<f>”元素以查找对已删除范围的引用。
2. 如果任何公式引用已删除的行/列中的单元格，请勿删除 - 相反，请清除该行的数据或咨询用户。
3. 删除后，将所有对删除点以外的行/列的引用向下/向左移动。

---

## 6. 模板填充 — 识别和填充输入单元格

模板将某些单元格指定为输入区域。识别它们的常见模式：

### 6.1 模板如何向输入区域发出信号

|信号| XML表现|寻找什么 |
|--------|--------------------|-----------------|
|蓝色字体颜色 | `s` 属性指向带有 `fontId` 的 `cellXfs` 条目 → `<color rgb="000000FF"/>` |检查“styles.xml”以解码“s”值 |
|黄色填充（突出显示）| `s` → `fillId` → `<fill><patternFill><fgColor rgb="00FFFF00"/>` | |
|空 `<v>` 元素 | `<c r="B5"><v></v></c>` 或 `<row>` 中完全不存在的单元格 |该单元格还没有任何值 |
|单元格附近的评论/注释 | `xl/comments1.xml` 与 `ref="B5"` |注释通常会标记输入字段 |
|命名范围 | `xl/workbook.xml` `<定义名称>` 元素 |模板可以定义 `InputRevenue` 等。

### 6.2 填充模板单元格

不要更改 `s` 属性。不要更改“t”属性，除非必须从空更改为类型。仅更改“<v>”或添加“<f>”。

**之前（保留样式的空输入单元格）：**```xml
<c r="C5" s="3">
  <v></v>
</c>
```**之后（填充数字，样式不变）：**```xml
<c r="C5" s="3">
  <v>125000</v>
</c>
```**之后（填充文本 - 需要首先输入共享字符串）：**```xml
<!-- 1. Append to sharedStrings.xml: <si><t>North Region</t></si> at index 7 -->
<c r="C5" t="s" s="3">
  <v>7</v>
</c>
```**之后（填充公式，保留风格）：**```xml
<c r="C5" s="3">
  <f>Assumptions!D12</f>
  <v></v>
</c>
```### 6.3 无需在 Excel 中打开文件即可定位输入区域

解压后，解码可疑输入单元格上的样式索引，以确定它们是否具有模板的输入颜色：

1. 记下单元格上的“s”值（例如“s=”4“”）。
2. 在 `xl/styles.xml` 中，找到 `<cellXfs>` 并查看第 5 个条目（索引 4）。
3. 记下其 `fontId`（例如，`fontId="2"`）。
4. 在“<fonts>”中，查看第三个条目（索引 2）并检查“<color rgb="000000FF"/>”（蓝色）或其他输入标记。

如果模板使用命名范围作为输入字段，请从“xl/workbook.xml”中读取它们：```xml
<definedNames>
  <definedName name="InputGrowthRate">Assumptions!$B$5</definedName>
  <definedName name="InputDiscountRate">Assumptions!$B$6</definedName>
</definedNames>
```直接填写目标单元格（“假设！B5”、“假设！B6”）。

### 6.4 模板填写规则

- 仅填充模板指定为输入的单元格。不要填充公式驱动的单元格。
- 填充时不要应用新样式。模板的格式是可交付成果。
- 不要在模板数据区域内添加或删除行，除非模板明确具有“附加到此处”区域。
- 填写后，验证是否引入公式错误：某些模板具有输入验证公式，如果输入错误的数据类型，则会生成“#VALUE！”。

---

## 7. 绝对不能修改的文件

### 7.1 绝对非接触列表

|文件/位置|为什么 |
|-----------------|-----|
| `xl/vbaProject.bin` |二进制 VBA 字节码。任何字节修改都会破坏宏项目。即使编辑一位也会导致宏无法加载。 |
| `xl/pivotCaches/pivotCacheDefinition*.xml` |缓存定义将数据透视表与其源数据联系起来。编辑它而不更新相应的“pivotTable*.xml”将会损坏数据透视表。 |
| `xl/pivotTables/*.xml` |数据透视表 XML 与缓存定义以及加载时 Excel 重建的内部状态紧密耦合。不要编辑。如果您移动了行并且数据透视表的源范围现在指向错误的数据，则仅更新缓存定义中的“<cacheSource>”范围，并且仅更新数据透视表中的“ref”属性 - 没有其他更改。 |
| `xl/slicers/*.xml` |切片器连接到特定的缓存 ID 和数据透视字段。静默地断开这些连接会损坏文件。 |
| `xl/connections.xml` |外部数据连接。编辑会中断实时数据刷新。 |
| `xl/externalLinks/` |外部工作簿链接。此处的二进制“.bin”文件不得修改。 |

### 7.2 有条件安全的文件（仅更新特定属性）

|文件 |您可能会更新什么 |独自留下什么|
|------|--------------------|--------------------|
| `xl/charts/chartN.xml` |行/列移位后的数据系列范围引用 (`<numRef><f>`) |图表类型、格式、布局 |
| `xl/tables/tableN.xml` |添加行后“<table>”上的“ref”属性 |列定义、样式信息 |
| `xl/pivotCaches/pivotCacheDefinition*.xml` |移动源数据后“<cacheSource><worksheetSource>”上的“ref”属性 |所有其他内容 |

---

## 8. 每次编辑后验证

切勿跳过验证。即使公式中的一个字符发生变化也可能导致级联错误。```bash
# Pack
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx

# Static formula validation (always run)
python3 SKILL_DIR/scripts/formula_check.py output.xlsx

# Dynamic validation (if LibreOffice available)
python3 SKILL_DIR/scripts/libreoffice_recalc.py output.xlsx /tmp/recalc.xlsx
python3 SKILL_DIR/scripts/formula_check.py /tmp/recalc.xlsx
```如果 `formula_check.py` 报告任何错误：
1. 再次解压输出文件（这是加壳版本）。
2. 在工作表 XML 中找到报告的单元格。
3. 修复`<f>`元素。
4. 重新包装并重新验证。

在 `formula_check.py` 报告零错误之前不要传送文件。

---

## 9. 绝对规则总结

|规则|理由|
|------|------------|
|切勿在现有文件上使用 openpyxl `load_workbook` + `save` |往返会破坏数据透视表、VBA、迷你图、切片器 |
|切勿删除或重新排序sharedStrings | 中现有的“<si>”条目。打破引用该索引的每个单元格 |
|切勿删除或重新排序“<cellXfs>”中现有的“<xf>”条目 |使用该样式索引打破每个单元格 |
|切勿修改`vbaProject.bin` |二进制文件；任何更改都会破坏 VBA |
|重命名工作表时切勿更改“sheetId”|内部ID稳定；改变它会破坏关系|
|切勿跳过编辑后验证 |使损坏的引用未被发现|
|切勿编辑超出所需数量的 XML 节点 |额外的改变可能会带来微妙的腐败|
|更改公式时将 `<v>` 清除为空字符串 |防止过时的缓存值误导下游消费者 |
|仅附加到共享字符串 |现有索引必须保持有效 |
|仅附加到样式集合 |现有样式索引必须保持有效 |