# 体积渲染——详细参考

本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、分步解释、数学推导和高级用法。

## 先决条件

- **GLSL 基础知识**：统一、变化、内置函数
- **向量数学**：点积、叉积、归一化
- **射线表示**：`P = ro + t * rd`（射线原点 + t × 射线方向）
- **噪声函数基础**：值噪声、柏林噪声、fBM（分形布朗运动）
- **基本光学概念**：
  - 透射率：光穿过介质后剩余的部分
  - 散射：光在介质内改变方向
  - 吸收：光能被介质转化为热能

## 核心原则

体积渲染的核心是**光线行进**：沿着每条视图光线，以固定或自适应步长前进，查询每个样本点的介质密度，并累积颜色和不透明度。

### 关键数学公式

#### 1. 比尔-朗伯透射定律

光穿过厚度为 d 、消光系数为 σe 的介质时的透射率：```
T = exp(-σe × d)
```其中`σe = σs + σa`（散射系数+吸收系数）。

**物理意义**：消光系数越大或介质越厚，通过的光越少。这是所有体积渲染的基本法则。

#### 2. 从前到后 Alpha 合成

标准形式：```
color_acc += sample_color × sample_alpha × (1.0 - alpha_acc)
alpha_acc += sample_alpha × (1.0 - alpha_acc)
```等效的预乘 alpha 形式（实际代码中最常用）：```glsl
col.rgb *= col.a;           // Premultiply
sum += col * (1.0 - sum.a); // Front-to-back compositing
```**为什么从前到后？** 因为它允许在累积不透明度接近 1.0 时提前退出（提前光线终止），从而节省大量计算。

#### 3. Henyey-Greenstein 相函数

描述介质中光散射的方向分布：```
HG(cosθ, g) = (1 - g²) / (1 + g² - 2g·cosθ)^(3/2)
```- `g > 0`：前向散射（例如，云中的一线希望效应）——光主要沿着其原始方向继续传播
- `g < 0`：后向散射 - 光主要反射回来
- `g = 0`：各向同性散射 - 光在各个方向上均匀散射

**实际应用**：云通常使用双瓣HG函数，混合前向散射瓣（g≈0.8）和后向散射瓣（g≈-0.2）来模拟云层的真实光散射特性。前向散射产生一线希望，而后向散射则提供体积定义。

#### 4. 冻伤改进积分公式

在每一步中，散射光不是简单的“S × dt”，而是一个更精确的积分：```
Sint = (S - S × exp(-σe × dt)) / σe
```**为什么需要改进？** 简单的“S × dt”积分高估了较大步长或较强散射的散射光，导致能量不守恒（图像太亮或太暗）。 Frostbite 公式通过精确积分比尔-朗伯定律，确保任何步长下的能量守恒。

## 实施步骤

### 第 1 步：相机和光线构建

**什么**：从相机为每个像素生成一条光线。

**为什么**：这是所有光线行进技术的起点。摄像头位置决定视角；射线方向决定采样路径。```glsl
// Normalize screen coordinates to [-1,1], correcting for aspect ratio
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Camera parameters
vec3 ro = vec3(0.0, 1.0, -5.0);  // Tunable: camera position
vec3 ta = vec3(0.0, 0.0, 0.0);   // Tunable: look-at target

// Build camera matrix
vec3 ww = normalize(ta - ro);
vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
vec3 vv = cross(uu, ww);

// Generate ray direction
float fl = 1.5; // Tunable: focal length, larger = narrower FOV
vec3 rd = normalize(uv.x * uu + uv.y * vv + fl * ww);
```**关键参数说明**：
- `ro`：相机位置 - 改变它围绕体积的轨道
- `ta`：注视目标 — 相机指向该位置
- `fl`：焦距 — 1.0 ≈ 90° FOV，1.5 ≈ 67° FOV，2.0 ≈ 53° FOV
- 使用“iResolution.y”进行标准化可确保圆圈不会扭曲

### 步骤 2：体积边界相交

