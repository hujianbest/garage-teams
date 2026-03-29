# 多通道缓冲技术 — 详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，涵盖了前提条件、每个步骤的深入解释、完整的变体描述、性能优化分析以及完整的组合代码示例。

## 先决条件

### GLSL 基础知识

- GLSL基本语法：`uniform`、`variing`、`sampler2D`
- ShaderToy 执行模型：`iChannel0-3` 纹理输入、`iResolution`、`iTime`、`iFrame`、`iMouse`
- `texture()` 和 `texelFetch()` 之间的区别：
  - `texture()` 执行插值采样（双线性过滤），适合连续场采样
  - `texelFetch()` 精确读取特定的纹素，无需插值，适合数据存储读取
- `textureLod()`用于显式MIP级别采样，避免自动MIP选择造成的模糊
- ShaderToy中的缓冲区A/B/C/D概念：每个缓冲区都是一个独立的渲染通道，输出到相应的纹理，该纹理可以被其他通道读取或通过iChannel本身读取

### 基础数学

- 基本向量数学和矩阵变换
- 有限差分法：使用邻近像素来近似梯度和拉普拉斯算子
- 迭代映射：‘x(n+1) = f(x(n))’的概念，自反馈的数学基础

## 实施步骤

### 第 1 步：建立最小的自我反馈循环

**什么**：创建一个 Buffer，读取它自己的前一帧输出，添加新内容，并输出结果。 Image pass 只是显示 Buffer 结果。

**为什么**：这是所有多遍技术的基石。一旦你理解了自反馈回路，流体模拟、时间累积等都是这个基础的延伸。初始化保护（“iFrame == 0”或“iFrame < N”）可防止读取未初始化的数据。

**iChannel Binding**：Buffer A的iChannel0 → Buffer A（自反馈）；图像的 iChannel0 → 缓冲区 A

**要点**：
- `exp(-33.0 / iResolution.y)` 控制衰减率；值越高，衰减越快
- `fragCoord + vec2(1.0, sin(iTime))` 偏移创建运动效果
- `iFrame < 4` 保护确保前几帧的稳定初始值

### 步骤 2：实施自我平流

**内容**：基于自反馈，将缓冲区值解释为速度场并实现自平流 - 每个像素根据局部速度偏移其采样位置。

**为什么**：自平流是所有欧拉网格流体模拟的核心。通过旋转采样累积多个尺度的旋转信息，无需完整的纳维-斯托克斯求解器即可产生丰富的涡流结构。

**参数调整**：
- `ROT_NUM`（旋转样本计数）：影响旋转场的采样精度； 5是一个很好的平衡
- `SCALE_NUM`（尺度级别数）：影响漩涡的细节级别； 20 个级别产生丰富的多尺度结构
- `bbMax = 0.7 * iResolution.y`：自适应循环终止阈值

**数学原理**：
- `getRot` 函数对给定位置周围 ROT_NUM 等距角度方向的速度场进行采样
- 通过“点（速度 - 0.5，垂直）”计算旋转分量
- 多尺度循环`b *= 2.0`逐步扩大采样半径，捕获不同尺度的涡流

### 步骤 3：纳维-斯托克斯流体求解器

**内容**：基于论文“简单且快速的流体”（Guay、Colin、Egli，2011）实现速度场求解，包括平流、粘性力和涡度限制。

**原因**：比纯粹的旋转自平流在物理上更准确，支持低粘度流体模拟（例如烟雾、火焰）。涡量存储在 Alpha 通道中以避免额外的缓冲区开销。

