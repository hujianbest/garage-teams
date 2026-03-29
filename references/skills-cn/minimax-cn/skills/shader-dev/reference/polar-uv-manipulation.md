# 极坐标和 UV 操作 - 详细参考

> 本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、分步说明、变体详细信息、深入的性能分析以及完整的组合代码示例。

## 先决条件

### GLSL 基础知识
- **统一/变化**：全局变量传递机制
- **内置函数**：`sin`、`cos`、`atan`、`length`、`fract`、`mod`、`smoothstep`、`mix`、`clamp`、`pow`、`exp`、`log`、`abs`、`max`、`min`、`floor`、`ceil`、`dot`
- **矢量类型**：`vec2`、`vec3`、`vec4`，支持 swizzle（例如，`.xy`、`.rgb`）
- **矩阵类型**：用于 2D 旋转的 `mat2`

### 向量数学
- 2D 向量运算：加法、减法、乘法、除法、长度（`length`）、归一化（`normalize`）
- 点积（`dot`）：投影和角度关系
- 二维旋转矩阵：```glsl
mat2 rotate(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}
```### 坐标系
- 笛卡尔坐标(x,y)：标准直角坐标系
- 屏幕坐标：左下角 (0,0)、右上角（iResolution.x、iResolution.y）
- 标准化坐标：通常映射到 [-1, 1] 或 [0, 1] 范围

### ShaderToy 框架
- `mainImage(out vec4 fragColor, in vec2 fragCoord)`：入口函数
- `fragCoord`：当前像素的屏幕坐标
- `iResolution`：视口分辨率（像素）
- `iTime`：自启动以来的时间（秒）
- `iMouse`：鼠标位置

## 实施步骤

### 第 1 步：UV 归一化和居中

**什么**：将屏幕像素坐标转换为以屏幕中心为中心、统一缩放的标准化坐标。

**为什么**：所有后续的极坐标操作都依赖于正确的中心点和统一的比例尺。如果没有这一步，效果就会被抵消或拉伸。

**比较三种方法**：

|方法|范围 |使用案例|
|----------|--------|----------|
| `/ 分钟（iResolution.x，iResolution.y）` | [-1, 1] 方形区域 |最通用，确保圆圈保持圆形 |
| `/ iResolution.y` | [-方面，方面] × [-1, 1] |当需要全屏宽度时 |
|像素量化|取决于 PIXEL_FILTER |像素化/复古风格 |```glsl
// Approach 1: range [-1, 1], most common
vec2 uv = (2.0 * fragCoord - iResolution.xy) / min(iResolution.x, iResolution.y);

// Approach 2: range [-aspect, aspect] x [-1, 1]
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Approach 3: precise pixel size control (precise pixel size control)
float pixel_size = length(iResolution.xy) / PIXEL_FILTER; // PIXEL_FILTER adjustable: pixelation level
vec2 uv = (floor(fragCoord * (1.0/pixel_size)) * pixel_size - 0.5*iResolution.xy) / length(iResolution.xy);
```### 步骤 2：笛卡尔坐标到极坐标变换

**什么**：将（x，y）坐标转换为（r，θ）极坐标。

**为什么**：这是整个范式的基本变换，将线性 xy 空间映射到以原点为中心的径向空间。在极坐标中：
- 圆就是 r = 常数
- 射线就是 θ = 常数
- 这使得创建环形/螺旋/径向效果非常简单

**关于`atan`函数**：
- `atan(y, x)`（双参数版本）相当于数学中的 atan2，返回 [-π, π]
- `atan(y/x)`（单参数版本）仅返回 [-π/2, π/2]，丢失象限信息
- 始终使用两个参数版本```glsl
// Basic transform
float r = length(uv);           // Radius
float theta = atan(uv.y, uv.x); // Angle, range [-PI, PI]

// Wrapped as reusable functionvec2 toPolar(vec2 p) {
    return vec2(length(p), atan(p.y, p.x));
}

// Normalize angle to [0, 1] rangevec2 polar = vec2(atan(uv.y, uv.x) / 6.283 + 0.5, length(uv));
// polar.x in [0,1], polar.y is radius
```### 步骤3：极坐标空间中的运算