**什么**：计算光线进入和离开体积的距离“tmin”/“tmax”，限制行进范围。

**为什么**：避免在空白区域浪费样本。不同的体积形状使用不同的相交方法。```glsl
// --- Method A: Horizontal plane boundaries (cloud layers) ---
float yBottom = -1.0; // Tunable: volume bottom Y coordinate
float yTop    =  2.0; // Tunable: volume top Y coordinate
float tmin = (yBottom - ro.y) / rd.y;
float tmax = (yTop    - ro.y) / rd.y;
if (tmin > tmax) { float tmp = tmin; tmin = tmp; tmax = tmin; tmin = tmp; }
// In practice, handle edge cases like ray direction parallel to plane

// --- Method B: Sphere boundary (explosions, fur balls, atmospheres) ---
// Returns intersection distances of ray with sphere centered at origin with radius r
vec2 intersectSphere(vec3 ro, vec3 rd, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float d = b * b - c;
    if (d < 0.0) return vec2(1e5, -1e5); // No hit
    d = sqrt(d);
    return vec2(-b - d, -b + d);
}
```**选型指南**：
- 对云层等水平分布的体积使用平面边界（方法 A）
- 对爆炸或行星大气等球形体积使用球体相交（方法 B）
- AABB（轴对齐边界框）相交也可用于长方体形状的体积

### 步骤 3：密度场定义

**什么**：定义空间中每个点的介质密度。这是体积渲染中最核心、最灵活的部分。

**为什么**：密度场决定了体积的形状、纹理和动态特性。不同的密度函数产生完全不同的视觉效果。```glsl
// 3D Value Noise (classic texture-lookup-based implementation)
float noise(vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f); // smoothstep interpolation

    vec2 uv = (p.xy + vec2(37.0, 239.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z);
}

// fBM (Fractal Brownian Motion) — layering multiple frequency noises
float fbm(vec3 p) {
    float f = 0.0;
    f += 0.50000 * noise(p); p *= 2.02;
    f += 0.25000 * noise(p); p *= 2.03;
    f += 0.12500 * noise(p); p *= 2.01;
    f += 0.06250 * noise(p); p *= 2.02;
    f += 0.03125 * noise(p);
    return f;
}

// Cloud density function example
float cloudDensity(vec3 p) {
    vec3 q = p - vec3(0.0, 0.1, 1.0) * iTime; // Wind direction animation
    float f = fbm(q);
    // Use Y coordinate to limit cloud height range
    return clamp(1.5 - p.y - 2.0 + 1.75 * f, 0.0, 1.0);
}
```**密度场设计要点**：
- “noise”函数使用纹理查找（“iChannel0”）来实现 3D 值噪声，比纯算术实现更快
- `fbm` 分层 5 个八度的噪声以产生自然的分形细节
- 非整数倍频器（2.02、2.03）破坏重复性
- 在`cloudDensity`中，`1.5 - p.y - 2.0`建立一个随着高度减小的基础密度场
- 时间偏移“iTime”产生风吹效果

### 步骤 4：光线行进主循环

**什么**：沿着光线从“tmin”行进到“tmax”，每一步采样密度并累积颜色和不透明度。

