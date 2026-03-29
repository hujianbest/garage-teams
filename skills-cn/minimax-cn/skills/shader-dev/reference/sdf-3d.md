# 3D 有符号距离场 (3D SDF) — 详细参考

本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、分步解释、数学推导和高级用法。

## 先决条件

- **GLSL 基础**：统一变量（`iTime`、`iResolution`、`iMouse`）、`fragCoord` 坐标系
- **矢量数学**：内置函数，如“dot”、“cross”、“normalize”、“length”、“reflect”
- **光线和相机**：了解如何从屏幕像素生成光线（光线原点+光线方向）
- **隐式曲面概念**：f(p) = 0 定义曲面，f(p) > 0 为外部，f(p) < 0 为内部

## 分步详细说明

### 步骤 1：SDF 基元库

**什么**：定义基本的几何距离函数。

**为什么**：所有SDF场景都是由基本图元组成的。每个图元都是一个纯函数，它获取空间中的一个点并返回到该图元表面的最短距离。这些基元的准确性直接决定了球体追踪的效率——准确的 SDF 允许更大的步长。

**代码**：```glsl
// Sphere: p=sample point, r=radius
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

// Box: p=sample point, b=half-size (xyz dimensions)
float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

// Ellipsoid (approximate): p=sample point, r=three-axis radii
float sdEllipsoid(vec3 p, vec3 r) {
    float k0 = length(p / r);
    float k1 = length(p / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

// Torus: p=sample point, t.x=major radius, t.y=tube radius
float sdTorus(vec3 p, vec2 t) {
    return length(vec2(length(p.xz) - t.x, p.y)) - t.y;
}

// Capsule (two endpoints + radius): useful for skeleton/limb modeling
float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}

// Cylinder (vertical): h.x=radius, h.y=half-height
float sdCylinder(vec3 p, vec2 h) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - h;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

// Plane (y=0)
float sdPlane(vec3 p) {
    return p.y;
}
```### 步骤 2：布尔运算和平滑混合

**什么**：定义基元之间的组合操作 - 并集、减法、交集及其平滑变体。

**为什么**：Union 将多个图元合并到一个场景中；减法将一个物体从另一个物体中雕刻出来；交集保留重叠区域。平滑变体（“smin”/“smax”）使用控制参数“k”来产生平滑的混合过渡——这是 SDF 相对于传统建模最强大的功能之一，无需额外的几何体即可实现有机形式。

**代码**：```glsl
// === Hard Boolean Operations ===

// Union: take the nearer surface
float opUnion(float d1, float d2) { return min(d1, d2); }

// Subtraction: subtract d2 from d1
float opSubtraction(float d1, float d2) { return max(d1, -d2); }

// Intersection: keep the overlapping region
float opIntersection(float d1, float d2) { return max(d1, d2); }

// Union with material ID (vec2.x stores distance, vec2.y stores material ID)
vec2 opU(vec2 d1, vec2 d2) { return (d1.x < d2.x) ? d1 : d2; }

// === Smooth Boolean Operations ===

// Smooth union: k=blend radius (larger = smoother, typical values 0.1~0.5)
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}
// vec2 version of smin: for smooth blending of vec2(distance, materialID)
vec2 smin(vec2 a, vec2 b, float k) {
    float h = max(k - abs(a.x - b.x), 0.0);
    float d = min(a.x, b.x) - h * h * 0.25 / k;
    float m = (a.x < b.x) ? a.y : b.y;
    return vec2(d, m);
}

// Smooth subtraction / smooth max
float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}
```### 步骤 3：场景定义（地图函数）

**什么**：编写`map()`函数，将上述基元和操作组合成一个完整的3D场景。

**为什么**：`map(p)` 是 SDF 渲染管道的核心 - 它返回空间中任意点 p 到最近场景表面的距离（加上可选的材质信息）。光线行进、正常计算、阴影和 AO 都依赖于该函数。场景的所有几何复杂性都封装在这里。