**什么**：在 (r, θ) 空间中执行各种变换以创建效果。

**为什么**：极坐标空间的独特之处在于，旋转、螺旋、径向重复等在笛卡尔坐标中极其困难的效果在这里变成了简单的加减乘运算。

#### 3a。径向畸变（漩涡）——半径的角度偏移

**原理**：`θ_new = θ - k × r`使得离中心越远的点旋转得越多，自然形成漩涡。 `k` 控制涡流的“紧密程度”。```glsl
// Greater radius = more rotation → vortex effect
float spin_amount = 0.25; // Adjustable: vortex strength, 0=no rotation, 1=maximum rotation
float new_theta = theta - spin_amount * 20.0 * r;
```#### 3b。角度扭曲 — 角度加时间偏移

**原理**：将时间和角度本身的函数添加到角度上会产生随时间变化的扭曲环。 “sin(theta)”项使失真变得不均匀，创造出一种有机的感觉。```glsl
// Angle varies with time and position → twisted ringsfloat twist_angle = theta + 2.0 * iTime + sin(theta) * sin(iTime) * 3.14159;
```#### 3c。阿基米德螺线 — 半径减角

**原理**：阿基米德螺线r = a + bθ具有等距性质。在 UV 空间中，`y -= x`（即 r -= θ）将同心环“展开”为等距螺旋带。```glsl
// Unfold into spiral bandsvec2 spiral_uv = vec2(theta_normalized, r);
spiral_uv.y -= spiral_uv.x; // Key: "unfold" radial space into spirals
```#### 3d。对数螺线 — 角度加上 log(r) 剪切

**原理**：对数螺线（等角螺线）r = ae^(bθ) 具有自相似性——放大后看起来一模一样。 “log(r)”剪切力使旋转量在不同半径处呈对数增长，这在自然界中很常见（鹦鹉螺壳、星系臂）。```glsl
// Logarithmic spiral stretch
float shear = 2.0 * log(r); // Adjustable: coefficient controls spiral tightness
float c = cos(shear), s = sin(shear);
mat2 spiral_mat = mat2(c, -s, s, c); // Rotation matrix implements shear
```#### 3e。万花筒 — 角度模数和镜像

**原理**：将2π角度范围划分为N个相等的扇区，然后将所有像素映射到单个扇区。镜像使相邻扇区对称，避免接缝。

**数学推导**：
1. `sector = 2π / N`：每个扇区的角宽度
2.`c_idx=floor((θ+sector/2)/sector)`：当前扇区索引
3.`θ'=mod(θ+sector/2,sector)-sector/2`：折叠到[-sector/2,sector/2]
4. `θ' *= (2 × (c_idx mod 2) - 1)`：翻转奇数扇区```glsl
// Angular subdivision + mirroring for kaleidoscopefloat rep = 12.0;          // Adjustable: number of symmetry axes
float sector = TAU / rep;  // Angle per sector
float a = polar.y;         // Angle component

// Modulo to single sector
float c_idx = floor((a + sector * 0.5) / sector);
a = mod(a + sector * 0.5, sector) - sector * 0.5;

// Mirror: flip adjacent sectors
a *= mod(c_idx, 2.0) * 2.0 - 1.0;
```#### 3f。螺旋臂压缩——角域的周期性调制

**原理**：星系旋臂不是简单的线条，而是物质密度较高的区域。 `cos(N × (θ - 剪切))` 在角域中产生周期性压缩，导致物质（颜色/亮度）沿着 N 个臂累积。 `COMPR` 参数控制手臂的“锐度”。

**密度补偿**：压缩改变局部密度（如手风琴效果）； “arm_密度”补偿了这种不均匀性，防止手臂太亮或太暗。```glsl
// Galaxy spiral arm effect
float NB_ARMS = 5.0;   // Adjustable: number of spiral arms
float COMPR = 0.1;      // Adjustable: intra-arm compression strength
float phase = NB_ARMS * (theta - shear);
theta = theta - COMPR * cos(phase); // Compress angular domain to form arm structures
float arm_density = 1.0 + NB_ARMS * COMPR * sin(phase); // Density compensation
```### 步骤 4：极坐标到笛卡尔重建（往返）