**为什么**：这是体积渲染的核心循环。步数和步长直接影响质量和性能。```glsl
#define NUM_STEPS 64        // Tunable: march steps, more = finer
#define STEP_SIZE 0.05      // Tunable: fixed step size (or use adaptive)

vec4 raymarch(vec3 ro, vec3 rd, float tmin, float tmax, vec3 bgCol) {
    vec4 sum = vec4(0.0); // rgb = accumulated color (premultiplied alpha), a = accumulated opacity

    // Jitter starting position to eliminate banding artifacts
    float t = tmin + STEP_SIZE * fract(sin(dot(fragCoord, vec2(12.9898, 78.233))) * 43758.5453);

    for (int i = 0; i < NUM_STEPS; i++) {
        if (t > tmax || sum.a > 0.99) break; // Early exit: out of range or fully opaque

        vec3 pos = ro + t * rd;
        float den = cloudDensity(pos);

        if (den > 0.01) {
            // --- Color and lighting (see Step 5) ---
            vec4 col = vec4(1.0, 0.95, 0.8, den); // Placeholder color

            // Opacity scaling
            col.a *= 0.4; // Tunable: density scale factor
            // Can also multiply by step size: col.a = min(col.a * 8.0 * dt, 1.0);

            // Premultiply alpha and front-to-back compositing
            col.rgb *= col.a;
            sum += col * (1.0 - sum.a);
        }

        t += STEP_SIZE;
        // Adaptive step variant: t += max(0.05, 0.02 * t);
    }

    return clamp(sum, 0.0, 1.0);
}
```**关键设计决策**：
- **步数与步长**：固定步数适合已知的体积大小；固定步长适合不确定的体积大小
- **抖动**：没有抖动，出现可见的条带伪影；添加与像素相关的随机偏移将条带转换为不可见的噪声
- **提前退出条件**：`sum.a > 0.99` 是最重要的性能优化之一
- **密度阈值**：`den > 0.01` 跳过空白区域，避免不必要的照明计算
- **自适应步长**：`max(0.05, 0.02 * t)` 提供近距离的小步长（良好的细节）和远距离的大步长（快速）

### 步骤 5：照明计算

**内容**：计算体积内每个样本点的照明颜色。

**为什么**：光照是体积渲染中视觉质量的决定因素。不同的照明模式适合不同的场景。```glsl
// === Method A: Directional derivative lighting (simplest, single extra sample) ===
// Classic directional derivative method, requires only 1 extra noise sample
vec3 sundir = normalize(vec3(1.0, 0.0, -1.0)); // Tunable: sun direction
float dif = clamp((den - cloudDensity(pos + 0.3 * sundir)) / 0.6, 0.0, 1.0);
vec3 lin = vec3(1.0, 0.6, 0.3) * dif + vec3(0.91, 0.98, 1.05); // Sunlight color + sky light
```**方法 A 详细信息**：通过将当前点的密度与沿光方向的偏移位置进行比较来估计光照。密度减小的方向表示光源。这是一种近似方法——速度极快，但物理上不太准确。适用于风格化云或性能关键场景。```glsl
// === Method B: Volumetric shadow (secondary ray march) ===
// Volumetric shadow (Frostbite-style)
float volumetricShadow(vec3 from, vec3 lightDir) {
    float shadow = 1.0;
    float dt = 0.5;            // Tunable: shadow step size
    float d = dt * 0.5;
    for (int s = 0; s < 6; s++) { // Tunable: shadow steps (6-16)
        vec3 pos = from + lightDir * d;
        float muE = cloudDensity(pos);
        shadow *= exp(-muE * dt); // Beer-Lambert
        dt *= 1.3;               // Tunable: step size increase factor
        d += dt;
    }
    return shadow;
}
```**方法 B 详细信息**：对于每个采样点，向光源执行第二次光线行进，累积透射率。这是物理上更准确的方法，但计算成本较高（每个主要步骤需要额外的 6-16 个影子步骤）。增加步长（`dt *= 1.3`）是因为远处区域对阴影的贡献较小。```glsl
// === Method C: Henyey-Greenstein phase function scattering ===
float HenyeyGreenstein(float cosTheta, float g) {
    float gg = g * g;
    return (1.0 - gg) / pow(1.0 + gg - 2.0 * g * cosTheta, 1.5);
}
// Mix forward and backward scattering
float sundotrd = dot(rd, -sundir);
float scattering = mix(
    HenyeyGreenstein(sundotrd, 0.8),   // Tunable: forward scattering g value
    HenyeyGreenstein(sundotrd, -0.2),  // Tunable: backward scattering g value
    0.5                                 // Tunable: blend ratio
);
```**方法C细节**：相位函数描述了光在不同方向上散射的概率分布。双瓣 HG 函数混合前向和后向散射，模拟云一线效应（前​​向散射瓣）和暗侧体积定义（后向散射瓣）。 “g=0.8”的前向散射使照亮的一面非常明亮——这是真实云的一个重要视觉特征。

