## WebGL2 适配要求

本文档中的代码模板使用ShaderToy GLSL风格。生成独立 HTML 页面时，必须适应 WebGL2：

- 使用`canvas.getContext("webgl2")`
- 第一行着色器：“#version 300 es”，在片段着色器中添加“ precision highp float;”
- 顶点着色器：`attribute` -> `in`、`variing` -> `out`
- 片段着色器：`variing` -> `in`、`gl_FragColor` -> 自定义输出变量（必须在 `void main()` 之前声明，例如 `out vec4 outColor;`）、`texture2D()` -> `texture()`
- ShaderToy 的 `void mainImage(out vec4 fragColor, in vec2 fragCoord)` 必须适应标准的 `void main()` 入口点

# CSG 布尔运算

## 核心原则

CSG 布尔运算是两个距离字段上的每点值运算：

|运营|表达|意义|
|------------|------------|---------|
|联盟| `min(d1, d2)` |取最近的表面，保持两种形状 |
|交叉口| `最大（d1，d2）` |取最远的表面，仅保留重叠|
|减法| `最大（d1，-d2）` |使用 d2 的内部切割 d1 |

**平滑布尔值**（平滑最小/最大）在过渡区域引入混合带。参数“k”控制混合带宽（较大=更圆，“k=0”退化为硬布尔值）。存在具有不同数学属性的多种变体。

## 实施步骤

### 步骤 1：硬布尔运算```glsl
float opUnion(float d1, float d2) { return min(d1, d2); }
float opIntersection(float d1, float d2) { return max(d1, d2); }
float opSubtraction(float d1, float d2) { return max(d1, -d2); }
```### 步骤 2：平滑并集（多项式版本）```glsl
// k: blend radius, typical values 0.05~0.5
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}
```### 步骤 3：平滑减法和交集（多项式版本）```glsl
float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```### 步骤 4：二次优化版本（推荐默认）```glsl
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// Subtraction via smax
float sSub(float d1, float d2, float k) {
    return smax(d1, -d2, k);
}
```### 步骤 4b：平滑最小变体库

不同的 smin 实现具有不同的数学属性。根据您的需求选择：

|变体 |刚性|联想|最适合 |
|--------|---------|-------------|---------|
|二次（上面默认）|是的 |没有 |一般用途，最快|
|立方|是的 |没有 |更平滑的 C2 过渡 |
|四次|是的 |没有 |最高品质的混合 |
|指数|没有 |是的 |多体混合（与顺序无关）|
|圆形几何|是的 |是的 |严格的局部混合 |

**刚性**：保留混合区域外的原始 SDF 形状（无低估）。
**关联**： `smin(a, smin(b, c))` == `smin(smin(a, b), c)` — 在混合评估顺序不同的许多对象时很重要。```glsl
// --- Cubic Polynomial smin (C2 continuous, smoother transitions) ---
float sminCubic(float a, float b, float k) {
    k *= 6.0;
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * h * k * (1.0 / 6.0);
}

// --- Quartic Polynomial smin (C3 continuous, highest quality) ---
float sminQuartic(float a, float b, float k) {
    k *= 16.0 / 3.0;
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * h * (4.0 - h) * k * (1.0 / 16.0);
}

// --- Exponential smin (associative — order independent for multi-body blending) ---
float sminExp(float a, float b, float k) {
    float r = exp2(-a / k) + exp2(-b / k);
    return -k * log2(r);
}

// --- Circular Geometric smin (rigid + local + associative) ---
float sminCircle(float a, float b, float k) {
    k *= 1.0 / (1.0 - sqrt(0.5));
    return max(k, min(a, b)) - length(max(k - vec2(a, b), 0.0));
}

// --- Gradient-aware smin (carries material/color through blending) ---
// x = distance, yzw = material properties or color components
vec4 sminColor(vec4 a, vec4 b, float k) {
    k *= 4.0;
    float h = max(k - abs(a.x - b.x), 0.0) / (2.0 * k);
    return vec4(
        min(a.x, b.x) - h * h * k,
        mix(a.yzw, b.yzw, (a.x < b.x) ? h : 1.0 - h)
    );
}