**什么**：将修改后的极坐标转换回笛卡尔坐标。

**为什么**：某些效果需要在极坐标空间中进行变换，然后返回到 xy 空间进行进一步处理（例如，叠加纹理噪声、Truchet 图案等）。这就形成了完整的笛卡尔→极坐标→笛卡尔“往返”。

**注释**：
- 逆变换后，坐标原点可能需要调整（例如，到屏幕中心的“mid”偏移）
- 如果您只需要在极坐标空间中着色（例如，环形渐变），则不需要逆变换```glsl
// Basic inverse transform
vec2 new_uv = vec2(r * cos(new_theta), r * sin(new_theta));

// Wrapped as reusable functionvec2 toRect(vec2 p) {
    return vec2(p.x * cos(p.y), p.x * sin(p.y));
}

// Complete round trip: offset to screen center after transform
vec2 mid = (iResolution.xy / length(iResolution.xy)) / 2.0;
vec2 warped_uv = vec2(
    r * cos(new_theta) + mid.x,
    r * sin(new_theta) + mid.y
) - mid;
```### 步骤 5：极坐标形状定义 (SDF)

**什么**：通过极坐标中的 r(θ) 函数定义形状的有符号距离场。

**为什么**：许多经典曲线（心形曲线、玫瑰曲线、星形曲线）在极坐标中都有优雅的解析表达式，而在笛卡尔坐标中则极其复杂。

**SDF的优点**：
- 负值 = 内部，正值 = 外部，零 = 边界
- 方便的布尔运算（“max”=交集，“min”=并集）
- `smoothstep` 直接产生抗锯齿边缘
- `abs(d)` 产生轮廓，`1/abs(d)` 产生发光```glsl
// Cardioid
float a = atan(p.x, p.y) / 3.141593; // Note: atan(x,y) not atan(y,x), so heart points up
float h = abs(a);
float heart_r = (13.0*h - 22.0*h*h + 10.0*h*h*h) / (6.0 - 5.0*h);
float dist = r - heart_r; // Negative = inside, positive = outside

// Rose curve / petals
float PETAL_FREQ = 3.0; // Adjustable: petal frequency (K.x/K.y controls integer/fractional petals)
float A_coeff = 0.2;    // Adjustable: petal amplitude
float rose_dist = abs(r - A_coeff * sin(PETAL_FREQ * theta) - 0.5); // Distance to curve

// Render SDF as visible shape
float shape = smoothstep(0.01, -0.01, dist); // Anti-aliased edge
```### 第 6 步：着色和抗锯齿

**什么**：基于极坐标信息的颜色并处理边缘抗锯齿。

**为什么**：极坐标着色自然会产生径向渐变和环形图案。抗锯齿在极坐标中尤其重要，因为由于角度细分，像素密度在远离中心的地方变化很大。

**抗锯齿方法比较**：

|方法|优点 |缺点 |
|--------|------|------|
| `fwidth` |自适应、精确 |需要GPU衍生支持 |
|固定分辨率宽度|简单、可靠 |不适应缩放|
| `smoothstep` + 固定偏移 |最简单|平均结果 |```glsl
// Adaptive anti-aliasing based on fwidthfloat aa = smoothstep(-1.0, 1.0, value / fwidth(value));

// Resolution-based anti-aliasingfloat aa_size = 2.0 / iResolution.y;
float edge = smoothstep(0.5 - aa_size, 0.5 + aa_size, value);

// General SDF anti-aliasing using smoothstep
float d = some_sdf_value;
float col = smoothstep(aa_size, -aa_size, d); // aa_size ≈ 1~3 pixels

// Radial gradient coloring
vec3 color = vec3(1.0, 0.4 * r, 0.3); // Color varies with radius
color *= 1.0 - 0.4 * r;               // Darken at edges

// Inter-spiral-band anti-aliasingfloat inter_spiral_aa = 1.0 - pow(abs(2.0 * fract(spiral_uv.y) - 1.0), 10.0);
```## 变体详细信息

### 变体 1：动态涡流/漩涡背景

**与基础版本的区别**：完整的笛卡尔→极坐标→笛卡尔往返+迭代域扭曲生成复杂的纹理。

