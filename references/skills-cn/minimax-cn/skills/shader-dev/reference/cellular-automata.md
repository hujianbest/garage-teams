# 元胞自动机和反应扩散 — 详细参考

本文档是对 [SKILL.md](SKILL.md) 的详细补充，包含先决条件、分步说明、变体详细信息、性能分析以及组合建议的完整代码示例。

---

## 先决条件

### GLSL 基础知识
- **统一变量**：`iResolution`（视口分辨率）、`iFrame`（当前帧编号）、`iTime`（经过的时间）、`iMouse`（鼠标位置）
- **纹理采样**：使用 UV 坐标（带过滤）的“texture(iChannel0, uv)”样本，在精确整数像素坐标处的“texelFetch(iChannel0, ivec2(px), 0)”样本
- **多缓冲区反馈架构**：ShaderToy支持Buffer A~D，每个缓冲区可以绑定自身或其他缓冲区作为iChannel输入

### ShaderToy 多通道机制
Buffer A写入的数据→下一帧Buffer A通过iChannel0自反馈读取。这是帧间状态持久化的核心机制。图像通道处理最终的视觉输出。

### 2D 网格采样
- 像素坐标“fragCoord”是浮点型，范围“[0.5，分辨率 - 0.5]”
- UV 坐标 = `fragCoord / iResolution.xy`，范围 `[0, 1]`
- `texelFetch(iChannel0, ivec2(px), 0)` 精确读取指定像素（无过滤），适用于离散 CA
-`texture(iChannel0, uv)`使用硬件双线性插值，适合连续RD

### 基本向量数学
- `normalize(v)`：标准化向量
- `dot(a, b)`：点积
- `cross(a, b)`：叉积
- `length(v)`: 向量长度

### 卷积核概念
3x3 模板对中心像素及其 8 个相邻像素进行加权求和。不同的重量会产生不同的效果：
- **拉普拉斯核**：检测当前值与邻域平均值的偏差（扩散）
- **高斯内核**：模糊/平滑
- **Sobel 内核**：边缘检测/梯度计算

---

## 详细实施步骤

### 第 1 步：电网状态存储和自反馈

**什么**：使用ShaderToy的Buffer自读机制将模拟状态持久存储在缓冲区纹理中。每个帧读取前一帧的状态，计算新状态，然后将其写回。

**为什么**：GPU 着色器本质上是无状态的；时间步迭代需要缓冲帧间反馈。状态存储在 RGBA 通道中 — CA 可以使用单个通道表示活动/死亡，而 RD 分别使用两个通道表示 u 和 v。

**代码**：```glsl
// Buffer A: read previous frame's own state
// iChannel0 is bound to Buffer A itself (self-feedback)
vec4 prevState = texelFetch(iChannel0, ivec2(fragCoord), 0);

// Can also sample with UV coordinates (supports texture filtering)
vec2 uv = fragCoord / iResolution.xy;
vec4 prevSmooth = texture(iChannel0, uv);
```**要点**：
- `texelFetch` 不执行任何过滤，精确读取单个像素，适合离散 CA
-`texture`使用硬件双线性插值，混合像素边界附近的相邻像素值，适合连续RD
- 四个RGBA通道可以存储不同的状态变量（例如，u、v、速度场分量等）

### 步骤 2：初始化（噪声播种）

**什么**：在第一帧（或前几帧）上使用伪随机噪声初始化网格，为模拟提供种子。

**为什么**：CA 和 RD 都需要初始扰动才能开始进化。不同的初始条件产生不同的最终模式。在实践中，由于 ShaderToy 偶尔会跳过第一帧，因此通常会在前 2~10 帧中重复播种。

**代码**：```glsl
// Simple hash noise function
float hash1(float n) {
    return fract(sin(n) * 138.5453123);
}

vec3 hash33(in vec2 p) {
    float n = sin(dot(p, vec2(41, 289)));
    return fract(vec3(2097152, 262144, 32768) * n);
}

// Initialization branch in mainImage
if (iFrame < 2) {
    // CA: random binary initialization
    float f = step(0.9, hash1(fragCoord.x * 13.0 + hash1(fragCoord.y * 71.1)));
    fragColor = vec4(f, 0.0, 0.0, 0.0);
} else if (iFrame < 10) {
    // RD: random continuous value initialization
    vec3 noise = hash33(fragCoord / iResolution.xy + vec2(53, 43) * float(iFrame));
    fragColor = vec4(noise, 1.0);
}
```**要点**：
- `hash1` 是一个基于 `sin` 的简单伪随机数生成器，生成 [0, 1) 中的值
- `hash33` 从 2D 坐标生成 3D 随机向量，用于多通道 RD 初始化
- CA 初始化使用“step(0.9, ...)”来产生大约 10% 的活细胞密度
- RD 初始化使用连续随机值，并添加“iFrame”，因此每个帧的种子都不同
- 多帧播种（`iFrame < 10`）确保足够丰富的初始扰动

