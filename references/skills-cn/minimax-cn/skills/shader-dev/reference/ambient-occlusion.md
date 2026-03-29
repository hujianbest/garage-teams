# SDF 环境光遮挡 — 详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含完整的分步教程、数学推导、变体分析和高级用法。

## 先决条件

- GLSL基本语法（统一、变化、函数定义）
- **有符号距离场 (SDF)** 概念：`map(p)` 返回从点 p 到最近表面的距离
- **射线行进**基本循环：沿着射线行进以找到表面交叉点
- **表面法线计算**：通过SDF梯度（有限差分）获取法线方向
- 向量数学基础：点积、归一化、向量加法/减法

## 核心原则详细信息

SDF环境光遮挡的核心思想：**沿表面法线在多个距离处对SDF进行采样，并将“预期距离”与“实际距离”进行比较，以估计遮挡程度。**

对于具有法线 N 的曲面上距离 h 处的点 P：
- **预期距离** = h（如果周围环境完全开放，SDF值应等于到表面的距离）
- **实际距离** = 地图(P + N × h) (真实SDF值)
- **遮挡贡献** = h - map(P + N × h) （差异越大，附近的几何体越被遮挡）

最终结果是来自多个样本点的遮挡贡献的加权和，产生 [0, 1] 遮挡因子：
- 1.0 = 无遮挡（明亮）
- 0.0 = 完全遮挡（暗角）

关键数学公式（加法累加形式）：```
AO = 1 - k × Σ(weight_i × max(0, h_i - map(P + N × h_i)))
```其中“weight_i”通常呈指数或几何衰减（更接近的样本具有更高的权重），“k”是全局强度系数。

## 详细实施步骤

### 第 1 步：构建基础 SDF 场景

**什么**：定义一个“map()”函数，返回空间中任意点的有符号距离值。

**为什么**：AO计算完全依赖于SDF查询，因此首先需要一个工作距离字段。```glsl
float map(vec3 p) {
    float d = p.y; // Ground plane
    d = min(d, length(p - vec3(0.0, 1.0, 0.0)) - 1.0); // Sphere
    d = min(d, length(vec2(length(p.xz) - 1.5, p.y - 0.5)) - 0.4); // Torus
    return d;
}
```### 步骤 2：计算表面法线

**什么**：通过 SDF 梯度的有限差分近似计算法线方向。

**为什么**：AO采样探头沿法线方向向外；法线决定采样方向。```glsl
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}
```### 步骤 3：实施经典法向 AO（加法累加）

**什么**：沿法线方向在 5 个距离处对 SDF 进行采样，累积遮挡。

**为什么**：这是一个经典方法——最简洁、最高效的 SDF-AO 实现。 5 个样品在质量和性能之间取得了出色的平衡。权重以 0.95 呈指数衰减，使更接近的样本产生更大的影响（近表面遮挡在感知上更重要）。```glsl
// Classic AO
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0; // Initial weight
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0; // Sample distance: 0.01 ~ 0.13
        float d = map(pos + h * nor);             // Actual SDF distance
        occ += (h - d) * sca;                     // Accumulate (expected - actual) × weight
        sca *= 0.95;                              // Weight decay
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```### 步骤 4：将 AO 应用于照明

**什么**：将 AO 因子乘以环境光和间接光分量。

**为什么**：AO 模拟间接光被遮挡的程度。从物理上讲，它应该只影响环境/间接光，而不影响直接光源的漫反射和镜面反射（直接光遮挡由阴影处理）。然而，在实践中，AO 通常会乘以所有照明以获得更强的视觉效果。```glsl
float ao = calcAO(pos, nor);

// Method A: Affect only ambient light (physically correct)
vec3 ambient = vec3(0.2, 0.3, 0.5) * ao;
vec3 color = diffuse * shadow + ambient;

// Method B: Affect all lighting (stronger visual effect)
vec3 color = (diffuse * shadow + ambient) * ao;

// Method C: Combined with sky visibility bias
float skyVis = 0.5 + 0.5 * nor.y; // Upward-facing surfaces are brighter
vec3 color = diffuse * shadow + ambient * ao * skyVis;
```### 步骤 5：Raymarching 主循环集成

**内容**：将 AO 集成到完整的光线行进管道中。

**为什么**：AO 是光照计算的一部分，需要在撞击表面之后但最终输出之前进行计算。```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // ... camera setup, ray generation ...

    // Raymarching loop
    float t = 0.0;
    for (int i = 0; i < 128; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < 0.001) break;
        t += d;
        if (t > 100.0) break;
    }

    // Compute lighting on hit
    vec3 col = vec3(0.0);
    if (t < 100.0) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);
        float ao = calcAO(pos, nor);

        // Lighting
        vec3 lig = normalize(vec3(1.0, 0.8, -0.6));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        float sky = 0.5 + 0.5 * nor.y;
        col = vec3(1.0) * dif + vec3(0.2, 0.3, 0.5) * sky * ao;
    }

    fragColor = vec4(col, 1.0);
}
```## 变体详细信息

