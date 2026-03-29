# CSG 布尔运算 — 详细参考

本文档是 [SKILL.md](SKILL.md) 的完整参考手册，包括分步教程、数学推导、变体详细信息和高级用法。

## 用例

- **几何建模**：通过布尔组合（坚果、建筑物、机械零件、有机角色等）从简单的图元（球体、盒子、圆柱体）构建复杂的形状。
- **Ray Marching 场景**：所有基于 SDF 的光线行进渲染都依赖 CSG 来组成场景
- **有机形式**：使用平滑变体（smin/smax）在形状之间创建自然过渡，适合角色建模（蜗牛、大象）、云、地形等。
- **建筑/工业设计**：使用减法来雕刻窗户和门口，使用交叉来切割形状
- **2D SDF Compositing**：同样适用于2D场景（赛博朋克云、UI形状合成等）

## 先决条件

- GLSL基本语法（`vec3`、`float`、`mix`、`clamp`、`min`、`max`）
- SDF（Signed Distance Field）概念：空间中每个点到最近表面的有符号距离，负值表示内部
- 基本 SDF 基元：球体 `length(p) - r`，盒子 `length(max(abs(p)-b, 0.0))`
- 光线行进基础知识：从相机沿视图方向步进，使用 SDF 值确定步长

## 核心原则详细信息

CSG布尔运算的本质是**两个距离场上的每点值运算**：

|运营|数学表达式 |意义|
|------------|----------------|---------|
|联盟| `min(d1, d2)` |取最近的表面，保持两个形状 |
|交叉口| `最大（d1，d2）` |取最远的表面，仅保留重叠|
|减法| `最大（d1，-d2）` |使用 d2 的内部（取反）来切割 d1 |

**硬布尔值**在连接处产生尖锐的边缘。 **平滑布尔值**（平滑最小/最大）在过渡区域引入混合带，将两个形状“融合”在一起。关键参数“k”控制混合带宽：

- 较大的“k”意味着更宽、更平滑的过渡
- 较小的“k”意味着更接近硬布尔锐边
- `k = 0` 退化为硬布尔值

三种主流顺滑配方，各具特色：
1. **多项式**：最常用、计算速度快、自然转换
2. **二次优化**：更紧凑、数学上更优雅
3. **指数**：最平滑的过渡，但计算成本更高

## 详细实施步骤

### 步骤 1：硬布尔运算

**什么**：实现三个基本布尔运算——并、交、减。

**为什么**：这些是所有 CSG 运营的基础。 `min` 选择最近的曲面来实现并集； `max` 选择最远的曲面进行相交；对第二个操作数求反并用第一个操作数取“max”可实现减法（保留 d1 中不在 d2 内的区域）。```glsl
// Union: keep both shapes
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

// Intersection: keep only the overlapping region
float opIntersection(float d1, float d2) {
    return max(d1, d2);
}

// Subtraction: carve d2 out of d1
float opSubtraction(float d1, float d2) {
    return max(d1, -d2);
}
```### 步骤 2：平滑并集 — 多项式版本

**什么**：通过混合过渡实现联合操作，在两个形状之间产生圆形连接。

**为什么**：硬 `min` 在 SDF 交界处产生 C0 连续性（尖锐折痕）。多项式平滑最小值在过渡带内插值，其中 `|d1-d2| < k`，产生 C1 连续性（平滑过渡）。在公式中，“h”是归一化混合因子，“k*h*(1-h)”项确保距离场正确地下降到过渡区域（产生比普通“mix”更准确的距离值）。```glsl
// Polynomial smooth union
// k: blend radius, typical values 0.05~0.5
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}
```### 步骤 3：平滑减法和平滑交集 — 多项式版本

**什么**：将平滑并集方法扩展到减法和交集。

**为什么**：减法 = 与倒置的 SDF 相交；交集 = 反转输入的反转并集。公式中的符号变化反映了这种二元性。请注意，减法使用“d2+d1”（而不是“d2-d1”），因为 d1 在运算中被取反。```glsl
// Smooth subtraction: smoothly carve d2 out of d1
float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

// Smooth intersection: smoothly keep the overlapping region
float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```### 步骤 4：二次优化平滑运算

