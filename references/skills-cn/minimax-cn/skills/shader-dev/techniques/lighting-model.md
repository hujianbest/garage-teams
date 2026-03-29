# 灯光模型技巧

## 用例
- 为光线行进或光栅化场景添加逼真的照明
- 模拟光与各种材料（金属、电介质、水、皮肤等）的相互作用
- 从简单的漫反射/镜面反射到完整的 PBR
- 多光合成（太阳、天空、环境光）
- 在 ShaderToy 中向 SDF 场景添加材质外观

## 核心原则

照明 = 漫反射 + 镜面反射：

- **漫反射**：兰伯特定律`I = max(0, N·L)`
- **镜面**：经验模型使用 Blinn-Phong `pow(max(0, N·H), shininess)`；基于物理的模型使用 Cook-Torrance BRDF

### 关键公式```
Lambert:        L_diffuse  = albedo * lightColor * max(0, N·L)
Blinn-Phong:    H = normalize(V + L); L_specular = lightColor * pow(max(0, N·H), shininess)
Cook-Torrance:  f_specular = D(h) * F(v,h) * G(l,v,h) / (4 * (N·L) * (N·V))
Fresnel:        F = F0 + (1 - F0) * (1 - V·H)^5
```- **D** = GGX/Trowbridge-Reitz 正态分布
- **F** = Schlick 菲涅尔近似
- **G** = 史密斯几何阴影
- F0：电介质~0.04，金属使用baseColor

## 实施步骤

### 第 1 步：场景基础知识（法线 + 矢量设置）```glsl
// SDF normal (finite difference method)
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

vec3 N = calcNormal(pos);           // surface normal
vec3 V = -rd;                        // view direction
vec3 L = normalize(lightPos - pos);  // light direction (point light)
// directional light: vec3 L = normalize(vec3(0.6, 0.8, -0.5));
```### 步骤 2：兰伯特漫反射```glsl
float NdotL = max(0.0, dot(N, L));
vec3 diffuse = albedo * lightColor * NdotL;

// energy-conserving version
vec3 diffuse_conserved = albedo / PI * lightColor * NdotL;

// Half-Lambert (reduces over-darkening on backlit faces, commonly used for SSS approximation)
float halfLambert = NdotL * 0.5 + 0.5;
vec3 diffuse_wrapped = albedo * lightColor * halfLambert;
```### 步骤 3：Blinn-Phong 镜面反射```glsl
vec3 H = normalize(V + L);
float NdotH = max(0.0, dot(N, H));
float SHININESS = 32.0;  // 4.0 (rough) ~ 256.0 (smooth)

// with normalization factor for energy conservation
float normFactor = (SHININESS + 8.0) / (8.0 * PI);
float spec = normFactor * pow(NdotH, SHININESS);
vec3 specular = lightColor * spec;
```### 步骤 4：菲涅耳石里克```glsl
vec3 fresnelSchlick(vec3 F0, float cosTheta) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

// metallic workflow
vec3 F0 = mix(vec3(0.04), baseColor, metallic);

// computed with V·H (specular reflection BRDF)
float VdotH = max(0.0, dot(V, H));
vec3 F = fresnelSchlick(F0, VdotH);

// computed with N·V (environment reflection, rim light)
float NdotV = max(0.0, dot(N, V));
vec3 F_env = fresnelSchlick(F0, NdotV);
```### 步骤 5：GGX 正态分布（D 项）```glsl
float distributionGGX(float NdotH, float roughness) {
    float a = roughness * roughness;  // roughness must be squared first
    float a2 = a * a;
    float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}
```### 步骤 6：几何阴影（G 术语）```glsl
// Method 1: Schlick-GGX
float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}
float geometrySmith(float NdotV, float NdotL, float roughness) {
    return geometrySchlickGGX(NdotV, roughness) * geometrySchlickGGX(NdotL, roughness);
}

// Method 2: Height-Correlated Smith (more accurate, directly returns the visibility term)
float visibilitySmith(float NdotV, float NdotL, float roughness) {
    float a2 = roughness * roughness;
    float gv = NdotL * sqrt(NdotV * (NdotV - NdotV * a2) + a2);
    float gl = NdotV * sqrt(NdotL * (NdotL - NdotL * a2) + a2);
    return 0.5 / max(gv + gl, 0.00001);
}

