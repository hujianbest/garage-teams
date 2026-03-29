---
名称：着色器开发
描述：用于创建令人惊叹的视觉效果的综合 GLSL 着色器技术 - 光线行进、SDF 建模、流体模拟、粒子系统、程序生成、照明、后处理等。
许可证：麻省理工学院
元数据：
  版本：“1.0”
  类别：图形
---

# 着色工艺

涵盖 36 种 GLSL 着色器技术（兼容 ShaderToy）的统一技能，可实现实时视觉效果。

## 调用```
/shader-dev <request>
````$ARGUMENTS` 包含用户的请求（例如“创建具有软阴影的光线行进 SDF 场景”）。

## 技能结构```
shader-dev/
├── SKILL.md                      # Core skill (this file)
├── techniques/                   # Implementation guides (read per routing table)
│   ├── ray-marching.md           # Sphere tracing with SDF
│   ├── sdf-3d.md                 # 3D signed distance functions
│   ├── lighting-model.md         # PBR, Phong, toon shading
│   ├── procedural-noise.md       # Perlin, Simplex, FBM
│   └── ...                       # 34 more technique files
└── reference/                    # Detailed guides (read as needed)
    ├── ray-marching.md           # Math derivations & advanced patterns
    ├── sdf-3d.md                 # Extended SDF theory
    ├── lighting-model.md         # Lighting math deep-dive
    ├── procedural-noise.md       # Noise function theory
    └── ...                       # 34 more reference files
