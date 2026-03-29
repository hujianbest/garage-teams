---
名称：minimax-multimodal-toolkit
描述：>
  MiniMax 多模态模型技能 — 使用 MiniMax 多模态模型处理语音、音乐、视频和图像。
  使用 MiniMax AI 创建语音、音乐、视频和图像：TTS（文本转语音、语音克隆、语音设计、
  多段）、音乐（歌曲、乐器）、视频（文本到视频、图像到视频、开始结束帧、
  主题参考、模板、长格式多场景）、图像（文本到图像、带字符的图像到图像）
  参考）和媒体处理（转换、连接、修剪、提取）。
  当用户提到 MiniMax、多模态生成，或者想要语音/音乐/视频/图像 AI 时使用，
  MiniMax API 或 FFmpeg 工作流程以及 MiniMax 输出。
许可证：麻省理工学院
元数据：
  版本：“1.0”
  类别：媒体生成
---

# MiniMax 多模态工具包

通过 MiniMax API 生成语音、音乐、视频和图像内容 — **MiniMax 多模式**用例（音频 + 音乐 + 视频 + 图像）的统一入口。包括用于自定义语音的语音克隆和语音设计、带有字符参考的图像生成，以及用于音频/视频格式转换、连接、修剪和提取的基于 FFmpeg 的媒体工具。

## 输出目录

**所有生成的文件必须保存到代理当前工作目录（而不是技能目录）下的“minimax-output/”。**每个脚本调用必须包含指向此位置的显式“--output”/“-o”参数。切勿省略输出参数或依赖脚本默认值。

**规则：**
1. 在运行任何脚本之前，请确保代理的工作目录中存在“minimax-output/”（如果需要，请创建：“mkdir -p minimax-output”）
2. 始终使用代理工作目录中的绝对或相对路径：`--output minimax-output/video.mp4`
3. **切勿** `cd` 进入技能目录来运行脚本 — 使用完整脚本路径从代理的工作目录运行
4. 中间/临时文件（音频片段、视频片段、提取的帧）自动放置在“minimax-output/tmp/”中。当不再需要时可以清理它们：`rm -rf minimax-output/tmp`

## 先决条件```bash
brew install ffmpeg jq              # macOS (or apt install ffmpeg jq on Linux)
bash scripts/check_environment.sh
```不需要 Python 或 pip — 所有脚本都是使用“curl”、“ffmpeg”、“jq”和“xxd”的纯 bash。

### API 主机配置

MiniMax为不同区域提供了两个服务端点。在运行任何脚本之前设置“MINIMAX_API_HOST”：

|地区 |平台网址 | API 主机价值 |
|--------|-------------|----------------|
|中国大陆（中国大陆） | https://platform.minimaxi.com | `https://api.minimaxi.com` |
|全球（全球） | https://platform.minimax.io | `https://api.minimax.io` |```bash
# China Mainland
export MINIMAX_API_HOST="https://api.minimaxi.com"

# or Global
export MINIMAX_API_HOST="https://api.minimax.io"
```**重要 — 当 API 主机丢失时：**
在运行任何脚本之前，请检查环境中是否设置了“MINIMAX_API_HOST”。如果没有配置：
1. 询问用户他们的 MiniMax 帐户使用哪个服务端点：
   - **中国大陆** → `https://api.minimaxi.com`
   - **全球** → `https://api.minimax.io`
2. 指导并帮助用户通过终端中的 `export MINIMAX_API_HOST="https://api.minimaxi.com"` （或全局变体）进行设置，或将其添加到 shell 配置文件 (`~/.zshrc` / `~/.bashrc`) 中以实现持久性

### API 密钥配置

在运行任何脚本之前设置“MINIMAX_API_KEY”环境变量：```bash
export MINIMAX_API_KEY="your-api-key-here"
```密钥以“sk-api-”或“sk-cp-”开头，可从 https://platform.minimaxi.com（中国）或 https://platform.minimax.io（全球）获取

