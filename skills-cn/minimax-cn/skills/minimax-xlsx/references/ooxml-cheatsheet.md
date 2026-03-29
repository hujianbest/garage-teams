# OOXML SpreadsheetML 备忘单

xlsx 文件的 XML 操作的快速参考。

---

## 包结构```
my_file.xlsx  (ZIP archive)
├── [Content_Types].xml          ← declares MIME types for all files
├── _rels/
│   └── .rels                    ← root relationship: points to xl/workbook.xml
└── xl/
    ├── workbook.xml             ← sheet list, calc settings
    ├── styles.xml               ← ALL style definitions
    ├── sharedStrings.xml        ← ALL text strings (referenced by index)
    ├── _rels/
    │   └── workbook.xml.rels    ← maps r:id → worksheet/styles/sharedStrings files
    ├── worksheets/
    │   ├── sheet1.xml           ← Sheet 1 data
    │   ├── sheet2.xml           ← Sheet 2 data
    │   └── ...
    ├── charts/                  ← chart XML (if any)
    ├── pivotTables/             ← pivot table XML (if any)
    └── theme/
        └── theme1.xml           ← color/font theme
```---

## 单元格引用格式```
A1  → column A (1), row 1
B5  → column B (2), row 5
AA1 → column 27, row 1
```列字母↔数字转换：```python
def col_letter(n):  # 1-based → letter
    r = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        r = chr(65 + rem) + r
    return r

def col_number(s):  # letter → 1-based
    n = 0
    for c in s.upper():
        n = n * 26 + (ord(c) - 64)
    return n
```---

## 单元格 XML 参考

### 数据类型

|类型 | `t` 属性 | XML 示例 |价值|
|------|---------|-------------|--------|
|数量 |省略| `<c r="B2"><v>1000</v></c>` | 1000 | 1000
|字符串（共享）| `s` | `<c r="A1" t="s"><v>0</v></c>` |共享字符串[0] |
|字符串（内联）| `inlineStr` | `<c r="A1" t="inlineStr"><is><t>嗨</t></is></c>` | “嗨”|
|布尔 | `b` | `<c r="D1" t="b"><v>1</v></c>` |正确 |
|错误| `e` | `<c r="E1" t="e"><v>#REF!</v></c>` | #参考！ |
|公式|省略| `<c r="B4"><f>SUM(B2:B3)</f><v></v></c>` |计算|

### 公式类型```xml
<!-- Basic formula (no leading = in XML!) -->
<c r="B4"><f>SUM(B2:B3)</f><v></v></c>

<!-- Cross-sheet -->
<c r="C1"><f>Assumptions!B5</f><v></v></c>
<c r="C1"><f>'Sheet With Spaces'!B5</f><v></v></c>

<!-- Shared formula: D2:D100 all use B*C with relative row offset -->
<c r="D2"><f t="shared" ref="D2:D100" si="0">B2*C2</f><v></v></c>
<c r="D3"><f t="shared" si="0"/><v></v></c>

<!-- Array formula -->
<c r="E1"><f t="array" ref="E1:E5">SORT(A1:A5)</f><v></v></c>
```---

## styles.xml 参考

### 间接引用链```
Cell s="3"
  ↓
cellXfs[3] → fontId="2", fillId="0", borderId="0", numFmtId="165"
  ↓              ↓             ↓            ↓              ↓
