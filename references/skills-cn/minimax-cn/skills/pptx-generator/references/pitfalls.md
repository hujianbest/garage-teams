# 质量保证流程和常见陷阱

## 质量检查流程

**假设存在问题。你的工作就是找到他们。**

你的第一次渲染几乎从来都不正确。将 QA 视为 bug 搜寻，而不是确认步骤。如果您在第一次检查时发现零问题，则说明您检查得不够仔细。

### 内容质量检查```bash
python -m markitdown output.pptx
```检查是否有内容缺失、拼写错误、顺序错误。

**检查剩余的占位符文本：**```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder|this.*(page|slide).*layout"
```如果 grep 返回结果，请在声明成功之前修复它们。

### 验证循环

1. 生成幻灯片 -> 使用 `python -m markitdown output.pptx` 提取文本 -> 查看内容
2. **列出发现的问题**（如果没有发现，请更仔细地再看一遍）
3.修复问题
4. **重新验证受影响的幻灯片** - 一项修复通常会产生另一个问题
5. 重复直到完整通过没有发现新问题

**在至少完成一个修复和验证周期之前，不要宣布成功。**

### 每张幻灯片 QA（用于从头开始创建）```bash
python -m markitdown slide-XX-preview.pptx
```检查是否缺少内容、占位符文本、缺少页码标记。

---

## 要避免的常见错误

- **不要重复相同的布局** - 在幻灯片中改变列、卡片和标注
- **不要将正文居中** — 左对齐段落和列表；仅中心标题
- **不要吝惜大小对比** — 标题需要 36pt+ 才能从 14-16pt 正文中脱颖而出
- **不要默认为蓝色** — 选择反映特定主题的颜色
- **不要随机混合间距** — 选择 0.3 英寸或 0.5 英寸间隙并一致使用
- **不要设计一张幻灯片而让其余部分保持简单** - 完全承诺或保持简单
- **不要创建纯文本幻灯片** — 添加图像、图标、图表或视觉元素；避免简单的标题+项目符号
- **不要忘记文本框填充** - 将线条或形状与文本边缘对齐时，在文本框上设置“边距：0”或偏移形状以考虑填充
- **不要使用低对比度元素** - 图标和文本需要与背景形成强烈对比
- **切勿在标题下使用重音线** - 这是人工智能生成幻灯片的标志；使用空白或背景颜色代替
- **切勿将“#”与十六进制颜色一起使用** - 导致 PptxGenJS 中的文件损坏
- **永远不要在十六进制字符串中编码不透明度** - 使用“opacity”属性代替
- **切勿在 createSlide() 中使用 async/await** —compile.js 不会等待
- **切勿在 PptxGenJS 调用中重复使用选项对象** - PptxGenJS 就地改变对象

---

## 关键陷阱 — PptxGenJS

### 切勿在 createSlide() 中使用 async/await```javascript
// WRONG - compile.js won't await
async function createSlide(pres, theme) { ... }

// CORRECT
function createSlide(pres, theme) { ... }
```### 切勿将“#”与十六进制颜色一起使用```javascript
color: "FF0000"      // CORRECT
color: "#FF0000"     // CORRUPTS FILE
```### 永远不要在十六进制字符串中编码不透明度```javascript
shadow: { color: "00000020" }              // CORRUPTS FILE
shadow: { color: "000000", opacity: 0.12 } // CORRECT
```### 防止标题中的文本换行```javascript
// Use fit:'shrink' for long titles
slide.addText("Long Title Here", {
  x: 0.5, y: 2, w: 9, h: 1,
  fontSize: 48, fit: "shrink"
});
```### 切勿在调用之间重复使用选项对象```javascript
// WRONG
const shadow = { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 };
slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });
slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });

// CORRECT - factory function
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
```