**重要 — 当 API 密钥丢失时：**
在运行任何脚本之前，请检查环境中是否设置了“MINIMAX_API_KEY”。如果没有配置：
1. 要求用户提供 MiniMax API 密钥
2. 指导并帮助用户在终端中通过 `export MINIMAX_API_KEY="sk-..."` 进行设置，或将其添加到 shell 配置文件 (`~/.zshrc` / `~/.bashrc`) 中以实现持久性

## 计划限制和配额

**重要 — 在生成内容之前始终尊重用户的计划限制。** 如果用户的配额已用完或不足，请在继续之前警告他们。

### 标准计划

|能力|入门 |加|最大|
|---|---|---|---|
| M2.7（聊天）| 600 请求/5 小时 | 1,500 请求/5 小时 | 4,500 请求/5 小时 |
|语音2.8 | — | 4,000 个字符/天 | 11,000 个字符/天 |
|图像-01 | — | 50 张图像/天 | 120 张图像/天 |
|海螺-2.3-快768P 6s | — | — |每天 2 个视频 |
|海螺-2.3 768P 6s | — | — |每天 2 个视频 |
|音乐2.5 | — | — |每天 4 首歌曲（每首≤5 分钟）|

### 高速计划

|能力|加-HS |最大-HS |超HS |
|---|---|---|---|
| M2.7-高速（聊天）| 1,500 请求/5 小时 | 4,500 请求/5 小时 | 30,000 请求/5 小时 |
|语音2.8 | 9,000 个字符/天 | 19,000 个字符/天 | 50,000 个字符/天 |
|图像-01 | 100 张图像/天 | 200 张图像/天 | 800 张图像/天 |
|海螺-2.3-快768P 6s | — |每天 3 个视频 |每天 5 个视频 |
|海螺-2.3 768P 6s | — |每天 3 个视频 |每天 5 个视频 |
|音乐2.5 | — |每天 7 首歌曲（每首≤5 分钟）|每天 15 首歌曲（每首≤5 分钟）|

**主要配额限制：**
- **视频分辨率：仅限 768P** — 任何套餐均不提供 1080P
- **视频时长：6秒** — 所有计划配额均以 6 秒为单位计算
- **视频配额非常有限**（2-5/天，具体取决于计划）- 在生成视频之前始终与用户确认

## 关键能力

|能力|描述 |切入点|
|------------|-------------|-------------|
|语音合成 |具有多种声音和情感的文本到语音合成 | `脚本/tts/generate_voice.sh` |
|语音克隆 |从音频样本中克隆声音（10 秒至 5 分钟）| `scripts/tts/generate_voice.sh 克隆` |
|语音设计|根据文本描述创建自定义语音 | `scripts/tts/generate_voice.sh 设计` |
|音乐一代|生成带有歌词或器乐曲目的歌曲 | `脚本/音乐/generate_music.sh` |
|图像生成|带有字符参考的文本到图像、图像到图像 | `脚本/图像/generate_image.sh` |
|视频生成|文本到视频、图像到视频、主题参考、模板 | `脚本/视频/generate_video.sh` |
|长视频 |具有淡入淡出过渡的多场景链接视频 | `脚本/视频/generate_long_video.sh` |
|媒体工具|音视频格式转换、拼接、修剪、提取 | `scripts/media_tools.sh` |

## TTS（文本转语音）

入口点：`scripts/tts/generate_voice.sh`

### 重要提示：单一语音与多分段 — 选择正确的方法

|用户意图 |方法|
|----------|----------|
|单语音/无需多角色| `tts` 命令 — 在一次调用中生成整个文本 |
|多个角色/旁白+对话 |带有segments.json的`generate`命令 |

**默认行为：** 当用户只是要求生成语音/语音且未提及多个语音或字符时，请直接使用“tts”命令和单个适当的语音。不要拆分成段或使用多段管道 - 只需在一次调用中将全文传递到“tts”即可。

仅在以下情况下使用多段“生成”：
- 用户明确需要多个声音/角色
- 文字需要旁白+人物对话分离
- 文本超过 **10,000 个字符**（每个请求的 API 限制）— 在这种情况下，将分成具有相同语音的片段

