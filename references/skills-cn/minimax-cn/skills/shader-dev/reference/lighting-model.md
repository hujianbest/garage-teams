# 光照模型详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充参考，涵盖必备知识、每一步的深入讲解、变体的完整描述、性能优化分析以及组合建议的完整代码示例。

---

## 先决条件

### 向量数学基础知识
- **点积**：`dot(A, B) = |A||B|cos(θ)`，用于计算两个向量之间的角度关系。光照模型大量使用点积，例如 N·L、N·V、N·H、V·H
- **叉积**：`cross(A, B)`返回垂直于A和B的向量，用于构建相机坐标系和切线空间
- **归一化**：将向量缩放到单位长度；光照计算需要对所有方向向量进行归一化
- **reflect**: `reflect(I, N) = I - 2.0 * dot(N, I) * N`，计算入射向量 I 关于法线 N 的反射

### GLSL 基础知识
- **统一/变化**：统一是全局常量（例如，iTime、iResolution）；变量从顶点插值到片段
- **关键内置功能**：
  - `clamp(x, min, max)` — 钳位到范围
  - `mix(a, b, t)` — 线性插值 `a*(1-t) + b*t`
  - `pow(base, exp)` — 求幂，用于镜面反射衰减
  - `exp(x)` / `exp2(x)` — 指数函数，用于衰减和比尔定律
  - `smoothstep(edge0, edge1, x)` — Hermite 平滑插值

### 基本计算机图形概念
- **法线 (N)**：从表面向外指向的单位矢量，确定照明强度
- **视图方向 (V)**：从表面点到相机的单位向量
- **光方向 (L)**：从表面点到光源的单位向量
- **Half Vector (H)**：`normalize(V + L)`，Blinn-Phong模型的核心
- **反射向量 (R)**：`reflect(-L, N)`，用于经典的 Phong 模型

### Raymarching 基础知识（推荐）
- **SDF（有符号距离函数）**：返回从点到最近表面的有符号距离
- **法线计算（有限差分）**：通过计算 SDF 沿 x、y 和 z 轴的小偏移差来近似梯度（即法线方向）
- **行进**：沿射线方向前进 SDF 返回的距离，直到击中表面或超出范围

---

## 详细实施步骤

### 第 1 步：场景基础（UV、相机、光线行进）

**内容**：建立标准ShaderToy框架——UV坐标、相机光线、SDF场景、法线计算。

**为什么**：光照计算需要法线 N、视图方向 V 和光线方向 L 作为输入，所有这些都取决于场景几何形状。如果没有正确的法线和方向向量，任何照明模型都无法工作。

**详情**：
- UV 坐标通常标准化为“(2.0 * fragCoord - iResolution.xy) / iResolution.y”，以确保正确的纵横比
- 相机使用观察矩阵：向前方向“ww”，向右方向“uu”，向上方向“vv”
- SDF法线使用六点中心差分，比前向差分更准确
- `e = vec2(0.001, 0.0)` 中的 epsilon 值影响正常精度：太大会模糊细节，太小会引入噪声

**代码**：```glsl
// Compute normal from SDF scene (finite differences) — standard technique
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// Prepare basic vectors needed for lighting
vec3 N = calcNormal(pos);           // Surface normal
vec3 V = -rd;                        // View direction (reverse of ray)
vec3 L = normalize(lightPos - pos);  // Light direction (point light)
// Or directional light: vec3 L = normalize(vec3(0.6, 0.8, -0.5));
```### 步骤 2：兰伯特漫反射

**内容**：计算基本漫射照明——所有照明模型的基础。

**原因**：兰伯特定律描述了粗糙表面的理想漫射行为 - 亮度与 cos（入射角）成正比。这是最基本的基于物理的照明模型，假设光线进入表面并均匀散射。

**详情**：
- `max(0.0, dot(N, L))` 使用 `max(0,...)` 来避免负值（背面照明）
- 节能朗伯漫射需要除以 PI，因为朗伯 BRDF = 反照率/PI 且积分辐照度 = PI * L_incoming
- Half-Lambert (`NdotL * 0.5 + 0.5`) 是 Valve 发明的一项技术，将 [-1,1] 映射到 [0,1]，为背光区域提供一些亮度；常用于角色渲染和SSS近似
- 许多海洋着色器使用类似的包裹漫反射图案

