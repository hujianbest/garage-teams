# 分析光线追踪

## 用例

- 渲染由几何图元（球体、平面、盒子、圆柱体、椭球体等）组成的场景
- 需要精确的表面交点、法线和距离计算（无迭代近似）
- 为光线追踪器/路径追踪器构建底层几何引擎
- 需要精确阴影、反射和折射的场景

## 核心原则

将射线方程`P(t) = O + tD`代入几何体的隐式方程，得到`t`的代数方程，然后用封闭形式求解。

**统一相交工作流程**：建立方程 -> 简化为标准形式 -> 判别测试 -> 取最小正根 -> 计算法线相交处的梯度

**关键公式**：
- **球体** `|P-C|^2 = r^2` -> 二次方程
- **平面** `N·P + d = 0` -> 线性方程
- **盒子** 三对平行平面的交点 -> 板法
- **椭球** `|P/R|^2 = 1` -> 缩放空间中的球体相交
- **环面** `(|P_xy| - R)^2 + P_z^2 = r^2` -> 四次方程

## 实施步骤

### 第 1 步：射线生成```glsl
vec3 generateRay(vec2 fragCoord, vec2 resolution, vec3 ro, vec3 ta) {
    vec2 p = (2.0 * fragCoord - resolution) / resolution.y;
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0, 1, 0)));
    vec3 cv = cross(cu, cw);
    float fov = 1.5;
    return normalize(p.x * cu + p.y * cv + fov * cw);
}
```### 步骤 2：光线球体相交```glsl
// Optimized version with sphere center at origin
float iSphere(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float h = b * b - c;
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float d1 = -b - h;
    float d2 = -b + h;
    if (d1 >= distBound.x && d1 <= distBound.y) {
        normal = normalize(ro + rd * d1);
        return d1;
    } else if (d2 >= distBound.x && d2 <= distBound.y) {
        normal = normalize(ro + rd * d2);
        return d2;
    }
    return MAX_DIST;
}
```

```glsl
// General version, supports arbitrary sphere center (sph = vec4(center.xyz, radius))
float sphIntersect(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    if (h < 0.0) return -1.0;
    return -b - sqrt(h);
}
```### 步骤 3：光线平面相交```glsl
float iPlane(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
             vec3 planeNormal, float planeDist) {
    float denom = dot(rd, planeNormal);
    if (denom > 0.0) return MAX_DIST;
    float d = -(dot(ro, planeNormal) + planeDist) / denom;
    if (d < distBound.x || d > distBound.y) return MAX_DIST;
    normal = planeNormal;
    return d;
}

// fast horizontal ground plane
float iGroundPlane(vec3 ro, vec3 rd, float height) {
    return -(ro.y - height) / rd.y;
}
```### 步骤 4：Ray-Box 相交（板法）```glsl
float iBox(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 boxSize) {
    vec3 m = sign(rd) / max(abs(rd), 1e-8);
    vec3 n = m * ro;
    vec3 k = abs(m) * boxSize;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF <= 0.0) return MAX_DIST;
    if (tN >= distBound.x && tN <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tN;
    } else if (tF >= distBound.x && tF <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
        return tF;
    }
    return MAX_DIST;
}
```### 步骤 5：射线与椭球体相交```glsl
// Transform to unit sphere space for intersection, transform normal back to original space
float iEllipsoid(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 rad) {
    vec3 ocn = ro / rad;
    vec3 rdn = rd / rad;
    float a = dot(rdn, rdn);
    float b = dot(ocn, rdn);
    float c = dot(ocn, ocn);
    float h = b * b - a * (c - 1.0);
    if (h < 0.0) return MAX_DIST;
    float d = (-b - sqrt(h)) / a;
    if (d < distBound.x || d > distBound.y) return MAX_DIST;
    normal = normalize((ro + d * rd) / rad);
    return d;
}
```### 第 6 步：射线与圆柱相交（带端盖）```glsl
// pa, pb: cylinder axis endpoints, ra: radius
float iCylinder(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
                vec3 pa, vec3 pb, float ra) {
    vec3 ca = pb - pa;
    vec3 oc = ro - pa;
    float caca = dot(ca, ca);
    float card = dot(ca, rd);
    float caoc = dot(ca, oc);
    float a = caca - card * card;
    float b = caca * dot(oc, rd) - caoc * card;
    float c = caca * dot(oc, oc) - caoc * caoc - ra * ra * caca;
    float h = b * b - a * c;
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float d = (-b - h) / a;
    float y = caoc + d * card;
    if (y > 0.0 && y < caca && d >= distBound.x && d <= distBound.y) {
        normal = (oc + d * rd - ca * y / caca) / ra;
        return d;
    }
    d = ((y < 0.0 ? 0.0 : caca) - caoc) / card;
    if (abs(b + a * d) < h && d >= distBound.x && d <= distBound.y) {
        normal = normalize(ca * sign(y) / caca);
        return d;
    }
    return MAX_DIST;
}
```### 步骤 7：场景交叉和着色```glsl
#define MAX_DIST 1e10

