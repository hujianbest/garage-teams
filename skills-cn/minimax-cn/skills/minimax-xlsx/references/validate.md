# 公式验证和重新计算指南

在交付前确保 xlsx 文件中的每个公式都可证明是正确的。打开且没有可见错误的文件不是通过文件 — 只有已通过两个验证层的文件才是通过文件。

---

## 基本规则

- **在未先运行 `formula_check.py` 的情况下切勿声明 PASS。** 电子表格的目视检查不是验证。
- **第 1 层（静态）在每种情况下都是强制的。** 当 LibreOffice 可用时，第 2 层（动态）是强制的。如果不可用，您必须在报告中明确说明这一点 - 您不能默默地跳过它。
- **切勿将 openpyxl 与 `data_only=True` 一起使用来检查公式值。** 在 `data_only=True` 模式下打开和保存工作簿会将所有公式永久替换为最后缓存的值。之后配方无法恢复。
- **仅自动修复确定性错误。** 任何需要理解业务逻辑的修复都必须标记为供人工审核。

---

## 两层验证架构```
Tier 1 — Static Validation (XML scan, no external tools)
  │
  ├── Detect: all 7 Excel error types already cached in <v> elements
  ├── Detect: cross-sheet references pointing to nonexistent sheets
  ├── Detect: formula cells with t="e" attribute (error type marker)
  └── Tool: formula_check.py + manual XML inspection
        │
        ▼ (if LibreOffice is present)
Tier 2 — Dynamic Validation (LibreOffice headless recalculation)
  │
  ├── Executes all formulas via the LibreOffice Calc engine
  ├── Populates <v> cache values with real computed results
  ├── Exposes runtime errors invisible before recalculation
  └── Follow-up: re-run Tier 1 on the recalculated file
```**为什么有两层？**

openpyxl 和所有 Python xlsx 库将公式字符串（例如 `=SUM(B2:B9)`）写入 `<f>` 元素，但不计算它们。新生成的文件的每个公式单元格都有空的“<v>”缓存元素。这意味着：

- 第 1 层只能捕获已编码在 XML 中的错误 - 无论是作为“t="e”单元格还是结构上损坏的跨表引用。
- 第 2 层使用 LibreOffice 作为实际计算引擎，运行每个公式，用真实结果填充 `<v>`，并显示仅在计算后才会出现的运行时错误（`#DIV/0!`、`#N/A` 等）。

仅靠这两层是不够的。它们一起覆盖了整个可校正性表面。

---

## 第 1 层 — 静态验证

静态验证不需要外部工具。它直接作用于 xlsx 文件的 ZIP/XML 结构。

### 第 1 步：运行 Formula_check.py

**标准（人类可读）输出：**```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx
```**JSON 输出（用于编程处理）：**```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx --json
```**单页模式（目标检查速度更快）：**```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx --sheet Summary
```**摘要模式（仅计数，没有每个单元格的详细信息）：**```bash
python3 SKILL_DIR/scripts/formula_check.py /path/to/file.xlsx --summary
```退出代码：
- `0` — 无硬错误（通过或带有启发式警告的通过）
- `1` — 检测到硬错误，或文件无法打开（失败）

#### Formula_check.py 检查什么

该脚本将 xlsx 作为 ZIP 存档打开，而不使用任何 Excel 库。它读取“xl/workbook.xml”以枚举工作表名称和命名范围，读取“xl/_rels/workbook.xml.rels”以将每个工作表映射到其 XML 文件，然后迭代每个工作表中的每个“<c>”元素。

它执行五项检查：

1. **错误值检测**：如果单元格具有`t="e"`，则其`<v>`元素包含Excel错误字符串。记录单元格及其工作表名称、单元格引用（例如“C5”）、错误值以及公式文本（如果存在）。

2. **损坏的跨工作表引用检测**：如果单元格具有“<f>”元素，则脚本会提取公式中引用的所有工作表名称（“SheetName!”和“'Sheet Name'!”语法）。每个名称都会与“workbook.xml”中的工作表列表进行比较。不匹配是一个损坏的参考。