// --- Smooth maximum from any smin variant ---
// smax(a, b, k) = -smin(-a, -b, k)
// Smooth subtraction: smax(d1, -d2, k)
// Smooth intersection: smax(d1, d2, k)
```### 步骤 5：基本 SDF 基元```glsl
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}
```### 步骤 6：场景构建的 CSG 组合```glsl
float mapScene(vec3 p) {
    float cube = sdBox(p, vec3(1.0));
    float sphere = sdSphere(p, 1.2);
    float cylX = sdCylinder(p.yzx, 2.0, 0.4);
    float cylY = sdCylinder(p.xyz, 2.0, 0.4);
    float cylZ = sdCylinder(p.zxy, 2.0, 0.4);

    // (cube intersect sphere) - three cylinders = nut
    float shape = opIntersection(cube, sphere);
    float holes = opUnion(cylX, opUnion(cylY, cylZ));
    return opSubtraction(shape, holes);
}
```### 步骤 7：有机形式的平滑 CSG 建模```glsl
// Use different k values for different body parts: large k for major joints, small k for fine details
float mapCreature(vec3 p) {
    float body = sdSphere(p, 0.5);
    float head = sdSphere(p - vec3(0.0, 0.6, 0.3), 0.25);
    float d = smin(body, head, 0.15);          // large blend

    float leg = sdCylinder(p - vec3(0.2, -0.5, 0.0), 0.3, 0.08);
    d = smin(d, leg, 0.08);                    // medium blend

    float eye = sdSphere(p - vec3(0.05, 0.75, 0.4), 0.05);
    d = smax(d, -eye, 0.02);                  // small blend for subtraction
    return d;
}
```### 步骤 8：光线行进主循环```glsl
float rayMarch(vec3 ro, vec3 rd, float maxDist) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = mapScene(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > maxDist) break;
    }
    return -1.0;
}
```### 步骤9：正常计算（四面体采样，4个样本比6个样本更有效，有中心差异）```glsl
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(0.001, -0.001);
    return normalize(
        e.xyy * mapScene(pos + e.xyy) +
        e.yyx * mapScene(pos + e.yyx) +
        e.yxy * mapScene(pos + e.yxy) +
        e.xxx * mapScene(pos + e.xxx)
    );
}
```## 完整代码模板```glsl
// === CSG Boolean Operations - WebGL2 Full Template ===
// Note: When generating HTML with this template, pass iTime, iResolution, etc. via uniforms

#define MAX_STEPS 128
#define MAX_DIST 50.0
#define SURF_DIST 0.001
#define SMOOTH_K 0.1

// === Hard Boolean Operations ===
float opUnion(float d1, float d2) { return min(d1, d2); }
float opIntersection(float d1, float d2) { return max(d1, d2); }
float opSubtraction(float d1, float d2) { return max(d1, -d2); }

// === Smooth Boolean Operations (Quadratic Optimized) ===
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// === SDF Primitives ===
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

float sdEllipsoid(vec3 p, vec3 r) {
    float k0 = length(p / r);
    float k1 = length(p / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}

// === Scene Definition ===
float mapScene(vec3 p) {
    // Rotation animation
    float angle = iTime * 0.3;
    float c = cos(angle), s = sin(angle);
    p.xz = mat2(c, -s, s, c) * p.xz;

    // Primitives
    float cube = sdBox(p, vec3(1.0));
    float sphere = sdSphere(p, 1.25);
    float cylR = 0.45;
    float cylX = sdCylinder(p.yzx, 2.0, cylR);
    float cylY = sdCylinder(p.xyz, 2.0, cylR);
    float cylZ = sdCylinder(p.zxy, 2.0, cylR);

    // Hard boolean combination: nut = (cube intersect sphere) - three cylinders
    float nut = opSubtraction(
        opIntersection(cube, sphere),
        opUnion(cylX, opUnion(cylY, cylZ))
    );

    // Organic spheres -- smooth union blending
    float blob1 = sdSphere(p - vec3(1.8, 0.0, 0.0), 0.4);
    float blob2 = sdSphere(p - vec3(-1.8, 0.0, 0.0), 0.4);
    float blob3 = sdSphere(p - vec3(0.0, 1.8, 0.0), 0.4);
    float blobs = smin(blob1, smin(blob2, blob3, 0.3), 0.3);

    return smin(nut, blobs, 0.15);
}

// === Normal Calculation (Tetrahedral Sampling) ===
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(0.001, -0.001);
    return normalize(
        e.xyy * mapScene(pos + e.xyy) +
        e.yyx * mapScene(pos + e.yyx) +
        e.yxy * mapScene(pos + e.yxy) +
        e.xxx * mapScene(pos + e.xxx)
    );
}

// === Ray Marching ===
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = mapScene(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > MAX_DIST) break;
    }
    return -1.0;
}

// === Soft Shadows ===
float calcSoftShadow(vec3 ro, vec3 rd, float k) {
    float res = 1.0;
    float t = 0.02;
    for (int i = 0; i < 64; i++) {
        float h = mapScene(ro + rd * t);
        res = min(res, k * h / t);
        t += clamp(h, 0.01, 0.2);
        if (res < 0.001 || t > 20.0) break;
    }
    return clamp(res, 0.0, 1.0);
}

