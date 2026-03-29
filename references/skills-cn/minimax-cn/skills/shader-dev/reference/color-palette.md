# 调色板和色彩空间技术 - 详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含分步教程、数学推导和高级用法。

## 先决条件

- GLSL基本语法：`vec3`、`mix`、`clamp`、`smoothstep`、`fract`、`mod`
- 三角函数`cos`/`sin`的基本性质（周期性，范围[-1, 1]）
- 色彩空间基础：RGB 是立方体，HSV/HSL 是柱坐标，Lab/Lch 是感知均匀空间
- 伽马校正概念：显示器存储 sRGB（非线性），着色计算应在线性空间中执行

## 分步教程

### 步骤 1：余弦调色板函数

**什么**：实现最基本、最常用的程序调色板功能

**为什么**：只需要 4 个 vec3 参数即可生成无限平滑的色带，计算成本极低（单个 cos 运算）。该函数在 ShaderToy 社区中广泛使用，是程序着色的基石。

**数学推导**：```
color(t) = a + b * cos(2pi * (c * t + d))
```- **a** = 亮度偏移（色带的中心亮度），通常约为 0.5
- **b** = 幅度（颜色对比度），通常约为 0.5
- **c** = 频率（每个通道振荡多少次），vec3(1,1,1) 表示R/G/B各振荡一次
- **d** = 相位偏移（每个通道的色调起始位置），这是控制颜色风格的关键参数

当a=b=0.5，c=(1,1,1)时，单独改变d会产生完全不同的颜色渐变，如彩虹、暖色调、冷色调等。

**代码**：```glsl
// Cosine Palette
// a: offset/center color, b: amplitude, c: frequency, d: phase
// t: input scalar, typically [0,1] but can exceed this range
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}
```### 步骤 2：经典参数预设

**什么**：提供即用型调色板参数

**为什么**：原始演示展示了 7 种经典参数组合，涵盖了彩虹、暖色、冷色和双色调方案等常见需求。记住一些参数集可以快速调整颜色。

**代码**：```glsl
// Rainbow color ramp (classic)
// a=(.5,.5,.5) b=(.5,.5,.5) c=(1,1,1) d=(0.0, 0.33, 0.67)

// Warm gradient
// a=(.5,.5,.5) b=(.5,.5,.5) c=(1,1,1) d=(0.0, 0.10, 0.20)

// Blue-purple to orange tones
// a=(.5,.5,.5) b=(.5,.5,.5) c=(1,0.7,0.4) d=(0.0, 0.15, 0.20)

// Custom warm-cool mix
// a=(.8,.5,.4) b=(.2,.4,.2) c=(2,1,1) d=(0.0, 0.25, 0.25)

// Simplified version: fix a/b/c, just adjust d
vec3 palette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.28318 * (c * t + d));
}
```### 步骤 3：HSV 到 RGB 转换（标准 + 平滑）

**内容**：实现无分支 HSV 到 RGB 的转换及其三次平滑变体

**为什么**：HSV 空间非常适合按色调旋转、按饱和度/值缩放。标准实现具有 C0 不连续性（分段线性）；平滑版本通过 Hermite 插值实现 C1 连续性，产生更平滑的色调动画。

**原理**：使用向量化 `mod` + `abs` + `clamp` 操作可以避免 if/else 分支：```
rgb = clamp(abs(mod(H*6 + vec3(0,4,2), 6) - 3) - 1, 0, 1)
```这本质上是使用分段线性函数来模拟 R/G/B 通道随色调 H 的变化。C1 不连续性可以通过三次平滑“rgb*rgb*(3-2*rgb)”来消除。

**代码**：```glsl
// Standard HSV -> RGB (branchless)
// c.x = Hue [0,1], c.y = Saturation [0,1], c.z = Value [0,1]
vec3 hsv2rgb(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return c.z * mix(vec3(1.0), rgb, c.y);
}

// Smooth HSV -> RGB (C1 continuous)
vec3 hsv2rgb_smooth(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    rgb = rgb * rgb * (3.0 - 2.0 * rgb); // Cubic Hermite smoothing
    return c.z * mix(vec3(1.0), rgb, c.y);
}
```### 步骤 4：HSL 到 RGB 转换

**什么**：实现 HSL 色彩空间转换

**为什么**：HSL比HSV更直观——L=0是黑色，L=1是白色，L=0.5是纯色。适用于需要控制“亮度”而不是“值”的场景（例如，将迭代计数映射到数据可视化中的色调）。

