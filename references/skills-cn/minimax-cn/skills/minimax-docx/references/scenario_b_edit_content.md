# 场景B：编辑/填充现有DOCX中的内容

## 核心原则

**“首先，不要造成伤害。”** 编辑现有文档时，尽量减少更改。仅触摸需要更改的内容。保留编辑中不直接涉及的所有格式、样式、关系和结构。

---

## 何时使用

- 替换占位符文本（`{{name}}`、`$DATE$`、`[PLACEHOLDER]`）
- 更新特定段落或表格单元格
- 填写表格字段
- 在已知位置添加或删除段落
- 插入审核工作流程的跟踪更改

不要在以下情况下使用：用户想要更改整个文档的外观/风格（→ 场景 C）或从头开始创建（→ 场景 A）。

---

## 工作流程```
1. Preview   → CLI: analyze <input.docx>
2. Analyze   → Understand structure: sections, styles, headings, tables
3. Identify  → Locate exact edit targets (paragraph index, table index, placeholder text)
4. Edit      → Apply surgical changes via CLI or direct XML
5. Validate  → CLI: validate <output.docx>
6. Diff      → Compare before/after to verify only intended changes were made
```---

## 何时使用 API 与直接 XML

### 在以下情况下使用 CLI 编辑命令：
- 替换占位符文本（例如，“{{fieldName}}”→实际值）
- 从 JSON 填充表数据
- 更新文档属性（标题、作者）
- 简单的文本插入或删除

### 在以下情况下使用直接 XML 操作：
- 文本跨越多个具有不同格式的运行（运行边界问题）
- 添加复杂的结构（嵌套表格、多图像布局）
- 操作跟踪更改标记
- 修改页眉/页脚内容
- 调整部分属性

---

## 占位符模式

CLI 本身支持 `{{fieldName}}` 占位符：```bash
# Replace all {{placeholders}} from a JSON map
dotnet run ... edit input.docx --fill-placeholders data.json --output filled.docx
```其中“data.json”：```json
{
  "companyName": "Acme Corp",
  "date": "March 21, 2026",
  "amount": "$15,000.00",
  "recipientName": "Jane Smith"
}
```其他占位符格式（`$FIELD$`、`[PLACEHOLDER]`）需要文本替换：```bash
dotnet run ... edit input.docx --replace "$DATE$" "March 21, 2026" --output updated.docx
```---

## 文本替换策略

### 简单替换

当整个搜索文本位于单个“w:r”（运行）中时：```xml
<!-- Before -->
<w:r>
  <w:rPr><w:b /></w:rPr>
  <w:t>{{companyName}}</w:t>
</w:r>

<!-- After — formatting preserved -->
<w:r>
  <w:rPr><w:b /></w:rPr>
  <w:t>Acme Corp</w:t>
</w:r>
```直接更换。运行的“w:rPr”未受影响。

### 复杂替换（拆分运行）

当搜索文本拆分为多个运行时（常见于 Word 应用拼写检查或格式化中间文本时）：```xml
<!-- "{{companyName}}" split into 3 runs -->
<w:r><w:rPr><w:b /></w:rPr><w:t>{{company</w:t></w:r>
<w:r><w:rPr><w:b /><w:i /></w:rPr><w:t>Na</w:t></w:r>
<w:r><w:rPr><w:b /></w:rPr><w:t>me}}</w:t></w:r>
```策略：
1. 连接各个运行中的文本以查找匹配项
2. 将替换文本放在**第一次**运行中（保留其`w:rPr`）
3. 从后续运行中删除文本（如果为空，则完全删除运行）```xml
<!-- After -->
<w:r><w:rPr><w:b /></w:rPr><w:t>Acme Corp</w:t></w:r>
```**规则**：始终保留比赛中第一次运行的格式。

---

## 表格编辑

### 按索引

表按文档顺序从 0 索引：```bash
dotnet run ... edit input.docx --table-index 0 --table-data data.json --output updated.docx
```### 通过标题匹配

通过表头行内容查找表：```bash
dotnet run ... edit input.docx --table-match "Name,Amount,Date" --table-data data.json
```### 表数据 JSON 格式```json
{
  "rows": [
    ["Alice Johnson", "$5,000", "2026-03-15"],
    ["Bob Smith", "$3,200", "2026-03-18"]
  ],
  "appendRows": true
}
```- `appendRows: true` — 在现有数据之后添加行
- `appendRows: false` (默认) — 替换所有数据行（保留标题行）

### 直接 XML 表编辑

要修改特定单元格，请通过行/列索引找到它：```xml
<!-- Row 2 (0-indexed), Column 1 -->
<w:tr>  <!-- tr[2] -->
  <w:tc>...</w:tc>
  <w:tc>  <!-- tc[1] — target cell -->
    <w:p>
      <w:r><w:t>Old Value</w:t></w:r>
    </w:p>
  </w:tc>
