# 水和海洋渲染 — 详细参考

本文档是 [SKILL.md](SKILL.md) 的完整参考，涵盖先决条件、每个步骤的详细说明、变体描述、深入的性能优化分析以及组合建议的完整代码示例。

## 先决条件

- **GLSL 基础知识**：统一、变化、内置函数
- **向量数学**：点积、叉积、反射/折射向量
- **基本光线行进概念**
- **FBM（分形布朗运动）/多倍频程噪声分层基础**
- **菲涅耳效应的物理直觉**：掠射角处强反射，法向入射处强透射

## 核心原则

水渲染的本质是解决三个核心问题：**水面形状生成**、**光与水面交互**、**水体颜色合成**。

### 1. 波浪生成：指数正弦分层 + 导数域扭曲

传统的正弦和使用“sin(x)”来产生对称波形，但真实的海浪具有**尖锐的波峰和宽阔的波谷**。核心公式：```
wave(x) = exp(sin(x) - 1)
```- 当 `sin(x) = 1`（峰值）时：`exp(0) = 1.0`，尖峰
- 当`sin(x) = -1`（谷）时：`exp(-2) ≈ 0.135`，宽阔平坦的谷

这自然会产生类似于格斯特纳波的**次摆线轮廓**，但计算成本要低得多。

当分层多个波浪时，关键的创新是**导数域扭曲（拖动）**：```
position += direction * derivative * weight * DRAG_MULT
```每个波浪层的采样位置都会被前一层的导数所抵消，从而导致小波纹自然地聚集在较大波浪的波峰上 - 模拟真实海洋中毛细波骑在重力波上的现象。

### 2. 照明模型：Schlick Fresnel + 次表面散射近似

**石里克菲涅尔近似**：```
F = F0 + (1 - F0) * (1 - dot(N, V))^5
```其中水的 F0 ≈ 0.04（法向入射时仅反射 4%）。

**次表面散射 (SSS)** 通过水厚度来近似：槽的水层较厚，蓝绿色散射较强；波峰的层数较薄，散射较弱，自然产生透明波峰和深蓝色波谷的视觉效果。

### 3.水面交汇：有界高地行进

水面被限制在“[0，-WATER_DEPTH]”的边界框中，并且光线仅在两个平面的交点之间行进。步长是自适应的：“step = ray_y - wave_height”——远离表面时大步长，靠近表面时小精确步长。

## 实施步骤

### 步骤 1：指数正弦波函数

**内容**：定义单向波的值和导数计算函数。

**为什么**：`exp(sin(x) - 1)` 将对称正弦转换为具有尖锐波峰和宽波谷的真实波形。它还返回解析导数，用于后续域扭曲和正常计算。

**代码**：```glsl
vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);     // Sharp crest, broad trough waveform
    float dx = wave * cos(x);            // Analytical derivative = exp(sin(x)-1) * cos(x)
    return vec2(wave, -dx);              // Return (value, negative derivative)
}
```### 步骤 2：具有域扭曲的多倍频程波形分层

**内容**：对具有不同方向、频率和速度的多个波进行分层，在每层之间应用导数驱动的位置偏移（阻力）。

**为什么**：单个波浪太规则了。多八度分层产生自然的复杂波形。域扭曲是关键——它使小波聚集在大波之上，这是区分“好看的海洋”和“普通噪音”的核心技术。 1.18 的频率增长率（而不是传统的 FBM 2.0）在波层之间创建更平滑的过渡。

**代码**：```glsl
#define DRAG_MULT 0.38  // Tunable: domain warp strength, 0=none, 0.5=strong clustering

float getwaves(vec2 position, int iterations) {
    float wavePhaseShift = length(position) * 0.1; // Break long-distance phase synchronization
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 2.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));  // Pseudo-random wave direction

        vec2 res = wavedx(position, p, frequency, iTime * timeMultiplier + wavePhaseShift);

        // Core: offset sampling position based on derivative (small waves ride big waves)
        position += p * res.y * weight * DRAG_MULT;

        sumOfValues += res.x * weight;
        sumOfWeights += weight;

        weight = mix(weight, 0.0, 0.2);      // Tunable: weight decay, 0.2 = 80% retained per layer
        frequency *= 1.18;                     // Tunable: frequency growth rate
        timeMultiplier *= 1.07;                // Tunable: higher frequency waves animate faster (dispersion)
        iter += 1232.399963;                   // Large irrational increment ensures uniform direction distribution
    }
    return sumOfValues / sumOfWeights;
}
```### 步骤 3：有界边界框射线行进

