# 开始使用

## 1.设置API密钥```bash
export MINIMAX_API_KEY="<paste-your-key-here>"
```## 2.安装依赖项```bash
pip install requests

# FFmpeg (optional, for audio post-processing)
# macOS:
brew install ffmpeg
# Ubuntu:
sudo apt install ffmpeg
```## 3. 快速测试```bash
python scripts/minimax_tts.py "Hello world" -o test.mp3
```如果成功，您将看到“OK: xxxxx bytes -> test.mp3”。

## 后续步骤

- **语音选择**：参见 [minimax-voice-catalog.md](minimax-voice-catalog.md)
- **TTS 工作流程**：请参阅 [minimax-tts-guide.md](minimax-tts-guide.md)
- **故障排除**：请参阅 [troubleshooting.md](troubleshooting.md)