# 路径追踪和全局照明 - 详细参考

本文档是[SKILL.md](SKILL.md)的完整参考，涵盖必备知识、分步详细讲解、数学推导和高级用法。

## 先决条件

- **GLSL基本语法**：ShaderToy多通道（Buffer A/B/Image）架构
- **矢量数学**：点积、叉积、反射/折射矢量计算
- **概率基础**：PDF（概率密度函数）、蒙特卡罗积分、重要性采样
- **渲染方程**基本形式：$L_o = L_e + \int f_r \cdot L_i \cdot \cos\theta \, d\omega$
- **射线几何相交**方法（球体、平面、SDF）

## 核心原则详细信息

路径追踪通过蒙特卡罗方法求解渲染方程。对于每个像素，从相机发出一条光线并在场景中反弹。每次弹跳时：

1. **交集**：找到光线与场景最近的交集
2. **着色**：根据材质类型（漫反射/镜面反射/折射）计算当前节点的光照贡献
3. **采样下一个方向**：根据BRDF/BSDF生成下一个反弹光线
4. **累加**：将路径上所有节点的加权光照贡献相加

### 核心数学

- **渲染方程**： $L_o(x, \omega_o) = L_e(x, \omega_o) + \int_\Omega f_r(x, \omega_i, \omega_o) L_i(x, \omega_i) (\omega_i \cdot n) d\omega_i$
- **蒙特卡罗估计**：$L \approx \frac{1}{N} \sum \frac{f_r \cdot L_i \cdot \cos\theta}{p(\omega)}$
- **施里克菲涅耳**：$F = F_0 + (1 - F_0)(1 - \cos\theta)^5$
- **余弦加权采样 PDF**: $p(\omega) = \frac{\cos\theta}{\pi}$

### 按键设计

**迭代循环**取代了递归，使用两个变量“acc”（累积辐射率）和“掩模/吞吐量”（路径衰减）来跟踪路径贡献。每次反弹时，材质颜色都会乘以吞吐量，并添加自发射和直接照明以符合要求。

## 详细实施步骤

### 步骤 1：伪随机数生成器

**什么**：为每帧每个像素提供不同的随机数序列，驱动所有蒙特卡罗采样。

**为什么**：路径追踪中的所有随机决策（方向采样、俄罗斯轮盘赌、菲涅尔选择）都取决于随机数。种子必须在像素和帧之间充分去相关；否则会出现结构化噪声。

**方法一：sin-hash（简单，适合入门）**```glsl
float seed;
float rand() { return fract(sin(seed++) * 43758.5453123); }
// Initialization: seed = iTime + iResolution.y * fragCoord.x / iResolution.x + fragCoord.y / iResolution.y;
```**方法2：整数哈希（质量更好，推荐）**```glsl
int iSeed;
int irand() { iSeed = iSeed * 0x343fd + 0x269ec3; return (iSeed >> 16) & 32767; }
float frand() { return float(irand()) / 32767.0; }
void srand(ivec2 p, int frame) {
    int n = frame;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.y;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    n += p.x;
    n = (n << 13) ^ n; n = n * (n * n * 15731 + 789221) + 1376312589;
    iSeed = n;
}
```sin-hash 可能会在某些 GPU 上产生周期性伪影（由于硬件上的 sin 精度不一致）。整数哈希更加可靠和统一。 Visual Studio LCG (`0x343fd`) 是常用的线性同余生成器。

### 步骤 2：光线场景相交

**什么**：给定光线原点和方向，找到最近的交点以及交点处的法线和材质信息。

**为什么**：这是路径追踪的基本操作。可以使用解析几何（球体、平面）或 SDF 射线行进。

**分析球体相交（经典的smallpt方法）**```glsl
struct Ray { vec3 o, d; };
struct Sphere { float r; vec3 p, e, c; int refl; };

float intersectSphere(Sphere s, Ray r) {
    vec3 op = s.p - r.o;
    float b = dot(op, r.d);
    float det = b * b - dot(op, op) + s.r * s.r;
    if (det < 0.) return 0.;
    det = sqrt(det);
    float t = b - det;
    if (t > 1e-3) return t;
    t = b + det;
    return t > 1e-3 ? t : 0.;
}
```推导：射线$r(t) = o + td$，球体$|p - c|^2 = R^2$，替换产生二次$t^2 - 2b \cdot t + c = 0$，其中$b = (c - o) \cdot d$，判别式$\Delta = b^2 - |c - o|^2 + R^2$。 `1e-3` 的 epsilon 可以防止自相交。

