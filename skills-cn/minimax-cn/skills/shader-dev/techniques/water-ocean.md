# 水和海洋渲染技巧

## 用例
- 渲染海洋、湖泊和河流等水体表面
- 水面反射/折射、菲涅尔效应
- 水下焦散照明效果
- 波浪、泡沫和水流动画

## 核心原则

水渲染解决了三个问题：**水面形状生成**、**光与水面交互**、**水体颜色合成**。

### 波浪生成：指数正弦叠加 + 导数域扭曲

`wave(x) = exp(sin(x) - 1)` — 尖锐的波峰 (`exp(0)=1`)，宽阔平坦的波谷 (`exp(-2)≈0.135`)，类似于余摆线轮廓，但计算成本比格斯特纳波低得多。

叠加多个波浪时，使用**导数域扭曲（拖动）**：```
position += direction * derivative * weight * DRAG_MULT
```小波纹聚集在大波浪的波峰上，模拟重力波上的毛细波。

### 照明：Schlick Fresnel + 次表面散射

- **Schlick Fresnel**：`F = F0 + (1-F0) * (1-dot(N,V))^5`，水 F0 ≈ 0.04
- **SSS近似**：波谷处较厚的水层→更强的蓝绿色散射；波峰处的层较薄 → 散射较弱

### 水面交叉点：限高田野行进

水面被限制在“[0, -WATER_DEPTH]”边界框内，具有自适应步长：“step = ray_y - wave_height”。

## 实施步骤

### 步骤 1：指数正弦波函数```glsl
// Single wave: exp(sin(x)-1) produces sharp peaks and broad troughs, returns (value, negative derivative)
vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);
    float dx = wave * cos(x);
    return vec2(wave, -dx);
}
```### 步骤 2：具有域扭曲的多倍频程波叠加```glsl
#define DRAG_MULT 0.38  // Domain warp strength, 0=none, 0.5=strong clustering

float getwaves(vec2 position, int iterations) {
    float wavePhaseShift = length(position) * 0.1;
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 2.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));  // Pseudo-random wave direction
        vec2 res = wavedx(position, p, frequency, iTime * timeMultiplier + wavePhaseShift);
        position += p * res.y * weight * DRAG_MULT; // Derivative domain warp
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = mix(weight, 0.0, 0.2);      // Weight decay
        frequency *= 1.18;                     // Frequency growth rate
        timeMultiplier *= 1.07;                // Dispersion
        iter += 1232.399963;                   // Uniform direction distribution
    }
    return sumOfValues / sumOfWeights;
}
```### 步骤 3：有界边界框射线行进```glsl
#define WATER_DEPTH 1.0

float intersectPlane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

float raymarchwater(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < 64; i++) {
        float height = getwaves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);      // Adaptive step size
    }
    return distance(start, camera);
}
```### 步骤4：正常计算和距离平滑```glsl
#define ITERATIONS_RAYMARCH 12  // For marching (fewer = faster)
#define ITERATIONS_NORMAL 36    // For normals (more = finer detail)

vec3 calcNormal(vec2 pos, float e, float depth) {
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

// Distance smoothing: normals approach (0,1,0) at far distances
// N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));
```### 步骤 5：菲涅耳反射和次表面散射```glsl
float fresnel = 0.04 + 0.96 * pow(1.0 - max(0.0, dot(-N, ray)), 5.0);

vec3 R = normalize(reflect(ray, N));
R.y = abs(R.y);  // Force upward to avoid self-intersection

vec3 reflection = getAtmosphere(R) + getSun(R);

vec3 scattering = vec3(0.0293, 0.0698, 0.1717) * 0.1
                * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);

vec3 C = fresnel * reflection + scattering;
```### 步骤 6：气氛和色调映射```glsl
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
```## 完整的代码模板

可以直接粘贴到ShaderToy中运行。摘自“afl_ext”的“非常快的程序海洋”。```glsl
// Water & Ocean Rendering — ShaderToy Template
// exp(sin) wave model + derivative domain warp + Schlick Fresnel + SSS

