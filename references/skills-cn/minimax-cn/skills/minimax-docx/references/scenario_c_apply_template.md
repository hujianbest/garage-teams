# 场景 C：应用格式/模板

## 何时使用

在以下情况下使用场景 C：
- 用户有一个现有文档并想要应用不同的视觉样式
- 用户想要重新命名文档（新字体、颜色、标题样式）
- 用户提供模板 DOCX 并希望将其外观应用于内容文档
- 用户希望多个文档的格式保持一致

不要在以下情况下使用：用户想要编辑内容（→ 场景 B）或从头开始创建（→ 场景 A）。

---

## 工作流程```
1. Analyze source    → CLI: analyze source.docx      (list styles, fonts, structure)
2. Analyze template  → CLI: analyze template.docx     (list styles, fonts, structure)
3. Map styles        → Create mapping plan (source style → template style)
4. Apply template    → CLI: apply-template source.docx --template template.docx --output result.docx
5. Validate (XSD)    → CLI: validate result.docx --xsd wml-subset.xsd
6. GATE-CHECK        → CLI: validate result.docx --xsd business-rules.xsd   ← MUST PASS
7. Diff verify       → CLI: diff source.docx result.docx --text-only   (content must be identical)
```---

## 从模板复制什么

|部分|文件 |描述 |
|------|------|-------------|
|风格 | `word/styles.xml` |所有样式定义（段落、字符、表格、编号）|
|主题 | `word/theme/theme1.xml` |配色方案、字体方案、格式方案 |
|编号| `word/numbering.xml` |列表和编号定义 |
|标题 | `字/标题*.xml` |标题内容和格式 |
|页脚| `字/页脚*.xml` |页脚内容和格式|
|道具栏目| `w:sectPr` |页边距、页面大小、方向、列|

## 什么不会被复制

|部分|原因 |
|------|--------|
|文档内容 |段落、表格、图像均来自来源 |
|评论 |属于源文档的审阅历史 |
|跟踪更改 |属于源文件的修订历史 |
|自定义 XML 部件 |特定于应用程序的数据，而非视觉数据 |
|文档属性 |标题、作者、日期均属于来源 |
|术语表文件 |模板的构建块未转移 |

---

## 模板结构分析（必填）

在选择 Overlay 或 Base-Replace 之前，必须分析模板的内部结构。这是跳过时失败的第一大原因。

### 步骤 1：计算模板段落并识别结构区域

运行 `$CLIanalyze --input template.docx` 或手动检查：```bash
# Quick structure scan
scripts/docx_preview.sh template.docx
```识别模板中的这些区域：```
Zone A: Front matter (cover page, declaration, abstract, TOC)
        → These are KEPT from template, never replaced
Zone B: Example/placeholder body content ("第1章 XXX", sample paragraphs)
        → This is REPLACED with user's actual content
Zone C: Back matter (appendices, acknowledgments, blank pages)
        → These are KEPT from template or removed
Zone D: Final sectPr
        → ALWAYS kept from template
```### 步骤2：找到B区边界（替换范围）

在模板的 document.xml 中搜索标记示例内容开始和结束的锚文本：

**启动锚定模式**（示例正文的第一段）：
- "第一章", "第一章", "第一章", "1 引言", "绪论"
- TOC 之后第一个具有 Heading1 等效样式的段落

**结束锚定模式**（后面的内容之前的最后一段）：
- 《参考文献》、《参考文献》、《致谢》、《致谢》
- 附录或最后 sectPr 之前的最后一段```python
# Pseudocode for finding replacement range
for i, element in enumerate(template_body_elements):
    text = get_text(element)
    style = get_style(element)
    if style in heading1_styles and ("第1章" in text or "Chapter 1" in text):
        replace_start = i
    if "参考文献" in text or "References" in text:
        replace_end = i
        break
