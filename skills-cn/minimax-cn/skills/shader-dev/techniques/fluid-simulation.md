**重要：从 HTML 脚本标签中提取着色器时的常见错误**：从 `<script type="x-shader/x-fragment">` 提取源代码时，必须确保 `#version` 是字符串的 **第一个字符**，没有前导空格或换行符：```javascript
// WRONG: indentation/newline inside script tag
// <script id="fs">
//     #version 300 es  <-- leading newline here!
// </script>
const source = document.getElementById('fs').textContent; // contains leading whitespace

// CORRECT: use .trim() or place template string flush with the start
const source = document.getElementById('fs').textContent.trim();
// Or in HTML, place content directly after the tag:
// <script id="fs">#version 300 es
// ...
```### 重要提示：浮动纹理兼容性（流体模拟最关键的问题）

流体模拟需要浮动纹理来存储速度（可以为负）、压力和墨水浓度（可以超过 1.0）。

**重要：必须使用 RGBA16F 而不是 RGBA32F**：许多环境（无头 Chrome、SwiftShader、移动设备）不支持 `RGBA32F` 渲染目标。即使“EXT_color_buffer_float”扩展声称可用，“RGBA32F”FBO 也可能会默默地失败（帧缓冲区报告已完成，但呈现全零或全一）。 `RGBA16F + HALF_FLOAT` 的兼容性远远好于 `RGBA32F`，其精度对于流体模拟来说绰绰有余。```javascript
const gl = canvas.getContext("webgl2");
if (!gl) { /* error handling */ }

const ext = gl.getExtension("EXT_color_buffer_float");
// IMPORTANT: Continue even if ext is null — some environments support RGBA16F without this extension

function createFloatTexture(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // IMPORTANT: Must use RGBA16F + HALF_FLOAT, do NOT use RGBA32F + FLOAT
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return tex;
}

function createFBO(w, h) {
    const tex = createFloatTexture(w, h);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (status !== gl.FRAMEBUFFER_COMPLETE) {
        console.error("FBO incomplete:", status);
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { fbo, tex };
}
```### 鼠标交互实现

流体模拟需要跟踪鼠标位置和拖动方向。 iMouse 统一约定：**xy=当前鼠标位置，z=鼠标按下标志（>0 表示按下），w=未使用**。鼠标速度根据当前帧和前一帧之间的位置差计算：```javascript
// IMPORTANT: iMouse convention: xy=current position, z=pressed flag (1.0=down, 0.0=up), w=0
// Mouse velocity is computed via prevMouse on the JS side, passed through a separate uniform
let iMouse = [0, 0, 0, 0]; // [x, y, pressed, 0]
let prevMouse = [0, 0];
let mouseDown = false;

canvas.addEventListener('mousemove', (e) => {
    const dpr = Math.min(window.devicePixelRatio, 1.5);
    const x = e.clientX * dpr;
    const y = canvas.height - e.clientY * dpr; // WebGL Y-axis is flipped
    if (mouseDown) {
        prevMouse[0] = iMouse[0];
        prevMouse[1] = iMouse[1];
        iMouse[0] = x;
        iMouse[1] = y;
    }
});

canvas.addEventListener('mousedown', (e) => {
    mouseDown = true;
    const dpr = Math.min(window.devicePixelRatio, 1.5);
    const x = e.clientX * dpr;
    const y = canvas.height - e.clientY * dpr;
    iMouse[0] = x; iMouse[1] = y;
    iMouse[2] = 1.0; // Flag: mouse pressed
    prevMouse[0] = x; prevMouse[1] = y;
});

canvas.addEventListener('mouseup', () => {
    mouseDown = false;
    iMouse[2] = 0.0; // Flag: mouse released
});

// Pass uniforms in render loop
// iMouse: xy=position, z=pressed flag, w=0
gl.uniform4f(uMouse, iMouse[0], iMouse[1], iMouse[2], 0.0);
// IMPORTANT: Mouse velocity must be clamped, otherwise fast dragging produces huge velocity deltas causing NaN explosion
const mvx = Math.max(-50, Math.min(50, iMouse[0] - prevMouse[0]));
const mvy = Math.max(-50, Math.min(50, iMouse[1] - prevMouse[1]));
gl.uniform2f(uMouseVel, mvx, mvy);
```### 处理 WebGL 2 不可用```javascript
const gl = canvas.getContext("webgl2");
if (!gl) {
    document.body.innerHTML = `
        <div style="color:#fff;padding:20px;font-family:sans-serif;">
            <h2>WebGL 2 Not Supported</h2>
            <p>Fluid simulation requires WebGL 2. Please use a modern browser (Chrome 56+, Firefox 51+, Safari 15+).</p>
        </div>
    `;
    throw new Error('WebGL2 not supported');
}
```# 实时流体模拟

## 用例
- ShaderToy/WebGL 中的实时 2D 流体效果（烟雾、液体、墨水扩散）
- 交互式流体：鼠标/触摸驱动的流体响应
- **水中墨水扩散/卷曲涡旋效应**：涡旋限制+高扩散系数+单色或多色墨水
- **多色墨水混合**：多种墨水颜色相互渗透混合（需要Buffer B存储RGB墨水，参见多色墨水混合模板）
- 装饰流体背景、粒子系统、涡流可视化
- **熔岩/火/岩浆效果**：流体模拟+FBM噪声纹理+温度颜色映射
- **水面波纹效果**：波动方程+点击产生的同心波纹+干涉和阻尼
- 核心：在 GPU 片段着色器中求解简化的纳维-斯托克斯方程或波动方程

## 核心原则

不可压缩纳维-斯托克斯方程离散化：```
Momentum equation: ∂v/∂t = -(v·∇)v - ∇p + ν∇²v + f
Continuity equation: ∇·v = 0
```术语含义：`-(v·∇)v`平流、`-∇p`压力梯度、`ν∇²v`粘性扩散、`f`外力。
零发散 = 不可压缩性约束，通过压力泊松方程投影速度场来实现。

**ShaderToy实现策略**：纹理缓冲区帧间反馈，每一帧执行：平流→扩散→外力→压力投影。每个像素存储网格点物理量（速度、压力、密度）。

###水面波纹原理（波动方程）

水面波纹使用 2D 波动方程而不是纳维-斯托克斯方程：```
∂²h/∂t² = c² * ∇²h - damping * ∂h/∂t
```使用 Verlet 积分进行离散化：“下一个 = 速度 * (2*curr - 上一个 + 拉普拉斯算子) * 阻尼”。

数据编码：`.r = 前一帧高度 (prev)`，`.g = 当前帧高度 (curr)`。每帧计算拉普拉斯算子以推进波前，乒乓缓冲区交替读/写。

## 实施步骤

### 步骤 1：数据编码和邻域采样```glsl
// Data layout: .xy=velocity, .z=pressure/density, .w=ink
#define T(p) texture(iChannel0, (p) / iResolution.xy)

