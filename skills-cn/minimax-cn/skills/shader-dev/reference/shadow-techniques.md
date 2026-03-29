# SDF 软阴影技术 - 详细参考

本文档是对[SKILL.md](SKILL.md)的完整补充，涵盖必备知识、分步详细解释、数学推导、变体描述以及组合的完整代码示例。

## 用例

- **SDF 光线行进场景中的阴影计算**：当使用有符号距离场 (SDF) 进行光线行进渲染时，需要向场景添加软阴影效果
- **实时软阴影/半影效果**：模拟真实光源区域产生的半影渐变，而不是简单的硬阴影二值结果
- **地形/高度场阴影**：程序地形和高度图的阴影计算
- **多层阴影合成**：将地面阴影、植被阴影、云阴影和其他阴影源组合成最终结果
- **体积光/上帝射线效果**：重用阴影函数沿视图光线采样以生成体积光散射效果
- **分析阴影**：对球体等简单几何体使用 O(1) 分析阴影，而不是光线行进

## 先决条件

- **GLSL 基础**：uniforms、variations、内置函数（`clamp`、`mix`、`smoothstep`、`normalize`、`dot`、`reflect`）
- **Raymarching**：了解 SDF 场景表示和基本球体追踪工作流程
- **SDF 基础知识**：了解有符号距离场 — `map(p)` 返回从点 p 到最近表面的距离
- **基本照明模型**：漫反射 (N·L)、镜面反射 (Blinn-Phong)、环境光
- **向量数学**：点积、叉积、向量归一化、射线参数方程 `ro + rd * t`

## 核心原则详细信息

SDF软阴影的核心思想是：**从表面点向光源行进，利用“最近距离与行进距离”的比率来估计半影宽度**。

### 经典方程式 (2013)```
shadow = min(shadow, k * h / t)
```其中：
- `h` = 当前行军位置的 SDF 值（到最近表面的距离）
- `t` = 已经沿着阴影光线行进的距离
- `k` = 控制半影柔软度的常数（较大 = 较硬，较小 = 较软）

**几何直觉**：比率“h/t”近似于“从阴影射线上的当前点看到的最近遮挡物的角宽度”。当光线掠过物体表面时，h较小，t较大，使得h/t较小，产生半影区域；当光线远离所有物体时，`h/t`很大并且该区域被完全照亮。

沿光线的所有采样点取最小值“min(res, k*h/t)”会产生“最暗点”，这是最终的阴影因子。

### 改良配方 (2018)

经典公式会在锐利边缘附近产生过暗的伪像。改进版本使用相邻步骤的 SDF 值来执行几何三角测量，估计更准确的最近点：```
y = h² / (2 * ph)           // ph = SDF value from previous step
d = sqrt(h² - y²)           // true nearest distance perpendicular to ray direction
shadow = min(shadow, d / (w * max(0, t - y)))
```**数学推导**：假设光线位置“t-h_step”的前一步具有 SDF 值“ph”，位置“t”的当前步骤具有 SDF 值“h”。这两个 SDF 球体的相交区域（分别具有半径“ph”和“h”）提供了对最近表面点的更准确估计。通过简单的三角形几何：
- `y` 是从当前采样点到最近点投影沿射线后退的距离
- `d` 是最近表面点到射线的垂直距离
- 修正后的有效距离是“t - y”而不是“t”

### 负扩展 (2020)

允许 `res` 下降到负值（最小 -1），然后使用自定义平滑映射重新映射到 [0,1]：```
res = max(res, -1.0)
shadow = 0.25 * (1 + res)² * (2 - res)
```这消除了经典的“clamp(0,1)”产生的硬折痕，实现了更平滑的半影过渡。

**为什么有效**：经典方法由于夹紧而在“res=0”处产生 C0 连续（非平滑）折痕。通过让`res`进入负域[-1, 0]，然后用C1连续函数`0.25*(1+res)²*(2-res)`重新映射，得到完全平滑的半影梯度。该函数在“res=-1”时计算为 0，在“res=1”时计算为 1，两端具有平滑的导数转换。

## 详细实施步骤

### 第 1 步：场景 SDF 定义

**什么**：定义场景的有符号距离函数，返回空间中任意点到最近表面的距离。

**为什么**：阴影光线行进需要“map(p)”查询来确定步长和半影估计。```glsl
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdPlane(vec3 p) {
    return p.y;
}