### 单语音生成（默认）```bash
bash scripts/tts/generate_voice.sh tts "Hello world" -o minimax-output/hello.mp3
bash scripts/tts/generate_voice.sh tts "你好世界" -v female-shaonv -o minimax-output/hello_cn.mp3
```### 多片段生成（多语音/有声读物/播客）

**完整的工作流程 - 按顺序执行所有步骤：**

1. **编写segments.json** - 将文本分割成带有语音分配的片段（请参阅下面的格式和规则）
2. **运行“generate”命令** — 这会读取segment.json，通过TTS API为每个片段生成音频，然后使用交叉淡入淡出将它们合并到单个输出文件中```bash
# Step 1: Write segments.json to minimax-output/
# (use the Write tool to create minimax-output/segments.json)

# Step 2: Generate audio from segments.json — this is the CRITICAL step
# It generates each segment individually and merges them into one file
bash scripts/tts/generate_voice.sh generate minimax-output/segments.json \
  -o minimax-output/output.mp3 --crossfade 200
```**不要跳过第 2 步。** 单独编写 snippets.json 不会执行任何操作 - 您必须运行“generate”命令才能实际生成音频。

### 语音管理```bash
# List all available voices
bash scripts/tts/generate_voice.sh list-voices

# Voice cloning (from audio sample, 10s–5min)
bash scripts/tts/generate_voice.sh clone sample.mp3 --voice-id my-voice

# Voice design (from text description)
bash scripts/tts/generate_voice.sh design "A warm female narrator voice" --voice-id narrator
```### 音频处理```bash
bash scripts/tts/generate_voice.sh merge part1.mp3 part2.mp3 -o minimax-output/combined.mp3
bash scripts/tts/generate_voice.sh convert input.wav -o minimax-output/output.mp3
```### TTS 模型

|型号|笔记|
|--------|--------|
|语音2.8高清|推荐，自动情感匹配 |
|语音2.8-turbo |更快的变体|
|语音2.6高清|上一代，手动情感|
|语音2.6-turbo |上一代，速度更快 |

### snippets.json 格式

段之间的默认交叉淡入淡出：**200ms**（`--crossfade 200`）。```json
[
  { "text": "Hello!", "voice_id": "female-shaonv", "emotion": "" },
  { "text": "Welcome.", "voice_id": "male-qn-qingse", "emotion": "happy" }
]
```对于语音 2.8 模型，将 `emotion` 留空（从文本自动匹配）。

### 重要提示：多片段脚本生成规则（有声读物、播客等）

为有声读物、播客或任何多角色旁白生成 paragraphs.json 时，您必须将旁白文本从角色对话拆分为具有不同声音的单独片段。

**规则：旁白和对话始终是独立的部分。**

像“汤姆说：今天天气真好！”这样的句子必须分为两段：
- 第 1 段（旁白声音）：“汤姆说：”
- 第 2 段（角色声音）：“今天天气真好！”

**示例 — 带叙述者 + 2 个字符的有声读物：**```json
[
  { "text": "Morning sunlight streamed into the classroom as students filed in one by one.", "voice_id": "narrator-voice", "emotion": "" },
  { "text": "Tom smiled and turned to Lisa:", "voice_id": "narrator-voice", "emotion": "" },
  { "text": "The weather is amazing today! Let's go to the park after school!", "voice_id": "tom-voice", "emotion": "happy" },
  { "text": "Lisa thought for a moment, then replied:", "voice_id": "narrator-voice", "emotion": "" },
  { "text": "Sure, but I need to drop off my backpack at home first.", "voice_id": "lisa-voice", "emotion": "" },
  { "text": "They exchanged a smile and went back to listening to the lecture.", "voice_id": "narrator-voice", "emotion": "" }
]
```**关键原则：**
1. **旁白**自始至终使用一致的中性旁白声音
2. **每个角色**都有一个专用的 voice_id，在所有对话中保持一致
3. **在对话边界处分割** — “他说：”是叙述者，引用的内容是人物
4. **不要将**叙述者文本和角色语音合并为一个片段
5. 对于没有预先存在voice_id的角色，请先使用语音克隆或语音设计来创建它们，然后在分段中引用创建的voice_id

## 音乐一代

入口点：`scripts/music/generate_music.sh`

### 重要提示：器乐与歌词 — 何时使用哪个

|场景|模式|行动|
|----------|------|--------|
|视频/语音/播客的 BGM |器乐（默认）|直接使用 `--instrumental`，不要询问用户 |
|用户明确要求“创作音乐”/“制作歌曲” |先询问用户 |询问他们想要器乐还是歌词 |

**向视频或语音内容添加背景音乐时**，始终默认为乐器模式（`--instrumental`）。不要询问用户 - BGM 绝对不应该让声音与主要内容竞争。

**当用户明确要求将创建/生成音乐作为主要任务**时，询问他们是否想要：
- 器乐（纯音乐，无人声）
- 带歌词（带人声的歌曲 - 用户提供或您帮助写歌词）```bash
# Instrumental (for BGM or when user chooses instrumental)
bash scripts/music/generate_music.sh \
  --instrumental \
  --prompt "ambient electronic, atmospheric" \
  --output minimax-output/ambient.mp3 --download

