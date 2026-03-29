# 调色板和色彩空间

## 用例
- 将标量值（距离、温度、时间、迭代次数）映射到连续色带
- 感知均匀的颜色插值/渐变
- 使用线性空间工作流程进行 HDR 渲染（sRGB 解码 -> 着色 -> 色调映射 -> sRGB 编码）
- 物理真实的发光/火焰/黑体辐射颜色

## 核心原则

核心：**将 [0,1] 中的标量 t 映射到 RGB vec3**。

### 余弦调色板```
color(t) = a + b * cos(2pi * (c * t + d))
```- **a** = 亮度偏移 (~0.5)，**b** = 幅度 (~0.5)，**c** = 频率，**d** = 相位（控制颜色样式的关键参数）

### HSV/HSL 无分支转换```
rgb = clamp(abs(mod(H*6 + vec3(0,4,2), 6) - 3) - 1, 0, 1)
```使用分段线性函数来近似 RGB 随色调的变化。 C1连续性可以通过“rgb*rgb*(3-2*rgb)”来实现。

### CIE Lab/Lch 感知均匀插值
RGB -> XYZ -> Lab -> Lch 管线；在感知均匀的空间中进行插值以避免 RGB/HSV 中的亮度不连续性。

### 黑体辐射调色板
温度 T -> 普朗克轨迹近似 -> CIE 色度 -> XYZ -> RGB，用 Stefan-Boltzmann (T^4) 控制亮度。

## 实施

### 余弦调色板```glsl
// a: offset, b: amplitude, c: frequency, d: phase, t: input scalar
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}
```### 经典预设参数```glsl
// Rainbow: d=(0.0, 0.33, 0.67)
// Warm: d=(0.0, 0.10, 0.20)
// Blue-purple to orange: c=(1,0.7,0.4) d=(0.0, 0.15, 0.20)
// Warm-cool mix: a=(.8,.5,.4) b=(.2,.4,.2) c=(2,1,1) d=(0.0, 0.25, 0.25)

// Simplified version: fixed a/b/c, only adjust d
vec3 palette(float t) {
    vec3 a = vec3(0.5, 0.5, 0.5);
    vec3 b = vec3(0.5, 0.5, 0.5);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.263, 0.416, 0.557);
    return a + b * cos(6.28318 * (c * t + d));
}
```### HSV -> RGB（标准 + 平滑）```glsl
// Standard HSV -> RGB (branchless)
vec3 hsv2rgb(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return c.z * mix(vec3(1.0), rgb, c.y);
}

// Smooth version (C1 continuous)
vec3 hsv2rgb_smooth(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    rgb = rgb * rgb * (3.0 - 2.0 * rgb); // Hermite smoothing
    return c.z * mix(vec3(1.0), rgb, c.y);
}
```### HSL -> RGB```glsl
vec3 hue2rgb(float h) {
    return clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
}

vec3 hsl2rgb(float h, float s, float l) {
    vec3 rgb = hue2rgb(h);
    return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}
```### RGB -> HSV```glsl
// Sam Hocevar branchless method
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
```### CIE 实验室/Lch 转换管道```glsl
float xyzF(float t) { return mix(pow(t, 1.0/3.0), 7.787037 * t + 0.139731, step(t, 0.00885645)); }
float xyzR(float t) { return mix(t * t * t, 0.1284185 * (t - 0.139731), step(t, 0.20689655)); }

vec3 rgb2lch(vec3 c) {
    c *= mat3(0.4124, 0.3576, 0.1805,
              0.2126, 0.7152, 0.0722,
              0.0193, 0.1192, 0.9505);
    c = vec3(xyzF(c.x), xyzF(c.y), xyzF(c.z));
    vec3 lab = vec3(max(0.0, 116.0 * c.y - 16.0),
                    500.0 * (c.x - c.y),
                    200.0 * (c.y - c.z));
    return vec3(lab.x, length(lab.yz), atan(lab.z, lab.y));
}

