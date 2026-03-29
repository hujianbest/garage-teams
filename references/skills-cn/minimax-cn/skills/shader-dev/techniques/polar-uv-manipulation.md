## WebGL2 适配要求

本文档中的代码模板使用 ShaderToy GLSL 风格。生成独立 HTML 页面时，必须适应 WebGL2：

- 使用`canvas.getContext("webgl2")`
- **重要：版本指令必须严格位于第一行**：将着色器代码注入 HTML 时，请确保“#version 300 es”之前没有任何内容 - 没有换行符、空格、注释或其他字符。常见陷阱：连接模板字符串时意外添加 `\n`，导致版本指令出现在第 2-3 行
- 着色器第一行：“#version 300 es”，为片段着色器添加“ precision highp float;”
- 顶点着色器：`attribute`→`in`、`variing`→`out`
- 片段着色器：`variing`→`in`、`gl_FragColor`→自定义`out vec4 fragColor`、`texture2D()`→`texture()`
- ShaderToy 的 `void mainImage(out vec4 fragColor, in vec2 fragCoord)` 必须适应标准的 `void main()` 条目

**重要：GLSL 类型严格警告**：
- `vec2 = float` 是非法的：类型必须完全匹配，例如，`float r = length(uv)` 而不是 `vec2 r = length(uv)`
- 函数返回类型必须匹配：常用的`fbm()` / `noise()`返回`float`，不能赋值给`vec2`
- 如果您需要 vec2 类型，请使用 `vec2(fbm(...), fbm(...))` 或 `vec2(value)` 构造函数

# 极坐标和 UV 操作

## 用例
- 径向对称效果：花朵、万花筒、齿轮、径向图案
- 螺旋图案：星系、漩涡、螺旋楼梯
- 环形/隧道效果：管飞行、环面扭曲、圆形 UI 元素
- 极坐标形状：心形、玫瑰曲线、星形以及由 r(θ) 定义的其他形状
- 漩涡动画：漩涡、旋转扭曲、纸牌游戏背景（例如 Balatro）
- 分形/重复结构：基于角度细分的递归对称模式

## 核心原则

极坐标将 (x, y) 转换为 (r, θ)：
- **r = length(p)** — 到原点的距离
- **θ = atan(y, x)** — 与正 x 轴的角度，范围 [-π, π]

逆变换：x = r·cos(θ), y = r·sin(θ)

操控效果：
- 修改 θ → 旋转、扭曲、万花筒
- 修改 r → 缩放、径向波纹
- θ += f(r) → 螺旋效应

|螺旋式|方程 |代码|
|------------|----------|------|
|阿基米德螺旋| r = a + bθ | `theta += 半径` |
|对数螺线| r = ae^(bθ) | `theta += log(半径)` |
|玫瑰曲线| r = cos(nθ) | `r - A*sin(n*theta)` |

## 实施步骤

### 第 1 步：UV 归一化和居中```glsl
// Range [-1, 1], most commonly used
vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);

// Range [-aspect, aspect] x [-1, 1]
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Pixelated style (Balatro style)
float pixel_size = length(iResolution.xy) / PIXEL_FILTER;
vec2 uv = (floor(fragCoord * (1.0/pixel_size)) * pixel_size - 0.5*iResolution.xy) / length(iResolution.xy);
```### 步骤 2：笛卡尔坐标 → 极坐标```glsl
float r = length(uv);
float theta = atan(uv.y, uv.x); // [-PI, PI]

// Reusable function
vec2 toPolar(vec2 p) { return vec2(length(p), atan(p.y, p.x)); }