**代码**：```glsl
// Hue -> RGB base color (branchless)
vec3 hue2rgb(float h) {
    return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}

// HSL -> RGB
// h: Hue [0,1], s: Saturation [0,1], l: Lightness [0,1]
vec3 hsl2rgb(float h, float s, float l) {
    vec3 rgb = hue2rgb(h);
    return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}
```### 步骤 5：双向 RGB <-> HSV 转换

**什么**：实现从 RGB 到 HSV 的反向转换

**为什么**：在 HSV 空间中混合颜色时，您需要首先将两个端点颜色从 RGB 转换为 HSV，进行插值，然后再转换回来。 RGB 到 HSV 使用经典的无分支实现。

**代码**：```glsl
// RGB -> HSV (branchless method)
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
```### 步骤 6：CIE Lab/Lch 感知均匀插值

**内容**：实现完整的 RGB <-> Lab <-> Lch 转换管道

**原因**：RGB 和 HSV 空间中的线性插值在感知上并不均匀 - 人眼对绿色比红色更敏感。 Lch（亮度-色度-色调）空间中的插值可产生视觉上最自然的渐变，特别适合 UI 配色方案和艺术渐变。

**数学推导**：转换管道为 RGB -> XYZ（通过 sRGB D65 矩阵） -> Lab（通过非线性映射） -> Lch（通过将 a、b 转换为极坐标：色度、色调）。逆过程反转每一步。

**代码**：```glsl
// Helper function: XYZ nonlinear mapping
float xyzF(float t) { return mix(pow(t, 1.0/3.0), 7.787037 * t + 0.139731, step(t, 0.00885645)); }
float xyzR(float t) { return mix(t * t * t, 0.1284185 * (t - 0.139731), step(t, 0.20689655)); }

// RGB -> Lch (via XYZ -> Lab -> polar coordinates)
vec3 rgb2lch(vec3 c) {
    // RGB -> XYZ (sRGB D65 matrix)
    c *= mat3(0.4124, 0.3576, 0.1805,
              0.2126, 0.7152, 0.0722,
              0.0193, 0.1192, 0.9505);
    // XYZ -> Lab
    c = vec3(xyzF(c.x), xyzF(c.y), xyzF(c.z));
    vec3 lab = vec3(max(0.0, 116.0 * c.y - 16.0),
                    500.0 * (c.x - c.y),
                    200.0 * (c.y - c.z));
    // Lab -> Lch (convert a,b to polar: Chroma, Hue)
    return vec3(lab.x, length(lab.yz), atan(lab.z, lab.y));
}

// Lch -> RGB (inverse process)
vec3 lch2rgb(vec3 c) {
    // Lch -> Lab
    c = vec3(c.x, cos(c.z) * c.y, sin(c.z) * c.y);
    // Lab -> XYZ
    float lg = (1.0 / 116.0) * (c.x + 16.0);
    vec3 xyz = vec3(xyzR(lg + 0.002 * c.y),
                    xyzR(lg),
                    xyzR(lg - 0.005 * c.z));
    // XYZ -> RGB (inverse matrix)
    return xyz * mat3( 3.2406, -1.5372, -0.4986,
                      -0.9689,  1.8758,  0.0415,
                       0.0557, -0.2040,  1.0570);
}

// Circular hue interpolation (avoids 0/360 degree wraparound jump)
float lerpAngle(float a, float b, float x) {
    float ang = mod(mod((a - b), 6.28318) + 9.42477, 6.28318) - 3.14159;
    return ang * x + b;
}

// Lch space linear interpolation
vec3 lerpLch(vec3 a, vec3 b, float x) {
    return vec3(mix(b.xy, a.xy, x), lerpAngle(a.z, b.z, x));
}
```### 步骤 7：sRGB Gamma 和线性空间工作流程

**内容**：实现正确的 sRGB 编码/解码功能和完整的线性空间管道

**为什么**：所有照明/混合计算必须在线性空间中执行。 sRGB 纹理需要首先解码（pow 2.2 或精确分段函数），然后在计算后编码回 sRGB。忽略此步骤会导致颜色显得太暗且混合不自然。

**完整管道**：sRGB 纹理解码 -> 线性空间着色/混合 -> Reinhard 色调图 -> sRGB 编码

