# 分形渲染——详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含先决条件、分步解释、数学推导、变体描述、深入的性能分析和完整的组合示例代码。

## 先决条件

- **GLSL 基础知识**：统一、变化、内置函数（`dot`、`length`、`normalize`、`abs`、`fract`）
- **复数算术**：将复数表示为`vec2`，乘法`(a+bi)(c+di) = (ac-bd, ad+bc)`
- **矢量数学**：点积、叉积、矩阵变换
- **射线行进基础知识**（3D 分形所需）：沿着射线步进，使用距离场进行碰撞检测
- **坐标标准化**：将像素坐标映射到“[-1, 1]”范围

## 核心原则详细信息

分形渲染的本质是**迭代系统的可视化**。核心算法模式分为三类：

### 1.逃逸时间算法

对于复平面上的每个点“c”，重复迭代“Z <- Z^2 + c”，计算 Z 逃逸 (“|Z| > R”) 所需的步数。更多的步骤意味着更接近分形边界。

**距离估计** 通过同时跟踪导数“Z”来计算从点到分形的精确距离：```
Z  <- Z^2 + c       (value iteration)
Z' <- 2*Z*Z' + 1    (derivative iteration)
d(c) = |Z|*log|Z| / |Z'|  (Hubbard-Douady potential function)
```距离估计比纯粹的逃逸时间步数计数产生更平滑的着色，并且是 3D 分形中光线行进的先决条件。

### 2.迭代函数系统（IFS）

对空间中的点应用一组变换（折叠“abs()”、缩放“Scale”、偏移“Offset”），重复迭代以产生自相似结构。 3D中常用的KIFS（万花筒IFS）核心步骤：```
p = abs(p)                          // Fold (symmetrize)
sort p.xyz descending               // Sort (select symmetry axis)
p = Scale * p - Offset * (Scale-1)  // Scale and offset
```### 3.球形反演分形

阿波罗型分形使用 `fract()` 进行空间折叠 + 球面反转 `p *= s/dot(p,p)`：```
p = -1.0 + 2.0 * fract(0.5*p + 0.5)   // Fold space to [-1,1]
r^2 = dot(p, p)
k = s / r^2                             // Inversion factor
p *= k; scale *= k                       // Spherical inversion
```所有 3D 分形均使用 **球体追踪（光线行进）** 进行渲染：沿着视图光线按每一步的距离场值步进，直到足够接近表面。

## 详细实施步骤

### 第 1 步：坐标标准化

**什么**：通过长宽比校正将像素坐标映射到以屏幕为中心的标准坐标。

**为什么**：所有分形计算都必须在数学空间中执行，与像素分辨率无关。```glsl
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
// p now has y range [-1,1], x scaled by aspect ratio
```### 步骤 2：2D 分形 — Mandelbrot 逃逸时间迭代

**什么**：对于作为复数“c”的每个像素点，迭代“Z <- Z^2 + c”，同时跟踪导数。

**为什么**：逃逸时间产生分形结构；导数跟踪可以实现距离估计着色。```glsl
float distanceToMandelbrot(in vec2 c) {
    vec2 z  = vec2(0.0);
    vec2 dz = vec2(0.0);  // Derivative
    float m2 = 0.0;

    for (int i = 0; i < MAX_ITER; i++) {
        if (m2 > BAILOUT * BAILOUT) break;

        // Z' -> 2*Z*Z' + 1 (complex derivative chain rule)
        dz = 2.0 * vec2(z.x*dz.x - z.y*dz.y,
                         z.x*dz.y + z.y*dz.x) + vec2(1.0, 0.0);

        // Z -> Z^2 + c (complex squaring)
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;

        m2 = dot(z, z);
    }

    // Distance estimation: d(c) = |Z|*log|Z| / |Z'|
    return 0.5 * sqrt(dot(z,z) / dot(dz,dz)) * log(dot(z,z));
}
```### 步骤 3：3D 分形 — 距离场函数（曼德尔球示例）

**内容**：使用球坐标实现曼德尔球 N 次幂迭代，返回距离估计。

**为什么**：3D 分形不能通过像素上的逃逸时间直接着色；它们需要距离场来进行射线行进。```glsl
float mandelbulb(vec3 p) {
    vec3 z = p;
    float dr = 1.0;  // Derivative (distance scaling factor)
    float r;

    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > BAILOUT) break;

        // Convert to spherical coordinates
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);

        // Derivative: dr -> power * r^(power-1) * dr + 1
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;

        // z -> z^power + p (spherical coordinate exponentiation)
        r = pow(r, POWER);
        theta *= POWER;
        phi *= POWER;
        z = r * vec3(cos(theta)*cos(phi),
                      sin(theta)*cos(phi),
                      sin(phi)) + p;
    }

    // Distance estimation
    return 0.5 * log(r) * r / dr;
}
```### 步骤 4：3D 分形 — IFS 距离场（Menger 海绵示例）

