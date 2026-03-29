# 音乐生成指南

## CLI 用法```bash
# Instrumental (no vocals)
python scripts/minimax_music.py --prompt "Jazz piano, smooth, relaxing" --instrumental -o jazz.mp3

# With custom lyrics
python scripts/minimax_music.py --prompt "Indie folk, melancholic" --lyrics "[verse]\nStreetlights flicker\nOn empty roads" -o song.mp3

# Auto-generate lyrics from prompt
python scripts/minimax_music.py --prompt "Upbeat pop, energetic, summer vibes" --auto-lyrics -o pop.mp3

# From lyrics file
python scripts/minimax_music.py --prompt "Soulful blues, rainy night" --lyrics-file lyrics.txt -o blues.mp3

# Custom audio settings
python scripts/minimax_music.py --prompt "Lo-fi beats" --instrumental -o lofi.wav --format wav --sample-rate 44100 --bitrate 256000
```## 程序化使用```python
from minimax_music import generate_music

# Instrumental
result = generate_music(prompt="Jazz piano, smooth", is_instrumental=True)
with open("jazz.mp3", "wb") as f:
    f.write(result["audio_bytes"])

# With lyrics
result = generate_music(
    prompt="Indie folk, acoustic guitar",
    lyrics="[verse]\nWalking through the rain\n[chorus]\nI'll find my way home",
)

# Auto-generate lyrics
result = generate_music(
    prompt="Upbeat pop, summer anthem",
    lyrics_optimizer=True,
)

# Access metadata
print(f"Duration: {result['duration']}ms")
print(f"Sample rate: {result['sample_rate']}")
print(f"Size: {result['size']} bytes")
```## 型号

|型号|特点|
|--------|----------|
| `音乐-2.5+` |受到推崇的。支持乐器模式、完整的歌曲结构、高保真音频 |
| `音乐-2.5` |标准型号。无乐器模式 |

## 即时写作

`prompt` 参数使用逗号分隔的描述符描述音乐风格：

|类别 |示例 |
|----------|----------|
|类型 |蓝调、流行、摇滚、爵士、电子、嘻哈、民谣、古典 |
|心情 |深情、忧郁、乐观、活力、平和、黑暗、怀旧 |
|场景|雨夜、夏日、公路旅行、深夜、日出 |
|仪器仪表|电吉他、钢琴、原声、合成器、弦乐 |
|声乐类型|男声、女声、柔和的声音、有力的声音 |
|节奏|慢节奏、快节奏、中节奏、放松|

**提示示例：**```
"Soulful Blues, Rainy Night, Melancholy, Male Vocals, Slow Tempo"
"Upbeat Pop, Summer Vibes, Female Vocals, Energetic, Synth-heavy"
"Lo-fi Hip-hop, Chill, Relaxed, Instrumental, Piano samples"
"Cinematic Orchestral, Epic, Building tension, Strings and Brass"
```## 歌词格式

使用括号中的结构标签来组织歌曲部分：

### 结构标签

|标签 |目的|
|-----|---------|
| `[简介]` |开场部分（可以是乐器）|
| `[诗节]` / `[诗节 1]` |故事/叙述部分 |
| `[前副歌]` |合唱前的准备|
| `[合唱]` |主钩子，通常重复 |
| `[后合唱]` |副歌后的延伸|
| `[桥]` |近端对比部分|
| `[插曲]` |器乐休息|
| `[独奏]` |器乐独奏（添加方向：“缓慢，蓝调”）|
| `[尾声]` |结束部分|
| `[中断]` |短暂的停顿或过渡 |
| `[挂钩]` |朗朗上口的重复短语|
| `[建立]` |张力构建部分|
| `[Inst]` |器乐部分|
| `[过渡]` |章节变更 |

### 伴唱和指导

使用括号来伴奏人声或演奏音符：```
(Ooh, yeah)
(Harmonize)
(Whispered)
(Fade out...)
```### 歌词示例```
[Intro]
(Soft piano)

[Verse 1]
Streetlights flicker on empty roads
The rain keeps falling, the wind still blows
I'm walking home with nowhere to go
Just memories of what I used to know

[Pre-Chorus]
And I can feel it coming back to me
(Coming back to me)

[Chorus]
Under the neon lights tonight
I'm searching for what feels right
(Oh, feels right)
These city streets will guide me home
I'm tired of feeling so alone

[Verse 2]
Coffee shops and midnight trains
The faces change but the feeling remains
...

[Bridge]
Maybe tomorrow will be different
Maybe I'll finally understand
(Understand...)

[Solo]
(Slow, mournful, bluesy guitar)

[Outro]
(Fade out...)
Under the neon lights...
```## 音频设置

|参数|选项|默认 |笔记|
|------------|---------|---------|--------|
| `格式` | mp3、wav、pcm | mp3| WAV 最高品质 |
| `采样率` | 16000、24000、32000、44100 | 44100 | 44100 推荐 |
| `比特率` | 32000、64000、128000、256000 | 256000 | 256000更高=更好的质量|

## 生成模式

### 1. 仅乐器```bash
python scripts/minimax_music.py --prompt "Ambient electronic, space theme" --instrumental -o ambient.mp3
```- 需要 `music-2.5+` 模型
- 只需“提示”，无需歌词

### 2. 带有自定义歌词```bash
python scripts/minimax_music.py --prompt "Pop ballad, emotional" --lyrics "[verse]\nYour lyrics here" -o ballad.mp3
```- 提供“提示”（风格）和“歌词”（单词+结构）

### 3.自动生成歌词```bash
python scripts/minimax_music.py --prompt "Rock anthem about freedom" --auto-lyrics -o rock.mp3
```- 系统根据提示生成歌词
- 当歌词不重要时，适合快速生成

## 限制

- **提示：** 最多 2,000 个字符
- **歌词：** 1–3,500 个字符
- **持续时间：** 每代约 25-30 秒（各不相同）
- **URL有效期：** 24小时（使用URL输出模式时）

## 最佳实践

1. **图层风格描述符** - 结合流派+情绪+乐器以获得精确的结果
2. **使用结构标签** — 即使是简单的 `[verse]` `[chorus]` 也能改善编排
3. **包括背景声音提示** - “(Ooh)”、“(Yeah)”添加制作润色
4. **将提示与歌词情绪相匹配** — 冲突的提示/歌词会产生不一致的结果
5. **背景乐器** — 使用 `--instrumental` 作为 BGM，避免声音干扰
6. **制作时使用高比特率** — 最终资源使用 256000，草稿使用较低比特率

## 常见用例

|使用案例|命令|
|----------|---------|
|背景音乐| `--提示“低保真、平静、环境”--instrumental` |
|登陆页面英雄 | `--提示“电影、鼓舞人心、建筑”--instrumental` |
|播客简介 | `--prompt“乐观、充满活力、简短”--instrumental` |
|示范曲 | `--提示“流行，朗朗上口”--自动歌词` |
|定制顺口溜| `--提示“快乐、明亮、企业”--歌词“[hook]\n你的品牌名称”` |

## 错误处理

|错误代码 |意义|解决方案 |
|------------|---------|----------|
| 1002 | 1002速率限制 |等待并重试 |
| 1004 | 1004验证失败 |检查 API 密钥 |
| 1008 | 1008余额不足|账户充值|
| 1026 | 1026已标记的内容 |改写提示/歌词 |
| 2013 |无效参数 |检查提示/歌词长度 |