# Song with lyrics (when user chooses vocal music)
bash scripts/music/generate_music.sh \
  --lyrics "[verse]\nHello world\n[chorus]\nLa la la" \
  --prompt "indie folk, melancholic" \
  --output minimax-output/song.mp3 --download

# With style fields
bash scripts/music/generate_music.sh \
  --lyrics "[verse]\nLyrics here" \
  --genre "pop" --mood "upbeat" --tempo "fast" \
  --output minimax-output/pop_track.mp3 --download
```### 音乐模型

默认模型：`music-2.5`

`music-2.5` 不直接支持 `--instrumental`。当需要器乐时，脚本会自动应用一种解决方法：
- 将歌词设置为“[intro] [outro]”（空结构标签，没有实际的人声），在提示中附加“纯音乐，无歌词”

这会产生乐器风格的输出，无需手动干预。您始终可以使用“--instrumental”，脚本会处理其余的事情。

## 图像生成

入口点：`scripts/image/generate_image.sh`

模型：`image-01` — 根据文本提示生成逼真的图像，并具有图像到图像的可选字符参考。

### 重要提示：模式选择 — t2i 与 i2i

|用户意图 |模式|
|----------|------|
|从文本描述生成图像（默认）| `t2i` — 文本到图像 |
|使用角色参考照片生成图像（保留同一个人）| `i2i` — 图像到图像 |

**默认行为：** 当用户要求生成/创建图像而不提及参考照片时，使用“t2i”模式（默认）。仅当用户提供角色参考图像或明确要求将图像基于现有人物的外观时，才使用“i2i”模式。

### 重要提示：宽高比 — 从用户上下文推断

不要总是默认为“1:1”。分析用户的请求，选择最合适的长宽比：

|用户意图/上下文|推荐比例|分辨率|
|------------------------|--------------------|------------|
| 头像、图标、社交媒体头像、头像、图标、个人资料图片 | `1:1` | 1024×1024 |
| 风景、横幅、桌面壁纸、风景、横幅、桌面壁纸 | `16:9` | 1280×720 |
| 传统照片、经典比例、经典照片 | `4:3` | 1152×864 |
| 摄影作品、杂志封面、摄影、杂志 | `3:2` | 1248×832 |
| 人物竖图、海报、肖像照、海报 | `2:3` | 832×1248 |
| 竖版海报、书籍封面、大海报、书籍封面 | `3:4` | 864×1152 |
| 手机壁纸、社交媒体故事、手机壁纸、故事、卷轴 | `9:16` | 720×1280 |
| 超宽全景、电影幅图、全景、电影超宽 | `21:9` | 1344×576 | 1344×576
| 未指定特定需求 / 不明确 | `1:1` | 1024×1024 |

### 重要提示：图像计数 — 何时生成多个图像

|用户意图 |计数 (`-n`) |
|-------------|--------------|
|默认/单图像请求 | `1`（默认）|
| 用户说“几张”、“多张”、“一些” / “几个”、“几个” | `3` |
| 用户说“多种方案”、“创业” / “变体”、“选项” | `3`–`4` |
| 用户明确指定数量 |使用指定的数字 (1–9) |

### 文本到图像示例```bash
# Basic text-to-image
bash scripts/image/generate_image.sh \
  --prompt "A cat sitting on a rooftop at sunset, cinematic lighting, warm tones, photorealistic" \
  -o minimax-output/cat.png