**SDF 射线行进（用于复杂几何形状）**```glsl
float map(vec3 p) { /* returns distance to nearest surface */ }

float raymarch(vec3 ro, vec3 rd, float tmax) {
    float t = 0.01;
    for (int i = 0; i < 256; i++) {
        float h = map(ro + rd * t);
        if (abs(h) < 0.0001 || t > tmax) break;
        t += h;
    }
    return t;
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.0001, 0.);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)));
}
```自卫队行军的原则是：每一步都按照“到最近地面的距离”安全前进，确保不跨越地面。步数 (128-256) 和阈值 (0.0001) 表示准确性和性能之间的权衡。

### 步骤 3：余弦加权半球采样

**什么**：根据表面法线上方半球的余弦权重生成随机方向分布，用于漫反射。

**为什么**：余弦加权采样（Malley 方法）将朗伯 BRDF 分布与 PDF $\cos\theta / \pi$ 相匹配，将 BRDF/PDF 简化为反照率并大大减少方差。

使用均匀半球采样 (PDF = $1/2\pi$)，每次反弹都需要额外乘以 $\cos\theta \cdot 2$，并且方差会更高，因为许多样本方向对积分的贡献很小。

**方法一：fizzer法（最简洁）**```glsl
vec3 cosineDirection(vec3 nor) {
    float u = frand();
    float v = frand();
    float a = 6.2831853 * v;
    float b = 2.0 * u - 1.0;
    vec3 dir = vec3(sqrt(1.0 - b * b) * vec2(cos(a), sin(a)), b);
    return normalize(nor + dir); // fizzer method
}
```原理：在单位球面上均匀采样一点并加上法线方向，然后归一化，自然就产生了余弦分布。这是有效的，因为单位球体上的均匀点投影到法线上方的半球上，自然形成余弦分布。

**方法2：经典ONB构建（更直观）**```glsl
vec3 cosineDirectionONB(vec3 n) {
    vec2 r = vec2(frand(), frand());
    vec3 u = normalize(cross(n, vec3(0., 1., 1.)));
    vec3 v = cross(u, n);
    float ra = sqrt(r.y);
    float rx = ra * cos(6.2831853 * r.x);
    float ry = ra * sin(6.2831853 * r.x);
    float rz = sqrt(1.0 - r.y);
    return normalize(rx * u + ry * v + rz * n);
}
```原理：首先建立以 n 为 z 轴的正交基（ONB），然后使用 Malley 方法在局部坐标中采样：将均匀随机数映射到单位圆盘上（$r = \sqrt{\xi_2}$，$\phi = 2\pi\xi_1$），z 分量为 $\sqrt{1 - r^2}$。

### 步骤 4：材料系统和 BRDF 评估

**内容**：根据相交处的材质类型（漫反射、镜面反射、折射），确定光线的下一个方向和能量衰减。

**为什么**：不同的材料对光的反应完全不同。漫反射随机散射，镜面反射完美，折射材料遵循斯涅尔定律。菲涅尔效应决定反射/折射比。```glsl
#define MAT_DIFFUSE  0
#define MAT_SPECULAR 1
#define MAT_DIELECTRIC 2
```**扩散**：
- 新方向 = `cosineDirection(normal)`
- `吞吐量*=反照率`
- 由于采用余弦加权采样，BRDF($1/\pi$) * $\cos\theta$ / PDF($\cos\theta/\pi$) = 1，所以吞吐量只需要乘以反照率即可

**镜面**：
- 新方向 = `reflect(rd, normal)`
- `吞吐量*=反照率`
- 完美镜像的 BRDF 是 delta 函数；只有一个方向有贡献