### 第 6 步：颜色映射

**什么**：将密度值映射到颜色。

**为什么**：不同的介质（云、火焰、爆炸）需要不同的着色策略。```glsl
// === Method A: Density interpolation coloring (clouds) ===
vec3 cloudColor = mix(vec3(1.0, 0.95, 0.8),   // Lit side color (tunable)
                      vec3(0.25, 0.3, 0.35),   // Dark side color (tunable)
                      den);
```**方法A细节**：低密度区域显示明亮的颜色（接近白色，模拟薄云半透明），高密度区域显示深色（灰蓝色，模拟厚云遮光）。简单高效。```glsl
// === Method B: Radial gradient coloring (explosions, flames) ===
vec3 computeColor(float density, float radius) {
    vec3 result = mix(vec3(1.0, 0.9, 0.8),
                      vec3(0.4, 0.15, 0.1), density);
    vec3 colCenter = 7.0 * vec3(0.8, 1.0, 1.0);  // Tunable: core highlight color
    vec3 colEdge = 1.5 * vec3(0.48, 0.53, 0.5);   // Tunable: edge color
    result *= mix(colCenter, colEdge, min(radius / 0.9, 1.15));
    return result;
}
```**方法 B 详细信息**：爆炸/火焰核心极其明亮（HDR 值 > 1.0，乘以 7.0），而边缘较暗。密度和距中心的距离决定颜色。核心颜色乘以 7.0 会产生过度曝光效果，与后处理色调映射相结合，产生灼热的外观。```glsl
// === Method C: Height-based ambient gradient (production-grade clouds) ===
vec3 ambientLight = mix(
    vec3(39., 67., 87.) * (1.5 / 255.),   // Bottom ambient color (tunable)
    vec3(149., 167., 200.) * (1.5 / 255.), // Top ambient color (tunable)
    normalizedHeight
);
```**方法 C 详细信息**：真实的云底部呈深蓝色（接收地面反射和天空散射），而顶部呈较亮的灰蓝色（接收更多天空光）。使用归一化高度进行插值会产生自然的垂直梯度。

### 步骤 7：最终合成和后处理

**内容**：将体积渲染结果与背景混合，应用色调映射和后处理。

**为什么**：后处理显着影响最终的视觉质量。```glsl
// Background sky
vec3 bgCol = vec3(0.6, 0.71, 0.75) - rd.y * 0.2 * vec3(1.0, 0.5, 1.0);
float sun = clamp(dot(sundir, rd), 0.0, 1.0);
bgCol += 0.2 * vec3(1.0, 0.6, 0.1) * pow(sun, 8.0); // Sun halo

// Composite volume with background
vec4 vol = raymarch(ro, rd, tmin, tmax, bgCol);
vec3 col = bgCol * (1.0 - vol.a) + vol.rgb;

// Sun flare
col += vec3(0.2, 0.08, 0.04) * pow(sun, 3.0);

// Tone mapping (simple smoothstep version)
col = smoothstep(0.15, 1.1, col);

// Optional: distance fog (inside the marching loop)
// col.xyz = mix(col.xyz, bgCol, 1.0 - exp(-0.003 * t * t));

// Optional: vignette
float vignette = 0.25 + 0.75 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.1);
col *= vignette;
```**后处理细节**：
- **天空渐变**：`rd.y`控制从地平线到天顶的天空颜色变化
- **太阳光环**：`pow(sun, 8.0)`产生狭窄、明亮的光环；指数越高=光环越窄
- **太阳耀斑**：`pow(sun, 3.0)`产生更广泛的暖色耀斑
- **距离雾**：`exp(-0.003 * t * t)`逐渐将远处的体积融合到背景中
- **色调映射**：`smoothstep(0.15, 1.1, col)` 提升阴影、压缩高光并增加对比度
- **晕影**：模拟镜头晕影效果，引导视觉焦点到画面中心

