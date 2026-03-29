# 2D 程序模式 - 详细参考

本文档是对[SKILL.md](SKILL.md)的完整补充，包含先决条件、每个步骤的详细说明、变体描述、深入的性能分析和组合示例代码。

---

## 先决条件

- **GLSL 基本语法**：统一、变化、内置函数
- **向量数学**：`dot`、`length`、`normalize`、`atan`
- **坐标空间概念**：UV归一化、纵横比校正
- **基本数学函数**：`sin`/`cos`、`fract`/`floor`/`mod`、`smoothstep`、`pow`
- **极坐标**：`atan(y,x)` 返回角度，`length` 返回径向距离

---

## 核心原则详细信息

2D 程序模式的本质是**域变换 + 距离场 + 颜色映射** 的组合：

1. **域重复**：使用`fract()`/`mod()`将无限平面折叠成有限单元，每个单元独立渲染相同（或变体）的图案
2. **单元格识别**：使用`floor()`提取当前单元格的整数坐标作为哈希种子来生成伪随机数，驱动每个单元格的独立变化
3. **距离场（SDF）**：使用数学函数计算从像素到几何形状（圆形、六边形、线段、弧）的距离，通过“smoothstep”转换为清晰或柔和的边缘
4. **颜色映射**：余弦调色板 `a + b*cos(2pi(c*t+d))` 或 HSV 映射，将标量值转换为丰富的颜色
5. **分层合成**：通过加法、乘法或“混合”组合多个循环或多层传递的结果以构建视觉复杂性

---

## 详细实施步骤

### 第 1 步：UV 坐标归一化和纵横比校正

**什么**：将像素坐标转换为以屏幕为中心、Y 轴范围为 [-1, 1] 的标准化坐标

**Why**: A unified coordinate system ensures patterns don't distort with resolution changes;使用 Y 轴作为参考保持方形像素```glsl
vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;
```### 步骤 2：域重复 — 将空间划分为重复单元

**什么**：缩放UV坐标并取小数部分生成重复的局部坐标；使用“floor”同时提取单元格 ID

**为什么**： `fract()` 将无限平面折叠到重复的 [0,1) 空间中，`floor()` 为后续随机化提供了唯一的单元格标识符。减去0.5中心原点```glsl
#define SCALE 4.0 // Tunable: repetition density, higher = more cells
vec2 cell_uv = fract(uv * SCALE) - 0.5;
vec2 cell_id = floor(uv * SCALE);
```Error 500 (Server Error)!!1500.That’s an error.There was an error. Please try again later.That’s all we know.```glsl
const vec2 s = vec2(1, 1.7320508); // 1 and sqrt(3)
vec4 hC = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
vec4 h = vec4(p - hC.xy * s, p - (hC.zw + 0.5) * s);
// Take the nearest hexagonal center
vec4 hex_data = dot(h.xy, h.xy) < dot(h.zw, h.zw)
    ? vec4(h.xy, hC.xy)
    : vec4(h.zw, hC.zw + vec2(0.5, 1.0));
```### 步骤 3：细胞随机化

**什么**：使用单元格 ID 生成伪随机数，为每个单元格提供不同的属性（大小、位置、颜色偏移）

**为什么**：纯粹的重复看起来很机械；随机化赋予模式“程序化但生动”的品质```glsl
float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(141.173, 289.927))) * 43758.5453);
}

float rnd = hash21(cell_id);
float radius = 0.15 + 0.1 * rnd; // Tunable: base radius and random range
```### 步骤 4：距离场形状渲染

**什么**：计算从像素到目标形状的距离，然后使用“smoothstep”转换为可视化

**为什么**：SDF 是程序图形的基石 - 单个标量值同时编码形状、边缘和发光效果```glsl
// Circle SDF
float d = length(cell_uv) - radius;

// Hexagon SDF
float hex_sdf(vec2 p) {
    p = abs(p);
    return max(dot(p, vec2(0.5, 0.866025)), p.x);
}

// Line segment SDF (for networks/grid lines)
float line_sdf(vec2 a, vec2 b, vec2 p) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Anti-aliased rendering with smoothstep
float shape = 1.0 - smoothstep(radius - 0.008, radius + 0.008, length(cell_uv));
```### 步骤 5：极坐标转换和环形/弧形图案

**什么**：将笛卡尔坐标转换为极坐标，使用径向距离绘制同心环，使用角度绘制扇形/弧段

**为什么**：极坐标自然适合雷达扫描、同心圆、螺旋和其他径向对称图案```glsl
vec2 polar = vec2(length(uv), atan(uv.y, uv.x));
float ring_id = floor(polar.x * NUM_RINGS + 0.5) / NUM_RINGS; // Tunable: NUM_RINGS ring count