3. **未知命名范围检测（启发式）**：公式中不是函数名称、不是单元格引用且在“workbook.xml”的“<defineNames>”中找不到的标识符将被标记为“unknown_name_ref”警告。这是一种启发式方法——误报是可能的；始终手动验证。

4. **共享公式完整性**：共享公式使用者单元格（仅具有 `<f t="shared" si="N"/>` 的单元格）将被跳过进行公式计数和交叉引用检查，因为它们继承了主单元格的公式。仅检查和计数主单元格（具有“ref=”...“”属性和公式文本）。

5. **格式错误的错误单元格**：带有 `t="e"` 但没有 `<v>` 子元素的单元格被标记为结构性 XML 问题。

硬错误（退出代码 1）：“error_value”、“broken_sheet_ref”、“malformed_error_cell”、“file_error”
软警告（退出代码 0）：`unknown_name_ref` — 必须手动验证，但不要单独阻止交付

#### 读取 Formula_check.py 人类可读的输出

一个干净的文件看起来像这样：```
File   : /tmp/budget_2024.xlsx
Sheets : Summary, Q1, Q2, Q3, Q4, Assumptions
Formulas checked      : 312 distinct formula cells
Shared formula ranges : 4 ranges
Errors found          : 0

PASS — No formula errors detected
```有错误的文件如下所示：```
File   : /tmp/budget_2024.xlsx
Sheets : Summary, Q1, Q2, Q3, Q4, Assumptions
Formulas checked      : 312 distinct formula cells
Shared formula ranges : 4 ranges
Errors found          : 4

── Error Details ──
  [FAIL] [Summary!C12] contains #REF! (formula: Q1!A0/Q1!A1)
  [FAIL] [Summary!D15] references missing sheet 'Q5'
         Formula: Q5!D15
         Valid sheets: ['Assumptions', 'Q1', 'Q2', 'Q3', 'Q4', 'Summary']
  [FAIL] [Q1!F8] contains #DIV/0!
  [WARN] [Q2!B10] uses unknown name 'GrowthAssumptions' (heuristic — verify manually)
         Formula: SUM(GrowthAssumptions)
         Defined names: ['RevenueRange', 'CostRange']

FAIL — 3 error(s) must be fixed before delivery
WARN — 1 heuristic warning(s) require manual review
```每行解释：
- `[失败] [摘要！C12] 包含#REF！ （公式：Q1!A0/Q1!A1）` — 单元格具有 `t="e"` 和 `<v>#REF!</v>`。该公式引用第 0 行，该行在 Excel 基于 1 的系统中不存在。这是生成的参考中的一个相差一错误。
- `[FAIL] [Summary!D15] 引用缺少工作表 'Q5'` — 公式包含 `Q5!D15`，但工作簿中不存在名为 `Q5` 的工作表。提供有效的图纸列表以供比较。
- `[FAIL] [Q1!F8] contains #DIV/0!` — 此单元格的 `<v>` 已经是错误值（该文件之前已重新计算）。该公式除以零。
- `[WARN] [Q2!B10] 使用未知名称 'GrowthAsspirations'` — 标识符 `GrowthAsminations` 出现在公式中，但不在 `<defineNames>` 中。这可能是拼写错误或意外遗漏的名称。这是一个启发式警告——手动验证。仅警告并不会阻止交付。