# Landscape with inferred aspect ratio
bash scripts/image/generate_image.sh \
  --prompt "Mountain landscape with misty valleys, photorealistic, golden hour" \
  --aspect-ratio 16:9 \
  -o minimax-output/landscape.png

# Phone wallpaper (portrait 9:16)
bash scripts/image/generate_image.sh \
  --prompt "Aurora borealis over a snowy forest, vivid colors, magical atmosphere" \
  --aspect-ratio 9:16 \
  -o minimax-output/wallpaper.png

# Multiple variations
bash scripts/image/generate_image.sh \
  --prompt "Abstract geometric art, vibrant colors" \
  -n 3 \
  -o minimax-output/art.png

# With prompt optimizer
bash scripts/image/generate_image.sh \
  --prompt "A man standing on Venice Beach, 90s documentary style" \
  --aspect-ratio 16:9 --prompt-optimizer \
  -o minimax-output/beach.png

# Custom dimensions (must be multiple of 8)
bash scripts/image/generate_image.sh \
  --prompt "Product photo of a luxury watch on marble surface" \
  --width 1024 --height 768 \
  -o minimax-output/watch.png
```### 图像到图像（字符参考）

使用参考照片在新场景中生成具有相同角色的图像。单张正面肖像的最佳效果。支持的格式：JPG、JPEG、PNG（最大 10MB）。```bash
# Character reference — place same person in a new scene
bash scripts/image/generate_image.sh \
  --mode i2i \
  --prompt "A girl looking into the distance from a library window, warm afternoon light" \
  --ref-image face.jpg \
  --aspect-ratio 16:9 \
  -o minimax-output/girl_library.png

# Multiple character variations
bash scripts/image/generate_image.sh \
  --mode i2i \
  --prompt "A woman in a red dress at a gala event, elegant, cinematic" \
  --ref-image face.jpg -n 3 \
  -o minimax-output/gala.png
