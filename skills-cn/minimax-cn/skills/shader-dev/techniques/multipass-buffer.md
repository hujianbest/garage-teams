### 独立 HTML 完整着色器模板（必须严格遵循）

**重要：以下模板可以直接复制；每一行都必须严格遵守**：

**顶点着色器**（所有着色器通用）：```glsl
#version 300 es
in vec4 iPosition;
void main() {
    gl_Position = iPosition;
}
```**片段着色器缓冲区示例**（粒子物理模拟）：```glsl
#version 300 es
precision highp float;

// IMPORTANT: Critical: uniforms must be declared; ShaderToy's iTime/iResolution etc. are global variables
uniform float iTime;
uniform vec2 iResolution;
uniform int iFrame;
uniform vec4 iMouse;

// IMPORTANT: Critical: mainImage parameters need manual extraction
// ShaderToy: void mainImage(out vec4 fragColor, in vec2 fragCoord)
// Adapted to:
out vec4 fragColor;
void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = fragCoord / iResolution;

    // IMPORTANT: Critical: texture2D → texture
    vec4 prev = texture(iChannel0, uv);

    // ... particle physics logic ...

    fragColor = vec4(pos, vel);
}
```**片段着色器图像示例**：```glsl
#version 300 es
precision highp float;

uniform float iTime;
uniform vec2 iResolution;
uniform int iFrame;
uniform vec4 iMouse;
uniform sampler2D iChannel0;

out vec4 fragColor;

void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = fragCoord / iResolution;

    // IMPORTANT: Critical: texture2D → texture, mainImage → standard main
    vec4 col = texture(iChannel0, uv);

    // Rendering logic
    col = col / (1.0 + col);  // Tone mapping

    fragColor = col;
}
```**重要：常见 GLSL ES 3.00 错误**（必须避免）：
1. **#version 必须位于第一行** - 任何注释/空行都会导致“version 指令必须出现在第一行”错误
2. **in/out 限定符** - WebGL1 的 attribute/variing 必须在 ES3 中更改为 in/out
3. **纹理函数** - ES3使用`texture(sampler, uv)`，而不是`texture2D(sampler, uv)`
4. **类型严格性** - `vec4 = float` 是非法的，必须使用 `vec4(v, v, v, v)` 或 `vec4(v)` 或 `vec4(vec3(v), 1.0)`

## 独立 HTML 多通道帧缓冲区实现

**重要：多通道渲染管道核心陷阱**：ShaderToy 代码需要手动实现 Framebuffer 渲染管道。以下模板演示了正确的方法：```javascript
// Correct multi-channel Framebuffer creation
const NUM_BUFFERS = 2;  // Buffer A, Buffer B
const buffers = [];
const textures = [];

// Check float texture linear filtering extension
const ext = gl.getExtension('EXT_color_buffer_float');
const floatLinear = gl.getExtension('OES_texture_float_linear');

// Each Buffer needs an independent Framebuffer + texture
for (let i = 0; i < NUM_BUFFERS; i++) {
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);

    // IMPORTANT: Critical: Must use UNSIGNED_BYTE format without EXT_color_buffer_float extension!
    // RGBA16F/RGBA32F require the extension, otherwise GL_INVALID_OPERATION
    // Float textures need EXT_color_buffer_float; RGBA16F supports HDR data
    if (ext) {
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, width, height, 0, gl.RGBA, gl.FLOAT, null);
    } else {
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    }

    // IMPORTANT: Critical: Texture parameters must be set, otherwise GL_INVALID_FRAMEBUFFER
    // IMPORTANT: Float textures use NEAREST, or require OES_texture_float_linear extension for LINEAR
    // IMPORTANT: Critical: Float textures must use CLAMP_TO_EDGE wrap mode; REPEAT is not supported for float textures
    // IMPORTANT: Critical: Must fall back to UNSIGNED_BYTE format without EXT_color_buffer_float extension
    const filterMode = (ext && floatLinear) ? gl.LINEAR : gl.NEAREST;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filterMode);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filterMode);
    // IMPORTANT: Must use CLAMP_TO_EDGE: float textures do not support REPEAT
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);

    // IMPORTANT: Critical: Check Framebuffer completeness
    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    if (status !== gl.FRAMEBUFFER_COMPLETE) {
        console.error("Framebuffer incomplete:", status);
    }

    textures.push(texture);
    buffers.push(fbo);
}
gl.bindFramebuffer(gl.FRAMEBUFFER, null);

// Render loop: render to Buffer first, then render to screen
function render() {
    // 1. Render to Buffer A (self-feedback reads previous Buffer)
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[0]);
    gl.viewport(0, 0, width, height);
    // Bind previous frame texture to iChannel0
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);  // Read from other Buffer
    // Set uniforms etc...
    // Execute shader rendering

    // 2. Swap Buffers (simulate self-feedback)
    // IMPORTANT: Critical: Must swap textures for next frame reading; FBO handles remain unchanged
    [textures[0], textures[1]] = [textures[1], textures[0]];

    // 3. Render to screen
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    // Bind Buffer result to texture
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[0]);
    // Execute Image pass shader
}
```**重要：常见错误**（JavaScript/WebGL 方面）：
1. **缺少纹理参数** - 必须设置`TEXTURE_MIN_FILTER`、`TEXTURE_MAG_FILTER`、`TEXTURE_WRAP_S/T`
2. **缺少帧缓冲区完整性检查** - `gl.checkFramebufferStatus()` 在使用前必须返回 `FRAMEBUFFER_COMPLETE`
3. **浮动纹理扩展** - `gl.RGBA16F` 需要 `EXT_color_buffer_float` 扩展，否则回退到 `gl.UNSIGNED_BYTE`
4. **Buffer ping-pong error** - 自反馈必须使用2个独立的FBO交替读/写；单个 FBO + 纹理交换导致“反馈循环”错误
5. **粒子系统空纹理初始化** - 第一帧之前纹理为空；着色器读取默认值导致渲染失败 - 必须执行 initPass() 才能预渲染