vec4 c = T(p);                    // center
vec4 n = T(p + vec2(0, 1));       // north
vec4 e = T(p + vec2(1, 0));       // east
vec4 s = T(p - vec2(0, 1));       // south
vec4 w = T(p - vec2(1, 0));       // west
```### 步骤 2：离散微分算子```glsl
// Laplacian (weighted 3x3 stencil)
const float _K0 = -20.0 / 6.0;
const float _K1 =   4.0 / 6.0;
const float _K2 =   1.0 / 6.0;
vec4 laplacian = _K0 * c
    + _K1 * (n + e + s + w)
    + _K2 * (T(p+vec2(1,1)) + T(p+vec2(-1,1)) + T(p+vec2(1,-1)) + T(p+vec2(-1,-1)));

// Gradient (central difference)
vec4 dx = (e - w) / 2.0;
vec4 dy = (n - s) / 2.0;

// Divergence & Curl
float div = dx.x + dy.y;
float curl = dx.y - dy.x;
```### 步骤 3：半拉格朗日平流```glsl
#define DT 0.15  // time step
// Backward trace: sample from upstream, unconditionally stable
vec4 advected = T(p - DT * c.xy);
c.xyw = advected.xyw;
```### 步骤 4：粘性扩散```glsl
#define NU 0.5     // kinematic viscosity (0.01=water, 1.0=syrup)
#define KAPPA 0.1  // ink diffusion coefficient

c.xy += DT * NU * laplacian.xy;
c.w  += DT * KAPPA * laplacian.w;
```### 步骤 5：压力投射```glsl
#define K 0.2  // pressure correction strength
c.xy -= K * vec2(dx.z, dy.z);
c.z -= DT * (dx.z * c.x + dy.z * c.y + div * c.z);
```### 第 6 步：鼠标交互```glsl
// IMPORTANT: iMouse.z is the mouse-down flag (>0=pressed), not a position coordinate
// iMouseVel is mouse movement velocity, passed via a separate uniform
// IMPORTANT: Must clamp mouseVel to prevent NaN explosion
if (iMouse.z > 0.0) {
    vec2 mouseVel = clamp(iMouseVel, vec2(-50.0), vec2(50.0));
    float dist2 = dot(p - iMouse.xy, p - iMouse.xy);
    float influence = exp(-dist2 / 50.0);  // 50.0=influence radius
    c.xy += DT * influence * mouseVel;
    c.w  += DT * influence * 0.5;
}
```### 步骤 6b：涡度限制（墨水卷曲效果所需）```glsl
// IMPORTANT: Ink diffusion/swirl effects require vorticity confinement, otherwise small vortices dissipate quickly leaving only smooth flow
// Vorticity confinement re-injects energy into small-scale vortices, producing characteristic curling textures
#define VORT_STR 0.035  // [0.01=subtle, 0.05=noticeable, 0.1=strong]
float curl_c = dx.y - dy.x;
float curl_n = (T(p + vec2(1,1)).y - T(p + vec2(-1,1)).y) / 2.0
             - (T(p + vec2(0,2)).x - T(p).x) / 2.0;
float curl_s = (T(p + vec2(1,-1)).y - T(p + vec2(-1,-1)).y) / 2.0
             - (T(p).x - T(p + vec2(0,-2)).x) / 2.0;
float curl_e = (T(p + vec2(2,0)).y - T(p).y) / 2.0
             - (T(p + vec2(1,1)).x - T(p + vec2(1,-1)).x) / 2.0;
float curl_w = (T(p).y - T(p + vec2(-2,0)).y) / 2.0
             - (T(p + vec2(-1,1)).x - T(p + vec2(-1,-1)).x) / 2.0;
vec2 eta = normalize(vec2(abs(curl_e)-abs(curl_w), abs(curl_n)-abs(curl_s)) + vec2(1e-5));
c.xy += DT * VORT_STR * vec2(eta.y, -eta.x) * curl_c;
```### 步骤 7：自动墨水源（关键：确保可见输出而无需交互）```glsl
// IMPORTANT: Must have automatic ink sources! Otherwise the screen is completely black without mouse interaction
// IMPORTANT: Ink injection and decay must be balanced! Too-strong injection or too-weak decay causes ink saturation across the entire screen → solid color with no features
// IMPORTANT: Gaussian denominator controls emitter radius — larger denominator means larger emitter!
//     Denominator > 300 makes emitter cover most of the screen, ink saturates quickly
//     Recommended 100~200, keeping it locally concentrated with visible gradient falloff at distance
float t = iTime;

// Emitter positions should move over time for dynamic effects
vec2 em1 = iResolution.xy * vec2(0.25, 0.5 + 0.2 * sin(t * 0.7));
vec2 em2 = iResolution.xy * vec2(0.75, 0.5 + 0.2 * cos(t * 0.9));
vec2 em3 = iResolution.xy * vec2(0.5, 0.3 + 0.15 * sin(t * 1.3));

// Gaussian influence radius controls locality (smaller denominator = more concentrated, 100~200 is reasonable)
float r1 = exp(-dot(p - em1, p - em1) / 150.0);
float r2 = exp(-dot(p - em2, p - em2) / 150.0);
float r3 = exp(-dot(p - em3, p - em3) / 120.0);

// Inject velocity (rotating, crossing directions make fluid motion more interesting)
c.xy += DT * r1 * vec2(cos(t), sin(t * 1.3)) * 3.0;
c.xy += DT * r2 * vec2(-cos(t * 0.8), sin(t * 0.6)) * 3.0;
c.xy += DT * r3 * vec2(sin(t * 1.1), -cos(t)) * 2.0;

// Inject ink (note: injection amount must balance with INK_DECAY, otherwise screen saturates)
c.w += DT * (r1 + r2 + r3) * 2.0;
```### 步骤 8：边界与稳定性```glsl
// No-slip boundary
if (p.x < 1.0 || p.y < 1.0 ||
    iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
    c.xyw *= 0.0;
}