```### 宽高比参考

|比率|分辨率|最适合 |
|--------|------------|----------|
| `1:1` | 1024×1024 |默认、头像、图标、社交媒体 |
| `16:9` | 1280×720 |风景，横幅，桌面壁纸|
| `4:3` | 1152×864 |经典照片、演示|
| `3:2` | 1248×832 |摄影、杂志排版|
| `2:3` | 832×1248 |肖像照片、海报|
| `3:4` | 864×1152 |书籍封面、高海报|
| `9:16` | 720×1280 |手机壁纸、社会故事/卷轴|
| `21:9` | 1344×576 | 1344×576超宽全景、电影 |

### 关键选项

|选项 |描述 |
|--------|-------------|
| `--提示文本` |图片描述，最多 1500 个字符（必填）|
| `--纵横比 RATIO` |长宽比（见上表）。从用户上下文推断 |
| `--宽度 PX` / `--高度 PX` |自定义尺寸，512–2048，必须是 8 的倍数，两者都需要一起。如果两者均设置，则被 `--aspect-ratio` 覆盖 |
| `-n N` |要生成的图像数量，1–9（默认 1）|
| `--种子 N` |用于再现性的随机种子。相同的种子 + 相同的参数 → 相似的结果 |
| `--提示优化器` |通过API启用自动提示优化 |
| `--ref-image 文件` | i2i 模式的角色参考图像（本地文件或 URL，JPG/JPEG/PNG，最大 10MB）|
| `--无下载` |打印图像 URL 而不是下载文件 |
| `--aigc-水印` |为生成的图像添加 AIGC 水印 |

## 视频生成

### 重要提示：单段与多段 — 选择正确的脚本

|用户意图 |使用脚本 |
|------------|----------------|
|默认/无特殊要求 | `scripts/video/generate_video.sh`（单段，**6s，768P**）|
|用户明确要求“长视频”、“多场景”、“故事”或时长 > 10 秒 | `scripts/video/generate_long_video.sh`（多段）|

**默认行为：** 始终使用单段 `generate_video.sh`，**时长 6 秒，分辨率 768P**，除非用户明确要求长视频或多场景视频。不要自动分割成多个片段 - 单个 6 秒视频是标准输出。仅当用户明确需要多场景或更长的内容时才使用“generate_long_video.sh”。

入口点（单个视频）：`scripts/video/generate_video.sh`
入口点（长/多场景）：`scripts/video/generate_long_video.sh`

### 视频模型约束（必须遵循）

**各型号支持的分辨率和持续时间：**

|型号|分辨率|持续时间 |
|--------|------------|----------|
| MiniMax-Hailuo-2.3 |仅限 768P | 6 秒或 10 秒 |
| MiniMax-Hailuo-2.3-快速 |仅限 768P | 6 秒或 10 秒 |
| MiniMax-Hailuo-02 | 512P、768P（默认）| 6 秒或 10 秒 |
| T2V-01 / T2V-01-导演 | 720P |仅 6 秒 |
| I2V-01 / I2V-01-导演 / I2V-01-现场 | 720P |仅 6 秒 |
| S2V-01（参考）| 720P |仅 6 秒 |

**关键规则：**
- **默认：6s + 768P** — 计划配额以 6 秒为单位计算；除非用户明确请求 10 秒，否则使用 6 秒
- **任何套餐均不支持 1080P** — Hailuo-2.3/2.3-Fast 始终使用 768P
- 旧型号（T2V-01、I2V-01、S2V-01）仅支持 720P 6 秒

### 重要提示：提示优化（在生成任何视频之前必须遵循）

在调用任何视频生成脚本之前，您必须通过阅读并应用“references/video-prompt-guide.md”来优化用户提示。切勿将用户的原始描述直接作为“--prompt”传递。

**优化步骤：**

1. **应用专业公式**：`主体+场景+运动+镜头运动+审美氛围`
   - 坏：“公园里的小狗”
   - 好：“一只金毛小狗在公园里阳光斑驳的草地小路上跑向镜头，[附近]流畅的跟踪镜头，温暖的黄金时刻灯光，浅景深，欢乐的气氛”`

2. **添加相机指令**使用`[指令]`语法：`[推进]`、`[拉远]`、`[紧随]`、`[固定]`、`[左摇]`等。

3. **包括美学细节**：灯光（黄金时刻、戏剧性的侧光）、颜色分级（暖色调、电影）、纹理（灰尘颗粒、雨滴）、氛围（亲密、史诗、和平）

4. **在 6-10 秒的视频中保留 1-2 个关键操作** — 不要让事件过多

5. **对于 i2v 模式**（图像到视频）：将提示聚焦于**仅移动和更改**，因为图像已经建立了视觉效果。不要重新描述图像中的内容。
   - 不好：“有山的湖”（只是重复图像）
   - 好：“水面泛起轻柔的涟漪，微风吹过远处的树木沙沙作响，[固定]固定的相机，柔和的晨光，平和而宁静”`6. **对于多段长视频**：每个段的提示必须是独立的并单独优化。 i2v 片段（片段 2+）应描述相对于前一个片段的结束帧的运动/变化。```bash
# Text-to-video (default: 6s, 768P)
bash scripts/video/generate_video.sh \
  --mode t2v \
  --prompt "A golden retriever puppy bounds toward the camera on a sunlit grass path, [跟随] tracking shot, warm golden hour, shallow depth of field, joyful" \
  --output minimax-output/puppy.mp4

# Image-to-video (prompt focuses on MOTION, not image content)
bash scripts/video/generate_video.sh \
  --mode i2v \
  --prompt "The petals begin to sway gently in the breeze, soft light shifts across the surface, [固定] fixed framing, dreamy pastel tones" \
  --first-frame photo.jpg \
  --output minimax-output/animated.mp4

# Start-end frame interpolation (sef mode uses MiniMax-Hailuo-02)
bash scripts/video/generate_video.sh \
  --mode sef \
  --first-frame start.jpg --last-frame end.jpg \
  --output minimax-output/transition.mp4

