# 域重复和空间折叠——详细参考

本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、分步解释、数学推导和高级用法。

## 先决条件

- GLSL基本语法，`vec2/vec3/mat2`操作
- 内置函数的行为，如“mod()”、“fract()”、“abs()”、“atan()”
- 有符号距离场 (SDF) 概念 — 返回从点到最近表面的距离的函数
- Ray Marching 的基本原理
- 2D 旋转矩阵 `mat2(cos(a), sin(a), -sin(a), cos(a))`

## 核心原则详细信息

域重复的本质是**坐标变换**：在计算SDF之前，点“p”的坐标被折叠/映射到有限的“基本域”中，以便无限空间中的每个点都映射到同一个单元。 SDF 函数只需要计算单个单元内的坐标，结果会自动在所有空间中重复。

**三个基本操作：**

|运营|公式|效果|
|------------|---------|--------|
| **模组重复** | `p = mod(p + period/2, period) - period/2` |沿轴无限平移重复 |
| **abs 镜像** | `p = 绝对值(p)` |沿轴平面镜像对称 |
| **旋转折叠** | `角度 = mod(atan(p.y, p.x), TAU/N); p = 旋转(p, -角度)` | N 重旋转对称 |

**关键数学：**

- `mod(x, c)` 将 x 映射到 `[0, c)` 范围，提供周期性
- `abs(x)` 将负半空间折叠到正半空间上，提供反射对称
- `fract(x) = x - Floor(x)` 等价于 `mod(x, 1.0)`，提供标准化周期性

## 详细步骤

### 第 1 步：基本笛卡尔域重复（mod 重复）

**什么**：通过平移沿一个或多个轴无限重复 3D 空间。

**为什么**：`mod(p, c) - c/2` 将坐标限制在 `[-c/2, c/2)` 范围内，将空间划分为无限多个大小为 `c` 的单元，其中每个单元具有相同的坐标。 SDF 只需要在单个单元内定义。

**代码**：```glsl
// Standard 3D domain repetition (centered version)
// period is the size of each cell
vec3 domainRepeat(vec3 p, vec3 period) {
    return mod(p + period * 0.5, period) - period * 0.5;
}

// Usage example: infinitely repeat a box
float map(vec3 p) {
    vec3 q = domainRepeat(p, vec3(4.0)); // Repeat every 4 units
    return sdBox(q, vec3(0.5));          // One box per cell
}
```> 这个 `pos = mod(pos-2., 4.) -2.;` 就是这个精确的模式 — period=4，offset=2，完美居中。 `p1.x = mod(p1.x-5., 10.) - 5.;` 遵循相同的逻辑（周期=10，以原点为中心）。

### 步骤 2：对称折叠重复（abs-mod 混合）

**什么**：除了 mod 重复之外，使用 `abs()` 使每个单元镜像对称，消除单元边界处的接缝。

**为什么**：普通的“mod”重复在单元格边界处存在坐标不连续性（从“+c/2”跳到“-c/2”），这可能会导致可见的接缝。 `abs(tile - mod(p,tile*2))` 使坐标在每个图块内从 0 到图块到 0 来回折叠，确保边界的连续性（相当于“三角波”）。

**代码**：```glsl
// Symmetric fold (triangle wave mapping)
// tile is the half-period length, full period is tile*2
vec3 symmetricFold(vec3 p, float tile) {
    return abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
}

// Usage: classic tiling fold
vec3 p = from + s * dir * 0.5;
p = abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
```> 核心行 `p = abs(vec3(tile)-mod(p,vec3(tile*2.)));` 就是这种模式。 `tpos.xz=abs(.5-mod(tpos.xz,1.));` 是相同模式的 2D 版本（tile=0.5，period=1）。

### 步骤 3：角域重复（极坐标折叠）

**什么**：将空间划分为绕轴旋转的 N 个相等的扇区，实现万花筒效果。

**为什么**：将坐标转换为极坐标形式后，应用“mod(angle, TAU/N)”将完整的 360 度折叠成单个“TAU/N”扇区。向后旋转坐标使所有扇区共享相同的 SDF。

**代码**：```glsl
// Angular domain repetition
// p: xz plane coordinates, count: repetition count
// Returns rotated coordinates (folded into the first sector)
vec2 pmod(vec2 p, float count) {
    float angle = atan(p.x, p.y) + PI / count;
    float sector = TAU / count;
    angle = floor(angle / sector) * sector;
    return p * rot(-angle);  // rot is a 2D rotation matrix
}

// Usage: 5-fold rotational symmetry
vec3 p1 = p;
p1.xy = pmod(p1.xy, 5.0); // 5-fold symmetry in the xy plane
```> `pmod()` 函数实现了这种模式。另一种“amod()”函数遵循相同的想法，但使用“inout”参数直接修改坐标并返回扇区索引（用于着色变体）。

