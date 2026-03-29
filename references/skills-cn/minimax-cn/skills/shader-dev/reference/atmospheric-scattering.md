# 大气和地下散射 - 详细参考

本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、分步解释、数学推导、变体详细信息以及完整的组合代码示例。

## 先决条件

使用此技能之前所需的基本概念：

- **GLSL 基础知识**：统一、变化、内置函数
- **向量数学**：点积、叉积、向量归一化
- **射线-球体相交**：给定射线原点和方向，找到与球体表面的相交距离
- **指数函数的物理意义**（比尔-朗伯定律）：光通过介质呈指数衰减，`I = I₀ × e^(-σ×d)`，其中 σ 是消光系数，d 是距离
- **基本射线行进概念**：沿着射线方向逐步前进，在每个采样点积累信息

## 核心原则

大气散射模拟光子穿过大气并与气体分子/气溶胶颗粒碰撞并改变方向的过程。共有三个核心物理机制：

### 1.瑞利散射（分子散射）

由比光波长小得多的粒子（氮、氧分子）引起。 **短波长（蓝光）比长波长（红光）散射更强** - 这就是为什么天空是蓝色的，日落是红色的。

散射系数与波长的四次方成反比：```
β_R(λ) ∝ 1/λ⁴
```地球的典型海平面值：`β_R = vec3(5.5e-6, 13.0e-6, 22.4e-6)`（RGB 通道，以 m⁻¹ 为单位）

**瑞利相位函数**（描述光散射的角度分布，前后对称）：```
P_R(θ) = 3/(16π) × (1 + cos²θ)
```### 2. 米氏散射（气溶胶散射）

由大小与光波长大致相同的颗粒（水滴、灰尘）引起。 **与波长无关（所有颜色均匀散射）**，但具有很强的前向散射特性，在太阳周围形成光晕。

地球的典型海平面值：“β_M = vec3(21e-6)”（所有通道均相同）

**Henyey-Greenstein 相函数**（描述米氏散射的强前向散射）：```
P_HG(θ, g) = (1 - g²) / (4π × (1 + g² - 2g·cosθ)^(3/2))
```其中`g ε (-1, 1)`控制前向散射强度；典型的地球大气值`g ≈ 0.76 ~ 0.88`。

### 3. 比尔-朗伯衰减

光通过介质的指数衰减：```
T(A→B) = exp(-∫ σ_e(s) ds)   // Transmittance from A to B
```其中“σ_e”是消光系数（消光=散射+吸收）。

### 整体算法流程

沿着视图方向行进（光线行进），在每个样本点：
1.计算该点的大气密度（随高度呈指数下降）
2. 向光源进行第二次行进，计算从太阳到该点的光学深度
3. 使用 Beer-Lambert 计算到达该点的太阳光强度
4. 使用相位函数计算向相机散射的光量
5. 累积所有样本点的贡献

## 实施步骤

### 步骤 1：光线球体相交

**什么**：计算视图光线与大气层的交点，以确定光线行进的开始/结束范围。

**为什么**：大气层是围绕地球的球壳；我们只集成在 shell 中。```glsl
// Ray-sphere intersection, returns distances to two intersection points (t_near, t_far)
// p: ray origin (relative to sphere center), dir: ray direction, r: sphere radius
vec2 raySphereIntersect(vec3 p, vec3 dir, float r) {
    float b = dot(p, dir);
    float c = dot(p, p) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5); // No intersection
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```推导：球面方程 `|p + t·dir|² = r²` 展开为 `t² + 2t·dot(p,dir) + dot(p,p) - r² = 0`。由于`dir`已经归一化，所以可以省略`a=1`，直接用二次公式求解两个t值。

### 步骤 2：定义大气物理常数

**内容**：设置行星和大气的尺度参数和散射系数。