# 多通道缓冲技术

## 用例

当单帧计算无法达到预期效果，需要跨帧数据持久化或者多级处理流水线时，可以使用多通道缓冲区：

- **时间累积**：运动模糊、TAA、渐进式渲染
- **物理模拟**：流体、反应扩散、粒子系统
- **持久状态**：游戏状态、粒子位置/速度、交互历史
- **延迟渲染**：G-Buffer → 后处理 → 合成
- **后处理链**：HDR Bloom（下采样 → 模糊 → 合成）
- **迭代求解器**：泊松求解器、涡度限制、多尺度计算

## 核心原则

多通道缓冲区将渲染管道分成多个缓冲区，每个缓冲区输出一个纹理作为下一阶段的输入。

### 自我反馈
Buffer 读取自己的前一帧输出，实现跨帧状态持久化：`x(n+1) = f(x(n))````
Buffer A (frame N) reads → Buffer A (frame N-1) output
```### 管道链
多个Buffer依次处理：```
Buffer A (geometry) → Buffer B (blur H) → Buffer C (blur V) → Image (compositing)
```### 结构化数据存储
特定像素作为数据寄存器，通过“texelFetch”精确读取：```
texel (0,0) = ball position+velocity (vec4)
texel (1,0) = paddle position
texel (x,1)-(x,12) = brick grid state
```### 关键数学模式

- **流体自平流**：`newPos = 纹理(buf, uv - dt * 速度 * texelSize)`
- **高斯模糊**：`sum += 纹理(buf, uv + offset_i) * Weight_i`
- **时间混合**：`结果 = mix(newFrame, prevFrame, BlendWeight)`
- **涡度限制**：`vortForce = 旋度 × 归一化（梯度（|旋度|））`

## 实施步骤

### 步骤 1：最小自反馈环路

缓冲区A（iChannel0→缓冲区A自反馈）：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    vec4 prev = texture(iChannel0, uv);

    // New content: procedural noise contour lines
    float n = noise(vec3(uv * 8.0, 0.1 * iTime));
    float v = sin(6.2832 * 10.0 * n);
    v = smoothstep(1.0, 0.0, 0.5 * abs(v) / fwidth(v));
    vec4 newContent = 0.5 + 0.5 * sin(12.0 * n + vec4(0, 2.1, -2.1, 0));

    // Decay + offset blending
    vec4 decayed = exp(-33.0 / iResolution.y) * texture(iChannel0, (fragCoord + vec2(1.0, sin(iTime))) / iResolution.xy);
    fragColor = mix(decayed, newContent, v);

    // Initialization guard
    if (iFrame < 4) fragColor = vec4(0.5);
}
```图像（iChannel0 → 缓冲区 A）：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    fragColor = texture(iChannel0, fragCoord / iResolution.xy);
}
```### 步骤 2：流体自平流

