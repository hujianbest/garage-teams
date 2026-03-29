#中国大学论文模板指南 (中国高校论文模板指南)

## 本指南为何存在

中国大学论文模板 (.docx) 的结构模式存在显着差异
来自西方模板。采用西方惯例（标题 1/标题 2/普通）的代理将
屡屡失败。本指南记录了中文模板中的实际模式。

## 常见的 StyleId 模式

### 模式 A：数字 ID（在中文 Word 模板中最常见）

|风格目的|样式ID | w：名称 | w:基于 |
|--------------|---------|--------|-----------|
|正常身体| `a` | “正常” | — |
|默认段落字体| `a0` | “默认段落字体”| — |
|标题 1 (章标题) | `1` | “标题 1”| `a` |
|标题 2（节标题）| `2` | “标题 2”| `a` |
|标题 3（小节标题）| `3` | “标题 3” | `a` |
|目录 1 | `11` | “目录 1”| `a` |
|目录 2 | `21` | “目录 2”| `a` |
|目录 3 | `31` | “目录 3” | `a` |
|标题| `a3` | “标题” | `a` |
|页脚| `a4` | “页脚” | `a` |
|目录标题 | `10` | “目录标题”| `1` |

### 模式 B：英文 ID（不太常见，通常来自国际模板）
标准标题 1/标题 2/标题 3/普通 — 这些遵循西方模式。

### 模式C：混合（一些中文，一些英文）
一些模板定义带有中文名称的自定义样式：
|风格目的|样式ID | w：名称 |
|--------------|---------|--------|
| 论文标题 | `论文标提` | “论文标题” |
| 章标题 | `张标提` | “章标题”|
| 正文 | `郑文` | "正文" |

### 如何识别哪种模式```bash
# Extract all styleIds from the template
$CLI analyze --input template.docx --styles-only

# Or manually:
# unzip template.docx word/styles.xml
# Search for w:styleId= in the extracted file
```查看前几个styleId。如果您看到“1”、“2”、“3”、“a”、“a0” → 模式 A。
如果您看到“Heading1”、“Normal”→ 模式 B。

## 标准论文结构

中国大学论文遵循高度标准化的结构：```
┌─────────────────────────────────────┐
│ 封面 (Cover Page)                    │  ← Usually 1-2 pages
│   - 校名、校徽                       │
│   - 论文题目 (title)                  │
│   - 作者、导师、院系、日期             │
├─────────────────────────────────────┤
│ 学术诚信承诺书 / 独创性声明            │  ← 1 page
│   (Academic Integrity Declaration)   │
├─────────────────────────────────────┤
│ 中文摘要 (Chinese Abstract)          │  ← 1-2 pages
│   - "摘 要" heading                  │
│   - Abstract body                    │
│   - "关键词：" line                  │
├─────────────────────────────────────┤
│ 英文摘要 (English Abstract)          │  ← 1-2 pages
│   - "ABSTRACT" heading              │
│   - Abstract body                    │
│   - "Keywords:" line                 │
├─────────────────────────────────────┤
│ 目录 (Table of Contents)             │  ← 1-3 pages
│   - Often inside SDT block           │
│   - Static example entries           │
│   - TOC field code                   │
├─────────────────────────────────────┤
│ 正文 (Body)                          │  ← Main content
│   第1章 绪论                          │
│   1.1 研究背景                        │
│   1.2 研究目的和意义                   │
│   第2章 文献综述                       │
│   ...                                │
│   第N章 结论与展望                     │
├─────────────────────────────────────┤
│ 参考文献 (References)                │  ← Styled differently
├─────────────────────────────────────┤
│ 致谢 (Acknowledgments)              │  ← Optional
├─────────────────────────────────────┤
│ 附录 (Appendices)                    │  ← Optional
└─────────────────────────────────────┘
```## 识别模板中的区域边界

模板包含必须替换的示例内容。查找区域的方法如下：

### A 区（前面的内容）- 保留模板
- 开始于：第 0 段
- 结束于：第一章标题之前的段落
- 包含：封面、声明、摘要、目录
- 如何检测结尾：搜索样式为`1`（或Heading1）的第一段，其中包含“第1章”或“绪论”

### B区（正文内容）-替换为用户内容
- 开始于：第一章标题（“第 1 章...”）
- 结束于：“参考文献”标题（包括）或致谢之前的最后一个正文段落
- 如何检测：```python
  for i, el in enumerate(body_elements):
      text = get_text(el)
      style = get_style(el)
      if style in ('1', 'Heading1') and ('第1章' in text or '绪论' in text):
          zone_b_start = i
      if '参考文献' in text:
          zone_b_end = i
  ```

### Zone C (Back matter) — KEEP from template (or remove)
- Starts after: 参考文献
- Contains: 致谢, 附录, final sectPr

## Font Expectations in Chinese Thesis Templates

| Element | Font | Size (字号) | Size (pt) | w:sz |
|---------|------|------------|-----------|------|
| 论文标题 | 华文中宋 or 黑体 | 二号 or 小二 | 22pt or 18pt | 44 or 36 |
| 章标题 (H1) | 黑体 | 三号 | 16pt | 32 |
| 节标题 (H2) | 黑体 | 四号 | 14pt | 28 |
| 小节标题 (H3) | 黑体 | 小四 | 12pt | 24 |
| 正文 | 宋体 | 小四 | 12pt | 24 |
| 页眉 | 宋体 | 五号 | 10.5pt | 21 |
| 页脚/页码 | 宋体 | 五号 | 10.5pt | 21 |
| 表格内容 | 宋体 | 五号 | 10.5pt | 21 |
| 参考文献条目 | 宋体 | 五号 | 10.5pt | 21 |

## RunFonts for CJK Body Text

```xml
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"
          w:eastAsia="宋体" w:cs="Times New Roman"/>
```对于标题：```xml
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"
          w:eastAsia="黑体" w:cs="Times New Roman"/>
```重要提示：清除直接格式时，请始终保留 w:eastAsia。
删除它会导致中文文本回退到错误的字体。

## 中文模板的常见错误

1. **搜索“Heading1”** - 中文模板使用“1”，而不是“Heading1”
2. **清除所有 rFonts** — 必须保留 eastAsia 字体声明
3. **假设“第1章”是第一段** - 通常是封面/摘要/目录之后的第100+段
4. **忽略 TOC 中的 SDT 块** — TOC 包含在 SDT 中，而不仅仅是字段代码
5. **行距错误** - 中文论文通常使用固定的20pt（line="400"）或22pt（line="440"），而不是政府文件中使用的28pt
6. **缺少分节符** — 每个区域（摘要、目录、正文）通常对于不同的页眉/页脚都有自己的 sectPr

## 风格映射快速参考

当源文档使用西方 ID 而模板使用中文数字 ID 时：```json
{
  "Heading1": "1",
  "Heading2": "2",
  "Heading3": "3",
  "Heading4": "3",
  "Normal": "a",
  "BodyText": "a",
  "ListParagraph": "a",
  "Caption": "a",
  "TOC1": "11",
  "TOC2": "21",
  "TOC3": "31"
}
```当源使用中文数字 ID 而模板使用西方 ID 时 — 反转映射。