**什么**：将水面限制在两个水平面之间，并且仅在入口点和出口点之间行进。

**为什么**：比无限制的自卫队行军快得多。步长“pos.y - height”会自动适应——远离表面时跳跃较大，靠近表面时收敛良好。预先计算边界框交叉点可以避免在露天中浪费步骤。

**代码**：```glsl
#define WATER_DEPTH 1.0  // Tunable: water body thickness, affects SSS and wave amplitude

float intersectPlane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

float raymarchwater(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < 64; i++) {         // Tunable: march steps, 64 is usually sufficient
        float height = getwaves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);      // Adaptive step size
    }
    return distance(start, camera);          // If missed, assume hit at top surface
}
```### 步骤 4：距离平滑的正常计算

**什么**：使用有限差分计算水面法线，并根据距离向上方向插值以消除远处的混叠。

**为什么**：法线决定所有照明细节。与光线行进相比，对法线使用更多的波迭代（36 比 12）是一项核心性能技术 - 行进只需要粗略的形状，法线需要精细的细节。距离越远，高频法线越容易引起闪烁；向“(0,1,0)”平滑相当于隐式 LOD。

**代码**：```glsl
#define ITERATIONS_RAYMARCH 12  // Tunable: wave iterations for marching (fewer = faster)
#define ITERATIONS_NORMAL 36    // Tunable: wave iterations for normals (more = finer detail)

vec3 normal(vec2 pos, float e, float depth) {
    vec2 ex = vec2(e, 0);
    float H = getwaves(pos.xy, ITERATIONS_NORMAL) * depth;
    vec3 a = vec3(pos.x, H, pos.y);
    return normalize(
        cross(
            a - vec3(pos.x - e, getwaves(pos.xy - ex.xy, ITERATIONS_NORMAL) * depth, pos.y),
            a - vec3(pos.x, getwaves(pos.xy + ex.yx, ITERATIONS_NORMAL) * depth, pos.y + e)
        )
    );
}

// Distance smoothing: distant normals approach (0,1,0)
// N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
```### 步骤 5：菲涅耳反射和次表面散射

**内容**：使用 Schlick Fresnel 近似来计算反射/散射权重，将天空反射与深度相关的蓝绿色散射颜色相结合。

**原因**：菲涅尔效应是水面真实感的关键——近距离几乎完全透明，远处几乎完全反射。 SSS颜色“(0.0293,0.0698,0.1717)”来自深海散射光谱的经验值。槽槽水层较厚，SSS较强；波峰的层数较薄，SSS 较弱，自然会产生明暗变化。

**代码**：```glsl
// Schlick Fresnel, F0 = 0.04 (water's normal incidence reflectance)
float fresnel = 0.04 + 0.96 * pow(1.0 - max(0.0, dot(-N, ray)), 5.0);

// Reflection direction, force upward to avoid self-intersection
vec3 R = normalize(reflect(ray, N));
R.y = abs(R.y);

// Sky reflection + sun specular
vec3 reflection = getAtmosphere(R) + getSun(R);

// Subsurface scattering: deeper (trough) = bluer color
vec3 scattering = vec3(0.0293, 0.0698, 0.1717) * 0.1
                * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);

// Final compositing
vec3 C = fresnel * reflection + scattering;
```### 步骤 6：气氛和色调映射

**内容**：添加廉价的大气散射模型和 ACES 色调映射。