**代码**：```glsl
// Returns vec2(distance, materialID)
vec2 map(vec3 p) {
    // Ground
    vec2 res = vec2(p.y, 0.0); // Material 0: ground

    // Sphere (displaced to y=0.5)
    float d1 = sdSphere(p - vec3(0.0, 0.5, 0.0), 0.4);
    res = opU(res, vec2(d1, 1.0)); // Material 1: sphere

    // Box
    float d2 = sdBox(p - vec3(1.5, 0.4, 0.0), vec3(0.3, 0.4, 0.3));
    res = opU(res, vec2(d2, 2.0)); // Material 2: box

    // Blend two spheres with smin for organic blob effect
    float d3 = sdSphere(p - vec3(-1.2, 0.5, 0.0), 0.3);
    float d4 = sdSphere(p - vec3(-1.5, 0.8, 0.2), 0.25);
    float dBlob = smin(d3, d4, 0.3);
    res = opU(res, vec2(dBlob, 3.0)); // Material 3: blob

    return res;
}
```### 步骤 4：光线行进

**内容**：实现球体跟踪循环 - 从相机投射光线并沿着光线方向步进，直到击中表面或超过最大距离。

**为什么**：球体追踪利用了 SDF 的“安全距离”属性 - 当前的 SDF 值告诉我们在该半径内绝对没有表面，因此我们可以安全地前进那么远。这比固定步长体积射线行进效率高得多，通常在 64-128 步内即可获得精确结果。

**代码**：```glsl
#define MAX_STEPS 128      // Adjustable: step count, 64=fast/coarse, 256=precise/slow
#define MAX_DIST 40.0       // Adjustable: max trace distance
#define SURF_DIST 0.0001    // Adjustable: surface detection threshold

vec2 raycast(vec3 ro, vec3 rd) {
    vec2 res = vec2(-1.0, -1.0);
    float t = 0.01;

    for (int i = 0; i < MAX_STEPS && t < MAX_DIST; i++) {
        vec2 h = map(ro + rd * t);
        if (abs(h.x) < SURF_DIST * t) {
            res = vec2(t, h.y);
            break;
        }
        t += h.x; // Key: step distance = SDF value
    }
    return res; // .x=hit distance, .y=materialID; -1 means no hit
}
```###第五步：正常计算

**什么**：通过采用 SDF 的有限差分梯度来计算命中点处的表面法线。

**为什么**：SDF的梯度方向是表面法线方向。我们使用四面体技巧（4 个“map”调用）而不是中心差异（6 个调用），从而节省性能并避免多次内联“map()”导致编译器内联膨胀。

**代码**：```glsl
// Tetrahedron normal computation (recommended, only 4 map calls)
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(1.0, -1.0) * 0.5773 * 0.0005; // Adjustable: epsilon
    return normalize(
        e.xyy * map(pos + e.xyy).x +
        e.yyx * map(pos + e.yyx).x +
        e.yxy * map(pos + e.yxy).x +
        e.xxx * map(pos + e.xxx).x
    );
}

// Anti-compiler-inline version (suitable for complex map functions)
// Uses a loop to prevent compiler unrolling, uses a loop to prevent compiler unrolling
#define ZERO (min(iFrame, 0))
vec3 calcNormalLoop(vec3 pos) {
    vec3 n = vec3(0.0);
    for (int i = ZERO; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3((((i+3)>>1)&1), ((i>>1)&1), (i&1)) - 1.0);
        n += e * map(pos + 0.0005 * e).x;
    }
    return normalize(n);
}
```### 第 6 步：柔和阴影

**什么**：从表面点向光源投射二次光线，并根据沿途遇到的最小距离估计阴影柔和度。

**为什么**：硬阴影仅确定“被遮挡与否”（0/1），而SDF软阴影则使用中间距离信息来估计“距离被遮挡有多近”。在公式“k*h/t”中，“k”控制阴影柔和度——较大的“k”产生更锐利的阴影，较小的“k”产生更柔和的阴影。这是 SDF 渲染的杀手级功能之一。

**代码**：```glsl
// k=shadow sharpness (2=very soft, 32=near hard), mint=start offset, tmax=max distance
float calcSoftshadow(vec3 ro, vec3 rd, float mint, float tmax, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 24; i++) { // Adjustable: shadow step count
        float h = map(ro + rd * t).x;
        float s = clamp(k * h / t, 0.0, 1.0);
        res = min(res, s);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.004 || t > tmax) break;
    }
    res = clamp(res, 0.0, 1.0);
    return res * res * (3.0 - 2.0 * res); // Smooth Hermite interpolation
}
```### 步骤 7：环境光遮挡 (AO)