// ==================== Tunable Parameters ====================
#define DRAG_MULT 0.38
#define WATER_DEPTH 1.0
#define CAMERA_HEIGHT 1.5
#define ITERATIONS_RAYMARCH 12
#define ITERATIONS_NORMAL 36
#define RAYMARCH_STEPS 64
#define NORMAL_EPSILON 0.01
#define FRESNEL_F0 0.04
#define SSS_COLOR vec3(0.0293, 0.0698, 0.1717)
#define SSS_INTENSITY 0.1
#define SUN_POWER 720.0
#define SUN_BRIGHTNESS 210.0
#define EXPOSURE 2.0

// ==================== Wave Functions ====================
vec2 wavedx(vec2 position, vec2 direction, float frequency, float timeshift) {
    float x = dot(direction, position) * frequency + timeshift;
    float wave = exp(sin(x) - 1.0);
    float dx = wave * cos(x);
    return vec2(wave, -dx);
}

float getwaves(vec2 position, int iterations) {
    float wavePhaseShift = length(position) * 0.1;
    float iter = 0.0;
    float frequency = 1.0;
    float timeMultiplier = 2.0;
    float weight = 1.0;
    float sumOfValues = 0.0;
    float sumOfWeights = 0.0;
    for (int i = 0; i < iterations; i++) {
        vec2 p = vec2(sin(iter), cos(iter));
        vec2 res = wavedx(position, p, frequency, iTime * timeMultiplier + wavePhaseShift);
        position += p * res.y * weight * DRAG_MULT;
        sumOfValues += res.x * weight;
        sumOfWeights += weight;
        weight = mix(weight, 0.0, 0.2);
        frequency *= 1.18;
        timeMultiplier *= 1.07;
        iter += 1232.399963;
    }
    return sumOfValues / sumOfWeights;
}

// ==================== Ray Marching ====================
float intersectPlane(vec3 origin, vec3 direction, vec3 point, vec3 normal) {
    return clamp(dot(point - origin, normal) / dot(direction, normal), -1.0, 9991999.0);
}

float raymarchwater(vec3 camera, vec3 start, vec3 end, float depth) {
    vec3 pos = start;
    vec3 dir = normalize(end - start);
    for (int i = 0; i < RAYMARCH_STEPS; i++) {
        float height = getwaves(pos.xz, ITERATIONS_RAYMARCH) * depth - depth;
        if (height + 0.01 > pos.y) {
            return distance(pos, camera);
        }
        pos += dir * (pos.y - height);
    }
    return distance(start, camera);
}