</w:tr>
```替换`w:t`内容。请勿修改“w:tcPr”（单元格属性）或“w:tblPr”（表属性）。

---

## 跟踪变更指南

### 何时添加修订标记
- 用户明确请求跟踪的更改
- 文档已启用跟踪（设置中的“w:trackChanges”）
- 协作评审工作流程

### 何时不添加修订标记
- 表格填写/占位符替换（这些是“完成”文档，而不是“修改”文档）
- 在用户想要干净结果的地方直接编辑
- 批量数据填充操作

### 添加跟踪更改

有关完整的 XML 示例，请参阅“references/track_changes_guide.md”。

快速参考 - 插入带跟踪的文本：```xml
<w:ins w:id="1" w:author="MiniMaxAI" w:date="2026-03-21T10:00:00Z">
  <w:r>
    <w:t>New text here</w:t>
  </w:r>
</w:ins>
```删除带有跟踪的文本：```xml
<w:del w:id="2" w:author="MiniMaxAI" w:date="2026-03-21T10:00:00Z">
  <w:r>
    <w:delText>Removed text</w:delText>  <!-- MUST use delText, not t -->
  </w:r>
</w:del>
```---

## 常见陷阱

### 1. 打破跑步界限

**问题**：通过天真地修改各个运行来替换跨运行的文本会破坏内联格式。

**修复**：连接运行文本，查找匹配边界，合并到第一个运行中，删除消耗的运行。

### 2.超链接内容

**问题**：在不保留超链接包装器的情况下替换“w:hyperlink”元素内的文本会删除链接。```xml
<w:hyperlink r:id="rId5">
  <w:r>
    <w:rPr><w:rStyle w:val="Hyperlink" /></w:rPr>
    <w:t>Click here</w:t>  <!-- Only replace this text -->
  </w:r>
</w:hyperlink>
```**修复**：仅修改超链接运行中的`w:t`。切勿删除或替换“w:hyperlink”元素本身。

### 3.跟踪变更背景

**问题**：在不了解修订上下文的情况下替换“w:ins”或“w:del”元素内的文本会创建无效标记。

**修复**：如果目标文本位于修订标记内，则：
- 在修订上下文中替换（保留 `w:ins`/`w:del` 包装器）
- 或者删除旧版本并创建新版本

### 4.风格保留

**问题**：添加新段落而不指定样式会导致它们继承“Normal”，这可能与周围的上下文不匹配。

**修复**：插入段落时，从相同类型的相邻段落复制`w:pStyle`。

### 5. 编号连续性

**问题**：插入新列表项会破坏编号顺序。

**修复**：确保新段落与相邻列表项具有相同的“w:numId”和“w:ilvl”。如果继续序列，请设置“w:numPr”以匹配。

### 6. XML 特殊字符

**问题**：用户内容包含 `&`、`<`、`>`、`"`、`'` — 这些必须在 XML 中转义。

**修复**：在插入 `w:t` 元素之前始终对用户提供的文本进行 XML 转义：
- `&` → `&amp;`
- `<`→`<`
- `>` → `>`
- `"` → `"`
- `'` → `'`

### 7. 空白保留

**问题**：`w:t` 中的前导/尾随空格被 XML 解析器删除。

**修复**：添加 `xml:space="preserve"` 属性：```xml
<w:t xml:space="preserve"> text with leading space</w:t>
```---

## 差异验证

编辑后，始终比较之前和之后的状态：```bash
# Structural diff — shows only changed elements
dotnet run ... diff original.docx modified.docx

# Text-only diff — shows content changes
dotnet run ... diff original.docx modified.docx --text-only
```验证：
- 仅更改了预期文本
- 没有修改样式
- 没有意外添加/删除关系
- 表结构完整（行/列数相同，除非故意更改）
- 图像和其他媒体不变