**代码**：```glsl
// Exact sRGB encode (linear -> sRGB)
float sRGB_encode(float t) {
    return mix(1.055 * pow(t, 1.0/2.4) - 0.055, 12.92 * t, step(t, 0.0031308));
}
vec3 sRGB_encode(vec3 c) {
    return vec3(sRGB_encode(c.x), sRGB_encode(c.y), sRGB_encode(c.z));
}

// Fast approximation (sufficient for most scenarios)
// Decode: pow(color, vec3(2.2))
// Encode: pow(color, vec3(1.0/2.2))

// Reinhard tone mapping (maps HDR values to [0,1])
vec3 tonemap_reinhard(vec3 col) {
    return col / (1.0 + col);
}
```### 步骤 8：黑体辐射调色板

**什么**：实现基于物理的温度到颜色映射

**为什么**：用于火、熔岩、星星、热金属和其他需要物理真实发射颜色的场景。比手动颜色调整更可信，具有直观的参数化（输入只是温度）。

**数学推导**：通过普朗克轨迹近似将温度 T 映射到 CIE 色度坐标 (cx, cy)，然后转换为 XYZ -> RGB，结合 Stefan-Boltzmann 定律 (T^4) 亮度缩放以产生物理上真实的发射颜色。

**代码**：```glsl
// Blackbody radiation palette
// t: normalized temperature [0,1], internally mapped to [0, TEMP_MAX] Kelvin
#define TEMP_MAX 4000.0 // Tunable: maximum temperature (K), affects color gamut width
vec3 blackbodyPalette(float t) {
    t *= TEMP_MAX;
    // Planck locus approximation on CIE chromaticity diagram
    float cx = (0.860117757 + 1.54118254e-4 * t + 1.28641212e-7 * t * t)
             / (1.0 + 8.42420235e-4 * t + 7.08145163e-7 * t * t);
    float cy = (0.317398726 + 4.22806245e-5 * t + 4.20481691e-8 * t * t)
             / (1.0 - 2.89741816e-5 * t + 1.61456053e-7 * t * t);
    // CIE chromaticity coordinates -> XYZ tristimulus values
    float d = 2.0 * cx - 8.0 * cy + 4.0;
    vec3 XYZ = vec3(3.0 * cx / d, 2.0 * cy / d, 1.0 - (3.0 * cx + 2.0 * cy) / d);
    // XYZ -> sRGB matrix
    vec3 RGB = mat3(3.240479, -0.969256, 0.055648,
                   -1.537150,  1.875992, -0.204043,
                   -0.498535,  0.041556,  1.057311) * vec3(XYZ.x / XYZ.y, 1.0, XYZ.z / XYZ.y);
    // Stefan-Boltzmann brightness scaling (T^4)
    return max(RGB, 0.0) * pow(t * 0.0004, 4.0);
}
```## 变体详细说明

### 变体 1：多谐波余弦调色板（抗锯齿）

**与基础版本的区别**：将单个cos扩展到9层不同频率，以获得更丰富的色彩细节；使用“fwidth()”进行带限滤波，以防止高频混叠。

**原理**：`fwidth()`返回相邻像素之间的变化。当振荡频率超过像素分辨率（即 w 接近或超过一个完整的 TAU 周期）时，“smoothstep”将 cos 贡献衰减至 0，从而实现近似 sinc 滤波。

**完整代码**：```glsl
// Band-limited cos: automatically attenuates when oscillation frequency exceeds pixel resolution
vec3 fcos(vec3 x) {
    vec3 w = fwidth(x);
    return cos(x) * smoothstep(TAU, 0.0, w); // Approximate sinc filtering
}

// 9-layer stacked palette
vec3 getColor(float t) {
    vec3 col = vec3(0.4);
    col += 0.12 * fcos(TAU * t *   1.0 + vec3(0.0, 0.8, 1.1));
    col += 0.11 * fcos(TAU * t *   3.1 + vec3(0.3, 0.4, 0.1));
    col += 0.10 * fcos(TAU * t *   5.1 + vec3(0.1, 0.7, 1.1));
    col += 0.09 * fcos(TAU * t *   9.1 + vec3(0.2, 0.8, 1.4));
    col += 0.08 * fcos(TAU * t *  17.1 + vec3(0.2, 0.6, 0.7));
    col += 0.07 * fcos(TAU * t *  31.1 + vec3(0.1, 0.6, 0.7));
    col += 0.06 * fcos(TAU * t *  65.1 + vec3(0.0, 0.5, 0.8));
    col += 0.06 * fcos(TAU * t * 115.1 + vec3(0.1, 0.4, 0.7));
    col += 0.09 * fcos(TAU * t * 265.1 + vec3(1.1, 1.4, 2.7));
    return col;
}
```### 变体 2：哈希驱动的每图块颜色变化