vec3 lch2rgb(vec3 c) {
    c = vec3(c.x, cos(c.z) * c.y, sin(c.z) * c.y);
    float lg = (1.0 / 116.0) * (c.x + 16.0);
    vec3 xyz = vec3(xyzR(lg + 0.002 * c.y),
                    xyzR(lg),
                    xyzR(lg - 0.005 * c.z));
    return xyz * mat3( 3.2406, -1.5372, -0.4986,
                      -0.9689,  1.8758,  0.0415,
                       0.0557, -0.2040,  1.0570);
}

// Circular hue interpolation
float lerpAngle(float a, float b, float x) {
    float ang = mod(mod((a - b), 6.28318) + 9.42477, 6.28318) - 3.14159;
    return ang * x + b;
}

vec3 lerpLch(vec3 a, vec3 b, float x) {
    return vec3(mix(b.xy, a.xy, x), lerpAngle(a.z, b.z, x));
}
```### sRGB 伽玛和色调映射```glsl
// Precise sRGB encoding
float sRGB_encode(float t) {
    return mix(1.055 * pow(t, 1.0/2.4) - 0.055, 12.92 * t, step(t, 0.0031308));
}
vec3 sRGB_encode(vec3 c) {
    return vec3(sRGB_encode(c.x), sRGB_encode(c.y), sRGB_encode(c.z));
}

// Fast approximation: pow(color, vec3(2.2)) / pow(color, vec3(1.0/2.2))

// Reinhard tone mapping
vec3 tonemap_reinhard(vec3 col) {
    return col / (1.0 + col);
}
```### 黑体辐射调色板```glsl
#define TEMP_MAX 4000.0 // Tunable: maximum temperature (K)
vec3 blackbodyPalette(float t) {
    t *= TEMP_MAX;
    float cx = (0.860117757 + 1.54118254e-4 * t + 1.28641212e-7 * t * t)
             / (1.0 + 8.42420235e-4 * t + 7.08145163e-7 * t * t);
    float cy = (0.317398726 + 4.22806245e-5 * t + 4.20481691e-8 * t * t)
             / (1.0 - 2.89741816e-5 * t + 1.61456053e-7 * t * t);
    float d = 2.0 * cx - 8.0 * cy + 4.0;
    vec3 XYZ = vec3(3.0 * cx / d, 2.0 * cy / d, 1.0 - (3.0 * cx + 2.0 * cy) / d);
    vec3 RGB = mat3(3.240479, -0.969256, 0.055648,
                   -1.537150,  1.875992, -0.204043,
                   -0.498535,  0.041556,  1.057311) * vec3(XYZ.x / XYZ.y, 1.0, XYZ.z / XYZ.y);
    return max(RGB, 0.0) * pow(t * 0.0004, 4.0);
}
```## 完整的代码模板

演示所有核心技术的 ShaderToy 着色器：```glsl
// === Procedural Color Palette Showcase ===
#define PI  3.14159265
#define TAU 6.28318530

// ============ Tunable Parameters ============
#define PALETTE_A vec3(0.5, 0.5, 0.5)   // Offset: increase = brighter overall
#define PALETTE_B vec3(0.5, 0.5, 0.5)   // Amplitude: increase = more contrast
#define PALETTE_C vec3(1.0, 1.0, 1.0)   // Frequency: increase = denser color variation
#define PALETTE_D vec3(0.0, 0.33, 0.67) // Phase: change = completely different hues
#define TEMP_MAX 4000.0                  // Blackbody max temperature (K)
#define NUM_ITER 4                       // Fractal iteration count

// ============ Color Functions ============

vec3 cosinePalette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

vec3 palette(float t) {
    return cosinePalette(t, PALETTE_A, PALETTE_B, PALETTE_C, PALETTE_D);
}

vec3 hsv2rgb(vec3 c) {
    vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    rgb = rgb * rgb * (3.0 - 2.0 * rgb);
    return c.z * mix(vec3(1.0), rgb, c.y);
}

