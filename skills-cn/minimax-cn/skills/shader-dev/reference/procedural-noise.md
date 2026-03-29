# 程序噪声——详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含分步教程、数学推导和高级用法。

## 先决条件

- **GLSL 基础**：统一、变化、内置函数（`fract`、`floor`、`mix`、`smoothstep`、`dot`、`sin`/`cos`）
- **矢量数学**：点积、叉积、矩阵乘法（`mat2` 旋转矩阵）
- **坐标空间**：UV坐标归一化，屏幕纵横比校正
- **插值理论**：线性插值、Hermite插值 `3t^2-2t^3` (smoothstep)
- **ShaderToy 环境**：`iTime`、`iResolution`、`fragCoord`、`mainImage` 签名

## 详细用例

程序噪声是实时 GPU 图形中最基本、最通用的技术，适用于：

- **自然现象模拟**：火、云、水面、熔岩、闪电、烟雾等。
- **地形生成**：山脉、峡谷、侵蚀景观、雪线分布
- **纹理合成**：大理石纹理、木纹、有机图案、抽象艺术
- **体积渲染**：体积云、体积雾、光散射
- **运动效果**：流体模拟近似、粒子轨迹扰动、域扭曲动画

核心思想：不使用预先制作的纹理，而是通过数学函数在GPU上实时生成伪随机、空间连续的信号，然后通过分形求和（FBM）和域扭曲产生丰富的多尺度细节。

## 核心原则详细信息

### 1. 噪声函数 — 构建连续伪随机信号

噪声函数的本质是：**在整数格点处生成随机值，然后在它们之间平滑插值**。

两种主流实现：

**值噪声**：每个格点存储一个随机标量，双线性插值产生连续场。
- 公式：`N(p) = mix(mix(h00, h10, u), mix(h01, h11, u), v)`，其中`u,v`是Hermite平滑后的小数部分

**单纯形噪声**：在三角晶格 (2D) 或四面体晶格 (3D) 上使用梯度点积 + 径向衰减内核。
- 优点：更少的点阵查找（2D：3 vs 4），无轴对齐伪影，计算成本更低
- 核心：倾斜变换将方形网格映射到三角形网格，使用“K1=(sqrt(3)-1)/2”进行倾斜，“K2=(3-sqrt(3))/6”进行去倾斜

### 2. 哈希函数——格子随机值的来源

哈希函数将整数坐标映射到 [0,1] 或 [-1,1] 中的伪随机值：

- **基于 sin 的哈希**（经典但有精度风险）： `fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453)`
- **无罪哈希**（跨平台稳定）：纯算术 `fract(p * 0.1031)` + `dot` 混合 + `fract` 输出

### 3.FBM（分数布朗运动）——多尺度细节求和

对不同频率和幅度的多个噪声“八度音阶”求和：```
FBM(p) = sum( amplitude_i * noise(frequency_i * p) )
```标准参数：
- **空隙度（频率倍增器）**：每个八度音阶的频率乘以~2.0
- **余辉/增益（振幅衰减）**：每个八度音程的振幅乘以~0.5
- **八度间旋转**：使用旋转矩阵消除轴对齐伪影

### 4. 域扭曲 — 有机扭曲

将噪声输出作为坐标偏移反馈，产生扭曲的有机图案：
- **单层扭曲**：`fbm(p + fbm(p))`
- **多层级联**：`fbm(p + fbm(p + fbm(p)))` — 经典的三层域扭曲

### 5. FBM 变体 — 不同的视觉特征

|变体 |公式|视觉效果|
|--------|---------|------------|
|标准FBM | `sum(a*noise(p))` |光滑、柔软（云内饰）|
|脊状 FBM | `sum( a*abs(噪声(p)) )` |锐利的折痕（脊线、闪电）|
|正弦脊状 | `sum(a*sin(噪声(p)*k))` |周期性山脊（熔岩）|
|侵蚀FBM | `sum( a*noise(p)/(1+dot(d,d)) )` |山脊平坦，山谷细腻（地形）|
|海浪FBM | `sum( a*octave_fn(p) )` |尖锐的波峰（海洋表面）|

## 分步实施细节

### 步骤 1：哈希函数

**什么**：实现一个将 2D 整数坐标映射到伪随机值的哈希函数。

**为什么**：散列是所有噪音的基本组成部分。无罪版本在 GPU 上稳定； sin 版本更简洁。