### 步骤 3：邻域采样和拉普拉斯计算

**内容**：对当前像素的 8 个（或 4 个）邻居执行加权采样，计算拉普拉斯或邻居计数。

**为什么**：这是CA/RD的核心——本地规则通过邻居信息驱动状态更新。拉普拉斯算子描述了一个点的值与周围平均值的偏差程度，物理上对应于扩散。九点模板比简单的十字模板更精确且各向同性。

**三种采样方法比较**：

|方法|使用案例|优势 |缺点 |
|------|----------|------|------|
|方法 A：离散邻居计数 |加州 |精确的整数坐标，无过滤误差 |只能处理离散状态|
|方法 B：九点拉普拉斯 |研发|各向同性好，精度高 | 9 个纹理样本 |
|方法 C：3x3 高斯模糊 |简化研发|平滑效果好|不是真正的拉普拉斯|

**方法 A 代码详细信息**：```glsl
// Discrete CA neighbor counting using texelFetch for exact reads
int cell(in ivec2 p) {
    ivec2 r = ivec2(textureSize(iChannel0, 0));
    p = (p + r) % r;  // Wrap-around boundary (toroidal topology), left overflow appears on right
    return (texelFetch(iChannel0, p, 0).x > 0.5) ? 1 : 0;
}

ivec2 px = ivec2(fragCoord);
// Moore neighborhood: sum of 8 neighbors
int k = cell(px + ivec2(-1,-1)) + cell(px + ivec2(0,-1)) + cell(px + ivec2(1,-1))
      + cell(px + ivec2(-1, 0))                          + cell(px + ivec2(1, 0))
      + cell(px + ivec2(-1, 1)) + cell(px + ivec2(0, 1)) + cell(px + ivec2(1, 1));
```**方法 B 代码详细信息**：```glsl
// Nine-point Laplacian stencil (for RD)
// Weights: diagonal 0.5, cross 1.0, center -6.0 (sum = 0, ensuring Laplacian of a constant field is zero)
vec2 laplacian(vec2 uv) {
    vec2 px = 1.0 / iResolution.xy;
    vec4 P = vec4(px, 0.0, -px.x);
    return
        0.5 * texture(iChannel0, uv - P.xy).xy   // bottom-left
      +       texture(iChannel0, uv - P.zy).xy   // bottom
      + 0.5 * texture(iChannel0, uv - P.wy).xy   // bottom-right
      +       texture(iChannel0, uv - P.xz).xy   // left
      - 6.0 * texture(iChannel0, uv).xy           // center
      +       texture(iChannel0, uv + P.xz).xy   // right
      + 0.5 * texture(iChannel0, uv + P.wy).xy   // top-left
      +       texture(iChannel0, uv + P.zy).xy   // top
      + 0.5 * texture(iChannel0, uv + P.xy).xy;  // top-right
}
```**方法 C 代码详细信息**：```glsl
// 3x3 weighted blur (Gaussian approximation)
// Weights: diagonal 1, cross 2, center 4, total 16
// Uses vec3 swizzle to cleverly encode 9 offset directions
float blur3x3(vec2 uv) {
    vec3 e = vec3(1, 0, -1);  // e.x=1, e.y=0, e.z=-1
    vec2 px = 1.0 / iResolution.xy;
    float res = 0.0;
    // e.xx=(1,1), e.xz=(1,-1), e.zx=(-1,1), e.zz=(-1,-1) → four diagonals
    res += texture(iChannel0, uv + e.xx * px).x + texture(iChannel0, uv + e.xz * px).x
         + texture(iChannel0, uv + e.zx * px).x + texture(iChannel0, uv + e.zz * px).x;       // ×1
    // e.xy=(1,0), e.yx=(0,1), e.yz=(0,-1), e.zy=(-1,0) → four edges
    res += (texture(iChannel0, uv + e.xy * px).x + texture(iChannel0, uv + e.yx * px).x
          + texture(iChannel0, uv + e.yz * px).x + texture(iChannel0, uv + e.zy * px).x) * 2.; // ×2
    // e.yy=(0,0) → center
    res += texture(iChannel0, uv + e.yy * px).x * 4.;                                          // ×4
    return res / 16.0;
}
```### 步骤 4：状态更新规则

