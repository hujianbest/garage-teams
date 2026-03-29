# 纹理采样详细参考

本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、分步解释、数学推导、变体详细信息以及完整的组合代码示例。

## 先决条件

- **GLSL 基本语法**：`vec2`/`vec3`/`vec4`、`uniform sampler2D` 以及其他类型和声明
- **UV 坐标系**：“fragCoord / iResolution.xy”标准化为“[0,1]”，原点位于左下角
- **Mipmap 概念**：纹理的多分辨率金字塔，每个级别的分辨率为一半。 GPU 根据屏幕空间导数自动选择适当的级别以避免锯齿
- **ShaderToy Multi-Pass Architecture**：图像通道是最终输出，缓冲区 A/B/C/D 是中间计算通道，通过“iChannel0~3”绑定到纹理或缓冲区

## 实施步骤

### 第 1 步：基本纹理采样和 UV 归一化

**什么**：将屏幕像素坐标转换为UV坐标并读取纹理数据。

**为什么**：`texture()` 接受 `[0,1]` 范围内的 UV 坐标。 ShaderToy提供像素坐标“fragCoord”，需要通过除以分辨率来标准化。```glsl
// Normalize UV
vec2 uv = fragCoord / iResolution.xy;

// Basic texture sampling (hardware bilinear filtering)
vec4 col = texture(iChannel0, uv);
```硬件双线性过滤自动在最近的 4 个纹素之间执行线性插值。当UV恰好落在纹素中心时，返回准确的值；当它落在纹素之间时，返回周围四个点的加权平均值。

### 步骤2：使用textureLod控制Mipmap级别

**什么**：显式指定 LOD 级别来控制采样分辨率，实现模糊或避免光线行进中的自动 mip 选择。

**原因**：在光线行进中，GPU 无法正确估计屏幕空间导数，这会导致错误的 Mip 级别选择和伪影。使用 `textureLod(..., 0.0)` 强制以最高分辨率级别采样；使用较高的 LOD 值会产生模糊效果（例如景深、光晕）。

LOD值的物理意义：
- `lod = 0.0`：原始分辨率（mip 0）
- `lod = 1.0`：半分辨率 (mip 1)，相当于 2x2 区域平均值
- `lod = N`：分辨率是原始分辨率的 1/2^N```glsl
// In ray marching: force LOD 0 to avoid artifacts (from Campfire at night)
vec3 groundCol = textureLod(iChannel2, groundUv * 0.05, 0.0).rgb;

// Depth of field blur: LOD varies with distance (from Heartfelt)
float focus = mix(maxBlur - coverage, minBlur, smoothstep(.1, .2, coverage));
vec3 col = textureLod(iChannel0, uv + normal, focus).rgb;

// Bloom: explicitly sample high mip levels (from Campfire at night)
#define BLOOM_LOD_A 4.0  // Adjustable: bloom first layer mip level
#define BLOOM_LOD_B 5.0  // Adjustable: bloom second layer mip level
#define BLOOM_LOD_C 6.0  // Adjustable: bloom third layer mip level
vec3 bloom = vec3(0.0);
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_A), BLOOM_LOD_A).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_B), BLOOM_LOD_B).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_C), BLOOM_LOD_C).rgb;
bloom /= 3.0;
```### 步骤 3：使用 texelFetch 进行精确的像素数据访问

**什么**：使用整数坐标读取特定纹素的值，绕过所有过滤。