## 变体详细信息

### 变体 1：发射量（火焰/爆炸）

**与基础版的区别**：无外部光源；颜色完全由密度和位置决定。密度映射到发射颜色。

**设计理念**：火焰和爆炸是自发光的——无需外部照明计算。核心区域极其明亮（HDR），而边缘则暗淡。颜色通过密度和距中心的距离的组合来映射。光晕效果是通过在累积循环中添加距离衰减的光源贡献来实现的。

**关键代码**：```glsl
// Replace lighting calculation with emissive color mapping
vec3 emissionColor(float density, float radius) {
    vec3 result = mix(vec3(1.0, 0.9, 0.8), vec3(0.4, 0.15, 0.1), density);
    vec3 colCenter = 7.0 * vec3(0.8, 1.0, 1.0);
    vec3 colEdge = 1.5 * vec3(0.48, 0.53, 0.5);
    result *= mix(colCenter, colEdge, min(radius / 0.9, 1.15));
    return result;
}
// Use bloom effect in the accumulation loop
vec3 lightColor = vec3(1.0, 0.5, 0.25);
sum.rgb += lightColor / exp(lDist * lDist * lDist * 0.08) / 30.0;
```### 变体 2：物理散射大气（瑞利 + 米氏）

**与基础版本的区别**：使用嵌套光线行进来计算光学深度；分离瑞利和米氏散射通道；使用精确的比尔-朗伯透射率。

**设计理念**：大气散射需要分别处理两种散射机制：
- **瑞利散射**：与波长相关（波长越短散射越多），产生蓝天效应。散射系数与 λ⁻⁴ 成正比。
- **米氏散射**：与波长无关，主要由气溶胶/大颗粒引起，产生日落的橙红色和太阳周围的白色光晕。

密度随高度呈指数下降，使用不同的尺度高度参数来控制两种散射类型的高度分布。嵌套光线行进（每个样本点向太阳行进）计算光学深度以获得精确的比尔-朗伯透射率。

**关键代码**：```glsl
// Atmospheric density decreases exponentially with altitude
float density(vec3 p, float scaleHeight) {
    return exp(-max(length(p) - R_INNER, 0.0) / scaleHeight);
}
// Nested ray march to compute optical depth
float opticDepth(vec3 from, vec3 to, float scaleHeight) {
    vec3 s = (to - from) / float(NUM_STEPS_LIGHT);
    vec3 v = from + s * 0.5;
    float sum = 0.0;
    for (int i = 0; i < NUM_STEPS_LIGHT; i++) {
        sum += density(v, scaleHeight);
        v += s;
    }
    return sum * length(s);
}
// Rayleigh phase function
float phaseRayleigh(float cc) { return (3.0 / 16.0 / PI) * (1.0 + cc); }
// Combined Rayleigh + Mie
vec3 scatter = sumRay * kRay * phaseRayleigh(cc) + sumMie * kMie * phaseMie(-0.78, c, cc);
```### 变体 3：Frostbite 节能集成

**与基本版本的区别**：使用改进的散射积分公式，在强散射介质中保持能量守恒。

**设计理念**：朴素欧拉积分“S × dt”在大步长或密集介质中不准确。 Frostbite 公式对每一步的散射进行精确的指数积分，确保无论步长如何，累积的散射和透射率之和都不会超过入射光。这对于浓雾、体积照明和类似场景尤其重要。

**关键代码**：```glsl
// Replace naive integration with Frostbite formula
vec3 S = evaluateLight(p) * sigmaS * phaseFunction() * volumetricShadow(p, lightPos);
vec3 Sint = (S - S * exp(-sigmaE * dt)) / sigmaE; // Improved integration
scatteredLight += transmittance * Sint;
transmittance *= exp(-sigmaE * dt);
```### 变体 4：生产级云（地平线零之曙光风格）

**与基础版本的区别**：使用 Perlin-Worley 噪声纹理而不是程序噪声；分层密度建模（基础形状+细节侵蚀）；双瓣HG相位函数；时间重投影抗锯齿。