**什么**：根据邻居信息应用 CA 规则或 RD 微分方程来计算新的状态值。

**为什么**：这是核心模拟逻辑。 CA 使用离散决策（出生/生存/死亡），RD 使用带有欧拉积分的连续微分方程。

**CA 规则详细信息**：

康威的生命游戏 B3/S23 的意思是：
- B3 = 3 个邻居时出生
- S23 = 当有 2 或 3 个邻居时生存```glsl
int e = cell(px);  // current state (0 or 1)
// Equivalent to: if (k==3) born/survive; else if (k==2 && alive) survive; else die
float f = (((k == 2) && (e == 1)) || (k == 3)) ? 1.0 : 0.0;
```**通用位掩码规则**：位掩码可以对任意 CA 规则集进行编码，而无需修改逻辑代码。例如：
- B3/S23→bornset=8（二进制1000，位3），stayset=12（二进制1100，位2,3）
- B36/S23→bornset=40（位3,5），stayset=12```glsl
// stayset/bornset are bitmasks; bit n=1 means triggered when neighbor count is n
float ff = 0.0;
if (currentAlive) {
    ff = ((stayset & (1 << (k - 1))) > 0) ? float(k) : 0.0;  // survive
} else {
    ff = ((bornset & (1 << (k - 1))) > 0) ? 1.0 : 0.0;       // birth
}
```**RD Gray-Scott 更新详情**：

格雷-斯科特方程的物理意义：
- `Du·∇²u`：u 的扩散（空间平滑）
- `-u·v²`：反应消耗（当u和v相遇时u减少）
- `F·(1-u)`：补充u（喂食，将u拉回到1.0）
- `Dv·∇²v`：v 的扩散
- `+u·v²`：反应产物（当u和v相遇时v增加）
- `-(F+k)·v`：去除 v（杀戮+饲料的组合腐烂）```glsl
float u = prevState.x;
float v = prevState.y;
vec2 Duv = laplacian(uv) * DIFFUSION;  // DIFFUSION = vec2(Du, Dv)
float du = Duv.x - u * v * v + F * (1.0 - u);
float dv = Duv.y + u * v * v - (F + k) * v;
// Forward Euler integration, clamp to prevent numerical instability
fragColor.xy = clamp(vec2(u + du * DT, v + dv * DT), 0.0, 1.0);
```**简化的研发详细信息**：
这种方法不使用标准的格雷-斯科特方程，而是使用梯度驱动的位移和随机衰减来近似反应扩散行为。结果更有机，但更难控制。```glsl
float avgRD = blur3x3(uv);
vec2 pwr = (1.0 / iResolution.xy) * 1.5;
// Compute gradient (similar to Sobel)
vec2 lap = vec2(
    texture(iChannel0, uv + vec2(pwr.x, 0)).y - texture(iChannel0, uv - vec2(pwr.x, 0)).y,
    texture(iChannel0, uv + vec2(0, pwr.y)).y - texture(iChannel0, uv - vec2(0, pwr.y)).y
);
uv = uv + lap * (1.0 / iResolution.xy) * 3.0;  // Displace sampling point along gradient (diffusion)
float newRD = texture(iChannel0, uv).x + (noise.z - 0.5) * 0.0025 - 0.002;  // Random decay
newRD += dot(texture(iChannel0, uv + (noise.xy - 0.5) / iResolution.xy).xy, vec2(1, -1)) * 0.145;  // Reaction term
```### 步骤 5：可视化和着色

**什么**：将模拟缓冲区数据映射到视觉效果 - 颜色映射、渐变照明、凹凸贴图等。

**为什么**：原始模拟数据由 0~1 范围内的标量/矢量值组成，需要进行艺术处理才能产生吸引人的视觉效果。最常见的技术是计算缓冲区值的梯度以获得凹凸照明的法线信息。