**什么**：沿法线方向采样多个点，并将实际 SDF 值与预期距离进行比较，以估计遮挡。

**为什么**：SDF 自然地为廉价的 AO 近似提供距离信息：如果沿法线的采样点处的 SDF 值远小于其到表面的距离，则附近存在遮挡几何体。这种方法比传统的 SSAO 在物理上更准确，并且只需要 5 次“map”调用。

**代码**：```glsl
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) { // Adjustable: number of sample layers
        float h = 0.01 + 0.12 * float(i) / 4.0; // Adjustable: sample spacing
        float d = map(pos + h * nor).x;
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```### 步骤 8：相机和渲染管线

**内容**：构建观察相机矩阵，生成屏幕光线，并将整个渲染管道链接在一起。

**为什么**：将屏幕像素映射到 3D 光线是光线行进的起点。观察矩阵根据摄像机位置、目标点和向上方向构建正交基础，使摄像机控制更加直观。最终的管道链接了所有步骤：光线生成、光线行进、法线、照明/阴影/AO 和后处理。

**代码**：```glsl
// Camera look-at matrix
mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}

// Render: input ray, output color
vec3 render(vec3 ro, vec3 rd) {
    // Background color (sky gradient)
    vec3 col = vec3(0.7, 0.7, 0.9) - max(rd.y, 0.0) * 0.3;

    // Raycast intersection
    vec2 res = raycast(ro, rd);
    float t = res.x;
    float m = res.y; // Material ID

    if (m > -0.5) {
        vec3 pos = ro + t * rd;
        vec3 nor = calcNormal(pos);

        // Material color (varies by ID)
        vec3 mate = 0.2 + 0.2 * sin(m * 2.0 + vec3(0.0, 1.0, 2.0));

        // Lighting
        vec3 lig = normalize(vec3(-0.5, 0.4, -0.6));
        float dif = clamp(dot(nor, lig), 0.0, 1.0);
        dif *= calcSoftshadow(pos, lig, 0.02, 2.5, 8.0);
        float amb = 0.5 + 0.5 * nor.y;
        float occ = calcAO(pos, nor);

        col = mate * (dif * vec3(1.3, 1.0, 0.7) + amb * occ * vec3(0.4, 0.6, 1.0) * 0.6);

        // Fog (exponential decay)
        col = mix(col, vec3(0.7, 0.7, 0.9), 1.0 - exp(-0.0001 * t * t * t));
    }

    return clamp(col, 0.0, 1.0);
}
```## 变体详细说明

### 变体 1：动态有机体（平滑斑点动画）

**与基本版本的区别**：用通过“smin”混合的多个动画球体替换静态基元，产生熔岩/流体般的有机效果。有机流体效果的常用技术。

**关键修改代码**：```glsl
// Replace scene definition in map()
vec2 map(vec3 p) {
    float d = 2.0;
    for (int i = 0; i < 16; i++) { // Adjustable: number of spheres
        float fi = float(i);
        float t = iTime * (fract(fi * 412.531 + 0.513) - 0.5) * 2.0;
        d = smin(
            sdSphere(p + sin(t + fi * vec3(52.5126, 64.627, 632.25)) * vec3(2.0, 2.0, 0.8),
                     mix(0.5, 1.0, fract(fi * 412.531 + 0.5124))),
            d,
            0.4 // Adjustable: blend radius
        );
    }
    return vec2(d, 1.0);
}
```### 变体 2：无限重复走廊（域重复）

**与基本版本的区别**：使用`mod()`无限重复空间坐标。一种常见的域重复技术。可以分层“hash()”以引入每个重复单元的随机变化。

**关键修改代码**：```glsl
// Linear domain repetition
float repeat(float v, float c) {
    return mod(v, c) - c * 0.5;
}

// Angular domain repetition (repeat count times in polar coordinate direction)
float amod(inout vec2 p, float count) {
    float an = 6.283185 / count;
    float a = atan(p.y, p.x) + an * 0.5;
    float c = floor(a / an);
    a = mod(a, an) - an * 0.5;
    p = vec2(cos(a), sin(a)) * length(p);
    return c; // Returns sector index
}

vec2 map(vec3 p) {
    // Repeat every 4 units along the z axis
    p.z = repeat(p.z, 4.0);
    // Add bending offset along x axis
    p.x += 2.0 * sin(p.z * 0.1);

    float d = -sdBox(p, vec3(2.0, 2.0, 20.0)); // Invert = corridor interior
    d = max(d, -sdBox(p, vec3(1.8, 1.8, 1.9))); // Subtract interior space
    d = min(d, sdCylinder(p - vec3(1.5, -2.0, 0.0), vec2(0.1, 2.0))); // Add pillars
    return vec2(d, 1.0);
}
```### 变体 3：角色/生物建模（有机角色建模）