**为什么**：这些物理常数决定了天空的颜色特征。瑞利中不同的RGB值产生蓝色的天空（蓝色通道的散射系数最大）；米氏均匀值会产生白色光晕（所有波长均匀散射）。```glsl
#define PLANET_RADIUS 6371e3          // Earth radius (m)
#define ATMOS_RADIUS  6471e3          // Atmosphere outer radius (m), about 100km above Earth's radius
#define PLANET_CENTER vec3(0.0)       // Planet center position

// Scattering coefficients (m⁻¹), sea-level values
#define BETA_RAY vec3(5.5e-6, 13.0e-6, 22.4e-6) // Tunable: Rayleigh scattering, changes sky base color
#define BETA_MIE vec3(21e-6)                      // Tunable: Mie scattering, changes halo intensity
#define BETA_OZONE vec3(2.04e-5, 4.97e-5, 1.95e-6) // Tunable: ozone absorption, affects zenith deep blue

// Mie phase function anisotropy parameter
#define MIE_G 0.76   // Tunable: 0.76~0.88, larger = more concentrated sun halo

// Scale heights (m): altitude at which density drops to 1/e
#define H_RAY 8000.0  // Tunable: Rayleigh scale height, larger = thicker atmosphere
#define H_MIE 1200.0  // Tunable: Mie scale height, larger = higher haze layer

// Ozone parameters (optional)
#define H_OZONE 30e3         // Ozone peak altitude
#define OZONE_FALLOFF 4e3    // Ozone falloff width

// Sample step counts
#define PRIMARY_STEPS 32 // Tunable: primary ray steps, more = higher quality
#define LIGHT_STEPS 8    // Tunable: light direction steps
```参数调优指南：
- 增加整体“BETA_RAY”→更鲜艳的天空颜色
- 修改“BETA_RAY” RGB 比率 → 更改天空基本色调（例如，增加红色分量会产生更紫色的天空）
- 增加“BETA_MIE”→太阳周围的光晕更亮，雾霾更多
- 增加“MIE_G”→光晕更加集中于太阳方向（更窄的圆盘）
- 增加`H_RAY`→有效大气厚度增加，天空颜色更均匀
- 增加`H_MIE`→雾霾层更高，低空雾气效果减弱

### 步骤 3：实现阶段功能

**什么**：计算光以不同角度散射的概率分布。

**为什么**：瑞利相位是对称分布的（向前和向后散射）； Mie 相强烈向前偏置。这决定了整个天空的亮度分布——面向太阳的亮度较亮（米氏占主导地位），背向太阳的亮度较亮（瑞利占主导地位）。```glsl
// Rayleigh phase function: symmetric front-to-back
float phaseRayleigh(float cosTheta) {
    return 3.0 / (16.0 * 3.14159265) * (1.0 + cosTheta * cosTheta);
}

// Henyey-Greenstein phase function: forward scattering
// g: anisotropy parameter, 0 = isotropic, close to 1 = strong forward scattering
float phaseMie(float cosTheta, float g) {
    float gg = g * g;
    float num = (1.0 - gg) * (1.0 + cosTheta * cosTheta);
    float denom = (2.0 + gg) * pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
    return 3.0 / (8.0 * 3.14159265) * num / denom;
}
```注意：这里的 Mie 相位函数使用了 Cornette-Shanks 的改进版本（分子中附加了“(1 + cos²θ)”项，分母中附加了“(2 + g²)”归一化校正），这比原始 HG 物理上更准确。

### 步骤 4：大气密度采样

**什么**：根据海拔高度计算给定点的大气颗粒密度。

**原因**：大气密度随海拔高度呈指数下降，不同成分（瑞利、米氏、臭氧）具有不同的衰减率。瑞利粒子（气体分子）标度高度约8km，米氏粒子（气溶胶）集中在下层，标度高度约1.2km，臭氧峰值在高度约30km。```glsl
// Returns vec3(rayleigh_density, mie_density, ozone_density)
vec3 atmosphereDensity(vec3 pos, float planetRadius) {
    float height = length(pos) - planetRadius;

    float densityRay = exp(-height / H_RAY);
    float densityMie = exp(-height / H_MIE);

    // Ozone: peaks at ~30km altitude, approximated with Lorentzian distribution
    float denom = (H_OZONE - height) / OZONE_FALLOFF;
    float densityOzone = (1.0 / (denom * denom + 1.0)) * densityRay;

    return vec3(densityRay, densityMie, densityOzone);
}
```臭氧分布的数学解释：“1/(x² + 1)”是洛伦兹/柯西分布的形式，在“x=0”（即“高度 = H_OZONE”）处达到最大值 1，然后在两侧对称衰减。乘以“密度射线”即可得出臭氧也受到整体大气密度下降的影响。

### 步骤 5：光方向光学深度

**内容**：从主光线上的采样点开始，向太阳行进至大气边缘，累积光学深度。