**色彩映射技术**：```glsl
// Basic: nonlinear color separation
// c is a [0,1] value; different pow exponents make RGB channels respond at different rates
float c = 1.0 - texture(iChannel0, uv).y;
vec3 col = pow(vec3(1.5, 1, 1) * c, vec3(1, 4, 12));
// R channel responds linearly, G channel with 4th power (rapid decay in dark areas), B channel with 12th power (blue only at brightest spots)
```**梯度法线计算**：```glsl
// Compute surface normals from scalar field (for bump map lighting)
vec3 normal(vec2 uv) {
    vec3 delta = vec3(1.0 / iResolution.xy, 0.0);
    // Central difference for x and y gradients
    float du = texture(iChannel0, uv + delta.xz).x - texture(iChannel0, uv - delta.xz).x;
    float dv = texture(iChannel0, uv + delta.zy).x - texture(iChannel0, uv - delta.zy).x;
    // z component controls bump intensity (smaller = stronger bumps)
    return normalize(vec3(du, dv, 1.0));
}
```**镜面高光效果**：```glsl
// Produce specular edges via sampling offset
float c2 = 1.0 - texture(iChannel0, uv + 0.5 / iResolution.xy).y;
// c2*c2 - c*c is positive at gradient changes, producing edge highlights
col += vec3(0.36, 0.73, 1.0) * max(c2 * c2 - c * c, 0.0) * 12.0;
```**晕影+伽玛校正**：```glsl
// Vignette: darken edges
col *= pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.125) * 1.15;
// Fade-in effect
col *= smoothstep(0.0, 1.0, iTime / 2.0);
// Gamma correction (approximately 2.0)
fragColor = vec4(sqrt(min(col, 1.0)), 1.0);
```---

## 变体详细信息

### 变体 1：康威生命游戏（离散 CA）

**与基本版本的区别**：使用离散二元状态和邻居计数规则而不是连续的 RD 方程。这是最经典的元胞自动机，简单的规则可以产生极其复杂的行为（滑翔机、振荡器、静物等）。

**完整的缓冲区A代码**：```glsl
int cell(in ivec2 p) {
    ivec2 r = ivec2(textureSize(iChannel0, 0));
    p = (p + r) % r;  // wrap-around boundary
    return (texelFetch(iChannel0, p, 0).x > 0.5) ? 1 : 0;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    ivec2 px = ivec2(fragCoord);

    // Moore neighborhood counting
    int k = cell(px+ivec2(-1,-1)) + cell(px+ivec2(0,-1)) + cell(px+ivec2(1,-1))
          + cell(px+ivec2(-1, 0))                        + cell(px+ivec2(1, 0))
          + cell(px+ivec2(-1, 1)) + cell(px+ivec2(0, 1)) + cell(px+ivec2(1, 1));
    int e = cell(px);

    // B3/S23 rule
    float f = (((k == 2) && (e == 1)) || (k == 3)) ? 1.0 : 0.0;

    // Initialization: approximately 10% random living cells
    if (iFrame < 2) {
        f = step(0.9, fract(sin(fragCoord.x * 13.0 + sin(fragCoord.y * 71.1)) * 138.5));
    }

    fragColor = vec4(f, 0.0, 0.0, 1.0);
}
```**调整方向**：
- 修改B/S规则编号可以产生完全不同的行为
- 增加初始密度（改变“step(0.9, ...)”中的0.9）会改变进化结果
- .y 通道可以存储可视化期间颜色映射的“年龄”

### 变体 2：可配置规则集 CA（出生/生存位掩码）

**与基础版本的区别**：使用位掩码编码任意CA规则，支持摩尔/冯诺依曼/扩展邻域，能够产生蠕虫、海绵、爆炸等模式。

**位掩码编码解释**：
- `BORN_SET = 8` 是二进制 `0b1000`，意味着设置了位 3 → B3（当 3 个邻居时出生）
- `STAY_SET = 12` 是二进制 `0b1100`，意味着设置了位 2,3 → S23（当有 2 个或 3 个邻居时生存）
- `LIVEVAL` 控制活细胞的状态值；当大于1时，与`DECIMATE`结合可以产生梯度衰减效果
- `DECIMATE` 是每帧的衰减量，产生“拖尾”效果

