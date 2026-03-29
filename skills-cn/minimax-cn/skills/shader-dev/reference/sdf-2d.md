# 2D SDF 详细参考

该文件包含 [SKILL.md](SKILL.md) 的完整分步教程、数学推导、详细解释和高级用法。

## 先决条件

- **GLSL 基础知识**：统一、变化、内置函数（长度、点、钳位、混合、smoothstep、step、sign、abs、max、min）
- **矢量数学**：2D 向量运算、点积和叉积的几何意义
- **坐标系**：从屏幕坐标到标准化设备坐标（NDC）的转换，长宽比校正
- **有符号距离场概念**：函数返回到形状边界的有符号距离 - 内部为负，边界为零，外部为正

## 核心原则详细信息

2D SDF 的核心思想：**对于屏幕上的每个像素，计算其到目标形状边界的最短符号距离“d”**。

- `d < 0`：像素位于形状内部
- `d = 0`：像素正好在边界上
- `d > 0`：像素位于形状之外

获得距离值“d”后，使用“smoothstep”和“clamp”等函数将其映射到颜色/不透明度，从而实现：
- **填充**：当`d < 0`时的颜色
- **抗锯齿边缘**：`smoothstep(-aa, aa, d)`用于边界处的子像素平滑
- **描边**：在“abs(d) - 描边宽度”上再次应用 smoothstep
- **布尔运算**：`min(d1, d2)` = 并集，`max(d1, d2)` = 交集，`max(-d1, d2)` = 减法

关键数学公式：```
Circle:       d = length(p - center) - radius
Rectangle:    d = length(max(abs(p) - halfSize, 0.0)) + min(max(abs(p).x - halfSize.x, abs(p).y - halfSize.y), 0.0)
Line segment: d = length(p - a - clamp(dot(p-a, b-a)/dot(b-a, b-a), 0, 1) * (b-a)) - width/2
Union:        d = min(d1, d2)
Intersection: d = max(d1, d2)
Subtraction:  d = max(-d1, d2)
Smooth union: d = mix(d2, d1, h) - k*h*(1-h),  h = clamp(0.5 + 0.5*(d2-d1)/k, 0, 1)
```## 详细实施步骤

### 第 1 步：坐标归一化和纵横比校正

**什么**：将屏幕像素坐标转换为以屏幕中心为中心的归一化坐标，y 范围为 [-1, 1]。

**为什么**：像素坐标取决于分辨率。归一化后，SDF参数（例如半径）具有与分辨率无关的物理意义。除以“iResolution.y”（而不是“.x”）可确保正确的纵横比，这样圆形就不会变成椭圆形。

**代码**：```glsl
// Method 1: Origin at center, y range [-1, 1] (most common, standard practice)
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Method 2: If you need to work in pixel space (suitable for fixed pixel-size UI)
vec2 p = fragCoord.xy;
vec2 center = iResolution.xy * 0.5;

// Method 3: [0, 1] range normalization (requires manual aspect ratio handling)
vec2 uv = fragCoord.xy / iResolution.xy;
```### 步骤 2：定义 SDF 原语函数

**什么**：编写返回有符号距离的基本原语函数。每个函数都采用当前点“p”和形状参数，并返回一个“float”距离值。

**为什么**：这些是所有 2D SDF 图形的原子构建块。将它们封装为独立的函数，可以自由组合、转换和复用。

