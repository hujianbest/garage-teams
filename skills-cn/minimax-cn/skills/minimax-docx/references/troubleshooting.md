# 故障排除指南 — 症状驱动

## 如何使用本指南

按您观察到的**症状**进行搜索，而不是技术概念。每个条目如下：
- **症状** — 您看到的内容或用户报告的内容
- **诊断** — 如何确认根本原因
- **修复** — 确切的步骤、命令或代码
- **预防** — 下次如何避免

**快速搜索关键字：**标题错误、正文、修复、损坏、字体、表格丢失、图像丢失、目录损坏、更新表格、分页符、分节符、超链接、编号列表、项目符号、页边距、页面大小、中国豆腐、封面页、轨道更改、修订标记

---

## 1.“所有标题看起来都像正文”（未应用标题样式）

**症状：** 应用模板后，标题没有格式 - 它们看起来像普通段落。字体大小、粗体、间距都是错误的。

**诊断：** “document.xml”中的“pStyle”值与“styles.xml”中的“styleId”值不匹配。

常见的不匹配：
- 源使用“Heading1”，但模板将样式定义为“1”（中文模板通常使用数字 styleId）
- 源使用“heading1”（小写），但模板具有“Heading1”（区分大小写！）
- `pStyle` 引用了输出的 `styles.xml` 中根本不存在的样式

检查：```bash
# List all pStyle values used in the document
$CLI analyze --input output.docx | grep -i "pStyle"

# List all styleIds defined in styles.xml
$CLI analyze --input template.docx --part styles | grep "styleId"
```**修复：** 在应用模板之前构建 styleId 映射表。更新文档内容中的每个“pStyle”值。```csharp
// Build mapping: source styleId → template styleId
var mapping = new Dictionary<string, string>();
// Compare by style name (w:name), not by styleId
foreach (var srcStyle in sourceStyles)
{
    var templateStyle = templateStyles.FirstOrDefault(
        s => s.StyleName?.Val?.Value == srcStyle.StyleName?.Val?.Value);
    if (templateStyle != null)
        mapping[srcStyle.StyleId!] = templateStyle.StyleId!;
}

// Apply mapping to all paragraphs
foreach (var para in body.Descendants<Paragraph>())
{
    var pStyle = para.ParagraphProperties?.ParagraphStyleId;
    if (pStyle != null && mapping.TryGetValue(pStyle.Val!, out var newId))
        pStyle.Val = newId;
}
```**预防：** 在应用模板之前，始终从源和模板中提取并比较 styleId。永远不要假设文档中的 styleId 是相同的。

---

## 2.“文档打开时出现修复警告”（XML 损坏）

**症状：** Word 在打开时显示“我们发现某些内容有问题”或“Word 发现无法读取的内容”。

**诊断：** 元素排序错误。 OpenXML 对子元素顺序非常严格。

常见违规行为：
- `pPr` 必须在 `w:p` 中运行之前出现
- 在“w:tbl”中，“tblPr”必须位于“tblGrid”之前
- `rPr` 必须位于 `w:r` 中的 `t`/`br`/`tab` 之前
- 在“w:tr”中，“trPr”必须位于“tc”之前
- `tcPr` 必须位于 `w:tc` 中的内容之前```bash
# Validate to find ordering issues
$CLI validate --input doc.docx --xsd assets/xsd/wml-subset.xsd

# Auto-fix element ordering
$CLI fix-order --input doc.docx

# Re-validate
$CLI validate --input doc.docx --xsd assets/xsd/wml-subset.xsd
```**使固定：**```bash
$CLI fix-order --input doc.docx
```如果自动修复无法解决问题，请手动解压并检查：```bash
$CLI unpack --input doc.docx --output unpacked/
# Check word/document.xml for ordering issues
# Fix, then repack:
$CLI pack --input unpacked/ --output fixed.docx
```**预防：** 在编写任何 XML 操作代码之前，请阅读 `references/openxml_element_order.md`。始终先附加属性元素，然后附加内容元素。

