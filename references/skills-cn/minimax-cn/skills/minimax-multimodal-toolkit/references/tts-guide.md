# TTS 指南

## 设置```bash
cd skills/MiniMaxStudio
pip install -r requirements.txt
brew install ffmpeg   # macOS (or: sudo apt install ffmpeg)
export MINIMAX_API_KEY="your-api-key"   # sk-api-xxx or sk-cp-xxx
python scripts/check_environment.py
```## 快速测试```bash
python scripts/tts/generate_voice.py tts "Hello, this is a test." -o test.mp3
```## 语音管理

列出可用的声音：```bash
python scripts/tts/generate_voice.py list-voices
```### 语音克隆

从音频样本创建自定义语音：```bash
python scripts/tts/generate_voice.py clone audio.mp3 --voice-id my-custom-voice

# With preview
python scripts/tts/generate_voice.py clone audio.mp3 --voice-id my-voice --preview "Test text" --preview-output preview.mp3
```要求：时长10秒至5分钟，≤20MB，mp3/wav/m4a格式。

### 声音设计

根据文本描述设计声音：```bash
python scripts/tts/generate_voice.py design "A warm, gentle female voice" --voice-id designed-voice
```如果不与 TTS 一起使用，自定义语音将在 7 天后过期。

## 音频处理

### 合并```bash
python scripts/tts/generate_voice.py merge file1.mp3 file2.mp3 -o combined.mp3
python scripts/tts/generate_voice.py merge a.mp3 b.mp3 -o merged.mp3 --crossfade 300
```＃＃＃ 转变```bash
python scripts/tts/generate_voice.py convert input.wav -o output.mp3
python scripts/tts/generate_voice.py convert input.wav -o output.mp3 --format mp3 --bitrate 192k --sample-rate 32000
```需要 FFmpeg。支持的格式：mp3、wav、flac、ogg、m4a、aac、wma、opus、pcm。

## 基于分段的 TTS

对于使用“segments.json”文件的多语音、多情感工作流程：```bash
# Validate
python scripts/tts/generate_voice.py validate segments.json --verbose

# Generate
python scripts/tts/generate_voice.py generate segments.json -o output.mp3 --crossfade 200
```### snippets.json 格式```json
[
  { "text": "Hello!", "voice_id": "female-shaonv", "emotion": "" },
  { "text": "How are you?", "voice_id": "male-qn-qingse", "emotion": "happy" }
]
```- `text`（必需）：要合成的文本
- `voice_id`（必填）：语音 ID
- `emotion`（可选）：对于语音 2.8 型号，留空以进行自动匹配。有效值：快乐、悲伤、愤怒、恐惧、厌恶、惊讶、平静、流利、耳语

## 故障排除

|错误|解决方案 |
|--------|----------|
| `需要 MINIMAX_API_KEY` | `导出 MINIMAX_API_KEY="密钥"` |
| `FFmpeg 未安装` | `brew 安装 ffmpeg` |
| `找不到声音` | `python script/tts/generate_voice.py 列表声音` |
| `401 未经授权` |检查 API 密钥有效性 |
| `429 请求太多` |在请求之间添加延迟 |

## API 详细信息

- **端点**：`POST /v1/t2a_v2`
- **基本 URL**：`https://api.minimaxi.com`
- **授权**：`授权：持有者 {MINIMAX_API_KEY}`
- **型号**：speech-2.8-hd（推荐）、speech-2.8-turbo、speech-2.6-hd、speech-2.6-turbo、speech-02-hd、speech-02-turbo、speech-01-hd、speech-01-turbo
- **文本限制**：每个请求 10,000 个字符
- **暂停标记**：`<#x#>`，其中 x 是秒 (0.01–99.99)
- **感叹词标签**（仅限语音 2.8）：`（笑）`、`（咯咯）`、`（咳嗽）`、`（叹气）`、`（呼吸）` 等。