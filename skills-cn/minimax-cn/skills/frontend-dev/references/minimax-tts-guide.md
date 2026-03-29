# TTS 指南

## CLI 使用（推荐）```bash
# Basic
python scripts/minimax_tts.py "Hello world" -o output.mp3

# Custom voice and speed
python scripts/minimax_tts.py "你好世界" -o hi.mp3 -v female-shaonv --speed 0.9

# WAV format, high quality
python scripts/minimax_tts.py "Welcome" -o out.wav -v male-qn-jingying --format wav --sample-rate 32000

# With emotion (for speech-2.6 models)
python scripts/minimax_tts.py "Great news!" -o happy.mp3 -v female-shaonv --emotion happy --model speech-2.6-hd
```## 程序化使用```python
from minimax_tts import tts

# Basic
audio_bytes = tts("Hello world")

# With options
audio_bytes = tts(
    text="Welcome to our product.",
    voice_id="female-shaonv",
    model="speech-2.8-hd",
    speed=0.9,
    fmt="mp3",
)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```## 限制

- **同步 TTS：** 每个请求最多 10,000 个字符
- **暂停标记：** 插入 `<#1.5#>` 暂停 1.5 秒（范围：0.01–99.99 秒）

## 型号选择

|型号|最适合 |
|--------|----------|
| `语音-2.8-hd` |最高品质，自动情感（推荐） |
| `语音-2.8-turbo` |速度快，品质好|
| `语音-2.6-hd` |需要手动情绪控制|
| `语音-2.6-turbo` |快速+手动情感|

## 语音选择

有关完整列表，请参阅 [minimax-voice-catalog.md](minimax-voice-catalog.md)。

常见声音：

|语音识别 |性别 |风格|
|----------|--------|--------|
| `男qn情色` |男 |年轻、温柔|
| `男-qn-jingying` |男 |精英、权威|
| `男-qn-badao` |男 |霸道、强大|
| `女少女` |女|年轻、聪明|
| `女宇杰` |女|成熟、优雅|
| `女-成书` |女|精密|
| `主持人_男` |男 |新闻主持人 |
| `主持人_女性` |女|新闻主持人 |
| `有声书_男性_1` |男 |有声读物旁白 |
| `有声书_女性_1` |女|有声读物旁白 |

## 最佳实践

- 使用 `speech-2.8-hd` 并让情绪自动匹配 - 除非需要，否则不要手动设置情绪
- 对网络音频使用 32000 采样率（质量和文件大小的良好平衡）
- 对于长文本（>10,000 个字符），分成块并与 FFmpeg 合并