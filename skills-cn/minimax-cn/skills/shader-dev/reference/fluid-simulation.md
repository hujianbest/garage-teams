# 流体模拟 — 详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含必备知识、分步教程、数学推导和高级用法。

## 先决条件

### GLSL 基础知识
- `texture`/`texelFetch` 采样，`iChannel0` 缓冲区反馈，多通道渲染
- ShaderToy多缓冲区架构：Buffer A/B/C/D之间的数据流

### 向量微积分基础知识
- 梯度：标量场的空间变化率，指向最大增量的方向
- 散度：矢量场的“源/汇”强度
- Curl：矢量场的局部旋转强度
- 拉普拉斯算子：标量场的二阶导数，测量与邻域平均值的偏差

### 数据编码范式
理解“将物理量编码为纹理RGBA通道”的范式：
- `.xy` = 速度
- `.z` = 压力/密度
- `.w` = 被动标量，例如墨水浓度

## 详细实施步骤

### 步骤 1：数据编码和缓冲区布局

**什么**：将流体物理量编码到纹理的 RGBA 通道中。

**为什么**：GPU 纹理充当流体状态的存储介质。每个像素都是一个网格单元，其通道存储不同的物理量，从而实现完整的流体状态持久性。

**代码**：```glsl
// Data layout convention:
// .xy = velocity field
// .z  = pressure / density
// .w  = passive scalar, e.g., ink concentration

// Sampling macro — simplify neighborhood access
#define T(p) texture(iChannel0, (p) / iResolution.xy)

// Get current pixel and its four neighbors
vec4 c = T(p);                    // center
vec4 n = T(p + vec2(0, 1));       // north
vec4 e = T(p + vec2(1, 0));       // east
vec4 s = T(p - vec2(0, 1));       // south
vec4 w = T(p - vec2(1, 0));       // west
```### 步骤 2：离散微分算子

**内容**：计算 3x3 像素邻域上的梯度、拉普拉斯算子、散度和旋度。

**为什么**：这些算子是离散化纳维-斯托克斯方程的基础。 3x3 模板比简单的十字模板更具各向同性，从而减少了网格方向伪影。

**代码**：```glsl
// ===== Laplacian =====
// Weighted 3x3 stencil: center weight _K0, edge weight _K1, corner weight _K2
const float _K0 = -20.0 / 6.0;  // adjustable: center weight
const float _K1 =   4.0 / 6.0;  // adjustable: edge weight
const float _K2 =   1.0 / 6.0;  // adjustable: corner weight

vec4 laplacian = _K0 * c
    + _K1 * (n + e + s + w)
    + _K2 * (T(p+vec2(1,1)) + T(p+vec2(-1,1)) + T(p+vec2(1,-1)) + T(p+vec2(-1,-1)));

// ===== Gradient =====
// Central difference with diagonal correction
vec4 dx = (e - w) / 2.0;
vec4 dy = (n - s) / 2.0;

// ===== Divergence =====
float div = dx.x + dy.y;  // ∂vx/∂x + ∂vy/∂y

// ===== Curl / Vorticity =====
float curl = dx.y - dy.x;  // ∂vy/∂x - ∂vx/∂y
```### 步骤 3：初始帧和噪声

**什么**：初始化流体状态并注入少量噪声以避免对称锁定。

**为什么**：如果初始状态完全为零（零速度），流体方程将保持这种对称状态并且永远不会移动。添加少量随机噪声会破坏对称性，从而使湍流自然发展。

**代码**：```glsl
if (iFrame < 10) {
    vec2 uv = p / iResolution.xy;
    // Position-based pseudo-random noise
    float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453);
    // velocity.xy = small noise, pressure.z = 1.0, ink.w = small amount
    fragColor = vec4(noise * 1e-4, noise * 1e-4, 1.0, noise * 0.1);
    return;
}
```### 步骤 4：半拉格朗日平流

**什么**：沿着速度场向后追踪，并从上游位置采样以更新当前像素。

**为什么**：这是处理“-(v·∇)v”平流项的标准方法。欧拉网格上的直接前向平流会导致不稳定，而半拉格朗日方法是无条件稳定的——无论时间步长如何，它都不会爆炸。

**代码**：```glsl
#define DT 0.15  // adjustable: time step, larger = faster fluid motion but may reduce accuracy

// Core: backward tracing — find the "upstream" position by tracing backward along velocity
// Then sample from the upstream position, effectively "transporting" the upstream state here
vec4 advected = T(p - DT * c.xy);

// Only advect velocity and passive scalar (ink), preserve local pressure
c.xyw = advected.xyw;
```### 步骤 5：粘性扩散