**代码**：```glsl
// ---- Circle ----
// The most basic SDF: distance from point to center minus radius
float sdCircle(vec2 p, float radius) {
    return length(p) - radius;
}

// ---- Rectangle (optional rounded corners) ----
// halfSize is half-width and half-height, radius is the corner radius
float sdBox(vec2 p, vec2 halfSize, float radius) {
    halfSize -= vec2(radius);
    vec2 d = abs(p) - halfSize;
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - radius;
}

// ---- Line Segment ----
// Line segment from start to end, with width
float sdLine(vec2 p, vec2 start, vec2 end, float width) {
    vec2 dir = end - start;
    float h = clamp(dot(p - start, dir) / dot(dir, dir), 0.0, 1.0);
    return length(p - start - dir * h) - width * 0.5;
}

// ---- Triangle (exact signed distance) ----
// Three vertices p0, p1, p2, only one sqrt needed
float sdTriangle(vec2 p, vec2 p0, vec2 p1, vec2 p2) {
    vec2 e0 = p1 - p0, v0 = p - p0;
    vec2 e1 = p2 - p1, v1 = p - p1;
    vec2 e2 = p0 - p2, v2 = p - p2;

    // Squared distance to each edge (projection + clamp)
    float d0 = dot(v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0),
                   v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0));
    float d1 = dot(v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0),
                   v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0));
    float d2 = dot(v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0),
                   v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0));

    // Determine inside/outside using cross product sign
    float o = e0.x * e2.y - e0.y * e2.x;
    vec2 d = min(min(vec2(d0, o * (v0.x * e0.y - v0.y * e0.x)),
                     vec2(d1, o * (v1.x * e1.y - v1.y * e1.x))),
                     vec2(d2, o * (v2.x * e2.y - v2.y * e2.x)));
    return -sqrt(d.x) * sign(d.y);
}

// ---- Ellipse (approximate) ----
// Simplified ellipse SDF based on scaled space
float sdEllipse(vec2 p, vec2 center, float a, float b) {
    float a2 = a * a, b2 = b * b;
    vec2 d = p - center;
    return (b2 * d.x * d.x + a2 * d.y * d.y - a2 * b2) / (a2 * b2);
}
```### 步骤 3：CSG 布尔运算

**什么**：使用最小/最大运算组合两个 SDF 距离值，以实现形状的并集、减法和交集。

**为什么**：这是 SDF 最强大的功能——从简单的基元构建任意复杂的形状。 `min` 采用两个字段值中较小的一个来生成并集（因为较小的距离意味着“更接近”形状内部）； max 取较大值进行交集； `max(a, -b)` 反转 b 的内部/外部并相交进行减法。

**代码**：```glsl
// Union: take the nearest shape
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

// Intersection: overlapping region of both shapes
float opIntersect(float d1, float d2) {
    return max(d1, d2);
}

// Subtraction: carve d1 out of d2
float opSubtract(float d1, float d2) {
    return max(-d1, d2);
}

// Smooth union: produces a rounded transition at the junction, k controls transition width
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

// XOR: non-overlapping region of both shapes
float opXor(float d1, float d2) {
    return min(max(-d1, d2), max(-d2, d1));
}
```### 步骤 4：坐标变换

**内容**：在计算 SDF 之前变换坐标，以便形状出现在所需的位置和角度。

**为什么**：SDF 函数默认定义以原点为中心的形状。通过变换输入坐标（而不是形状本身），您可以在场景中自由放置和旋转多个图元，而不会影响距离场的数学属性。

**代码**：```glsl
// Translation: move the coordinate origin to position t
vec2 translate(vec2 p, vec2 t) {
    return p - t;
}

// Counter-clockwise rotation
vec2 rotateCCW(vec2 p, float angle) {
    mat2 m = mat2(cos(angle), sin(angle), -sin(angle), cos(angle));
    return p * m;
}

// Usage example: translate then rotate
float d = sdBox(rotateCCW(translate(p, vec2(0.5, 0.3)), iTime), vec2(0.2), 0.05);
```### 步骤 5：距离场可视化和渲染

**什么**：将 SDF 距离值转换为最终颜色输出。包括填充、抗锯齿、描边、轮廓线和其他可视化方法。

**为什么**：距离值本身只是一个标量，需要映射策略才能成为视觉效果。 “smoothstep”在边界处创建亚像素平滑过渡，避免硬边缘出现锯齿。 “fwidth”函数使用屏幕空间导数自动计算像素宽度，实现与分辨率无关的抗锯齿。