缓冲区A（iChannel0→缓冲区A自反馈）：```glsl
#define ROT_NUM 5
#define SCALE_NUM 20

const float ang = 6.2832 / float(ROT_NUM);
mat2 m = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));

float getRot(vec2 pos, vec2 b) {
    vec2 p = b;
    float rot = 0.0;
    for (int i = 0; i < ROT_NUM; i++) {
        rot += dot(texture(iChannel0, fract((pos + p) / iResolution.xy)).xy - vec2(0.5),
                   p.yx * vec2(1, -1));
        p = m * p;
    }
    return rot / float(ROT_NUM) / dot(b, b);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 pos = fragCoord;
    float rnd = fract(sin(float(iFrame) * 12.9898) * 43758.5453);
    vec2 b = vec2(cos(ang * rnd), sin(ang * rnd));

    // Multi-scale rotation sampling
    vec2 v = vec2(0);
    float bbMax = 0.7 * iResolution.y;
    bbMax *= bbMax;
    for (int l = 0; l < SCALE_NUM; l++) {
        if (dot(b, b) > bbMax) break;
        vec2 p = b;
        for (int i = 0; i < ROT_NUM; i++) {
            v += p.yx * getRot(pos + p, b);
            p = m * p;
        }
        b *= 2.0;
    }

    // Self-advection
    fragColor = texture(iChannel0, fract((pos + v * vec2(-1, 1) * 2.0) / iResolution.xy));

    // Center driving force
    vec2 scr = (fragCoord / iResolution.xy) * 2.0 - 1.0;
    fragColor.xy += 0.01 * scr / (dot(scr, scr) / 0.1 + 0.3);

    if (iFrame <= 4) fragColor = texture(iChannel1, fragCoord / iResolution.xy);
}
```### 步骤 3-4：纳维-斯托克斯求解器 + 链式加速

缓冲区 A / B / C 使用相同的代码（通过 Common 选项卡的 `solveFluid`）：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;

    vec4 lastMouse = texelFetch(iChannel0, ivec2(0, 0), 0);
    vec4 data = solveFluid(iChannel0, uv, w, iTime, iMouse.xyz, lastMouse.xyz);

    if (iFrame < 20) data = vec4(0.5, 0, 0, 0);
    if (fragCoord.y < 1.0) data = iMouse;  // Mouse state storage

    fragColor = data;
}
```iChannel 绑定：A→C（上一帧）、B→A、C→B — 每帧 3 次迭代。

### 步骤 5：可分离高斯模糊

缓冲区 B（水平，iChannel0 → 源缓冲区）— 缓冲区 C 垂直方向类似，使用 y 轴偏移：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 pixelSize = 1.0 / iResolution.xy;
    vec2 uv = fragCoord * pixelSize;
    float h = pixelSize.x;
    vec4 sum = vec4(0.0);
    // 9-tap Gaussian (sigma ≈ 2.0)
    sum += texture(iChannel0, fract(vec2(uv.x - 4.0*h, uv.y))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x - 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x - 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x - 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x,          uv.y))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x + 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x + 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x + 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x + 4.0*h, uv.y))) * 0.05;
    fragColor = vec4(sum.xyz / 0.98, 1.0);
}
```### 步骤 6：结构化状态存储```glsl
// Register address definitions
const ivec2 txBallPosVel = ivec2(0, 0);
const ivec2 txPaddlePos  = ivec2(1, 0);
const ivec2 txPoints     = ivec2(2, 0);
const ivec2 txState      = ivec2(3, 0);
const ivec4 txBricks     = ivec4(0, 1, 13, 12);

vec4 loadValue(ivec2 addr) {
    return texelFetch(iChannel0, addr, 0);
}

void storeValue(ivec2 addr, vec4 val, inout vec4 fragColor, ivec2 currentPixel) {
    fragColor = (currentPixel == addr) ? val : fragColor;
}

void storeValue(ivec4 rect, vec4 val, inout vec4 fragColor, ivec2 currentPixel) {
    fragColor = (currentPixel.x >= rect.x && currentPixel.y >= rect.y &&
                 currentPixel.x <= rect.z && currentPixel.y <= rect.w) ? val : fragColor;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 px = ivec2(fragCoord - 0.5);
    if (fragCoord.x > 14.0 || fragCoord.y > 14.0) discard;

    vec4 ballPosVel = loadValue(txBallPosVel);
    float paddlePos = loadValue(txPaddlePos).x;
    float points = loadValue(txPoints).x;

    if (iFrame == 0) {
        ballPosVel = vec4(0.0, -0.8, 0.6, 1.0);
        paddlePos = 0.0;
        points = 0.0;
    }

    // ... game logic update ...

    fragColor = loadValue(px);
    storeValue(txBallPosVel, ballPosVel, fragColor, px);
    storeValue(txPaddlePos, vec4(paddlePos, 0, 0, 0), fragColor, px);
    storeValue(txPoints, vec4(points, 0, 0, 0), fragColor, px);
}
```### 步骤 7：鼠标状态帧间跟踪```glsl
// Method 1: First-row pixel storage
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;
    vec4 lastMouse = texelFetch(iChannel0, ivec2(0, 0), 0);
    // ... simulation logic ...
    if (fragCoord.y < 1.0) fragColor = iMouse;
}