**代码**：```glsl
// Basic Lambert diffuse
float NdotL = max(0.0, dot(N, L));
vec3 diffuse = albedo * lightColor * NdotL;

// Energy-conserving version (albedo/PI)
vec3 diffuse_conserved = albedo / PI * lightColor * NdotL;

// Half-Lambert variant (wrapped dot product)
// Reduces over-darkening on backlit faces, commonly used for SSS approximation
float halfLambert = NdotL * 0.5 + 0.5;
vec3 diffuse_wrapped = albedo * lightColor * halfLambert;
```### 步骤 3：Blinn-Phong 镜面反射

**什么**：根据半向量添加镜面高光。

**为什么**：Blinn-Phong 比经典的 Phong 计算效率更高，物理上也更合理。半向量H是V和L的平均方向；当 H 与 N 对齐时，高光最亮。与 Phong 相比，Blinn-Phong 在掠射角上的表现也更真实。

**详情**：
- 半向量 H = Normalize(V + L)，这避免了 Phong 的 Reflect(-L, N) 所需的反射计算
- 光泽度控制高光浓度：4.0 给出非常粗糙的表面感觉，256.0 接近镜子
- 归一化因子“(光泽度 + 8.0) / (8.0 * PI)”确保改变光泽度时总反射能量保持恒定（能量守恒）
- 基于许多光线行进着色器中使用的标准半矢量方法

**代码**：```glsl
// Blinn-Phong specular (standard half vector method)
vec3 H = normalize(V + L);
float NdotH = max(0.0, dot(N, H));

// Empirical model: directly use shininess exponent
float SHININESS = 32.0;  // Adjustable: 4.0 (rough) ~ 256.0 (mirror-like)
float spec = pow(NdotH, SHININESS);

// With energy-conserving normalization factor
// Normalization factor (s+8)/(8*PI) ensures total energy is preserved when changing shininess
float normFactor = (SHININESS + 8.0) / (8.0 * PI);
float spec_normalized = normFactor * pow(NdotH, SHININESS);

vec3 specular = lightColor * spec_normalized;
```### 步骤 4：Fresnel-Schlick 近似

**内容**：根据视角计算反射率 - 反射率随掠射角度增加（“边缘增亮”效果）。

**原因**：所有真实材料在掠射角处的反射率都接近 100%。这是一种基本的物理现象（菲涅尔效应）。 Schlick 近似使用五次方曲线来模拟这一点，并且是所有 PBR 管道的核心组件。这是实时渲染中普遍存在的公式。

**详情**：
- F0 是法向入射时的反射率（直视表面）
- 电介质（塑料、水等）：F0约为0.02~0.04；大多数光是散射的（漫射的）
- 金属：F0 使用材质的基色，因为金属几乎没有漫反射
- `mix(vec3(0.04), baseColor, Metallic)` 是统一的金属工作流程，在电介质和金属之间进行插值
- 使用 V·H 表示 Cook-Torrance BRDF 镜面反射项
- 使用N·V进行环境反射、边缘照明等。
- 在实时和离线渲染管道中广泛使用的近似值。

**代码**：```glsl
// Fresnel-Schlick approximation (standard formulation)
vec3 fresnelSchlick(vec3 F0, float cosTheta) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// Dielectrics (plastic, water, etc.): F0 approximately 0.02~0.04
vec3 F0_dielectric = vec3(0.04);

// Metals: F0 uses the material's baseColor
vec3 F0_metal = baseColor;

// Unified metallic workflow
vec3 F0 = mix(vec3(0.04), baseColor, metallic);

// Compute Fresnel using V·H (for specular BRDF)
float VdotH = max(0.0, dot(V, H));
vec3 F = fresnelSchlick(F0, VdotH);

// Alternatively, compute Fresnel using N·V (for environment reflections, rim light)
// Optional: pow(fGloss, 20.0) factor for gloss adjustment
float NdotV = max(0.0, dot(N, V));
vec3 F_env = F0 + (1.0 - F0) * pow(1.0 - NdotV, 5.0);
```### 步骤 5：GGX 正态分布函数（D 项）

**什么**：计算与半向量对齐的微面法线的概率分布。