**代码**：```glsl
// ---- Method 1: clamp for simple alpha (most basic) ----
float t = clamp(d, 0.0, 1.0);
vec4 shapeColor = vec4(color, 1.0 - t);

// ---- Method 2: smoothstep anti-aliasing (recommended general approach) ----
// aa controls edge softness, typical value is pixel size px = 2.0/iResolution.y
float px = 2.0 / iResolution.y;                      // Adjustable: anti-aliasing width
float mask = smoothstep(px, -px, d);                  // 1.0 inside, 0.0 outside
vec3 col = mix(backgroundColor, shapeColor, mask);

// ---- Method 3: fwidth adaptive anti-aliasing (suitable for zooming scenes) ----
float anti = fwidth(d) * 1.0;                         // Adjustable: multiplier, larger = softer edges
float mask = 1.0 - smoothstep(-anti, anti, d);

// ---- Method 4: Classic distance field debug visualization ----
vec3 col = (d > 0.0) ? vec3(0.9, 0.6, 0.3)           // Outside: orange
                      : vec3(0.65, 0.85, 1.0);        // Inside: blue
col *= 1.0 - exp(-12.0 * abs(d));                     // Distance falloff
col *= 0.8 + 0.2 * cos(120.0 * d);                    // Contour lines, 120.0 adjustable: line density
col = mix(col, vec3(1.0), smoothstep(1.5*px, 0.0, abs(d) - 0.002)); // Zero contour highlight
```### 步骤 6：描边和边框渲染

**什么**：使用距离场的绝对值来提取形状的轮廓，或者分别渲染内/外边框。

**为什么**：笔画是 SDF 的自然副产品 - `abs(d)` 给出无符号距离，减去笔画宽度产生“笔画形状”SDF。与需要几何扩展的光栅化笔划不同，SDF 笔划仅需要一行数学运算。

**代码**：```glsl
// ---- Fill mask ----
float fillMask(float d) {
    return clamp(-d, 0.0, 1.0);
}

// ---- Stroke rendering (fwidth adaptive) ----
// stroke is the stroke width (in distance field units)
vec4 renderShape(float d, vec3 color, float stroke) {
    float anti = fwidth(d) * 1.0;
    vec4 strokeLayer = vec4(vec3(0.05), 1.0 - smoothstep(-anti, anti, d - stroke));
    vec4 colorLayer  = vec4(color,      1.0 - smoothstep(-anti, anti, d));
    if (stroke < 0.0001) return colorLayer;
    return vec4(mix(strokeLayer.rgb, colorLayer.rgb, colorLayer.a), strokeLayer.a);
}

// ---- Inner border mask ----
float innerBorderMask(float d, float width) {
    return clamp(d + width, 0.0, 1.0) - clamp(d, 0.0, 1.0);
}

// ---- Outer border mask ----
float outerBorderMask(float d, float width) {
    return clamp(d, 0.0, 1.0) - clamp(d - width, 0.0, 1.0);
}
```### 步骤 7：多层合成

**什么**：将多个 SDF 形状渲染为具有 Alpha 通道的图层，然后使用“mix”将它们从后到前混合。

**原因**：复杂的 2D 场景通常包含背景、多个形状、笔划和其他视觉层。将每个 SDF 渲染为独立的 RGBA 层，并使用标准 alpha 混合（`mix(bottom, top, top.a)`）逐层合成它们，既直观又可以精确控制堆叠顺序。

