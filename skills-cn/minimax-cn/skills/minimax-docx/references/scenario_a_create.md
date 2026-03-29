# 场景 A：从头开始创建新的 DOCX

## 何时使用

在以下情况下使用场景 A：
- 用户没有现有文件并想要一个全新的文档
- 用户提供内容（文本、表格、图像）并希望将其组装成 DOCX
- 用户指定文档类型（报告、信件、备忘录、学术）或描述自定义布局

不要在以下情况下使用：用户已经有了要修改的 DOCX（→ 场景 B）或想要重新设计现有文档的样式（→ 场景 C）。

---

## 分步工作流程

### 1. 确定文档类型

根据用户的请求询问或推断文档类型：

|类型 |典型信号 |
|------|----------------|
|报告| “报告”、“分析”、“白皮书”、带标题的部分 |
|信| “信”、“亲爱的”、地址栏、称呼 |
|备忘录 | “备忘录”、“备忘录”、收件人/发件人/主题字段 |
|学术| “论文”、“论文”、“论文”、APA/MLA/芝加哥提及 |
|定制|以上都不是，或者用户指定了确切的格式 |

### 2. 收集内容要求

从用户处收集：
- 标题和副标题（如果有）
- 作者/组织
- 章节结构（标题和嵌套）
- 每节的正文内容
- 表格（标题+行）
- 图像（文件路径或占位符）
- 特殊元素：目录、页码、水印、页眉/页脚

### 3.选择样式集

根据文档类型，加载匹配样式的 XML 资源：
- 报告 → `assets/styles/default_styles.xml` 或 `assets/styles/corporate_styles.xml`
- 学术 → `assets/styles/academic_styles.xml`
- 信函/备忘录/自定义 → `assets/styles/default_styles.xml`（带覆盖）

### 4. 配置页面设置

根据文档类型默认值（见下文）或用户覆盖设置“w:sectPr”值。```xml
<w:sectPr>
  <w:pgSz w:w="11906" w:h="16838" />  <!-- A4 -->
  <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"
           w:header="720" w:footer="720" w:gutter="0" />
</w:sectPr>
```### 5.构建文档结构

将 `word/document.xml` 组装为：
1. `w:body` 作为根容器
2. 带有章节标题标题样式的段落 (`w:p`)
3. 正文段落采用“Normal”风格
4. 表格、图像和其他需要的元素
5. 最终 `w:sectPr` 作为 `w:body` 的最后一个子级

### 6.应用版式默认值

在“w:docDefaults”下的“styles.xml”中设置文档级默认值：```xml
<w:docDefaults>
  <w:rPrDefault>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="SimSun" w:cs="Arial" />
      <w:sz w:val="22" />  <!-- 11pt -->
      <w:szCs w:val="22" />
    </w:rPr>
  </w:rPrDefault>
  <w:pPrDefault>
    <w:pPr>
      <w:spacing w:after="160" w:line="259" w:lineRule="auto" />
    </w:pPr>
  </w:pPrDefault>
</w:docDefaults>
```### 7. 添加复杂元素

请参阅下面的复杂元素指南部分。