**代码（无罪版）**：```glsl
// 2D -> 1D hash, sin-free, cross-platform stable
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// 2D -> 2D hash (for gradient noise)
vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}
```**代码（经典罪恶版本）**：```glsl
float hash(vec2 p) {
    float h = dot(p, vec2(127.1, 311.7));
    return fract(sin(h) * 43758.5453123);
}

// Gradient version, output [-1, 1]
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}
```### 第 2 步：评估噪声

**什么**：在整数格点处的哈希值之间执行 Hermite 平滑插值以获得连续的 2D 噪声场。

**为什么**：值噪声是最简单的噪声实现，代码最少，适合作为 FBM 和域扭曲的基础。使用“smoothstep”多项式“3t^2-2t^3”直接保证 C1 连续性（无接缝不连续性）。

**代码**：```glsl
float noise(in vec2 x) {
    vec2 p = floor(x);    // Integer lattice point
    vec2 f = fract(x);    // Fractional part within cell
    f = f * f * (3.0 - 2.0 * f);  // Hermite smoothing (can substitute quintic: 6t^5-15t^4+10t^3)
    float a = hash(p + vec2(0.0, 0.0));
    float b = hash(p + vec2(1.0, 0.0));
    float c = hash(p + vec2(0.0, 1.0));
    float d = hash(p + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);  // Bilinear interpolation
}
```### 步骤 3：单纯形噪声

**什么**：在三角形网格上使用梯度点积和径向衰减内核来生成各向同性 2D 噪声。

**为什么**：与值噪声相比，Simplex Noise 没有轴对齐伪影，计算成本更低（2D 仅需要 3 个格点而不是 4 个），并且视觉质量更高。适用于需要高质量噪声的场景（火、云）。

**代码**：```glsl
float noise(in vec2 p) {
    const float K1 = 0.366025404;  // (sqrt(3)-1)/2 — skew factor
    const float K2 = 0.211324865;  // (3-sqrt(3))/6 — unskew factor

    vec2 i = floor(p + (p.x + p.y) * K1);  // Skew to triangular grid

    vec2 a = p - i + (i.x + i.y) * K2;     // Vertex 0 offset
    vec2 o = (a.x > a.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);  // Determine which triangle
    vec2 b = a - o + K2;                    // Vertex 1 offset
    vec2 c = a - 1.0 + 2.0 * K2;           // Vertex 2 offset

    vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);  // Radial falloff
    vec3 n = h * h * h * h * vec3(  // h^4 kernel * gradient dot product
        dot(a, hash2(i + 0.0)),
        dot(b, hash2(i + o)),
        dot(c, hash2(i + 1.0))
    );
    return dot(n, vec3(70.0));  // Normalize to ~[-1, 1]
}
```### 步骤 4：标准 FBM（分数布朗运动）

**什么**：对振幅递减的多个倍频程噪声求和以获得多尺度分形信号。

**为什么**：单个噪声倍频程具有单一频率，无法产生自然界中发现的多尺度细节。 FBM 通过对不同频率的噪声求和来模拟分形自相似性。 **八度间旋转矩阵是打破轴对齐伪影的关键技术**。

**代码（4倍频程循环版本）**：```glsl
#define OCTAVES 4           // Tunable: number of octaves (1-8), more = richer detail but more expensive
#define GAIN 0.5            // Tunable: amplitude decay (0.3-0.7), higher = more prominent high frequencies
#define LACUNARITY 2.0      // Tunable: frequency multiplier (1.5-3.0), higher = larger gap between octaves

float fbm(vec2 p) {
    // Encodes both rotation and scaling, eliminates axis-aligned artifacts
    // |m| = sqrt(1.6^2+1.2^2) = 2.0, rotation angle ~ 36.87 degrees
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);

    float f = 0.0;
    float a = 0.5;   // Initial amplitude
    for (int i = 0; i < OCTAVES; i++) {
        f += a * noise(p);
        p = m * p;    // Rotation + frequency scaling
        a *= GAIN;    // Amplitude decay
    }
    return f;
}
```**手动展开版本（空隙略有不同）**：```glsl
// Slightly varying lacunarity (2.01, 2.02, 2.03...) breaks exact self-similarity
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80);  // Pure rotation ~36.87 degrees

float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;  // Normalization
}
```### 步骤 5：脊状 FBM

**什么**：在求和之前取噪声的绝对值，在零交叉处产生尖锐的“脊”。

**原因**：标准 FBM 生成过于平滑的图案，无法表示闪电、山脊或裂缝等尖锐结构。 “abs()”操作将噪声的零交叉折叠成尖锐的 V 形脊线。