**什么**：通过折叠-排序-尺度-偏移迭代构建 KIFS 分形距离场。

**为什么**：IFS 分形通过空间变换而不是数值迭代产生自相似结构；距离是通过“Scale^(-n)”缩放来跟踪的。```glsl
float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));  // Infinite tiling
    float d = 1000.0;

    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);                              // Fold
        if (z.x < z.y) z.xy = z.yx;             // Sort
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0); // Scale + offset
        if (z.z < -0.5 * OFFSET.z * (SCALE - 1.0))
            z.z += OFFSET.z * (SCALE - 1.0);
        d = min(d, length(z) * pow(SCALE, float(-n) - 1.0));
    }

    return d - 0.001;
}
```### 步骤 5：3D 分形 — 球面反演距离场（阿波罗型）

**什么**：使用分形折叠 + 球形反演迭代构造阿波罗分形，同时记录轨道陷阱。

**为什么**：球形反转 `p *= s/dot(p,p)` 产生球堆积结构；轨道陷阱提供颜色和 AO 信息。```glsl
vec4 orb;  // Global orbit trap

float apollonianDE(vec3 p, float s) {
    float scale = 1.0;
    orb = vec4(1000.0);

    for (int i = 0; i < INVERSION_ITER; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);  // Fold space to [-1,1]
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));          // Record orbit trap
        float k = s / r2;                          // Inversion factor
        p *= k;
        scale *= k;
    }

    return 0.25 * abs(p.y) / scale;
}
```### 步骤 6：光线行进（球体追踪）

**什么**：沿着射线方向步进，按每一步的距离场值前进，直到撞击表面。

**为什么**：距离场保证安全步进（不会穿过表面），并且是渲染隐式 3D 分形的标准方法。```glsl
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.01;
    for (int i = 0; i < MAX_STEPS; i++) {
        float precis = PRECISION * t;  // Relax precision with distance
        float h = map(ro + rd * t);
        if (h < precis || t > MAX_DIST) break;
        t += h * FUDGE_FACTOR;         // fudge < 1.0 improves safety
    }
    return (t > MAX_DIST) ? -1.0 : t;
}
```### 步骤 7：正常计算（有限差分）

**什么**：将命中点周围的距离场梯度采样为表面法线。

**为什么**：隐式曲面没有分析法线，需要数值近似。与中心差分（6-tap）相比，四面体采样（4-tap）可节省 1/3 的成本。```glsl
// 6-tap central difference method (more intuitive)
vec3 calcNormal_6tap(vec3 pos) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(pos + e.xyy) - map(pos - e.xyy),
        map(pos + e.yxy) - map(pos - e.yxy),
        map(pos + e.yyx) - map(pos - e.yyx)));
}

// 4-tap tetrahedral method (more efficient, recommended)
vec3 calcNormal_4tap(vec3 pos, float t) {
    float precis = 0.001 * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx));
}
```### 第 8 步：着色和照明

**内容**：计算命中表面的朗伯漫反射 + 环境光 + AO。

**原因**：照明赋予 3D 分形深度和材质质量。轨道陷阱值 (`orb`) 既可以用作颜色映射，也可以用作简单的 AO。```glsl
vec3 shade(vec3 pos, vec3 nor, vec3 rd, vec4 trap) {
    vec3 light1 = normalize(LIGHT_DIR);
    float diff = clamp(dot(light1, nor), 0.0, 1.0);
    float amb  = 0.7 + 0.3 * nor.y;
    float ao   = pow(clamp(trap.w * 2.0, 0.0, 1.0), 1.2); // Orbit trap AO

    vec3 brdf = vec3(0.4) * amb * ao      // Ambient
              + vec3(1.0) * diff * ao;     // Diffuse

    // Map material color from orbit trap
    vec3 rgb = vec3(1.0);
    rgb = mix(rgb, vec3(1.0, 0.8, 0.2), clamp(6.0*trap.y, 0.0, 1.0));
    rgb = mix(rgb, vec3(1.0, 0.55, 0.0), pow(clamp(1.0-2.0*trap.z, 0.0, 1.0), 8.0));

    return rgb * brdf;
}
```### 步骤 9：相机设置

**内容**：构建观察相机矩阵，将像素坐标转换为 3D 射线方向。

**为什么**：所有 3D 分形光线行进都需要统一的相机框架来生成光线。```glsl
void setupCamera(vec2 uv, vec3 ro, vec3 ta, float cr,
                 out vec3 rd) {
    vec3 cw = normalize(ta - ro);                   // forward
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);          // roll
    vec3 cu = normalize(cross(cw, cp));              // right
    vec3 cv = normalize(cross(cu, cw));              // up
    rd = normalize(uv.x * cu + uv.y * cv + 2.0 * cw); // FOV ~ 2.0
}
```## 常见变体详细信息