### 步骤 4：分形域折叠（用于分形迭代）

**什么**：在分形迭代循环中使用 `fract()` 将坐标重复折叠回 `[0,1)` 范围，结合缩放实现自相似结构。

**为什么**： `-1.0 + 2.0*fract(0.5*p+0.5)` 将 p 映射到 `[-1, 1)` 范围（居中的 fract）。每次迭代将空间划分为 8 个子单元（在 3D 中），每个子单元递归地进行相同的操作。与缩放因子“k = s/dot(p,p)”（球形反转）相结合，产生分形层次结构。

**代码**：```glsl
// Core loop of an Apollonian fractal
float map(vec3 p, float s) {
    float scale = 1.0;
    vec4 orb = vec4(1000.0); // Orbit trap for coloring

    for (int i = 0; i < 8; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // Centered fract fold

        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));  // Orbit capture

        float k = s / r2;    // Spherical inversion scaling
        p *= k;
        scale *= k;
    }

    return 0.25 * abs(p.y) / scale; // Distance must be divided by accumulated scale
}
```> `-1.0 + 2.0*fract(0.5*p+0.5)` 等价于 `mod(p+1, 2) - 1`，将 p 映射到 [-1,1)。

### 步骤 5：迭代 abs 折叠（IFS / Kali-set）

**什么**：在循环内重复执行`p = abs(p) - offset`，结合旋转和缩放，生成分形对称结构。

**为什么**：`abs(p)` 将空间折叠到正八分圆，`-offset` 平移原点，然后 `abs()` 再次折叠......每次迭代都会添加另一层对称性。这是迭代函数系统 (IFS) 的一种实现。与旋转相结合，产生极其丰富的分形结构。

**代码**：```glsl
// IFS abs folding fractal
float ifsBox(vec3 p) {
    for (int i = 0; i < 5; i++) {
        p = abs(p) - 1.0;        // Fold + offset
        p.xy *= rot(iTime * 0.3); // Rotation adds complexity
        p.xz *= rot(iTime * 0.1);
    }
    return sdBox(p, vec3(0.4, 0.8, 0.3));
}

// Kali-set variant: uses dot(p,p) scaling
vec2 de(vec3 pos) {
    vec3 tpos = pos;
    tpos.xz = abs(0.5 - mod(tpos.xz, 1.0)); // mod repetition first, then IFS
    vec4 p = vec4(tpos, 1.0);                // w component tracks scaling
    for (int i = 0; i < 7; i++) {
        p.xyz = abs(p.xyz) - vec3(-0.02, 1.98, -0.02);
        p = p * (2.0) / clamp(dot(p.xyz, p.xyz), 0.4, 1.0)
            - vec4(0.5, 1.0, 0.4, 0.0);
        p.xz *= rot(0.416);  // Intra-iteration rotation
    }
    return vec2(length(max(abs(p.xyz)-vec3(0.1,5.0,0.1), 0.0)) / p.w, 0.0);
}
```> 请注意，`de()` 变体使用 `vec4` 的 w 分量来累加缩放因子 (`p.w`)，并且最终距离除以 `p.w` 以保持 SDF 有效性。

### 步骤 6：反射折叠（多面体对称）

**什么**：通过一组反射平面将空间折叠成多面体（例如二十面体）的基本域。

**为什么**：正多面体有多个对称平面。通过“p = p - 2*dot(p,n)*n”沿每个对称平面反射将所有空间折叠成“基本域”（对于二十面体来说是整个多面体的 1/60）。几何只需要在这个基本域内定义。

**代码**：```glsl
// Plane reflection
float pReflect(inout vec3 p, vec3 planeNormal, float offset) {
    float t = dot(p, planeNormal) + offset;
    if (t < 0.0) {
        p = p - (2.0 * t) * planeNormal;
    }
    return sign(t);
}

// Icosahedral folding
void pModIcosahedron(inout vec3 p) {
    // nc is the third fold plane normal (the first two are the xz and yz planes)
    vec3 nc = vec3(-0.5, -cos(PI/5.0), sqrt(0.75 - cos(PI/5.0)*cos(PI/5.0)));
    p = abs(p);          // xz and yz plane reflections
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
}
```> 通过交替“abs()”和“pReflect()”实现完整的二十面体对称群。

### 步骤 7：环形/圆柱形域扭曲 (displaceLoop)

**什么**：将平面空间弯曲成圆柱形或环形拓扑。