vec3 worldHit(vec3 ro, vec3 rd, vec2 dist, out vec3 normal) {
    vec3 d = vec3(dist, 0.0);
    vec3 tmpNormal;
    float t;

    t = iPlane(ro, rd, d.xy, normal, vec3(0, 1, 0), 0.0);
    if (t < d.y) { d.y = t; d.z = 1.0; }

    t = iSphere(ro - vec3(0, 0.5, 0), rd, d.xy, tmpNormal, 0.5);
    if (t < d.y) { d.y = t; d.z = 2.0; normal = tmpNormal; }

    t = iBox(ro - vec3(2, 0.5, 0), rd, d.xy, tmpNormal, vec3(0.5));
    if (t < d.y) { d.y = t; d.z = 3.0; normal = tmpNormal; }

    return d;
}

vec3 shade(vec3 pos, vec3 normal, vec3 rd, vec3 albedo) {
    vec3 lightDir = normalize(vec3(-1.0, 0.75, 1.0));
    float diff = max(dot(normal, lightDir), 0.0);
    float amb = 0.5 + 0.5 * normal.y;
    return albedo * (amb * 0.2 + diff * 0.8);
}
```> **重要：严重的陷阱**：`d.xy` 必须作为 distBound 传递，并且每次找到更近的交叉点时都必须更新 `d.y`！如果部署的代码直接通过原始的`dist`而不进行更新，相交逻辑将失败（所有物距测试无效），导致全黑屏。```glsl
#define MAX_BOUNCES 4
#define EPSILON 0.001

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
            color += mask * vec3(0.6, 0.8, 1.0);
            break;
        }
        vec3 hitPos = ro + rd * res.y;
        vec3 albedo = getAlbedo(res.z);
        float F = schlickFresnel(max(0.0, dot(normal, -rd)), 0.04);
        color += mask * (1.0 - F) * shade(hitPos, normal, rd, albedo);
        mask *= F * albedo;
        rd = reflect(rd, normal);
        ro = hitPos + EPSILON * rd;
    }
    return color;
}
```## 完整的代码模板

直接在 ShaderToy 上运行，包括带有反射和 Blinn-Phong 着色的球体、平面和长方体基元。

> **重要：必须遵循**：所有交集函数调用必须使用“d.xy”作为“distBound”参数，并在找到每个更接近的交集后更新“d.y”。错误用法：“iSphere(ro, rd, dist, ...)”（始终使用原始 dist）。正确用法：“iSphere(ro, rd, d.xy, ...)”后接“if (t < d.y) { d.y = t; ... }` 进行更新。```glsl
// Analytic Ray Tracing - Complete ShaderToy Template
#define MAX_DIST 1e10
#define EPSILON 0.001
#define MAX_BOUNCES 3
#define FOV 1.5
#define GAMMA 2.2
#define SHADOW_ENABLED true

float iSphere(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float r) {
    float b = dot(ro, rd);
    float c = dot(ro, ro) - r * r;
    float h = b * b - c;
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float d1 = -b - h, d2 = -b + h;
    if (d1 >= distBound.x && d1 <= distBound.y) { normal = normalize(ro + rd * d1); return d1; }
    if (d2 >= distBound.x && d2 <= distBound.y) { normal = normalize(ro + rd * d2); return d2; }
    return MAX_DIST;
}

float iPlane(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal,
             vec3 planeNormal, float planeDist) {
    float denom = dot(rd, planeNormal);
    if (denom > 0.0) return MAX_DIST;
    float d = -(dot(ro, planeNormal) + planeDist) / denom;
    if (d < distBound.x || d > distBound.y) return MAX_DIST;
    normal = planeNormal;
    return d;
}

float iBox(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, vec3 boxSize) {
    vec3 m = sign(rd) / max(abs(rd), 1e-8);
    vec3 n = m * ro;
    vec3 k = abs(m) * boxSize;
    vec3 t1 = -n - k, t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    if (tN > tF || tF <= 0.0) return MAX_DIST;
    if (tN >= distBound.x && tN <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz); return tN;
    }
    if (tF >= distBound.x && tF <= distBound.y) {
        normal = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz); return tF;
    }
    return MAX_DIST;
}

struct Material { vec3 albedo; float specular; float roughness; };

Material getMaterial(float matId, vec3 pos) {
    if (matId < 1.5) {
        float checker = mod(floor(pos.x) + floor(pos.z), 2.0);
        return Material(vec3(0.4 + 0.4 * checker), 0.02, 0.8);
    } else if (matId < 2.5) { return Material(vec3(1.0, 0.2, 0.2), 0.5, 0.3); }
    else if (matId < 3.5) { return Material(vec3(0.2, 0.4, 1.0), 0.1, 0.6); }
    else if (matId < 4.5) { return Material(vec3(1.0, 1.0, 1.0), 0.8, 0.05); }
    else { return Material(vec3(0.8, 0.6, 0.2), 0.3, 0.4); }
}

vec3 worldHit(vec3 ro, vec3 rd, vec2 dist, out vec3 normal) {
    vec3 d = vec3(dist, 0.0); vec3 tmp; float t;
    t = iPlane(ro, rd, d.xy, tmp, vec3(0, 1, 0), 0.0);
    if (t < d.y) { d.y = t; d.z = 1.0; normal = tmp; }
    t = iSphere(ro - vec3(-2.0, 1.0, 0.0), rd, d.xy, tmp, 1.0);
    if (t < d.y) { d.y = t; d.z = 2.0; normal = tmp; }
    t = iSphere(ro - vec3(0.0, 0.6, 2.0), rd, d.xy, tmp, 0.6);
    if (t < d.y) { d.y = t; d.z = 3.0; normal = tmp; }
    t = iSphere(ro - vec3(2.0, 0.8, -1.0), rd, d.xy, tmp, 0.8);
    if (t < d.y) { d.y = t; d.z = 4.0; normal = tmp; }
    t = iBox(ro - vec3(0.0, 0.5, -2.0), rd, d.xy, tmp, vec3(0.5));
    if (t < d.y) { d.y = t; d.z = 5.0; normal = tmp; }
    return d;
}

float shadow(vec3 ro, vec3 rd, float maxDist) {
    vec3 normal;
    vec3 res = worldHit(ro, rd, vec2(EPSILON, maxDist), normal);
    return res.z > 0.5 ? 0.3 : 1.0;
}

float schlick(float cosTheta, float F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

vec3 skyColor(vec3 rd) {
    vec3 col = mix(vec3(1.0), vec3(0.5, 0.7, 1.0), 0.5 + 0.5 * rd.y);
    vec3 sunDir = normalize(vec3(-0.4, 0.7, -0.6));
    float sun = clamp(dot(sunDir, rd), 0.0, 1.0);
    col += vec3(1.0, 0.6, 0.1) * (pow(sun, 4.0) + 10.0 * pow(sun, 32.0));
    return col;
}

vec3 render(vec3 ro, vec3 rd) {
    vec3 color = vec3(0.0), mask = vec3(1.0), normal;
    for (int bounce = 0; bounce < MAX_BOUNCES; bounce++) {
        vec3 res = worldHit(ro, rd, vec2(EPSILON, 100.0), normal);
        if (res.z < 0.5) { color += mask * skyColor(rd); break; }
        vec3 hitPos = ro + rd * res.y;
        Material mat = getMaterial(res.z, hitPos);
        vec3 lightDir = normalize(vec3(-0.4, 0.7, -0.6));
        float diff = max(dot(normal, lightDir), 0.0);
        float amb = 0.5 + 0.5 * normal.y;
        float sha = SHADOW_ENABLED ? shadow(hitPos + normal * EPSILON, lightDir, 50.0) : 1.0;
        vec3 halfVec = normalize(lightDir - rd);
        float spec = pow(max(dot(normal, halfVec), 0.0), 1.0 / max(mat.roughness, 0.001));
        float F = schlick(max(0.0, dot(normal, -rd)), 0.04 + 0.96 * mat.specular);
        vec3 diffCol = mat.albedo * (amb * 0.15 + diff * sha * 0.85);
        vec3 specCol = vec3(spec * sha);
        color += mask * mix(diffCol, specCol, F * mat.specular);
        mask *= F * mat.albedo;
        if (length(mask) < 0.01) break;
        rd = reflect(rd, normal);
        ro = hitPos + normal * EPSILON;
    }
    return color;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    float angle = 0.3 * iTime;
    vec3 ro = vec3(4.0 * cos(angle), 2.5, 4.0 * sin(angle));
    vec3 ta = vec3(0.0, 0.5, 0.0);
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0, 1, 0)));
    vec3 cv = cross(cu, cw);
    vec3 rd = normalize(p.x * cu + p.y * cv + FOV * cw);
    vec3 col = render(ro, rd);
    col = col / (1.0 + col);
    col = pow(col, vec3(1.0 / GAMMA));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：路径追踪```glsl