**折射（玻璃）**：```glsl
void handleDielectric(inout Ray r, vec3 n, vec3 x, float ior,
                      vec3 albedo, inout vec3 mask) {
    float cosi = dot(n, r.d);
    float eta = cosi > 0. ? ior : 1.0 / ior;       // Entering/leaving medium
    vec3 nl = cosi > 0. ? -n : n;                    // Outward-facing normal
    cosi = abs(cosi);

    float cos2t = 1.0 - eta * eta * (1.0 - cosi * cosi);
    r = Ray(x, reflect(r.d, n));                      // Default to reflection

    if (cos2t > 0.) {
        vec3 tdir = normalize(r.d / eta + nl * (cosi / eta - sqrt(cos2t)));
        // Schlick Fresnel
        float R0 = ((ior - 1.) * (ior - 1.)) / ((ior + 1.) * (ior + 1.));
        float c = 1.0 - (cosi > 0. ? dot(tdir, n) : cosi);
        float Re = R0 + (1.0 - R0) * c * c * c * c * c;
        float P = 0.25 + 0.5 * Re;
        if (frand() < P) {
            mask *= Re / P;                            // Reflection
        } else {
            mask *= albedo * (1.0 - Re) / (1.0 - P);  // Refraction
            r = Ray(x, tdir);
        }
    }
}
```要点：
- **斯涅尔定律**：$n_1 \sin\theta_1 = n_2 \sin\theta_2$；当 $\sin\theta_2 > 1$ 时发生全内反射
- **Schlick 近似**：$R(\theta) = R_0 + (1-R_0)(1-\cos\theta)^5$，其中 $R_0 = ((n_1-n_2)/(n_1+n_2))^2$
- **俄罗斯轮盘赌选择**：不是直接通过`Re`进行选择，而是使用调整后的概率`P = 0.25 + 0.5 * Re`，然后通过掩码进行补偿。这避免了当Re较低时几乎总是选择折射的问题

### 步骤 5：直接光采样（下一个事件估计）

**内容**：在每个漫反射交叉点，直接向光源投射阴影光线以计算直接照明贡献。

**为什么**：纯随机路径不太可能击中小面积光源。直接对光源采样大大减少了方差并加速了收敛。```glsl
// Solid angle sampling of spherical light source
vec3 directLighting(vec3 x, vec3 n, vec3 albedo,
                    vec3 lightPos, float lightRadius, vec3 lightEmission,
                    int selfId) {
    vec3 l0 = lightPos - x;
    float cos_a_max = sqrt(1.0 - clamp(lightRadius * lightRadius / dot(l0, l0), 0., 1.));
    float cosa = mix(cos_a_max, 1.0, frand());
    float sina = sqrt(1.0 - cosa * cosa);
    float phi = 6.2831853 * frand();

    // Sample within the cone toward the light source
    vec3 w = normalize(l0);
    vec3 u = normalize(cross(w.yzx, w));
    vec3 v = cross(w, u);
    vec3 l = (u * cos(phi) + v * sin(phi)) * sina + w * cosa;

    // Shadow test
    if (shadowTest(Ray(x, l), selfId, lightId)) {
        float omega = 6.2831853 * (1.0 - cos_a_max); // Solid angle
        return albedo * lightEmission * clamp(dot(l, n), 0., 1.) * omega / 3.14159265;
    }
    return vec3(0.);
}
```数学推导：
- 着色点处球形光所对的立体角：$\omega = 2\pi(1 - \cos\alpha_{max})$，其中 $\cos\alpha_{max} = \sqrt{1 - R^2/d^2}$
- 锥体内均匀采样的 PDF：$p = 1/\omega$
- 直接光照贡献：$L_{direct} = \frac{f_r \cdot L_e \cdot \cos\theta_{light}}{p} = 反照率 \cdot L_e \cdot \cos\theta \cdot \omega / \pi$

注意：启用 NEE 后，撞击光源的间接反射不应再次累积其发射（以避免重复计数）。然而，在光源较大的小类型实现中，这种重复计数的影响可以忽略不计。严格的方法是当NEE激活时跳过间接命中发光。

### 步骤 6：路径跟踪主循环

**什么**：将上述所有模块组合成一个完整的路径跟踪器。

