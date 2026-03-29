# MiniMax 视频生成 API 文档

## API 端点

|端点 |方法|描述 |
|----------|--------|-------------|
| `/v1/video_ Generation` |发布 |创建视频生成任务（所有 4 种模式）|
| `/v1/query/video_ Generation` |获取 |查询任务状态 |
| `/v1/files/retrieve` |获取 |获取视频下载地址 |
| `/v1/video_template_ Generation` |发布 |创建基于模板的视频任务 |
| `/v1/query/video_template_ Generation` |获取 |查询模板任务状态 |

**基本 URL：** `https://api.minimaxi.com`
**授权：** `授权：持有者 {MINIMAX_API_KEY}`

---

## 视频生成模型

### 文本转视频 (T2V) 模型
|型号|分辨率|持续时间 |笔记|
|--------|---------|----------|--------|
| MiniMax-Hailuo-2.3 | 768P（默认）、1080P | 6 秒 (1080P)、6/10 秒 (768P) |推荐，最新|
| MiniMax-Hailuo-2.3-快速 | 768P（默认）、1080P | 6 秒 (1080P)、6/10 秒 (768P) |快速变体|
| MiniMax-Hailuo-02 | 512P、768P（默认）、1080P | 6秒（1080P）、6/10秒（512P/768P）|上一代 |
| T2V-01-导演| 720P | 6s |导演控制|
| T2V-01 | 720P | 6s |基础型号|

### 图像到视频 (I2V) 模型
|型号|分辨率|持续时间 |笔记|
|--------|---------|----------|--------|
| MiniMax-Hailuo-2.3 | 768P、1080P | 6s |推荐|
| MiniMax-Hailuo-2.3-快速 | 768P、1080P | 6s |快速变体 |
| MiniMax-Hailuo-02 | 512P、768P、1080P | 6/10 秒 |上一代 |
| I2V-01-总监 | 720P | 6s |导演控制|
| I2V-01-直播 | 720P | 6s |现场照片风格|
| I2V-01 | 720P | 6s |基础型号|

### 起始帧模型
|型号|笔记|
|--------|--------|
| MiniMax-Hailuo-02 |唯一支持起始帧的机型|

### 主题参考模型
|型号|笔记|
|--------|--------|
| S2V-01 |视频中的面部一致性 |

---

## 请求参数

### 通用参数（所有模式）
|参数|类型 |必填 |默认 |描述 |
|------------|------|----------|---------|------------|
|型号|字符串|是的 | - |型号名称 |
|提示|字符串|取决于 | - |视频描述，最多 2000 个字符 |
|持续时间|整数 |没有 | 6 |视频长度（以秒为单位）|
|分辨率|字符串|没有 | 768P/720P |视频分辨率|
|提示优化器 |布尔 |没有 |真实|自动优化提示 |
|快速预处理 |布尔 |没有 |假 |缩短优化器持续时间 |
|回调网址 |字符串|没有 | - |网络钩子 URL |
| aigc_水印 |布尔 |没有 |假 |添加水印 |

### 图像到视频参数
|参数|类型 |必填 |描述 |
|------------|------|----------|----------|
|第一帧图像 |字符串|是的 |起始帧（URL 或 base64 数据 URL）|

**图片要求：** JPG/JPEG/PNG/WebP，<20MB，短边>300px，长宽比2:5–5:2。

### 起始帧参数
|参数|类型 |必填 |描述 |
|------------|------|----------|----------|
|第一帧图像 |字符串|是的 |起始帧 |
|最后一帧图像 |字符串|是的 |结束帧|

### 主题参考参数
|参数|类型 |必填 |描述 |
|------------|------|----------|----------|
|主题参考 |数组|是的 |主题对象数组 |

每个对象都有“type”和“image”（图像 URL 数组）：```json
[{ "type": "character", "image": ["<image_url>"] }]
```---

## Camera Instructions

Supported in `[指令]` syntax for Hailuo-2.3, Hailuo-02, and Director models:

| Category | Instructions |
|----------|-------------|
| Pan | `[左移]`, `[右移]` |
| Rotation | `[左摇]`, `[右摇]` |
| Push/Pull | `[推进]`, `[拉远]` |
| Elevation | `[上升]`, `[下降]` |
| Tilt | `[上摇]`, `[下摇]` |
| Zoom | `[变焦推近]`, `[变焦拉远]` |
| Other | `[晃动]`, `[跟随]`, `[固定]` |

Combine for simultaneous: `[左摇,上升]` (max 3). Sequential: `...[推进], then ...[拉远]`

---

## Response

**Query status:** `Preparing`, `Queueing`, `Processing`, `Success`, `Fail`

**Error codes:** 0 (success), 1002 (rate limited), 1004 (auth failed), 1008 (insufficient balance), 1026 (sensitive content), 2013 (invalid params), 2049 (invalid API key)

---

## Video Templates

| Template | ID | Input | Description |
|----------|-----|-------|-------------|
| Diving | 392753057216684038 | Image | Diving motion |
| Rings | 393881433990066176 | Image | Gymnastics rings |
| Survival | 393769180141805569 | Image + Text | Outdoor survival |
| Labubu | 394246956137422856 | Image | Labubu character |
| McDonald's Delivery | 393879757702918151 | Image | Pet courier |
| Tibetan Portrait | 393766210733957121 | Image | Cultural portrait |
| Female Model Ads | 393866076583718914 | Image | Female fashion |
| Male Model Ads | 393876118804459526 | Image | Male fashion |
| Winter Romance | 393857704283172856 | Image | Snowy portrait |
| Four Seasons | 398574688191234048 | Image | Seasonal portrait |
| Helpless Moments | 394125185182695432 | Text only | Comedic animation |