float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

float map(vec3 p) {
    float d = sdPlane(p);
    d = min(d, sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5));
    d = min(d, sdRoundBox(p - vec3(-1.2, 0.3, 0.5), vec3(0.3), 0.05));
    return d;
}
```### 步骤2：经典软阴影功能

**什么**：从表面点向光源行进，逐渐累积最小“k*h/t”比率作为阴影因子。

**为什么**：这是所有 SDF 软阴影的基础框架。在每个步骤中，“h/t”近似于该点处的遮挡角宽度；整个射线的最小值作为最终的半影估计。 k值控制半影柔软度。```glsl
// Classic SDF soft shadow
// ro: shadow ray origin (surface position)
// rd: light direction (normalized)
// mint: starting offset (to avoid self-shadowing)
// tmax: maximum march distance
float calcSoftShadow(vec3 ro, vec3 rd, float mint, float tmax) {
    float res = 1.0;
    float t = mint;

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        float s = clamp(SHADOW_K * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, MIN_STEP, MAX_STEP);    // Step size clamping
        if (res < 0.004 || t > tmax) break;    // Early exit
    }

    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);      // Smoothstep smoothing
}
```### 步骤 3：改进的软阴影（几何三角测量）

**内容**：使用当前步骤和先前步骤中的 SDF 值，通过几何三角测量来估计更准确的最近点位置，消除锐边附近的半影伪影。

**为什么**：经典的“h/t”公式假设最近的表面点位于当前样本位置的正下方，但实际的最近点可能位于两个台阶之间。使用来自两个相邻步骤的 SDF 球体的相交关系可以更准确地估计垂直距离“d”和沿射线的校正深度“t-y”。```glsl
// Improved SDF soft shadow
float calcSoftShadowImproved(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    float res = 1.0;
    float t = mint;
    float ph = 1e10;  // Previous step SDF value, initialized large so first step y≈0

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);

        // Geometric triangulation: estimate corrected nearest distance
        float y = h * h / (2.0 * ph);         // Step-back distance along ray
        float d = sqrt(h * h - y * y);         // True nearest distance perpendicular to ray
        res = min(res, d / (w * max(0.0, t - y)));

        ph = h;                                // Save current h for next step
        t += h;

        if (res < 0.0001 || t > tmax) break;
    }

    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res);
}
```### 步骤 4：负扩展版本（最平滑半影）

**什么**：允许阴影因子落入负范围 [-1, 0]，然后使用自定义二次平滑函数重新映射到 [0, 1]，消除硬折痕。

**为什么**：经典方法会在“clamp(0,1)”处产生 C0 连续（非平滑）折痕。通过允许“res”进入负域并使用 C1 连续函数“0.25*(1+res)²*(2-res)”重新映射，实现了完全平滑的半影梯度。```glsl
// Negative extension soft shadow
float calcSoftShadowSmooth(vec3 ro, vec3 rd, float mint, float tmax, float w) {
    float res = 1.0;
    float t = mint;

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        float h = map(ro + rd * t);
        res = min(res, h / (w * t));
        t += clamp(h, MIN_STEP, MAX_STEP);
        if (res < -1.0 || t > tmax) break;    // Allow res to drop to -1
    }

    res = max(res, -1.0);                      // Clamp to [-1, 1]
    return 0.25 * (1.0 + res) * (1.0 + res) * (2.0 - res);  // Smooth remapping
}
```### 步骤 5：边界体积优化

**什么**：在开始行军之前，使用简单的几何测试（平面裁剪或 AABB 射线相交）来缩小阴影射线的有效范围。

**为什么**：如果阴影光线不可能击中有界区域之外的任何物体（例如，场景上方是空的），则可以提前缩短“tmax”或立即返回 1.0，从而节省许多行进迭代。```glsl
// Method A: Plane clipping — clip ray to scene upper bound plane
float tp = (SCENE_Y_MAX - ro.y) / rd.y;
if (tp > 0.0) tmax = min(tmax, tp);