**为什么**：迭代结构避免了GLSL缺乏递归支持，而吞吐量/acc模式是标准路径跟踪实现范例。```glsl
#define MAX_BOUNCES 8       // Adjustable: max bounce count; more = more accurate indirect lighting
#define ENABLE_NEE true     // Adjustable: whether to enable direct light sampling

vec3 pathtrace(Ray r) {
    vec3 acc = vec3(0.);        // Accumulated radiance
    vec3 throughput = vec3(1.); // Path attenuation (throughput)

    for (int depth = 0; depth < MAX_BOUNCES; depth++) {
        // 1. Intersection
        float t;
        vec3 n, albedo, emission;
        int matType;
        if (!intersectScene(r, t, n, albedo, emission, matType))
            break; // Shot into the sky

        vec3 x = r.o + r.d * t;
        vec3 nl = dot(n, r.d) < 0. ? n : -n; // Outward-facing normal

        // 2. Accumulate emission
        acc += throughput * emission;

        // 3. Russian roulette (starting from bounce 3)
        if (depth > 2) {
            float p = max(throughput.r, max(throughput.g, throughput.b));
            if (frand() > p) break;
            throughput /= p;
        }

        // 4. Sample based on material
        if (matType == MAT_DIFFUSE) {
            // Direct light sampling (NEE)
            if (ENABLE_NEE)
                acc += throughput * directLighting(x, nl, albedo, ...);
            // Indirect bounce
            throughput *= albedo;
            r = Ray(x + nl * 1e-3, cosineDirection(nl));

        } else if (matType == MAT_SPECULAR) {
            throughput *= albedo;
            r = Ray(x + nl * 1e-3, reflect(r.d, n));

        } else if (matType == MAT_DIELECTRIC) {
            handleDielectric(r, n, x, 1.5, albedo, throughput);
        }
    }
    return acc;
}
```设计要点：
- `acc` 累积最终颜色，`throughput` 记录沿路径所有材料的衰减
- 俄罗斯轮盘保持**无偏性**：终止概率为$1-p$，幸存路径将吞吐量除以$p$，因此期望值不变
- 正常偏移（`x + nl * 1e-3`）可防止由于浮点精度而导致的自相交

### 步骤7：渐进累积和显示

**内容**：对多帧结果进行加权平均，逐渐收敛到无噪声图像。应用色调映射和伽玛校正进行显示。

**为什么**：单帧路径追踪的噪声非常大。通过多帧累加，样本数线性增长，噪声降低$1/\sqrt{N}$。

**缓冲区A（路径追踪+累加）**```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    srand(ivec2(fragCoord), iFrame);
    // ... camera setup, ray generation ...
    vec3 color = pathtrace(ray);

    // Progressive accumulation
    vec4 prev = texelFetch(iChannel0, ivec2(fragCoord), 0);
    if (iFrame == 0) prev = vec4(0.);
    fragColor = prev + vec4(color, 1.0);
}
```累加策略：将每帧的颜色和样本数存储在RGBA中（RGB=颜色累加，A=样本数累加）。显示时除以A即可得到平均值。当`iFrame == 0`时清零以处理ShaderToy的编辑重置。

**图像传递（色调映射+伽玛）**```glsl
vec3 ACES(vec3 x) {
    float a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
    return (x * (a * x + b)) / (x * (c * x + d) + e);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 data = texelFetch(iChannel0, ivec2(fragCoord), 0);
    vec3 col = data.rgb / max(data.a, 1.0);

    col = ACES(col);                         // Tone mapping
    col = pow(col, vec3(1.0 / 2.2));         // Gamma correction

    // Optional: vignette
    vec2 uv = fragCoord / iResolution.xy;
    col *= 0.5 + 0.5 * pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.1);

    fragColor = vec4(col, 1.0);
}
```ACES 色调映射将 HDR 辐射值压缩到 [0,1] LDR 范围，同时保留高光和阴影的细节。伽马校正 (2.2) 将线性色彩空间转换为 sRGB 显示空间。

## 常见变体详细信息

### 1.SDF场景路径追踪

**与基础版本的区别**：用 SDF 射线行进替换解析球体相交，支持任意复杂的几何形状（分形、布尔运算等）。