// Method 3: Simplified approximation
float G1V(float dotNV, float k) {
    return 1.0 / (dotNV * (1.0 - k) + k);
}
// Usage: float vis = G1V(NdotL, k) * G1V(NdotV, k); where k = roughness/2
```### 步骤 7：组装 Cook-Torrance BRDF```glsl
vec3 cookTorranceBRDF(vec3 N, vec3 V, vec3 L, float roughness, vec3 F0) {
    vec3 H = normalize(V + L);
    float NdotL = max(0.0, dot(N, L));
    float NdotV = max(0.0, dot(N, V));
    float NdotH = max(0.0, dot(N, H));
    float VdotH = max(0.0, dot(V, H));

    float D = distributionGGX(NdotH, roughness);
    vec3 F = fresnelSchlick(F0, VdotH);
    float Vis = visibilitySmith(NdotV, NdotL, roughness);

    // Vis version already includes the 4*NdotV*NdotL denominator
    vec3 specular = D * F * Vis;
    // Or with standard G term: specular = (D * F * G) / max(4.0 * NdotV * NdotL, 0.001);

    return specular * NdotL;
}
```### 步骤8：多光累积和合成```glsl
vec3 shade(vec3 pos, vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 diffuseColor = albedo * (1.0 - metallic);  // metals have no diffuse
    vec3 color = vec3(0.0);

    // primary light (sun)
    vec3 sunDir = normalize(vec3(0.6, 0.8, -0.5));
    vec3 sunColor = vec3(1.0, 0.95, 0.85) * 2.0;
    vec3 H = normalize(V + sunDir);
    float NdotL = max(0.0, dot(N, sunDir));
    float NdotV = max(0.0, dot(N, V));
    float VdotH = max(0.0, dot(V, H));
    vec3 F = fresnelSchlick(F0, VdotH);
    vec3 kD = (1.0 - F) * (1.0 - metallic);  // energy conservation

    color += kD * diffuseColor / PI * sunColor * NdotL;
    color += cookTorranceBRDF(N, V, sunDir, roughness, F0) * sunColor;

    // sky light (hemisphere approximation)
    vec3 skyColor = vec3(0.2, 0.5, 1.0) * 0.3;
    float skyDiffuse = 0.5 + 0.5 * N.y;
    color += diffuseColor * skyColor * skyDiffuse;

    // back light / rim light
    vec3 backDir = normalize(vec3(-sunDir.x, 0.0, -sunDir.z));
    float backDiffuse = clamp(dot(N, backDir) * 0.5 + 0.5, 0.0, 1.0);
    color += diffuseColor * vec3(0.25, 0.15, 0.1) * backDiffuse;

    return color;
}
```### 步骤 9：环境光遮挡 (AO)```glsl
// Raymarching AO (using SDF queries)
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

float ao = calcAO(pos, N);
diffuseLight *= ao;
// specular AO (more subtle):
specularLight *= clamp(pow(NdotV + ao, roughness * roughness) - 1.0 + ao, 0.0, 1.0);
```### 户外三灯款

室外 SDF 场景的首选照明设置。使用三个方向光源以最小的成本近似完全的全局照明：```glsl
// === Outdoor Three-Light Lighting ===
// Compute material, occlusion, and shadow first
vec3 material = getMaterial(pos, nor);  // albedo, keep ≤ 0.2 for realism
float occ = calcAO(pos, nor);          // ambient occlusion
float sha = calcSoftShadow(pos, sunDir, 0.02, 8.0);

// Three light contributions
float sun = clamp(dot(nor, sunDir), 0.0, 1.0);        // direct sunlight
float sky = clamp(0.5 + 0.5 * nor.y, 0.0, 1.0);       // hemisphere sky light
float ind = clamp(dot(nor, normalize(sunDir * vec3(-1.0, 0.0, -1.0))), 0.0, 1.0); // indirect bounce

// Combine with colored shadows (key technique: shadow penumbra tints blue)
vec3 lin = vec3(0.0);
lin += sun * vec3(1.64, 1.27, 0.99) * pow(vec3(sha), vec3(1.0, 1.2, 1.5));  // warm sun, colored shadow
lin += sky * vec3(0.16, 0.20, 0.28) * occ;   // cool sky fill
lin += ind * vec3(0.40, 0.28, 0.20) * occ;   // warm ground bounce

vec3 color = material * lin;
```主要原则：
- **彩色阴影半影**：`pow(vec3(sha), vec3(1.0, 1.2, 1.5))`使阴影边缘略带蓝色/冷色，模仿半影区域中真实的次表面散射
- **材质反照率规则**：保持漫反射反照率≤0.2；调整亮度的光强度，而不是材料值。现实世界的表面反照率很少超过 0.3
- **线性工作流程**：线性空间中的所有计算，在最后应用 gamma `pow(color, vec3(1.0/2.2))`
- **天空光近似**：`0.5 + 0.5 *nor.y`是一个廉价的半球积分 - 指向上方的表面得到完整的天空，指向下方的表面没有得到
- 不要对太阳/主光应用环境光遮挡——阴影可以解决这个问题

## 完整的代码模板```glsl
// Lighting Model Complete Template - Runs directly in ShaderToy
// Progressive implementation from Lambert to Cook-Torrance PBR