**什么**：使用更紧凑的二次多项式公式实现 smin/smax。

**为什么**：这个版本在数学上是等效的，但更简洁，分支更少。 `h = max(k - abs(a-b), 0.0)` 直接计算过渡带内的影响，仅当 `|a-b| 时才非零< k`。 `h*h*0.25/k` 是二次校正项。 smax 可以直接通过 smin 的对偶性导出：`smax(a,b,k) = -smin(-a,-b,k)`。```glsl
// Quadratic optimized smooth union
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}

// Quadratic optimized smooth intersection / smooth max
float smax(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// Subtraction via smax
float sSub(float d1, float d2, float k) {
    return smax(d1, -d2, k);
}
```### 步骤 5：基本 SDF 基元

**什么**：定义用于组合的基本形状 SDF。

**为什么**：CSG 需要操作数。球体和盒子是最常见的图元；气缸通常用于钻孔。```glsl
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

float sdCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}
```###第6步：CSG组合进行场景构建

**什么**：将基元与布尔运算结合起来构建复杂的几何图形。

**为什么**：CSG 的力量在于联合。经典示例：将球体与立方体相交会生成圆形立方体，然后减去三个圆柱体会生成坚果形状。```glsl
float mapScene(vec3 p) {
    // Primitives
    float cube = sdBox(p, vec3(1.0));
    float sphere = sdSphere(p, 1.2);
    float cylX = sdCylinder(p.yzx, 2.0, 0.4); // Along X axis
    float cylY = sdCylinder(p.xyz, 2.0, 0.4); // Along Y axis
    float cylZ = sdCylinder(p.zxy, 2.0, 0.4); // Along Z axis

    // CSG combination: (Cube ∩ Sphere) - three cylinders
    float shape = opIntersection(cube, sphere);
    float holes = opUnion(cylX, opUnion(cylY, cylZ));
    return opSubtraction(shape, holes);
}
```### 第 7 步：使用 Smooth CSG 进行有机身体建模

**什么**：使用具有不同 k 值的 smin/smax 将多个椭球体/胶囊混合成有机特征。

**为什么**：不同的身体部位需要不同的混合量 - 大的 k 值用于广泛的连接（躯干-腿部），小 k 值用于精细的细节（眼睛-头部）。这是平滑CSG有机角色建模的核心技术。```glsl
float mapCreature(vec3 p) {
    // Torso
    float body = sdSphere(p, 0.5);

    // Head — larger blend radius
    float head = sdSphere(p - vec3(0.0, 0.6, 0.3), 0.25);
    float d = smin(body, head, 0.15);

    // Limbs — medium blend radius
    float leg = sdCylinder(p - vec3(0.2, -0.5, 0.0), 0.3, 0.08);
    d = smin(d, leg, 0.08);

    // Eye sockets — small blend radius for smooth subtraction
    float eye = sdSphere(p - vec3(0.05, 0.75, 0.4), 0.05);
    d = smax(d, -eye, 0.02);

    return d;
}
```### 步骤 8：光线行进主循环

**什么**：使用球体追踪算法渲染 SDF 场景。

**为什么**：SDF 场景无法使用传统的光栅化进行渲染。需要光线行进：从每个像素投射一条光线，每一步前进当前点到最近表面的距离（即 SDF 值），直到足够接近表面或超出范围。```glsl
float rayMarch(vec3 ro, vec3 rd, float maxDist) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = mapScene(p);
        if (d < SURF_DIST) return t;
        t += d;
        if (t > maxDist) break;
    }
    return -1.0; // No hit
}
```### 步骤9：正常计算和照明

**什么**：通过采用 SDF 的有限差分梯度来计算表面法线，然后应用照明。

**为什么**：SDF的梯度方向是表面法线方向。使用四面体采样仅需要 4 个 SDF 样本，这比中心差分所需的 6 个样本更有效。```glsl
vec3 calcNormal(vec3 pos) {
    vec2 e = vec2(0.001, -0.001);
    return normalize(
        e.xyy * mapScene(pos + e.xyy) +
        e.yyx * mapScene(pos + e.yyx) +
        e.yxy * mapScene(pos + e.yxy) +
        e.xxx * mapScene(pos + e.xxx)
    );
}
```## 常见变体详细信息