**代码**：```glsl
// Background layer
vec3 bgColor = vec3(1.0, 0.8, 0.7 - 0.07 * p.y) * (1.0 - 0.25 * length(p));

// Shape layer 1
float d1 = sdCircle(translate(p, pos1), 0.3);
vec4 layer1 = renderShape(d1, vec3(0.9, 0.3, 0.2), 0.02);

// Shape layer 2
float d2 = sdBox(translate(p, pos2), vec2(0.2), 0.05);
vec4 layer2 = renderShape(d2, vec3(0.2, 0.5, 0.8), 0.0);

// Composite back-to-front
vec3 col = bgColor;
col = mix(col, layer1.rgb, layer1.a);   // Overlay shape 1
col = mix(col, layer2.rgb, layer2.a);   // Overlay shape 2

fragColor = vec4(col, 1.0);
```## 变体详细说明

### 变体 1：实心填充 + 描边模式

**与基本版本的区别**：不显示距离场调试颜色，而是以干净的笔触渲染实体形状，适用于 UI 和图标。

**关键修改代码**：```glsl
// Replace the distance field visualization section
vec3 shapeColor = vec3(0.32, 0.56, 0.53);
float strokeW = 0.015;   // Adjustable: stroke width
vec4 shape = render(d, shapeColor, strokeW);

vec3 col = bgCol;
col = mix(col, shape.rgb, shape.a);
```### 变体 2：多层 CSG 插图

**与基础版本的区别**：将多个SDF基元通过布尔运算组合成复杂的图案（例如雨伞、标志），每层独立着色并逐层合成。适用于 2D 插图和图标构建。

**关键修改代码**：```glsl
// Build the body (ellipse intersection)
float a = sdEllipse(p, vec2(0.0, 0.16), 0.25, 0.25);
float b = sdEllipse(p, vec2(0.0, -0.03), 0.8, 0.35);
float body = opIntersect(a, b);
vec4 layer1 = render(body, vec3(0.32, 0.56, 0.53), fwidth(body) * 2.0);

// Build the handle (line segment + arc subtraction)
float handle = sdLine(p, vec2(0.0, 0.05), vec2(0.0, -0.42), 0.01);
float arc = sdCircle(translate(p, vec2(-0.04, -0.42)), 0.04);
float arcInner = sdCircle(translate(p, vec2(-0.04, -0.42)), 0.03);
handle = opUnion(handle, opSubtract(arcInner, arc));
vec4 layer0 = render(handle, vec3(0.4, 0.3, 0.28), STROKE_WIDTH);

// Composite
vec3 col = bgCol;
col = mix(col, layer0.rgb, layer0.a);
col = mix(col, layer1.rgb, layer1.a);
```### 变体 3：六角形网格平铺

**与基础版本的区别**：使用非正交坐标系域重复在屏幕上平铺SDF，每个单元格具有独立的ID以进行区分着色。适用于背景纹理和几何图案。

**关键修改代码**：```glsl
// Hexagonal grid function: returns (cellID.xy, edge distance, center distance)
vec4 hexagon(vec2 p) {
    vec2 q = vec2(p.x * 2.0 * 0.5773503, p.y + p.x * 0.5773503);
    vec2 pi = floor(q);
    vec2 pf = fract(q);
    float v = mod(pi.x + pi.y, 3.0);
    float ca = step(1.0, v);
    float cb = step(2.0, v);
    vec2 ma = step(pf.xy, pf.yx);
    float e = dot(ma, 1.0 - pf.yx + ca*(pf.x+pf.y-1.0) + cb*(pf.yx-2.0*pf.xy));
    p = vec2(q.x + floor(0.5 + p.y / 1.5), 4.0 * p.y / 3.0) * 0.5 + 0.5;
    float f = length((fract(p) - 0.5) * vec2(1.0, 0.85));
    return vec4(pi + ca - cb * ma, e, f);
}

// Usage
#define HEX_SCALE 8.0          // Adjustable: grid density
vec4 h = hexagon(HEX_SCALE * p + 0.5 * iTime);
vec3 col = 0.15 + 0.15 * hash1(h.xy + 1.2);          // Different gray per cell
col *= smoothstep(0.10, 0.11, h.z);                   // Edge lines
col *= smoothstep(0.10, 0.11, h.w);                   // Center falloff
```### 变体 4：有机形状（极坐标 SDF）