// IMPORTANT: Ink decay — must use multiplicative decay (e.g., *= 0.99), NOT subtractive decay (-= constant)
// Subtractive decay zeros out quickly at small ink values and decays too slowly at large values, causing saturation
// Multiplicative decay scales proportionally, maintaining contrast at any concentration
c.w *= 0.99;  // 1% decay per frame, adjustable [0.98=fast dissipation, 0.995=persistent]

c = clamp(c, vec4(-5, -5, 0.5, 0), vec4(5, 5, 3, 5));
```### 步骤 9：可视化（图像传递）— 一般流体```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);

    // IMPORTANT: Color base must be bright enough! 0.5+0.5*cos produces [0,1] range bright colors
    // Never use vec3(0.02, 0.01, 0.08) or similar near-zero base colors — they become invisible when multiplied by ink
    float angle = atan(c.y, c.x);
    vec3 col = 0.5 + 0.5 * cos(angle + vec3(0.0, 2.1, 4.2));

    // IMPORTANT: Use smoothstep to map ink concentration; upper limit should exceed actual ink range to preserve gradients
    float ink = smoothstep(0.0, 2.0, c.w);
    col *= ink;

    // Pressure highlights
    col += vec3(0.05) * clamp(c.z - 1.0, 0.0, 1.0);

    // IMPORTANT: Background color must be visible (RGB at least > 5/255 ≈ 0.02), otherwise users think the page is all black
    col = max(col, vec3(0.02, 0.012, 0.035));

    fragColor = vec4(col, 1.0);
}
```### 步骤 9b：可视化（图像传递）——熔岩/火焰/岩浆效果

熔岩/火需要 FBM 噪声来实现湍流纹理 + 温度色带映射。 **关键：必须使用 FBM 噪声来扭曲 UV 坐标和温度值，否则图像太平滑，看起来像普通渐变而不是熔岩。**```glsl
// IMPORTANT: FBM noise is the core of lava/fire visualization! Without it the image is a smooth gradient with no lava texture
// These noise functions must be defined in the Image Pass

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f); // smoothstep hermite
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// IMPORTANT: octaves=4~6 produces sufficient detail; fewer than 3 gives too-coarse textures
float fbm(vec2 p, int octaves) {
    float val = 0.0;
    float amp = 0.5;
    for (int i = 0; i < octaves; i++) {
        val += amp * noise(p);
        p *= 2.0;
        amp *= 0.5;
    }
    return val;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);
    float t = iTime;

    // Use fluid velocity field to distort noise sampling coordinates so noise moves with the fluid
    vec2 distortedUV = uv + c.xy * 0.002;
    // FBM noise: multi-octave superposition produces turbulent detail
    float n1 = fbm(distortedUV * 8.0 + t * 0.3, 5);
    float n2 = fbm(distortedUV * 4.0 - t * 0.2 + 5.0, 4);

    float ink = smoothstep(0.0, 2.0, c.w);
    float speed = length(c.xy);

    // Temperature = ink concentration + noise perturbation + speed contribution
    // IMPORTANT: Noise perturbation amplitude of 0.2~0.4 produces visible texture without becoming noisy
    float temp = ink * 0.7 + n1 * 0.25 + speed * 0.1;
    // Second noise layer for cracks/dark veins
    temp -= (1.0 - n2) * 0.15 * ink;
    temp = clamp(temp, 0.0, 1.0);

    // Lava temperature color band: black → dark red → orange → yellow → white-hot
    vec3 col;
    if (temp < 0.15) {
        col = mix(vec3(0.05, 0.0, 0.0), vec3(0.5, 0.05, 0.0), temp / 0.15);
    } else if (temp < 0.4) {
        col = mix(vec3(0.5, 0.05, 0.0), vec3(1.0, 0.35, 0.0), (temp - 0.15) / 0.25);
    } else if (temp < 0.7) {
        col = mix(vec3(1.0, 0.35, 0.0), vec3(1.0, 0.75, 0.1), (temp - 0.4) / 0.3);
    } else {
        col = mix(vec3(1.0, 0.75, 0.1), vec3(1.0, 0.95, 0.7), clamp((temp - 0.7) / 0.3, 0.0, 1.0));
    }

    // Glow effect: additional additive glow in high-temperature regions
    float glow = smoothstep(0.5, 1.0, temp) * 0.4;
    col += vec3(1.0, 0.5, 0.1) * glow;

    // HDR tone mapping
    col = 1.0 - exp(-col * 1.5);

    col = max(col, vec3(0.03, 0.005, 0.0));
    fragColor = vec4(col, 1.0);
}
```### 步骤 9c：可视化（图像传递）- 水面波纹效果

水波纹图像通道根据高度场计算法线，然后应用照明+环境反射。 **重点：法线扰动强度必须足够大（50~100），水基色必须明亮（蓝色分量> 0.15），镜面高光必须突出。**```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 texel = 1.0 / iResolution.xy;

    // IMPORTANT: Sample from wave height field: .g channel stores current frame height
    float h = texture(iChannel0, uv).g;
    float hn = texture(iChannel0, uv + vec2(0.0, texel.y)).g;
    float hs = texture(iChannel0, uv - vec2(0.0, texel.y)).g;
    float he = texture(iChannel0, uv + vec2(texel.x, 0.0)).g;
    float hw = texture(iChannel0, uv - vec2(texel.x, 0.0)).g;

    // IMPORTANT: Normal perturbation factor must be large enough (50~100), otherwise ripples are invisible
    // If drop strength is 1.0 and radius is 8~15px, using 80.0 produces clearly visible ripples
    vec3 normal = normalize(vec3((hw - he) * 80.0, (hs - hn) * 80.0, 1.0));

    vec3 lightDir = normalize(vec3(0.3, 0.5, 1.0));
    vec3 viewDir = vec3(0.0, 0.0, 1.0);
    vec3 halfVec = normalize(lightDir + viewDir);

    float diffuse = max(dot(normal, lightDir), 0.0);
    float specular = pow(max(dot(normal, halfVec), 0.0), 64.0);

    // IMPORTANT: Water base color must be bright enough! Deep color no darker than vec3(0.02, 0.08, 0.2), shallow color use vec3(0.1, 0.3, 0.6)
    vec3 deepColor = vec3(0.02, 0.08, 0.22);
    vec3 shallowColor = vec3(0.1, 0.35, 0.65);
    vec3 waterColor = mix(deepColor, shallowColor, 0.5 + h * 5.0);

    float fresnel = pow(1.0 - max(dot(normal, viewDir), 0.0), 3.0);

    vec3 col = waterColor * (0.4 + 0.6 * diffuse);
    col += vec3(0.9, 0.95, 1.0) * specular * 2.0;
    col += vec3(0.15, 0.25, 0.45) * fresnel * 0.6;

    // Caustic effect
    float caustic = pow(max(diffuse, 0.0), 8.0) * abs(h) * 5.0;
    col += vec3(0.15, 0.35, 0.55) * caustic;

    col = max(col, vec3(0.02, 0.06, 0.15));
    col = pow(col, vec3(0.95));

    fragColor = vec4(col, 1.0);
}
```## 重要提示：常见的致命错误

1. **RGBA32F 在无头/SwiftShader 环境中默默失败**：必须使用 `RGBA16F + HALF_FLOAT`
2. **墨水浸透整个屏幕**：高斯分母太大 (>300) 或衰减太弱 (>0.995)。修复：分母100~200，衰减 `*= 0.99`
3. **Image Pass 颜色太暗导致全黑屏幕**：使用 `0.5 + 0.5 * cos(...)` 色基以确保明亮范围
4. **未夹紧的鼠标速度导致 NaN 崩溃**：快速拖动或第一帧点击会产生巨大的速度增量 → 速度爆炸 → NaN 传播到整个屏幕。 **JS 端和着色器端都必须将 mouseVel 钳位到 [-50, 50]**
5. **对多色墨水使用单一标量可防止混合**：单个`c.w`只能做单色。多色墨水需要Buffer B存储RGB三个通道（参见多色墨水混合模板）
6. **GLSL严格输入**：`vec2 = float`是非法的，必须使用`vec2(float)`；整数和浮点数不能混合

## 完整的代码模板

设置：缓冲区 A 的 iChannel0 指向缓冲区 A 本身（反馈循环）。

### 独立 HTML JS 骨架（乒乓渲染管道）

流体模拟需要帧缓冲自反馈+浮动纹理。以下 JS 框架演示了正确的 WebGL2 多通道乒乓结构：```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fluid Simulation</title>
<style>
/* IMPORTANT: Critical: canvas must fill the viewport, otherwise it may be invisible or clipped */
*{margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden;background:#000}
canvas{display:block;width:100%;height:100%}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
let frameCount = 0;
// IMPORTANT: iMouse convention: [x, y, pressedFlag, 0] — z is the pressed flag (1 or 0), not a coordinate
let mouse = [0, 0, 0, 0];
let prevMouse = [0, 0];
let mouseDown = false;

const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');
if (!gl) {
    document.body.innerHTML = '<div style="color:#fff;padding:20px;font-family:sans-serif;"><h2>WebGL 2 not supported</h2></div>';
    throw new Error('WebGL2 not supported');
}
const ext = gl.getExtension('EXT_color_buffer_float');

function createShader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
        console.error(gl.getShaderInfoLog(s));
    return s;
}
function createProgram(vsSrc, fsSrc) {
    const p = gl.createProgram();
    gl.attachShader(p, createShader(gl.VERTEX_SHADER, vsSrc));
    gl.attachShader(p, createShader(gl.FRAGMENT_SHADER, fsSrc));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS))
        console.error(gl.getProgramInfoLog(p));
    return p;
}