// Method B: AABB bounding box clipping
vec2 iBox(vec3 ro, vec3 rd, vec3 rad) {
    vec3 m = 1.0 / rd;
    vec3 n = m * ro;
    vec3 k = abs(m) * rad;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF < 0.0) return vec2(-1.0);
    return vec2(tN, tF);
}

// Usage in shadow function
vec2 dis = iBox(ro, rd, BOUND_SIZE);
if (dis.y < 0.0) return 1.0;       // Ray completely misses bounding box
tmin = max(tmin, dis.x);
tmax = min(tmax, dis.y);
```### 第 6 步：阴影颜色渲染（渗色）

**什么**：不使用统一的标量阴影值，而是对 RGB 通道应用不同的阴影衰减曲线。

**原因**：在现实世界中，由于次表面散射和大气效应，半影区域表现出暖色变化 - 红光穿透最多，而蓝光首先被阻挡。通过对影子值应用每通道功率运算，可以以低成本来近似这种物理现象。```glsl
// Method A: Classic color shadow
// sha is a [0,1] shadow factor
vec3 shadowColor = vec3(sha, sha * sha * 0.5 + 0.5 * sha, sha * sha);
// R = sha (linear), G = softer quadratic blend, B = sha² (darkest)

// Method B: Per-channel power operation (Woods style)
vec3 shadowColor = pow(vec3(sha), vec3(1.0, 1.2, 1.5));
// R = sha^1.0, G = sha^1.2, B = sha^1.5 → penumbra region shifts warm
```### 步骤 7：集成到照明模型中

**什么**：将阴影值乘以漫反射和镜面反射照明的贡献。

**为什么**：阴影本质上是“光源可见性”的估计，并且应该充当依赖于该光源的所有照明项的乘法因子。通常仅当 N·L > 0（表面面向光）时才计算阴影，以避免在背光面上浪费 GPU 周期。```glsl
// Lighting integration
vec3 sunDir = normalize(vec3(-0.5, 0.4, -0.6));
vec3 hal = normalize(sunDir - rd);

// Diffuse × shadow
float dif = clamp(dot(nor, sunDir), 0.0, 1.0);
if (dif > 0.0001)
    dif *= calcSoftShadow(pos + nor * 0.01, sunDir, 0.02, 8.0);

// Specular is also modulated by shadow
float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0);
spe *= dif;  // dif already includes shadow

// Final color compositing
vec3 col = vec3(0.0);
col += albedo * 2.0 * dif * vec3(1.0, 0.9, 0.8);       // Sun diffuse
col += 5.0 * spe * vec3(1.0, 0.9, 0.8);                 // Sun specular
col += albedo * 0.5 * clamp(0.5 + 0.5 * nor.y, 0.0, 1.0)
     * vec3(0.4, 0.6, 1.0);                              // Sky ambient (no shadow)
```## 变体详细信息

### 变体 1：分析球体阴影

**与基础版本的区别**：不使用光线行进；相反，对球体执行 O(1) 解析最近距离计算。适用于仅包含球体或可以用球体近似的物体的场景。

**原理**：对于射线和球体，可以解析计算射线到球体表面的最近距离以及沿射线最近点处的参数“t”。这两个值直接形成“d/t”比率，无需迭代前进。```glsl
// Sphere analytical soft shadow
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    return vec2(d, -b - sqrt(max(h, 0.0)));
}