**内容**：将拉普拉斯扩散应用于速度场以模拟粘度。

**为什么**：对应于“ν∇²v”术语。粘度使速度场变得平滑，消散小规模涡流。参数“ν”控制流体的行为是否像“水”（低粘度）或“蜂蜜”（高粘度）。

**代码**：```glsl
#define NU 0.5     // adjustable: kinematic viscosity coefficient. 0.01=water, 1.0=syrup
#define KAPPA 0.1  // adjustable: passive scalar (ink) diffusion coefficient

c.xy  += DT * NU * laplacian.xy;     // velocity diffusion
c.w   += DT * KAPPA * laplacian.w;   // ink diffusion
```### 第 6 步：压力投影

**什么**：计算压力场的梯度并从速度场中减去它以强制不可压缩约束。

**为什么**：这是亥姆霍兹-霍奇分解的核心——将速度场分解为无散度部分（我们想要的）和无旋度部分。通过通过“v = v - K·∇p”投影散度分量，我们确保“∇·v ≈ 0”。在 ShaderToy 中，每帧缓冲区反馈本身构成隐式雅可比迭代。

**代码**：```glsl
#define K 0.2  // adjustable: pressure correction strength. Too large causes oscillation, too small yields poor incompressibility

// Pressure is stored in the .z channel
// Use pressure gradient to correct velocity, eliminating divergence
c.xy -= K * vec2(dx.z, dy.z);

// Mass conservation: update density/pressure based on divergence (Euler method)
c.z -= DT * (dx.z * c.x + dy.z * c.y + div * c.z);
```### 步骤 7：外力和鼠标交互

**内容**：根据鼠标输入将速度和墨水注入流体中。

**为什么**：外力项“f”是用户交互的入口点。典型的方法是在鼠标位置附近应用高斯衰减速度脉冲和墨水注射。

**代码**：```glsl
// Mouse interaction — drag to inject velocity and ink
if (iMouse.z > 0.0) {
    vec2 mousePos = iMouse.xy;
    vec2 mouseDelta = iMouse.xy - iMouse.zw;  // drag direction

    float dist = length(p - mousePos);
    float influence = exp(-dist * dist / 50.0);  // adjustable: 50.0 controls influence radius

    c.xy += DT * influence * mouseDelta;  // inject velocity
    c.w  += DT * influence;                // inject ink
}
```### 步骤 8：边界条件和数值稳定性

**内容**：处理边界像素、限制数值范围并应用耗散。

**为什么**：没有边界条件，流体“泄漏”到屏幕外；如果没有耗散，流体能量会无限累积，导致数值爆炸。

**代码**：```glsl
// Boundary condition: zero velocity at edge pixels (no-slip)
if (p.x < 1.0 || p.y < 1.0 ||
    iResolution.x - p.x < 1.0 || iResolution.y - p.y < 1.0) {
    c.xyw *= 0.0;
}

// IMPORTANT: Ink decay: must use multiplicative decay; subtractive decay causes saturation in high-concentration areas and overly fast decay in low-concentration areas
c.w *= 0.995;  // 0.5% decay per frame, adjustable [0.99=fast dissipation, 0.999=persistent]

// Numerical clamping (prevent explosion)
c = clamp(c, vec4(-5, -5, 0.5, 0), vec4(5, 5, 3, 5));
```### 步骤 9：可视化渲染（图像传递）

**什么**：将物理量从缓冲区映射到可见颜色。

**为什么**：原始物理数据（速度、压力）需要艺术色彩映射才能产生视觉效果。常见技术包括：将速度方向映射到色调、将压力映射到亮度以及叠加墨水浓度。

**代码**：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 c = texture(iChannel0, uv);

    // IMPORTANT: Color base must be bright enough! 0.5+0.5*cos produces bright colors in [0,1] range
    // Never use extremely dark base colors like vec3(0.02, 0.01, 0.08) — multiplied by ink, they become invisible
    vec3 col = 0.5 + 0.5 * cos(atan(c.y, c.x) + vec3(0.0, 2.1, 4.2));
    // IMPORTANT: Use smoothstep instead of linear division to preserve gradient variation
    float ink = smoothstep(0.0, 2.0, c.w);
    col *= ink;

    // IMPORTANT: Background color must be visible to the eye (RGB at least > 5/255 ≈ 0.02), otherwise users think the page is all black
    col = max(col, vec3(0.02, 0.012, 0.035));

    fragColor = vec4(col, 1.0);
}
```## 变体详细信息

### 变体 1：旋转自平流

**与基础版本的区别**：使用多尺度旋转采样代替压力投影来实现自然的无发散平流。计算更简单，适合纯装饰性流体效果。

**核心思想**：计算不同尺度下的局部旋转（卷曲），然后使用旋转偏移采样位置进行平流。

**关键代码**：```glsl
#define RotNum 3           // adjustable: rotational sample count [3-7], more = more precise
#define angRnd 1.0         // adjustable: rotational randomness [0-1]