// Method 2: Fixed UV region storage
vec2 mouseDelta() {
    vec2 pixelSize = 1.0 / iResolution.xy;
    float eighth = 1.0 / 8.0;
    vec4 oldMouse = texture(iChannel2, vec2(7.5 * eighth, 2.5 * eighth));
    vec4 nowMouse = vec4(iMouse.xy / iResolution.xy, iMouse.zw / iResolution.xy);
    if (oldMouse.z > pixelSize.x && oldMouse.w > pixelSize.y &&
        nowMouse.z > pixelSize.x && nowMouse.w > pixelSize.y) {
        return nowMouse.xy - oldMouse.xy;
    }
    return vec2(0.0);
}
```## 完整的代码模板

完全可运行的流体模拟着色器（自反馈+涡度限制+鼠标交互+颜色平流）。

### 常用选项卡```glsl
#define DT 0.15
#define VORTICITY_AMOUNT 0.11
#define VISCOSITY 0.55
#define PRESSURE_K 0.2
#define FORCE_RADIUS 0.001
#define FORCE_STRENGTH 0.001
#define VELOCITY_DECAY 1e-4

float mag2(vec2 p) { return dot(p, p); }

vec2 emitter1(float t) { t *= 0.62; return vec2(0.12, 0.5 + sin(t) * 0.2); }
vec2 emitter2(float t) { t *= 0.62; return vec2(0.88, 0.5 + cos(t + 1.5708) * 0.2); }

vec4 solveFluid(sampler2D smp, vec2 uv, vec2 w, float time, vec3 mouse, vec3 lastMouse) {
    vec4 data = textureLod(smp, uv, 0.0);
    vec4 tr = textureLod(smp, uv + vec2(w.x, 0), 0.0);
    vec4 tl = textureLod(smp, uv - vec2(w.x, 0), 0.0);
    vec4 tu = textureLod(smp, uv + vec2(0, w.y), 0.0);
    vec4 td = textureLod(smp, uv - vec2(0, w.y), 0.0);

    vec3 dx = (tr.xyz - tl.xyz) * 0.5;
    vec3 dy = (tu.xyz - td.xyz) * 0.5;
    vec2 densDif = vec2(dx.z, dy.z);

    data.z -= DT * dot(vec3(densDif, dx.x + dy.y), data.xyz);

    vec2 laplacian = tu.xy + td.xy + tr.xy + tl.xy - 4.0 * data.xy;
    vec2 viscForce = vec2(VISCOSITY) * laplacian;

    data.xyw = textureLod(smp, uv - DT * data.xy * w, 0.0).xyw;

    vec2 newForce = vec2(0);
    newForce += 0.75 * vec2(0.0003, 0.00015) / (mag2(uv - emitter1(time)) + 0.0001);
    newForce -= 0.75 * vec2(0.0003, 0.00015) / (mag2(uv - emitter2(time)) + 0.0001);

    if (mouse.z > 1.0 && lastMouse.z > 1.0) {
        vec2 vv = clamp((mouse.xy * w - lastMouse.xy * w) * 400.0, -6.0, 6.0);
        newForce += FORCE_STRENGTH / (mag2(uv - mouse.xy * w) + FORCE_RADIUS) * vv;
    }

    data.xy += DT * (viscForce - PRESSURE_K / DT * densDif + newForce);
    data.xy = max(vec2(0), abs(data.xy) - VELOCITY_DECAY) * sign(data.xy);

    data.w = (tr.y - tl.y - tu.x + td.x);
    vec2 vort = vec2(abs(tu.w) - abs(td.w), abs(tl.w) - abs(tr.w));
    vort *= VORTICITY_AMOUNT / length(vort + 1e-9) * data.w;
    data.xy += vort;

    data.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    data = clamp(data, vec4(vec2(-10), 0.5, -10.0), vec4(vec2(10), 3.0, 10.0));

    return data;
}
```### 缓冲液 A / B / C（流体子步骤 1/2/3）

iChannel 绑定：A←C（上一帧）、B←A、C←B```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;
    vec4 lastMouse = texelFetch(iChannel0, ivec2(0, 0), 0);
    vec4 data = solveFluid(iChannel0, uv, w, iTime, iMouse.xyz, lastMouse.xyz);
    if (iFrame < 20) data = vec4(0.5, 0, 0, 0);
    if (fragCoord.y < 1.0) data = iMouse;
    fragColor = data;
}
```### Buffer D（Color Advection，iChannel0 → Buffer C，iChannel1 → Buffer D 自反馈）```glsl
#define COLOR_DECAY 0.004
#define COLOR_ADVECT_SCALE 3.0

