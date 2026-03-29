# 编辑现有演示文稿

## 基于模板的工作流程

使用现有演示文稿作为模板时：

1. **复制并分析**：```bash
   cp /path/to/user-provided.pptx template.pptx
   python -m markitdown template.pptx > template.md
   ```查看“template.md”以查看占位符文本和幻灯片结构。

2. **规划幻灯片映射**：对于每个内容部分，选择一个模板幻灯片。

   **使用不同的布局**——单调的演示是一种常见的失败模式。不要默认使用基本标题+项目符号幻灯片。积极寻找：
   - 多列布局（2列、3列）
   - 图片+文字组合
   - 带文本覆盖的全出血图像
   - 报价或标注幻灯片
   - 部分分隔线
   - 统计/数字标注
   - 图标网格或图标+文本行

   **避免：** 每张幻灯片都重复相同的文本布局。

   将内容类型与布局风格相匹配（例如，关键点 -> 项目符号幻灯片、团队信息 -> 多列、推荐 -> 引用幻灯片）。

3. **解压**：使用Python的“zipfile”模块将PPTX提取到可编辑的XML树中。漂亮地打印 XML 以提高可读性。

4. **构建演示文稿**（您自己执行此操作，而不是与子代理一起执行）：
   - 删除不需要的幻灯片（从“<p:sldIdLst>”中删除）
   - 复制您想要重复使用的幻灯片（复制幻灯片 XML、关系并更新“Content_Types.xml”和“presentation.xml”）
   - 对 `<p:sldIdLst>` 中的幻灯片重新排序
   - **在步骤 5 之前完成所有结构更改**

5. **编辑内容**：更新每个“slide{N}.xml”中的文本。
   **如果可用，请在此处使用子代理** — 幻灯片是单独的 XML 文件，因此子代理可以并行编辑。

6. **清理**：删除孤立文件 - 不在 `<p:sldIdLst>` 中的幻灯片、未引用的媒体、孤立的相关文件。

7. **打包**：将 XML 树重新打包为 PPTX 文件。验证、修复、压缩 XML、重新编码智能报价。

   始终先写入“/tmp/”，然后复制到最终路径。 Python 的“zipfile”模块在内部使用“seek”，这在某些卷挂载（例如 Docker 绑定挂载）上失败。写入本地临时路径可以避免这种情况。

## 输出结构

将用户提供的文件复制到 cwd 中的“template.pptx”。这保留了原始名称并为所有下游操作提供了可预测的名称。```bash
cp /path/to/user-provided.pptx template.pptx
```

```text
./
├── template.pptx               # Copy of user-provided file (never modified)
├── template.md                 # markitdown extraction
├── unpacked/                   # Editable XML tree
└── edited.pptx                 # Final repacked deck
```最低预期交付成果：“edited.pptx”。

## 幻灯片操作

幻灯片顺序位于 `ppt/presentation.xml` -> `<p:sldIdLst>` 中。

**重新排序**：重新排列 `<p:sldId>` 元素。

**删除**：删除 `<p:sldId>`，然后清理孤立文件。

**添加**：复制源幻灯片的 XML 文件及其“.rels”文件，并更新“Content_Types.xml”和“presentation.xml”。切勿在未更新所有引用的情况下手动复制幻灯片文件 - 这会导致注释引用损坏和关系 ID 丢失。

## 编辑内容

**子代理：** 如果可用，请在此处使用它们（完成步骤 4 后）。每张幻灯片都是一个单独的 XML 文件，因此子代理可以并行编辑。在对子代理的提示中，包括：
- 要编辑的幻灯片文件路径
- **“使用编辑工具进行所有更改”**
- 下面的格式规则和常见陷阱

对于每张幻灯片：
1. 读取幻灯片的 XML
2. 识别所有占位符内容——文本、图像、图表、图标、标题
3. 将每个占位符替换为最终内容

**使用编辑工具，而不是 sed 或 Python 脚本。** 编辑工具强制指定要替换的内容和位置，从而产生更好的可靠性。

## 格式规则

- **将所有标题、副标题和内联标签加粗**：在 `<a:rPr>` 上使用 `b="1"`。这包括：
  - 幻灯片标题
  - 幻灯片中的节标题
  - 行首的内联标签（例如：“状态：”、“描述：”）
- **切勿使用 unicode 项目符号**：使用正确的列表格式“<a:buChar>”或“<a:buAutoNum>”
- **项目符号一致性**：让项目符号继承布局。仅指定“<a:buChar>”或“<a:buNone>”。

## 常见陷阱 — 模板编辑

### 模板适配

当源内容的项目少于模板时：
- **完全删除多余的元素**（图像、形状、文本框），而不仅仅是清除文本
- 清除文本内容后检查孤立的视觉效果
- 使用“markitdown”运行内容质量检查以捕获不匹配的计数

当用不同长度的内容替换文本时：
- **较短的更换**：通常是安全的
- **较长的替换**：可能会意外溢出或包裹
- 文本更改后使用“markitdown”进行验证
- 考虑截断或分割内容以适应模板的设计限制

**模板槽！=源项目**：如果模板有 4 个团队成员，但源有 3 个用户，则删除第四个成员的整个组（图像 + 文本框），而不仅仅是文本。

### 多项目内容

如果源有多个项目（编号列表、多个部分），请为每个项目创建单独的 `<a:p>` 元素 — **切勿连接成一个字符串**。

**错误** — 一个段落中的所有项目：```xml
<a:p>
  <a:r><a:rPr .../><a:t>Step 1: Do the first thing. Step 2: Do the second thing.</a:t></a:r>
</a:p>
```**正确** — 带有粗体标题的单独段落：```xml
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 1</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" .../><a:t>Do the first thing.</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 2</a:t></a:r>
</a:p>
<!-- continue pattern -->
```从原始段落复制“<a:pPr>”以保留行距。在标题上使用 `b="1"`。

### 智能报价

编辑工具将智能引号转换为 ASCII。 **添加带引号的新文本时，请使用 XML 实体：**```xml
<a:t>the &#x201C;Agreement&#x201D;</a:t>
```|人物 |名称 |统一码 | XML 实体 |
|------------|------|---------|------------|
| §|左双引号 | U+201C | `&#x201C;` |
| \u201d |右双引号 | U+201D | `&#x201D;` |
| \u2018 |左单引号 | U+2018 | ``` |
| \u2019 |右单引号 | U+2019 | ``` |

### 其他

- **空白**：在带有前导/尾随空格的 `<a:t>` 上使用 `xml:space="preserve"`
- **XML 解析**：使用 `defusedxml.minidom`，而不是 `xml.etree.ElementTree` （破坏命名空间）