#define PI 3.14159265359

// ========== Adjustable Parameters ==========
#define ROUGHNESS 0.35
#define METALLIC 0.0
#define ALBEDO vec3(0.8, 0.2, 0.2)
#define SUN_DIR normalize(vec3(0.6, 0.8, -0.5))
#define SUN_COLOR vec3(1.0, 0.95, 0.85) * 2.0
#define SKY_COLOR vec3(0.2, 0.5, 1.0) * 0.4
#define BACKGROUND_TOP vec3(0.5, 0.7, 1.0)
#define BACKGROUND_BOT vec3(0.8, 0.85, 0.9)

// ========== SDF Scene ==========
float map(vec3 p) {
    float sphere = length(p - vec3(0.0, 0.0, 0.0)) - 1.0;
    float ground = p.y + 1.0;
    return min(sphere, ground);
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// ========== AO ==========
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

// ========== Soft Shadow ==========
float softShadow(vec3 ro, vec3 rd, float mint, float maxt) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 24; i++) {
        float h = map(ro + rd * t);
        res = min(res, 8.0 * h / t);
        t += clamp(h, 0.02, 0.2);
        if (res < 0.001 || t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}

// ========== PBR BRDF Components ==========
float D_GGX(float NdotH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float d = NdotH * NdotH * (a2 - 1.0) + 1.0;
    return a2 / (PI * d * d);
}

vec3 F_Schlick(vec3 F0, float cosTheta) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

float V_SmithGGX(float NdotV, float NdotL, float roughness) {
    float a2 = roughness * roughness;
    a2 *= a2;
    float gv = NdotL * sqrt(NdotV * NdotV * (1.0 - a2) + a2);
    float gl = NdotV * sqrt(NdotL * NdotL * (1.0 - a2) + a2);
    return 0.5 / max(gv + gl, 1e-5);
}

// ========== Complete Lighting ==========
vec3 shade(vec3 pos, vec3 N, vec3 V, vec3 albedo, float roughness, float metallic) {
    vec3 F0 = mix(vec3(0.04), albedo, metallic);
    vec3 diffuseColor = albedo * (1.0 - metallic);
    float NdotV = max(dot(N, V), 1e-4);
    float ao = calcAO(pos, N);
    vec3 color = vec3(0.0);

    // sunlight
    {
        vec3 L = SUN_DIR;
        vec3 H = normalize(V + L);
        float NdotL = max(dot(N, L), 0.0);
        float NdotH = max(dot(N, H), 0.0);
        float VdotH = max(dot(V, H), 0.0);
        float D = D_GGX(NdotH, roughness);
        vec3  F = F_Schlick(F0, VdotH);
        float Vis = V_SmithGGX(NdotV, NdotL, roughness);
        vec3 kD = (1.0 - F) * (1.0 - metallic);
        vec3 diffuse  = kD * diffuseColor / PI;
        vec3 specular = D * F * Vis;
        float shadow = softShadow(pos, L, 0.02, 5.0);
        color += (diffuse + specular) * SUN_COLOR * NdotL * shadow;
    }

    // sky light (hemisphere approximation)
    {
        float skyDiff = 0.5 + 0.5 * N.y;
        color += diffuseColor * SKY_COLOR * skyDiff * ao;
    }

    // back light / rim light
    {
        vec3 backDir = normalize(vec3(-SUN_DIR.x, 0.0, -SUN_DIR.z));
        float backDiff = clamp(dot(N, backDir) * 0.5 + 0.5, 0.0, 1.0);
        color += diffuseColor * vec3(0.15, 0.1, 0.08) * backDiff * ao;
    }

    // environment reflection (simplified)
    {
        vec3 R = reflect(-V, N);
        vec3 envColor = mix(BACKGROUND_BOT, BACKGROUND_TOP, clamp(R.y * 0.5 + 0.5, 0.0, 1.0));
        vec3 F_env = F_Schlick(F0, NdotV);
        float envOcc = clamp(pow(NdotV + ao, roughness * roughness) - 1.0 + ao, 0.0, 1.0);
        color += F_env * envColor * envOcc * (1.0 - roughness * 0.7);
    }

    return color;
}

// ========== Raymarching ==========
float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < 128; i++) {
        float d = map(ro + rd * t);
        if (d < 0.001) return t;
        t += d;
        if (t > 50.0) break;
    }
    return -1.0;
}