**为什么**：GGX (Trowbridge-Reitz) 分布具有更广泛的“长尾”亮点，比 Beckmann 分布更接近真实材料。这是 PBR 管道中的核心术语，决定高光形状和大小。这是跨 PBR 实现使用的标准 GGX 公式。

**详情**：
- 必须首先对粗糙度进行平方（`a = 粗糙度 * 粗糙度`）；这是迪士尼从感知粗糙度到阿尔法的映射
- `a2 = a * a` 是 GGX 公式中的 alpha^2 项
- 当粗糙度=0.0时，D接近δ函数（完美镜面）；当粗糙度=1.0时，接近均匀分布
- 分母“PI * denom * denom”确保分布函数在半球上积分为 1
- 跨 PBR 实现使用的标准 GGX 公式

**代码**：```glsl
// GGX/Trowbridge-Reitz normal distribution function (standard formulation)
float distributionGGX(float NdotH, float roughness) {
    float a = roughness * roughness;  // Note: roughness must be squared first!
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

// Roughness parameter guide:
// roughness = 0.0 → perfect mirror (D approaches delta function)
// roughness = 0.5 → medium roughness
// roughness = 1.0 → fully rough (D approaches uniform distribution)
```### 步骤 6：几何遮挡函数（G 项）

**什么**：计算微面之间的相互阴影和掩蔽。

**为什么**：并非所有正确定向的微面都可以同时被光线和视图“看到”——G 项纠正了这种遮挡损失。微面模型假设表面由无数微小的平面组成，这些平面可以相互遮挡（阴影和遮蔽）。

**详情**：
- Smith方法将G分解为两个独立的项，分别为光方向（G1_L）和视图方向（G1_V）
- **Schlick-GGX**：对于直接照明，`k = (粗糙度+1)^2 / 8`，对于 IBL，`k = 粗糙度^2 / 2`
- **高度相关的史密斯**：物理上更准确，考虑了微面的高度相关性；直接返回可见性项“G/(4*NdotV*NdotL)”
- **简化近似** (G1V)：最紧凑的实现，适合代码高尔夫或性能极其受限的场景
- 具有不同精度/性能权衡的三种常见实现

**代码**：```glsl
// Smith method: decompose G into two independent G1 terms for light and view directions

// Method 1: Schlick-GGX (separated implementation)
// The clearest pedagogical implementation
float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;  // For direct lighting: k = (r+1)^2/8
    return NdotV / (NdotV * (1.0 - k) + k);
}

float geometrySmith(float NdotV, float NdotL, float roughness) {
    float ggx1 = geometrySchlickGGX(NdotV, roughness);
    float ggx2 = geometrySchlickGGX(NdotL, roughness);
    return ggx1 * ggx2;
}

// Method 2: Height-Correlated Smith (visibility term form)
// More physically accurate, directly returns G/(4*NdotV*NdotL), i.e., the "visibility term"
float visibilitySmith(float NdotV, float NdotL, float roughness) {
    float a2 = roughness * roughness;
    float gv = NdotL * sqrt(NdotV * (NdotV - NdotV * a2) + a2);
    float gl = NdotV * sqrt(NdotL * (NdotL - NdotL * a2) + a2);
    return 0.5 / max(gv + gl, 0.00001);
}

// Method 3: Simplified approximation (compact G1V helper)
// Most compact implementation
float G1V(float dotNV, float k) {
    return 1.0 / (dotNV * (1.0 - k) + k);
}
// Usage: float vis = G1V(NdotL, k) * G1V(NdotV, k); where k = roughness/2
```### 步骤 7：组装 Cook-Torrance BRDF

**什么**：将 D、F 和 G 项组合成完整的镜面反射 BRDF。

**为什么**：Cook-Torrance 微面模型是目前实时渲染中使用最广泛的基于物理的镜面反射模型。它基于微面理论，将表面建模为无数微小的完美镜子。

**详情**：
- 完整公式：`f_specular = D * F * G / (4 * NdotV * NdotL)`
- 使用“visibilitySmith”（返回“G/(4*NdotV*NdotL)”）时，无需手动除以分母
- 使用标准 `geometrySmith` （返回 G）时，必须显式除以 `4 * NdotV * NdotL`
- `max(4.0 * NdotV * NdotL, 0.001)` 防止被零除
- 基于标准 Cook-Torrance BRDF 公式