**与基本版本的区别**：使用 `sdEllipsoid` + `sdCapsule` (sdStick) 来组成身体部位，`smin` 来平滑过渡连接，使用 `smax` 来雕刻凹口（嘴）。结合程序动画来驱动关节。角色 SDF 建模的标准方法。

**关键修改代码**：```glsl
// Stick primitive (different radii at each end, suitable for limbs)
vec2 sdStick(vec3 p, vec3 a, vec3 b, float r1, float r2) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return vec2(length(pa - ba * h) - mix(r1, r2, h * h * (3.0 - 2.0 * h)), h);
}

vec2 map(vec3 pos) {
    // Body (ellipsoid)
    float d = sdEllipsoid(pos, vec3(0.25, 0.3, 0.25));

    // Head (sphere, connected with smin)
    float dHead = sdEllipsoid(pos - vec3(0.0, 0.35, 0.02), vec3(0.12, 0.15, 0.13));
    d = smin(d, dHead, 0.1);

    // Arms (sdStick)
    vec2 arm = sdStick(abs(pos.x) > 0.0 ? vec3(abs(pos.x), pos.yz) : pos,
                       vec3(0.18, 0.2, -0.05),
                       vec3(0.35, -0.1, -0.15), 0.03, 0.05);
    d = smin(d, arm.x, 0.04);

    // Mouth (carved with smax)
    float dMouth = sdEllipsoid(pos - vec3(0.0, 0.3, 0.15), vec3(0.08, 0.03, 0.1));
    d = smax(d, -dMouth, 0.03);

    return vec2(d, 1.0);
}
```### 变体 4：对称性利用

**与基本版本的区别**：利用几何对称性（镜像/旋转不变性）将 N 个重复元素的 SDF 评估减少到 N/k。例如，八面体对称性可以将 18 个元素减少到 4 个评估。关键是将输入点映射到对称性的基本域。

**关键修改代码**：```glsl
// Fold a point into the octahedral fundamental domain
vec2 rot45(vec2 v) {
    return vec2(v.x - v.y, v.y + v.x) * 0.707107;
}

vec2 map(vec3 p) {
    float d = sdSphere(p, 0.12); // Center sphere

    // Exploit symmetry: original 18 gears reduced to 4 evaluations
    vec3 qx = vec3(rot45(p.zy), p.x);
    if (abs(qx.x) > abs(qx.y)) qx = qx.zxy;

    vec3 qy = vec3(rot45(p.xz), p.y);
    if (abs(qy.x) > abs(qy.y)) qy = qy.zxy;

    vec3 qz = vec3(rot45(p.yx), p.z);
    if (abs(qz.x) > abs(qz.y)) qz = qz.zxy;

    vec3 qa = abs(p);
    qa = (qa.x > qa.y && qa.x > qa.z) ? p.zxy :
         (qa.z > qa.y) ? p.yzx : p.xyz;

    // Only 4 gear() evaluations needed instead of 18
    d = min(d, gear(qa, 0.0));
    d = min(d, gear(qx, 1.0));
    d = min(d, gear(qy, 1.0));
    d = min(d, gear(qz, 1.0));

    return vec2(d, 1.0);
}
```### 变体 5：PBR 材质渲染管道

**与基本版本的区别**：用 GGX 微面 BRDF 替换简化的 Blinn-Phong，结合材质 ID 系统为每个图元分配不同的粗糙度/金属度。 PBR 光线行进的标准方法。