**为什么**：水面反射着天空，所以天空的质量直接影响水的外观。 `1/(ray.y + 0.1)` 近似光路长度，`vec3(5.5, 13.0, 22.4)/22.4` 表示瑞利散射系数比。 ACES 色调映射将 HDR 值映射到显示范围，在压缩阴影的同时保留高光细节。

**代码**：```glsl
vec3 extra_cheap_atmosphere(vec3 raydir, vec3 sundir) {
    float special_trick = 1.0 / (raydir.y * 1.0 + 0.1);
    float special_trick2 = 1.0 / (sundir.y * 11.0 + 1.0);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0);
    float sundt = pow(max(0.0, dot(sundir, raydir)), 8.0);
    float mymie = sundt * special_trick * 0.2;
    vec3 suncolor = mix(vec3(1.0), max(vec3(0.0), vec3(1.0) - vec3(5.5, 13.0, 22.4) / 22.4),
                        special_trick2);
    vec3 bluesky = vec3(5.5, 13.0, 22.4) / 22.4 * suncolor;
    vec3 bluesky2 = max(vec3(0.0), bluesky - vec3(5.5, 13.0, 22.4) * 0.002
                   * (special_trick + -6.0 * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24 + raysundt * 0.24);
    return bluesky2 * (1.0 + 1.0 * pow(1.0 - raydir.y, 3.0));
}

vec3 aces_tonemap(vec3 color) {
    mat3 m1 = mat3(
        0.59719, 0.07600, 0.02840,
        0.35458, 0.90834, 0.13383,
        0.04823, 0.01566, 0.83777);
    mat3 m2 = mat3(
        1.60475, -0.10208, -0.00327,
       -0.53108,  1.10813, -0.07276,
       -0.07367, -0.00605,  1.07602);
    vec3 v = m1 * color;
    vec3 a = v * (v + 0.0245786) - 0.000090537;
    vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
    return pow(clamp(m2 * (a / b), 0.0, 1.0), vec3(1.0 / 2.2));
}
```## 常见变体

### 变体 1：2D 水下苛性纹理

与基础版本的区别：没有 3D 光线行进 — 纯粹是 2D 屏幕空间效果。使用迭代三角形反馈回路生成焦散光图案，适合作为水下场景的地面投影纹理或作为覆盖层。

关键代码：```glsl
#define TAU 6.28318530718
#define MAX_ITER 5       // Tunable: iteration count, more = finer caustics

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 0.5 + 23.0;
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec2 p = mod(uv * TAU, TAU) - 250.0;   // mod TAU ensures tileability
    vec2 i = vec2(p);
    float c = 1.0;
    float inten = 0.005;  // Tunable: caustic line width (smaller = thinner)

    for (int n = 0; n < MAX_ITER; n++) {
        float t = time * (1.0 - (3.5 / float(n + 1)));
        i = p + vec2(cos(t - i.x) + sin(t + i.y), sin(t - i.y) + cos(t + i.x));
        c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten), p.y / (cos(i.y + t) / inten)));
    }
    c /= float(MAX_ITER);
    c = 1.17 - pow(c, 1.4);
    vec3 colour = vec3(pow(abs(c), 8.0));
    colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0); // Aqua blue tint
    fragColor = vec4(colour, 1.0);
}
```### 变体 2：FBM 凹凸贴图湖面（平面交点 + 凹凸贴图）

与基础版本的区别：没有每像素光线行进 - 使用分析平面相交 + FBM 凹凸贴图。速度极快，适用于遥远的湖面或必须将水嵌入复杂场景的情况（例如，具有体积云反射）。