**技术要点**：
1.首先在极坐标中应用涡旋畸变
2. 转换回笛卡尔坐标
3. 在变换后的空间中执行 5 次域扭曲迭代，每次迭代非线性偏移坐标
4. 迭代的正弦/余弦组合产生复杂的有机纹理

**参数说明**：
- `SPIN_AMOUNT`：涡流强度，控制极性扭曲幅度
- `SPIN_EASE`：涡流缓动，使中心和边缘之间的旋转速度不同
- `speed`：动画速度，由`iTime`驱动```glsl
// Polar coordinate vortex transform
float new_angle = atan(uv.y, uv.x) + speed
    - SPIN_EASE * 20.0 * (SPIN_AMOUNT * uv_len + (1.0 - SPIN_AMOUNT));
vec2 mid = (screenSize.xy / length(screenSize.xy)) / 2.0;
uv = vec2(uv_len * cos(new_angle) + mid.x,
           uv_len * sin(new_angle) + mid.y) - mid;

// Iterative domain warping for organic textures
uv *= 30.0;
for (int i = 0; i < 5; i++) {
    uv2 += sin(max(uv.x, uv.y)) + uv;
    uv  += 0.5 * vec2(cos(5.1123 + 0.353*uv2.y + speed*0.131),
                       sin(uv2.x - 0.113*speed));
    uv  -= cos(uv.x + uv.y) - sin(uv.x*0.711 - uv.y);
}
```### 变体 2：极环扭转

**与基本版本的区别**：直接在极坐标空间中渲染几何体（不返回笛卡尔），通过角度切片模拟 3D 环面。

**技术要点**：
1. 将 r 尺寸偏移到环的中心线 (`r -= OUT_RADIUS`) 以使环区域居中
2.在角度维度上沿着环“切片”，每个切片都是正多边形的一条边
3. `twist` 变量使多边形沿着环扭曲，产生莫比乌斯带状效果
4. `sin(uvr.y)*sin(iTime)` 项根据角度改变扭曲速度，从而产生有机挤压/拉伸```glsl
// Geometric slicing in polar coordinates
vec2 uvr = vec2(length(uv), atan(uv.y, uv.x) + PI);
uvr.x -= OUT_RADIUS; // Offset to ring centerline

float twist = uvr.y + 2.0*iTime + sin(uvr.y)*sin(iTime)*PI;
for (int i = 0; i < NUM_FACES; i++) {
    float x0 = IN_RADIUS * sin(twist + TAU * float(i) / float(NUM_FACES));
    float x1 = IN_RADIUS * sin(twist + TAU * float(i+1) / float(NUM_FACES));
    // Define face start/end positions in the polar r direction
    vec4 face = slice(x0, x1, uvr);
    col = mix(col, face.rgb, face.a);
}
```### 变体 3：银河/对数螺旋（银河风格）

**与基本版本的区别**：对等角螺旋使用“log(r)”，并结合 FBM 噪声和螺旋臂压缩。

**技术要点**：
1.“log(r)”剪切力是核心——它将同心圆映射到对数螺线
2. 旋转矩阵R将噪声采样坐标旋转剪切角，使噪声沿着旋臂对齐
3.`NB_ARMS`和`COMPR`控制arm的数量和锐度
4. FBM噪声在旋转空间中采样，产生银河尘埃纹理```glsl
float rho = length(uv);
float ang = atan(uv.y, uv.x);
float shear = 2.0 * log(rho);     // Logarithmic spiral core
mat2 R = mat2(cos(shear), -sin(shear), sin(shear), cos(shear));

// Spiral arms
float phase = NB_ARMS * (ang - shear);
ang = ang - COMPR * cos(phase) + SPEED * t; // Inter-arm compression
uv = rho * vec2(cos(ang), sin(ang));         // Reconstruct Cartesian
float gaz = fbm_noise(0.09 * R * uv);        // Sample noise in spiral space
```### 变体 4：阿基米德螺旋带 + 涡旋

**与基本版本的区别**：将极坐标展开为螺旋带，在带内创建独立的涡流动画，并具有弧长参数化。