**与基本版本的区别**：使用极坐标“(atan, length)”定义形状边界函数，可以创建心形、花瓣、星星等非多边形有机形状。支持脉冲动画。

**关键修改代码**：```glsl
// Heart SDF (polar coordinate algebraic curve)
p.y -= 0.25;
float a = atan(p.x, p.y) / 3.141593;
float r = length(p);
float h = abs(a);
float d = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);

// Pulse animation
float tt = mod(iTime, 1.5) / 1.5;
float ss = pow(tt, 0.2) * 0.5 + 0.5;
ss = 1.0 + ss * 0.5 * sin(tt * 6.2831 * 3.0) * exp(-tt * 4.0);  // Adjustable: sin frequency controls pulse count

// Rendering
vec3 col = mix(bgCol, heartCol, smoothstep(-0.01, 0.01, d - r));
```### 变体 5：贝塞尔曲线 SDF

**与基本版本的区别**：通过求解三次方程（卡尔达诺公式）计算从点到二次贝塞尔曲线的精确符号距离。适用于弯曲文本、路径渲染等类似场景。

**关键修改代码**：```glsl
// Cubic equation solver (Cardano's formula)
vec3 solveCubic(float a, float b, float c) {
    float p = b - a*a/3.0, p3 = p*p*p;
    float q = a*(2.0*a*a - 9.0*b)/27.0 + c;
    float d = q*q + 4.0*p3/27.0;
    float offset = -a/3.0;
    if (d >= 0.0) {
        float z = sqrt(d);
        vec2 x = (vec2(z,-z) - q) / 2.0;
        vec2 uv = sign(x) * pow(abs(x), vec2(1.0/3.0));
        return vec3(offset + uv.x + uv.y);
    }
    float v = acos(-sqrt(-27.0/p3)*q/2.0) / 3.0;
    float m = cos(v), n = sin(v) * 1.732050808;
    return vec3(m+m, -n-m, n-m) * sqrt(-p/3.0) + offset;
}

// Bezier SDF (three control points A, B, C)
float sdBezier(vec2 A, vec2 B, vec2 C, vec2 p) {
    B = mix(B + vec2(1e-4), B, step(1e-6, abs(B*2.0-A-C)));
    vec2 a = B-A, b = A-B*2.0+C, c = a*2.0, d = A-p;
    vec3 k = vec3(3.*dot(a,b), 2.*dot(a,a)+dot(d,b), dot(d,a)) / dot(b,b);
    vec3 t = clamp(solveCubic(k.x, k.y, k.z), 0.0, 1.0);
    vec2 pos = A+(c+b*t.x)*t.x; float dis = length(pos-p);
    pos = A+(c+b*t.y)*t.y; dis = min(dis, length(pos-p));
    pos = A+(c+b*t.z)*t.z; dis = min(dis, length(pos-p));
    return dis * signBezier(A, B, C, p);   // signBezier uses barycentric coordinates to determine sign
}
```## 性能优化细节

### 1. 减少 sqrt 调用

在多边形 SDF（例如三角形）中，通过首先比较平方距离值并仅在最后对最小距离取“sqrt”，可以将多个“sqrt”调用减少为一次。这是三角形SDF实现背后的核心优化思想。```glsl
// Bad: sqrt on every edge
float d0 = length(v0 - e0 * h0);
float d1 = length(v1 - e1 * h1);
// Good: compare dot(v,v) squares, one sqrt at the end
float d0 = dot(proj0, proj0);
float d1 = dot(proj1, proj1);
return -sqrt(min(d0, d1)) * sign(...);
```### 2. fwidth 与固定像素宽度

`fwidth(d)` 调用屏幕空间偏导数。在简单的场景中，可以用固定的`px = 2.0/iResolution.y`来代替，以减少GPU导数计算开销。然而，在有坐标缩放/扭曲的场景中（比如六边形网格的`pos *= 1.2 + 0.15*length(pos)`），必须使用`fwidth`来保证正确的抗锯齿宽度。