**关键修改代码**：```glsl
// GGX/Trowbridge-Reitz NDF
float D_GGX(float NoH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float d = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / (3.14159 * d * d);
}

// Schlick Fresnel approximation
vec3 F_Schlick(float VoH, vec3 f0) {
    return f0 + (1.0 - f0) * pow(1.0 - VoH, 5.0);
}

// Replace lighting section in render()
vec3 pbrLighting(vec3 pos, vec3 nor, vec3 rd, vec3 albedo, float roughness, float metallic) {
    vec3 lig = normalize(vec3(-0.5, 0.4, -0.6));
    vec3 hal = normalize(lig - rd);
    vec3 f0 = mix(vec3(0.04), albedo, metallic);

    float NoL = max(dot(nor, lig), 0.0);
    float NoH = max(dot(nor, hal), 0.0);
    float VoH = max(dot(-rd, hal), 0.0);

    float D = D_GGX(NoH, roughness);
    vec3 F = F_Schlick(VoH, f0);

    vec3 spec = D * F * 0.25; // Simplified specular term
    vec3 diff = albedo * (1.0 - metallic) / 3.14159;

    float shadow = calcSoftshadow(pos, lig, 0.02, 2.5);
    return (diff + spec) * NoL * shadow * vec3(1.3, 1.0, 0.7) * 3.0;
}
```## 性能优化细节

### 1. 包围体加速

使用整体 AABB 或边界球来约束搜索范围。首先执行分析射线相交以缩小“tmin”/“tmax”范围，避免在空白区域中浪费步骤。高级光线行进着色器中的常见优化。```glsl
// Ray-AABB intersection (call before raycast)
vec2 iBox(vec3 ro, vec3 rd, vec3 rad) {
    vec3 m = 1.0 / rd;
    vec3 n = m * ro;
    vec3 k = abs(m) * rad;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    return vec2(max(max(t1.x, t1.y), t1.z),
                min(min(t2.x, t2.y), t2.z));
}
```### 2. 每个对象的边界

在“map()”中，首先使用廉价的 sdBox 检查当前点是否靠近图元。仅在接近时计算精确的 SDF。标准的每对象剔除技术。```glsl
// Inside map():
if (sdBox(pos - objectCenter, boundingSize) < res.x) {
    // Only compute precise SDF when bounding box distance is closer than current nearest
    res = opU(res, vec2(sdComplexShape(pos), matID));
}
```### 3.自适应步长

远距离时允许较大的精度公差，近距离时允许更严格的精度公差。基于几乎所有高级着色器中发现的“abs(h.x) < (0.0001 * t)”检查。

### 4. 防止编译器内联

复杂的“map()”函数在“calcNormal”中内联了 4 次，导致编译时间激增。使用循环+“ZERO”宏来防止内联。防止过度编译器内联的众所周知的技术。```glsl
#define ZERO (min(iFrame, 0)) // Compiler cannot prove this is 0 at compile time, so it won't unroll the loop
```### 5. 对称性利用

如果场景具有旋转/镜像对称性，则将该点折叠到基本域中并仅评估一次。实现显着的加速（例如，18 比 4 减少）或无限重复。

## 详细组合建议

### 1.SDF + 噪声位移

在“map()”返回值之上添加噪声，以将有机细节添加到平滑表面（地形、皮肤纹理）。```glsl
float d = sdSphere(p, 1.0);
d += 0.05 * (sin(p.x * 10.0) * sin(p.y * 10.0) * sin(p.z * 10.0)); // Simple displacement
// Or use fbm noise: d += 0.1 * fbm(p * 4.0);
```**注意**：噪声位移打破了 SDF 的 Lipschitz 条件 (|grad f| <= 1)。您需要将步长乘以安全系数（例如0.5~0.7）以避免穿透。

### 2.SDF + 凹凸贴图

仅在正常计算中添加细节扰动，而不是修改 SDF 本身。性能比噪声位移更好，因为它不影响光线行进。 SDF 渲染中的一种常用技术。```glsl
vec3 calcNormalBumped(vec3 pos) {
    vec3 n = calcNormal(pos);
    // Add high-frequency detail to the normal
    n += 0.1 * vec3(fbm(pos.yz * 20.0) - 0.5, 0.0, fbm(pos.xy * 20.0) - 0.5);
    return normalize(n);
}
```### 3.SDF + 域扭曲

在进入`map()`之前扭曲空间坐标，以实现弯曲、扭曲、极坐标变换等效果。一种常见的空间扭曲技术。```glsl
// Cartesian to polar ring space: straight corridor becomes a ring structure
vec2 displaceLoop(vec2 p, float r) {
    return vec2(length(p) - r, atan(p.y, p.x));
}
```### 4.SDF + 程序动画