**设计理念**：生产级云渲染采用分层方法：
1. **低频形状层** (`cloudMapBase`)：使用 Perlin-Worley 3D 纹理来定义粗糙的云形状
2. **高度梯度** (`cloudGradient`)：根据云类型（积云、层云等）控制随高度的密度分布
3. **高频细节层**（`cloudMapDetail`）：高频噪声侵蚀边缘，添加细节
4. **覆盖控制** (`COVERAGE`)：控制天空云覆盖比例的全局参数

时间重投影是生产级方法的关键：每个帧仅渲染 1/16 像素（棋盘图案），然后将结果重新投影到当前帧。结合 95% 的历史帧混合，它以最少的行进步骤实现了高质量的结果。

**关键代码**：```glsl
// Layered noise modeling
float m = cloudMapBase(pos, norY);          // Low-frequency shape
m *= cloudGradient(norY);                    // Height gradient
m -= cloudMapDetail(pos) * dstrength * 0.225; // High-frequency detail erosion
m = smoothstep(0.0, 0.1, m + (COVERAGE - 1.0));
// Dual-lobe HG scattering
float scattering = mix(
    HenyeyGreenstein(sundotrd, 0.8),   // Forward
    HenyeyGreenstein(sundotrd, -0.2),  // Backward
    0.5
);
// Temporal reprojection (between Buffers)
vec2 spos = reprojectPos(ro + rd * dist, iResolution.xy, iChannel1);
vec4 ocol = texture(iChannel1, spos, 0.0);
col = mix(ocol, col, 0.05); // 5% new frame + 95% history frame
```### 变体 5：渐变法线表面照明（毛球/体积表面）

**与基本版本的区别**：使用中心差分来计算体积内的梯度法线，然后应用漫反射+镜面反射照明，就好像它是一个表面一样。适用于具有清晰“表面”感觉的体积物体（毛皮、半透明球体）。

**设计理念**：一些体积对象（毛球、模糊表面）是体积数据，但视觉上类似于表面对象。在这种情况下，密度场的中心差分计算梯度（密度变化最快的方向），这作为传统表面照明模型的法线。

- **半朗伯**：`dot(N, L) * 0.5 + 0.5` 压缩暗侧范围，模拟次表面散射
- **Blinn-Phong**：提供镜面反射，添加材质定义

**关键代码**：```glsl
// Central differencing for normals
vec3 furNormal(vec3 pos, float density) {
    float eps = 0.01;
    vec3 n;
    n.x = sampleDensity(pos + vec3(eps, 0, 0)) - density;
    n.y = sampleDensity(pos + vec3(0, eps, 0)) - density;
    n.z = sampleDensity(pos + vec3(0, 0, eps)) - density;
    return normalize(n);
}
// Half-Lambert diffuse + Blinn-Phong specular
vec3 N = -furNormal(pos, density);
float diff = max(0.0, dot(N, L) * 0.5 + 0.5);  // Half-Lambert
float spec = pow(max(0.0, dot(N, H)), 50.0);     // Tunable: specular sharpness
```## 深入的性能优化

### 1. 早期光线终止

当累积的不透明度超过阈值（例如 0.99）时，立即中断循环。这是最重要的优化——所有分析的着色器都使用它。

**效果**：对于密集体积（例如厚云层），许多光线可以在20-30步内退出，而不是完成全部80+步，实现2-4倍的性能提升。

### 2.LOD 噪声

根据光线距离减少 fBM 倍频程计数。远处区域不需要高频细节：```glsl
int lod = 5 - int(log2(1.0 + t * 0.5));
```**效果**：远处区域仅使用 2-3 个 fBM 八度音程（而近距离区域则使用 5 个），将噪声采样减少 40-60%。由于远处的像素覆盖了更大的空间范围，因此高频细节无论如何都不会可见。

### 3.自适应步长