**为什么**：当纹理用作数据存储（游戏状态、预先计算的 LUT、键盘输入）时，必须读取特定像素的精确值 - 硬件过滤会破坏数据完整性。 `texelFetch` 使用 `ivec2` 整数坐标而不是 `vec2` 浮点 UV，直接通过地址访问像素，类似于数组索引。```glsl
// Define data storage addresses (from Bricks Game)
const ivec2 txBallPosVel = ivec2(0, 0);
const ivec2 txPaddlePos  = ivec2(1, 0);
const ivec2 txPoints     = ivec2(2, 0);
const ivec2 txState      = ivec2(3, 0);

// Read stored data
vec4 loadValue(in ivec2 addr) {
    return texelFetch(iChannel0, addr, 0);
}

// Write data (in buffer pass)
void storeValue(in ivec2 addr, in vec4 val, inout vec4 fragColor, in ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

// Read keyboard input (ShaderToy keyboard texture)
float key = texelFetch(iChannel1, ivec2(KEY_SPACE, 0), 0).x;
```### 步骤 4：手动双线性插值 + 五次 Hermite 平滑

**内容**：通过手动采样 4 个纹素并使用五次 Hermite 多项式进行插值以实现 C² 连续性，绕过硬件双线性过滤。

**为什么**：硬件双线性插值是线性的（C⁰连续），在对噪声FBM分层时会产生可见的网格状接缝。五次 Hermite 插值在采样点处具有零一阶和二阶导数，从而消除了这些伪影。

**数学推导**：

标准双线性插值使用线性权重“u = f”（其中“f = fract(x)”），这会导致边界处的导数不连续。

五次 Hermite 多项式：`u = f³(6f² - 15f + 10)`

验证 C² 连续性：
- `u(0) = 0`, `u(1) = 1` — 正确的插值边界
- `u'(f) = 30f²(f-1)²` → `u'(0) = 0`, `u'(1) = 0` — 一阶导数在边界处为零
- `u''(f) = 60f(f-1)(2f-1)` → `u''(0) = 0`, `u''(1) = 0` — 二阶导数在边界处为零```glsl
// Manual four-point sampling + quintic Hermite interpolation (from up in the cloud sea)
float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);

    // Quintic Hermite smoothing (C2 continuous)
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);

    // Manual sampling of four corner points (divided by texture resolution for normalization)
    #define TEX_RES 1024.0  // Adjustable: noise texture resolution
    float a = texture(iChannel0, (p + vec2(0.0, 0.0)) / TEX_RES).x;
    float b = texture(iChannel0, (p + vec2(1.0, 0.0)) / TEX_RES).x;
    float c = texture(iChannel0, (p + vec2(0.0, 1.0)) / TEX_RES).x;
    float d = texture(iChannel0, (p + vec2(1.0, 1.0)) / TEX_RES).x;

    // Bilinear blending
    return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}
```### 步骤 5：来自纹理的 FBM（分数布朗运动）噪声

**什么**：通过以不同频率分层多个纹理样本来构建多尺度程序噪声。

**为什么**：单个噪声样本缺乏自然界中发现的多尺度细节。 FBM 通过以双倍频率和减半振幅分层来模拟自然纹理的 1/f 光谱特性。大多数自然纹理（地形、云、岩石）都表现出 1/f 噪声特征 - 低频包含大部分能量，高频添加细节。

FBM 公式：`fbm(x) = Σ (余辉^i × 噪声(2^i × x))` for i = 0..N-1

参数效果：
- **OCTAVES（层数）**：层数越多，细节越多，但每增加一层，就会增加一个完整的噪声调用
- **持久性**：控制较高频率下的振幅衰减率。 0.5是经典值；较高的值 (0.6-0.7) 会产生较粗糙的纹理；较低的值 (0.3-0.4) 会产生更平滑的纹理```glsl
#define FBM_OCTAVES 5       // Adjustable: number of layers, more = richer detail
#define FBM_PERSISTENCE 0.5 // Adjustable: amplitude decay rate, higher = stronger high-frequency detail

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;          // Initial amplitude
    float totalWeight = 0.0;
    for (int i = 0; i < FBM_OCTAVES; i++) {
        v += a * noise(x);
        totalWeight += a;
        x *= 2.0;           // Double frequency
        a *= FBM_PERSISTENCE;
    }
    return v / totalWeight;
}
```### 步骤 6：可分离高斯模糊（多通道卷积）