骨骼/关节角度随时间变化，驱动 SDF 原始位置。 `smin` 确保关节处的平滑过渡。程序角色动画的常用技术（挤压和拉伸、骨链 IK）。```glsl
// Squash and stretch deformation
float p = 4.0 * t1 * (1.0 - t1); // Parabolic bounce
float sy = 0.5 + 0.5 * p;        // Stretch in y direction
float sz = 1.0 / sy;              // Compress in z direction (preserve volume)
vec3 q = pos - center;
float d = sdEllipsoid(q, vec3(0.25, 0.25 * sy, 0.25 * sz));
```### 5.SDF + 运动模糊

跨时间维度采样的平均多个帧。标准时间超级采样技术。```glsl
// Randomly offset time in mainImage
float time = iTime;
#if AA > 1
    time += 0.5 * float(m * AA + n) / float(AA * AA) / 24.0; // Intra-frame time jitter
#endif
```## 扩展 SDF 基元参考

### 圆角框 — `sdRoundBox(vec3 p, vec3 b, float r)`

- `p`: 样本点
- `b`：半尺寸尺寸（四舍五入之前）
- `r`：圆角半径 — 边缘和拐角按此值圆角化

### 框框架 — `sdBoxFrame(vec3 p, vec3 b, float e)`

- `p`: 样本点
- `b`：外部半尺寸尺寸
- `e`: 边缘厚度 — 盒子边缘的线框厚度

### 锥体 — `sdCone(vec3 p, vec2 c, float h)`

- `p`: 样本点
- `c`: 锥体张角的 vec2(sin, cos)
- `h`：圆锥体的高度

### 封顶锥 — `sdCappedCone(vec3 p, float h, float r1, float r2)`

- `p`: 样本点
- `h`：半高
- `r1`：底部半径
- `r2`：顶部半径

### 圆锥 — `sdRoundCone(vec3 p, float r1, float r2, float h)`

- `p`: 样本点
- `r1`：底部球体半径
- `r2`：顶部球体半径
- `h`：球心之间的高度

### 立体角 — `sdSolidAngle(vec3 p, vec2 c, float ra)`

- `p`: 样本点
- `c`: 立体角的 vec2(sin, cos)
- `ra`: 半径

### 八面体 — `sdOctahedron(vec3 p, float s)`

- `p`: 样本点
- `s`：尺寸（从中心到顶点的距离）

### 金字塔 — `sdPyramid(vec3 p, float h)`

- `p`: 样本点
- `h`：金字塔的高度（底面是以原点为中心的单位正方形）

### 六角棱镜 — `sdHexPrism(vec3 p, vec2 h)`

- `p`: 样本点
- `h.x`：六边形半径（圆周半径）
- `h.y`：沿 z 轴的半高

### 切割球体 — `sdCutSphere(vec3 p, float r, float h)`

- `p`: 样本点
- `r`：球体半径
- `h`：切割平面高度（在 y=h 处切割球体）

### Capped Torus — `sdCappedTorus(vec3 p, vec2 sc, float ra, float rb)`

- `p`: 样本点
- `sc`: 顶角的 vec2(sin, cos)
- `ra`: 大半径
- `rb`：管半径

### 链接 — `sdLink(vec3 p, float le, float r1, float r2)`

- `p`: 样本点
- `le`: 伸长率的一半
- `r1`：圆环横截面的主半径
- `r2`：管半径

### 平面（任意） — `sdPlane(vec3 p, vec3 n, float h)`

- `p`: 样本点
- `n`：平面法线（必须标准化）
- `h`：沿法线从原点偏移

### 菱形 — `sdRhombus(vec3 p, float la, float lb, float h, float ra)`

- `p`: 样本点
- `la`、`lb`：XZ 平面中菱形的半对角线
- `h`：半高（Y 方向拉伸）
- `ra`：圆角半径

### 三角形（无符号）— `udTriangle(vec3 p, vec3 a, vec3 b, vec3 c)`

- `p`: 样本点
- `a`、`b`、`c`：三角形顶点位置
- 返回无符号（非负）距离

## 变形算子参考

### Round — `opRound(float d, float r)`