const vsSource = `#version 300 es
in vec2 pos;
void main(){ gl_Position=vec4(pos,0,1); }`;

// fsBuffer / fsImage: adapt from the Buffer A / Image templates below
// IMPORTANT: Fragment shaders must declare these uniforms:
//   uniform sampler2D iChannel0;
//   uniform vec2 iResolution;
//   uniform float iTime;
//   uniform int iFrame;
//   uniform vec4 iMouse;    // xy=position, z=pressed flag, w=0
//   uniform vec2 iMouseVel; // mouse movement velocity (only needed in Buffer pass)

const progBuf = createProgram(vsSource, fsBuffer);
const progImg = createProgram(vsSource, fsImage);

// IMPORTANT: Must use RGBA16F + HALF_FLOAT, do NOT use RGBA32F + FLOAT
// RGBA32F may render all zeros in headless Chrome / SwiftShader even when framebuffer reports complete
function createFBO(w, h) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { fbo, tex };
}

let W, H, bufA, bufB;

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
gl.enableVertexAttribArray(0);
gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

function resize() {
    const dpr = Math.min(window.devicePixelRatio, 1.5);
    canvas.width = W = Math.floor(innerWidth * dpr);
    canvas.height = H = Math.floor(innerHeight * dpr);
    bufA = createFBO(W, H);
    bufB = createFBO(W, H);
    frameCount = 0;
}
addEventListener('resize', resize);
resize();

canvas.addEventListener('mousemove', e => {
    const dpr = Math.min(devicePixelRatio, 1.5);
    const x = e.clientX * dpr;
    const y = H - e.clientY * dpr;
    if (mouseDown) {
        prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
        mouse[0] = x; mouse[1] = y;
    }
});
canvas.addEventListener('mousedown', e => {
    mouseDown = true;
    const dpr = Math.min(devicePixelRatio, 1.5);
    mouse[0] = e.clientX * dpr;
    mouse[1] = H - e.clientY * dpr;
    mouse[2] = 1.0; // IMPORTANT: Pressed flag, not a coordinate
    prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
});
canvas.addEventListener('mouseup', () => {
    mouseDown = false;
    mouse[2] = 0.0; // IMPORTANT: Released flag
});

// Touch events (mobile)
canvas.addEventListener('touchstart', e => {
    e.preventDefault(); mouseDown = true;
    const t = e.touches[0], dpr = Math.min(devicePixelRatio, 1.5);
    mouse[0] = t.clientX * dpr; mouse[1] = H - t.clientY * dpr;
    mouse[2] = 1.0;
    prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
}, {passive:false});
canvas.addEventListener('touchmove', e => {
    e.preventDefault();
    const t = e.touches[0], dpr = Math.min(devicePixelRatio, 1.5);
    if (mouseDown) {
        prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];
        mouse[0] = t.clientX * dpr; mouse[1] = H - t.clientY * dpr;
    }
}, {passive:false});
canvas.addEventListener('touchend', () => { mouseDown = false; mouse[2] = 0.0; });

