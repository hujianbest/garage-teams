# MiniMax 音乐生成 API (music-2.5)

来源：https://platform.minimaxi.com/docs/api-reference/music- Generation

## 端点

`发布 https://api.minimaxi.com/v1/music_ Generation`

## 授权

`授权：持有者 <MINIMAX_API_KEY>`

## 请求（JSON）

要求：
- `model`: 字符串 — `music-2.5`
- `lyrics`：字符串（1–3500 个字符）— 必需。使用“\n”作为换行符。结构标签：`[Verse]`、`[Chorus]`、`[Bridge]`、`[Intro]`、`[Outro]`等。

可选：
- `prompt`: string (0–2000 chars) — 样式描述，可选但推荐。
- `lyrics_optimizer`: boolean — 当歌词为空时根据提示自动生成歌词。
- `stream`：布尔值（默认为`false`）
- `output_format`：`hex`（默认）或`url`。网址 24 小时有效。
- `aigc_watermark`：布尔值 — 顶级字段，仅限非流式传输。
- `音频设置`:
  - `采样率`：16000、24000、32000、44100
  - `比特率`: 32000, 64000, 128000, 256000
  - `格式`：mp3、wav、pcm

## 示例```json
{
  "model": "music-2.5",
  "prompt": "indie folk, melancholic, introspective",
  "lyrics": "[verse]\n...\n[chorus]\n...",
  "aigc_watermark": false,
  "audio_setting": {
    "sample_rate": 44100,
    "bitrate": 256000,
    "format": "mp3"
  }
}
```## 回应

- `data.audio`：十六进制字符串或 URL 取决于 `output_format`
- `data.status`: 1 (生成), 2 (完成)
- `extra_info`：持续时间、采样率、通道、比特率、大小
- `base_resp.status_code`：成功时为 0

## 注释

- `music-2.5` 不支持 `is_instrumental`。对于器乐，使用歌词“[intro] [outro]”，并在提示中添加“纯音乐，无歌词”。
- `prompt` 是可选的，但建议使用以更好地控制样式。
- `stream=true` 仅支持 `hex` 输出。