**为什么**：`displaceLoop` 将笛卡尔坐标 `(x, z)` 转换为 `(distance_to_center - R, angle)`，将平面“滚动”成半径为 R 的圆柱体/圆环。然后角度尺寸可以经历“amod”以进行角度重复。

**代码**：```glsl
// Toroidal domain warp: bend the xz plane into a torus
vec2 displaceLoop(vec2 p, float radius) {
    return vec2(length(p) - radius, atan(p.y, p.x));
}

// Usage example: architectural ring corridor
vec3 pDonut = p;
pDonut.x += donutRadius;
pDonut.xz = displaceLoop(pDonut.xz, donutRadius);
pDonut.z *= donutRadius; // Unwrap angle to linear length
// Now pDonut is "flattened" ring coordinates, ready for linear repetition
```> `displaceLoop` 函数将建筑场景弯曲成环形结构。

### 步骤 8：一维中心域重复（带有单元 ID）

**什么**：沿一个轴执行居中模重复并返回当前单元格编号。

**为什么**：单元 ID 可用于为每个单元的几何形状分配不同的随机属性（颜色、大小、旋转等），从而打破了完美重复的一致性。

**代码**：```glsl
// 1D centered domain repetition, returns cell index
float pMod1(inout float p, float size) {
    float halfsize = size * 0.5;
    float c = floor((p + halfsize) / size); // Cell index
    p = mod(p + halfsize, size) - halfsize; // Centered local coordinate
    return c;
}

// Usage: repeat along x axis and get cell ID
float cellID = pMod1(p.x, 2.0);
float salt = fract(sin(cellID * 127.1) * 43758.5453); // Random seed
```> 这是一个标准的域重复库函数。一个更简单的“repeat()”函数遵循相同的模式（不返回索引的版本）。

## 常见变体详细信息

### 1. 体积发光渲染

与标准光线行进不同，这不会检查表面撞击。相反，它在每一步都会累积“距离到亮度”的贡献。

**与基本版本的区别**：不需要正常计算或传统着色。每一步都通过“exp(-dist * k)”累积辉光。

**关键修改代码**：```glsl
// Replace hit detection in raymarch with glow accumulation
float acc = 0.0;
float t = 0.0;
for (int i = 0; i < 99; i++) {
    vec3 pos = ro + rd * t;
    float dist = map(pos);
    dist = max(abs(dist), 0.02);     // Prevent division by zero, abs allows passing through surfaces
    acc += exp(-dist * 3.0);          // Adjustable: decay coefficient controls glow sharpness
    t += dist * 0.5;                  // Adjustable: step scale (<1 means denser sampling)
}
vec3 col = vec3(acc * 0.01, acc * 0.011, acc * 0.012);
```> 这种体积发光渲染策略通常用于分形域重复着色器。

### 2. 单轴/双轴选择性重复

仅沿某些轴重复，同时保持其他轴不变。适用于走廊、柱子等定向场景。

**与基础版的区别**：不使用`vec3`全轴重复；仅将 mod 应用于所需的组件。

**关键修改代码**：```glsl
// Repeat only along x and z axes, y axis unrepeated
float map(vec3 pos) {
    vec3 q = pos;
    q.xz = mod(q.xz + 2.0, 4.0) - 2.0; // Only xz repeated
    // q.y retains original value, providing finite height
    return sdBox(q, vec3(0.3, 0.5, 0.3));
}
```### 3.分形分形域折叠（阿波罗型）

使用“fract()”代替“mod()”进行迭代折叠，并结合缩放和轨道捕获来创建分形。

**与基本版本的区别**：在循环中重复应用 fract+scaling，而不是一次性 mod；使用轨道陷阱着色。

**关键修改代码**：```glsl
float scale = 1.0;
for (int i = 0; i < 8; i++) {
    p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // fract fold
    float r2 = dot(p, p);
    float k = 1.2 / r2;                      // Adjustable: scaling parameter
    p *= k;
    scale *= k;
}
return 0.25 * abs(p.y) / scale;
```### 4. 多级嵌套重复

在一个扇区内应用角度重复，然后在每个扇区内应用线性重复，反之亦然。

**与基本版本的区别**：域重复操作是跨多个级别嵌套的，每个级别提供不同的空间组织。

**关键修改代码**：```glsl
// Outer level: angular repetition
float indexX = amod(p.xz, segments); // Divide into N sectors
p.x -= radius;
// Inner level: linear repetition
p.y = repeat(p.y, cellSize);         // Repeat along y axis
// Random seed for each cell
float salt = rng(vec2(indexX, floor(p.y / cellSize)));
```> 这种嵌套通常用于建筑场景着色器。

