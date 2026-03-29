# 域扭曲

## 用例

- **大理石/玉石纹理**：多层扭曲产生条纹石材纹理
- **织物/丝绸外观**：翘曲场折痕模拟纺织品表面
- **地质构造**：岩层、熔岩流、地表侵蚀
- **气态巨行星大气**：木星式带状环流
- **烟雾/火焰/爆炸**：流体效果与体积渲染相结合
- **抽象艺术背景**：程序有机图案，适合UI背景、音乐可视化
- **电流/等离子体效应**：脊状 FBM 变体产生尖锐的电弧图案

核心优势：仅依赖数学函数（不需要纹理资源）、输出无缝平铺、可动画化、GPU 友好。

## 核心原则

用噪声扭曲输入坐标，然后查询主函数：```
f(p) -> f(p + fbm(p))
```经典的多层递归嵌套：```
result = fbm(p + fbm(p + fbm(p)))
```每个FBM层的输出作为下一层的坐标偏移；更深的嵌套会产生更多的有机变形。

**关键数学结构**：

1. **噪声** `noise(p)`：整数格点处的伪随机值+Hermite插值`f*f*(3.0-2.0*f)`
2. **FBM**：`fbm(p) = (0.5^i) * 噪声之和(p * 2^i * R^i)`，其中`R`是用于去相关的旋转矩阵
3. **域扭曲链**：`fbm(p + fbm(p + fbm(p)))`

旋转矩阵“mat2(0.80, 0.60, -0.60, 0.80)”（约 36.87 度）是最广泛使用的去相关变换。

## 实施步骤

### 步骤 1：哈希函数```glsl
// Map 2D integer coordinates to a pseudo-random float
float hash(vec2 p) {
    p = fract(p * 0.6180339887); // golden ratio pre-perturbation
    p *= 25.0;
    return fract(p.x * p.y * (p.x + p.y));
}
```> 经典的 `fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453)` 也有效；上面的无罪版本在某些 GPU 上具有更稳定的精度。

### 第 2 步：评估噪声```glsl
// Hash values at integer lattice points, Hermite smooth interpolation
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}
```### 步骤 3：FBM```glsl
const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80); // rotation approx 36.87 deg

float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p); p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p);
    return f / 0.96875;
}
```> Lacunarity 使用 2.01~2.04 而不是精确的 2.0，以避免晶格正则性导致的视觉伪影。

### 步骤 4：域扭曲（核心）```glsl
// Classic three-layer domain warping
float pattern(vec2 p) {
    return fbm(p + fbm(p + fbm(p)));
}
```### 步骤 5：时间动画```glsl
// Inject time into the first and last octaves: low frequency drives overall flow, high frequency adds detail variation
float fbm(vec2 p) {
    float f = 0.0;
    f += 0.500000 * noise(p + iTime);       // lowest frequency: slow overall flow
    p = mtx * p * 2.02;
    f += 0.250000 * noise(p); p = mtx * p * 2.03;
    f += 0.125000 * noise(p); p = mtx * p * 2.01;
    f += 0.062500 * noise(p); p = mtx * p * 2.04;
    f += 0.031250 * noise(p); p = mtx * p * 2.01;
    f += 0.015625 * noise(p + sin(iTime));  // highest frequency: subtle detail motion
    return f / 0.96875;
}
```### 第 6 步：着色```glsl
// Map scalar field (0~1) to color using a mix chain
// IMPORTANT: Note: GLSL is strictly typed. Variable declarations must be complete, e.g. vec3 col = vec3(0.2, 0.1, 0.4)
// IMPORTANT: Decimals must be written as 0.x, not .x (division by zero errors)
vec3 palette(float t) {
    vec3 col = vec3(0.2, 0.1, 0.4);                               // deep purple base
    col = mix(col, vec3(0.3, 0.05, 0.05), t);                     // dark red
    col = mix(col, vec3(0.9, 0.9, 0.9), t * t);                   // high values toward white
    col = mix(col, vec3(0.0, 0.2, 0.4), smoothstep(0.6, 0.8, t)); // blue highlight
    return col * t * 2.0;
}
```## 完整代码模板```glsl
// Domain Warping — Full Runnable Template (ShaderToy)