vec3 getPalette(float x, vec3 c1, vec3 c2, vec3 p1, vec3 p2) {
    float x2 = fract(x / 2.0);
    x = fract(x);
    mat3 m = mat3(c1, p1, c2);
    mat3 m2 = mat3(c2, p2, c1);
    float omx = 1.0 - x;
    vec3 pws = vec3(omx * omx, 2.0 * omx * x, x * x);
    return clamp(mix(m * pws, m2 * pws, step(x2, 0.5)), 0.0, 1.0);
}

vec4 palette1(float x) {
    return vec4(getPalette(-x, vec3(0.2, 0.5, 0.7), vec3(0.9, 0.4, 0.1),
                vec3(1.0, 1.2, 0.5), vec3(1.0, -0.4, 0.0)), 1.0);
}
vec4 palette2(float x) {
    return vec4(getPalette(-x, vec3(0.4, 0.3, 0.5), vec3(0.9, 0.75, 0.4),
                vec3(0.1, 0.8, 1.3), vec3(1.25, -0.1, 0.1)), 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;

    vec2 velo = textureLod(iChannel0, uv, 0.0).xy;
    vec4 col = textureLod(iChannel1, uv - DT * velo * w * COLOR_ADVECT_SCALE, 0.0);

    vec2 mo = iMouse.xy / iResolution.xy;
    vec4 lastMouse = texelFetch(iChannel1, ivec2(0, 0), 0);
    if (iMouse.z > 1.0 && lastMouse.z > 1.0) {
        float str = smoothstep(-0.5, 1.0, length(mo - lastMouse.xy / iResolution.xy));
        col += str * 0.0009 / (pow(length(uv - mo), 1.7) + 0.002) * palette2(-iTime * 0.7);
    }

    col += 0.0025 / (0.0005 + pow(length(uv - emitter1(iTime)), 1.75)) * DT * 0.12 * palette1(iTime * 0.05);
    col += 0.0025 / (0.0005 + pow(length(uv - emitter2(iTime)), 1.75)) * DT * 0.12 * palette2(iTime * 0.05 + 0.675);

    if (iFrame < 20) col = vec4(0.0);
    col = clamp(col, 0.0, 5.0);
    col = max(col - (0.0001 + col * COLOR_DECAY) * 0.5, 0.0);

    if (fragCoord.y < 1.0 && fragCoord.x < 1.0) col = iMouse;
    fragColor = col;
}
```### 图像（iChannel0 → 缓冲区 D）```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec4 col = textureLod(iChannel0, fragCoord / iResolution.xy, 0.0);
    if (fragCoord.y < 1.0 || fragCoord.y >= iResolution.y - 1.0) col = vec4(0);
    fragColor = col;
}
```## 常见变体

### 变体 1：TAA 时间累积抗锯齿```glsl
// Buffer A: Sub-pixel jittered rendering
vec2 jitter = vec2(rand(uv + sin(iTime)), rand(uv + 1.0 + sin(iTime))) / iResolution.xy;
vec3 eyevec = normalize(vec3(((uv + jitter) * 2.0 - 1.0) * vec2(aspect, 1.0), fov));
float blendWeight = 0.9;
color = mix(color, texture(iChannel_self, uv).rgb, blendWeight);

// Buffer C (TAA): YCoCg neighborhood clamping to prevent ghosting
vec3 newYCC = RGBToYCoCg(newFrame);
vec3 histYCC = RGBToYCoCg(history);
vec3 colorAvg = ...; vec3 colorVar = ...;
vec3 sigma = sqrt(max(vec3(0), colorVar - colorAvg * colorAvg));
histYCC = clamp(histYCC, colorAvg - 0.75 * sigma, colorAvg + 0.75 * sigma);
result = YCoCgToRGB(mix(newYCC, histYCC, 0.95));
```### 变体 2：延迟渲染 G 缓冲区```glsl
// Buffer A: G-Buffer output
col.xy = (normal * camMat * 0.5 + 0.5).xy;  // Normal
col.z = 1.0 - abs((t * rd) * camMat).z / DMAX;  // Depth
col.w = dot(lightDir, nor) * 0.5 + 0.5;  // Diffuse