**关键代码**：```glsl
#define BORN_SET  8        // birth bitmask, 8 = B3 (bit 3 set)
#define STAY_SET  12       // survival bitmask, 12 = S23 (bits 2,3 set)
#define LIVEVAL   2.0      // living cell state value
#define DECIMATE  1.0      // decay value (0=no decay)

// Rule evaluation
float ff = 0.0;
float ev = texelFetch(iChannel0, px, 0).w;
if (ev > 0.5) {
    // Living cell: decay first, then check if survival rule is met
    if (DECIMATE > 0.0) ff = ev - DECIMATE;
    if ((STAY_SET & (1 << (k - 1))) > 0) ff = LIVEVAL;
} else {
    // Dead cell: check if birth rule is met
    ff = ((BORN_SET & (1 << (k - 1))) > 0) ? LIVEVAL : 0.0;
}
```**值得注意的规则集**：
- B3/S23（康威生活）：出生=8，停留=12
- B36/S23 (HighLife)：BORN=40，STAY=12 — 具有自我复制器
- B1/S1 (Gnarl): BORN=2, STAY=2 — 分形生长
- B3/S012345678（没有死亡的生命）：BORN=8，STAY=511 — 只生长，永不死亡

### 变体 3：可分离高斯模糊 RD（多缓冲区架构）

**与基础版本的区别**：用可分离的水平/垂直高斯模糊代替单个 3x3 拉普拉斯算子进行扩散步骤，以更平滑的图案实现更大的有效扩散半径。

**架构**：
- 缓冲区 A：反应步骤（将缓冲区 C 的模糊结果读取为扩散项）
- 缓冲区 B：水平高斯模糊（读取缓冲区 A）
- 缓冲区 C：垂直高斯模糊（读取缓冲区 B）

**为什么分开**：
- 直接 NxN 内核需要 N² 样本
- 分为水平+垂直通道，每个通道需要 N 个样本，总共 2N 个
- 9-tap 可分离模糊 = 18 个样本 ≈ 相当于 81 点 9x9 内核

**Buffer B完整代码（水平模糊）**：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    float h = 1.0 / iResolution.x;
    vec4 sum = vec4(0.0);
    // 9-tap Gaussian weights (approximate normal distribution)
    sum += texture(iChannel0, fract(vec2(uv.x - 4.0*h, uv.y))) * 0.05;
    sum += texture(iChannel0, fract(vec2(uv.x - 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x - 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x - 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x,         uv.y))) * 0.16;
    sum += texture(iChannel0, fract(vec2(uv.x + 1.0*h, uv.y))) * 0.15;
    sum += texture(iChannel0, fract(vec2(uv.x + 2.0*h, uv.y))) * 0.12;
    sum += texture(iChannel0, fract(vec2(uv.x + 3.0*h, uv.y))) * 0.09;
    sum += texture(iChannel0, fract(vec2(uv.x + 4.0*h, uv.y))) * 0.05;
    fragColor = vec4(sum.xyz / 0.98, 1.0);  // 0.98 = weight sum, normalized
}
```缓冲区 C 具有相同的结构，但沿 y 轴模糊（将“uv.x ± n*h”替换为“uv.y ± n*v”，其中“v = 1.0/iResolution.y”）。

### 变体 4：连续微分算子 CA（静脉/流体类型）

**与基本版本的区别**：计算网格上的旋度、散度和拉普拉斯算子，结合多步平流循环，产生位于 CA 和 PDE 流体模拟之间的静脉/流体状有机模式。

**核心概念**：
- **Curl**：描述场的旋转趋势，用于产生涡旋效应
- **发散**：描述一个场的扩散/汇聚趋势
- **平流**：沿速度场方向传播场值

**参数调整指南**：
- `STEPS (10~60)`: 平流步骤；更多=更流畅但更慢
- `ts (0.1~0.5)`: 平流旋转强度，控制涡流强度
- `cs (-3~-1)`：卷曲缩放；负值产生逆时针旋转
- `ls (0.01~0.1)`：拉普拉斯缩放，控制扩散强度
- `amp (0.5~2.0)`: 自放大系数
- `upd (0.2~0.6)`：更新平滑系数，控制新旧状态混合比例

**关键代码**：```glsl
#define STEPS 40
#define ts    0.2
#define cs   -2.0
#define ls    0.05
#define amp   1.0
#define upd   0.4

// Discrete curl and divergence on a 3x3 stencil
// Standard weights: _K0=-20/6 (center), _K1=4/6 (edge), _K2=1/6 (corner)
curl = uv_n.x - uv_s.x - uv_e.y + uv_w.y
     + _D * (uv_nw.x + uv_nw.y + uv_ne.x - uv_ne.y
           + uv_sw.y - uv_sw.x - uv_se.y - uv_se.x);
