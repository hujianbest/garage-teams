---
名称：前端开发
描述：|
  全栈前端开发结合优质 UI 设计、电影动画、
  人工智能生成的媒体资产、有说服力的文案和视觉艺术。构建完成，
  具有真实媒体、高级动作和引人注目的副本的视觉冲击力网页。
  使用场合：构建登陆页面、营销网站、产品页面、仪表板、
  生成媒体资产（图像/视频/音频/音乐），编写转换副本，
  创建生成艺术，或实现电影滚动动画。
许可证：麻省理工学院
元数据：
  版本：“1.0.0”
  类别：前端
  来源：
    - Framer 运动文档
    - GSAP / GreenSock 文档
    - Three.js 文档
    - Tailwind CSS 文档
    - React / Next.js 文档
    - AIDA 框架（埃尔莫·刘易斯）
    - p5.js 文档
---

# 前端工作室

通过协调 5 种专业功能来构建完整的、可立即投入生产的前端页面：设计工程、运动系统、人工智能生成的资产、有说服力的文案和生成艺术。

## 调用```
/frontend-dev <request>
```用户以自然语言的形式提供他们的请求（例如“为音乐流应用程序构建登陆页面”）。

## 技能结构```
frontend-dev/
├── SKILL.md                      # Core skill (this file)
├── scripts/                      # Asset generation scripts
│   ├── minimax_tts.py            # Text-to-speech
│   ├── minimax_music.py          # Music generation
│   ├── minimax_video.py          # Video generation (async)
│   └── minimax_image.py          # Image generation
├── references/                   # Detailed guides (read as needed)
│   ├── minimax-cli-reference.md  # CLI flags quick reference
│   ├── asset-prompt-guide.md     # Asset prompt engineering rules
│   ├── minimax-tts-guide.md      # TTS usage & voices
│   ├── minimax-music-guide.md    # Music prompts & lyrics format
│   ├── minimax-video-guide.md    # Camera commands & models
│   ├── minimax-image-guide.md    # Ratios & batch generation
│   ├── minimax-voice-catalog.md  # All voice IDs
│   ├── motion-recipes.md         # Animation code snippets
│   ├── env-setup.md              # Environment setup
│   └── troubleshooting.md        # Common issues
├── templates/                    # Visual art templates
│   ├── viewer.html               # p5.js interactive art base
│   └── generator_template.js     # p5.js code reference
└── canvas-fonts/                 # Static art fonts (TTF + licenses)
```## 项目结构

### 资产（通用）

所有框架都使用相同的资产组织：```
assets/
├── images/
│   ├── hero-landing-1710xxx.webp
│   ├── icon-feature-01.webp
│   └── bg-pattern.svg
├── videos/
│   ├── hero-bg-1710xxx.mp4
│   └── demo-preview.mp4
└── audio/
    ├── bgm-ambient-1710xxx.mp3
    └── tts-intro-1710xxx.mp3
```**资产命名：** `{type}-{descriptor}-{timestamp}.{ext}`

### 按框架

|框架|资产位置 |组件位置 |
|----------|--------------|--------------------|
| **纯 HTML** | `./assets/` |不适用（内联或“./js/”）|
| **React/Next.js** | `公共/资产/` | `src/组件/` |
| **Vue/Nuxt** | `公共/资产/` | `src/组件/` |
| **Svelte/SvelteKit** | `静态/资产/` | `src/lib/components/` |
| **天文** | `公共/资产/` | `src/组件/` |

### 纯 HTML```
project/
├── index.html
├── assets/
│   ├── images/
│   ├── videos/
│   └── audio/
├── css/
│   └── styles.css
└── js/
    └── main.js           # Animations (GSAP/vanilla)
