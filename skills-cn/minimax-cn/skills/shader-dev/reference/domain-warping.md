# 域扭曲 — 详细参考

本文档包含完整的分步教程、数学推导以及域扭曲技术的高级用法。请参阅 [SKILL.md](SKILL.md) 了解精简版本。

## 先决条件

- **GLSL基础**：统一变量，内置函数（`mix`，`smoothstep`，`fract`，`floor`，`sin`，`dot`）
- **矢量数学**：点积、矩阵乘法、2D 旋转矩阵
- **噪声函数概念**：理解值噪声的基本原理（格子插值）
- **fBM（分形布朗运动）**：不同频率/幅度的多个噪声层的叠加
- **ShaderToy 环境**：`iTime`、`iResolution`、`fragCoord` 的含义

## 详细实施步骤

### 步骤 1：哈希函数

**什么**：实现一个哈希函数，将 2D 整数坐标映射到伪随机浮点数。

**为什么**：这是噪声函数的基础——在每个格点产生确定性的“随机”值。 “sin-dot”技巧将 2D 输入压缩为 1D，然后取小数部分，利用 sin 的高频振荡产生混沌分布。

**代码**：```glsl
float hash(vec2 p) {
    p = fract(p * 0.6180339887); // Golden ratio pre-perturbation
    p *= 25.0;
    return fract(p.x * p.y * (p.x + p.y));
}
```> 注意：也可以使用经典的 `fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453)` 版本，但上面的无 sin 版本在某些 GPU 上精度更稳定。

### 第 2 步：评估噪声

**内容**：实现 2D 值噪声 - 在整数格点处获取哈希值，并使用 Hermite 平滑在它们之间进行插值。

**为什么**：值噪声是最简单的连续噪声，产生平滑、无跳跃的输出，适合作为 fBM 的基础。 Hermite插值`f*f*(3.0-2.0*f)`确保格点处导数为零，避免线性插值的角度出现。

**代码**：```glsl
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f); // Hermite smooth interpolation

    return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}
```### 步骤 3：fBM（分形布朗运动）

**什么**：叠加不同频率/幅度的多个噪声层，以创建具有自相似属性的分形噪声。

**为什么**：单个噪声层太均匀。 fBM 叠加多个“八度”来模拟自然的分形结构。每层的频率加倍（空隙度 ~ 2.0），振幅减半（持久性 = 0.5），并使用旋转矩阵来破坏晶格排列。

**代码**：```glsl
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80); // Rotation ~36.87°, for decorrelation

float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875; // Normalize: sum of all amplitudes
}
```> 使用 2.01~2.04 的空隙度值而不是精确的 2.0 是为了**避免晶格正则性引起的视觉伪影**。这是经典实现中广泛采用的技巧。

### 步骤 4：域扭曲（核心）

**什么**：使用fBM输出作为坐标偏移，递归嵌套形成多级扭曲。

**为什么**：这是整个技术的核心。 `fbm(p)` 生成一个标量场；将其添加到坐标“p”相当于“根据噪声场的形状拉动和拉伸空间”。多层嵌套使变形更加复杂和有机——每个扭曲级别在已经被前一个级别变形的空间中运行。

**代码**：```glsl
float pattern(vec2 p) {
    return fbm(p + fbm(p + fbm(p)));
}
```这条单线是经典的三级域扭曲。可以分解一下来理解：```glsl
float pattern(vec2 p) {
    float warp1 = fbm(p);           // Level 1: noise in original space
    float warp2 = fbm(p + warp1);   // Level 2: noise in first-level warped space
    float result = fbm(p + warp2);  // Level 3: final value in second-level warped space
    return result;
}
```### 步骤 5：时间动画

**什么**：将“iTime”注入特定的 fBM 八度音阶，以便扭曲场随着时间的推移而演变。

**为什么**：直接抵消所有八度会导致统一的翻译，缺乏有机的感觉。经典的方法是仅在最低频率（第一层）和最高频率（最后一层）注入时间 - 低频驱动整体流程，高频增加细节变化。