#define WARP_DEPTH 3        // Warp nesting depth (1=subtle, 2=moderate, 3=classic)
#define NUM_OCTAVES 6       // FBM octave count (4=coarse fast, 6=fine)
#define TIME_SCALE 1.0      // Animation speed (0.05=very slow, 1.0=fluid, 2.0=fast)
#define WARP_STRENGTH 1.0   // Warp intensity (0.5=subtle, 1.0=standard, 2.0=strong)
#define BASE_SCALE 3.0      // Overall noise scale (larger = denser texture)

const mat2 mtx = mat2(0.80, 0.60, -0.60, 0.80);

float hash(vec2 p) {
    p = fract(p * 0.6180339887);
    p *= 25.0;
    return fract(p.x * p.y * (p.x + p.y));
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}

float fbm(vec2 p) {
    float f = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    float norm = 0.0;

    for (int i = 0; i < NUM_OCTAVES; i++) {
        float t = 0.0;
        if (i == 0) t = iTime * TIME_SCALE;
        if (i == NUM_OCTAVES - 1) t = sin(iTime * TIME_SCALE);

        f += amp * noise(p + t);
        norm += amp;
        p = mtx * p * 2.02;
        amp *= 0.5;
    }
    return f / norm;
}

float pattern(vec2 p) {
    float val = fbm(p);

    #if WARP_DEPTH >= 2
    val = fbm(p + WARP_STRENGTH * val);
    #endif

    #if WARP_DEPTH >= 3
    val = fbm(p + WARP_STRENGTH * val);
    #endif

    return val;
}

vec3 palette(float t) {
    vec3 col = vec3(0.2, 0.1, 0.4);
    col = mix(col, vec3(0.3, 0.05, 0.05), t);
    col = mix(col, vec3(0.9, 0.9, 0.9), t * t);
    col = mix(col, vec3(0.0, 0.2, 0.4), smoothstep(0.6, 0.8, t));
    return col * t * 2.0;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    uv *= BASE_SCALE;

    float shade = pattern(uv);
    vec3 col = palette(shade);

    // Vignette effect
    vec2 q = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * sqrt(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y));

    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：多分辨率分层变形

不同的扭曲层使用不同倍频数的 FBM，输出“vec2”进行双轴位移，中间变量用于着色。```glsl
float fbm4(vec2 p) {
    float f = 0.0;
    f += 0.5000 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.02;
    f += 0.2500 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.03;
    f += 0.1250 * (-1.0 + 2.0 * noise(p)); p = mtx * p * 2.01;
    f += 0.0625 * (-1.0 + 2.0 * noise(p));
    return f / 0.9375;
}

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

vec2 fbm4_2(vec2 p) {
    return vec2(fbm4(p + vec2(1.0)), fbm4(p + vec2(6.2)));
}
vec2 fbm6_2(vec2 p) {
    return vec2(fbm6(p + vec2(9.2)), fbm6(p + vec2(5.7)));
}

float func(vec2 q, out vec2 o, out vec2 n) {
    q += 0.05 * sin(vec2(0.11, 0.13) * iTime + length(q) * 4.0);
    o = 0.5 + 0.5 * fbm4_2(q);
    o += 0.02 * sin(vec2(0.13, 0.11) * iTime * length(o));
    n = fbm6_2(4.0 * o);
    vec2 p = q + 2.0 * n + 1.0;
    float f = 0.5 + 0.5 * fbm4(2.0 * p);
    f = mix(f, f * f * f * 3.5, f * abs(n.x));
    return f;
}

// Coloring uses intermediate variables o, n
vec3 col = vec3(0.2, 0.1, 0.4);
col = mix(col, vec3(0.3, 0.05, 0.05), f);
col = mix(col, vec3(0.9, 0.9, 0.9), dot(n, n));
col = mix(col, vec3(0.5, 0.2, 0.2), 0.5 * o.y * o.y);
col = mix(col, vec3(0.0, 0.2, 0.4), 0.5 * smoothstep(1.2, 1.3, abs(n.y) + abs(n.x)));
col *= f * 2.0;
```### 变体 2：湍流/脊形扭曲（电弧/等离子效应）

在FBM中，应用“abs(noise - 0.5)”产生脊状纹理，具有双轴独立位移+时间反转漂移。```glsl
float fbm_ridged(vec2 p) {
    float z = 2.0;
    float rz = 0.0;
    for (float i = 1.0; i < 6.0; i++) {
        rz += abs((noise(p) - 0.5) * 2.0) / z;
        z *= 2.0;
        p *= 2.0;
    }
    return rz;
}

float dualfbm(vec2 p) {
    vec2 p2 = p * 0.7;
    vec2 basis = vec2(
        fbm_ridged(p2 - iTime * 0.24),
        fbm_ridged(p2 + iTime * 0.26)
    );
    basis = (basis - 0.5) * 0.2;
    p += basis;
    return fbm_ridged(p * makem2(iTime * 0.03));
}

// Electric arc coloring
vec3 col = vec3(0.2, 0.1, 0.4) / rz;
```### 变体 3：伪 3D 光照域扭曲