#### 读取 Formula_check.py JSON 输出```json
{
  "file": "/tmp/budget_2024.xlsx",
  "sheets_checked": ["Summary", "Q1", "Q2", "Q3", "Q4", "Assumptions"],
  "formula_count": 312,
  "shared_formula_ranges": 4,
  "error_count": 4,
  "errors": [
    {
      "type": "error_value",
      "error": "#REF!",
      "sheet": "Summary",
      "cell": "C12",
      "formula": "Q1!A0/Q1!A1"
    },
    {
      "type": "broken_sheet_ref",
      "sheet": "Summary",
      "cell": "D15",
      "formula": "Q5!D15",
      "missing_sheet": "Q5",
      "valid_sheets": ["Assumptions", "Q1", "Q2", "Q3", "Q4", "Summary"]
    },
    {
      "type": "error_value",
      "error": "#DIV/0!",
      "sheet": "Q1",
      "cell": "F8",
      "formula": null
    },
    {
      "type": "unknown_name_ref",
      "sheet": "Q2",
      "cell": "B10",
      "formula": "SUM(GrowthAssumptions)",
      "unknown_name": "GrowthAssumptions",
      "defined_names": ["RevenueRange", "CostRange"],
      "note": "Heuristic check — verify manually if this is a false positive"
    }
  ]
}
```现场参考：

|领域|意义|
|--------|---------|
| `类型：“错误值”` |单元格具有 `t="e"` — Excel 错误存储在 `<v>` 元素中 |
| `类型：“broken_sheet_ref”` |公式引用了 workbook.xml 中不存在的工作表名称 |
| `类型：“unknown_name_ref”` |公式引用了不在 `<defineNames>` 中的标识符（启发式、软警告） |
| `类型：“格式错误_单元格”` | Cell 有 `t="e"` 但没有 `<v>` 子元素 — 结构性 XML 问题 |
| `类型：“文件错误”` |文件无法打开（ZIP 错误、未找到等）|
| `表` |发现错误的表 |
| `细胞` | A1 表示法中的单元格引用 |
| `公式` |来自“<f>”元素的完整公式文本（如果不存在则为 null）|
| `错误` |来自“<v>”的错误字符串（对于“error_value”类型）|
| `缺失表` |从不存在的公式中提取的工作表名称|
| `有效表` | workbook.xml 中实际存在的所有工作表名称 |
| `未知名称` |在 `<defineNames>` 中找不到标识符 |
| `已定义的名称` |所有命名范围实际上都存在于workbook.xml |
| `共享公式范围` |共享公式定义的计数（顶级 `<f t="shared" ref="...">` 元素）|

### 步骤 2：手动 XML 检查

当 Formula_check.py 报告错误时，解压文件以检查原始 XML：```bash
python3 SKILL_DIR/scripts/xlsx_unpack.py /path/to/file.xlsx /tmp/xlsx_inspect/
```导航到报告工作表的工作表文件。工作表到文件的映射位于“xl/_rels/workbook.xml.rels”中。例如，如果`rId1`映射到`worksheets/sheet1.xml`，则sheet1.xml是`xl/workbook.xml`中带有`r:id="rId1"`的工作表的文件。

对于每个报告的错误单元格，找到“<c r="CELLREF">”元素并检查：

**对于“error_value”错误：**```xml
<!-- This is what an error cell looks like in XML -->
<c r="C12" t="e">
  <f>Q1!C10/Q1!C11</f>
  <v>#DIV/0!</v>
</c>
```问：
- `<f>` 公式语法正确吗？
- 公式中的单元格引用是否指向存在的行/列？
- 如果是除法，分母格是否有可能为空或为零？

**对于 `broken_sheet_ref` 错误：**

检查“xl/workbook.xml”以获取实际的工作表列表：```xml
<sheets>
  <sheet name="Summary" sheetId="1" r:id="rId1"/>
  <sheet name="Q1"      sheetId="2" r:id="rId2"/>
  <sheet name="Q2"      sheetId="3" r:id="rId3"/>