### 8. 运行验证管道```
dotnet run ... validate --xsd wml-subset.xsd
dotnet run ... validate --xsd business-rules.xsd   # if applying a template
```---

## 文档类型默认值

### 报告
|物业 |价值|
|----------|--------|
|正文字体|口径 11 点 |
|标题字体 |卡利布里光|
| H1/H2/H3/H4 尺寸 | 28 点 / 24 点 / 18 点 / 14 点 |
|标题颜色 | #2F5496（企业蓝）|
|利润 | 1 英寸 (1440 DXA) 所有面 |
|页面尺寸| A4（11906 × 16838 DXA）|
|行间距|单（行=“240”）|
|段落间距 |身体前 0pt，身体后 8pt |

### 信
|物业 |价值|
|----------|--------|
|字体|口径 11 点 |
|页面尺寸|信函 (12240 × 15840 DXA) |
|利润 | 1 inch all sides |
|结构|日期→地址→称呼→正文→结束→签名|
|行间距|单|

### 备忘录
|物业 |价值|
|----------|--------|
|字体|宋体 11pt |
|页面尺寸|信|
|利润 | 0.75 英寸 (1080 DXA) |
|标题| “MEMO”居中，粗体，16pt |
|领域 |收件人、发件人、日期、主题（粗体标签、制表符对齐值）|

### 学术
|物业 |价值|
|----------|--------|
|字体|泰晤士新罗马字体 12pt |
|行间距|双（行=“480”）|
|利润 |各边 1 英寸 |
|页面尺寸|信|
|标题 | H1/H2/H3 为粗体、相同字体、14/13/12pt |
|首行缩进| 0.5 英寸 (720 DXA) |
|标题颜色 |黑色（无颜色）|

---

## 内容配置 JSON 格式

CLI `create` 命令接受 JSON 配置：```json
{
  "type": "report",
  "title": "Quarterly Revenue Analysis",
  "subtitle": "Q1 2026",
  "author": "Finance Team",
  "pageSize": "A4",
  "margins": { "top": 1440, "right": 1440, "bottom": 1440, "left": 1440 },
  "sections": [
    {
      "heading": "Executive Summary",
      "level": 1,
      "content": [
        { "type": "paragraph", "text": "Revenue grew 12% year-over-year..." },
        {
          "type": "table",
          "headers": ["Region", "Revenue", "Growth"],
          "rows": [
            ["North America", "$4.2M", "+15%"],
            ["Europe", "$2.8M", "+8%"],
            ["Asia Pacific", "$1.9M", "+18%"]
          ]
        },
        { "type": "image", "path": "charts/revenue.png", "width": "5in", "alt": "Revenue chart" }
      ]
    },
    {
      "heading": "Detailed Analysis",
      "level": 1,
      "content": [
        { "type": "paragraph", "text": "Breaking down by product line..." }
      ]
    }
  ]
}
```支持的内容类型：
- `paragraph` — 正文（应用普通样式）
- `table` — 标题 + 行（应用 TableGrid 样式）
- `image` — 具有宽度/高度控制的内联图像
- `list` — 带项目符号或编号的列表项
- `pageBreak` — 强制分页

---

## 复杂元素指南

### 目录

插入目录字段代码。打开文件时，Word 将更新实际条目：```xml
<w:p>
  <w:pPr><w:pStyle w:val="TOCHeading" /></w:pPr>
  <w:r><w:t>Table of Contents</w:t></w:r>
</w:p>
<w:p>
  <w:r>
    <w:fldChar w:fldCharType="begin" />
  </w:r>
  <w:r>
    <w:instrText xml:space="preserve"> TOC \o "1-3" \h \z \u </w:instrText>
  </w:r>
  <w:r>
    <w:fldChar w:fldCharType="separate" />
  </w:r>
  <w:r>
    <w:t>[Table of contents — update to populate]</w:t>
  </w:r>
  <w:r>
    <w:fldChar w:fldCharType="end" />
  </w:r>
</w:p>
```### 页脚中的页码

添加页脚部分（`word/footer1.xml`）并在`w:sectPr`中引用它：```xml
<!-- In footer1.xml -->
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="center" /></w:pPr>
    <w:r>
      <w:fldChar w:fldCharType="begin" />
    </w:r>
    <w:r>
      <w:instrText>PAGE</w:instrText>
    </w:r>
    <w:r>
      <w:fldChar w:fldCharType="separate" />
    </w:r>
    <w:r><w:t>1</w:t></w:r>
    <w:r>
      <w:fldChar w:fldCharType="end" />
    </w:r>
  </w:p>
</w:ftr>

<!-- In sectPr -->
<w:footerReference w:type="default" r:id="rId8" />
```### 水印

添加标题部分，并在文本后面添加形状：```xml
<w:hdr>
  <w:p>
    <w:r>
      <w:pict>
        <v:shape style="position:absolute;margin-left:0;margin-top:0;width:468pt;height:180pt;
                        z-index:-251657216;mso-position-horizontal:center;
                        mso-position-vertical:center"
                 fillcolor="silver" stroked="f">
          <v:textpath style="font-family:'Calibri';font-size:1pt" string="DRAFT" />
        </v:shape>
      </w:pict>
    </w:r>
  </w:p>
</w:hdr>
```---

## 创建后清单

1. 针对“wml-subset.xsd”**验证** — 所有元素均按正确顺序排列，存在必需的属性
2. **使用相同的格式合并相邻的运行**以保持 XML 干净
3. **验证关系** — document.xml 中的每个 `r:id` 在 `document.xml.rels` 中都有一个匹配的条目
4. **检查内容类型** — 包中的每个部分都在“[Content_Types].xml”中注册
5. **预览** — 在 Word 或 LibreOffice 中打开以直观地确认布局
6. **文件大小** — 确认图像大小合理（如果每个 > 2MB，则进行压缩）