---

## 3.“所有文本的字体都是错误的”（字体污染）

**症状：** 模板指定宋体/Times New Roman，但文档显示 Google Sans、Arial、Calibri 或源文档使用的任何字体。

**诊断：** 源文档的 `rPr` 包含覆盖模板样式的内联 `rFonts` 声明。在 OpenXML 中，直接格式化始终胜过基于样式的格式化。```bash
# Check for font contamination
$CLI analyze --input output.docx | grep -i "font"
# Look for rFonts in the content — if present, they're overriding styles
```**修复：** 复制内容时从 `rPr` 中删除 `rFonts`，但保留 CJK 文本的 `w:eastAsia`：```csharp
foreach (var rPr in body.Descendants<RunProperties>())
{
    var rFonts = rPr.GetFirstChild<RunFonts>();
    if (rFonts != null)
    {
        // Preserve EastAsia font for CJK — removing it causes tofu (□□□)
        var eastAsia = rFonts.EastAsia?.Value;
        rFonts.Remove();

        // Re-add only eastAsia if it was set and text contains CJK
        if (!string.IsNullOrEmpty(eastAsia))
        {
            rPr.Append(new RunFonts { EastAsia = eastAsia });
        }
    }
}
```还要删除这些常见的直接格式覆盖：
- `w:sz` / `w:szCs` （字体大小）
- `w:color`（文本颜色）
- `w:b` / `w:i` 当它们与风格相矛盾时

**预防：** 在文档之间复制内容时，始终清理直接格式。仅保留 `pStyle`/`rStyle` 引用和 `w:t` 文本。

---

## 4.“表丢失”（复制期间丢失表）

**症状：** 源有 5 个表，但输出只有 2 个（或 0 个）。

**诊断：** 代码在顶层使用了 `body.findall('w:p')` 或 `body.Descendants<Paragraph>()`，而不是迭代所有子级。这会跳过“w:tbl”元素。```bash
# Verify table count
$CLI analyze --input source.docx | grep -i "table"
$CLI analyze --input output.docx | grep -i "table"
```**修复：** 使用 `list(body)` 或 `body.ChildElements` 获取所有顶级子元素，包括表：```csharp
// WRONG — skips tables, section properties, and other non-paragraph elements
var paragraphs = body.Elements<Paragraph>();

// CORRECT — gets everything: paragraphs, tables, SDT blocks, etc.
var allElements = body.ChildElements.ToList();
```在 Python 中使用 lxml：```python
# WRONG
elements = body.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')

# CORRECT
elements = list(body)  # all direct children
```**预防：** 始终使用 `list(body)` 或 `body.ChildElements` 进行迭代，复制内容时切勿单独按单个元素类型进行过滤。

---

## 5.“图像丢失或显示损坏的图标”

**症状：** 出现图像占位符，但图像不渲染。或者图像完全不存在。

**诊断：** `w:drawing` 中的 `r:embed` rId 与 `document.xml.rels` 中的任何关系都不匹配，或者媒体文件未复制到输出 ZIP。```bash
# Check relationships
$CLI analyze --input output.docx --part rels | grep -i "image"

# Check if media files exist
$CLI unpack --input output.docx --output unpacked/
ls unpacked/word/media/
```**修复：**
1.检查source rels中的图像文件路径
2. 将媒体文件从源复制到输出
3. 在输出rels中添加/更新关系
4. 更新绘图元素中的“r:embed”值```csharp
// When copying content with images between documents:
foreach (var drawing in body.Descendants<Drawing>())
{
    var blip = drawing.Descendants<DocumentFormat.OpenXml.Drawing.Blip>().FirstOrDefault();
    if (blip?.Embed?.Value != null)
    {
        var sourceRel = sourcePart.GetReferenceRelationship(blip.Embed.Value);
        // Copy the image part to the target document
        var imagePart = targetPart.AddImagePart(ImagePartType.Png);
        using var stream = sourcePart.GetPartById(blip.Embed.Value).GetStream();
        imagePart.FeedData(stream);
        // Update the rId reference
        blip.Embed = targetPart.GetIdOfPart(imagePart);
    }
}
```**预防：** 在文档之间移动内容时，始终执行 rId 重新映射 + 媒体文件复制。永远不要假设 rId 可以跨文档移植。