div  = uv_s.y - uv_n.y - uv_e.x + uv_w.x
     + _D * (uv_nw.x - uv_nw.y - uv_ne.x - uv_ne.y
           + uv_sw.x + uv_sw.y + uv_se.y - uv_se.x);

// Multi-step advection loop
for (int i = 0; i < STEPS; i++) {
    advect(off, vUv, texel, curl, div, lapl, blur);
    offd = rot(offd, ts * curl);  // rotate offset direction
    off += offd;                   // accumulate offset
    ab += blur / float(STEPS);    // accumulate blurred value
}
```### 变体 5：RD 驱动的 3D 表面 (Raymarched RD)

**与基础版本的区别**：2D RD 结果用作映射到 3D 球体上的纹理，驱动表面位移和颜色；图像通道成为完整的 raymarcher。

**实施要点**：
1. Buffer A维持标准RD模拟不变
2.图像通道成为光线行进渲染器
3. SDF函数将3D点映射到球形UV，然后对RD缓冲区进行采样
4. RD值驱动面位移

**关键代码**：```glsl
// Image pass: use RD texture for displacement in the SDF
vec2 map(in vec3 pos) {
    vec3 p = normalize(pos);
    vec2 uv;
    // Spherical parameterization: 3D point → 2D UV
    uv.x = 0.5 + atan(p.z, p.x) / (2.0 * 3.14159);  // longitude [0, 1]
    uv.y = 0.5 - asin(p.y) / 3.14159;                 // latitude [0, 1]

    float y = texture(iChannel0, uv).y;     // read v component from RD buffer
    float displacement = 0.1 * y;            // displacement amount (adjustable scale factor)
    float sd = length(pos) - (2.0 + displacement);  // base sphere SDF + displacement
    return vec2(sd, y);  // return distance and material parameter
}
```**延伸方向**：
- 用环面、平面或其他基本形状替换球体
- 使用两个RD通道分别驱动位移和颜色
- 添加法线扰动以获得更精细的表面细节
- 与环境贴图结合进行反射/折射

---

## 性能优化深度分析

### 1. texelFetch 与纹理

**离散 CA** 应使用 `texelFetch(iChannel0, ivec2(px), 0)` 而不是 `texture()`：
- 避免不必要的纹理过滤开销
- 保证像素精确读取，而不会因浮点精度而导致相邻像素采样
- 对于二进制状态 (0/1)，任何插值都会引入错误

**连续RD**可以使用带有线性过滤的`texture()`：
- 硬件自动执行双线性插值
- 插值效果相当于额外的平滑/扩散，这在某些情况下可能是有利的
- 硬件加速，比手动插值更快

### 2. 可分离模糊代替大核拉普拉斯算子

如果需要大的扩散半径：
- **不要**使用更大的 NxN 拉普拉斯内核 → O(N²) 样本
- **Do** 使用可分离的两遍高斯模糊（水平 + 垂直）→ O(2N) 个样本
- 通过额外的缓冲区传递来实现

**数值比较**：
|方法|等效内核大小 |样本计数 |
|------|------------|---------|
| 3x3 拉普拉斯 | 3×3 | 3×3 9 |
| 5x5 拉普拉斯 | 5×5 | 5×5 25 | 25
| 9x9 拉普拉斯 | 9×9 | 9×9 81 | 81
|可分离 9 抽头高斯 | ≈9×9 | 18 | 18
|可分离 13 抽头高斯 | ≈13×13 | 26 | 26

### 3. 多步子迭代

对于 RD，您可以使用较小的 DT 在单个帧内循环多个子迭代，从而在保持稳定性的同时提高收敛速度：```glsl
#define SUBSTEPS 4     // sub-iteration count
#define SUB_DT 0.25    // = DT / SUBSTEPS
for (int i = 0; i < SUBSTEPS; i++) {
    vec2 lap = laplacian9(uv);
    float uvv = u * v * v;
    u += (DU * lap.x - uvv + F * (1.0 - u)) * SUB_DT;
    v += (DV * lap.y + uvv - (F + K) * v) * SUB_DT;
}
```**注意**：在子迭代中，拉普拉斯算子仅在第一步从纹理读取时才是正确的；后续步骤应根据更新的值重新计算拉普拉斯算子。然而，在实践中，单读多步积分的近似值通常就足够好了。

### 4. 降低分辨率模拟

如果目标显示分辨率较高，但图案的空间频率不需要 1:1 像素精度：
- 在缓冲区中以较低分辨率运行模拟（不能在 ShaderToy 中直接配置，但可以在自定义引擎中配置）
- 在图像通道中使用双线性插值上采样
- 可以节省4x~16x的计算量

### 5. 避免分支和条件

使用“step()”、“mix()”、“clamp()”代替“if/else”进行 CA 规则评估，以减少 GPU 扭曲发散：```glsl
// Original if/else version:
// if (k==3) f=1.0; else if (k==2 && e==1) f=1.0; else f=0.0;