**技术要点**：
1. `U.y -= U.x` 是阿基米德展开的核心——将同心环转换为等距螺旋带
2. 弧长参数化“arc_length()”确保螺旋带内单元面积均匀
3.每个cell使用`dot`+`cos`创建一个小漩涡，中心强，边缘弱
4. `cell_id.x` 赋予不同细胞不同的涡旋相位，避免单调重复```glsl
vec2 U = vec2(atan(U.y, U.x)/TAU + 0.5, length(U));
U.y -= U.x;                                    // Archimedean unfolding
U.x = arc_length(ceil(U.y) + U.x) - iTime;     // Arc-length parameterization

// Vortex within each cell of the spiral band
vec2 cell_uv = fract(U) - 0.5;
float vortex = dot(cell_uv,
    cos(vec2(-33.0, 0.0)                       // Rotation matrix angle offset
        + 0.3 * (iTime + cell_id.x)            // Time + spatial rotation amount
        * max(0.0, 0.5 - length(cell_uv))));   // Strong at center, weak at edges
```### 变体 5：复数/极性对偶（宝石涡旋风格）

**与基本版本的区别**：使用复数运算（乘法=旋转+缩放，幂=螺旋映射）而不是显式三角函数来实现共形映射。

**技术要点**：
1. 复幂 `z^(1/e)` 相当于极坐标中的 `(r^(1/e), θ/e)` — 同时缩放半径和压缩角度
2. `exp(log(length(u)) / e)` 实现 `r^(1/e)` 而不显式计算幂
3.`ceil(r - a/TAU)`产生螺旋轮廓线——对应于复平面中黎曼曲面的不同片
4. 多层“sin”/“cos”组合产生宝石般的干涉色```glsl
float e = n * 2.0;  // Complex power exponent, controls spiral curvature
float a = atan(u.y, u.x) - PI/2.0;     // Angle
float r = exp(log(length(u)) / e);      // r^(1/e) — complex root
float sc = ceil(r - a/TAU);             // Spiral contour lines
float s = pow(sc + a/TAU, 2.0);         // Spiral gradient
// Multi-layer spiral compositing
col += sin(cr + s/n * TAU / 2.0);       // Spiral color layer 1
col *= cos(cr + s/n * TAU);             // Spiral color layer 2
col *= pow(abs(sin((r - a/TAU) * PI)), abs(e) + 5.0); // Smooth edges
```## 深入的性能分析

### 1. 避免极点的数值问题

`atan(0,0)` 和 `length(0)` 可能会在原点附近产生数值不稳定。虽然GLSL的`atan`不会在原点崩溃，但返回值是未定义的，可能会导致闪烁。```glsl
// Safe polar coordinate conversion
float r = max(length(uv), 1e-6); // Avoid division by zero
float theta = atan(uv.y, uv.x);  // atan2 is not well-defined at origin but won't crash
```**需要时**：后续计算包含`1.0/r`、`log(r)`或`normalize(uv)`时需要保护。如果只有‘r * somet’，原点处r=0自然是安全的。

### 2.三角函数优化

频繁的 sin/cos 调用是极坐标着色器的主要成本。尽管 GPU sin/cos 是硬件加速的，但循环中的大量使用仍然可能成为瓶颈。```glsl
// If both sin and cos are needed, replace with a single matrix multiplication
mat2 ROT(float a) { float c=cos(a), s=sin(a); return mat2(c,s,-s,c); }
vec2 rotated = ROT(angle) * uv; // Cleaner than computing sin, cos separately and manually constructing

// Use vector dot product instead of explicit trig
// Instead of U.y = cos(rot)*U.x + sin(rot)*U.y
// Use U.y = dot(U, cos(vec2(-33,0) + angle))
```**原理**：GLSL 中的 `cos(vec2(a, b))` 是一条 SIMD 指令，可同时计算两个 cos 值。与“dot”结合，只需一次“cos”调用即可实现旋转（利用恒等式“cos(x - π/2) = sin(x)”）。

### 3. 利用万花筒对称性

