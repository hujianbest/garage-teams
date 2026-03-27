# UI 错误检测

## 目的

为 Chrome DevTools MCP 功能测试定义**可客观、可自动化**的 UI 错误判定标准。解决 LLM 在明显 UI 错误仍存在时仍报告「正确」的问题 —— 用客观规则替代主观判断。

## 三层检测模型

| Layer | Mechanism | Type | Blocks on |
|-------|-----------|------|-----------|
| **Layer 1** | Automated JS detection script via `evaluate_script()` | Objective, automated | Any detected error (count > 0) |
| **Layer 2** | EXPECT/REJECT format in `[devtools]` verification steps | Semi-objective, structured | Missing EXPECT element or present REJECT condition |
| **Layer 3** | Console error gate via `list_console_messages()` | Objective, automated | Error count > 0 (unless explicitly expected) |

三层在每次 UI 验证中**按序**执行。任一层失败即整次 UI 测试失败。

## 第一层：自动化错误检测脚本

在 UI 测试过程中**每个页面**通过 `evaluate_script()` 执行下列脚本。返回 `{errors, count}`。`count > 0` 为**硬失败** —— 不允许 LLM 覆盖。

```javascript
() => {
  const errors = [];

  // 1. Zero-size visible interactive elements
  document.querySelectorAll('button,input,select,textarea,a,img,[role="button"]').forEach(el => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    if (style.display !== 'none' && style.visibility !== 'hidden'
        && style.opacity !== '0' && el.offsetParent !== null
        && (rect.width === 0 || rect.height === 0)) {
      errors.push({
        type: 'ZERO_SIZE',
        element: el.tagName.toLowerCase(),
        id: el.id || null,
        text: el.textContent?.slice(0, 30) || null
      });
    }
  });

  // 2. Interactive elements outside viewport
  document.querySelectorAll('button,input,a,[role="button"],select,textarea').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (el.offsetParent !== null && rect.width > 0 && rect.height > 0
        && (rect.right < 0 || rect.bottom < 0
            || rect.left > window.innerWidth || rect.top > window.innerHeight)) {
      errors.push({
        type: 'OFF_VIEWPORT',
        element: el.tagName.toLowerCase(),
        id: el.id || null,
        text: el.textContent?.slice(0, 30) || null,
        position: { left: rect.left, top: rect.top }
      });
    }
  });

  // 3. Placeholder/error text in page content
  const bodyText = document.body.innerText;
  const badPatterns = [
    { pattern: /\bundefined\b/gi, type: 'undefined' },
    { pattern: /\[object Object\]/g, type: '[object Object]' },
    { pattern: /\bNaN\b/g, type: 'NaN' },
    { pattern: /\bnull\b/gi, type: 'null' },
    { pattern: /\bTODO\b/g, type: 'TODO' },
    { pattern: /\bFIXME\b/g, type: 'FIXME' },
    { pattern: /lorem ipsum/gi, type: 'lorem ipsum' }
  ];
  for (const { pattern, type } of badPatterns) {
    const matches = bodyText.match(pattern);
    if (matches) {
      errors.push({
        type: 'BAD_TEXT',
        text: type,
        occurrences: matches.length
      });
    }
  }

  // 4. Interactive element overlap detection
  const interactiveEls = [...document.querySelectorAll(
    'button,a,input,[role="button"],select,textarea'
  )].filter(el => el.offsetParent !== null);
  for (let i = 0; i < interactiveEls.length; i++) {
    const a = interactiveEls[i].getBoundingClientRect();
    if (a.width === 0 || a.height === 0) continue;
    for (let j = i + 1; j < interactiveEls.length; j++) {
      const b = interactiveEls[j].getBoundingClientRect();
      if (b.width === 0 || b.height === 0) continue;
      const overlap = !(a.right <= b.left || a.left >= b.right
                     || a.bottom <= b.top || a.top >= b.bottom);
      if (overlap) {
        // Calculate overlap area to filter trivial 1px overlaps
        const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        const overlapArea = overlapWidth * overlapHeight;
        const smallerArea = Math.min(a.width * a.height, b.width * b.height);
        if (overlapArea > smallerArea * 0.1) { // >10% overlap
          errors.push({
            type: 'OVERLAP',
            el1: { tag: interactiveEls[i].tagName.toLowerCase(), text: interactiveEls[i].textContent?.slice(0, 20) },
            el2: { tag: interactiveEls[j].tagName.toLowerCase(), text: interactiveEls[j].textContent?.slice(0, 20) },
            overlapPercent: Math.round(overlapArea / smallerArea * 100)
          });
        }
      }
    }
  }

  // 5. Empty containers with layout roles
  document.querySelectorAll(
    'main,[role="main"],section,article,.container,.content,[role="region"],[role="contentinfo"]'
  ).forEach(el => {
    if (el.children.length === 0 && el.textContent.trim() === ''
        && getComputedStyle(el).display !== 'none') {
      errors.push({
        type: 'EMPTY_CONTAINER',
        element: el.tagName.toLowerCase(),
        id: el.id || null,
        className: el.className || null
      });
    }
  });

  // 6. Broken images
  document.querySelectorAll('img').forEach(img => {
    if (img.offsetParent !== null && (!img.complete || img.naturalWidth === 0)) {
      errors.push({
        type: 'BROKEN_IMAGE',
        src: img.src?.slice(0, 100),
        alt: img.alt || null
      });
    }
  });

  return { errors, count: errors.length };
}
```