```**关键**：通过打印里面的内容来验证范围：```
Template elements [0..replace_start-1]: front matter (KEEP)
Template elements [replace_start..replace_end]: example content (REPLACE)
Template elements [replace_end+1..end]: back matter (KEEP)
```如果找不到replace_start或replace_end，请不要继续。 Ask the user to identify the replacement boundaries.

### 步骤 3：决定覆盖还是基础替换

现在您已经了解了结构：

|观察|决定|
|----------|----------|
|模板≤30段，无封面/TOC | **C-1：叠加**（纯风格模板）|
|模板有超过 100 个段落，其中包括封面/目录/示例部分 | **C-2：基础替换** |
|模板段落数 ≈ 用户文档 | **C-1：覆盖**（类似结构）|
| Template paragraph count >> user document (e.g., 263 vs 134) | **C-2：基础替换** |

### Step 4: For Base-Replace, execute the replacement

1.加载模板作为基础（所有文件）
2. Extract user content elements using `list(body)` — NOT `findall('w:p')` (which misses tables)
3. Build new body: `template[0:replace_start] + cleaned_user_content + template[replace_end+1:]`
4. 对每个段落应用样式映射
5.干净的直接格式（参见下面的规则）
6. Rebuild document.xml, keeping template's namespace declarations
7. 合并关系（图像+超链接）
8. 使用模板作为 ZIP 基础编写输出

---

## 风格映射策略

When template style names differ from source style names, a mapping is required. **This step is mandatory** — skipping it is the #1 cause of formatting failures in template application.

### Step 0: Extract StyleIds from Both Documents (REQUIRED)

Before any template application, extract and compare styleIds from both documents:```bash
# Extract all styleIds from source
$CLI analyze --input source.docx --styles-only
# Output example:
#   Heading1  (paragraph, basedOn: Normal)
#   Heading2  (paragraph, basedOn: Normal)
#   Normal    (paragraph)
#   ListBullet (paragraph, basedOn: Normal)

# Extract all styleIds from template
$CLI analyze --input template.docx --styles-only
# Output example:
#   1         (paragraph, basedOn: a, name: "heading 1")
#   2         (paragraph, basedOn: a, name: "heading 2")
#   3         (paragraph, basedOn: a, name: "heading 3")
#   a         (paragraph, name: "Normal")
#   a0        (character, name: "Default Paragraph Font")
```**关键区别**：`w:styleId` 与 `w:name`：```xml
<!-- styleId="1" but name="heading 1" -->
<w:style w:type="paragraph" w:styleId="1">
  <w:name w:val="heading 1"/>
  <w:basedOn w:val="a"/>