通过减去半径来软化任何 SDF 的边缘。适用于任何 SDF 的结果。```glsl
// Round a box with radius 0.1
float d = opRound(sdBox(p, vec3(1.0)), 0.1);
```### 洋葱 — `opOnion(float d, float t)`

将任何 SDF 挖空成厚度为“t”的壳。可以堆叠成同心壳。```glsl
// Hollow sphere shell, 0.1 thick
float d = opOnion(sdSphere(p, 1.0), 0.1);
// Double shell
float d = opOnion(opOnion(sdSphere(p, 1.0), 0.1), 0.05);
```### 延长 — `opElongate(vec3 p, vec3 h, vec3 中心, vec3 大小)`

沿一个或多个轴将形状拉伸“h”。形状被拉伸而不变形——它插入了一个线性段。```glsl
// Elongate along Y to stretch a box
vec3 q = abs(p) - vec3(0.0, 0.5, 0.0);
float d = sdBox(max(q, 0.0), vec3(0.3)) + min(max(q.x, max(q.y, q.z)), 0.0);
```### Twist — `opTwist(vec3 p, float k)`

绕 Y 轴按高度比例旋转 XZ 横截面。返回转换后的坐标以传递到任何 SDF 中。```glsl
// Twisted box: k controls twist rate (radians per unit height)
vec3 q = opTwist(p, 3.0);
float d = sdBox(q, vec3(0.5));
```### 廉价弯曲 — `opCheapBend(vec3 p, float k)`

沿 X 轴弯曲几何体。返回转换后的坐标。```glsl
// Bent box
vec3 q = opCheapBend(p, 2.0);
float d = sdBox(q, vec3(0.5, 0.3, 0.5));
```### 位移 — `opDisplace(float d, vec3 p)`

添加程序正弦曲面细节。打破 Lipschitz 约束，因此将射线行进步长减小 0.5-0.7。```glsl
float d = sdSphere(p, 1.0);
d = opDisplace(d, p); // Adds bumpy surface detail
```## 2D 到 3D 构造函数参考

### Revolution — `opRevolution(vec3 p, float sdf2d_result, float o)`

通过绕 Y 轴旋转 2D SDF 创建 3D 旋转实体。计算“vec2(length(p.xz) - o, p.y)”处的 2D SDF 并传递结果。```glsl
// Create a torus-like shape by revolving a 2D circle
vec2 q = vec2(length(p.xz) - 1.0, p.y); // offset=1.0
float d2d = length(q) - 0.3;             // 2D circle radius=0.3
float d3d = opRevolution(p, d2d, 1.0);   // revolve around Y
```### 挤出 — `opExtrusion(vec3 p, float d2d, float h)`

沿 Z 轴以有限高度“h”延伸任何 2D SDF。 2D SDF 在 XY 平面中进行评估，并沿 Z 方向限制为“+/- h”。```glsl
// Extrude a 2D shape 0.2 units in both directions
float d2d = sdCircle2D(p.xy, 0.5);      // any 2D SDF
float d3d = opExtrusion(p, d2d, 0.2);    // finite extrusion
```## 对称运算符参考

### 镜像 X — `opSymX(vec3 p)`

使用“abs(p.x)”沿 X 轴进行镜像。仅建模一半并免费获得双边对称。放置在`map()`的开头。```glsl
vec2 map(vec3 p) {
    p = opSymX(p); // Mirror: only model x >= 0 side
    float d = sdSphere(p - vec3(1.0, 0.5, 0.0), 0.3);
    // Automatically appears at both x=+1 and x=-1
    return vec2(d, 1.0);
}
```### 镜像 XZ — `opSymXZ(vec3 p)`

X 轴和 Z 轴四重对称。模型一个象限，得到四份。```glsl
vec2 map(vec3 p) {
    p = opSymXZ(p); // Four-fold symmetry
    float d = sdBox(p - vec3(2.0, 0.5, 2.0), vec3(0.3));
    // Appears in all four quadrants
    return vec2(d, 1.0);
}
```### 任意镜像 — `opMirror(vec3 p, vec3 dir)`

跨越由其法线“dir”定义的任意平面的镜像（必须标准化）。将负侧的任意点反映到正侧。```glsl
// Mirror across a 45-degree plane
vec3 q = opMirror(p, normalize(vec3(1.0, 0.0, 1.0)));
float d = sdSphere(q - vec3(1.0, 0.5, 0.0), 0.3);
```