### 5. 有界域重复（有限重复）

使用“clamp”来限制 mod 单元索引，实现有限的重复次数。

**与基本版本的区别**：使用“clamp”将单元格索引限制为“[-N,N]”，仅重复“2N+1”次。

**关键修改代码**：```glsl
// Finite domain repetition: repeat at most N times along each axis
vec3 domainRepeatLimited(vec3 p, float size, vec3 limit) {
    return p - size * clamp(floor(p / size + 0.5), -limit, limit);
}

// Usage: repeat 5 times along x, 3 times each along y and z
vec3 q = domainRepeatLimited(p, 2.0, vec3(2.0, 1.0, 1.0));
```## 性能优化深入探讨

### 瓶颈 1：分形循环中的高迭代次数

**问题**：当 IFS 或 fract 折叠循环迭代次数过多时，`map()` 函数会变慢，并且在光线行进期间的每一步都会调用 `map()`。

**优化**：
- 减少分形迭代次数（5-8 次迭代通常就足够了）
- 使用`vec4`的w组件来跟踪缩放因子，避免额外的缩放变量
- 在“clamp(dot(p,p), min, max)”中设置上限和下限以防止数值爆炸

### 瓶颈 2：mod 重复导致距离场不准确

**问题**：域重复后的 SDF 在单元边界处可能不准确（相邻单元中的几何形状可能更接近），导致光线行进超调或额外步骤。

**优化**：
- 确保几何形状完全适合单元内（半径 < 周期/2）
- 使用较小的步长因子（`t += d * 0.5` 而不是 `t += d`）
- 对于体积发光渲染，使用“max(abs(d), minDist)”来防止步长过小

### 瓶颈 3：嵌套重复的编译时间

**问题**：多级嵌套域重复和分形循环可能会导致着色器编译时间非常长。

**优化**：
- 在`map()`中预先计算常量表达式
- 避免在循环内使用“normalize()”（改为手动除以长度）
- 使用循环版本进行正常计算而不是展开版本以减少编译器内联

### 瓶颈 4：体积发光渲染的采样率

**问题**：体积发光渲染需要沿光线进行密集采样。

**优化**：
- 随着距离增加步长：`t += dist * (0.3 + t * 0.02)`
- 降低遥远地区的采样密度；距离衰减“exp(-totdist)”自然隐藏了精度损失
- 使用“distfading”乘数逐渐减弱远处的贡献（例如，“fade *= distfading”）

## 组合建议与完整代码

### 1. 域重复 + 光线行进

**最基本、最常见的组合。** 域重复定义了几何空间结构；光线行进处理渲染。这是SDF渲染中最基本的组合。

### 2. 域重复 + 轨道陷阱着色

记录分形迭代循环期间的中间值（例如，“min（orb，abs（p））”），用于为分形结构着色。避免了分形表面上正常计算+照明的高成本。

**组合方法**：```glsl
vec4 orb = vec4(1000.0);
for (...) {
    p = fold(p);
    orb = min(orb, vec4(abs(p), dot(p,p)));
}
// Use orb values for color mapping
vec3 color = mix(vec3(1,0.8,0.2), vec3(1,0.55,0), clamp(orb.y * 6.0, 0.0, 1.0));
```### 3.域重复+环形/极坐标扭曲

首先使用“displaceLoop”将空间弯曲成环形拓扑，然后在展平坐标中执行线性和角度重复。适合创建环形走廊、环形建筑等。

**组合方法**：```glsl
p.xz = displaceLoop(p.xz, R);  // Bend into ring
p.z *= R;                       // Angle to length
amod(p.xz, N);                  // Angular repetition
p.y = repeat(p.y, cellSize);    // Linear repetition
```### 4. 域重复+噪声/随机变体

从单元 ID 生成伪随机数，将变化注入每个重复的单元（大小、旋转、颜色偏移），从而打破均匀性。

**组合方法**：```glsl
float cellID = pMod1(p.x, size);
float salt = fract(sin(cellID * 127.1) * 43758.5453);
// Use salt to modulate geometric parameters
float boxSize = 0.3 + 0.2 * salt;
```### 5.域重复+极坐标螺旋变换

使用 `cartToPolar` / `polarToCart` 坐标变换与 `pMod1` 相结合，沿着螺旋路径重复。适用于DNA双螺旋、弹簧、线等。

**组合方法**：```glsl
p = cartToPolar(p);         // Convert to polar coordinates
p.y *= radius;               // Unwrap angle to length
// Repeat along spiral line
vec2 closest = closestPointOnRepeatedLine(vec2(lead, radius*TAU), p.xy);
p.xy -= closest;             // Local coordinates
```
