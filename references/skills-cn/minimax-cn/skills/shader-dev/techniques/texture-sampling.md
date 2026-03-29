**重要 - GLSL 类型严格性**：
- GLSL是强类型语言，不支持`string`类型（不能定义`string var`）
- `vec2`/`vec3`/`vec4` 是向量类型，不能直接分配浮点数（例如，`vec2 a = 1.0` 必须是 `vec2 a = vec2(1.0)`）
- 数组索引必须是整型常量或统一变量；无法使用运行时计算的浮点数
- 避免未初始化的变量 - GLSL 默认值未定义

# 纹理采样

## 用例

- **后处理效果**：模糊、晕染、色散、色差
- **程序噪声**：FBM 从噪声纹理分层以生成地形、云、火
- **PBR/IBL**：立方体贴图环境照明、BRDF LUT 查找
- **模拟/反馈系统**：反应扩散、流体模拟多缓冲区反馈
- **数据存储**：用作结构化数据的纹理（游戏状态、键盘输入）
- **时间累积**：TAA、运动模糊、前一帧读取

## 核心原则

|功能|坐标类型|过滤|典型用途|
|----------|----------------|------------|-------------|
| `纹理（采样器，uv）` |浮动 UV `[0,1]` |硬件双线性|一般纹理阅读 |
| `textureLod（采样器，uv，lod）` |浮动 UV + LOD |指定的 mip 级别 |控制模糊级别/避免自动 mip |
| `texelFetch（采样器，ivec2，lod）` |整数像素坐标 |没有过滤 |精确的像素数据读取 |

关键数学：
1. **硬件双线性插值**：`texture()`在4个相邻纹理像素之间自动线性混合
2. **五次 Hermite 平滑**：`u = f^3(6f^2 - 15f + 10)`，C2 连续（消除硬件线性插值接缝）
3. **LOD控制**：`textureLod`第三个参数选择mipmap级别，`lod=0`为原始分辨率，每+1使分辨率减半
4. **坐标环绕**：`fract(uv)`实现环面边界，相当于`GL_REPEAT`

## 实施步骤

### 第 1 步：基本采样和 UV 归一化```glsl
vec2 uv = fragCoord / iResolution.xy;
vec4 col = texture(iChannel0, uv);
```### 步骤 2：Mipmap 控制的textureLod```glsl
// In ray marching: force LOD 0 to avoid artifacts
vec3 groundCol = textureLod(iChannel2, groundUv * 0.05, 0.0).rgb;

// Depth of field blur: LOD varies with distance
float focus = mix(maxBlur - coverage, minBlur, smoothstep(.1, .2, coverage));
vec3 col = textureLod(iChannel0, uv + normal, focus).rgb;

// Bloom: sample high mip levels
#define BLOOM_LOD_A 4.0  // adjustable: bloom first mip level
#define BLOOM_LOD_B 5.0
#define BLOOM_LOD_C 6.0
vec3 bloom = vec3(0.0);
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_A), BLOOM_LOD_A).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_B), BLOOM_LOD_B).rgb;
bloom += textureLod(iChannel0, uv + off * exp2(BLOOM_LOD_C), BLOOM_LOD_C).rgb;
bloom /= 3.0;
```### 步骤 3：texelFetch 进行精确的像素读取```glsl
// Data storage addresses
const ivec2 txBallPosVel = ivec2(0, 0);
const ivec2 txPaddlePos  = ivec2(1, 0);
const ivec2 txPoints     = ivec2(2, 0);
const ivec2 txState      = ivec2(3, 0);

vec4 loadValue(in ivec2 addr) {
    return texelFetch(iChannel0, addr, 0);
}

void storeValue(in ivec2 addr, in vec4 val, inout vec4 fragColor, in ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

// Keyboard input
float key = texelFetch(iChannel1, ivec2(KEY_SPACE, 0), 0).x;
```### 步骤 4：手动双线性 + 五次 Hermite 平滑```glsl
float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0); // C2 continuous

    #define TEX_RES 1024.0  // adjustable: noise texture resolution
    float a = texture(iChannel0, (p + vec2(0.0, 0.0)) / TEX_RES).x;
    float b = texture(iChannel0, (p + vec2(1.0, 0.0)) / TEX_RES).x;
    float c = texture(iChannel0, (p + vec2(0.0, 1.0)) / TEX_RES).x;
    float d = texture(iChannel0, (p + vec2(1.0, 1.0)) / TEX_RES).x;

    return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}
