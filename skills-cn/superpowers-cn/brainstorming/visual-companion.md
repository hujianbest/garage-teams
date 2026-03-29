# 可视化伴侣指南

基于浏览器的可视化头脑风暴伴侣，用于展示线框图、示意图与选项。

## 何时使用

按**每个问题**判断，而非按整场会话。检验标准：**用户是「看到」比「读到」更利于理解吗？**

在内容**本身偏视觉**时用浏览器：

- **UI 线框图** — 线框、版式、导航结构、组件设计
- **架构图** — 系统组件、数据流、关系图
- **并排视觉对比** — 比较两种版式、两种配色、两种设计方向
- **设计精修** — 问题涉及观感、间距、视觉层次时
- **空间关系** — 状态机、流程图、以图呈现的实体关系

在内容为文字或表格时用终端：

- **需求与范围问题** — 「X 是什么意思？」「哪些功能在范围内？」
- **概念性 A/B/C 选择** — 用文字描述的不同方案之间做选择
- **权衡列表** — 利弊、对比表
- **技术决策** — API 设计、数据建模、架构路线选择
- **澄清性问题** — 答案主要是文字而非视觉偏好时

*关于* UI 的话题并不自动等于视觉问题。「你想要哪种向导？」是概念性的 — 用终端。「这几种向导版式哪个更顺眼？」是视觉性的 — 用浏览器。

## 工作原理

服务器监视目录中的 HTML 文件，并把最新的一个提供给浏览器。你写入 HTML，用户在浏览器里查看并可通过点击选择选项。选择会记录到 `.events` 文件中，你在下一轮读取。

**内容片段 vs 完整文档：** 若 HTML 文件以 `<!DOCTYPE` 或 `<html` 开头，服务器按原样提供（仅注入辅助脚本）。否则服务器会自动用你的内容包进框架模板 — 加上页头、CSS 主题、选择指示器及全部交互基础设施。**默认写内容片段。** 仅当你需要完全控制页面时才写完整文档。

## 启动会话

```bash
# Start server with persistence (mockups saved to project)
scripts/start-server.sh --project-dir /path/to/project

# Returns: {"type":"server-started","port":52341,"url":"http://localhost:52341",
#           "screen_dir":"/path/to/project/.superpowers/brainstorm/12345-1706000000"}
```

保存响应中的 `screen_dir`。请用户打开返回的 URL。

**查找连接信息：** 服务器将启动 JSON 写入 `$SCREEN_DIR/.server-info`。若你在后台启动了服务器且未捕获标准输出，读取该文件以获取 URL 与端口。使用 `--project-dir` 时，在 `<project>/.superpowers/brainstorm/` 下查找会话目录。

**说明：** 将项目根目录作为 `--project-dir` 传入，以便线稿持久保存在 `.superpowers/brainstorm/` 并在服务器重启后仍在。若不指定，文件会落到 `/tmp` 并被清理。提醒用户若尚未忽略，请将 `.superpowers/` 加入 `.gitignore`。

**按平台启动服务器：**

**Claude Code（macOS / Linux）：**
```bash
# Default mode works — the script backgrounds the server itself
scripts/start-server.sh --project-dir /path/to/project
```

**Claude Code（Windows）：**
```bash
# Windows auto-detects and uses foreground mode, which blocks the tool call.
# Use run_in_background: true on the Bash tool call so the server survives
# across conversation turns.
scripts/start-server.sh --project-dir /path/to/project
```
通过 Bash 工具调用时，设置 `run_in_background: true`。然后在下一轮读取 `$SCREEN_DIR/.server-info` 以获取 URL 与端口。

**Codex：**
```bash
# Codex reaps background processes. The script auto-detects CODEX_CI and
# switches to foreground mode. Run it normally — no extra flags needed.
scripts/start-server.sh --project-dir /path/to/project
```

**Gemini CLI：**
```bash
# Use --foreground and set is_background: true on your shell tool call
# so the process survives across turns
scripts/start-server.sh --project-dir /path/to/project --foreground
```

**其他环境：** 服务器必须在多轮对话之间保持后台运行。若环境会回收已分离进程，请使用 `--foreground`，并用你平台上的后台执行机制启动命令。

若从你的浏览器无法访问该 URL（远程/容器环境常见），绑定非 loopback 地址：

```bash
scripts/start-server.sh \
  --project-dir /path/to/project \
  --host 0.0.0.0 \
  --url-host localhost
```

使用 `--url-host` 控制返回 URL JSON 中打印的主机名。

## 循环

1. **确认服务器仍在运行**，然后在 `screen_dir` 中**写入新的 HTML 文件**：
   - 每次写入前确认 `$SCREEN_DIR/.server-info` 存在。若不存在（或存在 `.server-stopped`），说明服务器已退出 — 先用 `start-server.sh` 重启再继续。服务器在无活动约 30 分钟后会自动退出。
   - 使用语义化文件名：`platform.html`、`visual-style.html`、`layout.html`
   - **永远不要复用文件名** — 每个画面使用新文件
   - 使用 Write 工具 — **不要用 cat/heredoc**（会在终端产生噪音）
   - 服务器自动提供最新修改的文件

2. **告知用户预期并结束本轮：**
   - 每次都要提醒 URL（不仅是第一次）
   - 用简短文字概括屏幕上内容（例如：「展示首页的 3 种版式选项」）
   - 请用户在终端回复：「请看一下并告诉我你的想法。若想选好某一项可以点击选择。」