**代码**：```glsl
// Complete Cook-Torrance BRDF assembly
// Standard Cook-Torrance BRDF assembly
vec3 cookTorranceBRDF(vec3 N, vec3 V, vec3 L, float roughness, vec3 F0) {
    vec3 H = normalize(V + L);

    float NdotL = max(0.0, dot(N, L));
    float NdotV = max(0.0, dot(N, V));
    float NdotH = max(0.0, dot(N, H));
    float VdotH = max(0.0, dot(V, H));

    // D: Normal distribution
    float D = distributionGGX(NdotH, roughness);

    // F: Fresnel
    vec3 F = fresnelSchlick(F0, VdotH);

    // G: Geometric occlusion (using visibility term form, which includes the 4*NdotV*NdotL denominator)
    float Vis = visibilitySmith(NdotV, NdotL, roughness);

    // Assembly (Vis version already divides by 4*NdotV*NdotL)
    vec3 specular = D * F * Vis;

    // Or using the standard G term form:
    // float G = geometrySmith(NdotV, NdotL, roughness);
    // vec3 specular = (D * F * G) / max(4.0 * NdotV * NdotL, 0.001);

    return specular * NdotL;
}
```### 步骤 8：多光累积和最终合成

**内容**：将漫反射和镜面反射与能量守恒混合在一起，并累积多个光源的贡献。

**为什么**：真实场景包含多个光源（太阳、天空、地面反射等）。漫反射和镜面反射之间必须保持能量守恒：已反射的能量 (F) 不应参与漫反射。

**详情**：
- `kD = (1.0 - F) * (1.0 - 金属)` 实现能量守恒：
  - `(1.0 - F)` 确保已经反射的光不参与漫反射
  - `(1.0 - 金属)`确保金属没有漫射（金属的自由电子吸收所有折射光）
- 天空光使用`0.5 + 0.5 * N.y`来近似半球积分——法线越向上，越亮
- 背光/边缘光使用来自太阳相反方向的包裹漫反射来提供填充照明
- 基于 PBR 光线行进着色器中常见的多光架构模式

**代码**：```glsl
// Complete multi-light PBR lighting accumulation
// Multi-light PBR architecture

vec3 shade(vec3 pos, vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 diffuseColor = albedo * (1.0 - metallic);  // Metals have no diffuse
    vec3 color = vec3(0.0);

    // --- Main light (sun) ---
    vec3 sunDir = normalize(vec3(0.6, 0.8, -0.5));
    vec3 sunColor = vec3(1.0, 0.95, 0.85) * 2.0;

    vec3 H = normalize(V + sunDir);
    float NdotL = max(0.0, dot(N, sunDir));
    float NdotV = max(0.0, dot(N, V));
    float VdotH = max(0.0, dot(V, H));

    vec3 F = fresnelSchlick(F0, VdotH);
    vec3 kD = (1.0 - F) * (1.0 - metallic);  // Energy conservation

    // Diffuse contribution
    color += kD * diffuseColor / PI * sunColor * NdotL;
    // Specular contribution
    color += cookTorranceBRDF(N, V, sunDir, roughness, F0) * sunColor;

    // --- Sky light (hemisphere light approximation) ---
    // Sky light (hemisphere light approximation)
    vec3 skyColor = vec3(0.2, 0.5, 1.0) * 0.3;
    float skyDiffuse = 0.5 + 0.5 * N.y;  // Simple hemisphere integration approximation
    color += diffuseColor * skyColor * skyDiffuse;

    // --- Back light / rim light ---
    // Back-light / fill light term
    vec3 backDir = normalize(vec3(-sunDir.x, 0.0, -sunDir.z));
    float backDiffuse = clamp(dot(N, backDir) * 0.5 + 0.5, 0.0, 1.0);
    color += diffuseColor * vec3(0.25, 0.15, 0.1) * backDiffuse;

    return color;
}
```### 步骤 9：环境光遮挡 (AO)

**内容**：近似减少由于几何遮挡而导致的表面缝隙中的间接照明。

**为什么**：没有 AO 的场景显得过于“平坦”并且缺乏空间深度。在光线行进场景中，SDF 可用于高效计算 AO——沿法线方向采样多个点，并将 SDF 距离与理想距离进行比较。