vec3 hsl2rgb(float h, float s, float l) {
    vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

vec3 blackbodyPalette(float t) {
    t *= TEMP_MAX;
    float cx = (0.860117757 + 1.54118254e-4*t + 1.28641212e-7*t*t)
             / (1.0 + 8.42420235e-4*t + 7.08145163e-7*t*t);
    float cy = (0.317398726 + 4.22806245e-5*t + 4.20481691e-8*t*t)
             / (1.0 - 2.89741816e-5*t + 1.61456053e-7*t*t);
    float d = 2.0*cx - 8.0*cy + 4.0;
    vec3 XYZ = vec3(3.0*cx/d, 2.0*cy/d, 1.0 - (3.0*cx + 2.0*cy)/d);
    vec3 RGB = mat3(3.240479, -0.969256, 0.055648,
                   -1.537150,  1.875992, -0.204043,
                   -0.498535,  0.041556,  1.057311) * vec3(XYZ.x/XYZ.y, 1.0, XYZ.z/XYZ.y);
    return max(RGB, 0.0) * pow(t * 0.0004, 4.0);
}

vec3 sRGB(vec3 c) { return pow(clamp(c, 0.0, 1.0), vec3(1.0/2.2)); }
vec3 tonemap(vec3 c) { return c / (1.0 + c); }

// ============ Main ============

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;
    vec2 uv0 = uv;
    float band = fragCoord.y / iResolution.y;
    vec3 col = vec3(0.0);

    if (band < 0.2) {
        // Cosine Palette
        float t = fragCoord.x / iResolution.x + iTime * 0.1;
        col = palette(t);
    } else if (band < 0.4) {
        // HSV color wheel
        float h = fragCoord.x / iResolution.x;
        float v = (band - 0.2) / 0.2;
        col = hsv2rgb(vec3(h + iTime * 0.05, 1.0, v));
    } else if (band < 0.6) {
        // HSL color wheel
        float h = fragCoord.x / iResolution.x;
        float l = (band - 0.4) / 0.2;
        col = hsl2rgb(h + iTime * 0.05, 1.0, l);
    } else if (band < 0.8) {
        // Blackbody radiation
        float t = fragCoord.x / iResolution.x;
        col = tonemap(blackbodyPalette(t));
    } else {
        // Cosine Palette fractal glow
        vec2 p = uv;
        vec3 finalColor = vec3(0.0);
        for (int i = 0; i < NUM_ITER; i++) {
            p = fract(p * 1.5) - 0.5;
            float d = length(p) * exp(-length(uv0));
            vec3 c = palette(length(uv0) + float(i) * 0.4 + iTime * 0.4);
            d = sin(d * 8.0 + iTime) / 8.0;
            d = abs(d);
            d = pow(0.01 / d, 1.2);
            finalColor += c * d;
        }
        col = tonemap(finalColor);
    }

    // Band separator lines
    float bandLine = smoothstep(0.003, 0.0, abs(fract(band * 5.0) - 0.5) - 0.49);
    col *= 1.0 - bandLine * 0.8;
    col = sRGB(col);
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 多谐波余弦调色板（抗锯齿）```glsl
vec3 fcos(vec3 x) {
    vec3 w = fwidth(x);
    return cos(x) * smoothstep(TAU, 0.0, w);
}

vec3 getColor(float t) {
    vec3 col = vec3(0.4);
    col += 0.12 * fcos(TAU * t *   1.0 + vec3(0.0, 0.8, 1.1));
    col += 0.11 * fcos(TAU * t *   3.1 + vec3(0.3, 0.4, 0.1));
    col += 0.10 * fcos(TAU * t *   5.1 + vec3(0.1, 0.7, 1.1));
    col += 0.09 * fcos(TAU * t *   9.1 + vec3(0.2, 0.8, 1.4));
    col += 0.08 * fcos(TAU * t *  17.1 + vec3(0.2, 0.6, 0.7));
    col += 0.07 * fcos(TAU * t *  31.1 + vec3(0.1, 0.6, 0.7));
    col += 0.06 * fcos(TAU * t *  65.1 + vec3(0.0, 0.5, 0.8));
    col += 0.06 * fcos(TAU * t * 115.1 + vec3(0.1, 0.4, 0.7));
    col += 0.09 * fcos(TAU * t * 265.1 + vec3(1.1, 1.4, 2.7));
    return col;
}
```### 哈希驱动的每图块颜色```glsl
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 tileId = floor(uv);
vec3 tileColor = palette(hash12(tileId));
```### 保留饱和度的改进 RGB 插值```glsl
float getsat(vec3 c) {
    float mi = min(min(c.x, c.y), c.z);
    float ma = max(max(c.x, c.y), c.z);
    return (ma - mi) / (ma + 1e-7);
}

vec3 iLerp(vec3 a, vec3 b, float x) {
    vec3 ic = mix(a, b, x) + vec3(1e-6, 0.0, 0.0);
    float sd = abs(getsat(ic) - mix(getsat(a), getsat(b), x));
    vec3 dir = normalize(vec3(2.0*ic.x - ic.y - ic.z,
                              2.0*ic.y - ic.x - ic.z,
                              2.0*ic.z - ic.y - ic.x));
    float lgt = dot(vec3(1.0), ic);
    float ff = dot(dir, normalize(ic));
    ic += 1.5 * dir * sd * ff * lgt;
    return clamp(ic, 0.0, 1.0);
}
```### 圆形色调插值```glsl
// HSV space (hue [0,1])
vec3 lerpHSV(vec3 a, vec3 b, float x) {
    float hue = (mod(mod((b.x - a.x), 1.0) + 1.5, 1.0) - 0.5) * x + a.x;
    return vec3(hue, mix(a.yz, b.yz, x));
}

// Lch space (hue [0, 2pi])
float lerpAngle(float a, float b, float x) {
    float ang = mod(mod((a - b), TAU) + PI * 3.0, TAU) - PI;
    return ang * x + b;
}
```### 附加颜色叠加（发光/HDR）```glsl
vec3 finalColor = vec3(0.0);
for (int i = 0; i < 4; i++) {
    vec3 col = palette(length(uv) + float(i) * 0.4 + iTime * 0.4);
    float glow = pow(0.01 / abs(sdfValue), 1.2);
    finalColor += col * glow;
}
finalColor = finalColor / (1.0 + finalColor); // Reinhard tonemap
```## 表演与作曲

**性能提示：**
- 余弦调色板：~3-4 个时钟周期（1 MAD + 1 COS + 1 MAD）
- HSV/HSL 转换：使用“mod”/“abs”/“clamp”矢量化完全无分支
- 多谐波带限滤波：`fwidth()` + `smoothstep` 添加了约 2 条额外指令来消除混叠
- Lch 流水线 ~57 条指令；如果您只需要“比 RGB 稍微好一点”，请使用 `iLerp` （~15 条指令）
- sRGB 近似值 `pow(c, 2.2)` 的误差 <0.4%，并且在编译器中优化得更好

**常见组合：**
- **余弦调色板 + SDF Raymarching**：法线/距离/属性作为 t 输入
- **HSL/HSV + 数据可视化**：迭代计数 -> 色调、饱和度/亮度编码其他维度
- **余弦调色板 + 分形/噪声**：`length(uv)` 或 `fbm(p)` + `iTime` 驱动动态颜色
- **黑体 + 体渲染/火**：温度场 -> `blackbodyPalette()` -> 物理上合理的颜色
- **线性空间工作流程**：sRGB 解码 -> 线性着色 -> 色调图 -> sRGB 编码
- **散列+调色板+平铺**：`散列（tileID）`作为调色板输入以实现统一的颜色和谐

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/color-palette.md)