**什么**：将 2D 高斯模糊分解为水平和垂直通道，每个通道执行 1D 卷积。

**为什么**：直接 NxN 2D 卷积需要 N² 样本；分离后，只需要2N。这利用了高斯核的可分离性——一个 2D 高斯函数可以分解为两个 1D 高斯函数的乘积：“G(x,y) = G(x) × G(y)”。 `fract()` 包装坐标以实现环面边界条件，避免边缘伪影。

优化技巧：利用硬件双线性过滤的“自由”插值 - 两个纹素之间的采样给出单个“texture()”调用两个纹素的加权平均值，通过“(N+1)/2”样本实现 N-tap 效果。```glsl
// Horizontal blur pass (from expansive reaction-diffusion)
#define BLUR_RADIUS 4  // Adjustable: blur radius (kernel width = 2*BLUR_RADIUS+1)

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 d = vec2(1.0 / iResolution.x, 0.0); // Horizontal step

    // 9-tap Gaussian weights (sigma ≈ 2.0)
    float w[9] = float[9](0.05, 0.09, 0.12, 0.15, 0.16, 0.15, 0.12, 0.09, 0.05);

    vec4 col = vec4(0.0);
    for (int i = -4; i <= 4; i++) {
        col += w[i + 4] * texture(iChannel0, fract(uv + float(i) * d));
    }
    col /= 0.98; // Weight normalization correction
    fragColor = col;
}

// Vertical blur pass: change d to vec2(0.0, 1.0/iResolution.y)
```### 步骤 7：色散采样（波长相关位移）

**内容**：沿着具有不同偏移的位移矢量对纹理进行多次采样，并通过光谱响应曲线进行加权，以模拟棱镜色散。

**为什么**：不同波长的真实光具有不同的折射率，导致空间色分离。通过沿着位移方向逐渐偏移 UV 并在每个 RGB 通道上累加不同的权重，可以模拟这种物理现象。

谱响应权重的设计原则：
- **红色通道** `t²`：在长波长端增强；红光位于光谱的远端
- **绿色通道** `46.6666 × ((1-t) × t)³`：中波长峰值，模拟人眼对绿色的最大敏感度
- **蓝色通道** `(1-t)²`：在短波长端增强；蓝光位于光谱的近端```glsl
#define DISP_SAMPLES 64  // Adjustable: dispersion sample count, more = smoother

// Spectral response weights (simulating human eye cone response)
vec3 sampleWeights(float i) {
    return vec3(
        i * i,                            // Red: long wavelength enhancement
        46.6666 * pow((1.0 - i) * i, 3.0), // Green: middle wavelength peak
        (1.0 - i) * (1.0 - i)             // Blue: short wavelength enhancement
    );
}

// Dispersion sampling
vec3 sampleDisp(sampler2D tex, vec2 uv, vec2 disp) {
    vec3 col = vec3(0.0);
    vec3 totalWeight = vec3(0.0);
    for (int i = 0; i < DISP_SAMPLES; i++) {
        float t = float(i) / float(DISP_SAMPLES);
        vec3 w = sampleWeights(t);
        col += w * texture(tex, fract(uv + disp * t)).rgb;
        totalWeight += w;
    }
    return col / totalWeight;
}
```### 步骤 8：IBL 环境采样（textureLod + 粗糙度映射）

**内容**：根据基于图像的照明的表面粗糙度选择立方体贴图 mipmap 级别。

**为什么**：在PBR中，粗糙的表面需要从更广泛的环境中收集光照（相当于模糊的环境贴图）。高 mipmap 级别自然对应于环境贴图的模糊版本，因此粗糙度可以直接映射到 LOD 级别。这就是Epic Games在UE4中推广的split-sum近似方法。