```### 步骤 5：FBM 纹理噪声```glsl
#define FBM_OCTAVES 5       // adjustable: number of layers
#define FBM_PERSISTENCE 0.5 // adjustable: amplitude decay rate

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    float totalWeight = 0.0;
    for (int i = 0; i < FBM_OCTAVES; i++) {
        v += a * noise(x);
        totalWeight += a;
        x *= 2.0;
        a *= FBM_PERSISTENCE;
    }
    return v / totalWeight;
}
```### 步骤 6：可分离高​​斯模糊```glsl
#define BLUR_RADIUS 4  // adjustable: blur radius

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 d = vec2(1.0 / iResolution.x, 0.0); // horizontal pass; for vertical pass change to vec2(0, 1/iResolution.y)
    float w[9] = float[9](0.05, 0.09, 0.12, 0.15, 0.16, 0.15, 0.12, 0.09, 0.05);

    vec4 col = vec4(0.0);
    for (int i = -4; i <= 4; i++) {
        col += w[i + 4] * texture(iChannel0, fract(uv + float(i) * d));
    }
    col /= 0.98;
    fragColor = col;
}
```### 步骤 7：色散采样```glsl
#define DISP_SAMPLES 64  // adjustable: sample count

vec3 sampleWeights(float i) {
    return vec3(i * i, 46.6666 * pow((1.0 - i) * i, 3.0), (1.0 - i) * (1.0 - i));
}

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
```### 步骤 8：IBL 环境采样```glsl
#define MAX_LOD 7.0     // adjustable: cubemap max mip level
#define DIFFUSE_LOD 6.5 // adjustable: diffuse sampling LOD

vec3 getSpecularLightColor(vec3 N, float roughness) {
    vec3 raw = textureLod(iChannel0, N, roughness * MAX_LOD).rgb;
    return pow(raw, vec3(4.5)) * 6.5; // HDR approximation
}

vec3 getDiffuseLightColor(vec3 N) {
    return textureLod(iChannel0, N, DIFFUSE_LOD).rgb;
}

// BRDF LUT lookup
vec2 brdf = texture(iChannel3, vec2(NdotV, roughness)).rg;
vec3 specular = envColor * (F * brdf.x + brdf.y);
```## 完整的代码模板

iChannel0 绑定到噪声纹理（例如，“灰色噪声介质”），并启用 mipmap。```glsl
// === Texture Sampling Comprehensive Demo ===
// iChannel0: noise texture (requires mipmap enabled)

#define TEX_RES 256.0
#define FBM_OCTAVES 6
#define FBM_PERSISTENCE 0.5
#define CLOUD_LAYERS 4
#define CLOUD_SPEED 0.02
#define DOF_MAX_BLUR 5.0
#define DOF_FOCUS_DIST 0.5
#define BLOOM_STRENGTH 0.3
#define BLOOM_LOD 4.0

float noise(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);

    float a = textureLod(iChannel0, (p + vec2(0.0, 0.0)) / TEX_RES, 0.0).x;
    float b = textureLod(iChannel0, (p + vec2(1.0, 0.0)) / TEX_RES, 0.0).x;
    float c = textureLod(iChannel0, (p + vec2(0.0, 1.0)) / TEX_RES, 0.0).x;
    float d = textureLod(iChannel0, (p + vec2(1.0, 1.0)) / TEX_RES, 0.0).x;

    return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}

float fbm(vec2 x) {
    float v = 0.0;
    float a = 0.5;
    float w = 0.0;
    for (int i = 0; i < FBM_OCTAVES; i++) {
        v += a * noise(x);
        w += a;
        x *= 2.0;
        a *= FBM_PERSISTENCE;
    }
    return v / w;
}

float cloudLayer(vec2 uv, float height, float time) {
    vec2 offset = vec2(time * CLOUD_SPEED * (1.0 + height), 0.0);
    float n = fbm((uv + offset) * (2.0 + height * 3.0));
    return smoothstep(0.4, 0.7, n);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float aspect = iResolution.x / iResolution.y;

    // 1. Procedural sky
    vec3 sky = mix(vec3(0.1, 0.15, 0.4), vec3(0.5, 0.7, 1.0), uv.y);

    // 2. FBM cloud layers
    vec3 col = sky;
    for (int i = 0; i < CLOUD_LAYERS; i++) {
        float h = float(i) / float(CLOUD_LAYERS);
        float density = cloudLayer(vec2(uv.x * aspect, uv.y), h, iTime);
        vec3 cloudCol = mix(vec3(0.8, 0.85, 0.9), vec3(1.0), h);
        col = mix(col, cloudCol, density * (0.3 + 0.7 * h));
    }

    // 3. textureLod depth of field blur
    float dist = abs(uv.y - DOF_FOCUS_DIST);
    float lod = dist * DOF_MAX_BLUR;
    vec3 blurred = textureLod(iChannel0, uv, lod).rgb;
    col = mix(col, blurred * 0.5 + col * 0.5, 0.3);

    // 4. Bloom
    vec3 bloom = textureLod(iChannel0, uv, BLOOM_LOD).rgb;
    bloom += textureLod(iChannel0, uv, BLOOM_LOD + 1.0).rgb;
    bloom += textureLod(iChannel0, uv, BLOOM_LOD + 2.0).rgb;
    bloom /= 3.0;
    col += bloom * BLOOM_STRENGTH;

    // 5. Post-processing
    col = (col * (6.2 * col + 0.5)) / (col * (6.2 * col + 1.7) + 0.06);
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.2);

    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：各向异性流场模糊```glsl
#define BLUR_ITERATIONS 32  // adjustable: number of samples along flow field
#define BLUR_STEP 0.008     // adjustable: UV offset per step

vec3 flowBlur(vec2 uv) {
    vec3 col = vec3(0.0);
    float acc = 0.0;
    for (int i = 0; i < BLUR_ITERATIONS; i++) {
        float h = float(i) / float(BLUR_ITERATIONS);
        float w = 4.0 * h * (1.0 - h);
        col += w * texture(iChannel0, uv).rgb;
        acc += w;
        vec2 dir = texture(iChannel1, uv).xy * 2.0 - 1.0;
        uv += BLUR_STEP * dir;
    }
    return col / acc;
}
```### 变体 2：缓冲区即数据存储```glsl
const ivec2 txPosition = ivec2(0, 0);
const ivec2 txVelocity = ivec2(1, 0);
const ivec2 txState    = ivec2(2, 0);

