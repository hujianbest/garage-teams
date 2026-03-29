# 2D 程序模式

## 用例
- 重复/非周期性 2D 图案：网格、六边形、Truchet、干涉图案、万花筒、螺旋、Lissajous
- 程序背景、UI 纹理、科幻 HUD/雷达
- 分形、水焦散和其他自然现象
- 无限细节、无缝平铺、参数驱动的视觉效果

## 核心原则

2D 程序模式 = **域变换 + 距离场 + 颜色映射**：

1. **域重复**： `fract()`/`mod()` 将无限平面折叠成重复单元
2. **单元格识别**：`floor()`提取整数坐标作为哈希种子，驱动每个单元格的随机变化
3. **距离场（SDF）**：数学函数计算像素到形状的距离，“smoothstep”渲染边缘
4. **颜色映射**：余弦调色板 `a + b*cos(2pi(c*t+d))` 或 HSV
5. **图层合成**：通过加法/乘法/`mix`混合多层循环结果

关键公式：```glsl
// UV normalization
uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;
// Domain repetition
cell_uv = fract(uv * SCALE) - 0.5;
cell_id = floor(uv * SCALE);
// Cosine palette
col = a + b * cos(6.28318 * (c * t + d));
// Hexagon SDF
hex(p) = max(dot(abs(p), vec2(0.5, 0.866025)), abs(p).x);
// 2D rotation
mat2(cos(a), -sin(a), sin(a), cos(a));
```## 实施步骤

### 第 1 步：UV 归一化```glsl
vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;
```### 第 2 步：域重复```glsl
#define SCALE 4.0
vec2 cell_uv = fract(uv * SCALE) - 0.5;
vec2 cell_id = floor(uv * SCALE);
```六边形网格域重复：```glsl
const vec2 s = vec2(1, 1.7320508);
vec4 hC = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
vec4 h = vec4(p - hC.xy * s, p - (hC.zw + 0.5) * s);
vec4 hex_data = dot(h.xy, h.xy) < dot(h.zw, h.zw)
    ? vec4(h.xy, hC.xy)
    : vec4(h.zw, hC.zw + vec2(0.5, 1.0));
```### 步骤 3：每个细胞随机化```glsl
float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(141.173, 289.927))) * 43758.5453);
}
float rnd = hash21(cell_id);
float radius = 0.15 + 0.1 * rnd;
```### 步骤 4：SDF 形状绘制```glsl
// Circle
float d = length(cell_uv) - radius;

// Hexagon
float hex_sdf(vec2 p) {
    p = abs(p);
    return max(dot(p, vec2(0.5, 0.866025)), p.x);
}

// Line segment
float line_sdf(vec2 a, vec2 b, vec2 p) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// Anti-aliased rendering
float shape = 1.0 - smoothstep(radius - 0.008, radius + 0.008, length(cell_uv));
```### 步骤 5：极坐标环/弧```glsl
vec2 polar = vec2(length(uv), atan(uv.y, uv.x));
float ring_id = floor(polar.x * NUM_RINGS + 0.5) / NUM_RINGS;
float ring = 1.0 - pow(abs(sin(polar.x * 3.14159 * NUM_RINGS)) * 1.25, 2.5);
float arc_end = polar.y + sin(iTime + ring_id * 5.5) * 1.52 - 1.5;
ring *= smoothstep(0.0, 0.05, arc_end);
```### 步骤 6：余弦调色板```glsl
vec3 palette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.28318 * (c * t + d));
}
```### 步骤 7：迭代堆叠和发光```glsl
#define NUM_LAYERS 4.0
vec3 finalColor = vec3(0.0);
vec2 uv0 = uv;
for (float i = 0.0; i < NUM_LAYERS; i++) {
    uv = fract(uv * 1.5) - 0.5;
    float d = length(uv) * exp(-length(uv0));
    vec3 col = palette(length(uv0) + i * 0.4 + iTime * 0.4);
    d = sin(d * 8.0 + iTime) / 8.0;
    d = abs(d);
    d = pow(0.01 / d, 1.2);
    finalColor += col * d;
}
```### 步骤 8：三角干涉```glsl
#define MAX_ITER 5
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
```### 步骤 9：多层深度合成```glsl
#define NUM_DEPTH_LAYERS 4.0
float m = 0.0;
for (float i = 0.0; i < 1.0; i += 1.0 / NUM_DEPTH_LAYERS) {
    float z = fract(iTime * 0.1 + i);
    float size = mix(15.0, 1.0, z);
    float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z);
    m += fade * patternLayer(uv * size, i, iTime);
}
```### 第 10 步：后处理```glsl
col = pow(clamp(col, 0.0, 1.0), vec3(1.0 / 2.2));                          // Gamma
col = col * 0.6 + 0.4 * col * col * (3.0 - 2.0 * col);                    // Contrast S-curve
col = mix(col, vec3(dot(col, vec3(0.33))), -0.4);                          // Saturation
vec2 q = fragCoord / iResolution.xy;
col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.7); // Vignette
```## 完整的代码模板```glsl
// ====== 2D Procedural Pattern Template ======
// Ready to run in ShaderToy

