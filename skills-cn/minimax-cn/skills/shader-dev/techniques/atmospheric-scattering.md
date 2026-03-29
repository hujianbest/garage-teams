# 大气和地下散射

## 用例
- 天空渲染（日出/日落/中午/夜晚）
- 空中视角
- 太阳晕（米氏散射雾霾）
- 行星大气层边缘发光
- 半透明材质SSS（蜡烛、皮肤、果冻）
- 体积光（上帝光线）

## 核心原则

三种物理机制：

**瑞利散射** — 分子尺度粒子，β_R(λ) ∝ 1/λ⁴，波长越短散射越强烈（蓝天/红色日落）。
海平面值：`vec3(5.5e-6, 13.0e-6, 22.4e-6)` m⁻¹。
相位函数：`P_R(θ) = 3/(16π) × (1 + cos²θ)`，前后对称。

**米氏散射** — 气溶胶颗粒，与波长无关，强前向散射（日晕）。
海平面值：`vec3(21e-6)` m⁻¹。
相函数：Henyey-Greenstein，`g ≈ 0.76~0.88`。

**比尔-朗伯衰减** — `T(A→B) = exp(-∫ σ_e(s) ds)`，光通过介质的指数衰减。

**算法流程**：光线沿着视图光线行进；在每个采样点：计算密度 → 计算朝向太阳的光学深度 → Beer-Lambert 衰减 → 相位函数加权 → 累加。

## 实施步骤

### 步骤 1：光线球体相交```glsl
// Returns (t_near, t_far); no intersection when t_near > t_far
vec2 raySphereIntersect(vec3 p, vec3 dir, float r) {
    float b = dot(p, dir);
    float c = dot(p, p) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5);
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```### 步骤 2：大气物理常数```glsl
#define PLANET_RADIUS 6371e3
#define ATMOS_RADIUS  6471e3
#define PLANET_CENTER vec3(0.0)

#define BETA_RAY vec3(5.5e-6, 13.0e-6, 22.4e-6)  // Rayleigh scattering coefficients
#define BETA_MIE vec3(21e-6)                        // Mie scattering coefficients
#define BETA_OZONE vec3(2.04e-5, 4.97e-5, 1.95e-6) // Ozone absorption

#define MIE_G 0.76          // Anisotropy parameter 0.76~0.88
#define MIE_EXTINCTION 1.1  // Extinction/scattering ratio

#define H_RAY 8000.0        // Rayleigh scale height
#define H_MIE 1200.0        // Mie scale height
#define H_OZONE 30e3        // Ozone peak altitude
#define OZONE_FALLOFF 4e3   // Ozone decay width

#define PRIMARY_STEPS 32    // Primary ray steps 8(mobile)~64(high quality)
#define LIGHT_STEPS 8       // Light direction steps 4~16
```### 步骤 3：相位函数```glsl
float phaseRayleigh(float cosTheta) {
    return 3.0 / (16.0 * 3.14159265) * (1.0 + cosTheta * cosTheta);
}