**详情**：
- 原理：沿着法线逐渐远离曲面，查询每个样本点的SDF值。如果 SDF 值小于采样距离 h，则存在附近的遮挡几何体
-`sca *= 0.95`逐渐减少更远的样本点的权重
- `3.0 * occ` 中的乘数控制 AO 强度（可调）
- AO 同时影响漫反射和镜面反射，但影响方式不同：
  - 漫反射：直接乘以 AO 值
  - 镜面反射：使用 `pow(NdotV + ao, roughness^2) - 1 + ao` 进行更细微的衰减
- 基于标准 SDF 环境光遮挡技术

**代码**：```glsl
// AO computation for raymarching scenes (standard SDF-based technique)
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0;
        float d = map(pos + h * nor);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}

// Using AO (AO affects both diffuse and specular)
float ao = calcAO(pos, N);
diffuseLight *= ao;
// More subtle specular AO:
specularLight *= clamp(pow(NdotV + ao, roughness * roughness) - 1.0 + ao, 0.0, 1.0);
```---

## 变体详细信息

### 变体 1：经典 Phong（非 PBR）

**与基础版本的区别**：使用反射向量`R = Reflect(-L, N)`而不是半向量；无 D/F/G 分解。

**用例**：快速原型设计、复古风格渲染、性能受限的场景。 Phong模型的计算成本最低，但不满足能量守恒，并且高光在掠射角处消失（与真实材料相反）。

**关键代码**：```glsl
// Classic Phong reflection model
vec3 R = reflect(-L, N);
float spec = pow(max(0.0, dot(R, V)), 32.0);
vec3 color = albedo * lightColor * NdotL    // diffuse
           + lightColor * spec;              // specular
```### 变体 2：点光衰减

**与基础版本的区别**：增加了距离衰减，适用于点光源/聚光灯场景。基本版本假设定向光（太阳），而点光强度随着距离而降低。

**使用案例**：室内场景、多点光源、近距离灯光效果。

**详情**：
- 物理上正确的衰减应该是“1/距离²”，但实际上“1/(1 + k1*d + k2*d²)”避免了近距离的无限亮度
- k1（线性衰减）：0.01~0.5，k2（二次衰减）：0.001~0.1
- 或者，使用具有最大强度上限的物理衰减：“min(1.0/(d*d), maxIntensity)”

**关键代码**：```glsl
// Point light attenuation (standard pattern)
float dist = length(lightPos - pos);
float attenuation = 1.0 / (1.0 + dist * 0.1 + dist * dist * 0.01);
// k1: linear attenuation coefficient (adjustable 0.01~0.5)
// k2: quadratic attenuation coefficient (adjustable 0.001~0.1)
color *= attenuation;
```### 变体 3：IBL（基于图像的照明）

**与基础版本的区别**：使用环境贴图而不是分析光源，分为漫反射 SH（球谐函数）和镜面拆分总和部分。

**用例**：需要真实环境照明反射的场景。 IBL 可以捕捉复杂的光照环境（例如 HDRI 全景图），产生非常自然的光照效果。

**详情**：
- 漫反射 IBL 使用球谐函数 (SH) 预先计算环境照明的低频分量
- Specular IBL 使用 Epic Games 的 split-sum 近似：将 BRDF 积分拆分为环境贴图 LOD 查找 + 预先计算的 BRDF 积分查找表
- `EnvBRDFApprox` 是虚幻引擎 4 的近似值，避免了对预先计算的 LUT 纹理的需要
- `textureLod(envMap, R, roughness * 7.0)` 使用 mipmap 级别来模拟粗糙表面上的模糊反射
- 基于PBR管道中常见的SH + EnvBRDFApprox方法

**关键代码**：```glsl
// IBL approximation (SH + EnvBRDFApprox method)
// Diffuse IBL: spherical harmonics
vec3 diffuseIBL = diffuseColor * SHIrradiance(N);

// Specular IBL: Unreal's EnvBRDFApprox approximation
vec3 EnvBRDFApprox(vec3 specColor, float roughness, float NdotV) {
    vec4 c0 = vec4(-1, -0.0275, -0.572, 0.022);
    vec4 c1 = vec4(1, 0.0425, 1.04, -0.04);
    vec4 r = roughness * c0 + c1;
    float a004 = min(r.x * r.x, exp2(-9.28 * NdotV)) * r.x + r.y;
    vec2 AB = vec2(-1.04, 1.04) * a004 + r.zw;
    return specColor * AB.x + AB.y;
}
vec3 R = reflect(-V, N);
vec3 envColor = textureLod(envMap, R, roughness * 7.0).rgb;
vec3 specularIBL = EnvBRDFApprox(F0, roughness, NdotV) * envColor;
```### 变体 4：次表面散射近似 (SSS)