**原因**：这决定了阳光在到达该点之前衰减了多少。日落时，光路穿过更多的大气层，蓝光被散射掉（因为瑞利散射系数的蓝色成分最大），只剩下红光——这就是日落呈红色的物理原因。```glsl
// Compute optical depth from pos along sunDir to the atmosphere edge
vec3 lightOpticalDepth(vec3 pos, vec3 sunDir) {
    float atmoDist = raySphereIntersect(pos - PLANET_CENTER, sunDir, ATMOS_RADIUS).y;
    float stepSize = atmoDist / float(LIGHT_STEPS);
    float rayPos = stepSize * 0.5;

    vec3 optDepth = vec3(0.0); // (ray, mie, ozone)

    for (int i = 0; i < LIGHT_STEPS; i++) {
        vec3 samplePos = pos + sunDir * rayPos;
        float height = length(samplePos - PLANET_CENTER) - PLANET_RADIUS;

        // If sample point is below the surface, it's occluded by the planet
        if (height < 0.0) return vec3(1e10); // Fully occluded

        vec3 density = atmosphereDensity(samplePos, PLANET_RADIUS);
        optDepth += density * stepSize;

        rayPos += stepSize;
    }
    return optDepth;
}
````stepSize * 0.5`作为起始偏移量是中点采样规则，比端点采样更准确地逼近积分。

### 步骤 6：初级散射积分（核心环）

**什么**：光线沿着视图方向行进，计算每个样本点的内散射贡献并累加。

**为什么**：这是整个算法的核心——沿着到达眼睛的视图方向整合所有散射光。每个点的贡献=到达该点的阳光×该点的密度×从该点到相机的衰减。

数学表达式：```
L(camera) = ∫[tStart→tEnd] sunIntensity × T(sun→s) × σ_s(s) × P(θ) × T(s→camera) ds
```其中T为透射率，σ_s为散射系数，P为相位函数。```glsl
vec3 calculateScattering(
    vec3 rayOrigin,    // Camera position
    vec3 rayDir,       // View direction
    float maxDist,     // Maximum distance (scene occlusion)
    vec3 sunDir,       // Sun direction
    vec3 sunIntensity  // Sun intensity
) {
    // Compute ray-atmosphere intersection
    vec2 atmoHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, ATMOS_RADIUS);
    if (atmoHit.x > atmoHit.y) return vec3(0.0); // Missed atmosphere

    // Compute ray-planet intersection (ground occlusion)
    vec2 planetHit = raySphereIntersect(rayOrigin - PLANET_CENTER, rayDir, PLANET_RADIUS);

    // Determine march range
    float tStart = max(atmoHit.x, 0.0);
    float tEnd = atmoHit.y;
    if (planetHit.x > 0.0) tEnd = min(tEnd, planetHit.x); // Ground occlusion
    tEnd = min(tEnd, maxDist); // Scene object occlusion

    float stepSize = (tEnd - tStart) / float(PRIMARY_STEPS);

    // Precompute phase functions (view-sun angle is constant along the entire ray)
    float cosTheta = dot(rayDir, sunDir);
    float phaseR = phaseRayleigh(cosTheta);
    float phaseM = phaseMie(cosTheta, MIE_G);

    // Accumulators
    vec3 totalRay = vec3(0.0); // Rayleigh in-scatter
    vec3 totalMie = vec3(0.0); // Mie in-scatter
    vec3 optDepthI = vec3(0.0); // View direction optical depth (ray, mie, ozone)

    float rayPos = tStart + stepSize * 0.5;

    for (int i = 0; i < PRIMARY_STEPS; i++) {
        vec3 samplePos = rayOrigin + rayDir * rayPos;

        // 1. Sample density
        vec3 density = atmosphereDensity(samplePos, PLANET_RADIUS) * stepSize;
        optDepthI += density;

        // 2. Compute light direction optical depth
        vec3 optDepthL = lightOpticalDepth(samplePos, sunDir);

        // 3. Beer-Lambert attenuation: total attenuation from sun through this point to camera
        vec3 tau = BETA_RAY * (optDepthI.x + optDepthL.x)
                 + BETA_MIE * 1.1 * (optDepthI.y + optDepthL.y) // 1.1 is Mie extinction/scattering ratio
                 + BETA_OZONE * (optDepthI.z + optDepthL.z);
        vec3 attenuation = exp(-tau);

        // 4. Accumulate in-scattering
        totalRay += density.x * attenuation;
        totalMie += density.y * attenuation;

        rayPos += stepSize;
    }

    // 5. Final color = scattering coefficient × phase function × accumulated scattering
    return sunIntensity * (
        totalRay * BETA_RAY * phaseR +
        totalMie * BETA_MIE * phaseM
    );
}
```关键细节说明：
- `1.1` 是米氏消光/散射比：米氏粒子不仅会散射光，还会吸收少量光，因此消光系数 ≈ 1.1 × 散射系数
- `optDepthI` 同时记录所有三个分量，以便在衰减计算中正确合成所有消光贡献
- 相位函数是在循环外部预先计算的，因为视图和太阳方向之间的角度沿整个光线是恒定的