const float ang = 2.0 * 3.14159 / float(RotNum);
mat2 m = mat2(cos(ang), sin(ang), -sin(ang), cos(ang));

// Compute rotation amount at a given scale
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

// Main loop: multi-scale advection accumulation
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
    sc *= 2.0;  // next scale
}
fragColor = texture(iChannel0, fract(uv + v * 3.0 / iResolution.x));
```### 变体 2：涡度限制

**与基础版本的区别**：在基础解算器顶部添加涡度限制力，以防止小涡流因数值扩散而消散过快。适合烟雾、火灾等需要丰富细节的场景。

**核心思想**：计算涡量场的梯度方向（涡量集中的方向），然后沿该方向施加恢复力。

**关键代码**：```glsl
#define VORT_STRENGTH 0.01  // adjustable: vorticity confinement strength [0.001 - 0.1]

// Compute gradient of vorticity magnitude (points toward increasing vorticity)
float curl_c = curl_at(uv);                    // current vorticity
float curl_n = abs(curl_at(uv + vec2(0, texel.y)));
float curl_s = abs(curl_at(uv - vec2(0, texel.y)));
float curl_e = abs(curl_at(uv + vec2(texel.x, 0)));
float curl_w = abs(curl_at(uv - vec2(texel.x, 0)));

vec2 eta = normalize(vec2(curl_e - curl_w, curl_n - curl_s) + 1e-5);

// Vorticity confinement force = ε * (η × ω)
vec2 conf = VORT_STRENGTH * vec2(eta.y, -eta.x) * curl_c;
c.xy += DT * conf;
```### 变体 3：粘性指法/反应扩散风格

**与基本版本的区别**：无平流；相反，使用旋转驱动的自放大和拉普拉斯扩散来产生类似于反应扩散的有机图案。适合抽象艺术生成。

**核心思想**：根据旋度计算旋转角度，将二维旋转应用于速度分量，并结合拉普拉斯扩散和发散反馈。

**关键代码**：```glsl
const float cs = 0.25;   // adjustable: curl → rotation angle scaling
const float ls = 0.24;   // adjustable: Laplacian diffusion strength
const float ps = -0.06;  // adjustable: divergence-pressure feedback strength
const float amp = 1.0;   // adjustable: self-amplification coefficient (>1 enhances patterns)
const float pwr = 0.2;   // adjustable: curl exponent (controls rotation sensitivity)

// Compute rotation angle from curl
float sc = cs * sign(curl) * pow(abs(curl), pwr);

// Temporary velocity (with diffusion and divergence feedback)
float ta = amp * uv.x + ls * lapl.x + norm.x * sp + uv.x * sd;
float tb = amp * uv.y + ls * lapl.y + norm.y * sp + uv.y * sd;

// Rotate velocity components
float a = ta * cos(sc) - tb * sin(sc);
float b = ta * sin(sc) + tb * cos(sc);

fragColor = clamp(vec4(a, b, div, 1), -1.0, 1.0);
```### 变体 4：高斯核 SPH 粒子流体

**与基础版本的区别**：完全放弃网格平流，而是使用高斯核函数来估计每个网格点的密度和速度。最少（核心代码约20行），适合快速原型制作和教学。

**核心思想**：对于邻域中的所有像素，使用基于速度+位移的高斯权重执行质量加权速度混合。这本质上是 SPH 的基于网格的近似。

**关键代码**：```glsl
#define RADIUS 7    // adjustable: search radius [3-10], larger = slower but smoother

vec4 r = vec4(0);
for (vec2 i = vec2(-RADIUS); ++i.x < float(RADIUS);)
    for (i.y = -float(RADIUS); ++i.y < float(RADIUS);) {
        vec2 v = texelFetch(iChannel0, ivec2(i + fragCoord), 0).xy;  // neighbor velocity
        float mass = texelFetch(iChannel0, ivec2(i + fragCoord), 0).z; // neighbor mass
        float w = exp(-dot(v + i, v + i)) / 3.14;  // Gaussian kernel weight
        r += mass * w * vec4(mix(v + v + i, v, mass), 1, 1);
    }