**与基础版本的区别**：模拟光线穿过半透明材料（例如皮肤、蜡、水面）。

**用例**：水面、皮肤、蜡烛、树叶和其他半透明材料。 SSS 使薄的部分显得更亮、更半透明。

**详情**：
- **方法 1（SDF 探测）**：沿光线方向探测材料内部的 SDF 值。如果SDF值远小于探头距离，则该点的材料较厚，透过的光较少；否则它会传输更多
- **方法 2（Henyey-Greenstein 相函数）**：描述光散射在介质中的方向分布。参数 g 控制前向/后向散射：g > 0 表示前向散射（例如，皮肤），g < 0 表示后向散射
- 将基于 SDF 的内部探测与 Henyey-Greenstein 相位函数相结合

**关键代码**：```glsl
// SSS approximation (SDF-based interior probing)
// Method 1: SDF-based interior probing
float subsurface(vec3 pos, vec3 L) {
    float sss = 0.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.05 + float(i) * 0.1;
        float d = map(pos + L * h);  // Probe along light direction into interior
        sss += max(0.0, h - d);      // Thinner areas transmit more light
    }
    return clamp(1.0 - sss * 4.0, 0.0, 1.0);
}

// Method 2: Henyey-Greenstein phase function
float HenyeyGreenstein(float cosTheta, float g) {
    float g2 = g * g;
    return (1.0 - g2) / (pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5) * 4.0 * PI);
}
float sssAmount = HenyeyGreenstein(dot(V, L), 0.5);
color += sssColor * sssAmount * NdotL;
```### 变体 5：比尔定律水照明

**与基础版本的区别**：模拟水/透明介质中光的指数衰减。

**用例**：水面、水下场景、玻璃、果汁和其他透明/半透明介质。比尔-朗伯定律描述了光强度在介质中传播时的指数衰减。

**详情**：
- `exp2(-opticalDepth * extinctColor)` 实现与波长相关的指数衰减
- 不同的颜色通道具有不同的衰减系数，产生水的特征颜色（蓝色/绿色传输最多）
- 在 `extinctColor = 1.0 - vec3(0.5, 0.4, 0.1)` 中，vec3 控制每个通道的吸收率
- 内散射模拟光在水体内部的多次散射，赋予深水固有的颜色
- `1.0 - exp(-深度 * 0.1)` 是一个简化的内散射模型
- 基于比尔-朗伯定律，用于波长相关的衰减

**关键代码**：```glsl
// Beer's Law light attenuation
vec3 waterExtinction(float depth) {
    float opticalDepth = depth * 6.0;  // Adjustable: controls attenuation rate
    vec3 extinctColor = 1.0 - vec3(0.5, 0.4, 0.1);  // Adjustable: water absorption color
    return exp2(-opticalDepth * extinctColor);
}

// Usage: underwater object color multiplied by attenuation
vec3 underwaterColor = objectColor * waterExtinction(depth);
// Add water inscattering
vec3 inscatter = waterDiffuse * (1.0 - exp(-depth * 0.1));
underwaterColor += inscatter;
```---

## 性能优化深度分析

### 1. 避免 pow(x, 5.0) 的成本

某些 GPU 上的“pow”函数实现为“exp2(5.0 * log2(x))”，涉及两个超越函数。手动展开乘法链效率更高：```glsl
// Efficient implementation of Schlick Fresnel
float x = 1.0 - cosTheta;
float x2 = x * x;
float x5 = x2 * x2 * x;  // Faster than pow(x, 5.0)
vec3 F = F0 + (1.0 - F0) * x5;
```### 2. 合并 G 和分母（可见性项）

使用`V_SmithGGX`直接返回`G / (4 * NdotV * NdotL)`避免了单独计算G然后再除法。这不仅消除了一次除法，还避免了“4 * NdotV * NdotL”接近零时的数值不稳定。与身高相关的史密斯版本在物理上也更加准确。

### 3. AO 样本计数