// Henyey-Greenstein phase function
float phaseMie(float cosTheta, float g) {
    float gg = g * g;
    float num = (1.0 - gg) * (1.0 + cosTheta * cosTheta);
    float denom = (2.0 + gg) * pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
    return 3.0 / (8.0 * 3.14159265) * num / denom;
}
```### 步骤 4：大气密度采样```glsl
// Returns vec3(rayleigh, mie, ozone) density
vec3 atmosphereDensity(vec3 pos, float planetRadius) {
    float height = length(pos) - planetRadius;
    float densityRay = exp(-height / H_RAY);
    float densityMie = exp(-height / H_MIE);
    float denom = (H_OZONE - height) / OZONE_FALLOFF;
    float densityOzone = (1.0 / (denom * denom + 1.0)) * densityRay;
    return vec3(densityRay, densityMie, densityOzone);
}
```### 步骤 5：光方向光学深度```glsl
vec3 lightOpticalDepth(vec3 pos, vec3 sunDir) {
    float atmoDist = raySphereIntersect(pos - PLANET_CENTER, sunDir, ATMOS_RADIUS).y;
    float stepSize = atmoDist / float(LIGHT_STEPS);
    float rayPos = stepSize * 0.5;
    vec3 optDepth = vec3(0.0);
    for (int i = 0; i < LIGHT_STEPS; i++) {
        vec3 samplePos = pos + sunDir * rayPos;
        float height = length(samplePos - PLANET_CENTER) - PLANET_RADIUS;
        if (height < 0.0) return vec3(1e10); // Occluded by planet
        optDepth += atmosphereDensity(samplePos, PLANET_RADIUS) * stepSize;
        rayPos += stepSize;
    }
    return optDepth;
}
```### 步骤 6：初级散射积分```glsl
vec3 calculateScattering(
    vec3 rayOrigin, vec3 rayDir, float maxDist,
    vec3 sunDir, vec3 sunIntensity
) {
    vec2 atmoHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, ATMOS_RADIUS);
    if (atmoHit.x > atmoHit.y) return vec3(0.0);

    vec2 planetHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, PLANET_RADIUS);

    float tStart = max(atmoHit.x, 0.0);
    float tEnd = atmoHit.y;
    if (planetHit.x > 0.0) tEnd = min(tEnd, planetHit.x);
    tEnd = min(tEnd, maxDist);

    float stepSize = (tEnd - tStart) / float(PRIMARY_STEPS);
    float cosTheta = dot(rayDir, sunDir);
    float phaseR = phaseRayleigh(cosTheta);
    float phaseM = phaseMie(cosTheta, MIE_G);

    vec3 totalRay = vec3(0.0), totalMie = vec3(0.0), optDepthI = vec3(0.0);
    float rayPos = tStart + stepSize * 0.5;

    for (int i = 0; i < PRIMARY_STEPS; i++) {
        vec3 samplePos = rayOrigin + rayDir * rayPos;
        vec3 density = atmosphereDensity(samplePos, PLANET_RADIUS) * stepSize;
        optDepthI += density;

        vec3 optDepthL = lightOpticalDepth(samplePos, sunDir);
        vec3 tau = BETA_RAY * (optDepthI.x + optDepthL.x)
                 + BETA_MIE * 1.1 * (optDepthI.y + optDepthL.y)
                 + BETA_OZONE * (optDepthI.z + optDepthL.z);
        vec3 attenuation = exp(-tau);

        totalRay += density.x * attenuation;
        totalMie += density.y * attenuation;
        rayPos += stepSize;
    }

    return sunIntensity * (totalRay * BETA_RAY * phaseR + totalMie * BETA_MIE * phaseM);
}
```### 步骤 7：色调映射```glsl
vec3 tonemapExposure(vec3 color) { return 1.0 - exp(-color); }

vec3 tonemapReinhard(vec3 color) {
    float l = dot(color, vec3(0.2126, 0.7152, 0.0722));
    vec3 tc = color / (color + 1.0);
    return mix(color / (l + 1.0), tc, tc);
}

vec3 gammaCorrect(vec3 color) { return pow(color, vec3(1.0 / 2.2)); }
```## 完整的代码模板

ShaderToy 完全可运行的 Rayleigh + Mie 大气散射：```glsl
#define PI 3.14159265359

#define PLANET_RADIUS 6371e3
#define ATMOS_RADIUS  6471e3
#define PLANET_CENTER vec3(0.0)

#define BETA_RAY vec3(5.5e-6, 13.0e-6, 22.4e-6)
#define BETA_MIE vec3(21e-6)
#define BETA_OZONE vec3(2.04e-5, 4.97e-5, 1.95e-6)

#define MIE_G 0.76
#define MIE_EXTINCTION 1.1

#define H_RAY 8e3
#define H_MIE 1.2e3
#define H_OZONE 30e3
#define OZONE_FALLOFF 4e3

#define PRIMARY_STEPS 32
#define LIGHT_STEPS 8

#define SUN_INTENSITY vec3(40.0)

vec2 raySphereIntersect(vec3 p, vec3 dir, float r) {
    float b = dot(p, dir);
    float c = dot(p, p) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5);
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}

float phaseRayleigh(float cosTheta) {
    return 3.0 / (16.0 * PI) * (1.0 + cosTheta * cosTheta);
}

float phaseMie(float cosTheta, float g) {
    float gg = g * g;
    float num = (1.0 - gg) * (1.0 + cosTheta * cosTheta);
    float denom = (2.0 + gg) * pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
    return 3.0 / (8.0 * PI) * num / denom;
}

vec3 atmosphereDensity(vec3 pos) {
    float height = length(pos - PLANET_CENTER) - PLANET_RADIUS;
    float dRay = exp(-height / H_RAY);
    float dMie = exp(-height / H_MIE);
    float dOzone = (1.0 / (pow((H_OZONE - height) / OZONE_FALLOFF, 2.0) + 1.0)) * dRay;
    return vec3(dRay, dMie, dOzone);
}