通过有限差分估计屏幕空间法线，应用定向照明以获得浮雕效果。```glsl
float e = 2.0 / iResolution.y;
vec3 nor = normalize(vec3(
    pattern(p + vec2(e, 0.0)) - shade,
    2.0 * e,
    pattern(p + vec2(0.0, e)) - shade
));

vec3 lig = normalize(vec3(0.9, 0.2, -0.4));
float dif = clamp(0.3 + 0.7 * dot(nor, lig), 0.0, 1.0);
vec3 lin = vec3(0.70, 0.90, 0.95) * (nor.y * 0.5 + 0.5);
lin += vec3(0.15, 0.10, 0.05) * dif;

col *= 1.2 * lin;
col = 1.0 - col;
col = 1.1 * col * col;
```### 变体 4：流场迭代扭曲（气态巨行星效应）

计算 FBM 梯度场，欧拉积分迭代平流坐标，模拟流体对流涡流。```glsl
#define ADVECT_ITERATIONS 5

vec2 field(vec2 p) {
    float t = 0.2 * iTime;
    p.x += t;
    float n = fbm(p, t);
    float e = 0.25;
    float nx = fbm(p + vec2(e, 0.0), t);
    float ny = fbm(p + vec2(0.0, e), t);
    return vec2(n - ny, nx - n) / e;
}

vec3 distort(vec2 p) {
    for (float i = 0.0; i < float(ADVECT_ITERATIONS); i++) {
        p += field(p) / float(ADVECT_ITERATIONS);
    }
    return vec3(fbm(p, 0.0));
}
```### 变体 5：3D 体积域扭曲（爆炸/火球效果）

使用通过体积光线行进渲染的 3D FBM 替换球体 SDF。```glsl
#define NOISE_FREQ 4.0
#define NOISE_AMP -0.5

mat3 m3 = mat3(0.00, 0.80, 0.60,
              -0.80, 0.36,-0.48,
              -0.60,-0.48, 0.64);

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

float fbm3D(vec3 p) {
    float f = 0.0;
    f += 0.5000 * noise3D(p); p = m3 * p * 2.02;
    f += 0.2500 * noise3D(p); p = m3 * p * 2.03;
    f += 0.1250 * noise3D(p); p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p); p = m3 * p * 2.02;
    f += 0.03125 * abs(noise3D(p));
    return f / 0.9375;
}

float distanceFunc(vec3 p, out float displace) {
    float d = length(p) - 0.5;
    displace = fbm3D(p * NOISE_FREQ + vec3(0, -1, 0) * iTime);
    d += displace * NOISE_AMP;
    return d;
}
```## 表演与作曲

### 性能提示

- 三个扭曲层 x 6 个八度 = 每像素 18 个噪声样本；添加点燃有限差分可以达到54
- **减少八度**：4 个而不是 6 个，性能增益约 33%，视觉差异最小
- **减少扭曲深度**：两层 `fbm(p + fbm(p))` 已经足够有机，节省约 33%
- **sin-product 噪声**： `sin(p.x)*sin(p.y)` 是无分支且无内存的，适合移动设备
- **GPU内置导数**：`dFdx/dFdy`代替有限差分，速度快3倍
- **纹理噪声**：预烘焙噪声纹理，交换内存读取的计算
- **LOD 自适应**：减少远处像素的倍频数
- **超级采样**：仅在需要抗锯齿时使用 2x2，4 倍性能成本

### 构图建议

- **射线行进**：扭曲标量场作为 SDF 位移函数 -> 火灾、爆炸、有机形式
- **极坐标变换**：极地空间中的域扭曲 -> 漩涡、星云、螺旋
- **余弦调色板**：`a + b*cos(2*pi*(c*t+d))` 比混合链更灵活
- **后处理**：绽放发光、色调映射 `col/(1+col)`、色差（RGB 通道偏移采样）
- **粒子/几何**：标量场驱动粒子速度场、顶点位移、UV 动画

## 进一步阅读

[参考](../reference/domain-warping.md) 中有完整的分步教程、数学推导和高级用法