# 提供商参考 — MiniMax

所有资产生成均使用 MiniMax API。环境：`MINIMAX_API_KEY`（必需）。

## 音频（同步 TTS）

**脚本：** `scripts/minimax_tts.py````bash
python scripts/minimax_tts.py "Hello world" -o output.mp3
python scripts/minimax_tts.py "你好" -o hi.mp3 -v female-shaonv
python scripts/minimax_tts.py "Welcome" -o out.wav -v male-qn-jingying --speed 0.8 --format wav
```**型号：** `speech-2.8-hd`（默认）。

|旗帜|默认 |范围/选项|
|------|---------|-----------------|
| `-o` | （必填）|输出文件路径 |
| `-v` | `男qn情色` |语音识别 |
| `--模型` | `语音-2.8-hd` |语音-2.8-hd / 语音-2.8-turbo / 语音-2.6-hd / 语音-2.6-turbo |
| `--速度` | 1.0 | 0.5–2.0 |
| `--音量` | 1.0 | 0.1–10 |
| `--间距` | 0 | -12 至 12 |
| `--情感` | （自动）|快乐/悲伤/愤怒/恐惧/厌恶/惊讶/平静/流利/耳语|
| `--格式` | mp3| mp3/wav/flac|
| `--lang` |汽车 |语言提升 |

**程序化：**```python
from minimax_tts import tts
audio_bytes = tts("Hello", voice_id="female-shaonv")
```## 视频（文本转视频）

**脚本：** `scripts/minimax_video.py````bash
python scripts/minimax_video.py "A cat playing piano" -o cat.mp4
python scripts/minimax_video.py "Ocean waves [Truck left]" -o waves.mp4 --duration 10
python scripts/minimax_video.py "City skyline [Push in]" -o city.mp4 --resolution 1080P
```**型号：** `MiniMax-Hailuo-2.3`（默认）。异步：脚本自动处理创建→轮询→下载。

|旗帜|默认 |选项|
|------|---------|---------|
| `-o` | （必填）|输出文件路径（.mp4）|
| `--模型` | `MiniMax-Hailuo-2.3` | MiniMax-Hailuo-2.3 / MiniMax-Hailuo-02 / T2V-01-Director / T2V-01 |
| `--持续时间` | 6 | 6 / 10（海螺型号仅 768P 10 秒）|
| `--决议` | 768P | 720P/768P/1080P（1080P仅6秒）|
| `--无优化` |假 |禁用提示自动优化 |
| `--轮询间隔` | 10 | 10状态检查之间的秒数 |
| `--max-wait` | 600 |最长等待时间（以秒为单位）|

**摄像机命令** — 在提示中插入“[命令]”：“[推入]”、“[卡车向左]”、“[向右平移]”、“[缩小]”、“[静态拍摄]”、“[跟踪拍摄]”等。

**程序化：**```python
from minimax_video import generate
generate("A cat playing piano", "cat.mp4", model="MiniMax-Hailuo-2.3", duration=6)
```有关完整的相机命令列表和型号兼容性，请参阅 [minimax-video-guide.md](minimax-video-guide.md)。

## 图像（文本到图像）

**脚本：** `scripts/minimax_image.py````bash
python scripts/minimax_image.py "A cat astronaut in space" -o cat.png
python scripts/minimax_image.py "Mountain landscape" -o hero.png --ratio 16:9
python scripts/minimax_image.py "Product icons, flat style" -o icons.png -n 4 --seed 42
```**型号：** `image-01`。同步：立即返回图像 URL（或 base64）。

|旗帜|默认 |选项|
|------|---------|---------|
| `-o` | （必填）|输出文件路径 (.png/.jpg) |
| `--比率` | 1:1 | 1:1 / 16:9 / 4:3 / 3:2 / 2:3 / 3:4 / 9:16 / 21:9 |
| `-n` | 1 |图片数量 (1–9) |
| `--种子` | （随机）|再现性种子 |
| `--优化` |假 |启用提示自动优化 |
| `--base64` |假 |返回 base64 而不是 URL |

**批量输出：**使用`-n > 1`，文件命名为`out-0.png`、`out-1.png`等。

**程序化：**```python
from minimax_image import generate_image, download_and_save
result = generate_image("A cat in space", aspect_ratio="16:9")
download_and_save(result["data"]["image_urls"][0], "cat.png")
```有关比例尺寸和详细信息，请参阅 [minimax-image-guide.md](minimax-image-guide.md)。

## 音乐（文本转音乐）

**脚本：** `scripts/minimax_music.py````bash
python scripts/minimax_music.py --prompt "Indie folk, melancholic" --lyrics "[verse]\nStreetlights flicker" -o song.mp3
python scripts/minimax_music.py --prompt "Upbeat pop, energetic" --auto-lyrics -o pop.mp3
python scripts/minimax_music.py --prompt "Jazz piano, smooth, relaxing" --instrumental -o jazz.mp3
```**型号：** `music-2.5+`（默认）。同步：返回音频十六进制或 URL。

|旗帜|默认 |选项|
|------|---------|---------|
| `-o` | （必填）|输出文件路径（.mp3/.wav）|
| `--提示` | （空）|音乐描述：风格、情绪、场景（最多 2000 个字符）|
| `--歌词` | （空）|带有结构标签的歌词（最多 3500 个字符）|
| `--歌词文件` | （空）|从文件中读取歌词 |
| `--模型` | `音乐-2.5+` |音乐-2.5+ / 音乐-2.5 |
| `--工具` |假 |仅生成器乐（无人声，仅音乐 2.5+）|
| `--自动歌词` |假 |根据提示自动生成歌词 |
| `--格式` | mp3| mp3/wav/pcm|
| `--采样率` | 44100 | 16000 / 24000 / 32000 / 44100 |
| `--比特率` | 256000 | 256000 32000 / 64000 / 128000 / 256000 |

**歌词结构标签：** `[Intro]`、`[Verse]`、`[Pre Chorus]`、`[Chorus]`、`[Interlude]`、`[Bridge]`、`[Outro]`、`[Post Chorus]`、`[Transition]`、`[Break]`、`[Hook]`、`[Build Up]`、`[Inst]`、`[Solo]`

**程序化：**```python
from minimax_music import generate_music
result = generate_music(prompt="Jazz piano", is_instrumental=True)
with open("jazz.mp3", "wb") as f:
    f.write(result["audio_bytes"])
```