r.xy /= r.z + 1e-6;  // mass-weighted average velocity
```### 变体 5：拉格朗日涡旋粒子法

**与基本版本的区别**：不是在网格上求解，而是跟踪离散涡旋粒子及其位置和涡度。使用毕奥-萨伐尔定律直接根据涡度分布计算速度场。适合少量涡流的精确模拟。

**核心思想**：每个粒子都带有位置和涡度。诱导速度通过 N 体求和计算。使用 Heun（半隐式）时间积分来提高准确性。

**关键代码**：```glsl
#define N 20                     // adjustable: N×N particles
#define STRENGTH 1e3 * 0.25      // adjustable: vorticity strength scaling

// Biot-Savart velocity computation (similar to 2D vortex 1/r decay)
vec2 F = vec2(0);
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++) {
        float w = vorticity(i, j);          // particle vorticity
        vec2 d = particle_pos(i, j) - my_pos;
        float l = dot(d, d);
        if (l > 1e-5)
            F += vec2(-d.y, d.x) * w / l;  // Biot-Savart: v = ω × r / |r|²
    }
velocity = STRENGTH * F;
position += velocity * dt;
```## 性能优化详情

### 瓶颈 1：邻域样本计数
- 基本的 5 点模板（十字）速度最快，但各向同性较差
- 3x3 模板（9 个样本）是准确性和性能之间的最佳平衡
- SPH 变体中的“N×N”搜索半径非常昂贵；任何高于 7 的值都会变慢
- **优化**：使用`texelFetch`代替`texture`（跳过过滤），或者使用`textureLod`锁定mip级别

### 瓶颈 2：多通道开销
- 经典求解器需要 2-4 个缓冲通道（速度、压力、涡度、可视化）
- **优化**：将多个步骤合并到一个通道中。压力投影可以利用帧间反馈作为隐式雅可比迭代，从而无需专用迭代遍
- 对于不需要严格不可压缩性的装饰效果，旋转自平流（变体1）可以完全消除压力投射

### 瓶颈 3：平流精度与性能
- 单步平流在高速区域丢失细节
- **优化**：多步平流（`ADVECTION_STEPS = 3`）使用 3 个小步而不是 1 个大步，代价是 3 倍采样
- 妥协：预先计算偏移量，然后统一细分采样（避免在每一步重新计算偏移量）

### 瓶颈 4：Mipmap 作为多尺度遍历的替代方案
- 多尺度流体需要不同空间尺度的计算。蛮力方法是多个大半径样本
- **优化**：利用 GPU 生成的 mipmap 进行 O(1) 多尺度读取，使用 `textureLod(channel, uv, mip)` 直接在不同尺度下读取

### 一般提示
- 在初始帧上添加微小噪声（`1e-6 * 噪声`）以避免数值精度问题导致的对称锁定
- 使用 `fract(uv + offset)` 作为周期性边界（圆环拓扑），消除边界检查分支
- 将压力场乘以接近 1 的衰减因子（例如“0.9999”）以防止压力漂移

## 组合建议

### 1.流体+法线贴图照明
将流体速度/密度场视为高度图，计算法线，并应用 Phong/GGX 照明来产生液态金属视觉效果。```glsl
// Compute normals from the density field
vec2 dxy = vec2(
    texture(buf, uv + vec2(tx, 0)).z - texture(buf, uv - vec2(tx, 0)).z,
    texture(buf, uv + vec2(0, ty)).z - texture(buf, uv - vec2(0, ty)).z
);
vec3 normal = normalize(vec3(-BUMP * dxy, 1.0));
// Then plug into Phong/GGX lighting calculation
```### 2. 流体+粒子追踪
在流体速度场中分散被动粒子，根据流速更新每帧的粒子位置。适合可视化流线和创建墨水扩散效果。```glsl
// Particle position update (in a separate buffer)
vec2 pos = texture(particleBuf, id).xy;
vec2 vel = texture(fluidBuf, pos / iResolution.xy).xy;
pos += vel * dt;
pos = mod(pos, iResolution.xy);  // periodic boundary
```### 3. Fluid + Color Advection
将 RGB 颜色存储在额外的通道或缓冲区中，并与速度场同步执行半拉格朗日平流，产生彩色墨水混合效果。

### 4.流畅+音频响应
将音频频谱低频能量映射到强制强度，将高频能量映射到涡量注入，从而创建音乐驱动的流体可视化。```glsl
float bass = texture(iChannel1, vec2(0.05, 0.0)).x;   // low frequency
float treble = texture(iChannel1, vec2(0.8, 0.0)).x;   // high frequency
// Low frequency → thrust, high frequency → vortex disturbance
c.xy += bass * radialForce + treble * randomVortex;
```### 5.流体+3D体积渲染
将 2D 流体扩展到 3D（使用 2D 纹理切片打包来存储 3D 体素）并通过光线行进渲染半透明体积。适合云朵和爆炸效果。