### 错误类型参考

| Type | Description | Severity | Common Cause |
|------|-------------|----------|--------------|
| `ZERO_SIZE` | Visible interactive element with 0 width or height | High | CSS issue, missing content, failed render |
| `OFF_VIEWPORT` | Interactive element fully outside visible area | High | Layout overflow, absolute positioning error |
| `BAD_TEXT` | Placeholder or error text visible to user | High | Unresolved template variable, unhandled error |
| `OVERLAP` | Interactive elements overlap > 10% | Medium | CSS positioning conflict, responsive breakpoint issue |
| `EMPTY_CONTAINER` | Layout container with no content | Medium | Missing data, failed component render |
| `BROKEN_IMAGE` | Image that failed to load | Medium | Wrong path, missing asset, CORS issue |

### 集成

在 Worker UI 测试流中执行：

```
1. navigate_page(url)
2. wait_for(expected_text)             ← wait for page load
3. evaluate_script(error_detector)     ← Layer 1 — HARD FAIL if count > 0
4. take_snapshot()                     ← For EXPECT/REJECT verification
5. [interactions: click, fill, etc.]
6. evaluate_script(error_detector)     ← Layer 1 again after interactions
7. list_console_messages(["error"])    ← Layer 3 — HARD FAIL if count > 0
8. Verify EXPECT/REJECT criteria      ← Layer 2
```

## 第二层：EXPECT/REJECT 验证步骤格式

### 格式

`feature-list.json` 中每条 `[devtools]` 验证步骤须为：

```
[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>
```

### 组成部分

**EXPECT** —— **必须存在**的元素、文本或状态。通过 `take_snapshot()` 输出核验。

**REJECT** —— **必须不存在**的条件。迫使 LLM 主动找错，而非只确认正向预期。

### 示例

```json
"[devtools] /login | EXPECT: form with email input (type=email), password input (type=password), submit button labeled 'Sign In' | REJECT: any input without label, submit button disabled without validation message, placeholder text 'TODO'"
```

```json
"[devtools] /dashboard | EXPECT: welcome message with user name, navigation sidebar with 5+ menu items, data table with column headers | REJECT: empty data table body, 'undefined' in welcome message, console errors, broken images"
```

```json
"[devtools] /settings | EXPECT: profile form pre-filled with current user data, save button enabled | REJECT: form fields showing 'null' or 'undefined', save button visible but zero-size, overlapping form elements"
```

### 为何 REJECT 必填

无 REJECT 时，LLM 默认行为是：
1. 检查 EXPECT
2. 全满足 → PASS

这会漏掉**存在但未主动查找**的错误。REJECT 迫使 LLM：
1. 检查 EXPECT
2. **主动查找** REJECT 条件
3. 仅当 EXPECT 满足且 REJECT 未触发时才 PASS

### 校验

`validate_features.py` 检查：
- 每条 `[devtools]` 步骤同时含 `EXPECT:` 与 `REJECT:`
- 若缺任一条子句则告警（非错误）—— 便于渐进采纳

## 第三层：控制台错误门禁

### 规则

页面交互完成后：

```
list_console_messages(types=["error"]) → count must be 0
```

**若 count > 0**：UI 测试**自动失败**。LLM 不得将控制台错误合理化接受。

### 例外机制

当某验证步骤**预期**会出现控制台错误（如测错误边界）时：

```
"[devtools] /error-test | EXPECT: error boundary fallback UI displayed | REJECT: blank page | [expect-console-error: TypeError]"
```

后缀 `[expect-console-error: <pattern>]` 允许特定错误模式。仅匹配该模式的错误可豁免；其它错误仍导致 FAIL。

### 实现逻辑

```
1. list_console_messages(types=["error"]) → collect errors
2. If verification_step contains [expect-console-error: <pattern>]:
   - Filter out errors matching <pattern>
   - Remaining errors > 0 → FAIL
3. Else:
   - Any errors > 0 → FAIL
```

## 与其它文档的关系

| Document | Relationship |
|----------|-------------|
| [test-scenario-rules.md](test-scenario-rules.md) | Rule 5 引用本文作为 UI 专用规则 |
| [architecture.md](../../using-long-task/references/architecture.md) | Chrome DevTools MCP 测试模式引用本文 |
| [testing-anti-patterns.md](../testing-anti-patterns.md) | 「跳过 Chrome DevTools 功能测试」反模式引用 EXPECT/REJECT |