**完整的 `solveFluid` 功能分解**：```glsl
vec4 solveFluid(sampler2D smp, vec2 uv, vec2 w, float time, vec3 mouse, vec3 lastMouse) {
    const float K = 0.2;   // Pressure coefficient: controls the strength of the incompressibility constraint
    const float v = 0.55;  // Viscosity coefficient: high value = viscous fluid, low value = thin fluid

    // Read four neighboring pixels (basis for central differencing)
    vec4 data = textureLod(smp, uv, 0.0);
    vec4 tr = textureLod(smp, uv + vec2(w.x, 0), 0.0);
    vec4 tl = textureLod(smp, uv - vec2(w.x, 0), 0.0);
    vec4 tu = textureLod(smp, uv + vec2(0, w.y), 0.0);
    vec4 td = textureLod(smp, uv - vec2(0, w.y), 0.0);

    // Density and velocity gradients (central differencing)
    vec3 dx = (tr.xyz - tl.xyz) * 0.5;  // x-direction gradient
    vec3 dy = (tu.xyz - td.xyz) * 0.5;  // y-direction gradient
    vec2 densDif = vec2(dx.z, dy.z);     // Density gradient

    // Density update: continuity equation ∂ρ/∂t + ∇·(ρv) = 0
    data.z -= DT * dot(vec3(densDif, dx.x + dy.y), data.xyz);

    // Viscous force (Laplacian operator): μ∇²v
    // Discrete Laplacian = up + down + left + right - 4*center
    vec2 laplacian = tu.xy + td.xy + tr.xy + tl.xy - 4.0 * data.xy;
    vec2 viscForce = vec2(v) * laplacian;

    // Advection: Semi-Lagrangian backtrace method
    // Trace backward from the current position along the reverse velocity direction, sample previous step's value
    data.xyw = textureLod(smp, uv - DT * data.xy * w, 0.0).xyw;

    // External forces (mouse interaction)
    vec2 newForce = vec2(0);
    if (mouse.z > 1.0 && lastMouse.z > 1.0) {
        // Mouse movement velocity as force direction
        vec2 vv = clamp((mouse.xy * w - lastMouse.xy * w) * 400.0, -6.0, 6.0);
        // Force magnitude inversely proportional to distance from mouse (similar to a point charge field)
        newForce += 0.001 / (dot(uv - mouse.xy * w, uv - mouse.xy * w) + 0.001) * vv;
    }

    // Velocity update: v += dt * (viscous force - pressure gradient + external forces)
    data.xy += DT * (viscForce - K / DT * densDif + newForce);
    // Linear decay: simulates energy dissipation
    data.xy = max(vec2(0), abs(data.xy) - 1e-4) * sign(data.xy);

    // Vorticity Confinement
    // Compute curl = ∂vy/∂x - ∂vx/∂y
    data.w = (tr.y - tl.y - tu.x + td.x);
    // Vorticity gradient direction
    vec2 vort = vec2(abs(tu.w) - abs(td.w), abs(tl.w) - abs(tr.w));
    // Normalize then multiply by vorticity value to produce a force that enhances vortices
    vort *= VORTICITY_AMOUNT / length(vort + 1e-9) * data.w;
    data.xy += vort;

    // Top/bottom boundaries: soft decay to avoid hard edges
    data.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    // Numerical stability: clamp extreme values
    data = clamp(data, vec4(vec2(-10), 0.5, -10.0), vec4(vec2(10), 3.0, 10.0));

    return data;
}
```**RGBA通道封装策略**：
- `xy` = 速度分量 (vx, vy)
- `z` = 密度
- `w` = 涡度（旋度）

单个 vec4 无需额外的缓冲区即可承载完整的流体状态。

### 步骤 4：用于加速模拟的链接缓冲区

**什么**：通过Buffer A → B → C 链式执行相同的模拟代码，每帧完成多个模拟子步骤。

**为什么**：每个 ShaderToy 缓冲区每帧仅执行一次。通过链接相同的代码（A 读取自身 → B 读取 A → C 读取 B），可在单个帧中完成 3 次迭代，从而在不增加缓冲区数量的情况下显着提高模拟速度。使用 Common 选项卡可以避免代码重复。

**iChannel 绑定**：
- 缓冲区 A：iChannel0 → 缓冲区 C（读取上一帧的最终结果）
- Buffer B：iChannel0 → Buffer A（读取当前帧的第一步结果）
- 缓冲区C：iChannel0→缓冲区B（读取当前帧的第二步结果）

**鼠标状态帧间传输**：
- `if (fragCoord.y < 1.0) data = iMouse;` 将当前帧的鼠标状态写入第一行像素
- `texelFetch(iChannel0, ivec2(0, 0), 0)` 在下一帧中读取上一帧的鼠标状态
- 两帧鼠标位置之间的增量给出了鼠标速度，用于计算所施加力的方向和大小

### 步骤 5：可分离高斯模糊管道

**什么**：使用两个Buffer来实现水平和垂直可分离的高斯模糊。

**为什么**：2D 高斯核可以分解为两个 1D 核的乘积。 NxN 内核从 N² 样本减少到 2N。这是 Bloom、反应扩散中的扩散项以及各种后处理模糊的标准实现。