// ========== Background ==========
vec3 background(vec3 rd) {
    vec3 col = mix(BACKGROUND_BOT, BACKGROUND_TOP, clamp(rd.y * 0.5 + 0.5, 0.0, 1.0));
    float sun = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    col += SUN_COLOR * 0.3 * pow(sun, 8.0);
    col += SUN_COLOR * 1.0 * pow(sun, 256.0);
    return col;
}

// ========== Main Function ==========
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    float angle = iTime * 0.3;
    vec3 ro = vec3(3.0 * cos(angle), 1.5, 3.0 * sin(angle));
    vec3 ta = vec3(0.0, 0.0, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.5 * ww);

    vec3 col = background(rd);
    float t = raymarch(ro, rd);

    if (t > 0.0) {
        vec3 pos = ro + t * rd;
        vec3 N = calcNormal(pos);
        vec3 V = -rd;
        vec3 albedo = ALBEDO;
        float roughness = ROUGHNESS;
        float metallic = METALLIC;

        if (pos.y < -0.99) {
            roughness = 0.8;
            metallic = 0.0;
            float checker = mod(floor(pos.x) + floor(pos.z), 2.0);
            albedo = mix(vec3(0.3), vec3(0.6), checker);
        }

        col = shade(pos, N, V, albedo, roughness, metallic);
    }

    col = col / (col + vec3(1.0));       // Tone mapping (Reinhard)
    col = pow(col, vec3(1.0 / 2.2));     // Gamma
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：经典 Phong（非 PBR）```glsl
vec3 R = reflect(-L, N);
float spec = pow(max(0.0, dot(R, V)), 32.0);
vec3 color = albedo * lightColor * NdotL + lightColor * spec;
```### 变体 2：点光衰减```glsl
float dist = length(lightPos - pos);
float attenuation = 1.0 / (1.0 + dist * 0.1 + dist * dist * 0.01);
color *= attenuation;
```### 变体 3：IBL（基于图像的照明）```glsl
// diffuse IBL: spherical harmonics
vec3 diffuseIBL = diffuseColor * SHIrradiance(N);

// specular IBL: EnvBRDFApprox
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
```### 变体 4：次表面散射近似 (SSS)```glsl
// SDF-based interior probing
float subsurface(vec3 pos, vec3 L) {
    float sss = 0.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.05 + float(i) * 0.1;
        float d = map(pos + L * h);
        sss += max(0.0, h - d);
    }
    return clamp(1.0 - sss * 4.0, 0.0, 1.0);
}

// Henyey-Greenstein phase function
float HenyeyGreenstein(float cosTheta, float g) {
    float g2 = g * g;
    return (1.0 - g2) / (pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5) * 4.0 * PI);
}
float sssAmount = HenyeyGreenstein(dot(V, L), 0.5);
color += sssColor * sssAmount * NdotL;
```### 变体 5：比尔定律水照明```glsl
vec3 waterExtinction(float depth) {
    float opticalDepth = depth * 6.0;
    vec3 extinctColor = 1.0 - vec3(0.5, 0.4, 0.1);
    return exp2(-opticalDepth * extinctColor);
}
vec3 underwaterColor = objectColor * waterExtinction(depth);
vec3 inscatter = waterDiffuse * (1.0 - exp(-depth * 0.1));
underwaterColor += inscatter;
```## 表演与作曲

- **菲涅耳优化**：使用 `x2*x2*x` 代替 `pow(x, 5.0)`
- **可见性**：使用`V_SmithGGX`直接返回`G/(4*NdotV*NdotL)`，避免单独除法
- **AO采样**：5个样本就足够了；远距离时可减少至 3 个
- **软阴影**：`clamp(h, 0.02, 0.2)`限制步长；通常14~24步就足够了； `8.0*h/t`控制柔软度
- **简化的 IBL**：没有立方体贴图，近似为 `mix(groundColor, skyColor, R.y*0.5+0.5)`
- **分支剔除**：当`NdotL <= 0`时跳过镜面反射计算
- **Raymarching集成**：对法线使用SDF有限差分，直接查询SDF以获取AO/阴影
- **体积渲染集成**：比尔定律衰减+Henyey-Greenstein相位函数； FBM 噪声程序法线可以直接传递给照明函数
- **后处理集成**：ACES `(col*(2.51*col+0.03))/(col*(2.43*col+0.59)+0.14)` / Reinhard `col/(col+1)` + Gamma
- **反射集成**：`reflect(rd, N)`再次查询场景，将结果与菲涅耳权重混合

## 进一步阅读

完整的分步教程、数学推导和高级用法，请参见 [参考](../reference/lighting-model.md)