### 步骤 7：色调映射和输出

**内容**：对 HDR 散射结果应用色调映射和伽玛校正。

**为什么**：散射计算输出 HDR 线性值（可能远大于 1.0），必须将其映射到 [0,1] 才能显示。不同的色调映射方法会影响最终的外观：

- **曝光映射`1 - exp(-x)`**：最简单，自然饱和且不会过度曝光，但高光细节有限
- **Reinhard**：保留更多高光细节，适合高动态范围场景
- **ACES**：电影色调映射，色彩更丰富，但实现更复杂```glsl
// Method 1: Simple exposure mapping (most common)
vec3 tonemapExposure(vec3 color) {
    return 1.0 - exp(-color); // Natural saturation, never overexposes
}

// Method 2: Reinhard (preserves more highlight detail)
vec3 tonemapReinhard(vec3 color) {
    float l = dot(color, vec3(0.2126, 0.7152, 0.0722));
    vec3 tc = color / (color + 1.0);
    return mix(color / (l + 1.0), tc, tc);
}

// Gamma correction
vec3 gammaCorrect(vec3 color) {
    return pow(color, vec3(1.0 / 2.2));
}
```Reinhard 实现细节：使用亮度“l”（感知加权）和每通道映射“tc”的混合，平衡颜色保真度和高光细节。

## 变体详细信息

### 变体 1：非物理分析近似（无光线行进）

**与基础版本的区别**：根本没有光线行进——使用分析函数以极高的性能模拟天空颜色。不是基于物理散射方程，而是使用经验公式来模拟视觉效果。

**使用案例**：移动平台、背景、物理精度要求不高的场景。

**它是如何工作的**：
- `zenithDensity` 模拟大气密度随视角的变化（朝地平线看更密集）
- `getSkyAbduction` 使用 `exp2` 来模拟大气吸收（类似于 Beer-Lambert）
- `getMie` 使用距离衰减 + smoothstep 来模拟太阳光晕
- 最终的混合考虑了太阳高度对整体天空色调的影响

**性能比较**：无循环，无光线行进 - 每个像素仅进行少量数学计算，比基本版本快 10-50 倍。

### 变体 2：带有臭氧吸收层

**与基础版本的区别**：添加臭氧吸收作为第三个组成部分，使天顶变得更深蓝色，并在日落时引入微妙的紫色色调。

**用例**：追求物理上更准确的天空颜色。

**物理原理**：臭氧主要在查普伊斯波段（500-700nm，即绿色和红色）吸收，使天顶方向（光路短，瑞利散射被臭氧过滤后剩余的光）呈现更深的蓝色。日落时，长光路使得臭氧吸收更加显着——红色经过瑞利散射、绿色被臭氧吸收后，只剩下蓝紫色调。

**关键修改**：在完整模板中将“BETA_OZONE”设置为非零值以启用 - 已经内置。

### 变体 3：次表面散射 (SSS)

**与基本版本的区别**：散射在半透明物体内而不是大气中。通过 SDF 估计物体厚度并通过厚度控制光传输。

**使用案例**：蜡烛、皮肤、果冻、树叶和其他半透明材料。

**它是如何工作的**：
1.利用斯涅耳定律（`折射`）计算光线进入物体后的折射方向
2.沿着SDF中的折射方向行进，累积负距离值（SDF在物体内部为负值）
3.累积负值越大，物体越厚，透光率越低
4.使用幂函数来控制衰减曲线（`pow`参数可调）

**可调参数**：
- IOR（折射率）：1.3（水）~1.5（玻璃）~2.0（宝石），影响折射角度
- `MAX_SCATTER`：最大分散行进距离，影响SSS穿透深度
- `SCATTER_STRENGTH`：散射强度乘数
- 步长0.2：更小=更准确但更慢

**用法**：```glsl
float ss = max(0.0, subsurface(hitPos, viewDir, normal));
vec3 sssColor = albedo * smoothstep(0.0, 2.0, pow(ss, 0.6));
finalColor = mix(lambertian, sssColor, 0.7) + specular;
```### 变体 4：LUT 预计算管道（生产级）