### 变体 1：乘法 AO

**与基础版本的区别**：从 1.0 开始，逐渐向下相乘，而不是使用累加然后反转。乘法形式自然地保证结果保持在 [0, 1] 范围内，避免了钳位的需要，并为多个重叠遮挡提供了更自然的衰减。

**来源**：乘法累加方法```glsl
// Multiplicative AO
float calcAO_multiplicative(vec3 pos, vec3 nor) {
    float ao = 1.0;
    float dist = 0.0;
    for (int i = 0; i <= 5; i++) {
        dist += 0.1; // Uniform step of 0.1
        float d = map(pos + nor * dist);
        ao *= 1.0 - max(0.0, (dist - d) * 0.2 / dist);
    }
    return ao;
}
```### 变体 2：多尺度 AO

**与基础版本的区别**：以指数方式增加采样距离（0.1、0.2、0.4、0.8、1.6、3.2、6.4），分别计算短程和长程遮挡。短程 AO 揭示接触阴影和表面细节；远距离 AO 揭示了大规模的环境遮挡。完全展开，无循环，使其具有 GPU 效率。

**来源**：多尺度抽样方法```glsl
// Multi-scale AO
float calcAO_multiscale(vec3 pos, vec3 nor) {
    // Short-range AO (contact shadows)
    float aoS = 1.0;
    aoS *= clamp(map(pos + nor * 0.1) * 10.0, 0.0, 1.0);  // Adjustable: distance 0.1, weight 10.0
    aoS *= clamp(map(pos + nor * 0.2) * 5.0,  0.0, 1.0);  // Adjustable: distance 0.2, weight 5.0
    aoS *= clamp(map(pos + nor * 0.4) * 2.5,  0.0, 1.0);  // Adjustable: distance 0.4, weight 2.5
    aoS *= clamp(map(pos + nor * 0.8) * 1.25, 0.0, 1.0);  // Adjustable: distance 0.8, weight 1.25

    // Long-range AO (large-scale occlusion)
    float ao = aoS;
    ao *= clamp(map(pos + nor * 1.6) * 0.625,  0.0, 1.0); // Adjustable: distance 1.6
    ao *= clamp(map(pos + nor * 3.2) * 0.3125, 0.0, 1.0); // Adjustable: distance 3.2
    ao *= clamp(map(pos + nor * 6.4) * 0.15625,0.0, 1.0);  // Adjustable: distance 6.4

    return max(0.035, pow(ao, 0.3)); // pow compresses dynamic range, min prevents total black
}
```### 变体 3：抖动采样 AO

**与基本版本的差异**：在统一样本位置之上添加基于哈希的抖动，打破由固定样本间距引起的条带伪影。还使用“1/(1+l)”距离衰减权重，因此较远的样本影响较小。

**来源**：抖动采样方法```glsl
// Jittered sampling AO
float hash(float n) { return fract(sin(n) * 43758.5453); }

float calcAO_jittered(vec3 pos, vec3 nor, float maxDist) {
    float ao = 0.0;
    const float nbIte = 6.0;          // Adjustable: number of samples
    for (float i = 1.0; i < nbIte + 0.5; i++) {
        float l = (i + hash(i)) * 0.5 / nbIte * maxDist; // Jittered sample position
        ao += (l - map(pos + nor * l)) / (1.0 + l);       // Distance-decay weight
    }
    return clamp(1.0 - ao / nbIte, 0.0, 1.0);
}
// Usage example: calcAO_jittered(pos, nor, 4.0)
```### 变体 4：半球形随机方向 AO

**与基础版本的区别**：不是仅沿法线方向采样，而是在法线半球内生成多个随机方向。更接近环境光遮挡的真实物理模型（光线从半球各个方向到达），但需要更多样本（通常为 32 个）才能获得平滑结果。

**来源**：半球随机方向方法```glsl
// Hemispherical random direction AO
vec2 hash2(float n) {
    return fract(sin(vec2(n, n + 1.0)) * vec2(43758.5453, 22578.1459));
}

float calcAO_hemisphere(vec3 pos, vec3 nor, float seed) {
    float occ = 0.0;
    for (int i = 0; i < 32; i++) {                              // Adjustable: sample count (16~64)
        float h = 0.01 + 4.0 * pow(float(i) / 31.0, 2.0);      // Quadratic distribution biased toward near-field
        vec2 an = hash2(seed + float(i) * 13.1) * vec2(3.14159, 6.2831); // Random spherical coordinates
        vec3 dir = vec3(sin(an.x) * sin(an.y), sin(an.x) * cos(an.y), cos(an.x));
        dir *= sign(dot(dir, nor));                               // Flip to normal hemisphere
        occ += clamp(5.0 * map(pos + h * dir) / h, -1.0, 1.0); // Signed occlusion
    }
    return clamp(occ / 32.0, 0.0, 1.0);
}
```### 变体 5：斐波那契球均匀半球 AO