完整的 split-sum IBL 工作流程：
1.预过滤环境贴图：不同的粗糙度值对应不同的mip级别
2. 预计算 BRDF LUT： `vec2(NdotV, roughness)` -> `vec2(scale,bias)`
3.最终合成：`specular = envColor * (F * brdf.x + brdf.y)````glsl
#define MAX_LOD 7.0     // Adjustable: cubemap maximum mip level
#define DIFFUSE_LOD 6.5 // Adjustable: diffuse sampling LOD (near the blurriest level)

// Specular IBL (from Old watch)
vec3 getSpecularLightColor(vec3 N, float roughness) {
    vec3 raw = textureLod(iChannel0, N, roughness * MAX_LOD).rgb;
    return pow(raw, vec3(4.5)) * 6.5; // HDR approximation boost
}

// Diffuse irradiance IBL
vec3 getDiffuseLightColor(vec3 N) {
    return textureLod(iChannel0, N, DIFFUSE_LOD).rgb;
}

// BRDF LUT query (precomputed split-sum approximation)
vec2 brdf = texture(iChannel3, vec2(NdotV, roughness)).rg;
vec3 specular = envColor * (F * brdf.x + brdf.y);
```## 变体详细信息

### 变体 1：各向异性流场模糊

**与基本版本的区别**：不是均匀的高斯模糊，而是沿着噪声驱动的方向场执行定向模糊，产生流动的笔触效果。方向场可以来自噪声纹理、速度场或用户定义的矢量场。抛物线权重“4h(1-h)”使路径中心的模糊最强，两端最弱，从而产生更自然的拖尾效果。```glsl
#define BLUR_ITERATIONS 32  // Adjustable: number of samples along flow field
#define BLUR_STEP 0.008     // Adjustable: UV offset per step

vec3 flowBlur(vec2 uv) {
    vec3 col = vec3(0.0);
    float acc = 0.0;
    for (int i = 0; i < BLUR_ITERATIONS; i++) {
        float h = float(i) / float(BLUR_ITERATIONS);
        float w = 4.0 * h * (1.0 - h); // Parabolic weight
        col += w * texture(iChannel0, uv).rgb;
        acc += w;
        // Direction from noise texture (or other vector field)
        vec2 dir = texture(iChannel1, uv).xy * 2.0 - 1.0;
        uv += BLUR_STEP * dir;
    }
    return col / acc;
}
```### 变体 2：纹理作为数据存储（缓冲区作为数据）

**与基本版本的区别**：纹理存储结构化数据（位置、速度、状态）而不是颜色，使用“texelFetch”进行精确读取以实现帧间持久状态。

该模式的关键是“地址-值”映射：每个像素坐标是一个“地址”，“vec4”是存储的“值”。在缓冲区通道中，着色器对每个像素执行，但仅在“fragPos == addr”时写入新值；所有其他像素保留其旧值。这样就实现了选择性写入。

适用场景：游戏状态（生命值、得分、位置）、粒子系统参数、物理模拟全局变量。```glsl
// Address definitions
const ivec2 txPosition = ivec2(0, 0);
const ivec2 txVelocity = ivec2(1, 0);
const ivec2 txState    = ivec2(2, 0);

// Data read/write interface
vec4 load(ivec2 addr) { return texelFetch(iChannel0, addr, 0); }

void store(ivec2 addr, vec4 val, inout vec4 fragColor, ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

// Usage in mainImage
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 p = ivec2(fragCoord);
    fragColor = texelFetch(iChannel0, p, 0); // Default: keep old value

    vec4 pos = load(txPosition);
    vec4 vel = load(txVelocity);
    // ... update logic ...
    store(txPosition, pos + vel * 0.016, fragColor, p);
    store(txVelocity, vel, fragColor, p);
}
```### 变体 3：色散

