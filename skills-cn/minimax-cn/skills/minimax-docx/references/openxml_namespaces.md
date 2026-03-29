# OpenXML 命名空间、关系类型和内容类型

## 核心命名空间

|前缀 |统一资源定位符 |用于 |
|--------|-----|---------|
| `w` | `http://schemas.openxmlformats.org/wordprocessingml/2006/main` | document.xml、styles.xml、numbering.xml、页眉、页脚 |
| `r` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` |关系参考 (r:id) |
| `wp` | `http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing` |文档中的图像/绘图位置 |
| `a` | `http://schemas.openxmlformats.org/drawingml/2006/main` | DrawingML 核心（形状、图像、主题）|
| `图片` | `http://schemas.openxmlformats.org/drawingml/2006/picture` | DrawingML 中的图片元素 |
| `v` | `urn:schemas-microsoft-com:vml` | VML（传统形状、水印）|
| `o` | `urn:schemas-microsoft-com:office:office` | Office VML 扩展 |
| `m` | `http://schemas.openxmlformats.org/officeDocument/2006/math` |数学方程 (OMML) |
| `mc` | `http://schemas.openxmlformats.org/markup-compatibility/2006` |标记兼容性（可忽略、AlternateContent）|

## 扩展命名空间

|前缀 |统一资源定位符 |目的|
|--------|-----|---------|
| `w14` | `http://schemas.microsoft.com/office/word/2010/wordml` | Word 2010 扩展（contentPart 等）|
| `w15` | `http://schemas.microsoft.com/office/word/2012/wordml` | Word 2013 扩展（commentEx 等）|
| `w16cid` | `http://schemas.microsoft.com/office/word/2016/wordml/cid` |评论 ID（持久 ID）|
| `w16cex` | `http://schemas.microsoft.com/office/word/2018/wordml/cex` |评论可扩展|
| `w16se` | `http://schemas.microsoft.com/office/word/2015/wordml/symex` |符号扩展|
| `wps` | `http://schemas.microsoft.com/office/word/2010/wordprocessingShape` | WordprocessingML 形状 |
| `木塑复合材料` | `http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas` |绘图画布|

## 关系类型

|关系 |输入 URI |
|----------|----------|
|文件| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument` |
|风格 | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles` |
|编号| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering` |
|字体表| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable` |
|设置| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings` |
|主题 | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme` |
|图片| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/image` |
|超链接| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink` |
|标题| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/header` |
|页脚| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer` |
|评论 | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments` |
|评论扩展 | `http://schemas.microsoft.com/office/2011/relationships/commentsExtended` |
|评论 ID | `http://schemas.microsoft.com/office/2016/09/relationships/commentsIds` |
|评论可扩展 | `http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible` |
|脚注| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes` |
|尾注| `http://schemas.openxmlformats.org/officeDocument/2006/relationships/endnotes` |
|词汇表 | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/glossaryDocument` |
|网页设置 | `http://schemas.openxmlformats.org/officeDocument/2006/relationships/webSettings` |

## 内容类型 (`[Content_Types].xml`)

### 默认扩展名```xml
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
<Default Extension="xml" ContentType="application/xml" />
<Default Extension="png" ContentType="image/png" />
<Default Extension="jpeg" ContentType="image/jpeg" />
<Default Extension="gif" ContentType="image/gif" />
<Default Extension="emf" ContentType="image/x-emf" />
```### 部分覆盖

|部分|内容类型 |
|------|-------------|
| `/word/document.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml` |
| `/word/styles.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml` |
| `/word/numbering.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml` |
| `/word/settings.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml` |
| `/word/fontTable.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml` |
| `/word/theme/theme1.xml` | `application/vnd.openxmlformats-officedocument.theme+xml` |
| `/word/header1.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml` |
| `/word/footer1.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml` |
| `/word/comments.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml` |
| `/word/commentsExtended.xml` | `application/vnd.ms-word.commentsExtended+xml` |
| `/word/commentsIds.xml` | `application/vnd.ms-word.commentsIds+xml` |
| `/word/commentsExtensible.xml` | `application/vnd.ms-word.commentsExtensible+xml` |
| `/word/footnotes.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml` |
| `/word/endnotes.xml` | `application/vnd.openxmlformats-officedocument.wordprocessingml.endnotes+xml` |