### 1. 2D Mandelbrot（距离估计着色）

与基础版本（3D Apollonian）的区别：纯2D计算，不需要光线行进，使用复杂迭代+距离着色。```glsl
// Replace entire mainImage
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0*fragCoord - iResolution.xy) / iResolution.y;

    // Animated zoom
    float tz = 0.5 - 0.5*cos(0.225*iTime);
    float zoo = pow(0.5, 13.0*tz);
    vec2 c = vec2(-0.05, 0.6805) + p * zoo; // Tunable: zoom center point

    // Iteration
    vec2 z = vec2(0.0), dz = vec2(0.0);
    for (int i = 0; i < 300; i++) { // Tunable: iteration count
        if (dot(z,z) > 1024.0) break;
        dz = 2.0*vec2(z.x*dz.x-z.y*dz.y, z.x*dz.y+z.y*dz.x) + vec2(1.0,0.0);
        z  = vec2(z.x*z.x-z.y*z.y, 2.0*z.x*z.y) + c;
    }

    float d = 0.5*sqrt(dot(z,z)/dot(dz,dz))*log(dot(z,z));
    d = clamp(pow(4.0*d/zoo, 0.2), 0.0, 1.0); // Tunable: 0.2 controls contrast
    fragColor = vec4(vec3(d), 1.0);
}
```### 2.Mandelbulb Power-N（3D 球面坐标分形）

与基础版本的区别：使用球坐标三角函数而不是球面反演，并使用可调节的“POWER”参数控制分形形状。```glsl
#define POWER 8.0   // Tunable: 2-16, higher = more complex structure
#define FRACTAL_ITER 4  // Tunable: 2-8, more = more detail

float mandelbulbDE(vec3 p) {
    vec3 z = p;
    float dr = 1.0;
    float r;
    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > 2.0) break;
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;
        r = pow(r, POWER);
        theta *= POWER;
        phi   *= POWER;
        z = r * vec3(cos(theta)*cos(phi), sin(theta)*cos(phi), sin(phi)) + p;
    }
    return 0.5 * log(r) * r / dr;
}
```### 3.蒙格海绵（KIFS折叠型）

与基础版本的区别：使用abs()折叠+条件排序而不是球形反转，产生规则的几何分形。```glsl
#define SCALE 3.0                           // Tunable: scaling factor, 2.0-4.0
#define OFFSET vec3(0.92858,0.92858,0.32858) // Tunable: offset vector, changes shape
#define IFS_ITER 7                          // Tunable: iteration count

float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));  // Infinite tiling
    float d = 1000.0;
    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);
        if (z.x < z.y) z.xy = z.yx;    // Conditional sorting
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0);
        if (z.z < -0.5*OFFSET.z*(SCALE-1.0))
            z.z += OFFSET.z*(SCALE-1.0);
        d = min(d, length(z) * pow(SCALE, float(-n)-1.0));
    }
    return d - 0.001;
}
```### 4.四元数朱莉娅集

与基本版本的区别：使用四元数代数“Z <- Z^2 + c”（4D），Julia 集使用固定的“c”参数而不是每点“c”，通过采用 3D 横截面进行可视化。```glsl
// Quaternion squaring
vec4 qsqr(vec4 a) {
    return vec4(a.x*a.x - a.y*a.y - a.z*a.z - a.w*a.w,
                2.0*a.x*a.y, 2.0*a.x*a.z, 2.0*a.x*a.w);
}

float juliaDE(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0);
    float md2 = 1.0;
    float mz2 = dot(z, z);

    for (int i = 0; i < 11; i++) { // Tunable: iteration count
        md2 *= 4.0 * mz2;         // |dz| -> 2*|z|*|dz|
        z = qsqr(z) + c;          // z -> z^2 + c
        mz2 = dot(z, z);
        if (mz2 > 4.0) break;
    }

    return 0.25 * sqrt(mz2 / md2) * log(mz2);
}
// Animated Julia parameter c:
// vec4 c = 0.45*cos(vec4(0.5,3.9,1.4,1.1) + time*vec4(1.2,1.7,1.3,2.5)) - vec4(0.3,0,0,0);
```### 5. 最小 IFS 场（2D，无光线行进）