// Cache uniform locations (avoid per-frame lookups)
const uBuf = {
    ch0: gl.getUniformLocation(progBuf, 'iChannel0'),
    res: gl.getUniformLocation(progBuf, 'iResolution'),
    time: gl.getUniformLocation(progBuf, 'iTime'),
    frame: gl.getUniformLocation(progBuf, 'iFrame'),
    mouse: gl.getUniformLocation(progBuf, 'iMouse'),
    mouseVel: gl.getUniformLocation(progBuf, 'iMouseVel')
};
const uImg = {
    ch0: gl.getUniformLocation(progImg, 'iChannel0'),
    res: gl.getUniformLocation(progImg, 'iResolution'),
    time: gl.getUniformLocation(progImg, 'iTime')
};

function render(t) {
    t *= 0.001;

    // Buffer pass: read bufA → write bufB
    gl.useProgram(progBuf);
    gl.bindFramebuffer(gl.FRAMEBUFFER, bufB.fbo);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);
    gl.uniform1i(uBuf.ch0, 0);
    gl.uniform2f(uBuf.res, W, H);
    gl.uniform1f(uBuf.time, t);
    gl.uniform1i(uBuf.frame, frameCount);
    gl.uniform4f(uBuf.mouse, mouse[0], mouse[1], mouse[2], 0.0);
    // IMPORTANT: Must clamp mouse velocity! Fast movement or first-frame clicks can produce huge velocity values,
    // causing shader velocity explosion → NaN propagation → page crash
    const mvx = Math.max(-50, Math.min(50, mouse[0] - prevMouse[0]));
    const mvy = Math.max(-50, Math.min(50, mouse[1] - prevMouse[1]));
    gl.uniform2f(uBuf.mouseVel, mvx, mvy);
    gl.bindVertexArray(vao);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    [bufA, bufB] = [bufB, bufA];

    // Reset prevMouse each frame to avoid velocity accumulation
    prevMouse[0] = mouse[0]; prevMouse[1] = mouse[1];

    // Image pass: read bufA → screen
    gl.useProgram(progImg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);
    gl.uniform1i(uImg.ch0, 0);
    gl.uniform2f(uImg.res, W, H);
    gl.uniform1f(uImg.time, t);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    frameCount++;
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
```**缓冲区 A（流体计算）**：```glsl
// Grid-Based Euler Fluid Solver — Buffer A
// Data layout: .xy=velocity, .z=pressure/density, .w=ink
// iChannel0 = Buffer A (self-feedback)

#define DT 0.15          // time step [0.05 - 0.3]
#define K 0.2            // pressure correction strength [0.1 - 0.4]
#define NU 0.5           // viscosity coefficient [0.01=water, 1.0=syrup]
#define KAPPA 0.1        // ink diffusion coefficient [0.0 - 0.5]
#define MOUSE_RAD 50.0   // mouse influence radius [10.0 - 200.0]

#define T(p) texture(iChannel0, (p) / iResolution.xy)

void mainImage(out vec4 fragColor, in vec2 p) {
    // Initial frames: add slight noise to break symmetry lock
    if (iFrame < 10) {
        vec2 uv = p / iResolution.xy;
        float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
        fragColor = vec4(noise * 1e-4, noise * 1e-4, 1.0, 0.0);
        return;
    }

    vec4 c = T(p);

    vec4 n = T(p + vec2(0, 1));
    vec4 e = T(p + vec2(1, 0));
    vec4 s = T(p - vec2(0, 1));
    vec4 w = T(p - vec2(1, 0));

    vec4 laplacian = (n + e + s + w - 4.0 * c);
    vec4 dx = (e - w) / 2.0;
    vec4 dy = (n - s) / 2.0;
    float div = dx.x + dy.y;

    c.z -= DT * (dx.z * c.x + dy.z * c.y + div * c.z);
    c.xyw = T(p - DT * c.xy).xyw;
    c.xyw += DT * vec3(NU, NU, KAPPA) * laplacian.xyw;
    c.xy -= K * vec2(dx.z, dy.z);

    // Mouse interaction: iMouse.z is the pressed flag (>0), velocity obtained via iMouseVel uniform
    // IMPORTANT: mouseVel must be clamped to prevent NaN explosion (JS side should also clamp — double safety)
    if (iMouse.z > 0.0) {
        vec2 mouseVel = clamp(iMouseVel, vec2(-50.0), vec2(50.0));
        float dist2 = dot(p - iMouse.xy, p - iMouse.xy);
        float influence = exp(-dist2 / MOUSE_RAD);
        c.xy += DT * influence * mouseVel;
        c.w  += DT * influence * 0.5;
    }

    // Vorticity confinement: prevents small vortices from dissipating too quickly, producing curling textures
    // IMPORTANT: Ink diffusion/swirl effects (e.g., ink diffusing in water) require vorticity confinement, otherwise curl dissipates quickly leaving only smooth flow
    float curl_c = dx.y - dy.x;
    float curl_n = (T(p + vec2(1,1)).y - T(p + vec2(-1,1)).y) / 2.0
                 - (T(p + vec2(0,2)).x - T(p).x) / 2.0;
    float curl_s = (T(p + vec2(1,-1)).y - T(p + vec2(-1,-1)).y) / 2.0
                 - (T(p).x - T(p + vec2(0,-2)).x) / 2.0;
    float curl_e = (T(p + vec2(2,0)).y - T(p).y) / 2.0
                 - (T(p + vec2(1,1)).x - T(p + vec2(1,-1)).x) / 2.0;
    float curl_w = (T(p).y - T(p + vec2(-2,0)).y) / 2.0
                 - (T(p + vec2(-1,1)).x - T(p + vec2(-1,-1)).x) / 2.0;
    vec2 eta = vec2(abs(curl_e) - abs(curl_w), abs(curl_n) - abs(curl_s));
    eta = normalize(eta + vec2(1e-5));
    c.xy += DT * 0.035 * vec2(eta.y, -eta.x) * curl_c;

    // IMPORTANT: Automatic ink sources: ensure visible fluid motion without mouse interaction
    // Emitter positions must move over time, and Gaussian radius must be small enough to maintain locality
    float t = iTime;
    vec2 em1 = iResolution.xy * vec2(0.25, 0.5 + 0.2 * sin(t * 0.7));
    vec2 em2 = iResolution.xy * vec2(0.75, 0.5 + 0.2 * cos(t * 0.9));
    vec2 em3 = iResolution.xy * vec2(0.5, 0.3 + 0.15 * sin(t * 1.3));

    float r1 = exp(-dot(p - em1, p - em1) / 150.0);
    float r2 = exp(-dot(p - em2, p - em2) / 150.0);
    float r3 = exp(-dot(p - em3, p - em3) / 120.0);

    c.xy += DT * r1 * vec2(cos(t), sin(t * 1.3)) * 3.0;
    c.xy += DT * r2 * vec2(-cos(t * 0.8), sin(t * 0.6)) * 3.0;
    c.xy += DT * r3 * vec2(sin(t * 1.1), -cos(t)) * 2.0;
    c.w += DT * (r1 + r2 + r3) * 2.0;

    // IMPORTANT: Ink decay: must use multiplicative decay, do NOT use subtractive (subtractive causes saturation)
    c.w *= 0.99;

    c = clamp(c, vec4(-5, -5, 0.5, 0), vec4(5, 5, 3, 5));

    if (p.x < 1.0 || p.y < 1.0 ||
        iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
        c.xyw *= 0.0;
    }

    fragColor = c;
}
```**图像（可视化渲染）**：```glsl
// Fluid Visualization — Image Pass
// iChannel0 = Buffer A

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);

    // IMPORTANT: Color base must be bright enough! 0.5+0.5*cos produces [0,1] range bright colors
    // Never use vec3(0.02, 0.01, 0.08) or similar extremely dark base colors — they become invisible when multiplied by ink
    float angle = atan(c.y, c.x);
    vec3 col = 0.5 + 0.5 * cos(angle + vec3(0.0, 2.1, 4.2));

    // IMPORTANT: smoothstep upper limit should cover actual ink range to preserve gradient variation
    float ink = smoothstep(0.0, 2.0, c.w);
    col *= ink;

    // Pressure highlights
    col += vec3(0.05) * clamp(c.z - 1.0, 0.0, 1.0);

    // IMPORTANT: Background color must be visible (RGB at least > 5/255 ≈ 0.02), otherwise users think the page is all black
    col = max(col, vec3(0.02, 0.012, 0.035));

    fragColor = vec4(col, 1.0);
}
```## 水面波纹完整模板

水面波纹使用波动方程而不是纳维-斯托克斯方程。点击/触摸会产生同心波纹，这些波纹相互干扰并逐渐衰减。

**重要提示：水波纹滴注入必须使用 iMouse 在着色器中直接实现，不要使用自定义统一数组来传递单击位置 - 这会增加 JS/GLSL 双方的复杂性并且容易出错（未找到统一位置、数组长度不匹配等）。

### 水波纹缓冲通道（波动方程求解器）```glsl
// Water Ripple — Buffer Pass (Wave Equation Solver)
// Data encoding: .r = previous frame height (prev), .g = current frame height (curr)
// iChannel0 = self-feedback (ping-pong)
// IMPORTANT: Drop injection is done directly in the shader via iMouse, no custom uniforms needed