vec3 cosWeightedRandomHemisphereDirection(vec3 n, inout uint seed) {
    uint ri = seed * 1103515245u + 12345u;
    seed = ri;
    float r1 = float(ri) / float(0xFFFFFFFFu);
    ri = seed * 1103515245u + 12345u;
    seed = ri;
    float r2 = float(ri) / float(0xFFFFFFFFu);
    vec3 uu = normalize(cross(n, abs(n.y) > 0.5 ? vec3(1,0,0) : vec3(0,1,0)));
    vec3 vv = cross(uu, n);
    float ra = sqrt(r1);
    float rx = ra * cos(6.2831 * r2);
    float ry = ra * sin(6.2831 * r2);
    float rz = sqrt(1.0 - r1);
    return normalize(rx * uu + ry * vv + rz * n);
}
// In the bounce loop, replace reflect with:
// rd = cosWeightedRandomHemisphereDirection(normal, seed);
// ro = hitPos + EPSILON * rd;
// mask *= mat.albedo;
```### 变体 2：分析软阴影```glsl
float sphSoftShadow(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    float t = -b - sqrt(max(h, 0.0));
    return (t > 0.0) ? max(d, 0.0) / t : 1.0;
}
```### 变体 3：分析抗锯齿```glsl
vec2 sphDistances(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    float d = sqrt(max(0.0, sph.w * sph.w - h)) - sph.w;
    return vec2(d, -b - sqrt(max(h, 0.0)));
}
// float px = 2.0 / iResolution.y;
// vec2 dt = sphDistances(ro, rd, sph);
// float coverage = 1.0 - clamp(dt.x / (dt.y * px), 0.0, 1.0);
// col = mix(bgColor, sphereColor, coverage);
```### 变体 4：折射（斯涅尔定律）```glsl
// Requires a random number function defined first
float hash1(float p) {
    return fract(sin(p) * 43758.5453);
}