### 3.避免过多的布尔运算嵌套

大量的“最小”/“最大”嵌套是正确的，但计算每帧每个像素的所有基元的距离可能会很昂贵。您可以通过检查粗略的边界框来跳过远处的基元：```glsl
// Only compute precisely when near the shape
if (length(p - shapeCenter) < shapeRadius + margin) {
    d = opUnion(d, sdComplexShape(p));
}
```### 4. 超级采样 AA 权衡

多个样本（例如 2x2 超级采样）可产生更高质量的抗锯齿效果，但会将片段着色器计算乘以 4：```glsl
#define AA 2  // Adjustable: 1 = no supersampling, 2 = 4x, 3 = 9x
for (int m = 0; m < AA; m++)
for (int n = 0; n < AA; n++) {
    vec2 off = vec2(m, n) / float(AA);
    // ... computation ...
    tot += col;
}
tot /= float(AA * AA);
```对于大多数实时场景，具有“smoothstep”或“fwidth”的单像素 AA 就足够了。超级采样主要用于离线渲染或展示场景。

### 5. 2D 软阴影的步长优化

在圆锥形行进 2D 软阴影中，使用“max(1.0, abs(sd))”而不是固定步长大小，以在开放区域中进行大跳跃并在形状附近进行小精确步骤。通常 64 个步骤可以覆盖一个大场景：```glsl
dt += max(1.0, abs(sd));  // Adaptive step size
if (dt > dl) break;       // Early exit after reaching the light source
```## 详细组合建议

### 1.SDF + 噪声纹理

将噪声值添加到距离场会产生溶解、侵蚀和有机边缘效果：```glsl
float d = sdCircle(p, 0.4);
d += noise(p * 10.0 + iTime) * 0.05;  // Organic jittery edges
```### 2.SDF + 2D 灯光和阴影

基于距离场的圆锥行进实现了2D场景的实时软阴影和多光照明。距离字段提供“场景查询”功能，在光线行进期间使用“sceneDist()”来检查遮挡：```glsl
// 2D soft shadow (see 4dfXDn for full implementation)
float shadow(vec2 p, vec2 lightPos, float radius) {
    vec2 dir = normalize(lightPos - p);
    float dl = length(p - lightPos);
    float lf = radius * dl;
    float dt = 0.01;
    for (int i = 0; i < 64; i++) {
        float sd = sceneDist(p + dir * dt);
        if (sd < -radius) return 0.0;
        lf = min(lf, sd / dt);
        dt += max(1.0, abs(sd));
        if (dt > dl) break;
    }
    lf = clamp((lf*dl + radius) / (2.0*radius), 0.0, 1.0);
    return smoothstep(0.0, 1.0, lf);
}
```### 3.SDF + 法线贴图/凹凸贴图

通过距离场上的有限差计算法线，然后应用标准光照模型，您可以在 2D SDF 上模拟 3D 凹凸/高光效果（如在 DVD Bounce 着色器中所做的那样）：```glsl
vec2 e = vec2(0.8, 0.0) / iResolution.y;
float fx = sceneDist(p) - sceneDist(p + e);
float fy = sceneDist(p) - sceneDist(p + e.yx);
vec3 nor = normalize(vec3(fx, fy, e.x / 0.1));  // 0.1 = bump factor, adjustable
// Standard Blinn-Phong lighting
vec3 lig = normalize(vec3(1.0, 2.0, 2.0));
float dif = clamp(dot(lig, nor), 0.0, 1.0);
```### 4. SDF + 域重复（空间平铺）