void main() {
    vec2 p = gl_FragCoord.xy;
    vec2 uv = p / iResolution.xy;

    if (iFrame < 2) {
        fragColor = vec4(0.0);
        return;
    }

    float prev = texture(iChannel0, uv).r;
    float curr = texture(iChannel0, uv).g;

    vec2 texel = 1.0 / iResolution.xy;
    float n = texture(iChannel0, uv + vec2(0.0, texel.y)).g;
    float s = texture(iChannel0, uv - vec2(0.0, texel.y)).g;
    float e = texture(iChannel0, uv + vec2(texel.x, 0.0)).g;
    float w = texture(iChannel0, uv - vec2(texel.x, 0.0)).g;

    float laplacian = n + s + e + w - 4.0 * curr;

    // Verlet integration: next = 2*curr - prev + c²*laplacian
    float speed = 0.45;
    float next = 2.0 * curr - prev + speed * laplacian;

    // damping: 0.995~0.998 lets ripples propagate several rings before disappearing
    float damping = 0.996;
    next *= damping;

    // IMPORTANT: Mouse click drop injection — directly using iMouse, simple and reliable
    // iMouse.z > 0 indicates mouse is pressed
    if (iMouse.z > 0.0) {
        float dist = length(p - iMouse.xy);
        float radius = 12.0;
        float strength = 1.5;
        next += strength * exp(-dist * dist / (2.0 * radius * radius));
    }

    // IMPORTANT: Automatic ripples: ensure visible ripples even without interaction
    // Use periodic functions of iTime to control auto-drop position and timing
    float autoPhase = iTime * 0.5;
    float autoPeriod = fract(autoPhase);
    // Only inject during phase < 0.05 each cycle (avoid continuous injection)
    if (autoPeriod < 0.05) {
        float idx = floor(autoPhase);
        // Pseudo-random position
        vec2 autoPos = iResolution.xy * vec2(
            0.2 + 0.6 * fract(sin(idx * 12.9898) * 43758.5453),
            0.2 + 0.6 * fract(sin(idx * 78.233) * 43758.5453)
        );
        float dist = length(p - autoPos);
        next += 1.2 * exp(-dist * dist / (2.0 * 10.0 * 10.0));
    }

    // Boundary absorption
    if (p.x < 2.0 || p.y < 2.0 ||
        iResolution.x - p.x < 2.0 || iResolution.y - p.y < 2.0) {
        next *= 0.0;
    }

    // IMPORTANT: Output: .r = current frame (becomes next frame's prev), .g = newly computed (becomes next frame's curr)
    fragColor = vec4(curr, next, 0.0, 1.0);
}
```### 水波纹JS端

水波纹 JS 结构与流体模拟骨架（乒乓 FBO + 渲染循环）相同，只有以下区别：
- 缓冲区通道着色器是波动方程求解器（上面的模板）
- 图像通道是水面光照渲染器（步骤9c）
- **不需要自定义统一数组**，滴注入完全通过 iMouse 在着色器中完成
- JS端只需要传递标准制服：`iChannel0，iResolution，iTime，iFrame，iMouse`

拖动鼠标时，会连续注入波纹（因为 iMouse.z > 0 保持不变），并且拖动速度越快会产生更密集的波纹（自然效果）。

### 水波纹图像通行证

请参阅上面的步骤 9c。

## 多色墨水混合模板（墨水在水中扩散/多色混合）

当多种墨水颜色需要相互渗透和混合时，单个标量“c.w”是不够的。您需要**两个缓冲区**：缓冲区A存储速度/压力（同上），缓冲区B存储RGB三通道墨水浓度，共享相同的平流速度场。

**重要提示：多色墨水的关键：缓冲区 B 的 RGB 通道独立存储每种墨水颜色的浓度，使用缓冲区 A 的速度场进行半拉格朗日平流。不同的墨水颜色在平流和扩散过程中自然混合。**

### JS 侧面变化（三缓冲乒乓）

需要两组乒乓 FBO：“bufA/bufB”（速度场）和“bufC/bufD”（墨水 RGB）。在渲染循环中，首先渲染Buffer A（速度场），然后渲染Buffer B（墨水平流），最后Image pass读取Buffer B进行可视化：```javascript
// Create additional ink FBO pair
let bufC, bufD;
function resize() {
    // ... same as above for bufA/bufB ...
    bufC = createFBO(W, H);
    bufD = createFBO(W, H);
}

