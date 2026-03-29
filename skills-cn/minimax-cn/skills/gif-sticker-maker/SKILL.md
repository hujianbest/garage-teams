---
名称： gif 贴纸制作器
描述：|
  将照片（人物、宠物、物体、徽标）转换为 4 个带标题的动画 GIF 贴纸。
  使用场合：用户想要创建卡通贴纸、GIF 表情、表情包、动画头像、
  或将照片转换为 Funko Pop / Pop Mart 盲盒风格动画。
  触发点：贴纸、GIF、卡通、表情符号、表情包、头像动画。
许可证：麻省理工学院
元数据：
  版本：“1.2”
  类别： 创意工具
  风格: Funko Pop / Pop Mart
  输出格式：GIF
  输出计数：4
  来源：
    - MiniMax 图像生成 API
    - MiniMax 视频生成 API
---

# GIF 贴纸制作器

将用户照片转换为 4 个动画 GIF 贴纸（Funko Pop / Pop Mart 风格）。

## 款式规格

- Funko Pop / Pop Mart 盲盒 3D 公仔
- C4D / Octane 渲染质量
- 白色背景，柔和的工作室灯光
- 标题：黑色文本+白色轮廓，图像底部

## 先决条件

在开始任何生成步骤之前，请确保：

1. **Python venv** 已激活，并安装了 [requirements.txt](references/requirements.txt) 中的依赖项
2. **`MINIMAX_API_KEY`** 被导出（例如 `export MINIMAX_API_KEY='your-key'`）
3. **`ffmpeg`** 在 PATH 上可用（用于步骤 3 GIF 转换）

如果缺少任何先决条件，请先进行设置。如果没有全部三个，请勿继续生成。

## 工作流程

### 第 0 步：收集字幕

询问用户（用他们的语言）：
>“您想自定义贴纸的标题，还是使用默认值？”

- **自定义**：收集 4 个简短的标题（1-3 个单词）。操作自动匹配标题含义。
- **默认**：通过**检测到的用户语言**查找[字幕表](references/captions.md)。 **切勿混合语言。**

### 第 1 步：生成 4 个静态贴纸图像

**工具**：`scripts/minimax_image.py`

1. 分析用户的照片——识别主题类型（人/动物/物体/标志）。
2. 对于 4 个贴纸中的每一个，通过填充“{action}”和“{caption}”从 [image-prompt-template.txt](assets/image-prompt-template.txt) 构建提示。
3. **如果主体是人**：传递 `--subject-ref <user_photo_path>`，以便生成的雕像保留人的实际面部相似度。
4. 生成（所有 4 个都是独立的 — **同时运行**）：```bash
python3 scripts/minimax_image.py "<prompt>" -o output/sticker_hi.png --ratio 1:1 --subject-ref <photo>
python3 scripts/minimax_image.py "<prompt>" -o output/sticker_laugh.png --ratio 1:1 --subject-ref <photo>
python3 scripts/minimax_image.py "<prompt>" -o output/sticker_cry.png --ratio 1:1 --subject-ref <photo>
python3 scripts/minimax_image.py "<prompt>" -o output/sticker_love.png --ratio 1:1 --subject-ref <photo>
```> `--subject-ref` 仅适用于人物主题（API 限制：type=character）。
> 对于动物/物体/徽标，省略标志并依赖文本描述。

### 第 2 步：为每个图像制作动画 → 视频

**工具**：带有“--image”标志的“scripts/minimax_video.py”（图像到视频模式）

对于每个贴纸图像，从 [video-prompt-template.txt](assets/video-prompt-template.txt) 构建提示，然后：```bash
python3 scripts/minimax_video.py "<prompt>" --image output/sticker_hi.png -o output/sticker_hi.mp4
python3 scripts/minimax_video.py "<prompt>" --image output/sticker_laugh.png -o output/sticker_laugh.mp4
python3 scripts/minimax_video.py "<prompt>" --image output/sticker_cry.png -o output/sticker_cry.mp4
python3 scripts/minimax_video.py "<prompt>" --image output/sticker_love.png -o output/sticker_love.mp4
```所有 4 个调用都是独立的 — **同时运行**。

### 步骤 3：转换视频 → GIF

**工具**：`scripts/convert_mp4_to_gif.py````bash
python3 scripts/convert_mp4_to_gif.py output/sticker_hi.mp4 output/sticker_laugh.mp4 output/sticker_cry.mp4 output/sticker_love.mp4
```与每个 MP4 一起输出 GIF 文件（例如 `sticker_hi.gif`）。

### 第 4 步：交付

输出格式（严格顺序）：
1. 简短的状态行（例如“已创建 4 个贴纸：”）
2. `<deliver_assets>` 块包含所有 GIF 文件
3. **deliver_assets 之后没有文字**```xml
<deliver_assets>
<item><path>output/sticker_hi.gif</path></item>
<item><path>output/sticker_laugh.gif</path></item>
<item><path>output/sticker_cry.gif</path></item>
<item><path>output/sticker_love.gif</path></item>
</deliver_assets>
```## 默认操作

| ＃|行动|文件名 ID |动画|
|---|--------|-------------|------------|
| 1 |快乐挥手|你好|挥手，轻微倾斜头部|
| 2 |笑得很厉害|笑 |笑得浑身发抖，眼睛眯起来|
| 3 |泪流满面|哭|泪流满面，身体颤抖|
| 4 |心形手势|爱|手心里有心，眼睛里闪闪发光|

请参阅 [references/captions.md](references/captions.md) 了解多语言字幕默认值。

## 规则

- 检测用户的语言，所有输出都遵循它
- 字幕必须来自与用户语言列匹配的 [captions.md](references/captions.md) — 切勿混合语言
- 无论用户语言如何，所有图像提示都必须为**英语**（仅本地化标题文本）
- `<deliver_assets>` 必须是最后的响应，之后没有文本