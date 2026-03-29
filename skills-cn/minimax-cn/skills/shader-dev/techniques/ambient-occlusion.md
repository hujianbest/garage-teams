## WebGL2 适配要求

**重要：GLSL 类型严格性**：float 和 vec 类型不能隐式转换。 `vec3 v = 1.0;` 是非法的；您必须使用向量形式（例如，`vec3(1.0)`、`vec3(1.0) * x`、`value * vec3(1.0)`）。

本文档中的代码模板使用ShaderToy GLSL风格。生成独立 HTML 页面时，必须适应 WebGL2：

- 使用`canvas.getContext("webgl2")`
- 着色器第一行：`#version 300 es`，在片段着色器中添加` precision highp float;`
- 顶点着色器：`attribute` -> `in`、`variing` -> `out`
- 片段着色器：`variing` -> `in`、`gl_FragColor` -> 自定义`out vec4 fragColor`、`texture2D()` -> `texture()`
- ShaderToy 的 `void mainImage(out vec4 fragColor, in vec2 fragCoord)` 必须适应标准的 `void main()` 入口点

# SDF 环境光遮挡

## 用例

- 模拟光线行进/SDF 场景中的间接光遮挡
- 添加空间深度和接触阴影（凹陷和缝隙中变暗）
- 从 5 个样本（性能优先）到 32 个半球样本（质量优先）

## 核心原则

沿表面法线方向在多个距离处对 SDF 进行采样，将“预期距离”与“实际距离”进行比较以估计遮挡。

对于表面点 P、法线 N 和采样距离 h：
- 预期距离 = h（当周围环境开放时，SDF 应等于 h）
- 实际距离 = 地图(P + N * h)
- 遮挡贡献 = h - map(P + N * h) （差异越大 = 遮挡越强）```
AO = 1 - k * sum(weight_i * max(0, h_i - map(P + N * h_i)))
```结果：1.0 = 无遮挡，0.0 = 完全遮挡。权重呈指数衰减（越近的样本权重越高）。

## 实施步骤

### 第 1 步：自卫队场景```glsl
float map(vec3 p) {
    float d = p.y; // ground
    d = min(d, length(p - vec3(0.0, 1.0, 0.0)) - 1.0); // sphere
    d = min(d, length(vec2(length(p.xz) - 1.5, p.y - 0.5)) - 0.4); // torus
    return d;
}
```### 第2步：正常计算```glsl
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}
```### 步骤 3：经典法向 AO（5 个样本）```glsl
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0; // sampling distance 0.01~0.13
        float d = map(pos + h * nor);
        occ += (h - d) * sca; // (expected - actual) * weight
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```### 步骤 4：将 AO 应用于照明```glsl
float ao = calcAO(pos, nor);

// affect ambient light only (physically correct)
vec3 ambient = vec3(0.2, 0.3, 0.5) * ao;
vec3 color = diffuse * shadow + ambient;

// affect all lighting (visually stronger)
vec3 color = (diffuse * shadow + ambient) * ao;

// combined with sky visibility
float skyVis = 0.5 + 0.5 * nor.y;
vec3 color = diffuse * shadow + ambient * ao * skyVis;
```### 步骤 5：Raymarching 集成```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // ... camera setup, ray generation ...
    float t = 0.0;
    for (int i = 0; i < 128; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < 0.001) break;
        t += d;
        if (t > 100.0) break;
    }

    vec3 col = vec3(0.0);
    if (t < 100.0) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);
        float ao = calcAO(pos, nor);

        vec3 lig = normalize(vec3(1.0, 0.8, -0.6));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float sky = 0.5 + 0.5 * nor.y;
        col = vec3(1.0) * dif + vec3(0.2, 0.3, 0.5) * sky * ao;
    }
    fragColor = vec4(col, 1.0);
}
```## 完整的代码模板

直接在ShaderToy中运行：```glsl
// SDF Ambient Occlusion — ShaderToy Template
// Synthesized from classic raymarching implementations