</w:style>
````w:styleId` 属性是 `<w:pStyle w:val="..."/>` 引用的内容。 `w:name` 属性是人类可读的显示名称。 **它们可以完全不同。** 许多 CJK 模板使用数字 styleId（`1`、`2`、`3`、`a`、`a0`）而不是英文名称。

### 第 1 层：精确 StyleId 匹配
如果源使用“Heading1”并且模板将“Heading1”定义为 styleId，则直接映射。无需采取任何行动。

### 第 2 层：基于名称的匹配
如果没有精确的 styleId 匹配，请尝试通过 `w:name` 属性进行匹配：
- 源 `Heading1` (name="heading 1") → 模板 styleId `1` (name="heading 1")
- 匹配名称值时不区分大小写

在同一类型中，还可以尝试通过以下方式进行匹配：
- 内置样式ID（Word的内部ID，例如标题1=内置ID 1）
- 样式类型（段落→段落、字符→字符、表格→表格）

### 第 3 层：手动映射
对于重命名或自定义样式，请提供显式映射：```json
{
  "styleMap": {
    "Heading1": "1",
    "Heading2": "2",
    "Heading3": "3",
    "Heading4": "3",
    "Normal": "a",
    "BodyText": "a",
    "ListBullet": "a",
    "CompanyName": "Title",
    "OldTableStyle": "TableGrid"
  }
}
```### 常见的非标准 StyleId 模式

|模板来源| StyleId 模式 |示例|
|----------------|-----------------|---------|
|中文单词（默认）|数字/字母 | `1`、`2`、`3`、`a`、`a0` |
|英文单词（默认）|英文名字| `标题1`、`正常`、`标题` |
| Google 文档导出 |前缀 | `副标题`、`NormalWeb` |
| WPS办公|混合| `1`、`Heading1`、自定义名称 |
|学术模板|定制| `论文标题1`、`论文正文` |

### 构建映射表

遵循这个算法：

1. **列出`document.xml`中实际使用的源styleIds**（并非全部在`styles.xml`中定义）：```python
   # Pseudocode: find all unique pStyle values in source document.xml
   used_styles = set()
   for p in body.iter('w:p'):
       pStyle = p.find('w:pPr/w:pStyle')
       if pStyle is not None:
           used_styles.add(pStyle.get('val'))
   ```2. **对于每种使用的样式**，在模板中找到最佳匹配：
   - 第一次尝试：完全匹配 styleId
   - 第二次尝试：按“w:name”值匹配（不区分大小写）
   - 第三次尝试：按样式目的匹配（任何标题→模板的标题样式）
   - 后备：映射到模板的默认段落样式（通常为“Normal”或“a”）

3. **验证映射** — 每个源 styleId 必须映射到现有模板 styleId：```
   ✓ Heading1 → 1 (name match: "heading 1")
   ✓ Heading2 → 2 (name match: "heading 2")
   ✓ Normal   → a (name match: "Normal")
   ✗ CustomCallout → ??? (no match found, will fallback to 'a')
   ```4. **在复制内容时应用映射** — 更新每个 `<w:pStyle w:val="..."/>`：```xml
   <!-- Source -->
   <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
   <!-- After mapping -->
   <w:pPr><w:pStyle w:val="1"/></w:pPr>
   ```### 未映射的样式
源文档中与模板中不匹配的样式将记录为警告：```
WARNING: Style 'CustomCallout' has no mapping in template. Content will fall back to 'a' (Normal).
```内容被保留；仅样式参考更新为模板的默认段落样式。

### C-2 BASE-REPLACE：其他 StyleId 注意事项

当使用模板作为基础文档（C-2 策略）时，模板的“styles.xml”已经就位。您必须：

1. **永远不要复制源代码 `styles.xml`** — 模板的样式才是权威
2. **在插入之前将每个内容段落的 pStyle** 映射到模板的 styleId
3. **选择性地剥离直接格式**（详细规则见下文）——让模板样式控制外观
4. **验证表格样式** - 如果源表使用 `TableGrid` 但模板将其定义为 `a3` 或类似的，也重新映射 `<w:tblStyle>`
5. **检查字符样式** - 运行中的“rPr”可能会引用模板中具有不同 ID 的字符样式，例如“Hyperlink”或“Strong”

### Direct Formatting Cleanup Rules (Detailed)

将内容从源复制到模板时，将这些规则应用于每个段落并运行：

**从 `<w:rPr>` 中删除：**
- `<w:rFonts w:ascii="..." w:hAnsi="..."/>` — 拉丁字体覆盖（除了：保留 `w:eastAsia`）
- `<w:sz>`, `<w:szCs>` — 字体大小（让样式控制）
- `<w:color>` — 文本颜色
- `<w:highlight>` — 突出显示颜色
- `<w:shd>` — 阴影
- `<w:b>`、`<w:i>` — 粗体/斜体，除非源样式需要（例如，强调）
- `<w:u>` — 下划线
- `<w:spacing>` — 字符间距

**保留在 `<w:rPr>` 中：**
- `<w:rFonts w:eastAsia="宋体"/>` — CJK 字体声明（必须保留，否则中文文本渲染错误）
- `<w:rFonts w:eastAsia="华文中宋"/>` — 同样的原因
- `<w:drawing>` 内的任何内容 — 图像引用（通过 rId 重新映射单独处理）

**从 `<w:pPr>` 中删除：**
- `<w:pBdr>` — 段落边框
- `<w:shd>` — 段落底纹
- `<w:spacing>` — 行/段落间距（让样式控制）
- `<w:jc>` — 理由（让样式控制）
- `<w:tabs>` — 自定义制表位
- pPr 内的 `<w:rPr>` — 段落的默认运行格式

**保留在 `<w:pPr>` 中：**
- `<w:pStyle>` — 样式引用（映射到模板的 styleId 之后）
- `<w:sectPr>` — 节属性（如果有意插入分节符）
- `<w:numPr>` — 编号参考（将 numId 映射到模板的编号之后）

**表格单元格（`<w:tc>`）：**
对每个单元格内的每个段落应用相同的 rPr/pPr 清理。另外：
- 保留`<w:tcPr>`结构属性（列跨度、行跨度、宽度）
- 删除`<w:tcPr><w:shd>`（单元格阴影 - 让表格样式控制）

---

## 关系 ID 重新映射

将模板中的部分（页眉、页脚、图像）复制到源包时，关系 ID (`r:id`) 可能会发生冲突。

**问题**：
- 源有 `rId7` → `image1.png`
- 模板有 `rId7` → `header1.xml`
- 复制模板的“rId7”会覆盖源的图像引用

**解决方案**：
1. 扫描源的“document.xml.rels”以查找所有现有的“rId”值
2. 查找最大数字 ID（例如 `rId12`）
3. 重新映射从`rId13`开始的所有模板关系ID
4. 更新复制零件中的所有引用以使用新 ID```xml
<!-- Template original -->
<Relationship Id="rId1" Type="...header" Target="header1.xml" />

<!-- After remapping into source package -->
<Relationship Id="rId13" Type="...header" Target="header1.xml" />

<!-- Update sectPr reference -->
<w:headerReference w:type="default" r:id="rId13" />
```### 超链接关系合并

当源文档包含外部超链接（例如，引用或脚注中的 URL）时，这些链接将作为关系存储在 `word/_rels/document.xml.rels` 中：```xml
<Relationship Id="rId15" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
              Target="https://example.com/paper" TargetMode="External"/>
```document.xml 中的相应文本引用此 rId：```xml
<w:hyperlink r:id="rId15">
  <w:r><w:t>https://example.com/paper</w:t></w:r>