SDF路径追踪的挑战：
- SDF 行进比分析交集慢得多（每一步需要 128+ 次迭代）
- 每次反弹都需要数值法线（中心差），添加 6 个额外的“map()”调用
- 自相交问题更加严重，需要更大的 epsilon 偏移量```glsl
float map(vec3 p) {
    float d = p.y + 0.5;                        // Ground
    d = min(d, length(p - vec3(0., 0.4, 0.)) - 0.4); // Sphere
    return d;
}

float intersectScene(vec3 ro, vec3 rd, float tmax) {
    float t = 0.01;
    for (int i = 0; i < 128; i++) {
        float h = map(ro + rd * t);
        if (h < 0.0001 || t > tmax) break;
        t += h;
    }
    return t < tmax ? t : -1.0;
}
// Normal via central difference: calcNormal()
// Materials distinguished by ID returned from map()
```### 2. 迪士尼 BRDF 路径追踪

**与基础版本的区别**：用迪士尼原理的 BRDF 替换简单的兰伯特 + 完美镜像，支持金属/粗糙度参数化 PBR 材质。

Disney BRDF 的核心组件：
- **GGX正态分布(D)**：描述微表面法线的统计分布；粗糙度越高=分布越宽
- **史密斯遮挡函数 (G)**：考虑微表面之间的自阴影
- **菲涅耳项 (F)**：Schlick 近似；金属控制 F0（金属：F0 = 反照率，电介质：F0 = 0.04）
- **VNDF采样**：可见正态分布函数采样，比传统GGX采样更高效```glsl
struct Material {
    vec3 albedo;
    float metallic;   // 0=dielectric, 1=metal
    float roughness;  // 0=smooth, 1=rough
};

// GGX normal distribution
float D_GGX(float a2, float NoH) {
    float d = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / (PI * d * d);
}

// Smith occlusion function
float G_Smith(float NoV, float NoL, float a2) {
    float g1 = (2.0 * NoV) / (NoV + sqrt(a2 + (1.0 - a2) * NoV * NoV));
    float g2 = (2.0 * NoL) / (NoL + sqrt(a2 + (1.0 - a2) * NoL * NoL));
    return g1 * g2;
}

// VNDF sampling for importance sampling GGX
vec3 SampleGGXVNDF(vec3 V, float ax, float ay, float r1, float r2) {
    vec3 Vh = normalize(vec3(ax * V.x, ay * V.y, V.z));
    float lensq = Vh.x * Vh.x + Vh.y * Vh.y;
    vec3 T1 = lensq > 0. ? vec3(-Vh.y, Vh.x, 0) * inversesqrt(lensq) : vec3(1, 0, 0);
    vec3 T2 = cross(Vh, T1);
    float r = sqrt(r1);
    float phi = 2.0 * PI * r2;
    float t1 = r * cos(phi), t2 = r * sin(phi);
    float s = 0.5 * (1.0 + Vh.z);
    t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;
    vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0., 1. - t1*t1 - t2*t2)) * Vh;
    return normalize(vec3(ax * Nh.x, ay * Nh.y, max(0., Nh.z)));
}
```当在路径追踪中使用Disney BRDF时，采样策略通常是：
- 使用金属作为在漫反射和镜面反射之间进行选择的概率
- 漫反射使用余弦加权采样
- Specular 使用 VNDF 采样进行 GGX

### 3. 景深

**与基础版本的区别**：使用薄镜头模型来模拟真实相机的散景效果。

薄透镜模型的原理：通过焦点的所有光线会聚到同一点。通过在孔径内随机偏移光线原点，同时保持焦平面上的目标点不变，可以模拟景深效应。```glsl
#define APERTURE 0.12    // Adjustable: aperture size; larger = stronger bokeh
#define FOCUS_DIST 8.0   // Adjustable: focus distance

// In mainImage, after generating the ray:
vec3 focalPoint = ro + rd * FOCUS_DIST;
vec3 offset = ca * vec3(uniformDisk() * APERTURE, 0.);
ro += offset;
rd = normalize(focalPoint - ro);

vec2 uniformDisk() {
    vec2 r = vec2(frand(), frand());
    float a = 6.2831853 * r.x;
    return sqrt(r.y) * vec2(cos(a), sin(a));
}
```参数调整建议：
- `APERTURE`：0.01（几乎没有散景）到 0.5（强散景）
- `FOCUS_DIST`：设置为从相机到您想要清晰对焦的物体的距离
- 散景效果需要更多样本才能收敛（因为添加了额外的随机维度）

