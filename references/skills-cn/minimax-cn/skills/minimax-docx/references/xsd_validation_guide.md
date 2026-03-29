# XSD 验证指南

## 运行验证```bash
# Validate against the WML subset schema
dotnet run --project minimax-docx validate input.docx --xsd assets/xsd/wml-subset.xsd

# Validate against business rules (REQUIRED for Scenario C gate-check)
dotnet run --project minimax-docx validate input.docx --xsd assets/xsd/business-rules.xsd

# Validate against both
dotnet run --project minimax-docx validate input.docx --xsd assets/xsd/wml-subset.xsd --xsd assets/xsd/business-rules.xsd
```---

## wml-subset.xsd 涵盖的内容

子集架构验证最常见的 WordprocessingML 元素：

|面积 |元素已验证 |
|------|--------------------|
|文档结构 | `w:document`、`w:body`、`w:sectPr` |
|段落| `w:p`、`w:pPr`、`w:r`、`w:rPr`、`w:t` |
|桌子| `w:tbl`、`w:tblPr`、`w:tblGrid`、`w:tr`、`w:tc` |
|风格 | `w:styles`、`w:style`、`w:docDefaults` |
|列表 | `w:编号`、`w:abstractNum`、`w:num` |
|页眉/页脚| `w:hdr`、`w:ftr` |
|追踪变更 | `w:ins`、`w:del`、`w:rPrChange`、`w:pPrChange` |
|评论 | `w:comment`、`w:commentRangeStart`、`w:commentRangeEnd` |

### 它不涵盖什么

- DrawingML 元素（`a:`、`pic:`、`wp:`）— 图像/形状内部
- VML 元素（`v:`、`o:`）— 遗留形状
- 数学元素 (`m:`) — 方程
- 扩展命名空间（`w14`、`w15`、`w16*`）- 供应商扩展
- 自定义 XML 数据部分
- 关系和内容类型验证（结构性的，而不是基于模式的）

---

## 解释错误

### 元素排序错误```
ERROR: Element 'w:jc' is not expected at this position.
Expected: w:spacing, w:ind, w:contextualSpacing, ...
Location: /word/document.xml, line 45
```**原因**：子元素顺序错误。请参阅“references/openxml_element_order.md”。
**修复**：重新排序子项以匹配架构序列。

### 缺少必需元素```
ERROR: Element 'w:tbl' missing required child 'w:tblPr'.
Location: /word/document.xml, line 102
```**原因**：缺少必需的子元素。
**修复**：添加缺少的元素。表格需要 `w:tblPr` 和 `w:tblGrid`。

### 属性值无效```
ERROR: Attribute 'w:val' has invalid value 'middle'.
Expected: 'left', 'center', 'right', 'both', 'distribute'
Location: /word/document.xml, line 78
```**原因**：属性值不在允许的枚举中。
**修复**：使用错误中列出的有效值之一。

### 意外元素```
ERROR: Element 'w:customTag' is not expected.
Location: /word/document.xml, line 200
```**原因**：子集架构中未定义元素。可能是供应商扩展。
**修复**：检查它是否是已知扩展名（w14/w15/w16）。如果是这样，它可能是安全的。如果未知，请调查或删除。

---

## 业务规则 XSD

“business-rules.xsd”模式强制执行超出标准 OpenXML 有效性的特定于项目的约束：

|规则|它检查什么 |
|------|----------------|
|所需款式 | `Normal`、`Heading1`-`Heading3`、`TableGrid` 必须存在于 `styles.xml` 中 |
|字体一致性 | `w:docDefaults` 字体与预期值匹配 |
|保证金范围 |页边距在可接受的范围内 (720-2160 DXA) |
|页面尺寸|必须是 A4 或 Letter |
|标题层次|无间隙（例如，H1 → H3，没有 H2）|
|风格链| `w:basedOn` 引用必须解析为现有样式 |

### 扩展业务规则

要添加特定于项目的规则，请添加 `xs:assert` 或 `xs:restriction` 元素：```xml
<!-- Require minimum 1-inch margins -->
<xs:element name="pgMar">
  <xs:complexType>
    <xs:attribute name="top" type="xs:integer">
      <xs:restriction>
        <xs:minInclusive value="1440" />
      </xs:restriction>
    </xs:attribute>
  </xs:complexType>
</xs:element>
```---

## 门检查：场景 C 硬门

在场景 C（应用模板）中，输出文档**必须**在交付前通过“business-rules.xsd”验证：```
1. Apply template  →  output.docx
2. Validate        →  dotnet run ... validate output.docx --xsd business-rules.xsd
3. PASS?           →  Deliver to user
4. FAIL?           →  Fix issues, re-validate, repeat until PASS
```**这是一道硬门。** 未通过业务规则验证的文档无法交付，即使它在 Word 中正确打开也是如此。

---

## 误报

### 供应商扩展

扩展命名空间（`w14`、`w15`、`w16*`）中的元素不在子集模式中，可能会触发警告：```
WARNING: Element '{http://schemas.microsoft.com/office/word/2010/wordml}shadow' is not expected.
```这些通常可以安全地忽略——它们是 Microsoft 对新功能的扩展（例如高级文本效果、评论扩展）。

### 标记兼容性

文档可能包含具有后备内容的“mc:AlternateContent”块。子集架构可能无法识别“mc:”命名空间处理。如果文档在 Word 中正确打开，这些都是安全的。

### 推荐方法

1. 运行验证
2. 将**错误**视为必须修复的
3. 查看**警告** — 忽略已知的供应商扩展，调查未知元素
4.修复错误后，重新验证确认