float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph, float k) {
    vec2 r = sphDistances(ro, rd, sph);
    if (r.y > 0.0)
        return clamp(k * max(r.x, 0.0) / r.y, 0.0, 1.0);
    return 1.0;
}
// Multi-sphere aggregation: res = min(res, sphSoftShadow(ro, rd, sphere[i], k))
```### 变体 2：地形高度场阴影

**与基础版本的区别**：`h` 不是从通用 SDF `map()` 获得的，而是计算为 `p.y -terrain(p.xz)`，即射线和地形之间的高度差。步长适应相机距离。

**用例**：程序地形渲染（使用 FBM 噪声生成的高度图）。地形SDF很难精确定义，但高度差可以作为近似距离估计。```glsl
float terrainShadow(vec3 ro, vec3 rd, float dis) {
    float minStep = clamp(dis * 0.01, 0.5, 50.0);  // Distance-adaptive minimum step
    float res = 1.0;
    float t = 0.01;
    for (int i = 0; i < 80; i++) {                  // Terrain needs more iterations
        vec3 p = ro + t * rd;
        float h = p.y - terrainMap(p.xz);           // Height difference replaces SDF
        res = min(res, 16.0 * h / t);               // k=16
        t += max(minStep, h);
        if (res < 0.001 || p.y > MAX_TERRAIN_HEIGHT) break;
    }
    return clamp(res, 0.0, 1.0);
}
```### 变体 3：每种材料的硬/软混合

**与基础版本的区别**：使用全局变量或额外参数来控制每个对象的阴影硬度，通过“mix(1.0, k*h/t, Hardness)”进行混合。当“hardness=0”时，产生硬阴影；当“hardness=1”时，完全柔和的阴影。

**用例**：角色需要锐利的硬阴影（以增强轮廓），而环境对象使用较柔和的阴影。```glsl
float hsha = 1.0;  // Global variable, set per material in map()

float mapWithShadowHardness(vec3 p) {
    float d = sdPlane(p);
    hsha = 1.0;  // Ground: fully soft shadow
    float dChar = sdCharacter(p);
    if (dChar < d) { d = dChar; hsha = 0.0; }  // Character: hard shadow
    return d;
}

// Inside shadow loop:
res = min(res, mix(1.0, SHADOW_K * h / t, hsha));
```### 变体 4：多层阴影合成

**与基础版本的区别**：不同类型的遮挡源分别计算，然后乘法组合。典型场景：地面阴影×植被阴影×云影。

**设计原理**：不同的阴影源具有截然不同的特性——地形阴影需要高精度行进，植被阴影可以使用概率/密度场近似，云阴影是大比例平面投影。分层计算允许对每种类型使用最佳算法。```glsl
// Layered computation
float sha_terrain = terrainShadow(pos, sunDir, 0.02);
float sha_trees   = treesShadow(pos, sunDir);
float sha_clouds  = cloudShadow(pos, sunDir);  // Single planar projection + FBM sample

// Multiplicative composition
float sha = sha_terrain * sha_trees;
sha *= smoothstep(-0.3, -0.1, sha_clouds);  // Cloud shadow softened with smoothstep