```## 如何使用

1. 阅读下面的**技术路由表**，以确定哪些技术符合用户的请求
2. 从“techniques/”中阅读相关文件——每个文件包含核心原理、实现步骤和完整的代码模板
3. 如果您需要更深入的理解（数学推导、高级模式），请点击每个技术文件底部的参考链接到“参考/”
4. 生成独立 HTML 页面时应用下面的 **WebGL2 适配规则**

## 技术路由表

|用户想要创建... |初级技术|与 | 结合
|---|---|---|
|数学中的 3D 对象/场景 | [光线行进](技术/ray-marching.md) + [sdf-3d](技术/sdf-3d.md) |光照模型、阴影技术|
|复杂的 3D 形状（布尔值、混合）| [csg-boolean-operations](技术/csg-boolean-operations.md) | sdf-3d，射线行进|
| 3D 无限重复图案 | [域重复](技术/域重复.md) | sdf-3d，射线行进|
|有机/扭曲形状| [域扭曲](技术/域扭曲.md) |程序噪声 |
|流体/烟雾/墨水效果| [流体模拟](技术/流体模拟.md) |多通道缓冲区 |
|粒子效果（火、火花、雪）| [粒子系统](技术/粒子系统.md) |程序噪声、调色板 |
|基于物理的模拟 | [模拟物理](技术/模拟物理.md) |多通道缓冲区 |
|生命游戏/反应扩散| [元胞自动机](技术/元胞自动机.md) |多通道缓冲区、调色板 |
|海洋/水面| [水-海洋](技术/water-ocean.md) |大气散射、照明模型 |
|地形/景观| [地形渲染](技术/地形渲染.md) |大气散射、程序噪声 |
|云/雾/体积火| [体积渲染](技术/体积渲染.md) |程序噪声、大气散射 |
|天空/日落/气氛| [大气散射](技术/大气散射.md) |体积渲染|
|真实光照（PBR、Phong）| [照明模型](技术/照明模型.md) |阴影技术、环境光遮挡 |
|阴影（软/硬）| [阴影技术](技术/阴影技术.md) |照明模型 |
|环境遮挡| [环境遮挡](技术/环境遮挡.md) |照明模型，正常估计 |
|路径追踪/全局照明| [路径跟踪-gi](技术/路径跟踪-gi.md) |分析光线追踪、多通道缓冲区 |
|精确的射线几何相交 | [分析光线追踪](技术/分析光线追踪.md) |照明模型 |
|体素世界（我的世界风格）| [体素渲染](技术/体素渲染.md) |光照模型、阴影技术|
|噪声/FBM 纹理 | [程序噪声](技术/程序噪声.md) |域扭曲 |
|平铺 2D 图案 | [程序-2d-模式](技术/程序-2d-pattern.md) |极紫外操纵 |
| Voronoi / 单元模式 | [voronoi-cellular-noise](techniques/voronoi-cellular-noise.md) |调色板 |
|分形（Mandelbrot、Julia、3D）| [分形渲染](技术/分形渲染.md) |调色板，极紫外操纵 |
|颜色分级/调色板| [调色板](技术/color-palette.md) | — |
| Bloom/色调映射/故障| [后处理](技术/post-processing.md) |多通道缓冲区 |
|多通道乒乓缓冲器| [multipass-buffer](技术/multipass-buffer.md) | — |
|纹理/采样技术| [纹理采样](技术/纹理采样.md) | — |
|相机/矩阵变换| [矩阵变换](技术/矩阵变换.md) | — |
|表面法线 | [正态估计](技术/正态估计.md) | — |
|极坐标/万花筒| [极紫外操纵](技术/极紫外操纵.md) |程序二维模式 |
| SDF 的 2D 形状/UI | [sdf-2d](技术/sdf-2d.md) |调色板 |
|程序音频/音乐| [声音合成](techniques/sound-synthesis.md) | — |
| SDF 技巧/优化 | [sdf-tricks](技术/sdf-tricks.md) | sdf-3d，射线行进|
|抗锯齿渲染 | [抗锯齿](技术/抗锯齿.md) | sdf-2d，后处理|
|景深/运动模糊/镜头效果| [相机效果](技术/相机效果.md) |后处理、多通道缓冲区 |
|高级纹理映射/无平铺纹理| [纹理映射高级](技术/纹理映射-advanced.md) |地形渲染、纹理采样 || WebGL2 着色器错误/调试 | [webgl-pitfalls](技术/webgl-pitfalls.md) | — |

## 技术指标

### 几何和 SDF
- **sdf-2d** — 用于形状、UI、抗锯齿渲染的 2D 有符号距离函数
- **sdf-3d** — 用于实时隐式表面建模的 3D 有符号距离函数
- **csg-boolean-operations** — 构造实体几何：并集、减法、平滑混合的交集
- **domain-repetition** — 无限空间重复、折叠和有限平铺
- **域扭曲** — 使用噪声扭曲域以获得有机、流动的形状
- **sdf-tricks** — SDF 优化、包围体、二分搜索细化、挖空、分层边缘、调试可视化

### 光线投射和照明
- **光线行进** — 使用 SDF 进行球体追踪以进行 3D 场景渲染
- **分析射线追踪** - 封闭形式射线基元相交（球体、平面、盒子、环面）
- **path-tracing-gi** — 用于逼真全局照明的蒙特卡罗路径追踪
- **光照模型** — Phong、Blinn-Phong、PBR (Cook-Torrance) 和卡通着色
- **阴影技术** - 硬阴影、软阴影（半影估计）、级联阴影
- **环境光遮挡** — 基于 SDF 的 AO，屏幕空间 AO 近似
- **正态估计** - 有限差分法线，四面体技术

### 模拟与物理
- **流体模拟** — 具有平流、扩散、压力投影功能的纳维-斯托克斯流体求解器
- **模拟物理** — 基于 GPU 的物理：弹簧、布料、N 体重力、碰撞
- **粒子系统** — 无状态和有状态粒子系统（火、雨、火花、星系）
- **细胞自动机** — 生命游戏、反应扩散（图灵模式）、沙子模拟

### 自然现象
- **水-海洋** — Gerstner 波、FFT 海洋、焦散、水下雾
- **地形渲染** — Heightfield 光线行进、FBM 地形、侵蚀
- **大气散射** — 瑞利/米氏散射、上帝射线、SSS 近似
- **体积渲染** — 云、雾、火、爆炸的体积光线行进

### 程序生成
- **程序噪声** — 值噪声、Perlin、Simplex、Worley、FBM、脊状噪声
- **程序二维图案** — 砖块、六边形、truchet、伊斯兰几何图案
- **voronoi-cellular-noise** — Voronoi 图、Worley 噪声、破裂的地球、水晶
- **分形渲染** — Mandelbrot、Julia 集、3D 分形（Mandelbox、Mandelbulb）
- **调色板** — 余弦调色板、HSL/HSV/Oklab、动态颜色映射

### 后处理和基础设施
- **后处理** — Bloom、色调映射（ACES、Reinhard）、晕影、色差、毛刺
- **multipass-buffer** — 乒乓 FBO 设置，跨帧状态持久性
- **纹理采样** — 双线性、双三次、mipmap、程序纹理查找
- **矩阵变换** — 相机观察、投影、旋转、轨道控制
- **极紫外操纵** — 极/对数极坐标、万花筒、螺旋映射
- **抗锯齿** — SSAA、SDF 分析 AA、时间抗锯齿 (TAA)、FXAA 后处理
- **相机效果** — 景深（薄镜头）、运动模糊、镜头畸变、胶片颗粒、晕影
- **纹理映射高级** — 双平面映射、纹理重复避免、光线差分过滤

### 音频
- **声音合成** — GLSL 中的程序音频：振荡器、包络、滤波器、FM 合成

### 调试和验证
- **webgl-pitfalls** — 常见的 WebGL2/GLSL 错误：`fragCoord`、`main()` 包装器、函数顺序、宏限制、统一 null

## WebGL2适配规则

所有技术文件都使用ShaderToy GLSL风格。生成独立 HTML 页面时，请应用以下调整：

### 着色器版本和输出
- 使用`canvas.getContext("webgl2")`
- 着色器第一行：“#version 300 es”，片段着色器添加“ precision highp float;”
- 片段着色器必须声明：`out vec4 fragColor;`
- 顶点着色器：`attribute`→`in`、`variing`→`out`
- 片段着色器：`variing`→`in`、`gl_FragColor`→`fragColor`、`texture2D()`→`texture()`

### 片段坐标
- **使用`gl_FragCoord.xy`**代替`fragCoord`（WebGL2没有内置`fragCoord`）```glsl
// WRONG
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
// CORRECT
vec2 uv = (2.0 * gl_FragCoord.xy - iResolution.xy) / iResolution.y;
```### ShaderToy 模板的 main() 包装器
- ShaderToy 使用 `void mainImage(out vec4 fragColor, in vec2 fragCoord)`
- WebGL2 需要标准 `void main()` 入口点 — 始终包装 mainImage：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // shader code...
    fragColor = vec4(col, 1.0);
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}
```### 函数声明顺序
- GLSL 要求函数在使用前声明——要么在使用前声明，要么重新排序：```glsl
// WRONG — getAtmosphere() calls getSunDirection() before it's defined
vec3 getAtmosphere(vec3 dir) { return getSunDirection(); } // Error!
vec3 getSunDirection() { return normalize(vec3(1.0)); }

// CORRECT — define callee first
vec3 getSunDirection() { return normalize(vec3(1.0)); }
vec3 getAtmosphere(vec3 dir) { return getSunDirection(); } // Works
```### 宏限制
- `#define` 不能使用函数调用 — 使用 `const` 代替：```glsl
// WRONG
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6))

// CORRECT
const vec3 SUN_DIR = vec3(0.756, 0.378, -0.567); // Pre-computed normalized value
```### 脚本标签提取
- 从“<script>”标签提取着色器源时，确保“#version”是**第一个字符** - 使用“.trim()”：```javascript
const fs = document.getElementById('fs').text.trim();
```### 常见陷阱
- **未使用的制服**：编译器可能会优化掉未使用的制服，导致`gl.getUniformLocation()`返回`null` - 始终以编译器无法优化的方式使用制服
- **循环索引**：在循环中使用运行时常量，而不是某些 ES 版本中的“#define”宏
- **地形函数**：像 `terrainM(vec2)` 这样的函数需要 XZ 分量 - 使用 `terrainM(pos.xz + offset)` 而不是 `terrainM(pos + offset)`

## HTML 页面设置

生成独立 HTML 页面时：

- 画布填充整个视口，在窗口大小调整时自动调整大小
- 页面背景黑色，无滚动条：`body { margin: 0;溢出：隐藏；背景：#000； }`
- 实现与 ShaderToy 兼容的制服：`iTime`、`iResolution`、`iMouse`、`iFrame`
- 对于多通道效果（缓冲区 A/B），请使用 WebGL2 帧缓冲区 + 乒乓球（请参阅多通道缓冲区技术）

## 常见陷阱

### JS 变量声明顺序（TDZ — 导致白屏崩溃）

`let`/`const` 变量必须在 `<script>` 块的 **top** 声明，位于任何引用它们的函数之前：```javascript
// 1. State variables FIRST
let frameCount = 0;
let startTime = Date.now();

// 2. Canvas/GL init, shader compile, FBO creation
const canvas = document.getElementById('canvas');
const gl = canvas.getContext('webgl2');
// ...

// 3. Functions and event bindings LAST
function resize() { /* can now safely reference frameCount */ }
function render() { /* ... */ }
window.addEventListener('resize', resize);
```原因：`let`/`const` 有一个临时死区 - 在声明之前引用它们会抛出 `ReferenceError`，导致白屏。

### GLSL编译错误（编写shader后自检）

- **函数签名不匹配**：调用必须与参数计数和类型中的定义完全匹配。如果定义为“float fbm(vec3 p)”，则无法使用“vec2”调用“fbm(uv)”
- **保留字作为变量名**：不要使用：`patch`、`cast`、`sample`、`filter`、`input`、`output`、`common`、`partition`、`active`
- **严格类型匹配**：`vec3 x = 1.0`是非法的——使用`vec3 x = vec3(1.0)`；无法使用“.z”访问“vec2”
- **结构上没有三元**：ESSL 不允许在结构类型上使用三元运算符 - 使用 `if`/`else` 代替

### 绩效预算

部署环境可以使用 GPU 功率有限的无头软件渲染。保持在这些限制之内：

- 射线行进主循环：≤ 128 步
- 体积采样/照明内循环：≤ 32 步
- FBM倍频程：≤6层
- 每个像素的嵌套循环迭代总数：≤ 1000（超过此值会冻结浏览器）

## 快速食谱

通用效果组合——由技术模块组装而成的完整渲染管道。

### 逼真的 SDF 场景
1. **几何**：sdf-3d（扩展基元）+ csg-boolean-operations（三次/四次 smin）
2. **渲染**：光线行进+法线估计（四面体法）
3. **Lighting**：lighting-model（室外三灯模型）+shadow-techniques（改进的软阴影）+ambient-occlusion
4. **大气**：大气散射（基于高度的雾，带有阳光色调）
5. **后期**：后期处理（ACES 色调映射）+ 抗锯齿（2x SSAA）+ 相机效果（晕影）

### 有机/生物形式
1. **几何**：sdf-3d（扩展基元+变形运算符：扭曲、弯曲）+ csg-boolean（用于材质混合的梯度感知 smin）
2. **细节**：程序噪声（带有导数的FBM）+域扭曲
3. **表面**：光照模型（通过半朗伯的次表面散射近似）

### 程序景观
1. **地形**：地形渲染+程序噪声（带有导数的侵蚀FBM）
2. **纹理**：纹理映射高级（双平面映射+无平铺）
3. **天空**：大气散射（瑞利/米氏 + 高度雾）
4. **水**：水-海洋（格斯特纳波）+照明模型（菲涅耳反射）

### 风格化 2D 艺术
1. **形状**：sdf-2d（扩展库）+ sdf-tricks（分层边缘、空心）
2. **颜色**：调色板（余弦调色板）+极坐标紫外线操纵（万花筒）
3. **抛光**：抗锯齿（SDF解析AA）+后处理（光晕、色差）

## 着色器调试技巧

可视化调试方法 - 暂时替换您的输出以诊断问题。

|检查什么 |代码|寻找什么 |
|---|---|---|
|表面法线 | `col =nor * 0.5 + 0.5;` |平滑的梯度=正确的法线；带状 = epsilon 太大 |
|雷行军步数 | `col = vec3(float(steps) / float(MAX_STEPS));` |红色热点=性能瓶颈；统一=浪费迭代|
|深度/距离| `col = vec3(t / MAX_DIST);` |验证正确的击球距离 |
|紫外线坐标| `col = vec3(uv, 0.0);` |检查坐标映射 |
| SDF 距离场 | `col = (d > 0.0 ? vec3(0.9,0.6,0.3) : vec3(0.4,0.7,0.85)) * (0.8 + 0.2*cos(150.0*d));` |可视化 SDF 频带和过零 |
|格子图案（UV）| `col = vec3(mod(floor(uv.x*10.)+floor(uv.y*10.), 2.0));` |验证 UV 变形、接缝 |
|仅照明| `col = vec3(shadow);` 或 `col = vec3(ao);` |隔离阴影/AO 贡献 |
|材料编号 | `col = 调色板(matId / maxMatId);` |验证材料分配 |