3. **下一轮** — 用户在终端回复之后：
   - 若存在则读取 `$SCREEN_DIR/.events` — 其中为用户在浏览器中的交互（点击、选择），JSON 行格式
   - 与用户在终端中的文字合并，形成完整反馈
   - 终端消息是主要反馈；`.events` 提供结构化交互数据

4. **迭代或推进** — 若反馈会改变当前画面，写入新文件（例如 `layout-v2.html`）。仅当当前步骤已确认后，再进入下一问题。

5. **回到终端时卸载画面** — 若下一步不需要浏览器（例如澄清问题、权衡讨论），推送等待页以清除过时内容：

   ```html
   <!-- filename: waiting.html (or waiting-2.html, etc.) -->
   <div style="display:flex;align-items:center;justify-content:center;min-height:60vh">
     <p class="subtitle">Continuing in terminal...</p>
   </div>
   ```

   这样用户不会盯着已做完的选择，而对话已进入下一阶段。下一个视觉问题出现时，照常推送新的内容文件。

6. 重复直至结束。

## 编写内容片段

只写放进页面里的内容。服务器会自动用框架模板包裹（页头、主题 CSS、选择指示器及全部交互基础设施）。

**最小示例：**

```html
<h2>Which layout works better?</h2>
<p class="subtitle">Consider readability and visual hierarchy</p>

<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>Single Column</h3>
      <p>Clean, focused reading experience</p>
    </div>
  </div>
  <div class="option" data-choice="b" onclick="toggleSelect(this)">
    <div class="letter">B</div>
    <div class="content">
      <h3>Two Column</h3>
      <p>Sidebar navigation with main content</p>
    </div>
  </div>
</div>
```

到此即可。不需要 `<html>`、不需要手写 CSS、不需要 `<script>` 标签。服务器会提供这些。

## 可用 CSS 类

框架模板为你的内容提供以下 CSS 类：

### 选项（A/B/C 选择）

```html
<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>Title</h3>
      <p>Description</p>
    </div>
  </div>
</div>
```

**多选：** 在容器上添加 `data-multiselect`，用户可多选。每次点击切换选中状态。指示条显示已选数量。

```html
<div class="options" data-multiselect>
  <!-- same option markup — users can select/deselect multiple -->
</div>
```

### 卡片（视觉设计）

```html
<div class="cards">
  <div class="card" data-choice="design1" onclick="toggleSelect(this)">
    <div class="card-image"><!-- mockup content --></div>
    <div class="card-body">
      <h3>Name</h3>
      <p>Description</p>
    </div>
  </div>
</div>
```

### 线框容器

```html
<div class="mockup">
  <div class="mockup-header">Preview: Dashboard Layout</div>
  <div class="mockup-body"><!-- your mockup HTML --></div>
</div>
```

### 分栏（并排）

```html
<div class="split">
  <div class="mockup"><!-- left --></div>
  <div class="mockup"><!-- right --></div>
</div>
```

### 利弊

```html
<div class="pros-cons">
  <div class="pros"><h4>Pros</h4><ul><li>Benefit</li></ul></div>
  <div class="cons"><h4>Cons</h4><ul><li>Drawback</li></ul></div>
</div>
```

### 线框元素（线框搭建块）

```html
<div class="mock-nav">Logo | Home | About | Contact</div>
<div style="display: flex;">
  <div class="mock-sidebar">Navigation</div>
  <div class="mock-content">Main content area</div>
</div>
<button class="mock-button">Action Button</button>
<input class="mock-input" placeholder="Input field">
<div class="placeholder">Placeholder area</div>
```

### 排版与区块

- `h2` — 页面标题
- `h3` — 小节标题
- `.subtitle` — 标题下的次要文字
- `.section` — 带底部间距的内容块
- `.label` — 小号大写标签文字

## 浏览器事件格式

用户在浏览器中点击选项时，交互会写入 `$SCREEN_DIR/.events`（每行一个 JSON 对象）。当你推送新画面时，该文件会自动清空。

```jsonl
{"type":"click","choice":"a","text":"Option A - Simple Layout","timestamp":1706000101}
{"type":"click","choice":"c","text":"Option C - Complex Grid","timestamp":1706000108}
{"type":"click","choice":"b","text":"Option B - Hybrid","timestamp":1706000115}
```

完整事件流展示用户的探索路径 — 在定案前可能点击多个选项。通常最后一个 `choice` 事件是最终选择，但点击模式也可能体现犹豫或值得追问的偏好。

若不存在 `.events`，说明用户未在浏览器中交互 — 仅使用其终端文字即可。

## 设计建议

- **保真度与问题匹配** — 版式用线框，精修问题用更高完成度
- **每页说明在问什么** — 「哪种版式更专业？」而不只是「选一个」
- **推进前先迭代** — 若反馈会改变当前画面，写新版本
- **每屏最多 2–4 个选项**
- **在重要时用真实内容** — 例如摄影作品集用真实图片（Unsplash）。占位内容会掩盖设计问题。
- **线框保持简单** — 聚焦版式与结构，而非像素级设计

## 文件命名

- 使用语义化名称：`platform.html`、`visual-style.html`、`layout.html`
- 不要复用文件名 — 每个画面必须是新文件
- 迭代时加版本后缀，如 `layout-v2.html`、`layout-v3.html`
- 服务器按修改时间提供最新文件

## 清理

```bash
scripts/stop-server.sh $SCREEN_DIR
```

若会话使用了 `--project-dir`，线稿文件会保留在 `.superpowers/brainstorm/` 供日后参考。仅使用 `/tmp` 的会话在停止时会被删除。

## 参考

- 框架模板（CSS 参考）：`scripts/frame-template.html`
- 辅助脚本（客户端）：`scripts/helper.js`