---

## 6.“目录显示陈旧/错误的条目”或“更新表不起作用”

**症状：** 目录显示模板的示例条目（例如，“第 1 章绪论...1”）而不是实际标题。或者在 Word 中单击“更新表格”不会执行任何操作。

**诊断：**
- **过时条目（正常）：** TOC 条目是缓存在字段内的静态文本。在用户在 Word 中明确更新之前，它们不会自动更新。
- **更新表失败：** SDT 包装器或字段代码结构已损坏。真实模板中的TOC是混合结构：SDT块+字段代码+静态条目。```bash
# Check if TOC SDT exists
$CLI analyze --input output.docx | grep -i "sdt\|toc"
```**修复：**
- **如果条目只是陈旧：** 这是预期的行为。用户必须右键单击目录，然后右键单击 Word 中的“更新字段”。或者启用自动更新：```csharp
  // See FieldAndTocSamples.EnableUpdateFieldsOnOpen()
  FieldAndTocSamples.EnableUpdateFieldsOnOpen(settingsPart);
  ```- **如果 SDT 损坏：** 保持模板中的整个 SDT 块完好无损。不要修改它。
- **如果缺少字段代码：** 确保目录包含：`fldChar begin` + `instrText` + `fldChar alone` + 静态条目 + `fldChar end`。有关完整模式，请参阅“FieldAndTocSamples.CreateMixedTocStructure()”。
- **如果您从头开始重建 TOC（常见错误）：** 您可能破坏了 SDT 包装器。请改用模板的原始 SDT 块。请参阅“Samples/FieldAndTocSamples.cs”方法“CreateMixedTocStructure”，了解现实世界 TOC 的结构。

**预防：** 进行碱基替换 (C-2) 时，保持模板的 TOC 区域完全不受影响。请勿剥离、重建或修改 SDT 块。当用户在 Word 中打开时，目录将自动更新。

---

## 7.“章节不从新页面开始”（缺少分节符）

**症状：** 内容连续流动，章节之间没有分页符。第 2 章在同一页上的第 1 章最后一段之后开始。

**诊断：** 章节之间没有 `sectPr` 元素或分页段落。

**修复：** 在每个章节标题之前的“pPr”中插入带有“sectPr”的段落，或插入分页符：```csharp
// Option 1: Section break (preserves per-section settings like headers/margins)
var breakPara = new Paragraph(
    new ParagraphProperties(
        new SectionProperties(
            new SectionType { Val = SectionMarkValues.NextPage })));

// Option 2: Simple page break (lighter weight)
var breakPara = new Paragraph(
    new Run(new Break { Type = BreakValues.Page }));

// Insert before each Heading1
body.InsertBefore(breakPara, heading1Paragraph);
```**预防措施：** 复制内容时，根据需要在 Heading1 段落前插入分页符/分节符。复制之前检查源文档的部分结构。

---

## 8.“超链接不起作用”（损坏的链接）

**症状：** 单击输出文档中的超链接不会执行任何操作，或者导航到错误的 URL。

**诊断：** `w:hyperlink r:id` 指向 `document.xml.rels` 中不存在的关系。```bash
# Check hyperlink relationships
$CLI analyze --input output.docx --part rels | grep -i "hyperlink"
```**修复：** 将源文档的超链接关系合并到输出的 rels 文件中。更新 rId 参考。```csharp
foreach (var hyperlink in body.Descendants<Hyperlink>())
{
    if (hyperlink.Id?.Value != null)
    {
        var sourceRel = sourcePart.HyperlinkRelationships
            .FirstOrDefault(r => r.Id == hyperlink.Id.Value);
        if (sourceRel != null)
        {
            targetPart.AddHyperlinkRelationship(sourceRel.Uri, sourceRel.IsExternal);
            var newRel = targetPart.HyperlinkRelationships.Last();
            hyperlink.Id = newRel.Id;
        }
    }
}
```**预防：** 合并文档时始终合并所有关系类型（图像、超链接、页眉、页脚）。切勿假设源 rId 在目标中有效。

