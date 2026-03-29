# 分析光线追踪 - 详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，涵盖必备知识、分步教程、数学推导和高级用法。

## 先决条件

- **向量数学基础**：点积`dot()`、叉积`cross()`、向量归一化`normalize()`
- **二次方程求解**：判别式`b²-4ac`，两个根的含义
- **射线参数表示**：`P(t) = ro + t * rd`，其中`ro`是射线原点，`rd`是方向，`t`是距离
- **GLSL 基础**：`struct`、`inout` 参数、`vec3`/`vec4` 操作
- **ShaderToy 框架**：`mainImage()` 函数、`iResolution`、`iTime` 和其他制服

## 用例（完整列表）

- 渲染由几何基元（球体、平面、盒子、圆柱体、圆环等）组成的场景时
- 当需要精确的表面交点、法线和距离时（不需要迭代近似）
- 实时渲染中需要高效的光线交叉时（比光线行进快几倍）
- 为光线追踪器和路径追踪器构建底层几何引擎
- 为硬表面建模创建可视化效果（珠宝、机械零件、国际象棋场景等）
- 需要精确阴影、反射和折射的场景（解析解没有采样误差）

## 核心原则详细信息

解析射线追踪的核心思想是：将射线方程“P(t)=O+tD”代入几何体的隐式方程，得到“t”中的代数方程，然后用闭式公式求解。

### 统一框架

所有解析交集函数都遵循相同的模式：

1. **建立方程**：将射线参数形式代入几何的隐式方程
2. **简化并求解**：使用代数恒等式简化为标准形式（二次/四次方程）
3. **判别式检查**：判别式<0表示没有交集
4. **选择最近交点**：取满足距离约束的最小正根
5. **计算法线**：计算交点处隐式方程的梯度

### 关键数学公式

**球体** `|P-C|² = r²` → 二次方程：`t² + 2bt + c = 0`

**平面** `N·P + d = 0` → 线性方程：`t = -(N·O + d) / (N·D)`

**Box** 三对平行平面的交点 → Slab 方法：`tN = max(t1.x, t1.y, t1.z), tF = min(t2.x, t2.y, t2.z)`

**椭球** `|P/R|² = 1` → 缩放空间中的球体相交

**环面** `(|P_xy| - R)² + P_z² = r²` → 四次方程，通过解析三次方程求解

## 详细实施步骤

### 第 1 步：射线生成

**什么**：从相机位置通过每个像素生成一条光线。

**为什么**：这是光线追踪的起点。每个像素对应于从相机穿过近平面的光线。标准方法是构建相机坐标系（右、上、前）并将标准化屏幕坐标映射到世界空间方向。```glsl
// Construct camera ray
vec3 generateRay(vec2 fragCoord, vec2 resolution, vec3 ro, vec3 ta) {
    vec2 p = (2.0 * fragCoord - resolution) / resolution.y;

    // Build camera coordinate system
    vec3 cw = normalize(ta - ro);               // forward
    vec3 cu = normalize(cross(cw, vec3(0, 1, 0))); // right
    vec3 cv = cross(cu, cw);                    // up

    float fov = 1.5; // Adjustable: field of view control (larger = narrower angle)
    vec3 rd = normalize(p.x * cu + p.y * cv + fov * cw);
    return rd;
}
```### 步骤 2：光线球体相交

**什么**：计算射线与球体的精确交点。这是最基本、最常用的交集函数。

**为什么**：将射线“P = O + tD”代入球方程“|P - C|² = r²”并展开，得到“t”的二次方程。判别式“h = b² - c”确定交叉点的数量（0、1 或 2）；最小的正根是最近的交点。

这是一种普遍存在的技术，有两种常见的变体：