// Concentric rings
float ring = 1.0 - pow(abs(sin(polar.x * 3.14159 * NUM_RINGS)) * 1.25, 2.5);

// Arc segment clipping
float arc_end = polar.y + sin(iTime + ring_id * 5.5) * 1.52 - 1.5;
ring *= smoothstep(0.0, 0.05, arc_end);
```### 步骤 6：余弦调色板

**什么**：使用四个 vec3 参数生成连续的彩虹颜色映射函数

**为什么**：单行代码生成无限平滑的配色方案，比查找表更灵活且对 GPU 友好```glsl
vec3 palette(float t) {
    // Tunable: modify a/b/c/d to change color scheme
    vec3 a = vec3(0.5, 0.5, 0.5);       // Brightness offset
    vec3 b = vec3(0.5, 0.5, 0.5);       // Amplitude
    vec3 c = vec3(1.0, 1.0, 1.0);       // Frequency
    vec3 d = vec3(0.263, 0.416, 0.557);  // Phase offset
    return a + b * cos(6.28318 * (c * t + d));
}
```### 步骤 7：迭代堆叠和发光效果

**什么**：循环反复进行域重复+距离场计算，累加颜色；使用 `pow(1/d)` 产生发光

**为什么**：单层图案太简单；多层迭代堆叠以最少的代码产生类似分形的视觉复杂性。指数衰减的辉光赋予图案霓虹灯的感觉```glsl
#define NUM_LAYERS 4.0 // Tunable: number of iteration layers, more = more complex
vec3 finalColor = vec3(0.0);
vec2 uv0 = uv; // Preserve original UV for global coloring

for (float i = 0.0; i < NUM_LAYERS; i++) {
    uv = fract(uv * 1.5) - 0.5;    // Tunable: 1.5 is the scale factor
    float d = length(uv) * exp(-length(uv0));
    vec3 col = palette(length(uv0) + i * 0.4 + iTime * 0.4);
    d = sin(d * 8.0 + iTime) / 8.0; // Tunable: 8.0 is the ripple frequency
    d = abs(d);
    d = pow(0.01 / d, 1.2);         // Tunable: 0.01 is glow width, 1.2 is decay exponent
    finalColor += col * d;
}
```### 步骤 8：三角干涉图案

**什么**：使用 `sin`/`cos` 在迭代中相互扰动坐标，生成类似水焦散的干涉图案

**为什么**：三角函数的叠加会产生复杂的莫尔式干涉图案；几次迭代产生高度有机的视觉效果```glsl
#define MAX_ITER 5 // Tunable: iteration count, more = richer detail
vec2 p = mod(uv * TAU, TAU) - 250.0; // TAU period ensures tileability
vec2 i = p;
float c = 1.0;
float inten = 0.005; // Tunable: intensity coefficient

for (int n = 0; n < MAX_ITER; n++) {
    float t = iTime * (1.0 - 3.5 / float(n + 1));
    i = p + vec2(cos(t - i.x) + sin(t + i.y),
                 sin(t - i.y) + cos(t + i.x));
    c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten),
                            p.y / (cos(i.y + t) / inten)));
}
c /= float(MAX_ITER);
c = 1.17 - pow(c, 1.4); // Tunable: 1.4 is the contrast exponent
vec3 colour = vec3(pow(abs(c), 8.0));
```### 步骤 9：多层深度合成

**什么**：在不同的缩放级别渲染相同的图案，使用深度淡入/淡出来模拟视差

**为什么**：多尺度堆叠打破了单尺度的机械感，产生伪3D深度效果```glsl
#define NUM_DEPTH_LAYERS 4.0 // Tunable: number of depth layers
float m = 0.0;
for (float i = 0.0; i < 1.0; i += 1.0 / NUM_DEPTH_LAYERS) {
    float z = fract(iTime * 0.1 + i);
    float size = mix(15.0, 1.0, z);    // Dense far away, sparse up close
    float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z); // Fade at both ends
    m += fade * patternLayer(uv * size, i, iTime);
}
```### 步骤 10：后处理管道

**内容**：依次应用伽玛校正、对比度增强、饱和度调整和晕影

**为什么**：后处理将“技术上正确”的输出转换为“视觉上令人愉悦的”最终结果```glsl
// Gamma correction
col = pow(clamp(col, 0.0, 1.0), vec3(1.0 / 2.2));
// Contrast enhancement (S-curve)
col = col * 0.6 + 0.4 * col * col * (3.0 - 2.0 * col);
// Saturation adjustment
col = mix(col, vec3(dot(col, vec3(0.33))), -0.4); // Tunable: -0.4 increases saturation, positive reduces it
// Vignette
vec2 q = fragCoord / iResolution.xy;
col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.7);
```---

## 常见变体详细信息

### 变体 1：六角形网格 + Truchet 弧线

**与基础版本的区别**：用六边形网格坐标系替换方形网格，在每个六边形单元内绘制三个随机方向的圆弧；弧线在细胞之间形成迷宫般的连续路径

**关键修改代码**：```glsl
// Hexagon distance field
float hex(vec2 p) {
    p = abs(p);
    return max(dot(p, vec2(0.5, 0.866025)), p.x);
}