vec3 calculateScattering(
    vec3 start, vec3 dir, float maxDist,
    vec3 sceneColor, vec3 sunDir, vec3 sunIntensity
) {
    start -= PLANET_CENTER;

    float a = dot(dir, dir);
    float b = 2.0 * dot(dir, start);
    float c = dot(start, start) - ATMOS_RADIUS * ATMOS_RADIUS;
    float d = b * b - 4.0 * a * c;
    if (d < 0.0) return sceneColor;

    vec2 rayLen = vec2(
        max((-b - sqrt(d)) / (2.0 * a), 0.0),
        min((-b + sqrt(d)) / (2.0 * a), maxDist)
    );
    if (rayLen.x > rayLen.y) return sceneColor;

    bool allowMie = maxDist > rayLen.y;
    rayLen.y = min(rayLen.y, maxDist);
    rayLen.x = max(rayLen.x, 0.0);

    float stepSize = (rayLen.y - rayLen.x) / float(PRIMARY_STEPS);
    float rayPos = rayLen.x + stepSize * 0.5;

    vec3 totalRay = vec3(0.0);
    vec3 totalMie = vec3(0.0);
    vec3 optI = vec3(0.0);

    float mu = dot(dir, sunDir);
    float phaseR = phaseRayleigh(mu);
    float phaseM = allowMie ? phaseMie(mu, MIE_G) : 0.0;

    for (int i = 0; i < PRIMARY_STEPS; i++) {
        vec3 pos = start + dir * rayPos;
        float height = length(pos) - PLANET_RADIUS;

        vec3 density = vec3(exp(-height / H_RAY), exp(-height / H_MIE), 0.0);
        float dOzone = (H_OZONE - height) / OZONE_FALLOFF;
        density.z = (1.0 / (dOzone * dOzone + 1.0)) * density.x;
        density *= stepSize;
        optI += density;

        float la = dot(sunDir, sunDir);
        float lb = 2.0 * dot(sunDir, pos);
        float lc = dot(pos, pos) - ATMOS_RADIUS * ATMOS_RADIUS;
        float ld = lb * lb - 4.0 * la * lc;
        float lightStepSize = (-lb + sqrt(ld)) / (2.0 * la * float(LIGHT_STEPS));
        float lightPos = lightStepSize * 0.5;
        vec3 optL = vec3(0.0);

        for (int j = 0; j < LIGHT_STEPS; j++) {
            vec3 posL = pos + sunDir * lightPos;
            float heightL = length(posL) - PLANET_RADIUS;
            vec3 densityL = vec3(exp(-heightL / H_RAY), exp(-heightL / H_MIE), 0.0);
            float dOzoneL = (H_OZONE - heightL) / OZONE_FALLOFF;
            densityL.z = (1.0 / (dOzoneL * dOzoneL + 1.0)) * densityL.x;
            densityL *= lightStepSize;
            optL += densityL;
            lightPos += lightStepSize;
        }

        vec3 attn = exp(
            -BETA_RAY * (optI.x + optL.x)
            - BETA_MIE * MIE_EXTINCTION * (optI.y + optL.y)
            - BETA_OZONE * (optI.z + optL.z)
        );

        totalRay += density.x * attn;
        totalMie += density.y * attn;

        rayPos += stepSize;
    }

    vec3 opacity = exp(-(BETA_MIE * optI.y + BETA_RAY * optI.x + BETA_OZONE * optI.z));

    return (
        phaseR * BETA_RAY * totalRay +
        phaseM * BETA_MIE * totalMie
    ) * sunIntensity + sceneColor * opacity;
}