// Normalized angle to [0, 1]
vec2 polar = vec2(atan(uv.y, uv.x) / 6.283 + 0.5, length(uv));
```### 步骤 3：极地空间行动

**3a。径向涡流**```glsl
float spin_amount = 0.25;
float new_theta = theta - spin_amount * 20.0 * r;
```**3b.角扭转**```glsl
float twist_angle = theta + 2.0 * iTime + sin(theta) * sin(iTime) * 3.14159;
```**3c。阿基米德螺旋**```glsl
vec2 spiral_uv = vec2(theta_normalized, r);
spiral_uv.y -= spiral_uv.x; // Unwrap into spiral band
```**3d。对数螺旋**```glsl
float shear = 2.0 * log(r);
float c = cos(shear), s = sin(shear);
mat2 spiral_mat = mat2(c, -s, s, c);
```**3e。万花筒**```glsl
float rep = 12.0;          // Number of symmetry axes
float sector = TAU / rep;
float a = polar.y;
float c_idx = floor((a + sector * 0.5) / sector);
a = mod(a + sector * 0.5, sector) - sector * 0.5;
a *= mod(c_idx, 2.0) * 2.0 - 1.0; // Mirror
```**3f。螺旋臂压缩**```glsl
float NB_ARMS = 5.0;
float COMPR = 0.1;
float phase = NB_ARMS * (theta - shear);
theta = theta - COMPR * cos(phase);
float arm_density = 1.0 + NB_ARMS * COMPR * sin(phase);
```### 步骤 4：极坐标 → 笛卡尔重建```glsl
vec2 new_uv = vec2(r * cos(new_theta), r * sin(new_theta));

vec2 toRect(vec2 p) { return vec2(p.x * cos(p.y), p.x * sin(p.y)); }

// Balatro-style round-trip (offset to screen center)
vec2 mid = (iResolution.xy / length(iResolution.xy)) / 2.0;
vec2 warped_uv = vec2(r * cos(new_theta) + mid.x, r * sin(new_theta) + mid.y) - mid;
```### 步骤 5：极坐标形状 SDF```glsl
// Cardioid
float a = atan(p.x, p.y) / 3.141593; // atan(x,y) makes the heart face upward
float h = abs(a);
float heart_r = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);
float dist = r - heart_r;

// Rose curve
float rose_dist = abs(r - A_coeff * sin(PETAL_FREQ * theta) - 0.5);

// Rendering
float shape = smoothstep(0.01, -0.01, dist);
```### 第 6 步：着色和抗锯齿```glsl
// fwidth adaptive anti-aliasing
float aa = smoothstep(-1.0, 1.0, value / fwidth(value));

// Resolution-based anti-aliasing
float aa_size = 2.0 / iResolution.y;
float edge = smoothstep(0.5 - aa_size, 0.5 + aa_size, value);

// Radial gradient coloring
vec3 color = vec3(1.0, 0.4 * r, 0.3);
color *= 1.0 - 0.4 * r;

// Inter-spiral-band anti-aliasing
float inter_spiral_aa = 1.0 - pow(abs(2.0 * fract(spiral_uv.y) - 1.0), 10.0);
```## 完整的代码模板```glsl
// === Polar Coordinates & UV Manipulation Complete Template ===
// Paste directly into ShaderToy to run

#define PI 3.14159265359
#define TAU 6.28318530718

// ===== Adjustable Parameters =====
#define MODE 0            // 0=swirl, 1=spiral, 2=kaleidoscope, 3=rose curve
#define SPIRAL_TYPE 0     // 0=Archimedean, 1=logarithmic (MODE=1)
#define NUM_ARMS 5.0      // Number of spiral arms (MODE=1)
#define KALEID_SEGMENTS 6.0 // Kaleidoscope segments (MODE=2)
#define PETAL_COUNT 5.0   // Number of petals (MODE=3)
#define SWIRL_STRENGTH 3.0 // Swirl intensity (MODE=0)
#define ANIM_SPEED 1.0    // Animation speed
#define COLOR_SCHEME 0    // 0=warm, 1=cool, 2=rainbow

vec2 toPolar(vec2 p) {
    return vec2(length(p), atan(p.y, p.x));
}

vec2 toRect(vec2 p) {
    return vec2(p.x * cos(p.y), p.x * sin(p.y));
}

vec2 kaleidoscope(vec2 polar, float segments) {
    float sector = TAU / segments;
    float a = polar.y;
    float c = floor((a + sector * 0.5) / sector);
    a = mod(a + sector * 0.5, sector) - sector * 0.5;
    a *= mod(c, 2.0) * 2.0 - 1.0;
    return vec2(polar.x, a);
}