// ==================== Normals ====================
vec3 calcNormal(vec2 pos, float e, float depth) {
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

// ==================== Camera ====================
#define NormalizedMouse (iMouse.xy / iResolution.xy)

mat3 createRotationMatrixAxisAngle(vec3 axis, float angle) {
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    return mat3(
        oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s, oc * axis.z * axis.x + axis.y * s,
        oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,          oc * axis.y * axis.z - axis.x * s,
        oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s, oc * axis.z * axis.z + c
    );
}

vec3 getRay(vec2 fragCoord) {
    vec2 uv = ((fragCoord.xy / iResolution.xy) * 2.0 - 1.0) * vec2(iResolution.x / iResolution.y, 1.0);
    vec3 proj = normalize(vec3(uv.x, uv.y, 1.5));
    if (iResolution.x < 600.0) return proj;
    return createRotationMatrixAxisAngle(vec3(0.0, -1.0, 0.0), 3.0 * ((NormalizedMouse.x + 0.5) * 2.0 - 1.0))
         * createRotationMatrixAxisAngle(vec3(1.0, 0.0, 0.0), 0.5 + 1.5 * (((NormalizedMouse.y == 0.0 ? 0.27 : NormalizedMouse.y)) * 2.0 - 1.0))
         * proj;
}

// ==================== Atmosphere ====================
vec3 getSunDirection() {
    return normalize(vec3(-0.0773502691896258, 0.5 + sin(iTime * 0.2 + 2.6) * 0.45, 0.5773502691896258));
}

vec3 extra_cheap_atmosphere(vec3 raydir, vec3 sundir) {
    float special_trick = 1.0 / (raydir.y * 1.0 + 0.1);
    float special_trick2 = 1.0 / (sundir.y * 11.0 + 1.0);
    float raysundt = pow(abs(dot(sundir, raydir)), 2.0);
    float sundt = pow(max(0.0, dot(sundir, raydir)), 8.0);
    float mymie = sundt * special_trick * 0.2;
    vec3 suncolor = mix(vec3(1.0), max(vec3(0.0), vec3(1.0) - vec3(5.5, 13.0, 22.4) / 22.4), special_trick2);
    vec3 bluesky = vec3(5.5, 13.0, 22.4) / 22.4 * suncolor;
    vec3 bluesky2 = max(vec3(0.0), bluesky - vec3(5.5, 13.0, 22.4) * 0.002 * (special_trick + -6.0 * sundir.y * sundir.y));
    bluesky2 *= special_trick * (0.24 + raysundt * 0.24);
    return bluesky2 * (1.0 + 1.0 * pow(1.0 - raydir.y, 3.0));
}

vec3 getAtmosphere(vec3 dir) {
    return extra_cheap_atmosphere(dir, getSunDirection()) * 0.5;
}

float getSun(vec3 dir) {
    return pow(max(0.0, dot(dir, getSunDirection())), SUN_POWER) * SUN_BRIGHTNESS;
}

// ==================== Tone Mapping ====================
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

// ==================== Main Function ====================
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 ray = getRay(fragCoord);
    if (ray.y >= 0.0) {
        vec3 C = getAtmosphere(ray) + getSun(ray);
        fragColor = vec4(aces_tonemap(C * EXPOSURE), 1.0);
        return;
    }

    vec3 waterPlaneHigh = vec3(0.0, 0.0, 0.0);
    vec3 waterPlaneLow = vec3(0.0, -WATER_DEPTH, 0.0);
    vec3 origin = vec3(iTime * 0.2, CAMERA_HEIGHT, 1.0);

    float highPlaneHit = intersectPlane(origin, ray, waterPlaneHigh, vec3(0.0, 1.0, 0.0));
    float lowPlaneHit = intersectPlane(origin, ray, waterPlaneLow, vec3(0.0, 1.0, 0.0));
    vec3 highHitPos = origin + ray * highPlaneHit;
    vec3 lowHitPos = origin + ray * lowPlaneHit;

    float dist = raymarchwater(origin, highHitPos, lowHitPos, WATER_DEPTH);
    vec3 waterHitPos = origin + ray * dist;

    vec3 N = calcNormal(waterHitPos.xz, NORMAL_EPSILON, WATER_DEPTH);
    N = mix(N, vec3(0.0, 1.0, 0.0), 0.8 * min(1.0, sqrt(dist * 0.01) * 1.1));

    float fresnel = FRESNEL_F0 + (1.0 - FRESNEL_F0) * pow(1.0 - max(0.0, dot(-N, ray)), 5.0);

    vec3 R = normalize(reflect(ray, N));
    R.y = abs(R.y);
    vec3 reflection = getAtmosphere(R) + getSun(R);

    vec3 scattering = SSS_COLOR * SSS_INTENSITY
                    * (0.2 + (waterHitPos.y + WATER_DEPTH) / WATER_DEPTH);

    vec3 C = fresnel * reflection + scattering;
    fragColor = vec4(aces_tonemap(C * EXPOSURE), 1.0);
}
```## 常见变体

### 变体 1：2D 水下苛性纹理```glsl
#define TAU 6.28318530718
#define MAX_ITER 5

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 0.5 + 23.0;
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec2 p = mod(uv * TAU, TAU) - 250.0;
    vec2 i = vec2(p);
    float c = 1.0;
    float inten = 0.005;

    for (int n = 0; n < MAX_ITER; n++) {
        float t = time * (1.0 - (3.5 / float(n + 1)));
        i = p + vec2(cos(t - i.x) + sin(t + i.y), sin(t - i.y) + cos(t + i.x));
        c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten), p.y / (cos(i.y + t) / inten)));
    }
    c /= float(MAX_ITER);
    c = 1.17 - pow(c, 1.4);
    vec3 colour = vec3(pow(abs(c), 8.0));
    colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0);
    fragColor = vec4(colour, 1.0);
}
```### 变体 2：FBM 凹凸贴图湖面```glsl
float waterMap(vec2 pos) {
    mat2 m2 = mat2(0.60, -0.80, 0.80, 0.60);
    vec2 posm = pos * m2;
    return abs(fbm(vec3(8.0 * posm, iTime)) - 0.5) * 0.1;
}