// Hexagonal grid coordinates (returns xy=cell-local coords, zw=cell ID)
const vec2 s = vec2(1.0, 1.7320508);
vec4 getHex(vec2 p) {
    vec4 hC = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
    vec4 h = vec4(p - hC.xy * s, p - (hC.zw + 0.5) * s);
    return dot(h.xy, h.xy) < dot(h.zw, h.zw)
        ? vec4(h.xy, hC.xy)
        : vec4(h.zw, hC.zw + vec2(0.5, 1.0));
}

// Truchet three-arc: one arc for each of three directions
float r = 1.0;
vec2 q1 = p - vec2(0.0, r) / s;
vec2 q2 = rot2(6.28318 / 3.0) * p - vec2(0.0, r) / s;
vec2 q3 = rot2(6.28318 * 2.0 / 3.0) * p - vec2(0.0, r) / s;
// Take nearest arc
float d = min(min(length(q1), length(q2)), length(q3));
d = abs(d - 0.288675) - 0.1; // 0.288675 = sqrt(3)/6, arc radius
```### 变体 2：水碱干扰图案

**与基础版本的区别**：不使用域重复网格；而是通过三角迭代生成全屏干扰纹理，无缝平铺

**关键修改代码**：```glsl
#define TAU 6.28318530718
#define MAX_ITER 5 // Tunable: iteration count

vec2 p = mod(uv * TAU, TAU) - 250.0;
vec2 i = p;
float c = 1.0;
float inten = 0.005;
for (int n = 0; n < MAX_ITER; n++) {
    float t = iTime * (1.0 - 3.5 / float(n + 1));
    i = p + vec2(cos(t - i.x) + sin(t + i.y),
                 sin(t - i.y) + cos(t + i.x));
    c += 1.0 / length(vec2(p.x / (sin(i.x + t) / inten),
                            p.y / (cos(i.y + t) / inten)));
}
c /= float(MAX_ITER);
c = 1.17 - pow(c, 1.4);
vec3 colour = vec3(pow(abs(c), 8.0));
colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0); // Aquatic color shift
```### 变体 3：极地同心环 + 动画弧段

**与基础版本的区别**：使用极坐标代替笛卡尔网格，用独立动画绘制同心环弧段，适合雷达/HUD风格

**关键修改代码**：```glsl
#define NUM_RINGS 20.0 // Tunable: ring count
#define PALETTE vec3(0.0, 1.4, 2.0) + 1.5

vec2 plr = vec2(length(p), atan(p.y, p.x));
float id = floor(plr.x * NUM_RINGS + 0.5) / NUM_RINGS;

// Each ring rotates independently
p *= rot2(id * 11.0);
p.y = abs(p.y); // Mirror symmetry

// Concentric ring SDF
float rz = 1.0 - pow(abs(sin(plr.x * 3.14159 * NUM_RINGS)) * 1.25, 2.5);

// Arc segment animation
float arc = plr.y + sin(iTime + id * 5.5) * 1.52 - 1.5;
rz *= smoothstep(0.0, 0.05, arc);

// Per-ring coloring
vec3 col = (sin(PALETTE + id * 5.0 + iTime) * 0.5 + 0.5) * rz;
```### 变体 4：多层深度视差网络

**与基础版本的区别**：以多个缩放级别渲染网格节点和连接，使用深度淡入/淡出产生伪 3D 效果

**关键修改代码**：```glsl
#define NUM_DEPTH_LAYERS 4.0 // Tunable: number of depth layers

// Random vertex position within each cell
vec2 GetPos(vec2 id, vec2 offs, float t) {
    float n = hash21(id + offs);
    return offs + vec2(sin(t + n * 6.28), cos(t + fract(n * 100.0) * 6.28)) * 0.4;
}