**iChannel 绑定**：缓冲区 B：iChannel0 → 缓冲区 A（源）；缓冲区C：iChannel0→缓冲区B（水平模糊结果）

**垂直模糊完整代码**（SKILL.md中的水平版本；垂直版本对称替换y轴）：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 pixelSize = 1.0 / iResolution.xy;
    vec2 uv = fragCoord * pixelSize;

    float v = pixelSize.y;
    vec4 sum = vec4(0.0);
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 4.0*v))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 3.0*v))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 2.0*v))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y - 1.0*v))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y         ))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 1.0*v))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 2.0*v))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 3.0*v))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x, uv.y + 4.0*v))) * 0.05;

    fragColor = vec4(sum.xyz / 0.98, 1.0);
}
```**9键重量说明**：
- 权重 [0.05, 0.09, 0.12, 0.15, 0.16, 0.15, 0.12, 0.09, 0.05] 近似于 sigma≈2.0 的高斯分布
- 总和为 0.98，除以 0.98 进行归一化
- `fract()` 实现换行寻址

### 步骤 6：结构化状态存储（Texel 寻址寄存器）

**什么**：使用缓冲区中的特定像素作为命名寄存器来存储非图像数据（位置、速度、分数等）。

**为什么**：GPU 没有全局变量。通过将语义分配给特定的纹素位置，可以将任意结构化状态保留在缓冲区中。这使得完整的游戏逻辑、粒子系统状态等能够在着色器中实现。

**设计模式详细信息**：

1. **地址常量**：使用`const ivec2`定义每个状态变量的texel地址
2. **加载函数**：`texelFetch(iChannel0, addr, 0)`用于精确读取（无插值）
3. **存储函数**：使用条件赋值 `fragColor = (px == addr) ? val : fragColor`，确保每个像素只写入属于自己地址的数据
4. **区域存储**：`ivec4 rect`定义网格状数据的矩形区域（例如，砖矩阵）
5. **丢弃数据区域之外**：`if (fragCoord.x > 14.0 || fragCoord.y > 14.0) Discard;` 跳过不必要的计算

**注释**：
- `ivec2(fragCoord - 0.5)` 确保正确的整数纹理像素坐标（fragCoord 的中心偏移）
- 当`iFrame == 0`时初始化必须设置所有状态值
- 默认行为 `fragColor = loadValue(px)` 保持未修改状态不变

### 步骤 7：帧间鼠标状态跟踪

**什么**：将鼠标位置存储在缓冲区的特定像素中，并通过读取前一帧的值来计算鼠标移动增量。

**为什么**：ShaderToy 不直接提供鼠标速度。将当前帧的“iMouse”存储在固定像素中可以计算下一帧的增量。这对于流体相互作用至关重要——需要鼠标速度来施加力。

**两种方法的比较**：

|特色|方法 1（第一行像素）|方法 2（固定 UV 区域）|
|--------|----------------------------------------|----------------------------|
|来源 |奇美拉之息|反应扩散|
|储存地点 | `fragCoord.y < 1.0` |固定 UV 坐标 |
|阅读方法| `texelFetch(ch, ivec2(0,0), 0)` | `纹理（ch，vec2（7.5/8，2.5/8））` |
|优势 |简单，适用于流体 |与分辨率无关 |
|缺点|占据第一行像素|需要额外的缓冲通道|

## 变体详细信息

### 变体 1：时间累积抗锯齿 (TAA)

**与基础版本的区别**：Buffer不进行物理模拟，而是渲染一个抖动的图像，并将其与历史帧混合以实现超采样。使用 YCoCg 色彩空间邻域钳位来防止重影。

**它是如何工作的**：
1. Buffer A渲染具有亚像素级随机抖动的场景
2. 新帧与历史帧以 10:90 的比例混合，随着时间的推移累积超级采样
3. TAA缓冲区执行YCoCg邻域钳位：将历史帧颜色约束到当前帧的3x3邻域的统计范围
4. 0.75 sigma 钳位范围平衡重影去除和细节保留

**完整的 TAA 流程**：```
Buffer A (render+jitter) → Buffer B (motion vectors, optional) → Buffer C (TAA blend) → Image
```### 变体 2：延迟渲染 G 缓冲区管道

**与基本版本的区别**：缓冲区不使用自反馈，而是在单个帧内分阶段处理：几何→边缘检测→后处理。

**G-Buffer 编码方案**：
- `col.xy`：视图空间法线 xy 分量（乘以 camMat 以转换为屏幕空间）
- `col.z`：线性深度（标准化为 [0,1]）
- `col.w`：漫反射照明+阴影信息

**边缘检测原理**：
- `checkSame` 函数比较相邻像素之间的法线差异和深度差异
- `Sensitivity.x` 控制正常边缘灵敏度
- `Sensitivity.y` 控制深度边缘灵敏度
- 阈值0.1决定边缘检测标准

### 变体 3：HDR Bloom 后处理管道

**与基础版的区别**：使用Buffers构建MIP金字塔，通过多级下采样和模糊实现大范围发光。

**MIP 金字塔打包策略**：
- 所有 MIP 级别都打包到单个纹理中
- `CalcOffset` 计算纹理内每个级别的偏移位置
- 每层尺寸为一半，有填充物以防止层间泄漏

**完整的 Bloom 管道**：```
Buffer A (scene render) → Buffer B (MIP pyramid) → Buffer C (horizontal blur) → Buffer D (vertical blur) → Image (compositing)
```**色调映射**：```glsl
// Reinhard tone mapping
color = pow(color, vec3(1.5));  // Gamma preprocessing
color = color / (1.0 + color);  // Reinhard compression
```### 变体 4：反应扩散系统

**与基本版本的区别**：模拟化学反应扩散（例如，Gray-Scott 模型）。扩散是通过可分离模糊实现的，反应项是在主缓冲区中计算的。

**格雷-斯科特方程**：
- `∂u/∂t = Du∇²u - uv² + F(1-u)` — 化学物质 u 的扩散和反应
- `∂v/∂t = Dv∇²v + uv² - (F+k)v` — 化学物质 v 的扩散和反应
- `Du`、`Dv` 是扩散系数，`F` 是进料速率，`k` 是杀灭率

**实施策略**：
- 扩散项通过可分离的模糊缓冲区实现（重用步骤 5 中的模糊管道）
- 反应项在主缓冲区中计算
- `uv_red`的偏移量实现扩散扩展
- 随机噪声衰减可防止模式停滞

### 变体 5：多尺度 MIP 流体

**与基础版本的区别**：使用`textureLod`显式采样不同的MIP级别，实现O(n)复杂度的多尺度计算（湍流、涡度限制、泊松求解），每个物理量都在自己的缓冲区中。

**核心优势**：
- 传统的多尺度计算需要 O(N²) 个样本（在每个尺度上采样 N 个邻居）
- MIP 采样利用硬件自动平均；高 MIP 级别的单个“textureLod”相当于大范围平均值
- 总复杂度降至 O(NUM_SCALES × 9)（每个尺度 3x3 邻域）

**权重函数选择**：
- `1.0/float(i+1)`：对数衰减，减少大规模影响
- `1.0/float(1<<i)`：指数衰减，快速抑制大尺度
- 恒定：所有秤的重量相同

## 深入的性能优化

### 1. 减少纹理样本

**可分离模糊**：
- 原理：2D高斯函数G(x,y) = G(x) × G(y)可以分成两个1D卷积
- NxN 内核从 N² 下降到 2N 样本
- 9-tap 示例：81 → 18 个样本

**双线性点击技巧**：```glsl
// Standard 9-tap: requires 9 samples
// Bilinear optimization: achieves equivalent results with 5 samples using hardware interpolation
// Key: place sample points between two texels, GPU hardware automatically computes weighted average
float offset1 = 1.0 + weight2 / (weight1 + weight2);  // Offset encodes weight ratio
vec4 s1 = texture(smp, uv + vec2(offset1, 0) * texelSize);
// s1 is automatically the weighted average of texel[1] and texel[2]
```**MIP 采样取代大内核**：
- `textureLod(smp, uv, 3.0)` 采样 MIP 级别 3，相当于 8×8 区域平均值
- 单个样本替代 64 个样本
- 适用于多尺度计算中的粗尺度近似

### 2.限制计算区域

**数据区域丢弃**：```glsl
// In a state storage shader, only the first 14×14 pixels store data
// Remaining pixels are discarded, GPU skips subsequent computation
if (fragCoord.x > 14.0 || fragCoord.y > 14.0) discard;
```**软边界**：```glsl
// Use smoothstep instead of if-statements
// Avoids branch divergence (warp divergence), more efficient on GPU
data.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
// Smoothly decays to 0 in the y=0.48~0.52 range
```### 3. 减少缓冲区数量

**RGBA 通道封装**：
|频道|流体模拟| G 缓冲器 |粒子系统|
|------|------------------|----------|----------------|
|右 |速度 x |正常 x |位置 x |
| G |速度 y |正常 y |位置 y |
|乙|密度|深度 |终身|
|一个 |涡度 |漫射|类型 ID |

**链接子步骤**：
- 3 个缓冲区运行相同的代码 = 每帧 3 次迭代
- 相当于3x时间步长，但更稳定（每一步仍然是一小步）
- 代码通过公共选项卡共享，零维护成本

### 4. 减少迭代/样本数量

**自适应循环终止**：```glsl
// In multi-scale sampling, exit early when the sampling radius exceeds the effective range
float bbMax = 0.7 * iResolution.y;
bbMax *= bbMax;
for (int l = 0; l < SCALE_NUM; l++) {
    if (dot(b, b) > bbMax) break;  // Beyond screen range, no need to continue
    // ...
    b *= 2.0;
}
```**MIP 级别计数调整**：
- `TURBULENCE_SCALES = 11`：完全多尺度，最高质量
- `TURBULENCE_SCALES = 7`：删除最大的尺度，最小的质量损失
- `TURBULENCE_SCALES = 5`：显着加速，适合移动设备

### 5.初始化策略

**渐进式初始化**：```glsl
// Output stable initial values for the first 20 frames
if (iFrame < 20) data = vec4(0.5, 0, 0, 0);
```- 为什么不是`iFrame == 0`？因为某些缓冲区依赖于其他缓冲区的输出
- 20帧确保所有缓冲区完成初始化传播

**微小噪音初始化**：```glsl
if (iFrame == 0) fragColor = 1e-6 * noise;
```- 避免精确的零值导致“0/0”或“标准化(vec2(0))”问题
- 微小的噪音打破对称性，让漩涡自然发展

## 组合示例及完整代码

### 1.流体模拟+灯光```glsl
// Image: Compute gradient from fluid buffer as normal, apply Phong lighting
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float delta = 1.0 / iResolution.y;

    // Compute fluid surface gradient
    float valC = getVal(uv);
    vec2 grad = vec2(
        getVal(uv + vec2(delta, 0)) - getVal(uv - vec2(delta, 0)),
        getVal(uv + vec2(0, delta)) - getVal(uv - vec2(0, delta))
    ) / delta;

    // Build normal (z=150 controls surface flatness)
    vec3 normal = normalize(vec3(grad, 150.0));

    // Lighting
    vec3 lightDir = normalize(vec3(-1.0, -1.0, 2.0));
    vec3 viewDir = vec3(0, 0, 1);

    float diff = clamp(dot(normal, lightDir), 0.5, 1.0);
    float spec = pow(clamp(dot(reflect(lightDir, normal), viewDir), 0.0, 1.0), 36.0);

    vec3 baseColor = vec3(0.2, 0.4, 0.8);  // Water surface color
    fragColor = vec4(baseColor * diff + vec3(1.0) * spec * 0.5, 1.0);
}
```### 2.流体模拟+颜色平流```glsl
// Color Buffer: Track a color field, advected by the velocity field
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 w = 1.0 / iResolution.xy;
    float dt = 0.15;
    float scale = 3.0;

    // Read velocity field
    vec2 velocity = textureLod(iChannel0, uv, 0.0).xy;

    // Color advection: sample own previous frame in the reverse velocity direction
    vec4 col = textureLod(iChannel1, uv - dt * velocity * w * scale, 0.0);

    // Inject color at the emission point
    vec2 emitPos = vec2(0.5, 0.5);
    float dist = length(uv - emitPos);
    float emitterStrength = 0.0025;
    float epsilon = 0.0005;
    col += emitterStrength / (epsilon + pow(dist, 1.75)) * dt * 0.12 * palette(iTime * 0.05);

    // Color decay
    float decay = 0.004;
    col = max(col - (0.0001 + col * decay) * 0.5, 0.0);
    col = clamp(col, 0.0, 5.0);

    fragColor = col;
}
```### 3.场景渲染+Bloom+TAA后处理链

四缓冲区管道：
- **缓冲区 A**：场景渲染（带有 TAA 的子像素抖动）
- **Buffer B**：亮度提取+下采样构建布隆金字塔
- **缓冲区 C/D**：可分离高斯模糊
- **图像**：Bloom合成+色调映射+色差+晕影```glsl
// Image: Final compositing
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // Original scene
    vec3 scene = texture(iChannel0, uv).rgb;

    // Multi-level bloom compositing
    vec3 bloom = vec3(0);
    bloom += Grab(uv, 1.0, CalcOffset(0.0)).rgb * 1.0;
    bloom += Grab(uv, 2.0, CalcOffset(1.0)).rgb * 1.5;
    bloom += Grab(uv, 4.0, CalcOffset(2.0)).rgb * 2.0;
    bloom += Grab(uv, 8.0, CalcOffset(3.0)).rgb * 3.0;

    // Compositing
    vec3 color = scene + bloom * 0.08;

    // Filmic tone mapping
    color = pow(color, vec3(1.5));
    color = color / (1.0 + color);

    // Chromatic Aberration
    float ca = 0.002;
    color.r = texture(iChannel0, uv + vec2(ca, 0)).r;
    color.b = texture(iChannel0, uv - vec2(ca, 0)).b;

    // Vignette
    float vignette = 1.0 - dot(uv - 0.5, uv - 0.5) * 0.5;
    color *= vignette;

    fragColor = vec4(color, 1.0);
}
```### 4. G 缓冲区 + 屏幕空间效果

双缓冲区管道，无时间反馈：
- **缓冲区 A**：输出法线 + 深度 + 漫反射到 G 缓冲区
- **缓冲区 B**：屏幕空间边缘检测/SSAO/SSR
- **图像**：风格化合成（例如手绘风格、噪声失真）```glsl
// Buffer B: Screen-space edge detection
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 offset = 1.0 / iResolution.xy;

    vec4 center = texture(iChannel0, uv);

    // Roberts Cross edge detection
    vec4 tl = texture(iChannel0, uv + vec2(-offset.x, offset.y));
    vec4 tr = texture(iChannel0, uv + vec2(offset.x, offset.y));
    vec4 bl = texture(iChannel0, uv + vec2(-offset.x, -offset.y));
    vec4 br = texture(iChannel0, uv + vec2(offset.x, -offset.y));

    float edge = checkSame(center, tl) * checkSame(center, tr) *
                 checkSame(center, bl) * checkSame(center, br);

    fragColor = vec4(edge, center.w, center.z, 1.0);
}
```### 5.状态存储+可视化分离

游戏/粒子系统的标准模式。逻辑和渲染完全分离：
- **Buffer A**：纯逻辑计算，状态存储在固定的纹素位置
- **图像**：纯渲染，通过“texelFetch”读取状态，使用距离场/光栅化绘制视觉效果```glsl
// Image: Read game state from Buffer A and render
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec2 aspect = vec2(iResolution.x / iResolution.y, 1.0);

    // Read ball state
    vec4 ballPV = texelFetch(iChannel0, ivec2(0, 0), 0);
    vec2 ballPos = ballPV.xy;

    // Read paddle position
    float paddleX = texelFetch(iChannel0, ivec2(1, 0), 0).x;

    // Draw ball (distance field)
    float ballDist = length((uv - ballPos * 0.5 - 0.5) * aspect);
    vec3 ballColor = vec3(1.0, 0.8, 0.2) * smoothstep(0.02, 0.015, ballDist);

    // Draw paddle
    vec2 paddleCenter = vec2(paddleX * 0.5 + 0.5, 0.05);
    vec2 paddleSize = vec2(0.08, 0.01);
    vec2 d = abs((uv - paddleCenter) * aspect) - paddleSize;
    float paddleDist = length(max(d, 0.0));
    vec3 paddleColor = vec3(0.2, 0.6, 1.0) * smoothstep(0.005, 0.0, paddleDist);

    // Read and draw brick grid
    vec3 brickColor = vec3(0);
    for (int y = 1; y <= 12; y++) {
        for (int x = 0; x <= 13; x++) {
            float alive = texelFetch(iChannel0, ivec2(x, y), 0).x;
            if (alive > 0.5) {
                vec2 brickCenter = vec2(float(x) / 14.0 + 0.036, float(y) / 14.0 + 0.036);
                vec2 bd = abs((uv - brickCenter) * aspect) - vec2(0.03, 0.015);
                float brickDist = length(max(bd, 0.0));
                brickColor += vec3(0.8, 0.3, 0.5) * smoothstep(0.003, 0.0, brickDist);
            }
        }
    }

    fragColor = vec4(ballColor + paddleColor + brickColor, 1.0);
}
```