**与基础版本的区别**：使用斐波那契球点而不是随机方向，实现准均匀的半球采样分布。避免纯随机抽样的聚类问题，在相同的样本数量下产生更高的质量。还可以与单独的方向遮挡功能（例如 SSS/软阴影）配对，以实现多级遮挡。

**来源**：斐波那契球采样方法```glsl
// Fibonacci sphere sampling AO
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
    for (int i = 0; i < 32; i++) {                         // Adjustable: sample count
        vec3 ap = forwardSF(float(i), 32.0);
        float h = hash1(float(i));
        ap *= sign(dot(ap, nor)) * h * 0.1;                // Flip to hemisphere + random scale
        ao += clamp(map(pos + nor * 0.01 + ap) * 3.0, 0.0, 1.0);
    }
    ao /= 32.0;
    return clamp(ao * 6.0, 0.0, 1.0);
}
```## 性能优化详情

### 瓶颈分析

SDF-AO 的性能瓶颈几乎完全在于 **SDF 样本计数** - 每个“map()”调用都是全场景距离计算。对于复杂的场景，这可能非常昂贵。

### 优化技术

#### 1. 减少样本数量

经典的法向 AO 只需 3~5 个样本即可达到可接受的质量。半球采样在物理上更正确，但需要16~32个样本；在性能预算允许的情况下使用它。

#### 2.提前退出优化

当累积的遮挡已经足够大时，尽早退出循环，避免不必要的 SDF 计算。```glsl
if (occ > 0.35) break; // Early exit when heavily occluded
```#### 3.展开循环

对于固定样本数（尤其是 4~7），手动展开循环可以避免分支开销并且对 GPU 友好。多尺度 AO 变体完全展开 7 个样本。

#### 4. 简化远处物体的 AO

远离相机的物体可以使用较少的 AO 样本或完全跳过 AO。```glsl
float aoSteps = mix(5.0, 2.0, clamp(t / 50.0, 0.0, 1.0));
```#### 5. 预编译开关

使用“#ifdef”在调试或低性能模式下禁用 AO。```glsl
#ifdef ENABLE_AMBIENT_OCCLUSION
    float ao = calcAO(pos, nor);
#else
    float ao = 1.0;
#endif
```#### 6.手绘伪AO混合

对于静态或半静态场景，可以预先计算伪 AO 值（基于材质 ID 或位置）并与实时 AO 混合，以减少运行时计算。```glsl
float focc = /* preset occlusion based on material */;
float finalAO = calcAO(pos, nor) * focc;
```#### 7.SDF 简化

简化版本的“map()”（忽略小细节）可用于 AO 采样，因为 AO 本质上是低频信息。

## 详细组合建议

### 1.AO + 软阴影

最常见的组合。 AO 处理间接光遮挡（角落、缝隙）；柔和的阴影处理直接光遮挡。只需将两者相乘即可：```glsl
float sha = calcShadow(pos, lightDir, 0.02, 20.0, 8.0);
float ao = calcAO(pos, nor);
col = diffuse * sha + ambient * ao; // Each handles its own domain
// Or more simply:
col = lighting * sha * ao;
```### 2. AO + 天空能见度

使用法线的 y 分量来估计朝上的程度，乘以 AO 来模拟天空光遮挡：```glsl
float skyVis = 0.5 + 0.5 * nor.y;
col += skyColor * ao * skyVis;
```### 3. AO + 次表面散射/反射光

AO 可以调制反射光和 SSS 强度（遮挡区域也不会接收反射光）：```glsl
float bou = clamp(-nor.y, 0.0, 1.0); // Downward-facing surfaces receive ground bounce
col += bounceColor * bou * ao;
col += sssColor * sss * (0.05 + 0.95 * ao); // SSS also modulated by AO
```### 4. AO + 凸度/角点检测

相同的 SDF 探测环路可以向外 (+N) 和向内 (-N) 采样，分别产生 AO 和凸度信息，对于边缘高光或磨损效果非常有用：```glsl
vec2 aoAndCorner = getOcclusion(pos, nor); // .x = AO, .y = convexity
col *= aoAndCorner.x;                       // AO darkening
col = mix(col, edgeColor, aoAndCorner.y);   // Convexity coloring
```### 5. AO + 菲涅尔环境反射

AO还应该调制环境反射项；否则凹面区域会表现出不自然的明亮环境反射：```glsl
float fre = pow(1.0 - max(dot(rd, nor), 0.0), 5.0);
col += envColor * fre * ao; // Reduce environment reflection in occluded areas
```