// Add refraction branch in the render loop:
float refrIndex = 1.5; // glass ~ 1.5, water ~ 1.33
bool inside = dot(rd, normal) > 0.0;
vec3 n = inside ? -normal : normal;
float eta = inside ? refrIndex : 1.0 / refrIndex;
vec3 refracted = refract(rd, n, eta);
float cosI = abs(dot(rd, n));
float F = schlick(cosI, pow((1.0 - eta) / (1.0 + eta), 2.0));
// Use bounce count as random seed
float randSeed = float(bounce) + 1.0;
if (refracted != vec3(0.0) && hash1(randSeed * 12.9898) > F) {
    rd = refracted;
} else {
    rd = reflect(rd, n);
}
ro = hitPos + rd * EPSILON;
```### 变体 5：高阶代数曲面 (Sphere4)```glsl
float iSphere4(vec3 ro, vec3 rd, vec2 distBound, inout vec3 normal, float ra) {
    float r2 = ra * ra;
    vec3 d2 = rd*rd, d3 = d2*rd;
    vec3 o2 = ro*ro, o3 = o2*ro;
    float ka = 1.0 / dot(d2, d2);
    float k0 = ka * dot(ro, d3);
    float k1 = ka * dot(o2, d2);
    float k2 = ka * dot(o3, rd);
    float k3 = ka * (dot(o2, o2) - r2 * r2);
    float c0 = k1 - k0 * k0;
    float c1 = k2 + 2.0 * k0 * (k0 * k0 - 1.5 * k1);
    float c2 = k3 - 3.0 * k0 * (k0 * (k0 * k0 - 2.0 * k1) + 4.0/3.0 * k2);
    float p = c0 * c0 * 3.0 + c2;
    float q = c0 * c0 * c0 - c0 * c2 + c1 * c1;
    float h = q * q - p * p * p * (1.0/27.0);
    if (h < 0.0) return MAX_DIST;
    h = sqrt(h);
    float s = sign(q+h) * pow(abs(q+h), 1.0/3.0);
    float t = sign(q-h) * pow(abs(q-h), 1.0/3.0);
    vec2 v = vec2((s+t) + c0*4.0, (s-t) * sqrt(3.0)) * 0.5;
    float r = length(v);
    float d = -abs(v.y) / sqrt(r + v.x) - c1/r - k0;
    if (d >= distBound.x && d <= distBound.y) {
        vec3 pos = ro + rd * d;
        normal = normalize(pos * pos * pos);
        return d;
    }
    return MAX_DIST;
}
```## 常见错误和保障措施

### 错误 1：距离限制未更新
**症状**：屏幕全黑或仅显示背景
**原因**：每次交叉后`distBound.y`未更新
**修复**：```glsl
// WRONG:
t = iSphere(ro, rd, dist, tmpNormal, 1.0);