vec3 getColor(float t, int scheme) {
    if (scheme == 1) return 0.5 + 0.5 * cos(TAU * (t + vec3(0.0, 0.33, 0.67)));
    if (scheme == 2) return 0.5 + 0.5 * cos(TAU * t + vec3(0.0, 2.1, 4.2));
    return vec3(1.0, 0.4 + 0.4 * cos(t * TAU), 0.3 + 0.2 * sin(t * TAU));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);
    vec2 polar = toPolar(uv);
    float r = polar.x;
    float theta = polar.y;
    float t = iTime * ANIM_SPEED;
    vec3 col = vec3(0.0);
    float aa = 2.0 / iResolution.y;

    #if MODE == 0
    // --- Swirl mode ---
    float swirl_theta = theta - SWIRL_STRENGTH * r + t;
    vec2 warped = toRect(vec2(r, swirl_theta));
    warped *= 10.0;
    float pattern = sin(warped.x) * cos(warped.y);
    pattern += 0.5 * sin(2.0 * warped.x + t) * cos(2.0 * warped.y - t);
    float val = smoothstep(-0.1, 0.1, pattern);
    col = mix(
        getColor(r * 0.5, COLOR_SCHEME),
        getColor(r * 0.5 + 0.5, COLOR_SCHEME),
        val
    );
    col *= exp(-r * 0.5);

    #elif MODE == 1
    // --- Spiral mode ---
    #if SPIRAL_TYPE == 0
        float spiral = theta / TAU + 0.5;
        float bands = spiral + r;
        bands -= t * 0.1;
        float arm = fract(bands * NUM_ARMS);
    #else
        float shear = 2.0 * log(max(r, 0.001));
        float phase = NUM_ARMS * (theta - shear);
        float arm = 0.5 + 0.5 * cos(phase);
        arm *= 1.0 + NUM_ARMS * 0.1 * sin(phase);
    #endif
    float brightness = smoothstep(0.0, 0.4, arm) * smoothstep(1.0, 0.6, arm);
    col = getColor(theta / TAU + t * 0.05, COLOR_SCHEME) * brightness;
    col *= exp(-r * r * 0.5);
    col += 0.15 * exp(-r * r * 8.0);

    #elif MODE == 2
    // --- Kaleidoscope mode ---
    vec2 kp = kaleidoscope(polar, KALEID_SEGMENTS);
    vec2 rect = toRect(kp);
    rect *= 4.0;
    rect += vec2(t * 0.3, 0.0);
    vec2 cell_id = floor(rect + 0.5);
    vec2 cell_uv = fract(rect + 0.5) - 0.5;
    float cell_hash = fract(sin(dot(cell_id, vec2(127.1, 311.7))) * 43758.5453);
    float d = length(cell_uv);
    float truchet = abs(d - 0.35);
    if (cell_hash > 0.5) {
        truchet = min(truchet, abs(length(cell_uv - 0.5) - 0.5));
    } else {
        truchet = min(truchet, abs(length(cell_uv + 0.5) - 0.5));
    }
    col = getColor(cell_hash + r * 0.2, COLOR_SCHEME);
    col *= smoothstep(0.05, 0.0, truchet - 0.03);
    col *= smoothstep(3.0, 0.0, r);

    #elif MODE == 3
    // --- Rose curve mode ---
    float rose_r = 0.6 * cos(PETAL_COUNT * theta + t);
    float dist = abs(r - abs(rose_r));
    float ribbon_width = 0.04;
    float rose_shape = smoothstep(ribbon_width + aa, ribbon_width - aa, dist);
    float depth = 0.5 + 0.5 * cos(PETAL_COUNT * theta + t);
    col = getColor(theta / TAU, COLOR_SCHEME) * depth;
    col *= rose_shape;
    float center = smoothstep(0.08 + aa, 0.08 - aa, r);
    col += getColor(0.5, COLOR_SCHEME) * center * 0.5;
    #endif

    col = pow(col, vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：动态涡旋背景（Balatro 风格）
笛卡尔→极坐标→笛卡尔往返+迭代域扭曲```glsl
float new_angle = atan(uv.y, uv.x) + speed
    - SPIN_EASE * 20.0 * (SPIN_AMOUNT * uv_len + (1.0 - SPIN_AMOUNT));
vec2 mid = (screenSize.xy / length(screenSize.xy)) / 2.0;
uv = vec2(uv_len * cos(new_angle) + mid.x,
           uv_len * sin(new_angle) + mid.y) - mid;
uv *= 30.0;
for (int i = 0; i < 5; i++) {
    uv2 += sin(max(uv.x, uv.y)) + uv;
    uv  += 0.5 * vec2(cos(5.1123 + 0.353*uv2.y + speed*0.131),
                       sin(uv2.x - 0.113*speed));
    uv  -= cos(uv.x + uv.y) - sin(uv.x*0.711 - uv.y);
}
```### 变体 2：极环扭转（环扭转式）
极空间直接渲染，角度切片模拟 3D 环面```glsl
vec2 uvr = vec2(length(uv), atan(uv.y, uv.x) + PI);
uvr.x -= OUT_RADIUS;
float twist = uvr.y + 2.0*iTime + sin(uvr.y)*sin(iTime)*PI;
for (int i = 0; i < NUM_FACES; i++) {
    float x0 = IN_RADIUS * sin(twist + TAU * float(i) / float(NUM_FACES));
    float x1 = IN_RADIUS * sin(twist + TAU * float(i+1) / float(NUM_FACES));
    vec4 face = slice(x0, x1, uvr);
    col = mix(col, face.rgb, face.a);
}
```### 变体 3：银河/对数螺旋（银河风格）
`log(r)`等角螺旋+FBM噪声+螺旋臂压缩```glsl
float rho = length(uv);
float ang = atan(uv.y, uv.x);
float shear = 2.0 * log(rho);
mat2 R = mat2(cos(shear), -sin(shear), sin(shear), cos(shear));
float phase = NB_ARMS * (ang - shear);
ang = ang - COMPR * cos(phase) + SPEED * t;
uv = rho * vec2(cos(ang), sin(ang));
float gaz = fbm_noise(0.09 * R * uv);
```### 变体 4：阿基米德螺旋带（波浪希腊饰带风格）
极地展开成螺旋带，在带内创建涡旋动画```glsl
vec2 U = vec2(atan(U.y, U.x)/TAU + 0.5, length(U));
U.y -= U.x;                                    // Archimedean unwrap
U.x = arc_length(ceil(U.y) + U.x) - iTime;     // Arc length parameterization
vec2 cell_uv = fract(U) - 0.5;
float vortex = dot(cell_uv,
    cos(vec2(-33.0, 0.0)
        + 0.3 * (iTime + cell_id.x)
        * max(0.0, 0.5 - length(cell_uv))));
```### 变体 5：复杂/极性二元性（宝石漩涡风格）
复杂算术取代了共形映射的显式三角函数```glsl
float e = n * 2.0;
float a = atan(u.y, u.x) - PI/2.0;
float r = exp(log(length(u)) / e);      // r^(1/e)
float sc = ceil(r - a/TAU);
float s = pow(sc + a/TAU, 2.0);
col += sin(cr + s/n * TAU / 2.0);
col *= cos(cr + s/n * TAU);
col *= pow(abs(sin((r - a/TAU) * PI)), abs(e) + 5.0);
```## 表演与作曲

### 性能提示
- **杆安全**：`float r = max(length(uv), 1e-6);`以避免被零除
- **三角优化**：当同时需要sin/cos时，使用旋转矩阵 `mat2 ROT(float a) { float c=cos(a),s=sin(a);返回 mat2(c,s,-s,c); }`
- **万花筒自然优化**：所有昂贵的计算都发生在单个扇区中，视觉复杂度×N
- **循环控制**：玫瑰曲线和其他多循环效果适用于 4-8 个循环；不要太高
- **像素下采样**：`floor(fragCoord / Pixel_size) * Pixel_size` 量化坐标以减少计算

### 构图技巧
- **Polar + FBM**：变换空间中的样本噪声 → 有机螺旋纹理
- **Polar + Truchet**：万花筒折叠后铺设 Truchet 瓷砖 → 几何隧道效果
- **Polar + SDF**：`r(θ)` 定义轮廓 + SDF 布尔运算/发光
- **极坐标 + 棋盘格**：`sign(sin(u*PI*4.0)*cos(uvr.y*16.0))` → 圆形棋盘格
- **极光 + 后处理**：伽玛 + 晕影 + 对比度增强，以提高视觉质量

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/polar-uv-manipulation.md)