```### React / Next.js```
project/
├── public/assets/        # Static assets
├── src/
│   ├── components/
│   │   ├── ui/           # Button, Card, Input
│   │   ├── sections/     # Hero, Features, CTA
│   │   └── motion/       # RevealSection, StaggerGrid
│   ├── lib/
│   ├── styles/
│   └── app/              # Pages
└── package.json
```### 查看/Nuxt```
project/
├── public/assets/
├── src/                  # or root for Nuxt
│   ├── components/
│   │   ├── ui/
│   │   ├── sections/
│   │   └── motion/
│   ├── composables/      # Shared logic
│   ├── pages/
│   └── assets/           # Processed assets (optional)
└── package.json
```### 太空人```
project/
├── public/assets/
├── src/
│   ├── components/       # .astro, .tsx, .vue, .svelte
│   ├── layouts/
│   ├── pages/
│   └── styles/
└── package.json
```**组件命名：** PascalCase (`HeroSection.tsx`, `HeroSection.vue`, `HeroSection.astro`)

---

## 合规性

**此技能中的所有规则都是强制性的。违反任何规则都是阻塞错误 - 在继续或交付之前修复。**

---

## 工作流程
### 第一阶段：设计架构
1. 分析请求——确定页面类型和上下文
2. 根据页面类型设置设计表盘
3.规划布局部分并确定资产需求

### 第 2 阶段：运动架构
1. 选择每个部分的动画工具（参见工具选择矩阵）
2. 遵循性能护栏规划运动序列

### 第三阶段：资产生成
使用“scripts/”生成所有图像/视频/音频资源。切勿使用占位符 URL（unsplash、picsum、placeholder.com、via.placeholder、placehold.co 等）或外部 URL。

1.解析资产需求（类型、风格、规格、用途）
2.精心制作优化提示，展示给用户，确认后再生成
3. 通过脚本执行，保存到项目 — 在所有资源都保存到本地之前，不要继续进行第 5 阶段

### 第 4 阶段：文案写作和内容
遵循文案写作框架（AIDA、PAS、FAB）来制作所有文本内容。不要使用“Lorem ipsum”——写真实的副本。

### 第 5 阶段：构建 UI
按照设计和运动规则搭建项目并构建每个部分。集成生成的资产并复制。所有 `<img>`、`<video>`、`<source>` 和 CSS `background-image` 必须引用第 3 阶段的本地资源。

### 第 6 阶段：质量门
运行最终检查表（请参阅质量门部分）。

---

# 1. 设计工程

## 1.1 基线配置

|拨号|默认 |范围 |
|------|---------|--------|
|设计变量 | 8 | 1=对称，10=不对称 |
|运动强度 | 6 | 1=静态，10=动态 |
|视觉密度 | 4 | 1=通风，10=紧凑 |

根据用户请求动态调整。

## 1.2 架构约定
- **依赖验证：** 在导入任何库之前检查 `package.json`。如果缺少则输出安装命令。
- **框架：** React/Next.js。默认为服务器组件。交互组件必须是隔离的“使用客户端”叶组件。
- **样式：** Tailwind CSS。检查 `package.json` 中的版本 - 切勿混合 v3/v4 语法。
- **反表情符号政策：** 切勿在任何地方使用表情符号。仅使用 Phosphor 或 Radix 图标。
- **视口：** 使用 `min-h-[100dvh]` 而不是 `h-screen`。使用 CSS 网格而不是弹性百分比数学。
- **布局：** `max-w-[1400px] mx-auto` 或 `max-w-7xl`。

## 1.3 设计规则
|规则|指令|
|------|------------|
|版式|标题：“text-4xl md：text-6xl 跟踪更紧密”。正文：`基于文本的领先放松 max-w-[65ch]`。 **永远不要**使用Inter——使用Geist/Outfit/Satoshi。 **永远不要**在仪表板上使用衬线。 |
|颜色 |最多 1 种重音，饱和度 < 80%。 **切勿** 使用 AI 紫色/蓝色。坚持使用一个调色板。 |
|布局| **切勿** 当方差 > 4 时使用居中英雄。强制分屏或不对称布局。 |
|卡片 | **切勿** 当密度 > 7 时使用通用卡片。使用“border-t”、“divide-y”或间距。 |
|州 | **始终**实现：加载（骨架）、空、错误、触觉反馈（`scale-[0.98]`）。 |
|表格 |输入上方的标签。错误如下。输入块的“gap-2”。 |

## 1.4 防倾斜技术

- **液体玻璃：** `背景模糊` + `边框白色/10` + `阴影-[inset_0_1px_0_rgba(255,255,255,0.1)]`
- **磁性按钮：** 使用 `useMotionValue`/`useTransform` — 切勿使用 `useState` 来实现连续动画
- **永动机：**当强度> 5时，添加无限微动画（脉冲、浮动、闪光）
- **布局转换：** 使用 Framer `layout` 和 `layoutId` 属性
- **交错：**使用 `staggerChildren` 或 CSS `animation-delay: calc(var(--index) * 100ms)`

## 1.5 禁止模式
|类别 |禁止 |
|----------|--------|
|视觉 |霓虹灯发光、纯黑色 (#000)、过饱和强调色、标题上的渐变文本、自定义光标 |
|版式|仪表板上的 Inter 字体、超大 H1、衬线字体 |
|布局| 3 列相等的卡片行，带有尴尬间隙的浮动元素 |
|组件|默认shadcn/ui，无需定制|

## 1.6 创意军械库

|类别 |图案|
|----------|----------|
|导航 |底座放大、磁性按钮、粘性菜单、动态岛、径向菜单、快速拨号、超级菜单 |
|布局|便当网格、砖石、色度网格、分屏滚动、窗帘显示 |
|卡片 |视差倾斜、聚光灯边框、玻璃态、全息箔、滑动堆栈、变形模式 ||滚动 |粘性堆栈、水平劫持、机车序列、缩放视差、进度路径、液体滑动 |
|画廊 |圆顶画廊、Coverflow、拖动平移、手风琴滑块、悬停轨迹、故障效果 |
|文字|动态选取框、文本蒙版显示、乱序效果、圆形路径、渐变描边、动态网格 |
|微|粒子爆炸、拉动刷新、骨架闪光、定向悬停、波纹点击、SVG 绘制、网格渐变、镜头模糊 |

## 1.7 便当范式

- **调色板：**背景`#f9fafb`，卡片纯白色，带有`border-slate-200/50`
- **表面：** `rounded-[2.5rem]`，扩散阴影
- **排版：** Geist/Satoshi，“tracking-tight”标题
- **标签：** 外侧和下方卡片
- **动画：** 弹簧物理（`刚度：100，阻尼：20`），无限循环，`React.memo` 隔离