关键代码：```glsl
// Water surface heightmap (FBM + abs folding produces ridge-like ripples)
float waterMap(vec2 pos) {
    mat2 m2 = mat2(0.60, -0.80, 0.80, 0.60); // Rotation matrix to avoid axis alignment
    vec2 posm = pos * m2;
    return abs(fbm(vec3(8.0 * posm, iTime)) - 0.5) * 0.1;
}

// Analytical plane intersection replaces ray marching
float t = -ro.y / rd.y;  // Water surface at y=0
vec3 hitPos = ro + rd * t;

// Finite difference normals (central differencing)
float eps = 0.1;
vec3 normal = vec3(0.0, 1.0, 0.0);
normal.x = -bumpfactor * (waterMap(hitPos.xz + vec2(eps, 0.0)) - waterMap(hitPos.xz - vec2(eps, 0.0))) / (2.0 * eps);
normal.z = -bumpfactor * (waterMap(hitPos.xz + vec2(0.0, eps)) - waterMap(hitPos.xz - vec2(0.0, eps))) / (2.0 * eps);
normal = normalize(normal);

// Bump strength fades with distance (LOD)
float bumpfactor = 0.1 * (1.0 - smoothstep(0.0, 60.0, distance(ro, hitPos)));

// Refraction uses the built-in refract() function
vec3 refracted = refract(rd, normal, 1.0 / 1.333);
```### 变体 3：脊状噪音海岸波浪

与基础版本的区别：使用“1 - abs(noise)”而不是“exp(sin)”来生成波形，并结合环内域扭曲。适用于具有更尖锐、更具冲击力的波浪并自然连接到海岸泡沫的沿海场景。

关键代码：```glsl
float sea(vec2 p) {
    float f = 1.0;
    float r = 0.0;
    float time = -iTime;
    for (int i = 0; i < 8; i++) {        // Tunable: 8 octaves
        r += (1.0 - abs(noise(p * f + 0.9 * time))) / f;  // Ridged noise
        f *= 2.0;
        p -= vec2(-0.01, 0.04) * (r - 0.2 * time / (0.1 - f)); // In-loop domain warping
    }
    return r / 4.0 + 0.5;
}

// Shore foam: based on distance between water surface and terrain
float dh = seaDist - rockDist; // Water-terrain SDF difference
float foam = 0.0;
if (dh < 0.0 && dh > -0.02) {
    foam = 0.5 * exp(20.0 * dh);   // Exponentially decaying shoreline glow
}
```### 变体 4：流量图水动画（河流/溪流）

与基础版本的区别：增加了流场驱动的FBM动画。使用两阶段时间循环来消除纹理拉伸，并根据地形梯度按程序生成水流方向。适用于江河、溪流等流向明确的水体。

关键代码：```glsl
// FBM with analytical derivatives + flow field offset
vec3 FBM_DXY(vec2 p, vec2 flow, float persistence, float domainWarp) {
    vec3 f = vec3(0.0);
    float tot = 0.0;
    float a = 1.0;
    for (int i = 0; i < 4; i++) {
        p += flow;
        flow *= -0.75;          // Negate + shrink each layer to prevent uniform sliding
        vec3 v = SmoothNoise_DXY(p);
        f += v * a;
        p += v.xy * domainWarp; // Gradient domain warping
        p *= 2.0;
        tot += a;
        a *= persistence;
    }
    return f / tot;
}

// Two-phase flow cycle (eliminates stretching)
float t0 = fract(time);
float t1 = fract(time + 0.5);
vec4 sample0 = SampleWaterNormal(uv + Hash2(floor(time)),     flowRate * (t0 - 0.5));
vec4 sample1 = SampleWaterNormal(uv + Hash2(floor(time+0.5)), flowRate * (t1 - 0.5));
float weight = abs(t0 - 0.5) * 2.0;
vec4 result = mix(sample0, sample1, weight);
```### 变体 5：比尔定律吸水率 + 体积散射

与基本版本的区别：用物理上正确的比尔-朗伯指数衰减代替简单的 SSS 近似，用于水下颜色吸收，加上前向散射项。适用于需要可调清水/浑水的现实场景。