**代码**：```glsl
float fbm_ridged(in vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        // abs((noise-0.5)*2) maps [0,1] to a V-shape in [0,1]
        rz += abs((noise(p) - 0.5) * 2.0) / z;
        z *= 2.0;   // Amplitude decay (1/z)
        p *= 2.0;   // Frequency scaling
    }
    return rz;
}
```**正弦脊形变体**：```glsl
// sin(noise*7) produces smoother periodic ridges, suitable for lava textures
rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z;
```### 步骤 6：域扭曲

**什么**：使用噪声/FBM 的输出来扭曲后续噪声的输入坐标，产生有机扭曲模式。

**为什么**：域扭曲是产生“绘画”、“水墨”、“地质”等有机图案的核心技术。嵌套扭曲层的数量控制复杂性。

**基本域扭曲**：```glsl
// Low-frequency FBM as offset to distort subsequent sampling
float q = fbm(uv * 0.5);   // Low-frequency domain warping field
uv -= q - time;             // Use q to offset sampling coordinates
float f = fbm(uv);          // Sample at warped coordinates
```**经典的三层级联域扭曲**：```glsl
// Two independent FBMs produce decorrelated vec2 offsets
vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));  // Different offsets for decorrelation
}

float func(vec2 q, out vec2 o, out vec2 n) {
    // Layer 1: q -> 4-octave FBM -> 2D offset field o
    o = 0.5 + 0.5 * fbm4_2(q);

    // Layer 2: o -> 6-octave FBM -> 2D offset field n (higher frequency)
    n = fbm6_2(4.0 * o);

    // Layer 3: original coordinates + offsets -> final FBM sampling
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p);

    // Contrast enhancement: boost contrast in heavily warped areas
    f = mix(f, f * f * f * 3.5, f * abs(n.x));
    return f;
}
```**双轴 FBM 域扭曲**：```glsl
float dualfbm(in vec2 p) {
    vec2 p2 = p * 0.7;
    // Two independent FBMs offset X/Y axes separately, different time offsets avoid symmetry
    vec2 basis = vec2(fbm(p2 - time * 1.6), fbm(p2 + time * 1.7));
    basis = (basis - 0.5) * 0.2;  // Center + scale
    p += basis;
    return fbm(p * makem2(time * 0.2));  // Final sampling after rotation
}
```### 步骤 7：流动噪音

**内容**：在每个 FBM 倍频程内应用独立的梯度场位移，模拟流体传输效果。

**原因**：普通域扭曲是“全局”的（在 FBM 之前或之后扭曲），而流动噪声是“每倍频程”——每个频率层都有自己的流动方向和速度，产生极其逼真的熔岩和流体效果。

**代码**：```glsl
#define FLOW_SPEED 0.6       // Tunable: main flow speed
#define BASE_SPEED 1.9       // Tunable: base point flow speed
#define ADVECTION 0.77       // Tunable: advection factor (0.5=stable, 0.95=turbulent)
#define GRAD_SCALE 0.5       // Tunable: gradient displacement strength

// Noise gradient (central differences)
vec2 gradn(vec2 p) {
    float ep = 0.09;
    float gradx = noise(vec2(p.x + ep, p.y)) - noise(vec2(p.x - ep, p.y));
    float grady = noise(vec2(p.x, p.y + ep)) - noise(vec2(p.x, p.y - ep));
    return vec2(gradx, grady);
}

float flow(in vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    vec2 bp = p;  // Base point (prevents advection divergence)
    for (float i = 1.0; i < 7.0; i++) {
        p += time * FLOW_SPEED;                        // Main flow displacement
        bp += time * BASE_SPEED;                       // Base flow displacement
        vec2 gr = gradn(i * p * 0.34 + time * 1.0);   // Noise gradient field
        gr *= makem2(time * 6.0 - (0.05 * p.x + 0.03 * p.y) * 40.0);  // Spatially varying rotation
        p += gr * GRAD_SCALE;                          // Gradient displacement
        rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z; // Sinusoidal ridged accumulation
        p = mix(bp, p, ADVECTION);                     // Mix back to base (prevent divergence)
        z *= 1.4;   // Amplitude decay
        p *= 2.0;   // Frequency scaling
        bp *= 1.9;  // Base frequency scaling (slightly different)
    }
    return rz;
}
```### 步骤 8：衍生 FBM

**内容**：跟踪 FBM 累积过程中噪声的分析梯度，使用累积的梯度幅度来抑制陡峭区域的高频细节。

