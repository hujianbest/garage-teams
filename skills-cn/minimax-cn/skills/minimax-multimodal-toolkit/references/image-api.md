# MiniMax 图像生成 API (image-01)

来源：https://platform.minimaxi.com/docs/api-reference/image- Generation-t2i 和 https://platform.minimaxi.com/docs/api-reference/image- Generation-i2i

## 端点

`发布 https://api.minimaxi.com/v1/image_ Generation`

## 授权

`授权：持有者 <MINIMAX_API_KEY>`

## 请求（JSON）

要求：
- `model`: 字符串 — `image-01`
- `prompt`：字符串（最多 1500 个字符）— 所需图像的文本描述

可选：
- `aspect_ratio`: string — 图像长宽比，默认为 `1:1`。选项：
  - `1:1` (1024×1024)
  - `16:9` (1280×720)
  - `4:3` (1152×864)
  - `3:2` (1248×832)
  - `2:3` (832×1248)
  - `3:4` (864×1152)
  - `9:16` (720×1280)
  - `21:9` (1344×576)
- `width`：整数 — 自定义宽度（以像素为单位）。范围 [512, 2048]，必须是 8 的倍数。如果两者均设置，则由 `aspect_ratio` 覆盖。
- `height`：整数 — 自定义高度（以像素为单位）。与“宽度”相同的规则。 “宽度”和“高度”必须一起设置。
- `response_format`：字符串 — `url` （默认，24 小时有效）或 `base64`
- `n`：整数（1–9，默认 1）— 要生成的图像数量
- `seed`: 整数 — 用于再现性的随机种子
- `prompt_optimizer`: boolean (默认 `false`) — 启用自动提示优化
- `aigc_watermark`: 布尔值 (默认 `false`) — 添加 AIGC 水印

### 主题参考（图像到图像）

- `subject_reference`：数组 — 用于图像到图像生成的字符引用
  - `type`: string — 目前只有 `character` （肖像）
  - `image_file`：字符串 — 将图像引用为公共 URL 或 Base64 数据 URL (`data:image/jpeg;base64,...`)。为获得最佳效果，请使用单人正面照片。格式：JPG、JPEG、PNG。最大大小：10MB。

## 示例 — 文本到图像```json
{
  "model": "image-01",
  "prompt": "A man in a white t-shirt, full-body, standing front view, outdoors, with the Venice Beach sign in the background, Los Angeles. Fashion photography in 90s documentary style, film grain, photorealistic.",
  "aspect_ratio": "16:9",
  "response_format": "url",
  "n": 3,
  "prompt_optimizer": true
}
```## 示例 — 图像到图像（字符参考）```json
{
  "model": "image-01",
  "prompt": "A girl looking into the distance from a library window",
  "aspect_ratio": "16:9",
  "subject_reference": [
    {
      "type": "character",
      "image_file": "https://example.com/face.jpg"
    }
  ],
  "n": 2
}
```＃＃ 回复```json
{
  "id": "03ff3cd0820949eb8a410056b5f21d38",
  "data": {
    "image_urls": ["https://...", "https://...", "https://..."],
    "image_base64": null
  },
  "metadata": {
    "success_count": 3,
    "failed_count": 0
  },
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```- `data.image_urls`：图像 URL 数组（当 `response_format` 为 `url` 时，24 小时有效）
- `data.image_base64`：Base64 字符串数组（当 `response_format` 为 `base64` 时）
- `metadata.success_count`：成功生成图像的数量
- `metadata.failed_count`：内容安全阻止的图像数量

## 状态代码

|代码|意义|
|------|---------|
| 0 |成功|
| 1002 | 1002速率有限，请稍后重试 |
| 1004 | 1004身份验证失败，请检查 API 密钥 |
| 1008 | 1008余额不足|
| 1026 | 1026提示包含敏感内容 |
| 2013 |无效参数 |
| 2049 | 2049无效的 API 密钥 |

## 注释

- API 是同步的 — 图像直接在响应中返回（无需轮询）。
- URL 格式的图像链接将在 24 小时后过期。
- 对于图像到图像：上传单个正面肖像以获得最佳角色参考结果。
- 如果同时提供了“width”/“height”，则“width”/“height”将被“aspect_ratio”覆盖。