**代码**：```glsl
float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p + iTime);  // Lowest frequency with time: slow overall flow
    p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p + sin(iTime)); // Highest frequency with time: subtle detail motion
    return f / 0.96875;
}
```### 第 6 步：着色

**什么**：将扭曲场的标量输出映射到颜色。

**为什么**：域扭曲输出一个标量场（0~1 范围），需要映射到视觉上有意义的颜色。经典方法使用“混合”链——使用扭曲值在多个预设颜色之间进行插值。

**代码**：```glsl
vec3 palette(float t) {
    vec3 col = vec3(0.2, 0.1, 0.4);                              // Deep purple base
    col = mix(col, vec3(0.3, 0.05, 0.05), t);                    // Dark red
    col = mix(col, vec3(0.9, 0.9, 0.9), t * t);                  // White at high values
    col = mix(col, vec3(0.0, 0.2, 0.4), smoothstep(0.6, 0.8, t));// Blue highlights
    return col * t * 2.0;                                         // Overall brightness modulation
}
```## 常见变体详细信息

### 变体 1：多分辨率分层变形

**与基本版本的区别**：对不同的变形层使用不同的八度数 - 粗略层使用 4 个八度（快速，低频），细节层使用 6 个八度（精细，高频）。输出二维位移“vec2”而不是标量偏移。中间变量参与着色，产生更丰富的颜色渐变。

**关键修改代码**：```glsl
// 4-octave fBM (coarse layer)
float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;
}

// 6-octave fBM (fine layer)
float fbm6(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875;
}

// vec2 output version (independent displacement per axis)
vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));
}
vec2 fbm6_2(vec2 p) {
    return vec2(fbm6(p + vec2(9.2)), fbm6(p + vec2(5.7)));
}

// Layered warping chain
float func(vec2 q, out vec2 o, out vec2 n) {
    q += 0.05 * sin(vec2(0.11, 0.13) * iTime + length(q) * 4.0);
    o = 0.5 + 0.5 * fbm4_2(q);           // Level 1: coarse displacement
    o += 0.02 * sin(vec2(0.13, 0.11) * iTime * length(o));
    n = fbm6_2(4.0 * o);                  // Level 2: fine displacement
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p); // Level 3: final scalar field
    f = mix(f, f * f * f * 3.5, f * abs(n.x)); // Contrast enhancement
    return f;
}

// Coloring uses intermediate variables o, n
vec3 col = vec3(0.2, 0.1, 0.4);
col = mix(col, vec3(0.3, 0.05, 0.05), f);
col = mix(col, vec3(0.9, 0.9, 0.9), dot(n, n));         // n magnitude drives white
col = mix(col, vec3(0.5, 0.2, 0.2), 0.5 * o.y * o.y);   // o.y drives brown
col = mix(col, vec3(0.0, 0.2, 0.4), 0.5 * smoothstep(1.2, 1.3, abs(n.y) + abs(n.x)));
col *= f * 2.0;
```### 变体 2：湍流/脊变形（电弧/等离子效应）

**与基本版本的区别**：取fBM内部噪声`abs(noise - 0.5)`的绝对值，产生尖锐的山脊纹理而不是平滑的波浪。双轴独立 fBM 位移（单独的 x/y 偏移）与反向时间漂移相结合会产生湍流。

**关键修改代码**：```glsl
// Turbulence / ridged fBM
float fbm_ridged(vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        rz += abs((noise(p) - 0.5) * 2.0) / z; // abs() produces ridge folding
        z *= 2.0;
        p *= 2.0;
    }
    return rz;
}

// Dual-axis independent displacement
float dualfbm(vec2 p) {
    vec2 p2 = p * 0.7;
    // Opposite time drift in two directions creates turbulence
    vec2 basis = vec2(
        fbm_ridged(p2 - iTime * 0.24),  // x axis drifts left
        fbm_ridged(p2 + iTime * 0.26)   // y axis drifts right
    );
    basis = (basis - 0.5) * 0.2;         // Scale to small displacement
    p += basis;
    return fbm_ridged(p * makem2(iTime * 0.03)); // Slow overall rotation
}

// Electric arc coloring (division creates high-contrast light/dark)
vec3 col = vec3(0.2, 0.1, 0.4) / rz;
```### 变体 3：使用伪 3D 光照进行域变形