近距离小步（精细细节），远距离大步（速度）：```glsl
float dt = max(0.05, 0.02 * t);
```**效果**：显着减少远距离步数，而不会明显降低近场质量。然而，突然的步长变化可能会导致视觉不连续。

### 4. 抖动

在光线起始位置添加与像素相关的随机偏移，以消除步进带状伪影：```glsl
t += STEP_SIZE * hash(fragCoord);
```**注意**：抖动不会提高性能，但会显着提高视觉质量 - 将可见的条带伪影转换为难以察觉的高频噪声。

### 5. 边界体积裁剪

仅在射线与体积相交的区间内行进（平面裁剪、球体相交、AABB 裁剪）。

**效果**：对于占据屏幕一小部分的体积，许多光线可以完全跳过行进。性能改进取决于卷的屏幕覆盖面积。

### 6. 密度阈值跳过

当密度低于阈值时跳过照明计算（照明通常是最昂贵的部分）：```glsl
if (den > 0.01) { /* compute lighting and compositing */ }
```**效果**：光照计算（尤其是二次体积阴影行进）是最耗时的部分。跳过低密度区域的照明可以节省大量计算量。

### 7. 最小阴影步数

体积自阴影步数可以远少于主循环（6-16 步就足够了），并增加步长以覆盖更远的距离。

**原因**：人眼对阴影细节的敏感度低于对形状细节的敏感度。 6 个步长增加 1.3 倍，可以覆盖大约 20 个单位的距离。

### 8. 时间重投影

将前一帧的结果重新投影到当前帧进行混合，从而大大减少每帧所需的行进步骤。

**典型配置**：仅使用 12 步 + 95% 历史帧混合（`mix(oldColor, newColor, 0.05)`）即可产生远远超过 12 步单帧渲染的质量。

**注意事项**：
- 需要额外的缓冲区来存储历史帧
- 快速运动可能会导致重影
- 需要对相机移动进行正确的重投影矩阵处理

## 组合建议

### 1.SDF地形+体积云

使用 SDF 射线行进渲染地面/山脉，然后使用体积行进渲染上方的云层。两者通过深度值相互遮挡。

**实施要点**：
- 首先渲染SDF地形，记录命中深度
- 在体积行进期间，停在深度值处（地面遮挡云）
- 如果射线在到达地面之前穿过云层，则在云层间隔内行进并终止于地面

### 2.体积雾+场景照明

在现有的 SDF/多边形场景上叠加体积雾，将“颜色 = 颜色 * 透射率 + 散射光”应用于已渲染的场景。

**实施要点**：
- 渲染场景后，沿着每个像素的光线行进雾
- 累积雾散射和透过率
- 最终颜色=场景颜色×透过率+雾散射光

### 3.多层卷

不同的高度或区域使用不同的密度函数（例如高空积云+低空雾层），各自独立行进然后合成。

**实施要点**：
- 每层都有自己的边界和密度函数
- 可以在同一个行进循环中处理（检查当前点位于哪一层），或单独行进然后合成
- 单独行进更灵活，但需要正确的层间遮挡处理

### 4.粒子系统+体积

粒子提供宏观尺度的运动和形状；体积渲染为粒子添加内部细节和照明。

### 5. 后处理光轴（上帝光线）

体积渲染后，使用径向模糊或屏幕空间光线行进添加光轴效果以增强体积定义。

**实施要点**：
- 在屏幕空间中，从太阳位置径向向外采样，累积亮度
- 或者对于每个像素，沿着光源方向行进一小段距离，采样遮挡深度
- 光轴强度乘以光方向和视角方向的点积来控制可见角度

### 6. 程序天空 + 体积云

首先渲染程序天空/大气散射作为背景，然后在顶部覆盖体积云。两者之间的过渡是通过距离雾实现自然混合的。

**实施要点**：
- 使用大气散射模型（变体 2）或简化的天空梯度模型
- 在体积行进循环中应用距离雾：`mix(litCol, bgCol, 1.0 - exp(-0.003 * t * t))`
- 远处的云朵自然地融入天空的颜色，避免了突然的边界