### 4. 多重重要性抽样 (MIS)

**与基础版本的区别**：同时使用 BRDF 采样和光源采样，将它们与功率启发式相结合，在所有场景配置中实现低方差。

MIS的核心思想：单一采样策略在某些场景配置中可能具有较高的方差（例如，NEE在光滑表面上表现不佳，BRDF采样在小光源下表现不佳）。 MIS结合了多种策略来弥补彼此的弱点。```glsl
// Power heuristic (beta=2)
float misWeight(float pdfA, float pdfB) {
    float a2 = pdfA * pdfA;
    float b2 = pdfB * pdfB;
    return a2 / (a2 + b2);
}

// During shading, compute both:
// 1. BRDF sampled direction -> if it hits a light, weight with misWeight(brdfPdf, lightPdf)
// 2. Light sampled direction -> weight with misWeight(lightPdf, brdfPdf)
// Sum of both replaces the single sampling strategy
```幂启发式 ($\beta=2$) 公式：$w_A = p_A^2 / (p_A^2 + p_B^2)$。维奇在他的论文中证明这几乎是最优的。

### 5.体积路径追踪（参与媒体）

**与基本版本的区别**：在介质内执行随机游走，通过比尔-朗伯衰减和散射事件模拟半透明/次表面散射效果。

体积渲染的核心概念：
- **消光系数** = 吸收 + 散射
- **比尔-朗伯定律**：透射率 $T = e^{-\sigma_t \cdot d}$
- **散射事件**：散射发生的概率为 $\sigma_s / \sigma_t$（相对于吸收）
- **相位函数**：确定散射方向的分布。均匀球体采样 = 各向同性散射，Henyey-Greenstein = 可控前向/后向散射```glsl
// Beer-Lambert transmittance attenuation
vec3 transmittance = exp(-extinction * distance);

// Random walk scattering
float scatterDist = -log(frand()) / extinctionMajorant;
if (scatterDist < hitDist) {
    // Scattering event occurs
    pos += ray.d * scatterDist;
    // Sample new direction with phase function (e.g., uniform or Henyey-Greenstein)
    ray.d = uniformSphereSample();
    throughput *= albedo; // scattering / extinction
}
```Henyey-Greenstein 相函数：
- [-1, 1] 中的参数 g：g > 0 前向散射，g < 0 后向散射，g = 0 各向同性
- $p(\cos\theta) = \frac{1-g^2}{4\pi(1+g^2-2g\cos\theta)^{3/2}}$

## 性能优化详情

### 1. 抽样策略
每帧每个像素 1-4 个样本，依靠帧间累积进行收敛。这可以保持实时帧速率，同时最终达到高质量。对于 ShaderToy，“SAMPLES_PER_FRAME = 1”或“2”通常是最佳选择，因为每帧更多样本会降低帧速率，而不会加速视觉收敛。

### 2.俄罗斯轮盘赌
从反弹 3-4 开始，使用最大吞吐量分量作为生存概率。这会尽早终止低能量路径，同时保持公正性。```glsl
float p = max(throughput.r, max(throughput.g, throughput.b));
if (frand() > p) break;
throughput /= p;
```数学保证：终止概率$q = 1 - p$，幸存路径吞吐量乘以$1/p$，因此期望值$E[L] = p \cdot L/p + (1-p) \cdot 0 = L$，无偏。

### 3.直接光采样（NEE）
始终明确地对漫反射表面上的光源进行采样，避免依赖于照射光的随机路径。对于小面积光源尤其重要。当光源对着半球立体角的一小部分时，纯 BRDF 采样几乎永远不会照射到光线；东东必不可少。