// Branch-free version:
float f = max(step(abs(float(k) - 3.0), 0.5),
              step(abs(float(k) - 2.0), 0.5) * step(0.5, float(e)));
```**说明**：
- 当 k=3 时，“step(abs(float(k) - 3.0), 0.5)”为 1.0，否则为 0.0
- 当 k=2 且 e=1 时，“step(abs(float(k) - 2.0), 0.5) * step(0.5, float(e))”为 1.0
- `max()` 结合了两个条件

---

## 组合建议 — 详细信息

### 1. RD + Raymarching（3D 置换/整形）

将 RD 结果作为高度图映射到 3D 表面（球体、平面、环面），并通过 SDF 位移创建有机凹凸表面。适用于生物有机体、外星地形和类似效果。

**完整图像传递示例**（球体 + RD 位移）：```glsl
vec2 map(in vec3 pos) {
    vec3 p = normalize(pos);
    vec2 uv;
    uv.x = 0.5 + atan(p.z, p.x) / (2.0 * 3.14159);
    uv.y = 0.5 - asin(p.y) / 3.14159;
    float y = texture(iChannel0, uv).y;
    float displacement = 0.1 * y;
    float sd = length(pos) - (2.0 + displacement);
    return vec2(sd, y);
}

// Use map() in the raymarch loop
// Normals computed via central difference of map()
// Material color based on y value returned by map() for color mapping
```### 2.CA/RD + 粒子系统

使用 CA/RD 场作为粒子的速度场或生成概率场：
- 粒子沿 RD 梯度流动
- 新粒子在活 CA 细胞中产生
- 产生“活的”粒子效果

**实施方式**：
- 缓冲区 A：RD/CA 模拟
- Buffer B：粒子位置存储（每个像素存储一个粒子的位置）
- 图像：可视化粒子和/或场

### 3. RD + 后处理光照

在图像通道中，根据 RD 值 → 凹凸贴图 → 照明/反射/折射计算法线。与环境贴图（立方体贴图）相结合，可以产生蚀刻的金属表面、液体波纹和类似的效果。

**关键技术**：
- 计算 RD 标量场的梯度以获得法线
- 使用 Phong/Blinn-Phong 光照模型
- 用于对环境反射的立方体贴图进行采样的法线
- 多种颜色映射方案增加视觉丰富度

### 4.CA + 颜色衰减轨迹

活细胞使用高值；死亡后，每个帧的值都会衰减（而不是立即降至零），RGB 通道中的不同衰减率会产生彩色拖尾效果。这是Automata X Showcase的核心技术。

**实现代码示例**：```glsl
// Add decay logic after CA update
vec4 prev = texelFetch(iChannel0, px, 0);
if (f > 0.5) {
    // Living cell: set to high value
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
} else {
    // Dead cell: different decay rates per channel
    fragColor = vec4(
        prev.x * 0.99,   // R decays slowly → longest red trail
        prev.y * 0.95,   // G decays moderately
        prev.z * 0.90,   // B decays fast → shortest blue trail
        1.0
    );
}
```### 5. RD + 域扭曲

在计算之前对 RD 采样 UV 应用涡旋扭曲或螺旋缩放域变换，导致扩散场本身扭曲，产生螺旋和涡旋状有机图案。 Flexi 的 Expansive RD 使用了这种技术。

**实现代码示例**：```glsl
// Apply domain transform to UV before RD update
vec2 warpedUV = uv;
// Vortex warp
float angle = length(uv - 0.5) * 3.14159 * 2.0;
float s = sin(angle * 0.1);
float c = cos(angle * 0.1);
warpedUV = (warpedUV - 0.5) * mat2(c, -s, s, c) + 0.5;

// Sample state using transformed UV
vec2 state = texture(iChannel0, warpedUV).xy;
// Then proceed with normal RD computation...
```