// Buffer B shader needs two input textures:
// iChannel0 = Buffer B self (ink RGB)
// iChannel1 = Buffer A (velocity field)
const uBufInk = {
    ch0: gl.getUniformLocation(progBufInk, 'iChannel0'),
    ch1: gl.getUniformLocation(progBufInk, 'iChannel1'),
    res: gl.getUniformLocation(progBufInk, 'iResolution'),
    time: gl.getUniformLocation(progBufInk, 'iTime'),
    frame: gl.getUniformLocation(progBufInk, 'iFrame'),
    mouse: gl.getUniformLocation(progBufInk, 'iMouse'),
};

function render(t) {
    t *= 0.001;
    // Pass 1: Buffer A (velocity) — read bufA, write bufB
    // ... same as above ...
    [bufA, bufB] = [bufB, bufA];

    // Pass 2: Buffer B (ink RGB) — read bufC(ink)+bufA(velocity), write bufD
    gl.useProgram(progBufInk);
    gl.bindFramebuffer(gl.FRAMEBUFFER, bufD.fbo);
    gl.viewport(0, 0, W, H);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufC.tex);  // previous frame ink
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, bufA.tex);  // current velocity field
    gl.uniform1i(uBufInk.ch0, 0);
    gl.uniform1i(uBufInk.ch1, 1);
    gl.uniform2f(uBufInk.res, W, H);
    gl.uniform1f(uBufInk.time, t);
    gl.uniform1i(uBufInk.frame, frameCount);
    gl.uniform4f(uBufInk.mouse, mouse[0], mouse[1], mouse[2], 0.0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    [bufC, bufD] = [bufD, bufC];

    // Pass 3: Image — read bufC(ink) to screen
    gl.useProgram(progImg);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, bufC.tex);
    // ...
}
```### 缓冲区 B — 多色墨水平流着色器```glsl
// Multi-Color Ink — Buffer B (Ink Advection)
// .rgb = concentrations of three ink colors
// iChannel0 = Buffer B self (ink RGB)
// iChannel1 = Buffer A (velocity field, .xy=velocity)

#define DT 0.15
#define INK_KAPPA 0.3        // ink diffusion coefficient (higher than single-color template for faster blending)
#define INK_DECAY 0.995      // ink decay (slower than single-color to maintain richness)

#define TINK(p) texture(iChannel0, (p) / iResolution.xy)
#define TVEL(p) texture(iChannel1, (p) / iResolution.xy)

void mainImage(out vec4 fragColor, in vec2 p) {
    if (iFrame < 10) { fragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }

    vec2 vel = TVEL(p).xy;

    // Semi-Lagrangian advection: backward trace using velocity field
    vec3 ink = TINK(p - DT * vel).rgb;

    // Diffusion: Laplacian operator
    vec3 inkC = TINK(p).rgb;
    vec3 inkN = TINK(p + vec2(0,1)).rgb;
    vec3 inkE = TINK(p + vec2(1,0)).rgb;
    vec3 inkS = TINK(p - vec2(0,1)).rgb;
    vec3 inkW = TINK(p - vec2(1,0)).rgb;
    vec3 lapInk = inkN + inkE + inkS + inkW - 4.0 * inkC;
    ink += DT * INK_KAPPA * lapInk;

    // Automatic ink sources: multiple emitters with different colors
    float t = iTime;
    vec2 em1 = iResolution.xy * vec2(0.25, 0.5 + 0.2 * sin(t * 0.7));
    vec2 em2 = iResolution.xy * vec2(0.75, 0.5 + 0.2 * cos(t * 0.9));
    vec2 em3 = iResolution.xy * vec2(0.5, 0.3 + 0.15 * sin(t * 1.3));
    vec2 em4 = iResolution.xy * vec2(0.5, 0.7 + 0.15 * cos(t * 0.5));

    float r1 = exp(-dot(p - em1, p - em1) / 200.0);
    float r2 = exp(-dot(p - em2, p - em2) / 200.0);
    float r3 = exp(-dot(p - em3, p - em3) / 180.0);
    float r4 = exp(-dot(p - em4, p - em4) / 180.0);

    // Each emitter injects a different color
    ink.r += DT * (r1 * 3.0 + r4 * 1.5);          // red/magenta
    ink.g += DT * (r2 * 3.0 + r3 * 1.5);          // green/cyan
    ink.b += DT * (r3 * 3.0 + r1 * 0.8 + r2 * 0.8); // blue/mixed

    // Mouse stirring injects white ink (all channels)
    if (iMouse.z > 0.0) {
        float dist2 = dot(p - iMouse.xy, p - iMouse.xy);
        float influence = exp(-dist2 / 80.0);
        ink += vec3(DT * influence * 2.0);
    }

    // Decay + clamp
    ink *= INK_DECAY;
    ink = clamp(ink, vec3(0.0), vec3(5.0));

    // Boundary clear
    if (p.x < 1.0 || p.y < 1.0 ||
        iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
        ink = vec3(0.0);
    }

    fragColor = vec4(ink, 1.0);
}
```### 步骤 9d：可视化（图像传递）— 多色墨水混合```glsl
// Multi-Color Ink Visualization — Image Pass
// iChannel0 = Buffer B (ink RGB)

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec3 ink = texture(iChannel0, uv).rgb;

    // Use smoothstep to map each channel, preserving concentration gradients
    vec3 mapped = smoothstep(vec3(0.0), vec3(2.5), ink);

    // Color mapping: map RGB concentrations to actual visible colors
    // IMPORTANT: Base colors must be bright, do not use extremely dark values
    vec3 col1 = vec3(0.9, 0.15, 0.2);  // red ink
    vec3 col2 = vec3(0.1, 0.8, 0.3);   // green ink
    vec3 col3 = vec3(0.15, 0.3, 0.95); // blue ink

    vec3 col = col1 * mapped.r + col2 * mapped.g + col3 * mapped.b;

    // Mixing regions produce new hues (additive blending naturally creates gradients)
    // HDR tone mapping to prevent overexposure
    col = 1.0 - exp(-col * 1.2);

    // Background color
    float totalInk = mapped.r + mapped.g + mapped.b;
    vec3 bg = vec3(0.02, 0.015, 0.04);
    col = mix(bg, col, smoothstep(0.0, 0.3, totalInk));

    fragColor = vec4(col, 1.0);
}
```**重要提示：多色墨水缓冲区 A 速度场模板与单色版本相同**，除了“c.w”不再用于墨水（墨水位于缓冲区 B 中）。缓冲器 A 仅处理速度 + 压力。

## 常见变体

### 变体 1：旋转自平流
不使用压力投射；通过多尺度旋转采样实现自然的无发散平流。```glsl
#define RotNum 3
#define angRnd 1.0