### 变体 1：多项式平滑并集（最通用版本）

与基础（二次优化）版本不同，采用“clamp + mix”的形式，使得代码意图更加直观。数学上近似等于二次版本，但在极端情况下过渡曲线略有不同。```glsl
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```### 变体 2：指数平滑并集

**与基本版本的区别**：使用`exp`实现，过渡更平滑（C-无穷连续性 vs 多项式的 C1）。然而，“exp”更贵。适用于地形建模（例如陨石坑）。参数“k”具有不同的含义 - 在指数版本中，较大的“k”会产生更尖锐的转换（与多项式相反）。在 RME4-Crater 中用于火山地形混合。```glsl
float sminExp(float a, float b, float k) {
    float res = exp(-k * a) + exp(-k * b);
    return -log(res) / k;
}
```### 变体 3：通过颜色混合实现平滑操作

**与基本版本的区别**：在几何融合过程中使用相同的混合因子来混合材质颜色。这样，交界处的材料就会自然过渡，而不是呈现出突然的颜色边界。对于有机形状连接处（例如外壳和主体）之间的颜色渐变很有用。```glsl
// vec3 overloaded smax, blending colors simultaneously
vec3 smax(vec3 a, vec3 b, float k) {
    vec3 h = max(k - abs(a - b), 0.0);
    return max(a, b) + h * h * 0.25 / k;
}

// Alternatively, a separated version: returns the blend factor to the caller
float sminWithFactor(float a, float b, float k, out float blend) {
    float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
    blend = h;
    return mix(b, a, h) - k * h * (1.0 - h);
}
// Usage example:
// float blend;
// float d = sminWithFactor(d1, d2, 0.1, blend);
// vec3 color = mix(color2, color1, blend);
```### 变体 4：分层 CSG 建模（建筑/工业场景）

**与基本版本的区别**：不使用平滑变体；相反，使用多级嵌套硬布尔运算来构建精确的几何结构。先加后减的模式——首先用并集构建整体形式，然后用减法雕刻细节（窗户、门口）。常用于建筑建模。```glsl
float sdBuilding(vec3 p) {
    // Step 1: Additive phase — build walls
    float walls = sdBox(p, vec3(1.0, 0.8, 1.0));

    // Step 2: Additive — roof
    vec3 roofP = p;
    roofP.y -= 0.8;
    float roof = sdBox(roofP, vec3(1.2, 0.3, 1.2));
    float d = opUnion(walls, roof);

    // Step 3: Subtractive phase — carve windows
    vec3 winP = abs(p);                  // Exploit symmetry
    winP -= vec3(1.01, 0.3, 0.4);
    float window = sdBox(winP, vec3(0.1, 0.15, 0.12));
    d = opSubtraction(d, window);

    // Step 4: Hollow out the interior
    float hollow = sdBox(p, vec3(0.95, 0.75, 0.95));
    d = opSubtraction(d, hollow);

    return d;
}
```### 变体 5：大规模有机角色建模

**与基本版本的区别**：广泛使用smin/smax（100+调用），针对不同的身体部位使用不同的k值来控制混合量。大 k (0.1~0.3) 用于躯干连接，小 k (0.01~0.05) 用于细节区域。复杂的有机角色可以通过100多个流畅的操作来雕刻出完整的形态。```glsl
float mapCharacter(vec3 p) {
    // Torso — main ellipsoid
    float body = sdEllipsoid(p, vec3(0.5, 0.4, 0.6));

    // Head — large blend, natural transition to neck
    float head = sdEllipsoid(p - vec3(0.0, 0.5, 0.5), vec3(0.25));
    float d = smin(body, head, 0.2);               // Large k: wide blend band

    // Ears — medium blend
    float ear = sdEllipsoid(p - vec3(0.3, 0.6, 0.3), vec3(0.15, 0.2, 0.05));
    d = smin(d, ear, 0.08);

    // Nostrils — small blend for smooth subtraction
    float nostril = sdSphere(p - vec3(0.0, 0.4, 0.7), 0.03);
    d = smax(d, -nostril, 0.02);                   // Small k: fine carving

    return d;
}
```## 性能优化细节

### 1. 包围体加速