#define SCALE 3.0
#define NUM_LAYERS 4.0
#define ZOOM_FACTOR 1.5
#define GLOW_WIDTH 0.01
#define GLOW_POWER 1.2
#define WAVE_FREQ 8.0
#define ANIM_SPEED 0.4
#define RING_COUNT 10.0

vec3 palette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.28318 * (c * t + d));
}

float hash21(vec2 p) {
    return fract(sin(dot(p, vec2(141.173, 289.927))) * 43758.5453);
}

mat2 rot2(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;
    vec2 uv0 = uv;
    vec3 finalColor = vec3(0.0);

    for (float i = 0.0; i < NUM_LAYERS; i++) {
        uv = fract(uv * ZOOM_FACTOR) - 0.5;
        float d = length(uv) * exp(-length(uv0));
        vec3 col = palette(length(uv0) + i * 0.4 + iTime * ANIM_SPEED);
        d = sin(d * WAVE_FREQ + iTime) / WAVE_FREQ;
        d = abs(d);
        d = pow(GLOW_WIDTH / d, GLOW_POWER);
        finalColor += col * d;
    }

    finalColor = pow(clamp(finalColor, 0.0, 1.0), vec3(1.0 / 2.2));
    finalColor = finalColor * 0.6 + 0.4 * finalColor * finalColor * (3.0 - 2.0 * finalColor);
    vec2 q = fragCoord / iResolution.xy;
    finalColor *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.7);

    fragColor = vec4(finalColor, 1.0);
}
```## 常见变体

### 变体 1：六角形特鲁切弧```glsl
float hex(vec2 p) {
    p = abs(p);
    return max(dot(p, vec2(0.5, 0.866025)), p.x);
}

const vec2 s = vec2(1.0, 1.7320508);
vec4 getHex(vec2 p) {
    vec4 hC = floor(vec4(p, p - vec2(0.5, 1.0)) / s.xyxy) + 0.5;
    vec4 h = vec4(p - hC.xy * s, p - (hC.zw + 0.5) * s);
    return dot(h.xy, h.xy) < dot(h.zw, h.zw)
        ? vec4(h.xy, hC.xy)
        : vec4(h.zw, hC.zw + vec2(0.5, 1.0));
}

