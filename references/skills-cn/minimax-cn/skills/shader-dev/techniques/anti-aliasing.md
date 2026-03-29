# 抗锯齿技术

## 用例
- 消除光线行进或 SDF 渲染场景中的锯齿状边缘（楼梯伪影）
- 平滑的 2D SDF 形状渲染
- 对任何着色器输出进行后处理边缘平滑
- 用于降噪的时间平滑

## 核心原则

着色器中的抗锯齿与光栅化管道不同。如果程序几何上没有硬件 MSAA，我们只能依靠分析或后处理方法。

## 技巧

### 1. Ray Marching 的超级采样 (SSAA)

渲染多个子像素样本并求平均值：```glsl
#define AA 2  // 1=off, 2=4x, 3=9x
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec3 totalColor = vec3(0.0);
    for (int m = 0; m < AA; m++)
    for (int n = 0; n < AA; n++) {
        vec2 offset = vec2(float(m), float(n)) / float(AA) - 0.5;
        vec2 uv = (2.0 * (fragCoord + offset) - iResolution.xy) / iResolution.y;
        vec3 col = render(uv);
        totalColor += col;
    }
    fragColor = vec4(totalColor / float(AA * AA), 1.0);
}
```成本：AA^2 × 完整渲染。使用 AA=2 表示质量，使用 AA=1 表示开发。

### 2.SDF 分析抗锯齿

对于 2D SDF 形状，使用像素宽度来计算平滑边缘：```glsl
float d = sdShape(uv);
float fw = fwidth(d);  // screen-space derivative of SDF
float alpha = smoothstep(fw, -fw, d);  // smooth edge over exactly 1 pixel

// Alternative: manual pixel width for more control
float pixelWidth = 2.0 / iResolution.y;  // approximate pixel size in UV space
float alpha2 = smoothstep(pixelWidth, -pixelWidth, d);
```对于 3D SDF 场景，在几何体边缘应用抗锯齿：```glsl
// After ray marching, at the surface:
float edgeFade = 1.0 - smoothstep(0.0, 0.01 * t, lastSdfValue);
// t = ray distance — scales threshold with distance for consistent edge width
```### 3. 临时抗锯齿 (TAA) 基础知识

使用多通道缓冲区将当前帧与前一帧混合：```glsl
// Buffer A: render with sub-pixel jitter
vec2 jitter = (hash22(vec2(iFrame)) - 0.5) / iResolution.xy;
vec2 uv = (fragCoord + jitter) / iResolution.xy;
vec3 currentColor = render(uv);

// Buffer A output: store current render
fragColor = vec4(currentColor, 1.0);

// Image shader: blend with history
vec3 current = texture(iChannel0, fragCoord / iResolution.xy).rgb;  // this frame
vec3 history = texture(iChannel1, fragCoord / iResolution.xy).rgb;  // previous frame
float blend = 0.9;  // higher = smoother but more ghosting
fragColor = vec4(mix(current, history, blend), 1.0);
```注意：完整的 TAA 还需要运动矢量和邻域钳位以避免重影。

### 4. FXAA（快速近似抗锯齿）

简化的后处理边缘检测和平滑：```glsl
vec3 fxaa(sampler2D tex, vec2 uv, vec2 texelSize) {
    // Sample center and 4 neighbors
    vec3 rgbM = texture(tex, uv).rgb;
    vec3 rgbN = texture(tex, uv + vec2(0.0, texelSize.y)).rgb;
    vec3 rgbS = texture(tex, uv - vec2(0.0, texelSize.y)).rgb;
    vec3 rgbE = texture(tex, uv + vec2(texelSize.x, 0.0)).rgb;
    vec3 rgbW = texture(tex, uv - vec2(texelSize.x, 0.0)).rgb;

    // Luma for edge detection
    vec3 lumaCoeff = vec3(0.299, 0.587, 0.114);
    float lumaN = dot(rgbN, lumaCoeff);
    float lumaS = dot(rgbS, lumaCoeff);
    float lumaE = dot(rgbE, lumaCoeff);
    float lumaW = dot(rgbW, lumaCoeff);
    float lumaM = dot(rgbM, lumaCoeff);

    float lumaMin = min(lumaM, min(min(lumaN, lumaS), min(lumaE, lumaW)));
    float lumaMax = max(lumaM, max(max(lumaN, lumaS), max(lumaE, lumaW)));
    float lumaRange = lumaMax - lumaMin;

    // Skip if edge contrast is low
    if (lumaRange < max(0.0312, lumaMax * 0.125)) return rgbM;

    // Blend along edge direction
    vec2 dir;
    dir.x = -((lumaN + lumaS) - 2.0 * lumaM);
    dir.y = ((lumaE + lumaW) - 2.0 * lumaM);
    float dirReduce = max(lumaRange * 0.25, 1.0 / 128.0);
    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
    dir = clamp(dir * rcpDirMin, -8.0, 8.0) * texelSize;

    vec3 rgbA = 0.5 * (texture(tex, uv + dir * (1.0/3.0 - 0.5)).rgb +
                        texture(tex, uv + dir * (2.0/3.0 - 0.5)).rgb);
    return rgbA;
}
```## 选择正确的方法

|方法|成本|品质 |最适合 |
|--------|------|---------|----------|
| SSAA 2x2 | 4× 渲染 |优秀|最终质量渲染 |
| SDF分析|最小|非常适合自卫队| 2D 形状、UI 元素 |
| TAA | 1× + 混合 |好+暂时|多通道动画场景 |
| FXAA | 1 通行证 |好 |任何场景，仅限后期处理 |

→ 更深入的细节请参见 [reference/anti-aliasing.md](../reference/anti-aliasing.md)