// Line segment SDF
float df_line(vec2 a, vec2 b, vec2 p) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Multi-layer compositing
float m = 0.0;
for (float i = 0.0; i < 1.0; i += 1.0 / NUM_DEPTH_LAYERS) {
    float z = fract(iTime * 0.1 + i);
    float size = mix(15.0, 1.0, z);
    float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z);
    m += fade * NetLayer(uv * size, i, iTime);
}
```### 变体 5：分形阿波罗图案

**与基础版本的区别**：使用迭代折叠和反转变换来生成无限详细的非周期性分形图案，并结合 HSV 着色

**关键修改代码**：```glsl
float apollian(vec4 p, float s) {
    float scale = 1.0;
    for (int i = 0; i < 7; ++i) {     // Tunable: iteration count (5~12)
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // Space folding
        float r2 = dot(p, p);
        float k = s / r2;              // Tunable: s is scaling factor (1.0~1.5)
        p *= k;                        // Inversion mapping
        scale *= k;
    }
    return abs(p.y) / scale;
}

// 4D slice animation for smooth morphing
vec4 pp = vec4(p.x, p.y, 0.0, 0.0) + offset;
pp.w = 0.125 * (1.0 - tanh(length(pp.xyz)));
float d = apollian(pp / 4.0, 1.2) * 4.0;

// HSV coloring
float hue = fract(0.75 * length(p) - 0.3 * iTime) + 0.3;
float sat = 0.75 * tanh(2.0 * length(p));
vec3 col = hsv2rgb(vec3(hue, sat, 1.0));
```---

## 深入的性能优化

### 1. 控制迭代次数
迭代循环是最大的性能瓶颈。将“NUM_LAYERS”从 4 增加到 8 会使性能减半。在移动设备上，将其保持在 3 层或更少。

### 2.避免分支
将 `if/else` 替换为无分支的 `step()`/`smoothstep()`/`mix()` 替代方案：```glsl
// Bad: if(rnd > 0.5) p.y = -p.y;
// Good: p.y *= sign(rnd - 0.5);  // or use mix
```### 3. 合并距离场计算
使用“min()”/“max()”组合多个形状 SDF 并应用单个“smoothstep”，而不是单独渲染每个形状。

### 4. 预计算常量
在循环外计算“sin”/“cos”对（例如旋转矩阵）；将无理数如 `1.7320508` (sqrt(3)) 写为直接常量。

### 5. 最小化 `atan` 调用
`atan` 是一个昂贵的函数。如果您只需要周期性的角度变化，请考虑使用“dot”进行近似。

### 6.LOD策略
减少距离/缩小时的迭代次数：```glsl
int iters = int(mix(3.0, float(MAX_ITER), smoothstep(0.0, 1.0, 1.0 / scale)));
```### 7. 使用 `smoothstep` 而不是 `pow`
在某些 GPU 上，`pow(x, n)` 比 `smoothstep` 慢，并且 `smoothstep` 自然会钳位到 [0,1]。

---

## 完整的组合建议示例

### 1. + 噪声纹理
在距离场上叠加 Perlin/Simplex 噪声扰动，赋予几何图案有机/侵蚀的感觉。三角噪声（如“Overly Satisfying”中所用）是一种高效、低成本的替代方案：```glsl
d += triangleNoise(uv * 10.0) * 0.05; // Noise perturbation amount is tunable
```### 2. + 后处理交叉影线
在图案上叠加交叉阴影效果以模拟手绘/版画风格（如“六角形迷宫流”中使用的）：```glsl
float gr = dot(col, vec3(0.299, 0.587, 0.114)); // Grayscale
float hatch = (gr < 0.45) ? clamp(sin((uv.x - uv.y) * 125.6) * 2.0 + 1.5, 0.0, 1.0) : 1.0;
col *= hatch * 0.5 + 0.5;
```### 3. + SDF 布尔运算
通过“min”（并集）、“max”（交集）和减法将多个基本模式组合成复杂的几何图形：```glsl
float d = max(hexSDF, -circleSDF); // Hexagon minus circle = hexagonal ring
```### 4. + 域扭曲
在域重复之前对 UV 应用正弦/余弦失真，产生流动/漩涡效果：```glsl
uv += 0.05 * vec2(sin(uv.y * 5.0 + iTime), sin(uv.x * 3.0 + iTime));
```### 5.+ 径向模糊/运动模糊
在最终颜色上对极坐标方向上的多个样本进行平均，产生旋转运动模糊以增强动态性。

### 6. + 伪 3D 光照
使用 SDF 渐变作为法线并添加简单的漫反射/镜面照明，为 2D 图案提供浮雕/浮雕外观（如“Apollian with a twin”阴影投射方法）。