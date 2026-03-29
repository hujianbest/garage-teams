# 故障排除

## 快速参考

|错误|原因 |修复 |
|--------|--------|-----|
| `MINIMAX_API_KEY 未设置` |未设置密钥 | `导出 MINIMAX_API_KEY="密钥"` |
| `401 未经授权` |密钥无效/过期 |检查密钥有效性 |
| `429 请求太多` |速率限制 |在请求之间添加延迟 |
| `超时错误` |网络或长文|使用异步 TTS 处理长文本，检查网络 |
| `无效参数，方法 t2a-v2 没有模型` |型号名称错误 |使用`speech-2.8-hd`（连字符，而不是下划线）|
| `brotli：解码器进程调用...` |编码问题 |已在 utils.py 中修复（Accept-Encoding 标头）|

## 环境

### API 密钥未设置```bash
export MINIMAX_API_KEY="<paste-your-key-here>"

# Verify
echo $MINIMAX_API_KEY
```### 未找到 FFmpeg```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg

# Verify
ffmpeg -version
```### 缺少 Python 包```bash
pip install requests
```## API 错误

### 身份验证 (401)

- 验证API密钥是否正确且未过期
- 检查键值中是否有多余空格

### 速率限制 (429)

在请求之间添加延迟：```python
import time
for text in texts:
    result = tts(text)
    time.sleep(1)
```### 型号名称无效

有效名称（使用连字符，必须包含 -hd 或 -turbo）：
- `speech-2.8-hd`（推荐）
- `语音-2.8-turbo`
- `语音-2.6-hd`
- `语音-2.6-turbo`

错误：`speech_01`、`speech_2.6`、`speech-01`

## 音频问题

### 质量差

使用更高的设置重新生成：```bash
python scripts/minimax_tts.py "text" -o out.mp3 --sample-rate 32000 --model speech-2.8-hd
```###无效情绪

有效情绪：
- 所有模型：快乐、悲伤、愤怒、恐惧、厌恶、惊讶、平静
- 仅语音 2.6：+ 流利、耳语
-speech-2.8：自动匹配（留空，推荐）