### 4.避免自相交
沿法线方向偏移交点（epsilon = 1e-3 ~ 1e-4），或记录最后命中的对象 ID 并跳过自交点。两种方法都有权衡：
- 正常偏移：简单且通用，但可能会穿透薄的物体
- ID跳跃：精确，但不适合凹面物体（可能需要自相交）

### 5.萤火虫抑制
使用“min(color, 10.)”限制极端亮度，以防止出现萤火虫噪声点。 ACES 色调映射还有助于压缩高动态范围。萤火虫的根本原因是某些路径找到了高能量但低概率的光传输路径，导致蒙特卡罗估计值极大。

### 6. SDF场景优化
- 限制最大行进步数（128-256）；将超过限制视为未命中
- 设置合理的最大追踪距离（tmax）以剔除远处的物体
- 在反弹期间使用更大的 epsilon（SDF 数值精度通常比解析几何差）
- “松弛球体追踪”可用于在安全时增加步长

### 7. 高质量 PRNG
使用整数哈希（例如 Visual Studio LCG 或 Wang 哈希）而不是 sin-hash 以避免某些 GPU 上出现周期性伪影。 sin-hash 的问题在于不同 GPU 的 sin 精度不同（有些仅使用中p），这会产生可见的结构化噪声。

## 详细组合建议

### 1.路径追踪+SDF建模
使用 SDF 定义复杂的场景几何形状（分形、平滑布尔运算），同时路径追踪处理光照计算。这是 ShaderToy 上最常见的组合。 SDF 的优点是能够轻松创建传统网格（Mandelbulb、Menger 海绵等）难以表达的形状，而路径追踪为这些复杂的几何形状提供物理上精确的照明。

### 2.路径追踪+环境地图
使用 HDR 立方体贴图作为无限远的环境光源。当路径射向天空时，对环境贴图进行采样以获得入射辐射。可以与大气散射模型相结合，以获得物理上更准确的天空。```glsl
// When path misses the scene:
if (!hit) {
    acc += throughput * texture(iChannel1, rd).rgb; // HDR environment map
    break;
}
```### 3.路径追踪+PBR材质
Disney BRDF/BSDF 提供金属/粗糙度参数化材料模型，结合 GGX 微表面分布和 VNDF 重要性采样，以获得生产质量结果。在ShaderToy中，可以按程序生成材质参数（基于位置、噪声等）。

### 4.路径追踪+体积渲染
将参与媒体添加到路径追踪框架中，使用比尔-朗伯定律进行透射，使用随机游走进行散射，以实现云、烟雾、次表面散射等效果。```glsl
// Add volume check in the path tracing loop:
if (insideVolume) {
    float scatterDist = -log(frand()) / sigma_t;
    if (scatterDist < surfaceDist) {
        // Volume scattering event
        x = r.o + r.d * scatterDist;
        r.d = samplePhaseFunction(r.d, g);
        throughput *= sigma_s / sigma_t; // albedo
        continue;
    }
}
```### 5.路径追踪+光谱渲染
每条路径对单个波长而不是 RGB 进行采样，使用 Sellmeier/Cauchy 方程计算与波长相关的折射率，最后通过 CIE XYZ 颜色匹配函数转换为 sRGB。这正确地模拟了色散和彩虹焦散。

基本光谱渲染工作流程：
1. 每条路径随机选择一个波长λ，范围为[380, 780] nm
2. 使用 Sellmeier 方程计算该波长的折射率： $n^2 = 1 + \sum B_i \lambda^2 / (\lambda^2 - C_i)$
3. 路径追踪中的所有颜色计算都变为单通道（该波长处的光谱功率）
4.最后通过CIE XYZ配色函数将光谱辐射亮度转换为XYZ，然后转换为sRGB

### 6.路径追踪+时间累积/TAA
利用 ShaderToy 的帧间缓冲区反馈机制进行渐进式渲染。可以进一步扩展到时间重投影，在相机移动期间重用历史帧数据以加速收敛。

基本时间重投影：
1.存储前一帧的相机矩阵
2. 将当前像素重新投影到前一帧的屏幕空间中
3. 如果位置有效且几何一致，则将历史帧与当前帧混合
4.否则丢弃历史数据并重新开始累加