// Buffer B: Edge detection
float checkSame(vec4 center, vec4 sample) {
    vec2 diffNormal = abs(center.xy - sample.xy) * Sensitivity.x;
    float diffDepth = abs(center.z - sample.z) * Sensitivity.y;
    return (diffNormal.x + diffNormal.y < 0.1 && diffDepth < 0.1) ? 1.0 : 0.0;
}
```### 变体 3：HDR Bloom```glsl
// Buffer B: MIP pyramid (multi-level downsampling packed into one texture)
vec2 CalcOffset(float octave) {
    vec2 offset = vec2(0);
    vec2 padding = vec2(10.0) / iResolution.xy;
    offset.x = -min(1.0, floor(octave / 3.0)) * (0.25 + padding.x);
    offset.y = -(1.0 - 1.0 / exp2(octave)) - padding.y * octave;
    offset.y += min(1.0, floor(octave / 3.0)) * 0.35;
    return offset;
}
// Image: Accumulate multi-level bloom + Reinhard tone mapping
bloom += Grab(coord, 1.0, CalcOffset(0.0)) * 1.0;
bloom += Grab(coord, 2.0, CalcOffset(1.0)) * 1.5;
color = pow(color, vec3(1.5));
color = color / (1.0 + color);
```### 变体 4：反应扩散系统```glsl
// Buffer A: Gray-Scott reaction-diffusion
vec2 uv_red = uv + vec2(dx.x, dy.x) * pixelSize * 8.0;
float new_val = texture(iChannel0, fract(uv_red)).x;
new_val += (noise.x - 0.5) * 0.0025 - 0.002;
new_val -= (texture(iChannel_blur, fract(uv_red)).x -
            texture(iChannel_self, fract(uv_red)).x) * 0.047;
```### 变体 5：多尺度 MIP 流体```glsl
for (int i = 0; i < NUM_SCALES; i++) {
    float mip = float(i);
    float stride = float(1 << i);
    vec4 t = stride * vec4(texel, -texel.y, 0);
    vec2 d = textureLod(sampler, fract(uv + t.ww), mip).xy;
    float w = WEIGHT_FUNCTION;
    result += w * computation(neighbors);
}
```### 变体 6：粒子系统（位置-速度存储）

**重要：粒子系统实现关键**：粒子状态存储在纹理像素中，每个像素一个粒子。渲染必须迭代粒子纹理以进行采样。

**缓冲区 A（粒子物理模拟）**：```glsl
// Each texture pixel stores one particle: xy=position, zw=velocity

// IMPORTANT: Critical: hash function must return vec2! Returning float causes type mismatch errors
vec2 hash2(vec2 p) {
    return fract(sin(mat2(127.1, 311.7, 269.5, 183.3) * p) * 43758.5453);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 prev = texture(iChannel0, uv);

    vec2 pos = prev.xy;
    vec2 vel = prev.zw;

    // IMPORTANT: Initialization guard: use integer comparison + pixel-coordinate-based random (avoids particle overlap when time is too small)
    if (iFrame < 3) {
        // Use fragCoord (pixel coordinates) to ensure each particle has a unique position, independent of time
        // IMPORTANT: Critical: hash2 returns vec2, assign directly to pos/vel
        pos = hash2(fragCoord * 0.01 + vec2(1.7, 9.3));
        vel = (hash2(fragCoord * 0.01 + vec2(5.3, 2.8)) - 0.5) * 0.02;
        fragColor = vec4(pos, vel);
        return;
    }

    // Physics update
    vel *= 0.98;  // Damping

    // Mouse interaction
    vec2 mouse = iMouse.xy / iResolution.xy;
    if (iMouse.z > 0.0) {
        vec2 toMouse = mouse - pos;
        vel += normalize(toMouse + 0.001) * 0.0005 / (length(toMouse) + 0.1);
    }

    // Motion
    pos += vel * 60.0 * 0.016;
    pos = fract(pos);  // Boundary wrapping

    fragColor = vec4(pos, vel);
}
```**图像（渲染粒子）**：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;

    vec3 color = vec3(0.02, 0.02, 0.05);  // Dark background

    // Iterate over particle texture for sampling (performance-sensitive, balance sample count)
    float glow = 0.0;
    for (float y = 0.0; y < 1.0; y += 0.02) {  // IMPORTANT: Step size determines sampling density
        for (float x = 0.0; x < 1.0; x += 0.02) {
            vec4 particle = texture(iChannel0, vec2(x, y));
            vec2 pPos = particle.xy;
            float dist = length(uv - pPos);
            float size = 0.01 + length(particle.zw) * 0.3;
            glow += exp(-dist * dist / (size * size)) * 0.15;
        }
    }

    // Particle glow
    color += vec3(0.3, 0.6, 1.0) * glow;

    // Vignette
    color *= 1.0 - length(uv - 0.5) * 0.8;

    // Tone mapping
    color = color / (1.0 + color);

    fragColor = vec4(color, 1.0);
}
```**要点**：
- 缓冲区 A 自反馈：iChannel0 → 缓冲区 A
- 图像读取：iChannel0 → 缓冲区 A（粒子状态）
- 步长0.02产生2500个样本；根据表现进行调整
- 颗粒尺寸随速度变化：`尺寸 = 0.01 + 长度(vel) * 0.3`