**与基本版本的区别**：沿位移矢量多次采样，每次采样具有不同的偏移量，并具有与波长相关的加权 RGB 累积，产生棱镜色散效果。 “DISP_STRENGTH”控制色散的空间范围 - 值越大，RGB 分离就越明显。```glsl
#define DISP_SAMPLES 64     // Adjustable: sample count
#define DISP_STRENGTH 0.05  // Adjustable: dispersion strength

vec3 dispersion(vec2 uv, vec2 displacement) {
    vec3 col = vec3(0.0);
    vec3 w_total = vec3(0.0);
    for (int i = 0; i < DISP_SAMPLES; i++) {
        float t = float(i) / float(DISP_SAMPLES);
        vec3 w = vec3(t * t, 46.666 * pow((1.0 - t) * t, 3.0), (1.0 - t) * (1.0 - t));
        col += w * texture(iChannel0, fract(uv + displacement * t * DISP_STRENGTH)).rgb;
        w_total += w;
    }
    return col / w_total;
}
```### 变体 4：三平面纹理映射

**与基本版本的区别**：对于 3D 表面，使用三个投影方向（X/Y/Z 轴）采样纹理并按法线权重混合，避免传统 UV 贴图的接缝问题。

`TRIPLANAR_SHARPNESS` 控制混合过渡锐度：值越高，投影面之间的过渡越锐利；值 1.0 提供最平滑但可能模糊的过渡。典型值为 2.0-4.0。

适用场景：程序地形（无法提前进行UV展开的情况）、SDF射线行进生成的几何体。```glsl
#define TRIPLANAR_SHARPNESS 2.0  // Adjustable: blend sharpness

vec3 triplanarSample(sampler2D tex, vec3 pos, vec3 normal, float scale) {
    vec3 w = pow(abs(normal), vec3(TRIPLANAR_SHARPNESS));
    w /= (w.x + w.y + w.z); // Normalize weights

    vec3 xSample = texture(tex, pos.yz * scale).rgb;
    vec3 ySample = texture(tex, pos.xz * scale).rgb;
    vec3 zSample = texture(tex, pos.xy * scale).rgb;

    return xSample * w.x + ySample * w.y + zSample * w.z;
}
```### 变体 5：时间重投影 (TAA)

**与基础版本的区别**：计算当前帧像素在前一帧中的UV位置，从缓冲区中采样前一帧数据，并进行混合以实现时间抗锯齿或累积效果。

`TAA_BLEND` 控制历史帧权重：较高的值（例如 0.95）提供更好的时间稳定性，但更多的运动拖尾；较低的值（例如 0.8）提供更快的响应，但闪烁更多。钳制操作可以防止重影——当历史颜色超过当前帧的邻域范围时，表明场景发生了较大的变化，并且应该减少历史权重。```glsl
#define TAA_BLEND 0.9  // Adjustable: history frame blend ratio (higher = smoother but more trailing)

vec3 temporalBlend(vec2 currUv, vec2 prevUv, vec3 currColor) {
    vec3 history = textureLod(iChannel0, prevUv, 0.0).rgb;
    // Simple clamp to prevent ghosting
    vec3 minCol = currColor - 0.1;
    vec3 maxCol = currColor + 0.1;
    history = clamp(history, minCol, maxCol);
    return mix(currColor, history, TAA_BLEND);
}
```## 性能优化详情

### 瓶颈1：纹理采样带宽

- **问题**：大量 `texture()` 调用（例如 64 个色散样本）是 GPU 带宽密集型操作
- **优化**：减少样本数量并通过更智能的重量功能进行补偿；使用 mipmap（高 LOD 处的“textureLod”）来减少缓存未命中
- **详细信息**：GPU纹理缓存在缓存行中工作；当相邻像素访问相似的纹理区域时，缓存命中率很高。 LOD 级别越高的纹理越小，并且更有可能完全适合缓存。对于色散采样，请考虑首先在低分辨率缓冲区中执行色散，然后进行双线性上采样

### 瓶颈2：可分离模糊