// === AO (Ambient Occlusion) ===
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i);
        float d = mapScene(pos + h * nor);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}

// === Main Function (WebGL2 Adapted) ===
out vec4 outColor;
void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;

    // Camera
    float camDist = 4.0;
    float camAngle = 0.3;
    vec3 ro = vec3(
        camDist * cos(iTime * 0.2),
        camDist * sin(camAngle),
        camDist * sin(iTime * 0.2)
    );
    vec3 ta = vec3(0.0, 0.0, 0.0);

    // Camera matrix
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 2.0 * ww);

    // Background color
    vec3 col = vec3(0.4, 0.5, 0.6) - 0.3 * rd.y;

    // Ray marching
    float t = rayMarch(ro, rd);
    if (t > 0.0) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);

        vec3 lightDir = normalize(vec3(0.8, 0.6, -0.3));
        float dif = clamp(dot(nor, lightDir), 0.0, 1.0);
        float sha = calcSoftShadow(pos + nor * 0.01, lightDir, 16.0);
        float ao = calcAO(pos, nor);
        float amb = 0.5 + 0.5 * nor.y;

        vec3 mate = vec3(0.2, 0.3, 0.4);
        col = vec3(0.0);
        col += mate * 2.0 * dif * sha;
        col += mate * 0.3 * amb * ao;
    }

    col = pow(col, vec3(0.4545));
    outColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：指数平滑并集```glsl
float sminExp(float a, float b, float k) {
    float res = exp(-k * a) + exp(-k * b);
    return -log(res) / k;
}
```### 变体 2：通过颜色混合实现平滑操作```glsl
// Returns blend factor for the caller to blend colors
float sminWithFactor(float a, float b, float k, out float blend) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    blend = h;
    return mix(b, a, h) - k * h * (1.0 - h);
}
// float blend;
// float d = sminWithFactor(d1, d2, 0.1, blend);
// vec3 color = mix(color2, color1, blend);

// vec3 overload of smax
vec3 smax(vec3 a, vec3 b, float k) {
    vec3 h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}
```### 变体 3：逐步 CSG 建模（建筑/工业）```glsl
float sdBuilding(vec3 p) {
    float walls = sdBox(p, vec3(1.0, 0.8, 1.0));
    vec3 roofP = p;
    roofP.y -= 0.8;
    float roof = sdBox(roofP, vec3(1.2, 0.3, 1.2));
    float d = opUnion(walls, roof);

    // Cut windows (exploiting symmetry)
    vec3 winP = abs(p);
    winP -= vec3(1.01, 0.3, 0.4);
    float window = sdBox(winP, vec3(0.1, 0.15, 0.12));
    d = opSubtraction(d, window);

    // Hollow out interior
    float hollow = sdBox(p, vec3(0.95, 0.75, 0.95));
    d = opSubtraction(d, hollow);
    return d;
}
```### 变体 4：大型有机角色建模```glsl
float mapCharacter(vec3 p) {
    float body = sdEllipsoid(p, vec3(0.5, 0.4, 0.6));
    float head = sdEllipsoid(p - vec3(0.0, 0.5, 0.5), vec3(0.25));
    float d = smin(body, head, 0.2);           // large k: wide blend

    float ear = sdEllipsoid(p - vec3(0.3, 0.6, 0.3), vec3(0.15, 0.2, 0.05));
    d = smin(d, ear, 0.08);                    // medium blend

    float nostril = sdSphere(p - vec3(0.0, 0.4, 0.7), 0.03);
    d = smax(d, -nostril, 0.02);               // small k: fine sculpting
    return d;
}
```## 表演和构图技巧

**性能：**
- 包围体加速：使用 AABB/包围球跳过远处的子场景，减少“mapScene()”调用
- 四面体采样法线（4 个样本）优于中心差异（6 个样本）
- 步进缩放`t += d * 0.9`可以减少超调穿透
- 更喜欢二次优化的 smin/smax（最快）；当需要极度平滑时使用指数版本
- `k` 不能为零（除以零错误）；当接近零时回落到硬布尔值
- 对于对称形状，使用“abs()”折叠坐标并仅定义一侧

**构图技巧：**
- **+ 域重复**：`mod()`/`fract()` 用于无限重复 CSG 形状（机械阵列、栏杆）
- **+ 程序位移**：在 SDF 上叠加噪声位移以获得表面细节
- **+ 程序纹理**：使用 smin 混合因子同时混合材质 ID/颜色
- **+ 2D SDF**：同样适用于2D场景（云、UI形状合成）
- **+动画**：将k值、位置和半径绑定到“iTime”以进行动态变形

## 进一步阅读

[参考](../reference/csg-boolean-operations.md) 中有完整的分步教程、数学推导和高级用法