- 5 个样本足以满足大多数场景
- 远处的物体最多可以使用 3 个（因为细节不可见）
- 样本步长 h 的上限（`0.12 * i / 4.0`）控制 AO 影响范围：增加它可以检测更大规模的遮挡，但需要更多样本
- 衰减率 `sca *= 0.95` 也是可调的：较小的值使 AO 更集中在表面附近

### 4.软阴影优化

- 使用“clamp(h, 0.02, 0.2)”来限制步长：最小步长 0.02 可防止卡在表面附近，最大步长 0.2 可防止跳过薄几何体
- 阴影光线 maxSteps 可以低于主光线（14~24 步通常就足够了），因为阴影不需要精确的生命值
- `8.0 * h / t` 中的 8.0 控制阴影柔和度：较高的值产生较硬的阴影，较低的值产生较柔和的阴影。这是一个直观的半影大小控制

### 5. 简化的 IBL

- 没有立方体贴图，使用简单的天空颜色渐变作为环境贴图的替代品
- `mix(groundColor, skyColor, R.y * 0.5 + 0.5)` 是最便宜的“环境反射”
- 可以添加太阳方向的`pow(max(0, dot(R, sunDir)), 64.0)`来模拟太阳的镜面反射

### 6. 分支剔除

当 NdotL <= 0 时，表面背向光源，并且可以跳过所有镜面反射计算（D、F、G）：```glsl
// Skip entire specular computation when NdotL <= 0
if (NdotL > 0.0) {
    // ... D, F, G computation ...
}
```注意：GPU 上的分支效率取决于同一扭曲/波前内像素的一致性。如果大面积背对光线，此分支有效；如果分支条件在相邻像素之间频繁切换，它实际上可能会更慢。

---

## 详细组合建议

### 灯光 + 光线行进

光线行进场景是光照模型最常见的宿主。法线是通过 SDF 有限差分获得的，AO 和阴影直接利用 SDF 查询。

关键集成点：
- `calcNormal` 提供正常的 N
- `calcAO` 利用 SDF 进行环境光遮挡
- `softShadow` 利用 SDF 实现软阴影
- 材质 ID 可以通过“map”函数的返回值传递

### 光照+体积渲染

云、烟和雾等体积效应需要比尔定律衰减和相位函数（例如 Henyey-Greenstein）。 PBR 表面照明与体积云照明自然集成。

关键集成点：
- 体积渲染使用光线行进来逐步穿过体积
- 每一步都会累积密度并应用比尔定律衰减
- 照明使用 Henyey-Greenstein 相位函数而不是 BRDF
- 最终结果与表面渲染输出进行 alpha 混合

### 光照+法线贴图/程序法线

法线不必来自自卫队。 FBM 噪声生成的程序法线（例如海浪法线、水面法线）可以直接传递到照明函数，从而产生丰富的表面细节。

关键集成点：
- 程序法线通过扰动基本法线来工作：“N = 标准化（N + 扰动）”
- FBM 噪声频率和幅度控制细节的粗糙度和强度
- SDF法线和程序法线可以组合用于宏观形状+微观细节

### 灯光+后期处理

色调映射和伽玛校正是 PBR 管道的重要组成部分。 HDR 光照值必须映射到 [0,1] LDR 范围才能正确显示：```glsl
// ACES — currently the most popular tone mapping
col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);

// Reinhard — simplest tone mapping
col = col / (col + 1.0);

// Gamma correction — convert from linear space to sRGB
col = pow(col, vec3(1.0 / 2.2));
```注意：所有光照计算必须在线性空间中进行；伽马校正仅应用于最终输出。

### 照明+反射

多层反射或环境反射会在“reflect(rd, N)”方向再次查询场景，将反射颜色混合到菲涅耳加权的最终结果中。```glsl
// Basic reflection pattern
vec3 R = reflect(rd, N);
vec3 reflColor = traceScene(pos + N * 0.01, R);  // Offset to avoid self-intersection
vec3 F = fresnelSchlick(F0, NdotV);
color = mix(color, reflColor, F);
```常见的水面渲染方式结合了折射+反射+菲涅尔混合：
- 反射方向`reflect(rd, N)`查询天空/场景
- 折射方向 `refract(rd, N, 1.0/1.33)` 查询水下场景
- 反射和折射之间的菲涅耳系数混合