**代码（优化版本，假设球体以原点为中心）**：```glsl
// Ray-sphere intersection (optimized version for sphere at origin)
// ro: ray origin (sphere center offset already subtracted)
// rd: ray direction (must be normalized)
// r:  sphere radius
// Returns: intersection distance, MAX_DIST if no intersection
float iSphere(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float h = b * b - c;       // Discriminant (optimized: 4a factor omitted)
    if (h < 0.0) return MAX_DIST; // No intersection

    h = sqrt(h);
    float d1 = -b - h;        // Near intersection
    float d2 = -b + h;        // Far intersection

    // Select the nearest intersection within valid range
    if (d1 >= distBound.x && d1 <= distBound.y) {
        normal = normalize(ro + rd * d1);
        return d1;
    } else if (d2 >= distBound.x && d2 <= distBound.y) {
        normal = normalize(ro + rd * d2);
        return d2;
    }
    return MAX_DIST;
}
```**代码（通用版，任意球心）**：```glsl
// Ray-sphere intersection (general version, supports arbitrary sphere center)
// sph: vec4(center.xyz, radius)
float sphIntersect(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    if (h < 0.0) return -1.0;
    return -b - sqrt(h);  // Returns only the near intersection
}
```### 步骤 3：光线平面相交

**什么**：计算射线与无限平面的交点。

**为什么**：用射线代替平面方程“N·P + d = 0”产生线性方程，直接通过除法求解。这是最简单的相交图元，常用于地板、墙壁、康奈尔盒子等。注意：当`N·D ≈ 0`时，射线平行于平面。```glsl
// Ray-plane intersection
// planeNormal: plane normal (must be normalized)
// planeDist:   distance from plane to origin (N·P + planeDist = 0)
float iPlane(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
             vec3 planeNormal, float planeDist) {
    float denom = dot(rd, planeNormal);
    // Only intersects when ray hits the front face of the plane
    if (denom > 0.0) return MAX_DIST;

    float d = -(dot(ro, planeNormal) + planeDist) / denom;

    if (d < distBound.x || d > distBound.y) return MAX_DIST;

    normal = planeNormal;
    return d;
}

// Quick version: horizontal ground plane (y-axis aligned)
float iGroundPlane(vec3 ro, vec3 rd, float height) {
    return -(ro.y - height) / rd.y;
}
```### 步骤 4：Ray-Box 相交（板法）

**什么**：计算射线与轴对齐边界框 (AABB) 的交点。

**为什么**：板法将盒子视为三对平行平面的交集。它计算射线与每对平面“(tmin, tmax)”的交点，然后取所有“tmin”值的最大值和所有“tmax”值的最小值。如果“tN > tF”或“tF < 0”，则不存在交集。法线由先被击中的面决定。```glsl
// Ray-box intersection (Slab Method, optimized version)
// boxSize: box half-size vec3(halfW, halfH, halfD)
float iBox(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 boxSize) {
    vec3 m = sign(rd) / max(abs(rd), 1e-8); // Avoid division by zero
    vec3 n = m * ro;
    vec3 k = abs(m) * boxSize;

    vec3 t1 = -n - k;  // Near plane intersections
    vec3 t2 = -n + k;  // Far plane intersections

    float tN = max(max(t1.x, t1.y), t1.z); // Entry distance into the box
    float tF = min(min(t2.x, t2.y), t2.z); // Exit distance from the box

    if (tN > tF || tF <= 0.0) return MAX_DIST; // No intersection

    if (tN >= distBound.x && tN <= distBound.y) {
        // Normal: determine which face was hit
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tN;
    } else if (tF >= distBound.x && tF <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tF;
    }
    return MAX_DIST;
}
```### 步骤 5：射线与椭球体相交

**什么**：计算射线与椭球体的交集。

**为什么**：椭球体可以被视为沿每个轴缩放不同的球体。通过将光线原点和方向除以椭球半径“R”，在缩放空间中执行球体相交，然后将法线变换回原始空间。这种“空间变换”技术是分析交集的核心思想之一。```glsl
// Ray-ellipsoid intersection
// rad: vec3(rx, ry, rz) three-axis radii
float iEllipsoid(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 rad) {
    // Transform to unit sphere space
    vec3 ocn = ro / rad;
    vec3 rdn = rd / rad;

    float a = dot(rdn, rdn);
    float b = dot(ocn, rdn);
    float c = dot(ocn, ocn);
    float h = b * b - a * (c - 1.0);

    if (h < 0.0) return MAX_DIST;

    float d = (-b - sqrt(h)) / a;

    if (d < distBound.x || d > distBound.y) return MAX_DIST;

    // Normal in original space: gradient of implicit equation |P/R|²=1 → P/(R²)
    normal = normalize((ro + d * rd) / rad);
    return d;
}
```### 第 6 步：射线与柱面相交