// Analytic plane intersection instead of ray marching
float t = -ro.y / rd.y;
vec3 hitPos = ro + rd * t;

// Finite difference normals (central differencing)
float eps = 0.1;
vec3 normal = vec3(0.0, 1.0, 0.0);
normal.x = -bumpfactor * (waterMap(hitPos.xz + vec2(eps, 0.0)) - waterMap(hitPos.xz - vec2(eps, 0.0))) / (2.0 * eps);
normal.z = -bumpfactor * (waterMap(hitPos.xz + vec2(0.0, eps)) - waterMap(hitPos.xz - vec2(0.0, eps))) / (2.0 * eps);
normal = normalize(normal);

float bumpfactor = 0.1 * (1.0 - smoothstep(0.0, 60.0, distance(ro, hitPos)));
vec3 refracted = refract(rd, normal, 1.0 / 1.333);
```### 变体 3：山脊噪声海岸波浪```glsl
float sea(vec2 p) {
    float f = 1.0;
    float r = 0.0;
    float time = -iTime;
    for (int i = 0; i < 8; i++) {
        r += (1.0 - abs(noise(p * f + 0.9 * time))) / f;
        f *= 2.0;
        p -= vec2(-0.01, 0.04) * (r - 0.2 * time / (0.1 - f));
    }
    return r / 4.0 + 0.5;
}

// Shoreline foam
float dh = seaDist - rockDist;
float foam = 0.0;
if (dh < 0.0 && dh > -0.02) {
    foam = 0.5 * exp(20.0 * dh);
}
```### 变体 4：流量图水动画```glsl
vec3 FBM_DXY(vec2 p, vec2 flow, float persistence, float domainWarp) {
    vec3 f = vec3(0.0);
    float tot = 0.0;
    float a = 1.0;
    for (int i = 0; i < 4; i++) {
        p += flow;
        flow *= -0.75;
        vec3 v = SmoothNoise_DXY(p);
        f += v * a;
        p += v.xy * domainWarp;
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
```### 变体 5：比尔定律吸水率```glsl
vec3 GetWaterExtinction(float dist) {
    float fOpticalDepth = dist * 6.0;
    vec3 vExtinctCol = vec3(0.5, 0.6, 0.9);
    return exp2(-fOpticalDepth * vExtinctCol);
}

vec3 vInscatter = vSurfaceDiffuse * (1.0 - exp(-refractDist * 0.1))
               * (1.0 + dot(sunDir, viewDir));

vec3 underwaterColor = terrainColor * GetWaterExtinction(waterDepth) + vInscatter;
vec3 finalColor = mix(underwaterColor, reflectionColor, fresnel);
```## 表演与作曲

### 性能提示
- **双迭代计数策略**：行进 12 次迭代，法线 36 次迭代 — 将渲染时间减半，几乎没有视觉损失
- **距离自适应法线平滑**：`N = mix(N, up, 0.8 * min(1.0, sqrt(dist*0.01)*1.1))`，消除远处闪烁
- **边界框裁剪**：预先计算上/下平面交叉点，提前确定天空方向
- **自适应步长**：`pos += dir * (pos.y - height)`，比固定步长快 3-5 倍
- **滤波器宽度感知衰减**：`dFdx/dFdy` 驱动正常 LOD
- **LOD条件细节**：仅计算近距离高频位移

### 构图技巧
- **体积云**：射线沿反射方向“R”行进云，混合到反射项中
- **地形海岸线**：`dh = waterSDF -terrainSDF`，当`dh ≈ 0`时渲染泡沫
- **焦散叠加**：将变体 1 投影到水下地形上，“焦散 * exp(-深度 * 吸收)”深度衰减
- **雾/大气**：独立消光 + 内散射、每通道 RGB 衰减：```glsl
  vec3 fogExtinction = exp2(fogExtCoeffs * -distance);
  vec3 fogInscatter = fogColor * (1.0 - exp2(fogInCoeffs * -distance));
  finalColor = finalColor * fogExtinction + fogInscatter;
  ```- **后处理**：Bloom（斐波那契螺旋模糊）、ACES 色调映射、景深 (DOF)

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/water-ocean.md)