</sheets>
```工作表名称区分大小写。 `q1` 和 `Q1` 是不同的表。将公式中的名称与此处的名称完全进行比较。

### 步骤 3：跨表参考审核（多表工作簿）

对于具有 3 个或更多工作表的工作簿，请在解压后运行更广泛的交叉引用审核：```bash
# Extract all formulas containing cross-sheet references
grep -h "<f>" /tmp/xlsx_inspect/xl/worksheets/*.xml | grep "!"

# List all actual sheet names from workbook.xml
grep -o 'name="[^"]*"' /tmp/xlsx_inspect/xl/workbook.xml | grep -v sheetId
```公式中出现的每个工作表名称（格式为“SheetName!”或“Sheet Name”!）必须出现在工作簿工作表列表中。如果有任何不匹配，即使 Formula_check.py 没有捕获它，这也是一个损坏的引用（这可能发生在仅检查主单元格的共享公式中）。

要专门检查共享公式，请查找 `<ft="shared" ref="...">` 元素：```xml
<!-- Shared formula: defined on D2, applied to D2:D100 -->
<c r="D2"><f t="shared" ref="D2:D100" si="0">Q1!B2*C2</f><v></v></c>

<!-- Shared formula consumers: only si is present, no formula text -->
<c r="D3"><f t="shared" si="0"/><v></v></c>
```Formula_check.py 从主单元格（上面的“D2”）读取公式文本。该公式中引用的工作表“Q1”适用于整个范围“D2:D100”。如果工作表损坏，所有 99 行都会损坏，即使它们显示为空的“<f>”元素。

---

## 第 2 层 — 动态验证（LibreOffice Headless）

### 检查 LibreOffice 可用性```bash
# Check macOS (typical install location)
which soffice
/Applications/LibreOffice.app/Contents/MacOS/soffice --version

# Check Linux
which libreoffice || which soffice
libreoffice --version
```如果两个命令都没有返回路径，则表明 LibreOffice 未安装。在报告中记录“第 2 层：已跳过 — LibreOffice 不可用”，然后仅交付第 1 层结果。

### 安装 LibreOffice（如果环境允许）

苹果系统：```bash
brew install --cask libreoffice
```Ubuntu/Debian：```bash
sudo apt-get install -y libreoffice
```### 运行无头重新计算

使用专用的重新计算脚本。它处理跨 macOS 和 Linux 的二进制发现，从输入的临时副本（保留原始）工作，并提供与验证管道兼容的结构化输出和退出代码。```bash
# Check LibreOffice availability first
python3 SKILL_DIR/scripts/libreoffice_recalc.py --check

# Run recalculation (default timeout: 60s)
python3 SKILL_DIR/scripts/libreoffice_recalc.py /path/to/input.xlsx /tmp/recalculated.xlsx

# For large or complex files, extend the timeout
python3 SKILL_DIR/scripts/libreoffice_recalc.py /path/to/input.xlsx /tmp/recalculated.xlsx --timeout 120
````libreoffice_recalc.py` 的退出代码：
- `0` — 重新计算成功，输出文件已写入
- `2` — LibreOffice 未找到（请注意报告中已跳过；不是硬故障）
- `1` — LibreOffice 已找到但失败（超时、崩溃、文件格式错误）

**脚本内部的作用：**

LibreOffice 的“--convert-to xlsx”命令使用完整的 Calc 引擎和“--infilter="Calc MS Excel 2007 XML"”过滤器打开文件，执行每个公式，将计算值写入“<v>”缓存元素，并保存输出。这是与“在 Excel 中打开并按保存”最接近的服务器端等效项。该脚本还传递“--norestore”以防止 LibreOffice 尝试恢复以前的会话，这可能会导致自动化环境中挂起。

**如果未安装 LibreOffice：**

苹果系统：```bash
brew install --cask libreoffice
```Ubuntu/Debian：```bash
sudo apt-get install -y libreoffice
```**如果脚本超时（libreoffice_recalc.py 退出并显示代码 1 和“超时”消息）：**

在报告中记录“第 2 层：超时 — LibreOffice 未在 N 秒内完成”。不要循环重试。调查文件是否具有循环引用或极大的数据范围。

### 重新计算后重新运行第 1 层

LibreOffice 重新计算后，“<v>”元素包含真实的计算值。以前不可见的错误（因为“<v>”在新生成的文件中为空）现在显示为带有实际错误字符串的“t="e”单元格。```bash
python3 SKILL_DIR/scripts/formula_check.py /tmp/recalculated.xlsx
```第二次第 1 层检查是最终的运行时错误检查。它发现的任何错误都是真正的计算失败，必须修复。

---

## 所有 7 种错误类型 — 原因和修复策略

### #参考！ — 无效的单元格引用

**含义：** 公式引用不再存在或从未存在的单元格、区域或工作表。

**生成文件中的常见原因：**
- 行/列计算中存在差一错误（例如，引用 Excel 的基于 1 的系统中不存在的行 0）
- 列字母计算不正确（例如，第 64 列映射到“BL”，而不是“BK”）
- 公式引用从未创建或重命名的工作表

**XML 签名：**```xml
<c r="D5" t="e">
  <f>Sheet2!A0</f>
  <v>#REF!</v>
</c>
```**修复 — 更正参考：**```xml
<c r="D5">
  <f>Sheet2!A1</f>
  <v></v>
</c>
```注意：更正公式后删除`t="e"`并清除`<v>`。错误类型标记属于缓存状态，而不是公式。

**可自动修复？** 仅当可以从周围环境中确定正确的目标时。否则标记为供人工审核。

---

### #DIV/0！ — 除以零

**含义：** 该公式除以零值或空单元格（空单元格在算术上下文中计算结果为 0）。

**生成文件中的常见原因：**
- 百分比变化公式`=(B2-B1)/B1`，其中`B1`为空或零
- 费率公式“=值/总计”，其中尚未填充总计行

**XML 签名：**```xml
<c r="C8" t="e">
  <f>B8/B7</f>
  <v>#DIV/0!</v>
</c>
```**修复 — 用 IFERROR 换行：**```xml
<c r="C8">
  <f>IFERROR(B8/B7,0)</f>
  <v></v>
</c>
```替代方案 - 显式零检查：```xml
<c r="C8">
  <f>IF(B7=0,0,B8/B7)</f>
  <v></v>
</c>
```**可自动修复？** 是的。对于大多数金融公式来说，用“IFERROR(...,0)”包装是安全的。如果业务期望结果应显示为空白而不是零，请改用“IFERROR(...,"")”。

 - -

＃＃＃ ＃价值！ — 错误的数据类型

**含义：** 该公式尝试对错误类型的值进行算术或逻辑运算（例如，将文本字符串添加到数字中）。

**生成文件中的常见原因：**
- 用于保存数字的单元格被写入字符串类型（`t="s"` 或 `t="inlineStr"`）而不是数字类型
- 公式引用包含文本的单元格（例如，“千”等单位标签）并将其视为数字

**XML 签名：**```xml
<c r="F3" t="e">
  <f>E3+D3</f>
  <v>#VALUE!</v>
</c>
```**修复 - 检查源单元格的类型是否不正确：**

如果 `D3` 被错误地写为字符串：```xml
<!-- Wrong: numeric value stored as string -->
<c r="D3" t="inlineStr"><is><t>1000</t></is></c>

<!-- Correct: numeric value stored as number (t attribute omitted or "n") -->
<c r="D3"><v>1000</v></c>
```或者，使用“VALUE()”转换包装公式：```xml
<c r="F3">
  <f>VALUE(E3)+VALUE(D3)</f>
  <v></v>
</c>
```**可自动修复？** 部分。如果源单元格类型明显错误（数字存储为字符串），请修复该类型。如果原因不明确（单元格应该包含文本），则标记为供人工审核。

 - -

＃＃＃ ＃姓名？ — 无法识别的名字

**含义：** 公式包含 Excel 无法识别的标识符 - 拼写错误的函数名称、未定义的命名范围或目标 Excel 版本中不可用的函数。

**生成文件中的常见原因：**
- LLM 编写的函数名称存在拼写错误：仅提供 3 个参数时，“SUMIF”写为“SUMIFS”，或者在面向 Excel 2010 的上下文中使用“XLOOKUP”
- 公式中引用的命名范围在“xl/workbook.xml”中不存在

**XML 签名：**```xml
<c r="B2" t="e">
  <f>SUMSQ(A2:A10)</f>
  <v>#NAME?</v>
</c>
```**修复 - 验证函数名称和命名范围：**

检查“xl/workbook.xml”中的命名范围：```xml
<definedNames>
  <definedName name="RevenueRange">Sheet1!$B$2:$B$13</definedName>
</definedNames>
```如果公式引用“RevenueRange”（拼写错误），请将其更正为“RevenueRange”：```xml
<c r="B2">
  <f>SUM(RevenueRange)</f>
  <v></v>
</c>
```**可自动修复？** 仅当正确名称明确时（例如，存在单个紧密匹配）。否则，需要进行人工审查标记 - 函数名称修复需要了解预期的计算。

---

### #N/A — 值不可用

**含义：** 查找函数（VLOOKUP、HLOOKUP、MATCH、INDEX/MATCH、XLOOKUP）搜索查找表中不存在的值。

**生成文件中的常见原因：**
- 公式中存在查找键，但查找表为空或尚未填充
- 密钥格式不匹配（文本“2024”与数字 2024）

**XML 签名：**```xml
<c r="G5" t="e">
  <f>VLOOKUP(F5,Assumptions!$A$2:$B$20,2,0)</f>
  <v>#N/A</v>
</c>
```**修复 — 用 IFERROR 包裹以实现缺失匹配容错：**```xml
<c r="G5">
  <f>IFERROR(VLOOKUP(F5,Assumptions!$A$2:$B$20,2,0),0)</f>
  <v></v>
</c>
```**可自动修复？** 如果可以接受零默认值，则添加“IFERROR”是安全的。如果查找失败表明存在数据完整性问题（密钥应始终存在），则不要自动修复 - 标记以供人工审核。

 - -

＃＃＃ ＃无效的！ — 空的路口

**含义：** 空间运算符（计算两个范围的交集）应用于两个不相交的范围。

**生成文件中的常见原因：**
- 两个范围引用之间的意外空格：`=SUM(A1:A5 C1:C5)` 而不是 `=SUM(A1:A5,C1:C5)`
- 在典型的金融模型中很少见；通常表示公式生成错误

**XML 签名：**```xml
<c r="H10" t="e">
  <f>SUM(A1:A5 C1:C5)</f>
  <v>#NULL!</v>
</c>
```**修复 - 用逗号（联合）或冒号（范围）替换空格：**```xml
<!-- Union of two separate ranges -->
<c r="H10">
  <f>SUM(A1:A5,C1:C5)</f>
  <v></v>
</c>
```**可自动修复？** 是的。在生成的公式中几乎从来没有有意使用空格运算符。用逗号替换是安全的。

---

### #NUM！ — 数字错误

**含义：** 公式生成 Excel 无法表示的数字（上溢、下溢）或没有实数结果的数学运算（负数的平方根、零或负数的 LOG）。

**生成文件中的常见原因：**
- IRR 或 NPV 公式，其中现金流系列没有收敛解
- `SQRT()` 应用于可以为负的单元格
- 非常大的指数

**XML 签名：**```xml
<c r="J15" t="e">
  <f>IRR(B5:B15)</f>
  <v>#NUM!</v>
</c>
```**修复 - 添加条件保护：**```xml
<c r="J15">
  <f>IFERROR(IRR(B5:B15),"")</f>
  <v></v>
</c>
```对于平方根：```xml
<c r="K5">
  <f>IF(A5>=0,SQRT(A5),"")</f>
  <v></v>
</c>
```**可自动修复？** 部分。使用“IFERROR”换行可以抑制错误显示，但不能解决根本的计算问题。即使在应用 IFERROR 包装器之后，也会对单元格进行标记以供人工审核。

---

## 自动修复与人工审核决策矩阵

|错误类型 |自动修复安全吗？ |状况 |行动|
|------------|-------------|------------|--------|
| `#DIV/0！` |是的 |永远 |用 `IFERROR(formula,0)` 换行 |
| `#NULL！` |是的 |永远 |将空格运算符替换为逗号 |
| `#REF！` |是的 |仅当正确的目标从上下文来看是明确的 |正确参考；否则标记 |
| `#NAME？` |是的 |仅当拼写错误恰好有一个合理的更正时 |修正名称；否则标记 |
| `#N/A` |有条件|如果零/空白默认值是业务可接受的 |添加 IFERROR 包装器；文件假设|
| `#VALUE！` |有条件|仅当源细胞类型明显错误时 |固定式；否则标记 |
| `#NUM！` |没有 |永远 |添加 IFERROR 来抑制显示，然后标记 |
|破损的纸张参考 |是的 |仅当重命名的工作表可以从 workbook.xml 中识别时 |正确的名字|
|业务逻辑错误 |从来没有|任何情况 |仅限人工审核 |

**什么算作业务逻辑错误（从不自动修复）：**
- 生成错误数字但不出现 Excel 错误的公式（例如，当意图是“=SUM(B2:B9)”时，会生成“=SUM(B2:B8)”）
- IFERROR 默认值有意义的公式（例如，是否使用 0、空白或前期值）
- 修复错误的任何公式都需要知道该公式应该计算什么

---

## 交付标准——验证报告

每个验证任务都必须生成结构化报告。无论是否发现错误，该报告都是可交付成果。

### 所需的报告格式```markdown
## Formula Validation Report

**File**: /path/to/filename.xlsx
**Date**: YYYY-MM-DD
**Sheets checked**: Sheet1, Sheet2, Sheet3
**Total formulas scanned**: N

---

### Tier 1 — Static Validation

**Status**: PASS / FAIL
**Tool**: formula_check.py (direct XML scan)

| Sheet | Cell | Error Type | Detail | Fix Applied |
|-------|------|-----------|--------|-------------|
| Summary | C12 | #REF! | Formula: Q1!A0 | Corrected to Q1!A1 |
| Summary | D15 | broken_sheet_ref | References missing sheet 'Q5' | Renamed to Q4 |

_(If no errors: "No errors detected.")_

---

### Tier 2 — Dynamic Validation

**Status**: PASS / FAIL / SKIPPED
**Tool**: LibreOffice headless (version X.Y.Z) / Not available

_(If SKIPPED: state the reason — LibreOffice not installed, timeout, etc.)_

| Sheet | Cell | Error Type | Detail | Fix Applied |
|-------|------|-----------|--------|-------------|
| Q1 | F8 | #DIV/0! | Formula: C8/C7 | Wrapped with IFERROR |

_(If no errors: "No runtime errors detected after recalculation.")_

---

### Summary

- **Total errors found**: N
- **Auto-fixed**: N (list types)
- **Flagged for human review**: N (list cells and reason)
- **Final status**: PASS (ready for delivery) / FAIL (blocked)

### Human Review Required

| Cell | Error | Reason Auto-Fix Not Applied |
|------|-------|----------------------------|
| Q2!B15 | #NUM! | IRR formula — business must confirm cash flow inputs |
```### 最少必填字段

如果缺少以下任何一项，则报告无效（并且发送被阻止）：
- 文件路径和日期
- 检查了哪些表
- 配方总数
- 具有明确通过/失败的 Tier 1 状态
- 具有明确“通过”/“失败”/“跳过”的第 2 层状态以及“跳过”的原因
- 对于每个错误：工作表、单元格、错误类型和处理（已修复或已标记）
- 最终交付状态

---

## 常见场景

### 场景1：创建新文件后立即验证

当“create.md”工作流程生成新的 xlsx 时，请在任何交付响应之前运行验证。```bash
# Step 1: Static check on the freshly written file
python3 SKILL_DIR/scripts/formula_check.py /path/to/output.xlsx

# Step 2: Dynamic check (if LibreOffice available)
python3 SKILL_DIR/scripts/libreoffice_recalc.py /path/to/output.xlsx /tmp/recalculated.xlsx
python3 SKILL_DIR/scripts/formula_check.py /tmp/recalculated.xlsx
```新创建的文件上的预期行为：第 1 层将发现零个“error_value”错误（因为“<v>”元素为空，没有错误值）。如果工作表名称拼写错误，它将找到任何损坏的跨工作表引用。第 2 层将填充“<v>”并显示运行时错误，例如“#DIV/0!”。

如果第 2 层显示错误，请在源 XML（而不是重新计算的副本）中修复它们，重新打包并重新运行这两个层。

### 场景 2：编辑现有文件后验证

当“edit.md”工作流程修改现有 xlsx 时，如果编辑是外科手术，则仅验证受影响的工作表。如果编辑涉及共享公式或跨工作表引用，请验证所有工作表。```bash
# Targeted static check — look at specific sheet
# (formula_check.py checks all sheets; examine only the relevant section of output)
python3 SKILL_DIR/scripts/formula_check.py /path/to/edited.xlsx --json \
  | python3 -c "
import json, sys
r = json.load(sys.stdin)
for e in r['errors']:
    if e.get('sheet') in ['Summary', 'Q1']:
        print(e)
"
```即使第 1 层通过，在修改公式的编辑后也始终运行第 2 层。对数据范围的编辑可能会导致先前有效的公式产生运行时错误。

### 场景 3：用户提供的文件疑似存在公式错误

当用户提交文件并报告错误值或可见错误时：```bash
# Step 1: Static scan — find all error cells
python3 SKILL_DIR/scripts/formula_check.py /path/to/user_file.xlsx --json > /tmp/validation_results.json

# Step 2: Unpack for manual inspection
python3 SKILL_DIR/scripts/xlsx_unpack.py /path/to/user_file.xlsx /tmp/xlsx_inspect/

# Step 3: Dynamic recalculation
python3 SKILL_DIR/scripts/libreoffice_recalc.py /path/to/user_file.xlsx /tmp/user_file_recalc.xlsx

# Step 4: Re-validate recalculated file
python3 SKILL_DIR/scripts/formula_check.py /tmp/user_file_recalc.xlsx --json > /tmp/validation_after_recalc.json

# Step 5: Compare before and after
python3 - <<'EOF'
import json
before = json.load(open("/tmp/validation_results.json"))
after  = json.load(open("/tmp/validation_after_recalc.json"))
print(f"Before recalc: {before['error_count']} errors")
print(f"After  recalc: {after['error_count']} errors")
EOF
```如果错误仅在重新计算后出现（不在原始静态扫描中），则公式在语法上是正确的，但在运行时会产生错误的结果。这些是运行时错误，需要公式级修复，而不是 XML 结构修复。

如果两次扫描中都出现错误，则在重新计算之前它们已缓存在“<v>”中 - 该文件之前已由 Excel/LibreOffice 打开，并且错误仍然存​​在。

---

## 关键陷阱

**陷阱 1：openpyxl `data_only=True` 破坏了公式。**
使用“data_only=True”打开工作簿会读取缓存的值而不是公式。如果您随后保存工作簿，所有“<f>”元素将被永久删除并替换为其最后缓存的值。切勿将此模式用于验证工作流程。

**陷阱 2：空 `<v>` 与传递公式不同。**
新生成的文件的所有公式单元格都包含空的“<v>”元素。 Formula_check.py 不会将这些报告为错误 - 它们还不是错误。如果计算值是错误类型，则仅在重新计算后它们才会变为错误。这就是为什么第 2 层是强制性的。

**陷阱 3：共享公式错误影响整个范围。**
如果共享公式的主单元格具有损坏的引用，则共享区域 (`ref="D2:D100"`) 中的每个单元格都会继承该损坏的引用。逻辑错误的计数可能比 Formula_check.py 输出中不同错误条目的计数大得多。修复损坏的共享公式时，修复主单元格的 `<ft="shared" ref="...">` 元素；消费者（`<ft t =“shared”si =“N”/>`）自动继承更正后的公式。

**陷阱 4：工作表名称区分大小写。**
`=q1!B5` 和 `=Q1!B5` 是不同的引用。 Excel 内部对它们的处理方式相同，但 Formula_check.py 的字符串比较区分大小写。如果公式使用与工作簿中的大写工作表匹配的小写工作表名称，它将被标记为损坏的引用。修复方法是匹配“workbook.xml”中的确切大小写。

**陷阱 5：`--convert-to xlsx` 不能保证公式保存。**
LibreOffice 的转换有时会改变某些公式类型（数组公式、动态数组函数，如“SORT”、“UNIQUE”）。在第 2 层之后，如果重新计算的文件显示与错误修复无关的公式更改，请不要直接交付重新计算的文件 - 而是使用具有目标 XML 修复的原始文件。