**与基础版本的区别**：使用哈希函数为每个网格/图块生成唯一的 ID，将 ID 作为调色板的 t 值提供，以实现“调色板相同但每个图块颜色不同”。

**用例**：程序瓷砖/砖砌体/马赛克、Voronoi 单元着色、建筑外墙。

**完整代码**：```glsl
// Hash function (sin-free version, avoids precision issues)
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// Usage in tile coloring
vec2 tileId = floor(uv);
vec3 tileColor = palette(hash12(tileId)); // Different color per tile
```### 变体 3：保留饱和度的改进 RGB 插值

**与基本版本的差异**：检测 RGB 空间插值期间的饱和度衰减，并将颜色移离灰色对角线，以非常低的成本（约 15 条指令）实现近似感知均匀的插值。

**原理**：
1. 计算RGB线性插值结果`ic`
2. 计算预期饱和度`mix(getsat(a), getsat(b), x)`和实际饱和度`getsat(ic)`之间的差异
3.找到远离灰色对角线`dir`的方向
4. 补偿沿该方向的饱和度损失

**完整代码**：```glsl
float getsat(vec3 c) {
    float mi = min(min(c.x, c.y), c.z);
    float ma = max(max(c.x, c.y), c.z);
    return (ma - mi) / (ma + 1e-7);
}

vec3 iLerp(vec3 a, vec3 b, float x) {
    vec3 ic = mix(a, b, x) + vec3(1e-6, 0.0, 0.0);
    float sd = abs(getsat(ic) - mix(getsat(a), getsat(b), x));
    vec3 dir = normalize(vec3(2.0*ic.x - ic.y - ic.z,
                              2.0*ic.y - ic.x - ic.z,
                              2.0*ic.z - ic.y - ic.x));
    float lgt = dot(vec3(1.0), ic);
    float ff = dot(dir, normalize(ic));
    ic += 1.5 * dir * sd * ff * lgt; // 1.5 = DSP_STR, tunable
    return clamp(ic, 0.0, 1.0);
}
```### 变体 4：圆形色调插值（HSV/Lch 空间）

**与基本版本的区别**：在具有圆形色调维度的色彩空间中进行插值时，必须处理从 0.9 到 0.1 穿过 1.0/0.0 的色调环绕，否则插值将采取“漫长的方式”（例如，红色 -> 洋红色 -> 蓝色 -> 青色 -> 绿色 -> 黄色 -> 红色，而不是直接红色 -> 橙色 -> 黄色）。

**完整代码**：```glsl
// HSV space circular hue interpolation (hue range [0,1])
vec3 lerpHSV(vec3 a, vec3 b, float x) {
    float hue = (mod(mod((b.x - a.x), 1.0) + 1.5, 1.0) - 0.5) * x + a.x;
    return vec3(hue, mix(a.yz, b.yz, x));
}

// Lch space circular hue interpolation (hue range [0, 2pi])
float lerpAngle(float a, float b, float x) {
    float ang = mod(mod((a - b), TAU) + PI * 3.0, TAU) - PI;
    return ang * x + b;
}
```### 变体 5：附加颜色叠加（发光/HDR 效果）

**与基础版本的区别**：不是选择单一颜色，而是从多次迭代中叠加叠加调色板颜色，产生自然的 HDR 发光效果。需要色调映射。

**用例**：分形发光、光晕、激光效果、粒子系统、体积光。

**完整代码**：```glsl
vec3 finalColor = vec3(0.0);
for (int i = 0; i < 4; i++) {
    vec3 col = palette(length(uv) + float(i) * 0.4 + iTime * 0.4);
    float glow = pow(0.01 / abs(sdfValue), 1.2); // Inverse-distance glow
    finalColor += col * glow; // Additive stacking, naturally produces HDR
}
finalColor = finalColor / (1.0 + finalColor); // Reinhard tonemap
```## 性能优化详情

### 1. 无分支 HSV/HSL 转换
使用向量化 `mod`/`abs`/`clamp` 操作而不是 if-else。上述所有实现都已经是无分支的。分支在 GPU 上的成本很高（尤其是扭曲/波前内的发散分支）；无分支版本确保所有线程遵循相同的执行路径。

### 2. 多谐波调色板的带限滤波
高频 cos 层会在一定距离或小角度处产生莫尔图案。使用“fwidth()”+“smoothstep”进行自动衰减只需约 2 条额外指令即可消除混叠。 `fwidth()` 以几乎零成本利用硬件偏导数计算。

