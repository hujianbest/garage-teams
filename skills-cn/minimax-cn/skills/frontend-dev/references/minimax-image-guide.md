# 图像生成指南

## CLI 用法```bash
# Basic (1:1, 1024x1024)
python scripts/minimax_image.py "A cat astronaut floating in space" -o cat.png

# 16:9 for hero banner
python scripts/minimax_image.py "Mountain landscape at golden hour" -o hero.png --ratio 16:9

# Batch: 4 images at once
python scripts/minimax_image.py "Minimalist product icon" -o icons.png -n 4

# With seed for reproducibility
python scripts/minimax_image.py "Abstract gradient background" -o bg.png --seed 42

# Enable prompt optimization
python scripts/minimax_image.py "a dog" -o dog.png --optimize

# Base64 mode (no URL download, save directly)
python scripts/minimax_image.py "Logo concept" -o logo.png --base64
```## 程序化使用```python
from minimax_image import generate_image, download_and_save

# Generate and get URL
result = generate_image("A cat in space", aspect_ratio="16:9")
url = result["data"]["image_urls"][0]
download_and_save(url, "cat.png")

# Generate multiple
result = generate_image("Icon design", n=4, aspect_ratio="1:1")
for i, url in enumerate(result["data"]["image_urls"]):
    download_and_save(url, f"icon-{i}.png")
```## 型号

目前只有“image-01”。

## 纵横比和尺寸

|比率|像素|使用案例 |
|--------|--------|----------|
| `1:1` | 1024x1024 | 1024x1024头像，图标，方形缩略图|
| `16:9` | 1280x720 | 1280x720英雄横幅，视频缩略图|
| `4:3` | 1152x864 |标准景观|
| `3:2` | 1248x832 | 1248x832照片风格|
| `2:3` | 832x1248 | 832x1248肖像，移动|
| `3:4` | 864x1152 |肖像卡|
| `9:16` | 720x1280 |手机全屏，故事|
| `21:9` | 1344x576 | 1344x576超宽横幅|

还支持自定义尺寸：[512, 2048] 中的宽度/高度，必须能被 8 整除。

## 限制

- 提示：最多 1,500 个字符
- 批次：每个请求 1–9 个图像
- URL 在 24 小时后过期（使用 `--base64` 以避免过期）
- 种子：设置为在相同的提示下可重现的结果