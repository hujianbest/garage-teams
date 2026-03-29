# 视频生成指南

## CLI 用法```bash
# Basic
python scripts/minimax_video.py "A cat playing piano in a cozy room" -o cat.mp4

# With camera control
python scripts/minimax_video.py "Ocean waves crashing on rocks [Truck left]" -o waves.mp4

# 10 seconds, 1080P
python scripts/minimax_video.py "City skyline at sunset [Push in]" -o city.mp4 --duration 10 --resolution 1080P

# Disable prompt auto-optimization
python scripts/minimax_video.py "Exact prompt I want used" -o out.mp4 --no-optimize
```## 程序化使用```python
from minimax_video import generate, create_task, poll_task, download_video

# Full pipeline (blocking)
generate("A cat playing piano", "cat.mp4", model="MiniMax-Hailuo-2.3", duration=6)

# Step by step
task_id = create_task("A cat playing piano")
file_id = poll_task(task_id, interval=10, max_wait=600)
download_video(file_id, "cat.mp4")
```## 型号

|型号|分辨率|持续时间 |笔记|
|--------|---------|----------|--------|
| `MiniMax-Hailuo-2.3` | 768P、1080P | 6 秒、10 秒（仅限 768P）|最新，推荐 |
| `MiniMax-Hailuo-02` | 768P、1080P | 6 秒、10 秒（仅限 768P）|上一代 |
| `T2V-01-导演` | 720P | 6s |优化相机控制 |
| `T2V-01` | 720P | 6s |基础型号|

## 相机命令

在提示文本中插入“[Command]”来控制相机移动：

|命令|效果|
|---------|--------|
| `[卡车向左]` |相机向左移动 |
| `[卡车右]` |相机向右移动 |
| `[推入]` | Camera moves toward subject |
| `[拉出]` |相机远离拍摄对象|
| `[向左平移]` |相机向左旋转（固定位置）|
| `[向右平移]` |相机向右旋转（固定位置）|
| `[向上倾斜]` |相机向上倾斜|
| `[向下倾斜]` |相机向下倾斜|
| `[底座上升]` |相机垂直上升|
| `[底座下降]` |相机垂直下降|
| `[放大]` |镜头拉近|
| `[缩小]` |镜头拉远 |
| `[静态镜头]` |没有相机移动|
| `[跟踪拍摄]` |相机跟随拍摄对象 |
| `[摇动]` |手持震动效果|

示例：“一名跑步者冲刺穿过森林小径[追踪镜头]”`

## 管道

该脚本处理完整的异步流程：

1. **创建任务** — `POST /v1/video_ Generation` → 返回 `task_id`
2. **轮询状态** — `GET /v1/query/video_ Generation?task_id=xxx` → 轮询直到`成功`
   - 状态值：`准备`→`排队`→`处理`→`成功`/`失败`
3. **下载** — `GET /v1/files/retrieve?file_id=xxx` → 获取 `download_url` (有效期 1 小时) → 保存文件

典型生成时间：1-5 分钟，具体取决于持续时间和分辨率。

## 限制

- 提示：最多 2,000 个字符
- 1080P：仅支持6秒时长
- 10 秒持续时间：仅适用于 Hailuo-2.3/02 的 768P
- 下载 URL 1 小时后过期