在坐标上使用 `fract` 或 `mod` 来无限重复；使用“floor”获取单元格ID以进行区分着色。适用于背景图案、粒子阵列等：```glsl
vec2 cellSize = vec2(0.5);
vec2 cellID = floor(p / cellSize);
vec2 cellP = fract(p / cellSize) - 0.5;        // Local coordinate within cell
float d = sdCircle(cellP, 0.15 + 0.05 * sin(iTime + cellID.x * 3.0));
```### 5.SDF + 动画

距离场参数（位置、半径、旋转角度）自然支持连续动画。与 `sin/cos` 周期运动、`exp` 衰减、`mod` 循环和其他时间函数结合：```glsl
// Bouncing
float y = abs(sin(iTime * 3.0)) * 0.5;
float d = sdCircle(translate(p, vec2(0.0, y)), 0.2);

// Pulse scaling
float pulse = 1.0 + 0.1 * sin(iTime * 6.28 * 2.0) * exp(-mod(iTime, 1.0) * 4.0);
float d = sdCircle(p / pulse, 0.3) * pulse;

// Rotation
float d = sdBox(rotateCCW(p, iTime), vec2(0.2), 0.03);
```## 扩展 2D SDF 基元参考

### sdRoundedBox — 具有独立角半径的圆角框

**签名**：`float sdRoundedBox(vec2 p, vec2 b, vec4 r)`

- `p`: 查询点
- `b`：盒子的一半大小
- `r`：角半径为 `vec4(右上、右下、左上、左下)`

根据“p”的象限选择适当的角半径，然后计算标准圆角框距离。对于每个角需要不同圆角的 UI 元素很有用。

### sdOrientedBox — 定向框

**签名**：`float sdOrientedBox(vec2 p, vec2 a, vec2 b, float th)`

- `p`: 查询点
- `a`, `b`：定义盒子中心轴的端点
- `th`：厚度（垂直于轴的全宽）

构造一个与线段“a”到“b”对齐的局部坐标系，然后评估标准框 SDF。用于以任意角度绘制粗线状矩形，无需手动旋转。

### sdArc — 弧

**签名**：`float sdArc(vec2 p, vec2 sc, float ra, float rb)`

- `p`: 查询点
- `sc`: 半孔径角的`vec2(sin, cos)`
- `ra`: 圆弧半径
- `rb`：圆弧厚度

计算到圆弧段的距离。孔径关于 y 轴对称。将角度夹紧与径向距离相结合。

### sdPie — 饼图/扇区

**签名**：`float sdPie(vec2 p, vec2 c, float r)`

- `p`: 查询点
- `c`: 半孔径角的`vec2(sin, cos)`
- `r`：半径

返回填充饼图（扇形）形状的带符号距离。该扇区关于 y 轴对称。

### sdRing — 环

**签名**：`float sdRing(vec2 p, vec2 n, float r, float th)`

- `p`: 查询点
- `n`: 半孔径角的`vec2(sin, cos)`
- `r`：环半径
- `th`: 环厚度

与“sdArc”类似，但具有有上限的端点和孔径内的全环行为。

### sdMoon — 月亮形状

**签名**：`float sdMoon(vec2 p, float d, float ra, float rb)`

- `p`: 查询点
- `d`：圆心之间的距离
- `ra`: 外圆半径
- `rb`：内（减去）圆的半径

通过用一个圆减去另一个圆来创建新月/月亮形状。两个圆沿 x 轴偏移距离“d”。

### sdHeart — 心（大约）

**签名**：`float sdHeart(vec2 p)`

- `p`：查询点（以原点为中心，大致单位比例）

由缝合在一起的两个几何区域组成的近似心脏 SDF。该形状大致从 (0,0) 垂直延伸到 (0,1)。

### sdVesica — Vesica / 镜片形状

**签名**：`float sdVesica(vec2 p, float w, float h)`

- `p`: 查询点
- `w`: 囊泡的宽度
- `h`: 囊泡的高度

由两个圆相交形成的透镜状图形（vesica piscis）。关于两个轴对称。

### sdEgg — 鸡蛋形状