# Subject reference (face consistency, ref mode uses S2V-01, 6s only)
bash scripts/video/generate_video.sh \
  --mode ref \
  --prompt "A young woman in a white dress walks slowly through a sunlit garden, [跟随] smooth tracking, warm natural lighting, cinematic depth of field" \
  --subject-image face.jpg \
  --duration 6 \
  --output minimax-output/person.mp4
```### 长视频（多场景）

多场景长视频将片段链接在一起：第一个片段通过文本到视频 (t2v) 生成，然后每个后续片段使用前一个片段的最后一帧作为其第一帧 (i2v)。片段通过淡入淡出过渡连接起来，以实现平滑的连续性。默认值为每段 6 秒。

**工作流程：**
1. 分段 1：t2v — 纯粹由优化的文本提示生成
2. 片段 2+：i2v — 前一个片段的最后一帧变为 `first_frame_image`，提示描述 **运动以及从该结束状态开始的变化**
3. 所有片段均以 0.5 秒交叉淡入淡出过渡连接，以消除跳切
4.可选：AI生成的背景音乐叠加

**各段提示规则：**
- 每个分段提示必须使用专业公式独立优化
- 片段 1 (t2v)：包含主题、场景、摄像机、氛围的完整场景描述
- 片段 2+ (i2v)：重点关注上一个结束帧的**变化和移动**。不要重复视觉描述——第一帧已经提供了它
- 保持视觉一致性：保持各个细分市场的灯光、颜色分级和风格关键词一致
- 每个片段仅包含 6 秒的动作 — 保持专注```bash
# Example: 3-segment story with optimized per-segment prompts (default: 6s/segment, 768P)
bash scripts/video/generate_long_video.sh \
  --scenes \
    "A lone astronaut stands on a red desert planet surface, wind blowing dust particles, [推进] slow push in toward the visor, dramatic rim lighting, cinematic sci-fi atmosphere" \
    "The astronaut turns and begins walking toward a distant glowing structure on the horizon, dust swirling around boots, [跟随] tracking from behind, vast desolate landscape, golden light from the structure" \
    "The astronaut reaches the structure entrance, a massive doorway pulses with blue energy, [推进] slow push in toward the doorway, light reflects off the visor, awe-inspiring epic scale" \
  --music-prompt "cinematic orchestral ambient, slow build, sci-fi atmosphere" \
  --output minimax-output/long_video.mp4

# With custom settings
bash scripts/video/generate_long_video.sh \
  --scenes "Scene 1 prompt" "Scene 2 prompt" \
  --segment-duration 6 \
  --resolution 768P \
  --crossfade 0.5 \
  --music-prompt "calm ambient background music" \
  --output minimax-output/long_video.mp4
```### 添加背景音乐```bash
bash scripts/video/add_bgm.sh \
  --video input.mp4 \
  --generate-bgm --instrumental \
  --music-prompt "soft piano background" \
  --bgm-volume 0.3 \
  --output minimax-output/output_with_bgm.mp4
```### 模板视频```bash
bash scripts/video/generate_template_video.sh \
  --template-id 392753057216684038 \
  --media photo.jpg \
  --output minimax-output/template_output.mp4
```### 视频模型

|模式|默认型号|默认持续时间 |默认分辨率|笔记|
|------|--------------|-----------------|--------------------|--------|
| t2v | MiniMax-Hailuo-2.3 | 6s | 768P |最新文字转视频 |
| i2v | MiniMax-Hailuo-2.3 | 6s | 768P |最新图像转视频 |
|自卫| MiniMax-Hailuo-02 | 6s | 768P |开始-结束帧|
|参考| S2V-01 | 6s | 720P |主题参考，仅 6s |

## 媒体工具（音频/视频处理）

入口点：`scripts/media_tools.sh`

基于 FFmpeg 的独立实用程序，用于格式转换、串联、提取、修剪和音频叠加。当用户需要处理现有媒体文件而不通过 MiniMax API 生成新内容时，请使用这些。

### 视频格式转换```bash
# Convert between formats (mp4, mov, webm, mkv, avi, ts, flv)
bash scripts/media_tools.sh convert-video input.webm -o output.mp4
bash scripts/media_tools.sh convert-video input.mp4 -o output.mov