**完整的 JavaScript 渲染管道（粒子系统 3 遍）**：```javascript
// Particle system needs 4 Framebuffers (2 each for Buffer A and Buffer B ping-pong) + screen output
// Buffer A: Particle physics (self-feedback) - uses FBO 0/1 ping-pong
// Buffer B: Density accumulation (reads Buffer A) - uses FBO 2/3 ping-pong
// Image: Final rendering (reads Buffer A + Buffer B)

// IMPORTANT: Critical: Must use 2 FBOs for ping-pong! Single FBO + texture swap causes
// "Feedback loop formed between Framebuffer and active Texture" error
const buffers = [null, null, null, null];  // [A_FBO0, A_FBO1, B_FBO0, B_FBO1]
const textures = [null, null, null, null];  // [A_tex0, A_tex1, B_tex0, B_tex1]

function createBuffers() {
    // Buffer A: 2 FBOs for ping-pong
    for (let i = 0; i < 2; i++) {
        const tex = createTexture();
        textures[i] = tex;

        const fbo = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
        buffers[i] = fbo;
    }
    // Buffer B: 2 FBOs for ping-pong
    for (let i = 0; i < 2; i++) {
        const tex = createTexture();
        textures[2 + i] = tex;

        const fbo = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
        buffers[2 + i] = fbo;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}

// IMPORTANT: Critical: Initialization pre-rendering - must execute before the first frame!
// Empty textures cause particle initialization failure (reading 0,0,0,0 makes all particles overlap)
let aReadIdx = 0;  // Current read FBO index (0 or 1)
let bReadIdx = 0;  // Buffer B current read FBO index (0 or 1)

function initPass() {
    // ===== Buffer A Initialization =====
    // Render first frame using FBO 0
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[0]);
    gl.viewport(0, 0, width, height);
    gl.useProgram(programBufferA);
    setupAttribute(programBufferA);
    // Bind FBO 1's texture as input (not yet rendered, but avoids binding errors)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iChannel0'), 0);
    gl.uniform2f(gl.getUniformLocation(programBufferA, 'iResolution'), width, height);
    gl.uniform1f(gl.getUniformLocation(programBufferA, 'iTime'), 0);
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iFrame'), 0);
    gl.uniform4f(gl.getUniformLocation(programBufferA, 'iMouse'), 0, 0, 0, 0);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Render second frame using FBO 1 (iFrame=1)
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[1]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[0]);  // Read FBO 0's result
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iFrame'), 1);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Render one more frame to ensure initialization is complete
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[0]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);
    gl.uniform1i(gl.getUniformLocation(programBufferA, 'iFrame'), 2);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // ===== Buffer B Initialization =====
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[2]);  // B_FBO0
    gl.viewport(0, 0, width, height);
    gl.useProgram(programBufferB);
    setupAttribute(programBufferB);

    // Bind latest Buffer A result (FBO 0's result)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[0]);
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iChannel0'), 0);

    // Bind Buffer B previous frame (FBO 3's texture, not yet rendered)
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[3]);
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iChannel1'), 1);

    gl.uniform2f(gl.getUniformLocation(programBufferB, 'iResolution'), width, height);
    gl.uniform1f(gl.getUniformLocation(programBufferB, 'iTime'), 0);
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iFrame'), 0);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Buffer B second frame
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[3]);  // B_FBO1
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[1]);  // Buffer A latest
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[2]);  // Buffer B FBO0 result
    gl.uniform1i(gl.getUniformLocation(programBufferB, 'iFrame'), 1);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Initialize ping-pong indices
    aReadIdx = 0;  // Next frame reads FBO 0
    bReadIdx = 0;  // Next frame reads FBO 2

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}

function render() {
    // ===== Pass 1: Buffer A (Particle Physics Self-Feedback) =====
    // aReadIdx = 0: read FBO 0, write FBO 1
    // aReadIdx = 1: read FBO 1, write FBO 0
    const aWriteIdx = 1 - aReadIdx;

    // Write to target FBO (not the current read FBO)
    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[aWriteIdx]);
    gl.viewport(0, 0, width, height);

    // Read previous frame Buffer A texture (from current read FBO's texture)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[aReadIdx]);
    gl.uniform1i(uniformsBufferA.iChannel0, 0);

    gl.uniform2f(uniformsBufferA.iResolution, width, height);
    gl.uniform1f(uniformsBufferA.iTime, time);
    gl.uniform1i(uniformsBufferA.iFrame, frameCount);
    gl.uniform4f(uniformsBufferA.iMouse, mouse.x, mouse.y, mouse.z, mouse.w);

    // Render particle physics
    gl.useProgram(programBufferA);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Switch read index
    aReadIdx = aWriteIdx;

    // ===== Pass 2: Buffer B (Density Field) =====
    const bWriteIdx = 1 - bReadIdx;

    gl.bindFramebuffer(gl.FRAMEBUFFER, buffers[2 + bWriteIdx]);  // B_FBO0 or B_FBO1
    gl.viewport(0, 0, width, height);

    // Bind current Buffer A particle state (use latest Buffer A result)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[aReadIdx]);  // A latest result
    gl.uniform1i(uniformsBufferB.iChannel0, 0);

    // Bind previous frame Buffer B density (for accumulation)
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[2 + bReadIdx]);  // B_read
    gl.uniform1i(uniformsBufferB.iChannel1, 1);

    gl.uniform2f(uniformsBufferB.iResolution, width, height);
    gl.uniform1f(uniformsBufferB.iTime, time);
    gl.uniform1i(uniformsBufferB.iFrame, frameCount);

    // Render density accumulation
    gl.useProgram(programBufferB);
    gl.drawArrays(gl.TRIANGLES, 0, 6);

    // Switch Buffer B read index
    bReadIdx = bWriteIdx;

    // ===== Pass 3: Image (Final Rendering to Screen) =====
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, width, height);

    // Bind Buffer A particles (use latest Buffer A result)
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textures[aReadIdx]);
    gl.uniform1i(uniformsImage.iChannel0, 0);

    // Bind Buffer B density (use latest Buffer B result)
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, textures[2 + bReadIdx]);
    gl.uniform1i(uniformsImage.iChannel1, 1);

    gl.uniform2f(uniformsImage.iResolution, width, height);
    gl.uniform1f(uniformsImage.iTime, time);
    gl.uniform1i(uniformsImage.iFrame, frameCount);
    gl.uniform4f(uniformsImage.iMouse, mouse.x, mouse.y, mouse.z, mouse.w);

    // Render to screen
    gl.useProgram(programImage);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
}
```**重要：要点**：
- **必须使用2个FBO进行乒乓**：每个Buffer需要两个独立的FBO（读FBO + 写FBO）；单个 FBO + 纹理交换导致“反馈循环”错误
- 使用FBO索引切换（不是纹理交换）：写入时绑定目标FBO，读取时绑定源纹理
- Image pass绑定最新的Buffer结果（通过读取索引获得）

