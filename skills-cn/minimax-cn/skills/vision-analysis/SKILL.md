---
名称：视觉分析
描述：>
  使用 MiniMax 视觉 MCP 工具分析、描述和提取图像信息。
  在以下情况下使用：用户共享图像文件路径或 URL（任何包含 .jpg、.jpeg、.png、
  .gif、.webp、.bmp 或 .svg 文件扩展名）或在图像附近使用以下任何单词/短语：
  “分析”、“分析”、“描述”、“解释”、“理解”、“查看”、“回顾”、
  “提取文本”，“OCR”，“其中有什么”，“其中有什么”，“阅读此图像”，“查看此图像”，
  “告诉我有关”、“解释一下”、“解释一下”，与图像、屏幕截图相关，
  图表、图表、模型、线框或照片。
  还触发：UI 模型审查、线框分析、设计批评、数据提取
  来自图表、物体检测、人/动物/活动识别。
  触发器：任何带有图像文件扩展名（jpg、jpeg、png、gif、webp、bmp、svg）的消息，
  或任何从图像、屏幕截图中分析/描述/理解/审查/提取文本的请求，
  图表、图表、照片、模型或线框图。
许可证：麻省理工学院
元数据：
  版本：“1.0”
  类别： 人工智能视觉
  来源：
    - MiniMax 代币计划 MCP（understand_image 工具）
---

# 视觉分析

使用 MiniMax 代币计划中提供的 MiniMax `MiniMax_understand_image` MCP 工具分析图像。

## 先决条件

- 具有有效“MINIMAX_API_KEY”的 MiniMax 令牌计划订阅
- 配置了 MiniMax MCP（可用“MiniMax_understand_image”工具）

### 如果未配置 MCP 工具

**步骤 1：** 代理应从以下位置获取设置指令：
**https://platform.minimaxi.com/docs/token-plan/mcp-guide**

**第2步：**检测用户的环境（OpenCode、Cursor、Claude Code等）并输出所需的确切命令。常见示例：

**OpenCode** — 添加到 `~/.config/opencode/opencode.json` 或 `package.json`：```json
{
  "mcp": {
    "MiniMax": {
      "type": "local",
      "command": ["uvx", "minimax-coding-plan-mcp", "-y"],
      "environment": {
        "MINIMAX_API_KEY": "YOUR_TOKEN_PLAN_KEY",
        "MINIMAX_API_HOST": "https://api.minimaxi.com"
      },
      "enabled": true
    }
  }
}
```**克劳德代码**：```bash
claude mcp add -s user MiniMax --env MINIMAX_API_KEY=your-key --env MINIMAX_API_HOST=https://api.minimaxi.com -- uvx minimax-coding-plan-mcp -y
```**光标** — 添加到 MCP 设置：```json
{
  "mcpServers": {
    "MiniMax": {
      "command": "uvx",
      "args": ["minimax-coding-plan-mcp"],
      "env": {
        "MINIMAX_API_KEY": "your-key",
        "MINIMAX_API_HOST": "https://api.minimaxi.com"
      }
    }
  }
}
```**步骤 3：** 配置后，告诉用户重新启动应用程序并使用 `/mcp` 进行验证。

**重要提示：** 如果用户没有 MiniMax 令牌计划订阅，请告知他们“understand_image”工具需要订阅 - 它不能与免费或其他层 API 密钥一起使用。

## 分析模式

|模式|何时使用 |即时策略|
|---|---|---|
| `描述` |一般图像理解 |求详细说明 |
| `ocr` |从屏幕截图、文档中提取文本 |要求逐字提取所有文本 |
| `ui-评论` | UI 模型、线框图、设计文件 |寻求设计评论和建议 |
| `图表数据` |图表、图形、数据可视化 |要求提取数据点和趋势 |
| `对象检测` |识别物体、人、活动 |要求列出并找到所有元素 |

## 工作流程

### 第 1 步：自动检测图像

当消息包含图像文件路径或带有扩展名的 URL 时，该技能会自动触发：
`.jpg`、`.jpeg`、`.png`、`.gif`、`.webp`、`.bmp`、`.svg`

从消息中提取图像路径。

### 步骤2：选择分析模式并调用MCP工具

使用带有特定模式提示的“MiniMax_understand_image”工具：

**描述：**```
Provide a detailed description of this image. Include: main subject, setting/background,
colors/style, any text visible, notable objects, and overall composition.
```**OCR：**```
Extract all text visible in this image verbatim. Preserve structure and formatting
(headers, lists, columns). If no text is found, say so.
```**用户界面评论：**```
You are a UI/UX design reviewer. Analyze this interface mockup or design. Provide:
(1) Strengths — what works well, (2) Issues — usability or design problems,
(3) Specific, actionable suggestions for improvement. Be constructive and detailed.
```**图表数据：**```
Extract all data from this chart or graph. List: chart title, axis labels, all
data points/series with values if readable, and a brief summary of the trend.
```**物体检测：**```
List all distinct objects, people, and activities you can identify. For each,
describe what it is and its approximate location in the image.
```### 第 3 步：展示结果

清晰返回分析。对于“描述”，请使用可读的散文。对于“ocr”，保留结构。对于“ui-review”，请使用结构化批评格式。

## 输出格式示例

对于描述模式：```
## Image Description

[Detailed description of the image contents...]
```对于ocr模式：```
## Extracted Text

[Preserved text structure from the image]
```对于 ui-review 模式：```
## UI Design Review

### Strengths
- ...

### Issues
- ...

### Suggestions
- ...
```## 注释

- 支持最大 20MB 的图像（JPEG、PNG、GIF、WebP）
- 如果 MiniMax MCP 配置了文件访问，则本地文件路径有效
- “MiniMax_understand_image”工具由“minimax-coding-plan-mcp”包提供