# With quality / resolution / fps options
bash scripts/media_tools.sh convert-video input.mp4 -o output.mp4 \
  --crf 18 --preset medium --resolution 1920x1080 --fps 30
```### 音频格式转换```bash
# Convert between formats (mp3, wav, flac, ogg, aac, m4a, opus, wma)
bash scripts/media_tools.sh convert-audio input.wav -o output.mp3
bash scripts/media_tools.sh convert-audio input.mp3 -o output.flac \
  --bitrate 320k --sample-rate 48000 --channels 2
```### 视频拼接```bash
# Concatenate with crossfade transition (default 0.5s)
bash scripts/media_tools.sh concat-video seg1.mp4 seg2.mp4 seg3.mp4 -o merged.mp4

# Hard cut (no crossfade)
bash scripts/media_tools.sh concat-video seg1.mp4 seg2.mp4 -o merged.mp4 --crossfade 0
```### 音频连接```bash
# Simple concatenation
bash scripts/media_tools.sh concat-audio part1.mp3 part2.mp3 -o combined.mp3

# With crossfade
bash scripts/media_tools.sh concat-audio part1.mp3 part2.mp3 -o combined.mp3 --crossfade 1
```### 从视频中提取音频```bash
# Extract as mp3
bash scripts/media_tools.sh extract-audio video.mp4 -o audio.mp3

# Extract as wav with higher bitrate
bash scripts/media_tools.sh extract-audio video.mp4 -o audio.wav --bitrate 320k
```### 视频修剪```bash
# Trim by start/end time (seconds)
bash scripts/media_tools.sh trim-video input.mp4 -o clip.mp4 --start 5 --end 15

# Trim by start + duration
bash scripts/media_tools.sh trim-video input.mp4 -o clip.mp4 --start 10 --duration 8
```### 将音频添加到视频（覆盖/替换）```bash
# Mix audio with existing video audio
bash scripts/media_tools.sh add-audio --video video.mp4 --audio bgm.mp3 -o output.mp4 \
  --volume 0.3 --fade-in 2 --fade-out 3

# Replace original audio entirely
bash scripts/media_tools.sh add-audio --video video.mp4 --audio narration.mp3 -o output.mp4 \
  --replace
```### 媒体文件信息```bash
bash scripts/media_tools.sh probe input.mp4
```## 脚本架构```
scripts/
├── check_environment.sh         # Env verification (curl, ffmpeg, jq, xxd, API key)
├── media_tools.sh               # Audio/video conversion, concat, trim, extract
├── tts/
│   └── generate_voice.sh        # Unified TTS CLI (tts, clone, design, list-voices, generate, merge, convert)
├── music/
│   └── generate_music.sh        # Music generation CLI
├── image/
│   └── generate_image.sh        # Image generation CLI (2 modes: t2i, i2i)
└── video/
    ├── generate_video.sh        # Video generation CLI (4 modes: t2v, i2v, sef, ref)
    ├── generate_long_video.sh   # Multi-scene long video
    ├── generate_template_video.sh # Template-based video
    └── add_bgm.sh              # Background music overlay
```## 参考文献

请阅读以下内容以了解详细的 API 参数、语音目录和提示工程：

- [tts-guide.md](references/tts-guide.md) — TTS 设置、语音管理、音频处理、分段格式、故障排除
- [tts-voice-catalog.md](references/tts-voice-catalog.md) — 包含 ID、描述和参数参考的完整语音目录
- [music-api.md](references/music-api.md) — 音乐生成 API：端点、参数、响应格式
- [image-api.md](references/image-api.md) — 图像生成 API：文本转图像、图像转图像、参数
- [video-api.md](references/video-api.md) — 视频 API：端点、模型、参数、相机指令、模板
- [video-prompt-guide.md](references/video-prompt-guide.md) — 视频提示工程：公式、样式、图像转视频提示