**与基本版本的区别**：使用有限差分从扭曲场估计屏幕空间法线，然后应用定向照明，为 2D 扭曲场提供 3D 浮雕外观。结合色彩反转和方形压缩，产生特有的暗色调。

**关键修改代码**：```glsl
// Screen-space normal estimation (finite differences)
float e = 2.0 / iResolution.y; // Sample spacing = 1 pixel
vec3 nor = normalize(vec3(
    pattern(p + vec2(e, 0.0)) - shade,  // df/dx
    2.0 * e,                             // Constant y (controls normal tilt)
    pattern(p + vec2(0.0, e)) - shade    // df/dy
));

// Dual-component lighting
vec3 lig = normalize(vec3(0.9, 0.2, -0.4));
float dif = clamp(0.3 + 0.7 * dot(nor, lig), 0.0, 1.0);
vec3 lin = vec3(0.70, 0.90, 0.95) * (nor.y * 0.5 + 0.5);  // Hemisphere ambient light
lin += vec3(0.15, 0.10, 0.05) * dif;                         // Warm diffuse

col *= 1.2 * lin;
col = 1.0 - col;       // Color inversion
col = 1.1 * col * col;  // Square compression, increases dark contrast
```### 变体 4：流场迭代扭曲（气态巨行星效应）

**与基本版本的区别**：不是直接嵌套fBM，而是计算fBM梯度场并通过欧拉积分迭代推进坐标。模拟流体平流，产生类似涡旋的行星大气带。

**关键修改代码**：```glsl
#define ADVECT_ITERATIONS 5 // Adjustable: iteration count, more = more pronounced vortices

// Compute fBM gradient (finite differences)
vec2 field(vec2 p) {
    float t = 0.2 * iTime;
    p.x += t;
    float n = fbm(p, t);
    float e = 0.25;
    float nx = fbm(p + vec2(e, 0.0), t);
    float ny = fbm(p + vec2(0.0, e), t);
    return vec2(n - ny, nx - n) / e; // 90° rotated gradient = streamline direction
}

// Iterative flow field advection
vec3 distort(vec2 p) {
    for (float i = 0.0; i < float(ADVECT_ITERATIONS); i++) {
        p += field(p) / float(ADVECT_ITERATIONS);
    }
    return vec3(fbm(p, 0.0)); // Sample at the advected coordinates
}
```### 变体 5：3D 体积域扭曲（爆炸/火球效果）

**与基本版本的区别**：将域扭曲从 2D 扩展到 3D，使用 3D fBM 置换球体的距离场，然后通过球体追踪或体积射线行进进行渲染。产生火山喷发、太阳表面和其他体积效果。

**关键修改代码**：```glsl
#define NOISE_FREQ 4.0     // Adjustable: noise frequency
#define NOISE_AMP -0.5     // Adjustable: displacement amplitude (negative = inward bulging feel)

// 3D rotation matrix (for decorrelation)
mat3 m3 = mat3(0.00, 0.80, 0.60,
              -0.80, 0.36,-0.48,
              -0.60,-0.48, 0.64);

// 3D value noise
float noise3D(vec3 p) {
    vec3 fl = floor(p);
    vec3 fr = fract(p);
    fr = fr * fr * (3.0 - 2.0 * fr);
    float n = fl.x + fl.y * 157.0 + 113.0 * fl.z;
    return mix(mix(mix(hash(n+0.0),   hash(n+1.0),   fr.x),
                   mix(hash(n+157.0), hash(n+158.0), fr.x), fr.y),
               mix(mix(hash(n+113.0), hash(n+114.0), fr.x),
                   mix(hash(n+270.0), hash(n+271.0), fr.x), fr.y), fr.z);
}

// 3D fBM
float fbm3D(vec3 p) {
    float f = 0.0;
    f += 0.5000 * noise3D(p); p = m3 * p * 2.02;
    f += 0.2500 * noise3D(p); p = m3 * p * 2.03;
    f += 0.1250 * noise3D(p); p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p); p = m3 * p * 2.02;
    f += 0.03125 * abs(noise3D(p)); // Last layer uses abs for added detail
    return f / 0.9375;
}

// Sphere distance field + domain warping displacement
float distanceFunc(vec3 p, out float displace) {
    float d = length(p) - 0.5; // Sphere SDF
    displace = fbm3D(p * NOISE_FREQ + vec3(0, -1, 0) * iTime);
    d += displace * NOISE_AMP;  // fBM displaces the surface
    return d;
}
```## 性能优化深入探讨