**什么**：计算射线与有限圆柱体（带端盖）的交集。

**为什么**：圆柱相交有两个部分：（1）将问题投影到垂直于轴的平面上，求解侧面相交的二次方程； (2) 检查交点是否在有限长度内，如果不在有限长度内，则测试端盖平面。```glsl
// Ray-capped cylinder intersection
// pa, pb: two endpoints of the cylinder axis
// ra: cylinder radius
float iCylinder(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
                vec3 pa, vec3 pb, float ra) {
    vec3 ca = pb - pa;          // Cylinder axis vector
    vec3 oc = ro - pa;

    float caca = dot(ca, ca);
    float card = dot(ca, rd);
    float caoc = dot(ca, oc);

    // Project onto plane perpendicular to axis, build quadratic equation
    float a = caca - card * card;
    float b = caca * dot(oc, rd) - caoc * card;
    float c = caca * dot(oc, oc) - caoc * caoc - ra * ra * caca;
    float h = b * b - a * c;

    if (h < 0.0) return MAX_DIST;

    h = sqrt(h);
    float d = (-b - h) / a;

    // Check if side intersection is within finite length
    float y = caoc + d * card;
    if (y > 0.0 && y < caca && d >= distBound.x && d <= distBound.y) {
        normal = (oc + d * rd - ca * y / caca) / ra;
        return d;
    }

    // Test end caps
    d = ((y < 0.0 ? 0.0 : caca) - caoc) / card;
    if (abs(b + a * d) < h && d >= distBound.x && d <= distBound.y) {
        normal = normalize(ca * sign(y) / caca);
        return d;
    }

    return MAX_DIST;
}
```### 第 7 步：场景交叉和着色

**什么**：遍历场景中的所有对象，找到最近的交叉点，并计算光照。

**为什么**：分析光线追踪中的场景遍历是线性的 - 每条光线按顺序测试所有对象。通过统一的交集API（`distBound`参数），每次发现较近的交集时，搜索范围自动缩短，实现隐式剔除。```glsl
#define MAX_DIST 1e10

// Unified scene intersection function
// Returns vec3(current nearest distance, final intersection distance, material ID)
vec3 worldHit(vec3 ro, vec3 rd, vec2 dist, out vec3 normal) {
    vec3 d = vec3(dist, 0.0); // (distBound.x, distBound.y, matID)
    vec3 tmpNormal;

    // Ground plane
    float t = iPlane(ro, rd, d.xy, normal, vec3(0, 1, 0), 0.0);
    if (t < d.y) { d.y = t; d.z = 1.0; }

    // Sphere
    t = iSphere(ro - vec3(0, 0.5, 0), rd, d.xy, tmpNormal, 0.5);
    if (t < d.y) { d.y = t; d.z = 2.0; normal = tmpNormal; }

    // Box
    t = iBox(ro - vec3(2, 0.5, 0), rd, d.xy, tmpNormal, vec3(0.5));
    if (t < d.y) { d.y = t; d.z = 3.0; normal = tmpNormal; }

    return d;
}

// Basic shading (Lambertian + shadow)
vec3 shade(vec3 pos, vec3 normal, vec3 rd, vec3 albedo) {
    vec3 lightDir = normalize(vec3(-1.0, 0.75, 1.0));

    // Diffuse
    float diff = max(dot(normal, lightDir), 0.0);

    // Ambient
    float amb = 0.5 + 0.5 * normal.y;

    return albedo * (amb * 0.2 + diff * 0.8);
}
```### 步骤 8：反射和折射

**什么**：实现非递归光线反弹的迭代反射/折射。