// CORRECT:
t = iSphere(ro, rd, d.xy, tmpNormal, 1.0);
if (t < d.y) { d.y = t; d.z = matId; normal = tmpNormal; }
```### 错误 2：EPSILON 太小导致自相交伪影
**症状**：物体表面出现黑点或伪影
**原因**：`EPSILON`值太小，光线仍然与自身相交
**修复**：根据场景比例调整EPSILON；典型值1e-3～1e-2

### 错误 3：变量用作循环上限
**症状**：WebGL2 编译失败或着色器崩溃
**原因**：在GLSL ES 3.0中，`for`循环上限必须是常量
**修复**：使用“#define”作为循环上限，并将边界保持在最多 4-5 次迭代

### 错误 4：除以零导致 NaN
**症状**：NaN 在屏幕上传播时出现条纹图案
**原因**：当光线方向分量为零时，除法不受保护
**修复**：始终使用“max(abs(x), 1e-8)”或类似的保护

### 错误 5：折射变体中缺少哈希函数
**症状**：编译错误“未定义函数'hash1'”
**修复**：添加使用折射变量时的函数定义：```glsl
float hash1(float p) {
    return fract(sin(p) * 43758.5453);
}
```## 表演与作曲

**性能提示**：
- **距离限制剪辑**：在每个更近的交叉点后缩短`distBound.y`；后续对象将自动跳过
- **边界球预测试**：使用边界球对复杂几何体（环面等）进行预筛选
- **阴影光线简化**：只需要确定遮挡，不需要普通计算
- **避免不必要的 sqrt**：判别式为负时提前返回； `c > 0.0 && b > 0.0` 用于快速拒绝
- **网格加速**：对大量相似图元使用 3D DDA 网格遍历

**构图方法**：
- **+ Raymarching SDF**：分析基元定义主要结构，SDF 处理复杂细节
- **+体积效应**：分析交集为范围内的体积采样提供精确的进入/退出距离
- **+ PBR 材质**：精确法线直接插入 Cook-Torrance 和其他 BRDF
- **+ 空间变换**：旋转/平移光线以重用相同的相交函数
- **+ 分析 AA/AO/软阴影**：完全分析管道，零噪声

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/analytic-ray-tracing.md)