与基础版本的区别：纯2D实现，仅约20行代码，使用“abs(p)/dot(p,p) + offset”进行迭代，通过加权累加产生密度场。```glsl
float field(vec3 p) {
    float strength = 7.0 + 0.03 * log(1.e-6 + fract(sin(iTime) * 4373.11));
    float accum = 0.0, prev = 0.0, tw = 0.0;
    for (int i = 0; i < 32; ++i) {  // Tunable: iteration count
        float mag = dot(p, p);
        p = abs(p) / mag + vec3(-0.5, -0.4, -1.5); // Tunable: offset values change shape
        float w = exp(-float(i) / 7.0);             // Tunable: 7.0 controls decay
        accum += w * exp(-strength * pow(abs(mag - prev), 2.3));
        tw += w;
        prev = mag;
    }
    return max(0.0, 5.0 * accum / tw - 0.7);
}
// Sample field() directly on fragCoord as brightness/color
```## 性能优化详情

### 瓶颈分析

分形渲染的核心瓶颈是**嵌套循环**：外部光线行进步骤 x 内部分形迭代。单个像素可以执行“200 步 x 8 次迭代 = 1600”距离场评估。

### 优化技术

#### 1. 减少光线行进步骤
将“MAX_STEPS”从 200 降低到 60-100，用模糊因子 (0.7-0.9) 补偿精度损失。```glsl
t += h * 0.7; // Fudge factor < 1.0, allows larger steps but reduces penetration risk
```#### 2. 自适应精度
随着距离的增加放宽碰撞阈值；远处的物体不需要像素级的精度。```glsl
float precis = 0.001 * t; // Precision grows linearly with distance
```#### 3.提前退出
在分形迭代中，一旦 `|z|^2 > bailout` 立即中断。```glsl
if (m2 > 4.0) break; // Don't continue useless iterations
```#### 4. 减少迭代次数
分形迭代计数（“INVERSION_ITER”、“IFS_ITER”）从 8 减少到 4-5，视觉影响最小，但性能提升显着。

#### 5. 对于法线使用 4-Tap 而不是 6-Tap
四面体方法只需要 4 次“map()”调用，而不是 6 次，节省了 33% 的正常计算成本。

#### 6. AA 降级
开发时使用`#define AA 1`，发布时改用`AA 2`。 “AA 3”具有巨大的性能影响（9 倍开销）。

#### 7. 距离场缩放
对于非单位大小的分形，请先缩放空间，然后缩放距离值，以避免精度问题。```glsl
float z1 = 2.0;
return mandelbulb(p / z1) * z1;
```#### 8. 避免循环内使用 `pow()`
曼德尔球中的“pow(r, power)”是昂贵的；低倍数（例如 2、3）可以手动扩展。

## 组合建议

### 1.分形+体积照明

在光线行进过程中累积穿过分形间隙的散射光，产生“上帝光线”效果。```glsl
// Accumulate additionally in ray march loop
float glow = 0.0;
for (...) {
    float h = map(ro + rd*t);
    glow += exp(-10.0 * h); // Closer to surface = larger contribution
    ...
}
col += glowColor * glow * 0.01;
```### 2. 分形+后处理（色调映射/FXAA）

3D 分形具有丰富的高频细节，容易出现锯齿。使用 ACES Tone Mapping + sRGB 校正 + FXAA 后处理。```glsl
// ACES tone mapping
vec3 aces_approx(vec3 v) {
    v = max(v, 0.0) * 0.6;
    float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((v*(a*v+b))/(v*(c*v+d)+e), 0.0, 1.0);
}
col = aces_approx(col);
col = pow(col, vec3(1.0/2.4)); // sRGB gamma
```### 3.分形+透明折射（多次反射折射）

用于体积分形（如曼德尔球）的“水晶球”效果。使用负距离场进行内部反向射线行进，并结合比尔定律吸收。```glsl
// Invert distance field for interior stepping
float dfactor = isInside ? -1.0 : 1.0;
float d = dfactor * map(ro + rd * t);
// Beer's law light absorption
ragg *= exp(-st * beer); // beer = negative color vector
// Refraction direction
vec3 refr = refract(rd, sn, isInside ? 1.0/ior : ior);
```### 4. 分形 + 轨道陷阱纹理映射

轨道陷阱值可以映射到 HSV 颜色空间以获得丰富的色彩，或映射为自发射以获得发光的分形效果。```glsl
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
// Map orbit trap to HSV
vec3 col = hsv2rgb(vec3(trap.x * 0.5, 0.9, 0.8));
```### 5.分形+软阴影

从分形表面向光源执行额外的光线行进，累积最小“h/t”比率以生成柔和的阴影。```glsl
float softshadow(vec3 ro, vec3 rd, float mint, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 64; i++) {
        float h = map(ro + rd*t);
        res = min(res, k * h / t); // Larger k = harder shadows
        if (res < 0.001) break;
        t += clamp(h, 0.01, 0.5);
    }
    return clamp(res, 0.0, 1.0);
}
```