---

## 9.“编号列表显示错误的数字”或“项目符号消失”

**症状：** 编号为 1、2、3 的列表现在显示 1、1、1 或根本没有编号/项目符号。

**诊断：** `pPr` 中的 `numId` 引用了 `numbering.xml` 中不存在的编号定义，或者 `abstractNumId` 映射已损坏。```bash
# Check numbering definitions
$CLI analyze --input output.docx --part numbering
```**修复：** 将源 numIds 映射到模板 numIds，或合并编号定义：```csharp
// 1. Copy abstractNum definitions from source to target numbering.xml
// 2. Create new num entries pointing to the copied abstractNum
// 3. Update all numId references in document content

var sourceNumbering = sourceNumberingPart.Numbering;
var targetNumbering = targetNumberingPart.Numbering;

// Get max existing IDs to avoid collisions
int maxAbstractNumId = targetNumbering.Elements<AbstractNum>()
    .Max(a => a.AbstractNumberId?.Value ?? 0) + 1;
int maxNumId = targetNumbering.Elements<NumberingInstance>()
    .Max(n => n.NumberID?.Value ?? 0) + 1;
```**预防：** 在模板应用程序工作流程中包含“numbering.xml”协调。请参阅“Samples/ListAndNumberingSamples.cs”以了解正确的编号设置。

---

## 10.“页边距/尺寸错误”

**症状：** 输出的边距、页面大小或方向与模板不同。

**诊断：** 源文档的 `sectPr` 覆盖了模板的 `sectPr`。最后的“sectPr”（“body”的子级）控制最后一个部分的布局。```bash
# Compare section properties
$CLI analyze --input template.docx | grep -i "sectPr\|margin\|pgSz"
$CLI analyze --input output.docx | grep -i "sectPr\|margin\|pgSz"
```**修复：** 使用模板的最终 `sectPr`。对于中间 `sectPr` 元素（多节文档），请小心合并。```csharp
// Replace output's final sectPr with template's
var templateSectPr = templateBody.Elements<SectionProperties>().LastOrDefault();
var outputSectPr = outputBody.Elements<SectionProperties>().LastOrDefault();

if (templateSectPr != null)
{
    var cloned = templateSectPr.CloneNode(true) as SectionProperties;
    if (outputSectPr != null)
        outputBody.ReplaceChild(cloned!, outputSectPr);
    else
        outputBody.Append(cloned!);
}
```**预防：** 始终使用模板的 `sectPr` 作为页面布局的权限。在复制内容之前删除源文档的 `sectPr`。

---

## 11.“中文文本呈现为盒子/豆腐”

**症状：** 汉字显示为方框 (□□□) 或缺少字形。

**诊断：** `rFonts w:eastAsia` 设置为系统上不存在或完全丢失的字体。如果没有东亚字体声明，渲染引擎可能会回退到没有 CJK 覆盖的字体。

**修复：** 确保所有 CJK 文本都将 `w:eastAsia` 设置为可用字体：```csharp
foreach (var run in body.Descendants<Run>())
{
    var text = run.InnerText;
    if (ContainsCjk(text))
    {
        var rPr = run.RunProperties ?? new RunProperties();
        var rFonts = rPr.GetFirstChild<RunFonts>();
        if (rFonts == null)
        {
            rFonts = new RunFonts();
            rPr.Append(rFonts);
        }
        // Set to a universally available CJK font
        rFonts.EastAsia = "SimSun"; // 宋体 — safest default
        if (run.RunProperties == null) run.PrependChild(rPr);
    }
}

static bool ContainsCjk(string text)
{
    return text.Any(c => c >= 0x4E00 && c <= 0x9FFF);
}
```常见的安全中日韩字体：宋体（SimSun）、黑体（SimHei）、仿宋（FangSong）、楷体（KaiTi）。

