# 评论系统指南（4文件架构）

## 概述

文字注释需要跨**四个 XML 文件**以及“document.xml”、“[Content_Types].xml”和“document.xml.rels”中的引用进行协调。

---

## 四个评论文件

### 1. `word/comments.xml` — 主要评论内容

包含实际的评论文本：```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:comment w:id="1" w:author="Alice" w:date="2026-03-21T09:00:00Z" w:initials="A">
    <w:p>
      <w:pPr><w:pStyle w:val="CommentText" /></w:pPr>
      <w:r>
        <w:rPr><w:rStyle w:val="CommentReference" /></w:rPr>
        <w:annotationRef />
      </w:r>
      <w:r>
        <w:t>This needs clarification.</w:t>
      </w:r>
    </w:p>
  </w:comment>
</w:comments>
```关键属性：`w:id`（唯一整数）、`w:author`、`w:date` (ISO 8601)、`w:initials`。

### 2. `word/commentsExtended.xml` — W15 扩展

将评论链接到段落并跟踪已解决的状态：```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w15:commentsEx xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml">
  <w15:commentEx w15:paraId="1A2B3C4D" w15:done="0" />
</w15:commentsEx>
```- `w15:paraId` — 匹配 `comments.xml` 中评论段落的 `w14:paraId`
- `w15:done` — `"0"` = 打开，`"1"` = 已解决

### 3. `word/commentsIds.xml` — 持久 ID 映射

提供持久的 ID，可在文档中进行复制/粘贴：```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cid:commentsIds xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid">
  <w16cid:commentId w16cid:paraId="1A2B3C4D" w16cid:durableId="12345678" />
</w16cid:commentsIds>
```- `w16cid:paraId` — 与 `w15:paraId` 相同
- `w16cid:durableId` — 全局唯一标识符（8 位十六进制）

### 4. `word/commentsExtensible.xml` — W16 扩展

现代注释扩展（在较新的 Word 版本中使用）：```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w16cex:commentsExtensible xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex">
  <w16cex:commentExtensible w16cex:durableId="12345678" w16cex:dateUtc="2026-03-21T09:00:00Z" />
</w16cex:commentsExtensible>
```---

## Document.xml 参考

评论使用三个元素锚定在文档内容中：```xml
<w:p>
  <w:commentRangeStart w:id="1" />
  <w:r><w:t>This text has a comment.</w:t></w:r>
  <w:commentRangeEnd w:id="1" />
  <w:r>
    <w:rPr><w:rStyle w:val="CommentReference" /></w:rPr>
    <w:commentReference w:id="1" />
  </w:r>
</w:p>
```- `w:commentRangeStart` — 标记注释文本的开始位置
- `w:commentRangeEnd` — 标记注释文本的结束位置
- `w:commentReference` — 可见的注释标记（上标数字），放置在范围结束之后的运行中

所有三个上的“w:id”必须与“comments.xml”中的“w:id”匹配。

---

## 内容类型注册

添加到`[Content_Types].xml`：```xml
<Override PartName="/word/comments.xml"
          ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml" />
<Override PartName="/word/commentsExtended.xml"
          ContentType="application/vnd.ms-word.commentsExtended+xml" />
<Override PartName="/word/commentsIds.xml"
          ContentType="application/vnd.ms-word.commentsIds+xml" />
<Override PartName="/word/commentsExtensible.xml"
          ContentType="application/vnd.ms-word.commentsExtensible+xml" />
```---

## 关系登记

添加到`word/_rels/document.xml.rels`：```xml
<Relationship Id="rId20" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
              Target="comments.xml" />
<Relationship Id="rId21" Type="http://schemas.microsoft.com/office/2011/relationships/commentsExtended"
              Target="commentsExtended.xml" />
<Relationship Id="rId22" Type="http://schemas.microsoft.com/office/2016/09/relationships/commentsIds"
              Target="commentsIds.xml" />
<Relationship Id="rId23" Type="http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible"
              Target="commentsExtensible.xml" />
```---

## 分步：添加新评论

1. **选择唯一的评论ID**（扫描现有的`w:id`值，使用max + 1）
2. **生成 paraId** （8 个字符的十六进制，例如 `"1A2B3C4D"`）和 DurableId （8 位十六进制）
3. **添加到`comments.xml`**：创建包含内容的`w:comment`元素
4. **添加到 `commentsExtended.xml`**：使用 `paraId`、`done="0"` 创建 `w15:commentEx`
5. **添加到`commentsIds.xml`**：使用`paraId`和`durableId`创建`w16cid:commentId`
6. **添加到`commentsExtensible.xml`**：使用`durableId`和`dateUtc`创建`w16cex:commentExtensible`
7. **添加到`document.xml`**：在目标文本周围插入`w:commentRangeStart`、`w:commentRangeEnd`和`w:commentReference`
8. **验证 `[Content_Types].xml`** 和 `document.xml.rels` 是否包含所有 4 个文件的条目

---

## 分步：添加回复

回复是其段落的“w14:paraId”链接到父评论的评论：

1. 在 `comments.xml` 中使用新的 `w:id` 创建一个新的 `w:comment`
2. 在 `commentsExtended.xml` 中，添加 `w15:commentEx`：
   - `w15:paraId` = 新段落 ID
   - `w15:paraIdParent` = 正在回复的评论的 `paraId`
   -`w15：完成=“0”`
3. 在 `commentsIds.xml` 和 `commentsExtensible.xml` 中添加条目
4. 在`document.xml`中，回复不需要自己的范围标记——它共享父级的范围```xml
<!-- In commentsExtended.xml -->
<w15:commentEx w15:paraId="5E6F7A8B" w15:paraIdParent="1A2B3C4D" w15:done="0" />
```---

## 分步：解决评论

在评论的 `w15:commentEx` 条目上设置 `w15:done="1"`：```xml
<!-- Before -->
<w15:commentEx w15:paraId="1A2B3C4D" w15:done="0" />

<!-- After -->
<w15:commentEx w15:paraId="1A2B3C4D" w15:done="1" />
```这标志着评论（及其所有回复）已解决。注释仍然可见，但在 Word 中显示为灰色。

---

## 最小可行评论

工作评论至少需要：
1.带有“w:comment”元素的“comments.xml”
2. 带有范围标记和引用的`document.xml`
3.`document.xml.rels`中的关系
4. `[Content_Types].xml` 中的内容类型

扩展文件（`commentsExtended`、`commentsIds`、`commentsExtensible`）是可选的，但建议与现代 Word 完全兼容。