**为什么**：GLSL不支持递归，所以用循环来模拟多次反弹。每次反弹时，交点加上偏移量 (epsilon) 作为新的光线原点，反射/折射方向作为新方向。菲涅耳项决定了反射和折射之间的能量分布。```glsl
#define MAX_BOUNCES 4       // Adjustable: number of reflection bounces (more = more realistic but slower)
#define EPSILON 0.001        // Adjustable: self-intersection offset

// Schlick Fresnel approximation
float schlickFresnel(float cosTheta, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 radiance(vec3 ro, vec3 rd) {
    vec3 color = vec3(0.0);
    vec3 mask = vec3(1.0);
    vec3 normal;

    for (int i = 0; i < MAX_BOUNCES; i++) {
        vec3 res = worldHit(ro, rd, vec2(EPSILON, MAX_DIST), normal);

        if (res.z < 0.5) {
            // No object hit → sky color
            color += mask * vec3(0.6, 0.8, 1.0);
            break;
        }

        vec3 hitPos = ro + rd * res.y;
        vec3 albedo = getAlbedo(res.z);

        // Fresnel reflection coefficient
        float F = schlickFresnel(max(0.0, dot(normal, -rd)), 0.04);

        // Add diffuse contribution
        color += mask * (1.0 - F) * shade(hitPos, normal, rd, albedo);

        // Update mask and ray (reflection)
        mask *= F * albedo;
        rd = reflect(rd, normal);
        ro = hitPos + EPSILON * rd;
    }

    return color;
}
```## 完整的代码模板

有关完整的可运行 ShaderToy 模板，请参阅 [SKILL.md](SKILL.md) 中的“完整代码模板”部分，其中包括支持反射和 Blinn-Phong 着色的球体、平面和长方体基元。

模板中可调整参数如下表：

|参数|默认 |描述 |
|------------|---------|-------------|
| `最大距离` | `1e10` |最大走线距离|
| '厄普西隆' | `0.001` |自相交偏移 |
| `MAX_BOUNCES` | `4` |最大反射次数|
| `NUM_SPHERES` | `3` |球体数量|
| `FOV` | `1.5` |视野（更大=更窄的角度）|
| `伽玛` | `2.2` |伽玛校正值|
| `SHADOW_ENABLED` | `真实` |是否启用阴影 |

## 变体详细信息

### 变体 1：路径追踪

与基础版本的区别：用随机半球采样代替确定性反射，实现全局照明。需要多帧累加和随机数生成。

关键代码：```glsl
// Cosine-weighted random hemisphere direction
vec3 cosWeightedRandomHemisphereDirection(vec3 n, inout float seed) {
    vec2 r = hash2(seed);
    vec3 uu = normalize(cross(n, abs(n.y) > 0.5 ? vec3(1,0,0) : vec3(0,1,0)));
    vec3 vv = cross(uu, n);
    float ra = sqrt(r.y);
    float rx = ra * cos(6.2831 * r.x);
    float ry = ra * sin(6.2831 * r.x);
    float rz = sqrt(1.0 - r.y);
    return normalize(rx * uu + ry * vv + rz * n);
}

// Replace reflect in the bounce loop:
rd = cosWeightedRandomHemisphereDirection(normal, seed);
ro = hitPos + EPSILON * rd;
mask *= mat.albedo; // No Fresnel weighting
```### 变体 2：分析软阴影

与基本版本的区别：使用从球体到射线的分析距离来计算软阴影渐变，无需额外采样。

关键代码：```glsl
// Sphere soft shadow
float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    // d: closest distance from ray to sphere surface, t: distance along ray
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    float t = -b - sqrt(max(h, 0.0));
    return (t > 0.0) ? max(d, 0.0) / t : 1.0;
}
```### 变体 3：分析抗锯齿

与基础版本的区别：使用球体到射线的解析距离来计算像素覆盖范围，无需多次采样即可实现边缘平滑。

关键代码：```glsl
// Sphere distance information (for antialiasing)
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w; // Closest distance
    return vec2(d, -b - sqrt(max(h, 0.0)));                // (distance, depth)
}

// In rendering, use coverage instead of hard boundary:
float px = 2.0 / iResolution.y; // Pixel size
vec2 dt = sphDistances(ro, rd, sph);
float coverage = 1.0 - clamp(dt.x / (dt.y * px), 0.0, 1.0);
col = mix(bgColor, sphereColor, coverage);
```### 变体 4：折射（使用斯涅尔定律）

与基础版本的区别：增加了折射光线；需要检测光线是从外部还是内部撞击表面，并相应地翻转法线。