vec4 load(ivec2 addr) { return texelFetch(iChannel0, addr, 0); }

void store(ivec2 addr, vec4 val, inout vec4 fragColor, ivec2 fragPos) {
    fragColor = (fragPos == addr) ? val : fragColor;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 p = ivec2(fragCoord);
    fragColor = texelFetch(iChannel0, p, 0);
    vec4 pos = load(txPosition);
    vec4 vel = load(txVelocity);
    // ... update logic ...
    store(txPosition, pos + vel * 0.016, fragColor, p);
    store(txVelocity, vel, fragColor, p);
}
```### 变体 3：色散效应```glsl
#define DISP_SAMPLES 64     // adjustable: sample count
#define DISP_STRENGTH 0.05  // adjustable: dispersion strength

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
```### 变体 4：三平面纹理映射```glsl
#define TRIPLANAR_SHARPNESS 2.0  // adjustable: blend sharpness

vec3 triplanarSample(sampler2D tex, vec3 pos, vec3 normal, float scale) {
    vec3 w = pow(abs(normal), vec3(TRIPLANAR_SHARPNESS));
    w /= (w.x + w.y + w.z);
    vec3 xSample = texture(tex, pos.yz * scale).rgb;
    vec3 ySample = texture(tex, pos.xz * scale).rgb;
    vec3 zSample = texture(tex, pos.xy * scale).rgb;
    return xSample * w.x + ySample * w.y + zSample * w.z;
}
```### 变体 5：时间重投影 (TAA)```glsl
#define TAA_BLEND 0.9  // adjustable: history frame blend ratio

vec3 temporalBlend(vec2 currUv, vec2 prevUv, vec3 currColor) {
    vec3 history = textureLod(iChannel0, prevUv, 0.0).rgb;
    vec3 minCol = currColor - 0.1;
    vec3 maxCol = currColor + 0.1;
    history = clamp(history, minCol, maxCol);
    return mix(currColor, history, TAA_BLEND);
}
```## 表演与作曲

**性能提示**：
- 大量采样（例如，64个色散样本）是带宽瓶颈——减少样本数量+使用智能权重补偿；使用具有高 LOD 的“textureLod”来减少缓存未命中
- 2D 高斯模糊使用可分离的两遍 (O(N^2) -> O(2N))，利用 (N+1)/2 个样本的硬件双线性来实现 N-tap
- 必须在光线行进中使用“textureLod(..., 0.0)”——GPU 无法正确估计屏幕空间导数
- 手动 Hermite 插值比硬件慢大约 4 倍 — 仅用于前两个 FBM 八度音程，对于更高频率则回退到“texture()”
- 每个多缓冲区反馈都会增加一帧延迟 - 将操作合并到同一通道中；使用 `texelFetch` 来避免过滤开销

**构图技巧**：
- **+ SDF Ray Marching**：置换贴图/材质的噪声纹理；在光线行进中使用 `textureLod(..., 0.0)`
- **+ 程序噪声**：Hermite + FBM 驱动域扭曲以生成地形/云/火；纹理噪声比纯数学噪声更快
- **+后处理管道**：多LOD光晕→可分离DOF→色散→色调映射，链接完整的后处理管道
- **+ PBR/IBL**：`textureLod` 按粗糙度对立方体贴图进行采样 + BRDF LUT 查找 = split-sum IBL
- **+模拟/反馈**：多缓冲反应扩散/流体；缓冲A状态，B/C可分离模糊扩散，图像可视化； `fract()` 环面边界

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/texture-sampling.md)