CSG 场景中最大的性能瓶颈是“mapScene()”被调用太多次（每帧每像素 MAX_STEPS）。使用 AABB 边界框跳过远处的子场景：```glsl
float mapScene(vec3 p) {
    float d = MAX_DIST;
    // Only compute complex sub-scene when inside bounding sphere
    float bound = length(p - vec3(2.0, 0.0, 0.0)) - 1.5;
    if (bound < d) {
        d = min(d, complexSubScene(p));
    }
    return d;
}
```使用“intersectAABB”针对 AABB 预先测试光线可以跳过无法击中的区域。

### 2. 减少 SDF 样本数量

- 使用四面体采样进行正常计算（4次调用）而不是中心差（6次调用）
- 使用 `t += d * 0.9` 稍微减小步长，防止过冲引起的穿透

### 3. smin/smax 选择

|方法|性能|准确度|推荐用途 |
|--------|-------------|----------|----------------|
|二次优化 |最快|好 |一般首选|
|多项式钳位 |快|好 |当需要单独的混合因子时 |
|指数|慢一点 |最佳|地形，当需要极其平滑的过渡时 |

### 4. 使用 smin 避免 k=0

当“k”为零时，二次优化版本会导致除零错误。始终确保 `k > 0`，或者当 k 接近零时回退到硬布尔值：```glsl
float safeSmin(float a, float b, float k) {
    if (k < 0.0001) return min(a, b);
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;
}
```### 5. 对称性利用

对于对称形状，使用“abs()”折叠坐标并仅定义一侧。对于对称窗户、四肢和其他镜像特征很有用：```glsl
vec3 q = vec3(p.xy, abs(p.z)); // Mirror along Z axis
```## 详细组合建议

### 1.CSG + 域重复

CSG形状可以通过`mod()`或`fract()`在空间中无限重复，适用于机械阵列、建筑栏杆等：```glsl
float mapRepeated(vec3 p) {
    vec3 q = p;
    q.x = mod(q.x + 1.0, 2.0) - 1.0; // Repeat every 2 units along X axis
    return mapSinglePiston(q);
}
```### 2. CSG + 程序置换

在 SDF 结果之上添加噪声位移，以提供平滑的 CSG 形状表面细节纹理，添加流动或有机的外观：```glsl
float mapWithDisplacement(vec3 p) {
    float base = smin(body, limb, 0.1);
    float noise = 0.02 * sin(10.0 * p.x) * sin(10.0 * p.y) * sin(10.0 * p.z);
    return base + noise;
}
```### 3.CSG + 程序纹理

使用 smin 的混合因子不仅可以混合几何体，还可以混合材质 ID 或颜色，从而实现交叉形状材质渐变：```glsl
vec2 mapWithMaterial(vec3 p) {
    float d1 = sdSphere(p, 0.5);
    float d2 = sdBox(p - vec3(0.3), vec3(0.3));
    float blend;
    float d = sminWithFactor(d1, d2, 0.1, blend);
    float matId = mix(1.0, 2.0, blend); // Blend material ID
    return vec2(d, matId);
}
```### 4.CSG + 2D SDF

CSG不限于3D。在 2D 场景中，平滑合并同样可以创建有机形状，例如风格化的云效果：```glsl
float sdCloud2D(vec2 p) {
    float d = sdBox(p, vec2(0.5, 0.1));
    d = opSmoothUnion(d, length(p - vec2(-0.3, 0.1)) - 0.15, 0.1);
    d = opSmoothUnion(d, length(p - vec2(0.1, 0.15)) - 0.12, 0.1);
    d = opSmoothUnion(d, length(p - vec2(0.3, 0.08)) - 0.1, 0.1);
    return d;
}
```### 5.CSG+动画

通过将CSG参数（k值、图元位置、图元半径）绑定到`iTime`，可以实现动态形状变形和混合动画：```glsl
float mapAnimated(vec3 p) {
    float k = 0.1 + 0.15 * sin(iTime);            // Dynamic blend radius
    float r = 0.3 + 0.1 * sin(iTime * 2.0);       // Dynamic radius
    float d1 = sdSphere(p, 0.5);
    float d2 = sdSphere(p - vec3(0.8 * sin(iTime), 0.0, 0.0), r);
    return smin(d1, d2, k);
}
```