vec3 getCameraVector(vec3 resolution, vec2 coord) {
    vec2 uv = coord.xy / resolution.xy - vec2(0.5);
    uv.x *= resolution.x / resolution.y;
    return normalize(vec3(uv.x, uv.y, -1.0));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 rayDir = getCameraVector(iResolution, fragCoord);
    vec3 cameraPos = vec3(0.0, PLANET_RADIUS + 100.0, 0.0);
    vec3 sunDir = normalize(vec3(0.0, cos(-iTime / 8.0), sin(-iTime / 8.0)));

    vec4 scene = vec4(0.0, 0.0, 0.0, 1e12);
    vec3 sunDisk = vec3(dot(rayDir, sunDir) > 0.9998 ? 3.0 : 0.0);
    scene.xyz = sunDisk;

    vec2 groundHit = raySphereIntersect(cameraPos - PLANET_CENTER, rayDir, PLANET_RADIUS);
    if (groundHit.x > 0.0) {
        scene.w = groundHit.x;
        vec3 hitPos = cameraPos + rayDir * groundHit.x - PLANET_CENTER;
        vec3 normal = normalize(hitPos);
        float shadow = max(0.0, dot(normal, sunDir));
        scene.xyz = vec3(0.1, 0.15, 0.08) * shadow;
    }

    vec3 col = calculateScattering(
        cameraPos, rayDir, scene.w,
        scene.xyz, sunDir, SUN_INTENSITY
    );

    col = 1.0 - exp(-col);
    col = pow(col, vec3(1.0 / 2.2));

    fragColor = vec4(col, 1.0);
}
```## 高级雾模型

三种渐进式雾化技术，从简单到物理驱动。这些可以单独使用，也可以与上面的完整大气散射结合使用。

### 第 1 级：基本指数雾```glsl
vec3 applyFog(vec3 col, float t) {
    float fogAmount = 1.0 - exp(-t * density);
    vec3 fogColor = vec3(0.5, 0.6, 0.7);
    return mix(col, fogColor, fogAmount);
}
```### 2 级：阳光感知雾（散射色调）
当看向太阳时，雾的颜色会变成暖色 - 产生非常自然的光色散效果：```glsl
vec3 applyFogSun(vec3 col, float t, vec3 rd, vec3 sunDir) {
    float fogAmount = 1.0 - exp(-t * density);
    float sunAmount = max(dot(rd, sunDir), 0.0);
    vec3 fogColor = mix(
        vec3(0.5, 0.6, 0.7),          // base fog (blue-grey)
        vec3(1.0, 0.9, 0.7),          // sun-facing fog (warm gold)
        pow(sunAmount, 8.0)
    );
    return mix(col, fogColor, fogAmount);
}
```### 第 3 级：基于高度的雾（分析集成）
密度随海拔高度呈指数下降：“d(y) = a * exp(-b * y)”。该公式是沿射线的精确解析积分，而不是近似值 - 山谷中的雾池和高空处的雾气：```glsl
vec3 applyFogHeight(vec3 col, float t, vec3 ro, vec3 rd) {
    float a = 0.5;    // density multiplier
    float b = 0.3;    // density falloff with height
    float fogAmount = (a / b) * exp(-ro.y * b) * (1.0 - exp(-t * rd.y * b)) / rd.y;
    fogAmount = clamp(fogAmount, 0.0, 1.0);
    vec3 fogColor = vec3(0.5, 0.6, 0.7);
    return mix(col, fogColor, fogAmount);
}
```### 第四级：灭绝+散落分离
用于吸收和散射的独立 RGB 系数 — 允许不同波长散射不同的彩色雾效果：```glsl
vec3 applyFogPhysical(vec3 col, float t, vec3 fogCol) {
    vec3 be = vec3(0.02, 0.025, 0.03);   // extinction coefficients (RGB)
    vec3 bi = vec3(0.015, 0.02, 0.025);  // inscattering coefficients (RGB)
    vec3 extinction = exp(-t * be);
    vec3 inscatter = (1.0 - exp(-t * bi));
    return col * extinction + fogCol * inscatter;
}
```## 常见变体

### 变体 1：非物理分析近似（无光线行进）

极低成本解析天空，适合移动/背景。```glsl
#define zenithDensity(x) 0.7 / pow(max(x - 0.1, 0.0035), 0.75)

vec3 getSkyAbsorption(vec3 skyColor, float zenith) {
    return exp2(skyColor * -zenith) * 2.0;
}

float getMie(vec2 p, vec2 lp) {
    float disk = clamp(1.0 - pow(distance(p, lp), 0.1), 0.0, 1.0);
    return disk * disk * (3.0 - 2.0 * disk) * 2.0 * 3.14159;
}