**5 张牌原型：**
1. 智能列表——通过`layoutId`自动排序
2.命令输入——打字机+闪烁光标
3. 实时状态——呼吸指示器
4.宽数据流——无限水平轮播
5. 上下文 UI — 交错突出显示 + 浮动工具栏

## 1.8 品牌覆盖

当品牌造型处于活动状态时：
- 深色：`#141413`，浅色：`#faf9f5`，中色：`#b0aea5`，微妙：`#e8e6dc`
- 口音：橙色`#d97757`，蓝色`#6a9bcc`，绿色`#788c5d`
- 字体：Poppins（标题）、Lora（正文）

---

# 2. 运动引擎

## 2.1 工具选择矩阵

|需要|工具|
|------|------|
| UI 进入/退出/布局 | **成帧器运动** — `AnimatePresence`、`layoutId`、弹簧 |
|滚动讲故事（别针、磨砂）| **GSAP + ScrollTrigger** — 帧精确控制 |
|循环图标| **Lottie** — 延迟加载 (~50KB) |
| 3D/WebGL | **Three.js / R3F** — 隔离`<Canvas>`，拥有`“使用客户端”边界 |
|悬停/焦点状态 | **仅 CSS** — 零 JS 成本 |
|原生滚动驱动 | **CSS** — `动画时间轴：scroll()` |

**冲突规则[强制]：**
- 切勿在同一组件中混合使用 GSAP + Framer Motion
- R3F 必须存在于隔离的 Canvas 包装中
- 始终延迟加载 Lottie、GSAP、Three.js

## 2.2 强度等级

|水平|技术|
|--------|------------|
| 1-2 微妙|仅 CSS 转换，150-300 毫秒 |
| 3-4 平滑 | CSS 关键帧 + Framer 动画，交错≤3 项 |
| 5-6 流体 | `whileInView`，磁悬停，视差倾斜 |
| 7-8 电影 | GSAP ScrollTrigger、固定部分、水平劫持 |
| 9-10 沉浸式 |完整滚动序列、Three.js 粒子、WebGL 着色器 |

## 2.3 动画配方

有关完整代码，请参阅“references/motion-recipes.md”。摘要：

|食谱|工具|用于 |
|--------|------|---------|
|滚动显示 |成帧器|视口入口处淡入淡出+滑动 |
|交错网格|成帧器|顺序列表动画 |
|固定时间线 | GSAP |带固定的水平滚动 |
|倾斜卡|成帧器|鼠标追踪 3D 视角 |
|磁性按钮|成帧器|光标吸引按钮 |
|文字打乱|香草|矩阵式解码效果|
| SVG 路径绘制 | CSS |滚动链接路径动画 |
|水平滚动| GSAP |垂直到水平劫持 |
|粒子背景| R3F |装饰WebGL粒子|
|布局变形|成帧器|卡到模式的扩展 |

## 2.4 性能规则
**仅限 GPU 的属性（仅对这些属性进行动画处理）：** `transform`、`opacity`、`filter`、`clip-path`

**切勿设置动画：** `width`、`height`、`top`、`left`、`margin`、`padding`、`font-size` — 如果您需要这些效果，请使用 `transform:scale()` 或 `clip-path` 代替。

**隔离：**
- 永久动画必须位于“React.memo”叶组件中
- 仅在动画期间`will-change：transform`
- 重型容器上的“包含：布局风格油漆”

**手机：**
- 始终尊重“偏好减少运动”
- 始终禁用“指针：粗略”上的视差/3D
- 上限颗粒：台式机800个、平板电脑300个、手机100个
- 在 < 768px 的移动设备上禁用 GSAP pin

**清理：** 每个具有 GSAP/观察者的 `useEffect` 必须 `return () => ctx.revert()`

## 2.5 弹簧和缓动

|感觉|成帧器配置 |
|------|----------------|
|敏捷 | `刚度：300，阻尼：30` |
|光滑| `刚度：150，阻尼：20` |
|弹性| `刚度：100，阻尼：10` |
|重| `刚度：60，阻尼：20` |

| CSS 缓动 |价值|
|------------|--------|
|平稳减速| `三次贝塞尔曲线(0.16, 1, 0.3, 1)` |
|平稳加速| `三次贝塞尔曲线(0.7, 0, 0.84, 0)` |
|弹性| `三次贝塞尔曲线(0.34, 1.56, 0.64, 1)` |

## 2.6 辅助功能
- 始终在“首选减少运动”检查中包裹运动
- 切勿闪烁内容 > 3 次/秒（癫痫风险）
- 始终提供可见的对焦环（使用“轮廓”而不是“盒子阴影”）- 始终添加 `aria-live="polite"` 以动态显示内容
- 始终包含用于自动播放动画的暂停按钮

## 2.7 依赖关系```bash
npm install framer-motion           # UI (keep at top level)
npm install gsap                    # Scroll (lazy-load)
npm install lottie-react            # Icons (lazy-load)
npm install three @react-three/fiber @react-three/drei  # 3D (lazy-load)
```---

# 3. 资产生成

## 3.1 脚本

|类型 |脚本 |图案|
|------|--------|---------|
|语音合成 | `scripts/minimax_tts.py` |同步|
|音乐| `scripts/minimax_music.py` |同步|
|视频 | `scripts/minimax_video.py` |异步（创建 → 轮询 → 下载）|
|图片| `scripts/minimax_image.py` |同步|

环境：`MINIMAX_API_KEY`（必需）。

## 3.2 工作流程
1. **解析：**类型、数量、款式、规格、用途
2. **工艺提示：** 具体（构图、灯光、风格）。 **切勿** 在图像提示中包含文本。
3. **执行：**向用户显示提示，**生成前必须确认**，然后运行脚本
4. **保存：** `<project>/public/assets/{images,videos,audio}/` as `{type}-{descriptor}-{timestamp}.{ext}` — **必须保存在本地**
5. **后处理：** 图片 → WebP，视频 → ffmpeg 压缩，音频 → 标准化
6. **交付：** 文件路径 + 代码片段 + CSS 建议

## 3.3 预设快捷键

|快捷方式 |规格|
|----------|------|
| `英雄` | 16:9，电影，文本安全 |
| `拇指` | 1:1，主体居中 |
| `图标` | 1:1，平坦，干净的背景 |
| `头像` | 1:1，肖像，圆形裁剪准备就绪 |
| `横幅` | 21:9，OG/社交 |
| `背景视频` | 768P、6s、`[静态镜头]` |
| `视频高清` | 1080P，6s |
| '背景音乐' | 30 多岁，没有人声，可循环 |
| `tts` | MiniMax 高清、MP3 |

## 3.4 参考

- `references/minimax-cli-reference.md` — CLI 标志
- `references/asset-prompt-guide.md` — 提示规则
- `references/minimax-voice-catalog.md` — 语音 ID
- `references/minimax-tts-guide.md` — TTS 用法
- `references/minimax-music-guide.md` — 音乐生成（提示、歌词、结构标签）
- `references/minimax-video-guide.md` — 相机命令
- `references/minimax-image-guide.md` — 比率、批次

---

# 4.文案写作

## 4.1 核心工作

1. 吸引注意力 → 2. 创造欲望 → 3. 消除摩擦 → 4. 迅速行动

## 4.2 框架

**AIDA**（登陆页面、电子邮件）：```
ATTENTION:  Bold headline (promise or pain)
INTEREST:   Elaborate problem ("yes, that's me")
DESIRE:     Show transformation
ACTION:     Clear CTA
```**PAS**（疼痛驱动产品）：```
PROBLEM:    State clearly
AGITATE:    Make urgent
SOLUTION:   Your product
```**FAB**（产品差异化）：```
FEATURE:    What it does
ADVANTAGE:  Why it matters
BENEFIT:    What customer gains
```## 4.3 标题

|公式|示例|
|---------|---------|
|承诺 | “30天内打开率翻倍”|
|问题 | “每周仍然浪费 10 个小时吗？” |
|操作方法 | “如何实现管道自动化”|
|数量 | “7 个错误导致转化率下降” |
|负面| “停止失去线索” |
|好奇心| “这一变化使预订量增加了两倍”|
|转型| “从 50 到 500 条线索” |

具体一点。以结果而非方法为主导。

## 4.4 号召性用语

**不好：** 提交，点击此处，了解更多

**好：**“开始免费试用”、“立即获取模板”、“预订我的策略通话”

**公式：** [动作动词] + [他们得到什么] + [紧急/轻松]

位置：折叠上方、值后、长页上的多个。

## 4.5 情绪触发因素

|触发|示例|
|---------|---------|
|错失恐惧症 | “仅剩3个名额”|
|害怕失去| “如果没有这个，你每天都会损失 X 美元”|
|状态 | “加入10,000+顶级机构”|
|轻松| “设置一次。永远忘记。” |
|沮丧| “厌倦了没有任何功能的工具？” |
|希望| “是的，您可以达到 10,000 美元的 MRR”|

## 4.6 异议处理

|反对|回应 |
|------------|----------|
|太贵了|显示投资回报率：“两周内收回成本”|
|对我不起作用 |来自类似客户的社会证明 |
|没有时间| “设置需要 10 分钟” |
|如果失败了怎么办 | “30 天退款保证”|
|需要思考|紧迫性/稀缺性|

放置在常见问题解答、推荐、CTA 附近。

## 4.7 证明类型

感言（带有姓名/头衔）、案例研究、数据/指标、社会证明、认证

---

#5.视觉艺术

哲学第一的工作流程。两种输出模式。

## 5.1 输出模式

|模式|输出|当 |
|------|--------|------|
|静态| PDF/PNG |海报、印刷品、设计资产 |
|互动| HTML (p5.js) |生成艺术，可探索的变化 |

## 5.2 工作流程

### 第 1 步：哲学创造
为该运动命名（1-2 个单词）。阐明哲学（4-6 段），涵盖：
- 静态：空间、形式、颜色、尺度、节奏、层次
- 交互式：计算、涌现、噪声、参数变化

### 第 2 步：概念种子
识别微妙的、利基的参考——复杂的，而不是字面的。爵士音乐家引用另一首歌。

### 第 3 步：创建

**静态模式：**
- 单页、高度视觉化、设计前卫
- 重复图案，完美形状
- 来自“canvas-fonts/”的稀疏排版
- 没有任何重叠，适当的边距
- 输出：`.pdf`或`.png`+哲学`.md`

**交互模式：**
1.首先阅读`templates/viewer.html`
2. 保留固定部分（标题、侧边栏、种子控件）
3.替换VARIABLE部分（算法、参数）
4. 种子随机性：`randomSeed(seed);噪音种子（种子）；`
5. 输出：单个独立的 HTML

### 步骤 4：细化
精炼，不要添加。使其酥脆。打磨成杰作。

---

# 质量门
**设计：**
- [ ] 针对高方差设计的移动布局折叠（`w-full`、`px-4`）
- [ ] `min-h-[100dvh]` 不是 `h-screen`
- [ ] 提供空、加载、错误状态
- [ ] 卡片在间距足够的情况下被省略

**运动：**
- [ ] 每个选择矩阵正确的工具
- [ ] 同一组件中不得混合 GSAP + Framer
- [ ] 所有`useEffect`都有清理返回
- [ ] 尊重“偏好减少运动”
- [ ] `React.memo` 叶组件中的永久动画
- [ ] 仅对 GPU 属性进行动画处理
- [ ] 重型库延迟加载

**一般：**
- [ ] 在 `package.json` 中验证依赖关系
- [ ] **没有占位符 URL** — grep 输出 `unsplash`、`picsum`、`placeholder`、`placehold`、`via.placeholder`、`lorem.space`、`dummyimage`。如果发现任何内容，请在交付之前停止并用生成的资产替换。
- [ ] **所有媒体资产都作为本地文件存在** 在项目的资产目录中
- [ ] 资产提示在生成前与用户确认

---

*React 和 Next.js 分别是 Meta Platforms, Inc. 和 Vercel, Inc. 的商标。 Vue.js 是 Evan You 的商标。 Tailwind CSS 是 Tailwind Labs Inc. 的商标。Svelte 和 SvelteKit 是其各自所有者的商标。 GSAP/GreenSock 是 GreenSock Inc. 的商标。Three.js、Framer Motion、Lottie、Astro 和所有其他产品名称是其各自所有者的商标。*