**为什么**：这是地形渲染的标志性技术。标准 FBM 在所有区域中统一添加细节，但自然地形由于水力侵蚀而具有平滑的山脊，而山谷保留了精细的细节。导数 FBM 通过“1/(1+|梯度|^2)”因子自动模拟这种侵蚀效应。

**代码**：```glsl
// Value noise with analytical derivative: returns vec3(value, d/dx, d/dy)
vec3 noised(in vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * (3.0 - 2.0 * f);           // Hermite interpolation
    vec2 du = 6.0 * f * (1.0 - f);               // Hermite derivative (analytical)

    float a = hash(p + vec2(0, 0));
    float b = hash(p + vec2(1, 0));
    float c = hash(p + vec2(0, 1));
    float d = hash(p + vec2(1, 1));

    return vec3(
        a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y,  // Value
        du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx)                  // Gradient
    );
}

#define TERRAIN_OCTAVES 16   // Tunable: terrain octave count (5-16), more = finer detail
#define TERRAIN_GAIN 0.5     // Tunable: amplitude decay

float terrainFBM(in vec2 x) {
    const mat2 m2 = mat2(0.8, -0.6, 0.6, 0.8);  // Pure rotation ~36.87 degrees
    float a = 0.0;       // Accumulated value
    float b = 1.0;       // Current amplitude
    vec2 d = vec2(0.0);  // Accumulated gradient

    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        vec3 n = noised(x);    // (value, dx, dy)
        d += n.yz;             // Accumulate gradient
        a += b * n.x / (1.0 + dot(d, d));  // Key: larger gradient = smaller contribution (erosion effect)
        b *= TERRAIN_GAIN;
        x = m2 * x * 2.0;     // Rotation + frequency scaling
    }
    return a;
}
```## 常见变体详细信息

### 变体 1：脊状 FBM（脊状/湍流 FBM）

- **与基本版本的差异**：将“abs()”应用于噪声值，在零交叉处产生尖锐的脊线
- **用例**：闪电、山脊、裂缝、静脉、电弧
- **关键修改代码**：```glsl
// Standard FBM line:
f += a * noise(p);
// Changed to ridged:
f += a * abs(noise(p));
// Or sinusoidal ridged (smoother periodic ridges, suitable for lava):
f += a * (sin(noise(p) * 7.0) * 0.5 + 0.5);
```### 变体 2：域扭曲 FBM

- **与基础版本的差异**：FBM 输出作为坐标偏移反馈，产生有机失真
- **用例**：云变形、地质纹理、水墨风格、抽象艺术
- **关键修改代码**：```glsl
// Classic three-layer domain warping
vec2 o = 0.5 + 0.5 * vec2(fbm(q + vec2(1.0)), fbm(q + vec2(6.2)));
vec2 n = vec2(fbm(4.0 * o + vec2(9.2)), fbm(4.0 * o + vec2(5.7)));
float f = 0.5 + 0.5 * fbm(q + 2.0 * n + 1.0);
```### 变体 3：衍生侵蚀 FBM

- **与基础版本的区别**：跟踪分析梯度，抑制陡峭区域的高频（模拟水力侵蚀）
- **用例**：现实地形、山脉、峡谷
- **关键修改代码**：```glsl
vec2 d = vec2(0.0);  // Accumulated gradient
for (int i = 0; i < N; i++) {
    vec3 n = noised(p);       // (value, dx, dy)
    d += n.yz;                // Accumulate gradient
    a += b * n.x / (1.0 + dot(d, d));  // Key: divide by gradient magnitude
    b *= 0.5;
    p = m2 * p * 2.0;
}
```### 变体 4：流动噪声

- **与基础版本的差异**：在每个倍频程内应用独立的梯度场位移，模拟流体传输
- **用例**：熔岩、液态金属、流动的岩浆
- **关键修改代码**：```glsl
for (float i = 1.0; i < 7.0; i++) {
    vec2 gr = gradn(i * p * 0.34 + time);                              // Gradient field
    gr *= makem2(time * 6.0 - (0.05 * p.x + 0.03 * p.y) * 40.0);     // Spatially varying rotation
    p += gr * 0.5;                                                      // Displacement
    rz += (sin(noise(p) * 7.0) * 0.5 + 0.5) / z;                      // Accumulation
    p = mix(bp, p, 0.77);                                               // Mix back to base
}
```### 变体 5：定制 Sea Octave FBM