**与基础版本的区别**：将透射率、多重散射和天空视图预先计算为单独的 LUT 纹理；在运行时仅执行查找，具有极高的帧速率。

**用例**：游戏引擎和需要高帧速率的实时应用程序中的生产级天空渲染。

**架构细节**：

- **缓冲区A（透射率LUT）**：256x64纹理，参数化为（sunCosZenith，高度），存储从某个高度沿某个方向到大气边缘的透射率。这是最基本的LUT； all other LUTs depend on it.

- **缓冲区 B（多重散射 LUT）**：32x32 纹理，预先计算多重散射贡献。单次散射不够准确——在真实大气中，光会被多次散射。该 LUT 使用迭代方法来近似多次散射的累积效应。

- **缓冲区 C（天空视图 LUT）**：200x200 纹理，存储各个方向的天空颜色。使用非线性高度映射为地平线区域（颜色变化最剧烈的区域）分配更高的精度。

- **Image Pass**：仅查找Sky-View LUT +覆盖太阳盘；每个像素只需要一次纹理查询。```glsl
// Transmittance LUT query (from Hillaire 2020 implementation)
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
```**性能**：Image Pass 接近 O(1)；所有繁重的计算都是在低分辨率 LUT 中完成的。 LUT 可以随着太阳角度的变化而增量更新。

### 变体 5：分析快速大气（无射线行进，但支持空中透视）

**与基础版本的区别**：使用分析指数近似而不是光线行进，同时支持距离衰减的空中透视效果。

**用例**：游戏场景需要大气透视而不需要每像素光线行进。

**它是如何工作的**：
- `getRayleighMie` 使用 `1 - exp(-x)` 形式来近似散射积分（基于 Beer-Lambert 的解析解）
- `getLightTransmittance` 使用多个指数项叠加来近似不同太阳高度下的光学深度
- 无需循环——每个像素只需固定数量的数学运算```glsl
// Based on Felix Westin's Fast Atmosphere
void getRayleighMie(float opticalDepth, float densityR, float densityM, out vec3 R, out vec3 M) {
    vec3 C_RAYLEIGH = vec3(5.802, 13.558, 33.100) * 1e-6;
    vec3 C_MIE = vec3(3.996e-6);
    R = (1.0 - exp(-opticalDepth * densityR * C_RAYLEIGH / 2.5)) * 2.5;
    M = (1.0 - exp(-opticalDepth * densityM * C_MIE / 0.5)) * 0.5;
}

// Analytical approximation of light transmittance (replaces ray march)
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
```**解析近似的数学基础**：将大气视为单个均匀层，散射积分`∫ e^(-σx) dx`具有解析解`(1 - e^(-σL)) / σ`。代码中的“2.5”和“0.5”是经验缩放因子，使分析结果在视觉上近似于完整的光线行进。

## 性能优化详情

### 瓶颈 1：嵌套 Ray March（O(N×M) 个样本）

N 个主光线步数 × 每步 M 个光方向步数 = N×M 密度计算。

**优化方法**：
- **减少步数**：在移动设备上使用“PRIMARY_STEPS=12，LIGHT_STEPS=4”；视觉差异很小，但性能提升显着
- **分析近似**：用快速大气方法替换光线方向光线行进，将复杂性从 O(N×M) 降低到 O(N)
- **透射率LUT**：预计算后，运行时仅执行查找，将复杂度降低至 O(N) 甚至 O(1)

### 瓶颈 2：密集的 exp() 和 pow() 调用

每个样本点进行多次指数函数调用——这些是 GPU 上相对昂贵的操作。

**优化方法**：
- 用 Schlick 近似替换 Henyey-Greenstein 相函数：```glsl
// Schlick approximation, only 1 division, no pow
float k = 1.55 * g - 0.55 * g * g * g;
float phaseSchlick = (1.0 - k * k) / (4.0 * PI * pow(1.0 + k * cosTheta, 2.0));
```- 合并多个exp调用：`exp(a) * exp(b) = exp(a+b)`，减少exp调用次数
- 在精度要求较低的场景中使用“exp2”而不是“exp”（exp2在某些GPU上更快）

### 瓶颈3：全屏逐像素计算

每个像素独立计算全散射。