### 瓶颈分析

域扭曲的主要性能瓶颈是**重复噪声采样**。三个扭曲级别乘以 6 个倍频程 = 每像素 18 个噪声样本，加上照明的有限差异（2 个额外的完整扭曲计算），总计高达 **54 个噪声样本/像素**。

### 优化技术

1. **减少八度音阶数**：使用 4 个八度音阶而不是 6 个八度音阶显示出的视觉差异很小，但性能提高了约 33%```glsl
   // Use 4 octaves for coarse layers, only 6 octaves for fine layers
   ```2. **减少扭曲深度**：两级扭曲 `fbm(p + fbm(p))` 已经产生有机结果，在三个级别上节省约 33% 的性能

3. **使用正积噪声代替值噪声**： `sin(p.x)*sin(p.y)` 完全无分支，无需内存访问，适合移动设备```glsl
   float noise(vec2 p) {
       return sin(p.x) * sin(p.y); // Minimal version, no hash needed
   }
   ```4. **GPU内置导数而不是有限差分**：节省2次额外的完整扭曲计算```glsl
   // Use dFdx/dFdy instead of manual finite differences (slightly lower quality but 3x faster)
   vec3 nor = normalize(vec3(dFdx(shade) * iResolution.x, 6.0, dFdy(shade) * iResolution.y));
   ```5. **纹理噪声**：预烘焙噪声纹理并使用“texture()”代替程序噪声，将计算转换为内存读取```glsl
   float noise(vec2 x) {
       return texture(iChannel0, x * 0.01).x;
   }
   ```6. **LOD适应**：减少远处像素的八度数```glsl
   int octaves = int(mix(float(NUM_OCTAVES), 2.0, length(uv) / 5.0));
   ```7. **超级采样策略**：仅在需要抗锯齿时才使用2x2超级采样（4倍性能成本）```glsl
   #if HW_PERFORMANCE == 0
   #define AA 1
   #else
   #define AA 2
   #endif
   ```## 组合建议与完整代码示例

### 与 Ray Marching 结合
由域扭曲生成的标量场可以直接用作 SDF 位移函数，将平滑的几何形状变形为有机形式。用于火焰、爆炸、外星生物等。```glsl
float sdf(vec3 p) {
    return length(p) - 1.0 + fbm3D(p * 4.0) * 0.3;
}
```### 与极坐标变换结合
在极坐标空间中执行域扭曲以产生漩涡、星云、螺旋和其他效果。```glsl
vec2 polar = vec2(length(uv), atan(uv.y, uv.x));
float shade = pattern(polar);
```### 与余弦调色板结合
余弦调色板 `a + b*cos(2*pi*(c*t+d))` 比固定混合链更灵活。通过调整四个vec3参数，可以快速切换配色方案。```glsl
vec3 palette(float t) {
    vec3 a = vec3(0.5); vec3 b = vec3(0.5);
    vec3 c = vec3(1.0); vec3 d = vec3(0.0, 0.33, 0.67);
    return a + b * cos(6.28318 * (c * t + d));
}
```### 与后处理效果结合
- **绽放/发光**：模糊并叠加高亮度区域以增强发光效果
- **色调映射**：`col = col / (1.0 + col)` 来压缩 HDR 范围
- **色差**：分别对 R/G/B 通道的偏移位置处的扭曲场进行采样```glsl
float r = pattern(uv + vec2(0.003, 0.0));
float g = pattern(uv);
float b = pattern(uv - vec2(0.003, 0.0));
```### 与粒子系统/几何相结合
域扭曲标量场可以驱动粒子速度场、网格顶点位移或 UV 动画变形 - 不限于纯片段着色器的使用。