- **与基础版本的区别**：使用“1-abs(sin(uv))”构建峰值波形，并结合双向传播和波涛汹涌的衰减
- **用例**：海洋水面、波浪
- **关键修改代码**：```glsl
float sea_octave(vec2 uv, float choppy) {
    uv += noise(uv);                      // Noise domain perturbation
    vec2 wv = 1.0 - abs(sin(uv));         // Peaked waveform
    vec2 swv = abs(cos(uv));              // Smooth waveform
    wv = mix(wv, swv, wv);               // Adaptive blending
    return pow(1.0 - pow(wv.x * wv.y, 0.65), choppy);
}
// Bidirectional propagation in FBM loop:
d  = sea_octave((uv + SEA_TIME) * freq, choppy);
d += sea_octave((uv - SEA_TIME) * freq, choppy);
choppy = mix(choppy, 1.0, 0.2);  // Higher octaves are smoother
```## 性能优化详情

### 1. 减少八度数（最直接）

每增加一个倍频程，噪声采样成本就会增加一倍。远处的物体可以使用更少的八度：```glsl
// LOD-aware octave count
int oct = 5 - int(log2(1.0 + t * 0.5));  // Fewer octaves at greater distances
```### 2. 多级LOD策略

为不同的目的提供不同精度级别的函数：```glsl
float terrainL(vec2 x) { /* 3 octaves — for camera height */ }
float terrainM(vec2 x) { /* 9 octaves — for ray marching */ }
float terrainH(vec2 x) { /* 16 octaves — for normal calculation */ }
```### 3. 使用纹理采样而不是数学

使用硬件纹理过滤而不是算术哈希将预先计算的噪声存储在纹理中：```glsl
float noise(in vec2 x) { return texture(iChannel0, x * 0.01).x; }
// Or use texelFetch for exact lookup:
float a = texelFetch(iChannel0, (p + 0) & 255, 0).x;
```### 4. 手动展开循环

GLSL 编译器通常比“for”循环更好地优化手动展开的小循环（4-6 次迭代），并且允许每个八度音程略有不同的空白度。

### 5.自适应步长（体积渲染）```glsl
// Step size grows linearly with distance
float dt = max(0.05, 0.02 * t);
```### 6. 方向导数代替全梯度（体积照明）```glsl
// 1 extra sample vs 3
float dif = clamp((den - map(pos + 0.3 * sundir)) / 0.25, 0.0, 1.0);
```### 7. 提前终止```glsl
if (sum.a > 0.99) break;  // Volume is already opaque, stop marching
```## 详细组合建议

### 1.FBM + 射线行进

噪声驱动高度场或密度场，光线行进找到交叉点。这是地形和海洋表面渲染的标准组合：
- 高度字段：`height =terrainFBM(pos.xz)`，光线行进找到`pos.y == height`的交点
- 体积场：`密度 = fbm(pos)`，前向累加透射率和颜色

### 2.FBM + 有限差分法线 + 光照

使用 2D 噪声场上的有限差分来估计法线，添加伪 3D 光照效果：```glsl
vec3 nor = normalize(vec3(f(p+ex)-f(p), epsilon, f(p+ey)-f(p)));
float dif = dot(nor, lightDir);
```### 3.FBM + 颜色映射

将不同幂指数的相同标量映射到 RGB 通道，产生自然的颜色渐变：```glsl
vec3 col = vec3(1.5*c, 1.5*c*c*c, c*c*c*c*c*c);  // Fire: red -> orange -> yellow -> white
```或逆颜色映射：```glsl
vec3 col = vec3(0.2, 0.07, 0.01) / rz;  // Areas with small ridge values are brightest
```### 4.FBM + 菲涅耳水面着色

噪声驱动水面波形，菲涅尔方程混合反射的天空和折射的水色：```glsl
float fresnel = pow(1.0 - dot(n, -eye), 3.0);
vec3 color = mix(refracted, reflected, fresnel);
```### 5.多层FBM合成

具有不同参数的不同 FBM 层控制不同的属性：
- **形状层**：低频标准FBM控制云形状
- **脊状层**：中频脊状 FBM 添加边缘细节
- **颜色层**：高频FBM控制云内部颜色变化
- **组合**：`f *= r + f;` 形状 * 脊状产生锋利的边缘

### 6.FBM + 体积光照（定向导数）

在体渲染中，沿光线方向的密度差近似于光照：```glsl
float shadow = clamp((density_here - density_toward_sun) / scale, 0.0, 1.0);
vec3 lit_color = mix(shadow_color, light_color, shadow);
```