**优化方法**：
- **天空视图 LUT**：将天空渲染为低分辨率 LUT（例如 200x200），然后以全分辨率查找。在地平线附近分配更多分辨率（非线性映射）
- **半分辨率渲染**：以半分辨率计算散射，然后双线性上采样。对于天空（低频信号）来说，质量损失很小

### 瓶颈 4：需要大量样本才能避免条带

步数低会导致可见的条带伪影。

**优化方法**：
- **非均匀步进**：`newT = ((i + 0.3) / numSteps) * tMax`，偏移 0.3 而不是 0.5 以减少视觉伪影
- **抖动开始偏移**：`startOffset += hash(fragCoord) * stepSize`，随机偏移每个像素的行进开始
- **时域蓝噪声抖动**：使用时域蓝噪声跨帧抖动样本位置；与 TAA 结合使用，条带几乎消除

## 组合建议

### 1. 大气散射 + 体积云

大气散射提供天空背景颜色和光源颜色；体积云照明使用大气透射率来确定到达云层的太阳光颜色。

关键集成点：
- 将大气散射函数的“maxDist”参数设置为云层距离，以实现正确的云前大气效果
- 云层渲染时，使用透射率LUT获取太阳光到达云层时的颜色
- 云层后面的天空颜色应该是完整的大气散射结果```glsl
// Pseudo-code example
float cloudDist = rayMarchClouds(rayOrigin, rayDir);
vec3 cloudColor = calculateCloudLighting(cloudPos, sunDir, transmittance);
vec3 skyBehind = calculateScattering(rayOrigin, rayDir, 1e12, sunDir, sunIntensity);
vec3 skyBeforeCloud = calculateScattering(rayOrigin, rayDir, cloudDist, sunDir, sunIntensity);

// Compositing: pre-cloud atmosphere + cloud × cloud opacity + post-cloud sky × transmittance
vec3 final = skyBeforeCloud + cloudColor * cloudAlpha + skyBehind * (1.0 - cloudAlpha) * atmosphereTransmittance;
```### 2.大气散射+SDF场景

将SDF射线行进距离作为“maxDist”参数传递给“calculateScattering()”，并将场景颜色作为“sceneColor”，以自动获得空中透视效果。```glsl
// SDF ray march yields hit information
float hitDist = sdfRayMarch(rayOrigin, rayDir);
vec3 sceneColor = shadeSurface(hitPos, normal, lightDir);

// Atmospheric scattering automatically handles perspective
vec3 final = calculateScattering(
    rayOrigin, rayDir, hitDist,
    sceneColor, sunDir, SUN_INTENSITY
);
```### 3.大气散射+上帝射线

在散射积分中添加遮挡参数（通过阴影贴图或用于遮挡检测的附加光线行进）可以产生体积光束效果。```glsl
// Add occlusion detection in the main loop
for (int i = 0; i < PRIMARY_STEPS; i++) {
    // ... density sampling ...

    // God rays: check if sample point is occluded
    float occlusion = 1.0;
    if (sdfScene(samplePos + sunDir * 0.1) < 0.0) {
        occlusion = 0.0; // Occluded by scene object, no in-scattering
    }

    totalRay += density.x * attenuation * occlusion;
    totalMie += density.y * attenuation * occlusion;
}
```Fast Atmosphere 示例通过“occlusion”参数实现此功能。

### 4.大气散射+地形渲染

使用空中透视：远处的地形颜色根据距离融入大气散射颜色。

关键公式：```glsl
// Basic aerial perspective
vec3 finalColor = terrainColor * transmittance + inscattering;

// transmittance: atmospheric transmittance from camera to terrain point
// inscattering: scattered light between camera and terrain point
// Distant objects: transmittance → 0, inscattering dominates → appears blue/gray
```### 5.SSS + PBR 材质

将次表面散射与 GGX 微表面镜面反射和菲涅耳反射相结合。 SSS 贡献替换了部分漫反射（通过混合），并在顶部添加了镜面反射层：```glsl
// Complete PBR + SSS shading
float fresnel = pow(max(0.0, 1.0 + dot(normal, viewDir)), 5.0);
vec3 diffuse = mix(lambert, sssContribution, 0.7);  // SSS replaces part of diffuse
vec3 final = ambient + albedo * diffuse + specular + fresnel * envColor;
```分层逻辑：
1.底层：环境光
2. 漫反射层：Lambert 和 SSS 的混合（SSS 允许光线穿过暗面）
3.镜面层：GGX微表面反射
4.菲涅耳层：增强掠射角环境反射