**预防：** 清理 `rPr` 格式时，始终保留 `w:eastAsia` 字体声明。另请参阅“references/cjk_typography.md”。

---

## 12.“模板的封面页/声明页丢失”

**症状：** 输出文档直接从正文内容开始 — 没有封面、没有声明、没有摘要、没有目录。模板的结构前面的内容被丢弃。

**诊断：** 当需要碱基替换（C-2）时使用覆盖（C-1）策略。覆盖将样式应用于源文档，但丢弃模板的结构内容（封面、声明、摘要、目录）。```bash
# Check template structure
$CLI analyze --input template.docx
# If template has >50 paragraphs with cover/TOC/declaration, C-2 is needed
```**修复：** 使用 Base-Replace (C-2) 策略 - 模板是基础，仅将示例正文内容区域替换为用户的内容：

1. 确定模板的“主体区域”（TOC 和最终 sectPr 之间的所有内容）
2. 删除模板的示例正文内容
3. 将用户内容插入正文区域
4. 保留模板中的其他所有内容（封面、声明、摘要、目录、sectPr）```bash
$CLI apply-template --input source.docx --template template.docx --output out.docx --strategy base-replace
```**预防：** 首先分析模板结构。如果模板具有结构内容（封面、目录、声明部分），请始终使用 C-2（基本替换）。阅读 `references/scenario_c_apply_template.md` 了解详细的决策标准。

---

## 13.“跟踪更改标记意外出现”

**症状：** 输出显示源文档中没有的红色/绿色修订标记（插入、删除）。

**诊断：** 模板启用了跟踪更改，或者内容作为修订版而不是普通文本插入。```bash
# Check for revision marks
$CLI analyze --input output.docx | grep -i "revision\|ins\|del\|track"
```**修复：** 通过展平 `w:ins` 和 `w:del` 元素接受所有修订：```csharp
// Accept insertions: unwrap w:ins, keep content
foreach (var ins in body.Descendants<InsertedRun>().ToList())
{
    var parent = ins.Parent!;
    foreach (var child in ins.ChildElements.ToList())
    {
        parent.InsertBefore(child.CloneNode(true), ins);
    }
    ins.Remove();
}

// Accept deletions: remove w:del and its content entirely
foreach (var del in body.Descendants<DeletedRun>().ToList())
{
    del.Remove();
}
```或者在设置中禁用跟踪：```csharp
var settings = settingsPart.Settings;
var trackChanges = settings.GetFirstChild<TrackChanges>();
trackChanges?.Remove();
```**预防：** 在开始之前检查模板的“settings.xml”中的“trackChanges”。如果存在，请首先接受模板中的所有修订。

---

## 恢复策略 — 当存在多个问题时

当文档存在多个问题时，请按以下优先顺序修复它们：```
1. [Content_Types].xml  — without this, nothing opens
2. _rels/.rels          — package relationships
3. word/_rels/document.xml.rels — part relationships (images, hyperlinks)
4. word/document.xml    — element ordering (fix-order)
5. word/styles.xml      — style definitions and styleId mapping
6. word/numbering.xml   — list/numbering definitions
7. Everything else      — headers, footers, comments, settings
```

```bash
# Full recovery pipeline
$CLI unpack --input broken.docx --output unpacked/
$CLI validate --input broken.docx --xsd assets/xsd/wml-subset.xsd  # find all errors
$CLI fix-order --input broken.docx                                   # fix element ordering
$CLI validate --input broken.docx --business                         # check business rules
scripts/docx_preview.sh broken.docx                                  # visual check
```
