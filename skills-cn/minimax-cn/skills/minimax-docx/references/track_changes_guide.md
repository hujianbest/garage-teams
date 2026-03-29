# 跟踪更改指南

## 概述

OpenXML 中的跟踪更改使用修订标记元素来记录插入、删除和格式更改。每个修订版都有唯一的 ID、作者和时间戳。

---

## 插入：`<w:ins>`

包裹跟踪期间插入的运行：```xml
<w:ins w:id="1" w:author="John Smith" w:date="2026-03-21T10:30:00Z">
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
      <w:sz w:val="22" />
    </w:rPr>
    <w:t>This text was inserted.</w:t>
  </w:r>
</w:ins>
```- `w:id` — 唯一修订 ID（整数，在整个文档中必须是唯一的）
- `w:author` — 标识作者的自由文本字符串
- `w:date` — ISO 8601 格式，带时区：`YYYY-MM-DDTHH:MM:SSZ`
- 里面的内容是正常运行（`w:r`），具有可选格式

---

## 删除：`<w:del>`

包装跟踪期间删除的运行：```xml
<w:del w:id="2" w:author="John Smith" w:date="2026-03-21T10:31:00Z">
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
      <w:sz w:val="22" />
    </w:rPr>
    <w:delText xml:space="preserve">This text was deleted.</w:delText>
  </w:r>
</w:del>
```**关键**：在 `<w:del>` 内，文本必须使用 `<w:delText>`，而不是 `<w:t>`。在删除中使用 `<w:t>` 是无效的，并且会导致损坏或意外行为。 Word 可能会默默修复它，但其他消费者会失败。

---

## 格式更改：`<w:rPrChange>`

记录运行格式已更改。放置在 `w:rPr` 内部，它存储**以前的**格式：```xml
<w:r>
  <w:rPr>
    <w:b />  <!-- Current: bold -->
    <w:rPrChange w:id="3" w:author="Jane Doe" w:date="2026-03-21T11:00:00Z">
      <w:rPr>
        <!-- Previous: not bold (empty rPr means no formatting) -->
      </w:rPr>
    </w:rPrChange>
  </w:rPr>
  <w:t>This text was made bold.</w:t>
</w:r>
```外部“w:rPr”保存**新**（当前）格式。 `w:rPrChange` 子项保留**旧**（以前的）格式。

---

## 段落属性更改：`<w:pPrChange>`

记录段落级格式更改（对齐方式、间距、样式）：```xml
<w:pPr>
  <w:jc w:val="center" />  <!-- Current: centered -->
  <w:pPrChange w:id="4" w:author="Jane Doe" w:date="2026-03-21T11:05:00Z">
    <w:pPr>
      <w:jc w:val="left" />  <!-- Previous: left-aligned -->
    </w:pPr>
  </w:pPrChange>
</w:pPr>
```---

## 修订 ID 管理

- 每个修订元素（`w:ins`、`w:del`、`w:rPrChange`、`w:pPrChange`、`w:tblPrChange` 等）都需要一个 `w:id` 属性
- ID 必须是整个文档中的**唯一整数**
- ID 应该**单调递增**（不是严格要求，但 Word 期望）
- 添加修订时，扫描当前最大“w:id”并从那里递增```
Existing max ID: 47
New insertion: w:id="48"
New deletion: w:id="49"
```---

## 作者和日期

- **作者**：自由文本。使用一致的字符串（例如，“MiniMaxAI”用于所有自动编辑）
- **日期**：带 UTC 时区标记的 ISO 8601：`2026-03-21T10:30:00Z`
  - 必须包含“T”分隔符和“Z”后缀（或“+HH:MM”偏移量）
  - 允许省略日期，但不建议

---

## 操作

### 提议插入

在目标位置添加新内容的“<w:ins>”包装：```xml
<w:p>
  <w:r><w:t>Existing text. </w:t></w:r>
  <w:ins w:id="5" w:author="MiniMaxAI" w:date="2026-03-21T12:00:00Z">
    <w:r><w:t>Proposed new text. </w:t></w:r>
  </w:ins>
  <w:r><w:t>More existing text.</w:t></w:r>
</w:p>
```### 提议删除

将现有内容包装在 `<w:del>` 中并将 `<w:t>` 更改为 `<w:delText>`：```xml
<w:p>
  <w:r><w:t>Keep this. </w:t></w:r>
  <w:del w:id="6" w:author="MiniMaxAI" w:date="2026-03-21T12:01:00Z">
    <w:r>
      <w:rPr><w:b /></w:rPr>
      <w:delText>Remove this.</w:delText>
    </w:r>
  </w:del>
  <w:r><w:t> Keep this too.</w:t></w:r>
</w:p>
```### 接受跟踪变更

- **接受插入**：删除 `<w:ins>` 包装器，保留内部运行作为正常内容
- **接受删除**：删除整个`<w:del>`元素及其内容

### 拒绝跟踪变更

- **拒绝插入**：删除整个 `<w:ins>` 元素及其内容
- **拒绝删除**：删除`<w:del>`包装，将`<w:delText>`更改回`<w:t>`

---

## 跨段落操作

### 删除段落分隔符（合并段落）

当跟踪删除跨越段落边界时，请在合并的段落上使用“<w:pPrChange>”：```xml
<w:p>
  <w:pPr>
    <w:pPrChange w:id="7" w:author="MiniMaxAI" w:date="2026-03-21T12:05:00Z">
      <w:pPr>
        <w:pStyle w:val="Normal" />
      </w:pPr>
    </w:pPrChange>
  </w:pPr>
  <w:r><w:t>First paragraph text. </w:t></w:r>
  <w:del w:id="8" w:author="MiniMaxAI" w:date="2026-03-21T12:05:00Z">
    <w:r><w:delText> </w:delText></w:r>
  </w:del>
  <w:r><w:t>Second paragraph text (now merged).</w:t></w:r>
</w:p>
```### 插入新段落

整个新段落包含在 `<w:ins>` 中：```xml
<w:p>
  <w:pPr>
    <w:rPr>
      <w:ins w:id="9" w:author="MiniMaxAI" w:date="2026-03-21T12:10:00Z" />
    </w:rPr>
  </w:pPr>
  <w:ins w:id="10" w:author="MiniMaxAI" w:date="2026-03-21T12:10:00Z">
    <w:r><w:t>Entirely new paragraph.</w:t></w:r>
  </w:ins>
</w:p>
```段落标记本身被标记为通过 `w:pPr > w:rPr` 内的 `w:ins` 插入。