#define AO_STEPS 5
#define AO_MAX_DIST 0.12
#define AO_MIN_DIST 0.01
#define AO_DECAY 0.95
#define AO_STRENGTH 3.0
#define MARCH_STEPS 128
#define MAX_DIST 100.0
#define SURF_DIST 0.001

float map(vec3 p) {
    float ground = p.y;
    float sphere = length(p - vec3(0.0, 1.0, 0.0)) - 1.0;
    float torus = length(vec2(length(p.xz) - 1.5, p.y - 0.5)) - 0.4;
    float box = length(max(abs(p - vec3(-2.5, 0.75, 0.0)) - vec3(0.75), 0.0)) - 0.05;
    float d = min(ground, sphere);
    d = min(d, torus);
    d = min(d, box);
    return d;
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < AO_STEPS; i++) {
        float h = AO_MIN_DIST + AO_MAX_DIST * float(i) / float(AO_STEPS - 1);
        float d = map(pos + h * nor);
        occ += (h - d) * sca;
        sca *= AO_DECAY;
    }
    return clamp(1.0 - AO_STRENGTH * occ, 0.0, 1.0);
}

float calcShadow(vec3 ro, vec3 rd, float mint, float maxt, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 64; i++) {
        float h = map(ro + rd * t);
        res = min(res, k * h / t);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.001 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    float an = 0.3 * iTime;
    vec3 ro = vec3(4.0 * cos(an), 2.5, 4.0 * sin(an));
    vec3 ta = vec3(0.0, 0.5, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.8 * ww);

    float t = 0.0;
    for (int i = 0; i < MARCH_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }

    vec3 col = vec3(0.4, 0.5, 0.7) - 0.3 * rd.y;

    if (t < MAX_DIST) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);
        float ao = calcAO(pos, nor);

        vec3 lig = normalize(vec3(0.8, 0.6, -0.5));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float sha = calcShadow(pos + nor * 0.01, lig, 0.02, 20.0, 8.0);
        float sky = 0.5 + 0.5 * nor.y;

        vec3 mate = vec3(0.18);
        if (pos.y < 0.01) {
            float f = mod(floor(pos.x) + floor(pos.z), 2.0);
            mate = 0.1 + 0.08 * f * vec3(1.0);
        }

        col = vec3(0.0);
        col += mate * vec3(1.0, 0.9, 0.7) * dif * sha;
        col += mate * vec3(0.2, 0.3, 0.5) * sky * ao;
        col += mate * vec3(0.3, 0.2, 0.1) * clamp(-nor.y, 0.0, 1.0) * ao;
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 乘法 AO (Spout / P_Malin)```glsl
float calcAO_multiplicative(vec3 pos, vec3 nor) {
    float ao = 1.0;
    float dist = 0.0;
    for (int i = 0; i <= 5; i++) {
        dist += 0.1;
        float d = map(pos + nor * dist);
        ao *= 1.0 - max(0.0, (dist - d) * 0.2 / dist);
    }
    return ao;
}
```### 多尺度分离 AO (Protophore / Eric Heitz)

采样距离呈指数级增加，将短距离接触阴影与长距离环境遮挡分开，完全展开而无循环。```glsl
float calcAO_multiscale(vec3 pos, vec3 nor) {
    float aoS = 1.0;
    aoS *= clamp(map(pos + nor * 0.1) * 10.0, 0.0, 1.0);
    aoS *= clamp(map(pos + nor * 0.2) * 5.0,  0.0, 1.0);
    aoS *= clamp(map(pos + nor * 0.4) * 2.5,  0.0, 1.0);
    aoS *= clamp(map(pos + nor * 0.8) * 1.25, 0.0, 1.0);

    float ao = aoS;
    ao *= clamp(map(pos + nor * 1.6) * 0.625,  0.0, 1.0);
    ao *= clamp(map(pos + nor * 3.2) * 0.3125, 0.0, 1.0);
    ao *= clamp(map(pos + nor * 6.4) * 0.15625,0.0, 1.0);

    return max(0.035, pow(ao, 0.3));
}
```### 抖动采样 AO