- **问题**：2D 高斯模糊需要 N² 样本
- **优化**：始终使用可分离的两遍方法（水平+垂直），将复杂性从 O(N²) 降低到 O(2N)
- **高级技巧**：利用硬件双线性过滤的“自由”插值 - 两个纹素之间的采样使硬件自动返回加权平均值，从而通过“(N+1)/2”样本实现 N-tap 效果。例如，9-tap 高斯仅需要 5 个纹理样本

### 瓶颈 3：Ray Marching 中的 Mip 选择

- **问题**：GPU 的屏幕空间导数 (`dFdx`/`dFdy`) 在光线行进循环内不正确，因为相邻像素可能处于完全不同的光线行进步骤，从而导致错误的自动 Mip 级别选择
- **优化**：在光线行进循环内的所有纹理查询中使用 `textureLod(..., 0.0)` 来强制基本级别
- **替代**：如果需要 mipmap 抗锯齿，请手动计算 LOD：根据光线长度和表面倾斜角度估计屏幕空间覆盖范围，然后使用“log2()”转换为 LOD

### 瓶颈 4：高频噪声的手动插值

- **问题**：手动四点采样 + Hermite 插值比硬件双线性大约慢 4 倍（4 个 `texture()` 调用 + 数学 vs. 1 个硬件过滤的 `texture()` 调用）
- **优化**：仅在视觉差异明显时使用它（FBM 的前 1-2 个八度）；较高频率的八度音阶可以回退到“texture()”，因为差异不再可见
- **权衡**：对于 6 倍频程 FBM，对前 2 个八度音阶（8 个样本）使用 Hermite，对后 4 个八度音阶（8 个样本）使用硬件双线性，总共 12 个样本 — 完整 Hermite 所需 24 个样本的一半

### 瓶颈 5：多缓冲区反馈延迟

- **问题**：多通道反馈循环中的每个缓冲区都会增加一帧的延迟（因为缓冲区的输出只能在下一帧中读取）
- **优化**：尽可能将可合并操作合并到一个通道中；使用 `texelFetch` 而不是 `texture` 来读取缓冲区数据，以避免不必要的过滤开销
- **架构建议**：设计缓冲区拓扑时，尽量减少反馈链长度。如果A→B→C→A形成三帧延迟循环，则考虑B和C是否可以合并为单通道

## 完整的组合代码示例

### 与 SDF Ray Marching 结合

纹理采样为 SDF 场景提供表面细节：采样噪声纹理以进行位移贴图、材质查找。关键：“textureLod(..., 0.0)”必须在光线行进循环内使用。```glsl
// Using texture noise for detail displacement in an SDF scene
float map(vec3 p) {
    float d = length(p) - 1.0; // Base sphere SDF

    // Texture noise displacement (must use textureLod inside ray march)
    float n = textureLod(iChannel0, p.xz * 0.5, 0.0).x;
    d += n * 0.1; // Surface detail

    return d;
}

// Material query also uses textureLod
vec3 getMaterial(vec3 p, vec3 n) {
    // Triplanar mapping for material color
    vec3 w = pow(abs(n), vec3(2.0));
    w /= (w.x + w.y + w.z);
    vec3 col = textureLod(iChannel1, p.yz * 0.5, 0.0).rgb * w.x
             + textureLod(iChannel1, p.xz * 0.5, 0.0).rgb * w.y
             + textureLod(iChannel1, p.xy * 0.5, 0.0).rgb * w.z;
    return col;
}
```### 与程序噪声相结合（域扭曲）

基于纹理的噪声（手动 Hermite + FBM）作为域扭曲的驱动器，用于生成地形、云、火焰和其他自然效果。纹理噪声比纯数学噪声更快（一个纹理样本与多个哈希计算）。```glsl
// Domain warping: use FBM to warp FBM's input coordinates
float domainWarp(vec2 p) {
    // First warping layer
    vec2 q = vec2(fbm(p + vec2(0.0, 0.0)),
                  fbm(p + vec2(5.2, 1.3)));

    // Second warping layer (more complex effect)
    vec2 r = vec2(fbm(p + 4.0 * q + vec2(1.7, 9.2)),
                  fbm(p + 4.0 * q + vec2(8.3, 2.8)));

    return fbm(p + 4.0 * r);
}
```### 与后处理管道结合