</w:hyperlink>
```**合并步骤：**
1. 扫描源 document.xml 中的所有 `<w:hyperlink r:id="...">` 元素
2.对于每一个，在source的rels文件中找到对应关系
3. 检查模板是否已与同一目标 URL 存在关系
   - 如果是：重用现有的rId，更新超链接引用
   - 如果没有：分配一个新的rId（从模板的最大rId + 1开始），将关系添加到模板的rels，更新超链接引用
4.还要检查脚注（`word/_rels/footnotes.xml.rels`）和尾注中使用的超链接关系

**常见错误：** 复制超链接段落而不合并rels→超链接默默地断开（在Word中单击不执行任何操作）。

---

## XSD 门检查

### 这是什么

应用模板后，输出文档**必须**通过“business-rules.xsd”验证。这是一个**硬门** - 如果失败，该文档**无法交付**。

###business-rules.xsd 检查什么

|规则|它验证了什么 |
|------|--------------------|
|模板样式存在 |内容段落引用的所有样式均在“styles.xml”中定义 |
|边距匹配 |页边距符合模板规范 |
|字体正确 | `w:docDefaults` 字体与模板的字体方案匹配 |
|标题层次|标题级别是连续的（没有 H1 → H3 没有 H2） |
|现有所需款式 | `Normal`、`Heading1`-`Heading3`、`TableGrid` 存在 |
|页面尺寸|匹配模板声明的页面大小 |

### 处理失败```
GATE-CHECK FAILED:
  - Style 'CustomStyle1' referenced in paragraph 14 but not defined in styles.xml
  - Margin w:left=1080 does not match template requirement 1440
```修复每个失败：
1. **缺少样式**：将样式定义添加到`styles.xml`，或将段落重新映射到现有样式
2. **边距不匹配**：更新`w:sectPr`边距以匹配模板
3. **字体不匹配**：更新`w:docDefaults`以匹配模板字体方案
4. **标题层次间隙**：插入中间标题级别或调整现有级别

每次修复后重新验证，直到门检查通过。

---

## 常见陷阱

### 1. 孤立编号参考

**问题**：源文档在列表段落中使用 `w:numId="5"`，但将 `numbering.xml` 替换为模板的版本后，编号 ID 5 不存在。

**症状**：列表显示为纯段落（没有项目符号/数字）。

**修复**：
- 将源编号 ID 映射到模板编号 ID
- 更新文档内容中的所有“w:numId”引用
- 或者将源编号定义合并到模板的“numbering.xml”中

### 2.缺少主题颜色

**问题**：源文档的样式引用的主题颜色 (`w:themeColor="accent1"`) 在模板的主题中具有不同的值。

**症状**：颜色意外变化（通常可以接受 - 这是重新主题的重点）。但是，如果样式将“w:color”与“w:val”和“w:themeColor”一起使用，则主题颜色在 Word 中获胜。

**修复**：查看颜色变化。如果必须保留特定颜色，请使用显式的“w:val”，而不使用“w:themeColor”。

### 3. 节属性冲突

**问题**：源文档有多个部分（例如，纵向+横向页面），但模板假定只有一个部分。

**症状**：所有部分都有相同的边距/方向，破坏横向页面。

**修复**：
- 仅将模板部分属性应用于“w:body”中的最终“w:sectPr”
- 保留源中的中间“w:sectPr”元素（在“w:pPr”内部）
- 或将模板属性应用于所有部分但保留方向覆盖

### 4.嵌入字体冲突

**问题**：模板指定的字体在目标系统上不可用。

**修复**：在 DOCX 中嵌入字体（`word/fonts/`）或使用网络安全替代方案：
- Calibri → 可在 Windows/Mac/Office 上在线使用
- Arial → 通用后备
- Times New Roman → 通用衬线后备

### 5. 风格继承被破坏

**问题**：模板具有基于“Normal”的“Heading1”，但应用模板后，“Normal”具有不同的属性，对标题进行级联不需要的更改。

**修复**：验证所有关键样式的“w:basedOn”链。确保基本样式也从模板正确转移。

---

## 验证清单

模板应用后，验证：

1. **内容保留** - 文本差异显示零内容更改
2. **门检查已通过** — `business-rules.xsd` 验证成功
3. **应用样式** — 标题、正文、表格使用模板格式
4. **图像完好无损** — 所有图像均正确渲染（关系 ID 有效）
5. **列表工作** - 编号和项目符号列表正确显示
6. **页眉/页脚** — 模板页眉/页脚出现在所有页面上
7. **页面布局** — 边距、页面大小、方向匹配模板
8. **无损坏** — 文件在 Word 中打开时没有错误