关键代码：```glsl
float refrIndex = 1.5; // Adjustable: index of refraction (glass≈1.5, water≈1.33)

// Add refraction branch in the bounce loop:
bool inside = dot(rd, normal) > 0.0;
vec3 n = inside ? -normal : normal;
float eta = inside ? refrIndex : 1.0 / refrIndex;
vec3 refracted = refract(rd, n, eta);

// Fresnel determines reflection/refraction ratio
float cosI = abs(dot(rd, n));
float F = schlick(cosI, pow((1.0 - eta) / (1.0 + eta), 2.0));

if (refracted != vec3(0.0) && hash1(seed) > F) {
    rd = refracted;
} else {
    rd = reflect(rd, n);
}
ro = hitPos + rd * EPSILON;
```### 变体 5：高阶代数曲面（四次曲面 - Sphere4、Goursat、Torus）

与基础版本的区别：将射线代入四次方程，通过求解三次方程求解。适用于环面、超椭球体和类似形状。

关键代码：```glsl
// Ray-Sphere4 intersection (|x|⁴+|y|⁴+|z|⁴ = r⁴)
float iSphere4(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float ra) {
    float r2 = ra * ra;
    vec3 d2 = rd*rd, d3 = d2*rd;
    vec3 o2 = ro*ro, o3 = o2*ro;
    float ka = 1.0 / dot(d2, d2);

    float k0 = ka * dot(ro, d3);
    float k1 = ka * dot(o2, d2);
    float k2 = ka * dot(o3, rd);
    float k3 = ka * (dot(o2, o2) - r2 * r2);

    // Reduce to depressed quartic, solve via resolvent cubic
    float c0 = k1 - k0 * k0;
    float c1 = k2 + 2.0 * k0 * (k0 * k0 - 1.5 * k1);
    float c2 = k3 - 3.0 * k0 * (k0 * (k0 * k0 - 2.0 * k1) + 4.0/3.0 * k2);

    float p = c0 * c0 * 3.0 + c2;
    float q = c0 * c0 * c0 - c0 * c2 + c1 * c1;
    float h = q * q - p * p * p * (1.0/27.0);

    if (h < 0.0) return MAX_DIST; // Convex body: only need to handle 2 real roots case

    h = sqrt(h);
    float s = sign(q+h) * pow(abs(q+h), 1.0/3.0);
    float t = sign(q-h) * pow(abs(q-h), 1.0/3.0);

    vec2 v = vec2((s+t) + c0*4.0, (s-t) * sqrt(3.0)) * 0.5;
    float r = length(v);
    float d = -abs(v.y) / sqrt(r + v.x) - c1/r - k0;

    if (d >= distBound.x && d <= distBound.y) {
        vec3 pos = ro + rd * d;
        normal = normalize(pos * pos * pos); // Gradient: 4x³
        return d;
    }
    return MAX_DIST;
}
```## 性能优化详情

### 1.距离限制修剪

最重要的优化。每次找到更近的交点时，`distBound.y`都会被缩短，并且自动跳过后续对象：```glsl
// distBound.y continuously shrinks with opU
d = opU(d, iSphere(..., d.xy, ...), matId);
d = opU(d, iBox(..., d.xy, ...), matId);   // Automatically skips objects farther than current hit
```### 2. 边界球/边界框预测试

对于复杂的几何形状（环面、Goursat 曲面等），首先测试一个简单的边界球以检查可能的相交：```glsl
// Test bounding sphere before torus intersection
if (iSphere(ro, rd, distBound, tmpNormal, torus.x + torus.y) > distBound.y) {
    return MAX_DIST; // Bounding sphere missed, skip expensive quartic equation
}
```### 3. 暗影射线提前退出

阴影检测只需要知道“是否有遮挡物”，而不是最近的交叉点，因此可以使用简化的交叉点函数：```glsl
// Fast sphere occlusion test (only checks for intersection, no normal computation)
float fastSphIntersect(vec3 ro, vec3 rd, vec3 center, float r) {
    vec3 v = ro - center;
    float b = dot(v, rd);
    float c = dot(v, v) - r * r;
    float d = b * b - c;
    if (d > 0.0) {
        float t = -b - sqrt(d);
        if (t > 0.0) return t;
        t = -b + sqrt(d);
        if (t > 0.0) return t;
    }
    return -1.0;
}
```### 4.网格加速结构