万花筒本质上将计算量减少了 N 倍（N = 对称段的数量），作为一种自然优化。所有昂贵的模式计算都仅在一个扇区中完成：```glsl
// Do kaleidoscope folding first, then expensive pattern computation
vec2 kp = kaleidoscope(polar, segments); // Cheap
vec2 rect = toRect(kp);
// All subsequent computation only applies to one sector
float expensive_pattern = some_costly_function(rect); // Same cost but N× visual complexity
```**注意**：万花筒折叠本身的成本（一些“floor”、“mod”和乘法运算）远远低于它“节省”的视觉复杂性。 12 段万花筒意味着您可以以 1/12 的模式计算成本获得 12 倍的视觉丰富度。

### 4. 螺旋带中的循环优化

对于像玫瑰曲线这样需要多循环计算的效果，请保持合理的循环计数：```glsl
// Rose curves only need ceil(K.y) loops
for (int i = 0; i < 7; i++) { // 7 loops are enough to cover most fractional frequencies
    v = max(v, ribbon_value);
    a += 6.28; // Next loop
}
// Don't use excessively large loop counts; 4~8 loops suffice for most cases
```**为什么4~8个循环**：玫瑰曲线r = cos(p/q × θ)有q个循环周期（当p/q为小数时）。对于大多数实用的花瓣频率，7 个循环可提供全面覆盖。过多的循环不仅浪费计算，还可能因浮点累积错误而产生伪影。

### 5. 像素滤波器下采样

对于风格化效果，下采样可以显着减少计算量：```glsl
float pixel_size = length(iResolution.xy) / 745.0; // Adjustable: smaller = more pixelated
vec2 uv = floor(fragCoord / pixel_size) * pixel_size; // Quantize coordinates
// All subsequent computation uses quantized uv, adjacent pixels share results
```**性能优势**：如果pixel_size使每个“虚拟像素”覆盖4×4实际像素，GPU只需要计算唯一值的1/16（剩余的相邻像素产生相同的结果，并且可能受益于缓存优化）。

## 完整的组合代码示例

### 极坐标 + FBM 噪声

在极坐标空间中采样 FBM 噪声以产生有机螺旋纹理（银河尘埃、火焰漩涡）：```glsl
vec2 polar_uv = rho * vec2(cos(modified_ang), sin(modified_ang));
float organic = fbm(polar_uv * frequency); // Sample in transformed space
```### 极坐标 + Truchet 模式

在万花筒折叠空间中铺设 Truchet 瓷砖，产生万花筒几何隧道效果。万花筒提供了对称性； Truchet 提供细节图案。```glsl
// Kaleidoscope folding
vec2 kp = kaleidoscope(polar, segments);
vec2 rect = toRect(kp);

// Truchet grid
rect *= 4.0;
vec2 cell_id = floor(rect + 0.5);
vec2 cell_uv = fract(rect + 0.5) - 0.5;
float cell_hash = fract(sin(dot(cell_id, vec2(127.1, 311.7))) * 43758.5453);

// Arc Truchet
float d = length(cell_uv);
float truchet = abs(d - 0.35);
if (cell_hash > 0.5) {
    truchet = min(truchet, abs(length(cell_uv - 0.5) - 0.5));
} else {
    truchet = min(truchet, abs(length(cell_uv + 0.5) - 0.5));
}
```### 极坐标 + SDF 形状

使用极坐标方程 r(θ) 定义形状轮廓，并结合布尔运算、圆角和发光的 SDF 技术：```glsl
float heart_sdf = r - heart_r_theta;
float glow = 0.02 / abs(heart_sdf); // Glow effect
float solid = smoothstep(0.01, -0.01, heart_sdf); // Solid fill
```### 极坐标+棋盘格/网格

在极坐标空间中铺设棋盘图案，自然形成环形/螺旋棋盘：```glsl
// Create checkerboard in polar UV
float checker = sign(sin(u * PI * 4.0) * cos(uvr.y * 16.0));
col *= checker * (1.0/16.0) + 0.7; // Low contrast checkerboard texture
```### 极坐标+后处理

极坐标效果与伽玛校正、晕影和颜色映射相结合可以极大地提高视觉质量：```glsl
col = pow(col, vec3(1.0/2.2));                                    // Gamma
col = col*0.6 + 0.4*col*col*(3.0-2.0*col);                      // Contrast enhancement
col *= 0.5 + 0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y), 0.7);  // Vignette
```