## 表演与作曲

**性能优化**：
- 可分离模糊：N² → 2N 个样本
- 双线性抽头技巧：5 个样本取代 9 抽头高斯
- MIP 采样取代了大内核：高 MIP 级别的 `textureLod` ≈ 大范围平均值
-“丢弃”外部数据区域以跳过不必要的计算
- RGBA 通道封装：一个 vec4 中的速度（xy）+密度（z）+旋度（w）
- 链接子步骤：A→B→C 相同的代码可实现 3 倍模拟速度
- `if (dot(b,b) > bbMax) break;` 自适应提前退出
- `iFrame < 20` 渐进式初始化以防止爆炸

**典型的构图模式**：
- **流体+照明**：流体缓冲区→图像计算梯度法线→漫反射+镜面反射
- **流体 + 颜色平流**：单独的缓冲区跟踪颜色场，通过速度场平流
- **场景 + Bloom + TAA**：4 缓冲区管道（渲染 → 下采样 → 模糊 → 复合色调映射）
- **G-Buffer + 屏幕空间效果**：没有时间反馈的 2-Buffer（几何 → 边缘/SSAO/SSR → 风格化合成）
- **状态存储+可视化分离**：Buffer A纯逻辑+图像纯渲染（`texelFetch`读取状态+距离场绘制）

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/multipass-buffer.md)