**签名**：`float sdEgg(vec2 p, float he, float ra, float rb)`

- `p`: 查询点
- `he`: 直线部分的半高
- `ra`：底部半径
- `rb`：顶部半径

产生顶部和底部具有不同半径的蛋状形状，通过直垂直部分连接。

### sdEquiteriorTriangle — 等边三角形

**签名**：`float sdEquisideTriangle(vec2 p, float r)`

- `p`: 查询点
- `r`：边长/比例

使用对称折叠以原点为中心的等边三角形的精确 SDF。

### sdPentagon — 五角大楼

**签名**：`float sdPentagon(vec2 p, float r)`

- `p`: 查询点
- `r`：外接半径

规则五边形 SDF 使用沿五边形边缘法线的镜像折叠操作。这些常数编码 72 度角的 cos/sin。

### sdHexagon — 六角形

**签名**：`float sdHexagon(vec2 p, float r)`

- `p`: 查询点
- `r`：外接半径

正六边形 SDF。常量编码 cos(30)、sin(30) 和 tan(30)。使用单镜面折叠。

### sdOctagon — 八边形

**签名**：`float sdOctagon(vec2 p, float r)`

- `p`: 查询点
- `r`：外接半径

正八边形 SDF。使用 22.5 度和 67.5 度角的两种镜面折叠。

### sdStar — N 角星

**签名**：`float sdStar(vec2 p, float r, int n, float m)`

- `p`: 查询点
- `r`：外半径
- `n`：点数
- `m`：内半径比（控制尖度；典型范围 2.0-6.0）

使用角度重复 (`mod(atan(...))`) 和边缘投影的一般 n 角星。较高的“m”值会产生更尖锐、更细的点。

### sdBezier（扩展）— 二次贝塞尔曲线 SDF

**签名**：`float sdBezier(vec2 pos, vec2 A, vec2 B, vec2 C)`

- `pos`: 查询点- `A`、`B`、`C`：二次贝塞尔曲线的控制点

另一种 Bezier SDF 公式使用三次公式求解曲线上的最近点。返回无符号距离（无符号）。请注意与 Variant 5 版本不同的参数顺序。

### sdParabola — 抛物线

**签名**：`float sdParabola(vec2 pos, float k)`

- `pos`: 查询点
- `k`：曲率系数 (y = k * x^2)

抛物线的有符号距离。使用三次根解来查找曲线上最接近的点。

### sdCross — 十字形状

**签名**：`float sdCross(vec2 p, vec2 b, float r)`

- `p`: 查询点
- `b`：每个臂的一半长度（b.x = 长度，b.y = 宽度）
- `r`：圆角偏移

由两个垂直矩形合并形成的加号/十字形状，具有可选的舍入参数。

## 2D SDF 修改器参考

### opRound2D — 舍入修饰符

**签名**：`float opRound2D(float d, float r)`

从任何 SDF 中减去“r”，通过“r”有效地向外扩展形状边界并圆化所有角/边缘。应用于任何现有的 SDF 以添加统一舍入。

### opAnnular2D — 环形（空心）修改器

**签名**：`float opAnnular2D(float d, float r)`

取距离的绝对值并减去厚度“r”，将任何填充形状转换为壁厚为“2*r”的环形/轮廓版本。可堆叠：涂抹两次可形成同心环。

### opRepeat2D — 网格重复

**签名**：`vec2 opRepeat2D(vec2 p, float s)`

应用“mod”将坐标折叠到大小为“s”的重复网格单元中。在传递到任何 SDF 之前应用到“p”以创建无限平铺。使用“floor(p / s)”获取每个单元格变化的单元格 ID。

### opMirror2D — 任意镜像

**签名**：`vec2 opMirror2D(vec2 p, vec2 dir)`

以“dir”方向镜像穿过原点的线的坐标（应标准化）。线负侧的任何点都会反射到正侧，从而有效地沿任意轴创建双边对称。