const float ang = 2.0 * 3.14159 / float(RotNum);
mat2 m = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));

float getRot(vec2 uv, float sc) {
    float ang2 = angRnd * randS(uv).x * ang;
    vec2 p = vec2(cos(ang2), sin(ang2));
    float rot = 0.0;
    for (int i = 0; i < RotNum; i++) {
        vec2 p2 = p * sc;
        vec2 v = texture(iChannel0, fract(uv + p2)).xy - vec2(0.5);
        rot += cross(vec3(v, 0.0), vec3(p2, 0.0)).z / dot(p2, p2);
        p = m * p;
    }
    return rot / float(RotNum);
}

// Multi-scale advection superposition
vec2 v = vec2(0);
float sc = 1.0 / max(iResolution.x, iResolution.y);
for (int level = 0; level < 20; level++) {
    if (sc > 0.7) break;
    vec2 p = vec2(cos(ang2), sin(ang2));
    for (int i = 0; i < RotNum; i++) {
        vec2 p2 = p * sc;
        float rot = getRot(uv + p2, sc);
        v += p2.yx * rot * vec2(-1, 1);
        p = m * p;
    }
    sc *= 2.0;
}
fragColor = texture(iChannel0, fract(uv + v * 3.0 / iResolution.x));
```### 变体 2：涡度限制
在基本解算器顶部添加涡旋限制力，防止小涡旋消散过快。```glsl
#define VORT_STRENGTH 0.01  // [0.001 - 0.1]

float curl_c = curl_at(uv);
float curl_n = abs(curl_at(uv + vec2(0, texel.y)));
float curl_s = abs(curl_at(uv - vec2(0, texel.y)));
float curl_e = abs(curl_at(uv + vec2(texel.x, 0)));
float curl_w = abs(curl_at(uv - vec2(texel.x, 0)));

vec2 eta = normalize(vec2(curl_e - curl_w, curl_n - curl_s) + 1e-5);
vec2 conf = VORT_STRENGTH * vec2(eta.y, -eta.x) * curl_c;
c.xy += DT * conf;
```### 变体 3：粘性指法
旋转驱动的自放大+拉普拉斯扩散，产生反应扩散式的有机图案。```glsl
const float cs = 0.25;   // curl→rotation scale
const float ls = 0.24;   // Laplacian diffusion strength
const float ps = -0.06;  // divergence-pressure feedback
const float amp = 1.0;   // self-amplification coefficient
const float pwr = 0.2;   // curl power exponent

float sc = cs * sign(curl) * pow(abs(curl), pwr);
float ta = amp * uv.x + ls * lapl.x + norm.x * sp + uv.x * sd;
float tb = amp * uv.y + ls * lapl.y + norm.y * sp + uv.y * sd;
float a = ta * cos(sc) - tb * sin(sc);
float b = ta * sin(sc) + tb * cos(sc);
fragColor = clamp(vec4(a, b, div, 1), -1.0, 1.0);
```### 变体 4：高斯核 SPH 粒子流体（高斯 SPH）
用于密度和速度估计的高斯核函数，基于网格的 SPH 近似。```glsl
#define RADIUS 7  // search radius [3-10]

vec4 r = vec4(0);
for (vec2 i = vec2(-RADIUS); ++i.x < float(RADIUS);)
    for (i.y = -float(RADIUS); ++i.y < float(RADIUS);) {
        vec2 v = texelFetch(iChannel0, ivec2(i + fragCoord), 0).xy;
        float mass = texelFetch(iChannel0, ivec2(i + fragCoord), 0).z;
        float w = exp(-dot(v + i, v + i)) / 3.14;
        r += mass * w * vec4(mix(v + v + i, v, mass), 1, 1);
    }
r.xy /= r.z + 1e-6;
```### 变体 5：拉格朗日涡旋粒子法
跟踪离散涡旋粒子，使用毕奥-萨伐尔定律计算速度场。```glsl
#define N 20              // N×N particles
#define STRENGTH 1e3*0.25 // vorticity strength scale

vec2 F = vec2(0);
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++) {
        float w = vorticity(i, j);
        vec2 d = particle_pos(i, j) - my_pos;
        float l = dot(d, d);
        if (l > 1e-5)
            F += vec2(-d.y, d.x) * w / l;
    }
velocity = STRENGTH * F;
position += velocity * dt;
```## 表演与作曲

**性能提示**：
- 5点十字模板速度最快； 3x3（9 个样本）是最佳精度/性能权衡
- SPH搜索半径>7时速度极慢；使用 `texelFetch` 而不是 `texture` 来跳过过滤
- 将多个步骤合并为一个通道；帧间反馈形成隐式雅可比迭代
- 多步平流 (`ADVECTION_STEPS=3`) 提高了准确性，但采样成本增加了 3 倍
- `textureLod` 提供 O(1) 多尺度读取，取代大半径采样
- 在初始帧上添加轻微的噪音（`1e-6`）以打破对称锁定
- `fract(uv + offset)` 实现没有分支的周期性边界
- 将压力场乘以“0.9999”衰减以防止漂移

**组成方向**：
- **+法线贴图照明**：密度场→高度图→法线→Phong/GGX，液态金属效果
- **+粒子追踪**：被动粒子跟随流场更新位置，可视化流线/墨水清洗
- **+ 颜色平流**：额外通道存储 RGB、同步半拉格朗日平流、彩色混合
- **+ 音频响应**：低频 → 推力，高频 → 涡扰动，音乐驱动流体
- **+ 3D 体积渲染**：2D 切片打包为 3D 体素，光线行进渲染云/爆炸

## 进一步阅读

[参考](../reference/fluid-simulation.md) 中有完整的分步教程、数学推导和高级用法