对于大量相同的基元（例如，数百个球体），使用空间网格来加速光线遍历：```glsl
// 3D DDA grid traversal (for scenes with many spheres)
vec3 pos = floor(ro / GRIDSIZE) * GRIDSIZE;
vec3 ri = 1.0 / rd;
vec3 rs = sign(rd) * GRIDSIZE;
vec3 dis = (pos - ro + 0.5 * GRIDSIZE + rs * 0.5) * ri;

for (int i = 0; i < MAX_STEPS; i++) {
    // Test spheres in current cell
    testSphereInGrid(pos.xz, ro, rd, ...);
    // DDA step to next cell
    vec3 mm = step(dis.xyz, dis.zyx);
    dis += mm * rs * ri;
    pos += mm * rs;
}
```### 5. 避免不必要的 sqrt

当判别式为负数时尽早返回，避免对负数使用“sqrt()”。在某些场景下，判别式的符号可以用于粗预过滤：```glsl
// Check if ray is heading toward sphere and not inside it
if (c > 0.0 && b > 0.0) return MAX_DIST; // Fast cull
```## 详细组合建议

### 1. 分析交集 + Raymarching SDF

对大型简单几何体（地面、边界框）使用分析基元，对复杂细节（分形、平滑布尔运算）使用 SDF 光线行进。分析交叉提供精确的起始/结束距离，加速行进收敛：```glsl
float d = iBox(ro, rd, distBound, normal, boxSize); // Analytic box
if (d < MAX_DIST) {
    // Refine with SDF inside the box
    float t = d;
    for (int i = 0; i < 64; i++) {
        float h = sdfScene(ro + t * rd);
        if (h < 0.001) break;
        t += h;
    }
}
```### 2. 分析交集 + 体积效应

使用解析交集获得精确的进入/退出距离，然后在该范围内执行体积采样（云、雾、次表面散射）：```glsl
// Use analytic ellipsoid intersection to obtain volume bounds
float tEnter = (-b - sqrt(h)) / a;
float tExit  = (-b + sqrt(h)) / a;
float thickness = tExit - tEnter; // Analytic thickness

// Sample volume within [tEnter, tExit]
vec3 volumeColor = vec3(0.0);
float dt = (tExit - tEnter) / float(VOLUME_STEPS);
for (int i = 0; i < VOLUME_STEPS; i++) {
    vec3 p = ro + rd * (tEnter + float(i) * dt);
    volumeColor += sampleVolume(p) * dt;
}
```### 3.解析交集+PBR材质系统

分析相交提供精确的法线和相交位置，直接输入 Cook-Torrance 和其他 PBR 着色模型：```glsl
// Cook-Torrance BRDF (requires precise normals)
float D = beckmannDistribution(NdotH, roughness);
float G = geometricAttenuation(NdotV, NdotL, VdotH, NdotH);
float F = fresnelSchlick(VdotH, F0);
vec3 specular = vec3(D * G * F) / (4.0 * NdotV * NdotL);
```### 4.分析交集+空间变换

通过旋转/平移/缩放射线，对变换后的几何体重复使用相同的交集函数：```glsl
// Rotate object: rotate the ray instead of the object
vec3 localRo = rotateY(ro - objectPos, angle);
vec3 localRd = rotateY(rd, angle);
float t = iBox(localRo, localRd, distBound, localNormal, boxSize);
// Transform normal back to world space
normal = rotateY(localNormal, -angle);
```### 5.分析相交+分析AO/软阴影/抗锯齿

完全分析的渲染管道：相交、阴影、遮挡和边缘平滑均使用封闭式公式，产生零噪声：```glsl
// Fully analytic pipeline (no random sampling, no noise)
float t = sphIntersect(ro, rd, sph);        // Analytic intersection
float shadow = sphSoftShadow(hitPos, ld, sph); // Analytic soft shadow
float ao = sphOcclusion(hitPos, normal, sph);  // Analytic ambient occlusion
float coverage = sphAntiAlias(ro, rd, sph, px); // Analytic antialiasing
```