关键代码：```glsl
// Beer-Lambert attenuation: red light absorbed fastest, blue light slowest
vec3 GetWaterExtinction(float dist) {
    float fOpticalDepth = dist * 6.0;     // Tunable: larger = more turbid water
    vec3 vExtinctCol = vec3(0.5, 0.6, 0.9); // Tunable: absorption spectrum (R decays fast, B slow)
    return exp2(-fOpticalDepth * vExtinctCol);
}

// Volumetric in-scattering
vec3 vInscatter = vSurfaceDiffuse * (1.0 - exp(-refractDist * 0.1))
               * (1.0 + dot(sunDir, viewDir));  // Forward scattering enhancement

// Final underwater color
vec3 underwaterColor = terrainColor * GetWaterExtinction(waterDepth) + vInscatter;

// Fresnel compositing
vec3 finalColor = mix(underwaterColor, reflectionColor, fresnel);
```## 深入的性能优化

### 1.双迭代计数策略（最关键的优化）

射线行进使用很少的迭代 (12)，正常计算使用很多 (36)。行军只需要一个大概的交点；法线需要精细的波浪细节。这种单一技术可以将渲染时间减半，而视觉质量几乎没有损失。

### 2.距离自适应法线平滑```glsl
N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
```远距离法线接近“(0,1,0)”，消除了远距离处的高频闪烁（相当于隐式法线 mipmapping），同时节省了远距离昂贵的法线计算。

### 3.边界框裁剪

预先计算光线与顶部和底部水平面的交点，并且仅在两个交点之间行进。指向天空的光线 (`ray.y >= 0`) 完全跳过水面计算——最简单、最有效的提前退出。

### 4.自适应步长

`pos += dir * (pos.y - height)` 使用当前高度差作为步长——远离表面时可能会跳跃很远的距离，接近时会自动缩小。比固定步长快 3-5 倍。

### 5. 滤波器宽度感知正常衰减（高级）

对于需要更精确 LOD 的场景：```glsl
vec2 vFilterWidth = max(abs(dFdx(uv)), abs(dFdy(uv)));
float fScale = 1.0 / (1.0 + max(vFilterWidth.x, vFilterWidth.y) * max(vFilterWidth.x, vFilterWidth.y) * 2000.0);
normalStrength *= fScale;
```使用屏幕空间导数自动检测像素覆盖区域 - 区域越大，法线越平坦。这是手动 mipmap 的精确实现。

### 6. LOD 条件详细信息```glsl
if (distanceToSurface < threshold) {
    // Only compute high-frequency detail when close to the water surface
    for (int i = 0; i < detailOctaves; i++) { ... }
}
```水面高频位移SDF仅在接近水面时计算；在远处，直接使用基面，避免不必要的噪声采样。

## 组合建议

### 1. 与体积云结合

在水面上加入云反射是增强真实感的关键。步骤：首先沿着反射方向“R”进行体积云光线行进，然后在菲涅尔合成中混合云颜色作为“反射”的一部分。这是水渲染着色器中的常见技术。

### 2. 与地形系统结合

海岸线渲染需要水面SDF和地形SDF之间的交互。关键技术：保持“dh = waterSDF -terrainSDF”，并在“dh ≈ 0”时渲染泡沫（“exp(k * dh)”产生指数衰减的海岸辉光）。海岸线渲染的标准技术。

### 3. 与焦散相结合

在水下场景中，将变体 1 中的焦散纹理投影到水下地形表面。将焦散强度调节为“焦散 * exp(-waterDepth * 吸收)”，以实现基于深度的衰减。

### 4. 与雾/大气散射相结合

远处的水面必须融入大气雾中。使用独立消光+内散射雾模型（不是简单的 lerp），每个 RGB 通道独立衰减：```glsl
vec3 fogExtinction = exp2(fogExtCoeffs * -distance);
vec3 fogInscatter = fogColor * (1.0 - exp2(fogInCoeffs * -distance));
finalColor = finalColor * fogExtinction + fogInscatter;
```### 5.与后处理结合

- **绽放**：水面上的太阳镜面高光需要绽放才能看起来自然；斐波那契螺旋模糊比简单的高斯模糊效果更好
- **色调映射**：ACES 是海洋场景的标准选择，在压缩阴影的同时保留阳光高光
- **景深 (DOF)**：聚焦于近处和远处模糊的中地波，大大提高了电影质量（后处理散景 DOF）