// Truchet triple arcs
float r = 1.0;
vec2 q1 = p - vec2(0.0, r) / s;
vec2 q2 = rot2(6.28318 / 3.0) * p - vec2(0.0, r) / s;
vec2 q3 = rot2(6.28318 * 2.0 / 3.0) * p - vec2(0.0, r) / s;
float d = min(min(length(q1), length(q2)), length(q3));
d = abs(d - 0.288675) - 0.1;
```### 变体 2：水腐蚀性干扰```glsl
#define TAU 6.28318530718
#define MAX_ITER 5
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
colour = clamp(colour + vec3(0.0, 0.35, 0.5), 0.0, 1.0);
```### 变体 3：极同心环弧段```glsl
#define NUM_RINGS 20.0
#define PALETTE vec3(0.0, 1.4, 2.0) + 1.5
vec2 plr = vec2(length(p), atan(p.y, p.x));
float id = floor(plr.x * NUM_RINGS + 0.5) / NUM_RINGS;
p *= rot2(id * 11.0);
p.y = abs(p.y);
float rz = 1.0 - pow(abs(sin(plr.x * 3.14159 * NUM_RINGS)) * 1.25, 2.5);
float arc = plr.y + sin(iTime + id * 5.5) * 1.52 - 1.5;
rz *= smoothstep(0.0, 0.05, arc);
vec3 col = (sin(PALETTE + id * 5.0 + iTime) * 0.5 + 0.5) * rz;
```### 变体 4：多层深度视差网络```glsl
#define NUM_DEPTH_LAYERS 4.0
vec2 GetPos(vec2 id, vec2 offs, float t) {
    float n = hash21(id + offs);
    return offs + vec2(sin(t + n * 6.28), cos(t + fract(n * 100.0) * 6.28)) * 0.4;
}
float df_line(vec2 a, vec2 b, vec2 p) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}
float m = 0.0;
for (float i = 0.0; i < 1.0; i += 1.0 / NUM_DEPTH_LAYERS) {
    float z = fract(iTime * 0.1 + i);
    float size = mix(15.0, 1.0, z);
    float fade = smoothstep(0.0, 0.6, z) * smoothstep(1.0, 0.8, z);
    m += fade * NetLayer(uv * size, i, iTime);
}
```### 变体 5：分形阿波罗```glsl
float apollian(vec4 p, float s) {
    float scale = 1.0;
    for (int i = 0; i < 7; ++i) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
        float r2 = dot(p, p);
        float k = s / r2;
        p *= k;
        scale *= k;
    }
    return abs(p.y) / scale;
}
vec4 pp = vec4(p.x, p.y, 0.0, 0.0) + offset;
pp.w = 0.125 * (1.0 - tanh(length(pp.xyz)));
float d = apollian(pp / 4.0, 1.2) * 4.0;
float hue = fract(0.75 * length(p) - 0.3 * iTime) + 0.3;
float sat = 0.75 * tanh(2.0 * length(p));
vec3 col = hsv2rgb(vec3(hue, sat, 1.0));
```## 表演与作曲

**性能：**
- 迭代循环是最大的瓶颈； `NUM_LAYERS` 4->8 性能减半；移动设备应使用 3 层或更少
- 使用 `step()`/`smoothstep()`/`mix()` 而不是 `if/else`
- 使用 `min()`/`max()` 合并多个 SDF，然后应用单个 `smoothstep`
- 在循环外预先计算 `sin`/`cos` 对；将无理常量写为文字值
- `atan` 很贵；当只需要周期性时使用“点”近似
- LOD：减少远处对象的迭代 `int iters = int(mix(3.0, float(MAX_ITER), smoothstep(...)));`
- `smoothstep` 通常比 `pow` 更好并且本质上限制在 [0,1]

**组合：**
- **+ 噪声**：`d += triangleNoise(uv * 10.0) * 0.05;` 用于有机侵蚀感
- **+ 交叉影线**：灰度阈值 + `sin` 线来模拟手绘风格
- **+ SDF Boolean**：复杂几何的“min”（并集）/“max”（交集）/减法
- **+ 域畸变**：`uv += 0.05 * vec2(sin(uv.y*5.+iTime), sin(uv.x*3.+iTime));`
- **+径向模糊**：沿极坐标方向的多样本平均
- **+ 伪 3D 照明**：SDF 渐变正常，添加漫反射/镜面反射以获得浮雕外观

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/procedural-2d-pattern.md)