fonts[2]      fills[0]    borders[0]    numFmts: id=165
blue color    no fill      no border    "0.0%"
```### 添加新样式（逐步）

1. 在 `<numFmts>` 中：添加 `<numFmt numFmtId="168" formatCode="0.00%"/>`，更新 `count`
2. 在`<fonts>`中：添加字体条目，记下其索引
3. 在 `<cellXfs>` 中：追加 `<xf numFmtId="168" fontId="N" .../>`，更新 `count`
4. 新样式索引 = 旧的 `cellXfs count` 值（递增之前）
5.应用于单元格：`<c r="B5" s="NEW_INDEX">...</c>`

### 颜色格式

`AARRGGBB` — Alpha（始终为“00”表示不透明）+ 红 + 绿 + 蓝```
000000FF → Blue
00000000 → Black
00008000 → Green (dark)
00FF0000 → Red
00FFFF00 → Yellow (for fills)
00FFFFFF → White
```### 内置 numFmtIds （无需声明）

|身份证 |格式|显示|
|----|--------|---------|
| 0 |一般|按原样 |
| 1 | 0 | 2024（使用多年！）|
| 2 | 0.00 | 0.00 1000.00 |
| 3 | #,##0 | 1,000 |
| 4 | #,##0.00 | 1,000.00 | 1,000.00
| 9 | 0% | 15% |
| 10 | 10 0.00% | 15.25% |
| 14 | 14月/日/年 | 2026 年 3 月 21 日 |

---

##sharedStrings.xml 参考```xml
<sst count="3" uniqueCount="3">
  <si><t>Revenue</t></si>      <!-- index 0 -->
  <si><t>Cost</t></si>         <!-- index 1 -->
  <si><t>Margin</t></si>       <!-- index 2 -->
</sst>
```带有前导/尾随空格的文本：```xml
<si><t xml:space="preserve">  indented  </t></si>
```特殊字符：```xml
<si><t>R&amp;D Expenses</t></si>   <!-- & must be &amp; -->
```---

## workbook.xml / .rels 同步

workbook.xml 中的每个“<sheet>”都需要 workbook.xml.rels 中匹配的“<Relationship>”：```xml
<!-- workbook.xml -->
<!-- NOTE: rId numbering depends on what rIds are already in workbook.xml.rels.
     The minimal template reserves rId1=sheet1, rId2=styles, rId3=sharedStrings.
     When ADDING sheets to the template, start from rId4 to avoid conflicts.
     The rId3 here is just a generic illustration — use the next available rId. -->
<sheet name="Summary" sheetId="3" r:id="rId3"/>

<!-- workbook.xml.rels -->
<Relationship Id="rId3"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
  Target="worksheets/sheet3.xml"/>
```以及“[Content_Types].xml”中匹配的“<Override>”：```xml
<Override PartName="/xl/worksheets/sheet3.xml"
  ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
```---

## 列/行尺寸```xml
<!-- Before <sheetData> -->
<cols>
  <col min="1" max="1" width="28" customWidth="1"/>   <!-- A: 28 chars -->
  <col min="2" max="6" width="14" customWidth="1"/>   <!-- B-F: 14 chars -->
</cols>

<!-- Row height on individual rows -->
<row r="1" ht="20" customHeight="1">
  ...
</row>
```---

## 冻结窗格

在 `<sheetView>` 内：```xml
<!-- Freeze row 1 (header row stays visible) -->
<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>

<!-- Freeze column A -->
<pane xSplit="1" topLeftCell="B1" activePane="topRight" state="frozen"/>

<!-- Freeze both row 1 and column A -->
<pane xSplit="1" ySplit="1" topLeftCell="B2" activePane="bottomRight" state="frozen"/>
```---

## 7 个 Excel 错误类型（交付时必须不存在所有错误类型）

|错误|意义|在 XML 中检测 |
|--------|---------|----------------|
| `#REF！` |无效的单元格引用 | `<c t="e"><v>#REF!</v></c>` |
| `#DIV/0！` |除以零 | `<c t="e"><v>#DIV/0!</v></c>` |
| `#VALUE！` |错误的数据类型 | `<c t="e"><v>#VALUE！</v></c>` |
| `#NAME？` |未知功能/名称 | `<c t="e"><v>#NAME?</v></c>` |
| `#NULL！` |空旷的路口| `<c t="e"><v>#NULL!</v></c>` |
| `#NUM！` |数量超出范围 | `<c t="e"><v>#NUM!</v></c>` |
| `#N/A` |未找到值 | `<c t="e"><v>#N/A</v></c>` |