### 3.Lch管道成本分析
完整的 RGB -> XYZ -> Lab -> Lch 管道需要约 57 条指令，包括矩阵乘法、pow、atan 等。如果您只需要“比 RGB 稍好”插值，请使用“iLerp”（改进的 RGB，约 15 条指令）而不是完整的 Lch 管道，以获得出色的质量/性能比。

### 4. sRGB 伽玛近似
精确的分段线性 sRGB 转换需要分支。在大多数视觉场景中，“pow(c, 2.2)”/“pow(c, 1.0/2.2)”足够准确（误差 < 0.4%），并且允许更好的编译器优化。确切的版本使用“mix”+“step”进行无分支实现，但需要一些额外的指令。

### 5. 余弦调色板矢量化
`a + b * cos(TAU*(c*t+d))` 在 GPU 上编译为 1 MAD + 1 COS + 1 MAD，大约需要 3-4 个时钟周期，效率极高。所有三个通道 (R/G/B) 通过 SIMD 并行执行。

### 6. 纹理 sRGB 解码
如果纹理数据已存储为 sRGB，请在计算前使用 pow(texture(...).rgb, vec3(2.2)) 解码到线性空间，避免非线性空间中光照造成的颜色失真。在OpenGL/Vulkan中，您还可以使用`GL_SRGB8_ALPHA8`格式进行自动硬件解码。

## 详细组合建议

### 1.余弦调色板 + SDF Raymarching
最经典的组合。使用光线行进击中点的法线方向、距离或表面属性作为调色板 t 输入，产生丰富的表面着色。

**例子**：```glsl
// After SDF raymarching hit
vec3 nor = calcNormal(pos);
float t_palette = dot(nor, vec3(0.0, 1.0, 0.0)) * 0.5 + 0.5; // Normal y-component mapped to [0,1]
vec3 col = palette(t_palette + iTime * 0.1);
```### 2. HSL/HSV + 数据可视化
将迭代计数、距离值或梯度方向映射到色调 (H)，通过饱和度/亮度对其他维度进行编码。例如，使用不同的色调来标记 SDF 轨迹可视化中的每个步骤。

**例子**：```glsl
// Mandelbrot iteration coloring
float h = float(iterations) / float(maxIterations);
vec3 col = hsl2rgb(h, 0.8, 0.5);
```### 3. 余弦调色板 + 分形/噪声
使用“length(uv)”或“fbm(p)”输出加上“iTime”作为t，结合加法堆叠和反距离发光，产生迷幻的动态色彩效果。

**例子**：```glsl
float n = fbm(uv * 3.0 + iTime * 0.2);
vec3 col = palette(n + length(uv) * 0.5);
```### 4.黑体调色板+体积渲染/火
通过“blackbodyPalette()”将温度场（噪声驱动或物理模拟）映射到颜色，产生物理上合理的火焰、熔岩和恒星效果。

**例子**：```glsl
// In fire volume rendering
float temperature = fbm(pos * 2.0 - vec3(0, iTime, 0)); // Noise-driven temperature field
vec3 fireColor = blackbodyPalette(temperature);
fireColor = tonemap_reinhard(fireColor); // HDR -> LDR
```### 5.线性空间工作流程+任何调色板技术
无论使用哪种调色板方法，始终遵循：sRGB 纹理解码 -> 线性空间着色/混合 -> Reinhard 色调图 -> sRGB 编码作为完整的管道，确保物理上正确的颜色计算。

**完整的管道示例**：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // 1. Decode sRGB texture to linear space
    vec3 texColor = pow(texture(iChannel0, uv).rgb, vec3(2.2));

    // 2. Perform all shading computations in linear space
    vec3 col = texColor * lighting;
    col += palette(t) * emission;

    // 3. Tone mapping (HDR -> LDR)
    col = col / (1.0 + col);

    // 4. sRGB encode
    col = pow(col, vec3(1.0/2.2));

    fragColor = vec4(col, 1.0);
}
```### 6.哈希+调色板+平铺系统
在程序瓷砖/砖砌/马赛克中，使用“hash(tileID)”作为调色板输入，以便每个瓷砖具有不同的颜色，同时保持整体协调的配色方案。

**完整示例**：```glsl
vec2 tileUV = fract(uv * 10.0);
vec2 tileID = floor(uv * 10.0);

// Base color per tile
float h = hash12(tileID);
vec3 tileColor = palette(h);

// Internal tile pattern (e.g., circle)
float d = length(tileUV - 0.5);
float mask = smoothstep(0.4, 0.38, d);

vec3 col = mix(vec3(0.05), tileColor, mask);
```