// Apply to lighting
dif *= sha;
```### 变体 5：体积光/God Ray 重用阴影函数

**与基础版本的区别**：沿着视线方向均匀行进，每一步都向光线调用阴影函数，积累光线能量。本质上是对阴影函数进行二次采样，以产生体积散射效果。

**原理**：体积光效果来自空气中颗粒对光的散射。在沿着视图光线的每个点，如果该点被太阳照亮（高阴影值），它就会为最终颜色贡献一些散射光。将沿视图光线的所有采样点的照明贡献相加即可产生体积光效果。```glsl
// Volumetric light (God Rays)
float godRays(vec3 ro, vec3 rd, float tmax, vec3 sunDir) {
    float v = 0.0;
    float dt = 0.15;                                 // View ray step size
    float t = dt * fract(texelFetch(iChannel0, ivec2(fragCoord) & 255, 0).x); // Jittering
    for (int i = 0; i < 32; i++) {                   // Number of samples
        if (t > tmax) break;
        vec3 p = ro + rd * t;
        float sha = calcSoftShadow(p, sunDir, 0.02, 8.0); // Reuse shadow function
        v += sha * exp(-0.2 * t);                    // Exponential distance falloff
        t += dt;
    }
    v /= 32.0;
    return v * v;                                    // Square to enhance contrast
}
// Usage: col += godRayIntensity * godRays(...) * vec3(1.0, 0.75, 0.4);
```## 性能优化详情

### 瓶颈分析

SDF 软阴影的主要成本是**每个像素的阴影光线行进**，其中涉及多个“map()”调用。对于复杂场景，单个“map()”调用可能包含数十个 SDF 组合操作。

### 优化技术

#### 1. 边界体积剔除（最重要）

- 平面裁剪：`tmax = min(tmax, (yMax - ro.y) / rd.y)` 将光线限制在场景高度范围内
- AABB 裁剪：使用 `iBox()` 将 `tmin`/`tmax` 限制在边界框内；当光线完全错过时立即返回 1.0
- 可以减少 30-70% 的浪费迭代

#### 2. 步长钳位

-`t+=clamp(h, minStep, maxStep)`防止极小的步骤（卡在表面附近）和极大的步骤（跳过薄物体）
- 典型的“minStep”值：0.005~0.05，“maxStep”：0.2~0.5
- 距离自适应：`minStep = Clip(dis * 0.01, 0.5, 50.0)` 对远处的阴影使用更大的步长

#### 3.提前退出

- 经典版本：`res < 0.004`已经足够暗了，不需要继续
- 负扩展：`res < -1.0` 已饱和
- 高度上限：`pos.y > yMax` 表示光线已离开场景

#### 4. 降低阴影 SDF 精度

- 使用简化的“map2()”，省略材质计算并仅返回距离
- 对于地形场景，使用低分辨率 `terrainM()` （较少的 FBM 八度）而不是全精度 `terrainH()`

#### 5.条件计算

- `if (dif > 0.0001) diff *= Shadow(...)` 仅计算面向光时的阴影
- 背光面直接为0，不需要阴影

#### 6.迭代次数调整

- 简单场景（一些基元）：16~32次迭代就足够了
- 复杂的FBM表面：需要64~128次迭代
- 地形场景：具有距离自适应步长，大约 80 次迭代

#### 7. 循环展开控制

- `#define ZERO (min(iFrame,0))` 防止编译器在编译时展开循环，减少指令缓存压力

## 带有完整代码的组合建议

### 使用环境光遮挡 (AO)

阴影处理直接光遮挡； AO 处理间接光遮挡。它们相辅相成：```glsl
float sha = calcSoftShadow(pos, sunDir, 0.02, 8.0);
float occ = calcAO(pos, nor);
col += albedo * dif * sha * sunColor;       // Direct light × shadow
col += albedo * sky * occ * skyColor;       // Ambient light × AO
```### 使用次表面散射 (SSS)

阴影值可以调制 SSS 强度，模拟阴影边缘的半透明透光效果：```glsl
float sss = pow(clamp(dot(rd, sunDir), 0.0, 1.0), 4.0);
sss *= 0.25 + 0.75 * sha;  // SSS reduced but not eliminated in shadow
col += albedo * sss * vec3(1.0, 0.4, 0.2);
```### 有雾/大气散射

阴影应该被远处的雾“冲掉”。常见的做法是在应用雾之前完成阴影照明，这样会自然地混合：```glsl
// First complete lighting with shadows
vec3 col = albedo * lighting_with_shadow;
// Then apply fog (distance fog naturally weakens shadow contrast)
col = mix(col, fogColor, 1.0 - exp(-0.001 * t * t));
```### 使用法线贴图/凹凸贴图

阴影使用几何法线（不是扰动法线）来计算 N·L 来确定面向光的方向，但阴影光线仍然从实际表面点投射。法线贴图仅影响光照计算，不影响阴影：```glsl
vec3 geoNor = calcNormal(pos);              // Geometric normal
vec3 nor = perturbNormal(geoNor, ...);      // Perturbed normal
float dif = clamp(dot(nor, sunDir), 0.0, 1.0);  // Use perturbed normal for diffuse
if (dot(geoNor, sunDir) > 0.0)                    // Use geometric normal to decide shadow
    dif *= calcSoftShadow(pos + geoNor * 0.01, sunDir, 0.02, 8.0);
```### 带有思考

阴影函数可以重复用于反射方向，遮挡不应该可见的镜面高光：```glsl
vec3 ref = reflect(rd, nor);
float refSha = calcSoftShadow(pos + nor * 0.01, ref, 0.02, 8.0);
col += specular * envColor * refSha * occ;
```