针对光晕的多 LOD 采样、针对景深的可分离高斯模糊、针对色差的色散采样。这些技术可以链接成完整的后处理流程。```glsl
// Complete post-processing chain (single-pass simplified version)
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // 1. Read scene color (from Buffer A)
    vec3 col = texture(iChannel0, uv).rgb;

    // 2. Bloom (multi-LOD sampling)
    vec3 bloom = vec3(0.0);
    bloom += textureLod(iChannel0, uv, 4.0).rgb * 0.5;
    bloom += textureLod(iChannel0, uv, 5.0).rgb * 0.3;
    bloom += textureLod(iChannel0, uv, 6.0).rgb * 0.2;
    col += bloom * 0.3;

    // 3. Chromatic aberration (simplified 3-tap)
    vec2 dir = uv - 0.5;
    float strength = length(dir) * 0.02;
    col.r = texture(iChannel0, uv + dir * strength).r;
    col.b = texture(iChannel0, uv - dir * strength).b;

    // 4. Tone mapping (Filmic)
    col = (col * (6.2 * col + 0.5)) / (col * (6.2 * col + 1.7) + 0.06);

    // 5. Vignette
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.2);

    fragColor = vec4(col, 1.0);
}
```### 与 PBR/IBL 光照相结合

“textureLod”根据基于图像的光照的粗糙度对立方体贴图进行采样，并结合预先计算的 BRDF LUT（通过“texelFetch”或“texture”查询），形成完整的 split-sum IBL 管道。```glsl
// Complete IBL lighting computation
vec3 computeIBL(vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    float NdotV = max(dot(N, V), 0.0);
    vec3 R = reflect(-V, N);

    // Fresnel (Schlick approximation)
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 F = F0 + (1.0 - F0) * pow(1.0 - NdotV, 5.0);

    // Specular: sample pre-filtered environment map by roughness
    vec3 specEnv = textureLod(iChannel0, R, roughness * 7.0).rgb;
    specEnv = pow(specEnv, vec3(4.5)) * 6.5; // HDR approximation

    // BRDF LUT query
    vec2 brdf = texture(iChannel3, vec2(NdotV, roughness)).rg;
    vec3 specular = specEnv * (F * brdf.x + brdf.y);

    // Diffuse irradiance
    vec3 diffEnv = textureLod(iChannel0, N, 6.5).rgb;
    vec3 kD = (1.0 - F) * (1.0 - metallic);
    vec3 diffuse = kD * albedo * diffEnv;

    return diffuse + specular;
}
```### 与模拟/反馈系统相结合

用于反应扩散、流体模拟和其他迭代系统的多缓冲区纹理采样。缓冲区 A 存储状态，缓冲区 B/C 执行可分离的模糊扩散，图像通道处理最终可视化。 `fract()` 包装圆环边界的坐标。```glsl
// Buffer A: Reaction-diffusion state update
// iChannel0: Buffer A itself (feedback)
// iChannel1: Buffer B (result after horizontal blur)
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 px = 1.0 / iResolution.xy;

    // Read current state and diffused state
    vec2 state = texelFetch(iChannel0, ivec2(fragCoord), 0).xy;
    vec2 diffused = texture(iChannel1, uv).xy; // After separable blur

    // Gray-Scott reaction-diffusion
    float a = diffused.x;
    float b = diffused.y;
    float feed = 0.037;
    float kill = 0.06;

    float da = 1.0 * (diffused.x - state.x) - a * b * b + feed * (1.0 - a);
    float db = 0.5 * (diffused.y - state.y) + a * b * b - (kill + feed) * b;

    state += vec2(da, db) * 0.9;
    state = clamp(state, 0.0, 1.0);

    fragColor = vec4(state, 0.0, 1.0);
}
```