vec3 getAtmosphericScattering(vec2 screenPos, vec2 lightPos) {
    vec3 skyColor = vec3(0.39, 0.57, 1.0);
    float zenith = zenithDensity(screenPos.y);
    float rayleighMult = 1.0 + pow(1.0 - clamp(distance(screenPos, lightPos), 0.0, 1.0), 2.0) * 1.57;
    vec3 absorption = getSkyAbsorption(skyColor, zenith);
    vec3 sunAbsorption = getSkyAbsorption(skyColor, zenithDensity(lightPos.y + 0.1));
    vec3 sky = skyColor * zenith * rayleighMult;
    vec3 mie = getMie(screenPos, lightPos) * sunAbsorption;
    float sunDist = clamp(length(max(lightPos.y + 0.1, 0.0)), 0.0, 1.0);
    vec3 totalSky = mix(sky * absorption, sky / (sky + 0.5), sunDist);
    totalSky += mie;
    totalSky *= sunAbsorption * 0.5 + 0.5 * length(sunAbsorption);
    return totalSky;
}
```### 变体 2：臭氧吸收层

已经集成到完整的模板中。将“BETA_OZONE”设置为非零值以启用，在日落时产生更深的蓝色天顶和紫色色调。

### 变体 3：次表面散射 (SSS)

对于半透明材质（蜡烛/皮肤/果冻），使用 SDF 估计的厚度来控制光透射。```glsl
float subsurface(vec3 p, vec3 viewDir, vec3 normal) {
    vec3 scatterDir = refract(viewDir, normal, 1.0 / 1.5); // IOR 1.3~2.0
    vec3 samplePos = p;
    float accumThickness = 0.0;
    float MAX_SCATTER = 2.5;
    for (float i = 0.1; i < MAX_SCATTER; i += 0.2) {
        samplePos += scatterDir * i;
        accumThickness += map(samplePos); // SDF function
    }
    float thickness = max(0.0, -accumThickness);
    float SCATTER_STRENGTH = 16.0;
    return SCATTER_STRENGTH * pow(MAX_SCATTER * 0.5, 3.0) / thickness;
}
// Usage: float ss = max(0.0, subsurface(hitPos, viewDir, normal));
// vec3 sssColor = albedo * smoothstep(0.0, 2.0, pow(ss, 0.6));
// finalColor = mix(lambertian, sssColor, 0.7) + specular;
```### 变体 4：LUT 预计算管道（生产级）

将透射率/多重散射/天空视图预先计算到 LUT 中，仅在运行时进行表查找。```glsl
// Transmittance LUT query (Hillaire 2020)
vec3 getValFromTLUT(sampler2D tex, vec2 bufferRes, vec3 pos, vec3 sunDir) {
    float height = length(pos);
    vec3 up = pos / height;
    float sunCosZenithAngle = dot(sunDir, up);
    vec2 uv = vec2(
        256.0 * clamp(0.5 + 0.5 * sunCosZenithAngle, 0.0, 1.0),
        64.0 * max(0.0, min(1.0, (height - groundRadiusMM) / (atmosphereRadiusMM - groundRadiusMM)))
    );
    uv /= bufferRes;
    return texture(tex, uv).rgb;
}
```### 变体 5：分析快速大气（具有空中视角）

解析指数近似取代射线行进，并支持距离衰减。```glsl
void getRayleighMie(float opticalDepth, float densityR, float densityM, out vec3 R, out vec3 M) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    R = (1.0 - exp(-opticalDepth * densityR * C_RAYLEIGH / 2.5)) * 2.5;
    M = (1.0 - exp(-opticalDepth * densityM * C_MIE / 0.5)) * 0.5;
}

vec3 getLightTransmittance(vec3 lightDir) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    vec3 C_OZONE = vec3(0.650, 1.881, 0.085) * 1e-6;
    float extinction = exp(-clamp(lightDir.y + 0.05, 0.0, 1.0) * 40.0)
                     + exp(-clamp(lightDir.y + 0.5, 0.0, 1.0) * 5.0) * 0.4
                     + pow(clamp(1.0 - lightDir.y, 0.0, 1.0), 2.0) * 0.02
                     + 0.002;
    return exp(-(C_RAYLEIGH + C_MIE + C_OZONE) * extinction * 1e6);
}
```## 表演与作曲

### 性能提示
- **嵌套光线行进 (O(N*M))**：减少步数（移动设备：PRIMARY=12，LIGHT=4），使用解析近似代替光行进，预计算透射率 LUT
- **Dense exp()/pow()**：Schlick 近似替代 HG 相位函数 — `k = 1.55*g - 0.55*g³；相位 = (1-k²) / (4π*(1+k*cosθ)²)`
- **全屏每像素**：Sky-View LUT (200x200) 表查找、半分辨率渲染 + 双线性上采样
- **条带抖动**：0.3 的非均匀步长偏移，临时蓝噪声抖动

### 构图技巧
- **+体积云**：大气透射率决定到达云层的太阳颜色，将“maxDist”设置为云距离
- **+ SDF场景**：SDF命中距离→`maxDist`，场景颜色→`sceneColor`，自动空中透视
- **+ God Rays**：为散射积分添加遮挡（阴影贴图或附加光线行进）
- **+ 地形**：`最终颜色 = 地形颜色 * 透射率 + 内散射`
- **+ PBR/SSS**: `漫反射 = mix(lambert, sss, 0.7);最终 = 环境光 + 反照率*漫反射 + 镜面反射 + 菲涅耳*env`

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/atmospheric-scattering.md)