哈希抖动会破坏条带伪影，“1/(1+l)”距离衰减。```glsl
float hash(float n) { return fract(sin(n) * 43758.5453); }

float calcAO_jittered(vec3 pos, vec3 nor, float maxDist) {
    float ao = 0.0;
    const float nbIte = 6.0;
    for (float i = 1.0; i < nbIte + 0.5; i++) {
        float l = (i + hash(i)) * 0.5 / nbIte * maxDist;
        ao += (l - map(pos + nor * l)) / (1.0 + l);
    }
    return clamp(1.0 - ao / nbIte, 0.0, 1.0);
}
// call: calcAO_jittered(pos, nor, 4.0)
```### 半球随机方向 AO

正常半球内的随机方向采样（更接近物理精确）需要 32 个样本。```glsl
vec2 hash2(float n) {
    return fract(sin(vec2(n, n + 1.0)) * vec2(43758.5453, 22578.1459));
}

float calcAO_hemisphere(vec3 pos, vec3 nor, float seed) {
    float occ = 0.0;
    for (int i = 0; i < 32; i++) {
        float h = 0.01 + 4.0 * pow(float(i) / 31.0, 2.0);
        vec2 an = hash2(seed + float(i) * 13.1) * vec2(3.14159, 6.2831);
        vec3 dir = vec3(sin(an.x) * sin(an.y), sin(an.x) * cos(an.y), cos(an.x));
        dir *= sign(dot(dir, nor));
        occ += clamp(5.0 * map(pos + h * dir) / h, -1.0, 1.0);
    }
    return clamp(occ / 32.0, 0.0, 1.0);
}
```### 斐波那契球均匀半球 AO

斐波那契球点用于准均匀半球采样，避免随机聚类。```glsl
vec3 forwardSF(float i, float n) {
    const float PI  = 3.141592653589793;
    const float PHI = 1.618033988749895;
    float phi = 2.0 * PI * fract(i / PHI);
    float zi = 1.0 - (2.0 * i + 1.0) / n;
    float sinTheta = sqrt(1.0 - zi * zi);
    return vec3(cos(phi) * sinTheta, sin(phi) * sinTheta, zi);
}

float hash1(float n) { return fract(sin(n) * 43758.5453); }

float calcAO_fibonacci(vec3 pos, vec3 nor) {
    float ao = 0.0;
    for (int i = 0; i < 32; i++) {
        vec3 ap = forwardSF(float(i), 32.0);
        float h = hash1(float(i));
        ap *= sign(dot(ap, nor)) * h * 0.1;
        ao += clamp(map(pos + nor * 0.01 + ap) * 3.0, 0.0, 1.0);
    }
    ao /= 32.0;
    return clamp(ao * 6.0, 0.0, 1.0);
}
```## 表演与作曲

### 性能提示

- **瓶颈**：`map()` 调用的数量。每个 AO 样本 = 一次完整的 SDF 评估
- **样本数选择**：经典法向3~5个样本就足够了；半球采样需要16~32
- **提前退出**：`if (occ > 0.35) break;` 跳过严重遮挡的区域
- **展开循环**：手动展开的固定迭代计数（4~7）对 GPU 更友好
- **距离退化**：`float aoSteps = mix(5.0, 2.0, Clip(t / 50.0, 0.0, 1.0));`
- **预处理器切换**：`#ifdef ENABLE_AMBIENT_OCCLUSION`用于开/关控制
- **SDF 简化**：AO 采样可以使用简化的 `map()`，忽略精细细节

### 构图技巧

- **AO + 软阴影**：`col = 漫反射 * sha + 环境 * ao;`
- **AO + 天空可见度**：`col += skyColor * ao * (0.5 + 0.5 *nor.y);`
- **AO + 反射光/SSS**：`col +=ounceColor * bou * ao;`
- **AO + 凸性检测**：沿 +N/-N 采样以获得 AO 和凸性
- **AO + 菲涅尔反射**：`col += envColor * fre * ao;` 减少遮挡区域的环境反射

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/ambient-occlusion.md)