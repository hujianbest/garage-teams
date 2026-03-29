# 体素渲染 - 详细参考

> 本文档是对[SKILL.md](SKILL.md)的详细补充，涵盖先决条件、分步教程、数学推导和高级用法。

## 先决条件

### GLSL 基础知识
- GLSL基本语法（统一、变化、内置函数）
- 向量数学：点积、叉积、归一化、反映
- 了解“floor()”、“sign()”、“step()”等步骤函数

### Ray-AABB 交点（Ray-Box 交点）
体素渲染的基础是光线追踪。您需要了解射线“P(t) = O + t * D”如何与轴对齐边界框 (AABB) 相交。 DDA算法本质上是这个测试向整个网格空间的延伸。

### 基本光照模型
- 兰伯特漫反射：`漫反射 = max(dot(normal, lightDir), 0.0)`
- Phong 镜面反射：`镜面反射 = pow(max(dot(reflect(-lightDir, normal), viewDir), 0.0), 光泽)`

### SDF（有符号距离场）基础知识
SDF 函数返回从点到最近曲面的有符号距离（内部为负，外部为正）。在体素渲染中，SDF通常用于定义体素占用：“d < 0.0”表示被占用。

常见的 SDF 原语：```glsl
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}
```SDF布尔运算：
- 联合：`min(d1, d2)`
- 交集：`max(d1, d2)`
- 减法：`max(d1, -d2)`

## 实施步骤

### 第 1 步：相机光线构造

**什么**：将每个像素坐标转换为世界空间射线原点和方向。

**为什么**：体素渲染遵循光线追踪范例，每个像素独立投射光线。屏幕坐标必须首先标准化为 [-1, 1] 范围，然后通过相机参数（焦距、平面矢量）进行转换以构造世界空间光线方向。

**数学推导**：
1. `screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0` 将像素坐标标准化为 [-1, 1]
2.`cameraDir`的z分量控制焦距：较大的值=较小的FOV（更“长焦”）
3.`cameraPlaneV`乘以纵横比校正以确保方形体素不被拉伸
4.最终光线方向=相机前向+屏幕偏移，无需归一化（DDA算法自然处理）

**代码**：```glsl
vec2 screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0;
vec3 cameraDir = vec3(0.0, 0.0, 0.8);  // Tunable: focal length, larger = smaller FOV
vec3 cameraPlaneU = vec3(1.0, 0.0, 0.0);
vec3 cameraPlaneV = vec3(0.0, 1.0, 0.0) * iResolution.y / iResolution.x;
vec3 rayDir = cameraDir + screenPos.x * cameraPlaneU + screenPos.y * cameraPlaneV;
vec3 rayPos = vec3(0.0, 2.0, -12.0);  // Tunable: camera position
```### 步骤 2：DDA 初始化

**什么**：计算射线遍历网格所需的初始参数。

**为什么**：DDA 算法需要预先计算每个轴的步长方向、步长成本以及到第一个边界的距离。这些值在整个遍历过程中逐渐更新，避免了每步的划分。

**关键变量详细信息**：

- **`mapPos = Floor(rayPos)`**：包含射线原点的单元格的网格坐标。 `floor()` 将连续坐标离散化为整数网格。

- **`rayStep = sign(rayDir)`**：每个轴的步进方向。 `sign()` 返回 +1 或 -1，确定射线在该轴上是沿正方向还是负方向前进。

- **`deltaDist = abs(1.0 / rayDir)`**：光线在每个轴上穿过一个完整网格单元的 t 成本。如果光线被归一化（length=1），则直接使用`1.0/rayDir`；当未标准化时，它相当于“abs(vec3(length(rayDir)) / rayDir)”。

- **`sideDist`**：从射线原点到每个轴上的下一个网格边界的 t 距离。公式 `(sign(rayDir) * (mapPos - rayPos) + sign(rayDir) * 0.5 + 0.5) * deltaDist` 计算从射线原点到该轴上下一个边界的距离比率，然后乘以 deltaDist 以获得实际的 t 值。

**代码**：```glsl
ivec3 mapPos = ivec3(floor(rayPos));        // Current grid coordinate
vec3 rayStep = sign(rayDir);                 // Step direction per axis (+1/-1)
vec3 deltaDist = abs(1.0 / rayDir); // t cost to traverse one cell (ray already normalized)
// Initial t distance to next boundary
vec3 sideDist = (sign(rayDir) * (vec3(mapPos) - rayPos) + (sign(rayDir) * 0.5) + 0.5) * deltaDist;
```### 步骤3：DDA遍历循环（无分支版本）

**什么**：逐个单元地遍历网格，检查是否命中。

**为什么**：无分支版本使用 `lessThanEqual` + `min` 向量比较来一次确定最小轴，避免嵌套 if-else 语句并提高 GPU 效率（减少扭曲发散）。

**算法逻辑**：
1.每次迭代首先检查当前cell是否被占用
2.如果没有命中，找到`sideDist`中最小分量对应的轴
3. `lessThanEqual(sideDist.xyz, min(sideDist.yzx, sideDist.zxy))` 生成一个 bvec3，其中最小轴为 true
4. 将 `deltaDist` 添加到该轴的 `sideDist`，并将 `rayStep` 添加到 `mapPos`
5.`mask`记录上一步的轴，后面用于正常计算

**代码**：```glsl
#define MAX_RAY_STEPS 64  // Tunable: maximum traversal steps, affects maximum view distance

bvec3 mask;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    if (getVoxel(mapPos)) break;  // Hit detection

    // Branchless axis selection: choose the axis with smallest sideDist
    mask = lessThanEqual(sideDist.xyz, min(sideDist.yzx, sideDist.zxy));

    sideDist += vec3(mask) * deltaDist;
    mapPos += ivec3(vec3(mask)) * ivec3(rayStep);
}
```**替代形式（步骤版本，常见于紧凑演示）**：```glsl
vec3 mask = step(sideDist.xyz, sideDist.yzx) * step(sideDist.xyz, sideDist.zxy);
sideDist += mask * deltaDist;
mapPos += mask * rayStep;
````step(a, b)` 返回 `a <= b ? 1.0 : 0.0`;乘以两个步长相当于“该轴同时 <= 两个其他轴”，即它是最小轴。

### 步骤 4：体素占用函数

**什么**：判断给定的网格坐标是否被占用。

**为什么**：这是唯一的“场景定义”界面。通过替换此函数，您可以从任何数据源（程序 SDF、高度图、噪声等）生成体素世界。这种设计将场景内容与渲染算法完全解耦。

**设计要点**：
- 输入为整数网格坐标；加0.5得到体素中心点
- 返回布尔值（简单版本）或材质 ID（高级版本）
- 可以在内部使用 SDF、噪声函数或纹理采样的任意组合
- 性能关键：每个 DDA 步骤都会调用此函数一次，因此请保持简洁

**代码**：```glsl
// Basic version: solid cube (use this when user requests a "voxel cube")
// NOTE: getVoxel receives ivec3, but internal calculations must all use float!
bool getVoxel(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);  // ivec3 → vec3 conversion (required!)
    float d = sdBox(p, vec3(6.0));  // Solid 12x12x12 block
    return d < 0.0;
}

// SDF boolean version: sphere carving out a block (keeping only edges)
bool getVoxelCarved(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);
    float d = max(-sdSphere(p, 7.5), sdBox(p, vec3(6.0)));  // box ∩ ¬sphere
    return d < 0.0;
}

// Advanced version: heightmap terrain with material IDs
// NOTE: Two correct approaches:
// Approach 1: Use vec3 parameter (recommended)
int getVoxelMaterial(vec3 c) {
    float height = getTerrainHeight(c.xz);
    if (c.y < height) return 1;       // Ground (c.y is float)
    if (c.y < height + 4.0) return 7;  // Tree trunk
    return 0;                          // Air
}

// Approach 2: Use ivec3 parameter (requires explicit conversion)
int getVoxelMaterial(ivec3 c) {
    vec3 p = vec3(c);  // ivec3 → vec3 conversion (required!)
    float height = getTerrainHeight(p.xz);
    if (float(c.y) < height) return 1;       // int → float comparison
    if (float(c.y) < height + 4.0) return 7; // int → float comparison
    return 0;
}
```### 步骤 5：面部阴影（普通 + 底色）

**什么**：根据被击中面的法线方向为不同的面分配不同的亮度级别。

**为什么**：这是最简单的体素着色方法 - 三种不同的面部亮度产生经典的“我的世界风格”视觉效果。无需额外的照明计算；仅面部方向就可以提供差异化​​。

**原理**：
- `mask`记录最后一个DDA步骤的轴
- 法线=步进轴的反向：`-mask * rayStep`
- X 轴面（侧面）最暗，Y 轴面（顶部/底部）最亮，Z 轴面（前/后）中等亮度
- 这种固定的三值着色模拟头顶照明下的基本照明

**代码**：```glsl
// Face normal derived directly from mask
vec3 normal = -vec3(mask) * rayStep;

// Three faces with different brightness
vec3 color;
if (mask.x) color = vec3(0.5);   // Side face (X axis) darkest
if (mask.y) color = vec3(1.0);   // Top face (Y axis) brightest
if (mask.z) color = vec3(0.75);  // Front/back face (Z axis) medium

fragColor = vec4(color, 1.0);
```### 步骤 6：精确的击球位置和面部 UV

**什么**：计算光线与体素表面的精确交点，以及该面内的 UV 坐标。

**为什么**：精确的交点用于纹理映射和AO插值，而不仅仅是网格坐标。面 UV 在单个体素面内提供连续坐标（0 到 1）——纹理映射和平滑 AO 的基础。

**数学推导**：
1.`sideDist - deltaDist`后退一步得到被击中面的t值
2. `dot(sideDist - deltaDist, mask)` 选择命中轴的 t
3.`hitPos = rayPos + rayDir * t`给出精确的交点
4. `uvw = hitPos - mapPos` 给出体素局部坐标 [0,1]^3
5、将uvw投影到击打面的两个切轴上得到UV：
   - 如果 X 面被击中，UV = (uvw.y, uvw.z)
   - 如果Y面被击中，UV = (uvw.z, uvw.x)
   - 如果Z面被击中，UV = (uvw.x, uvw.y)
   - `dot(mask * uvw.yzx, vec3(1.0))` 巧妙地使用 mask 来选择正确的组件

**代码**：```glsl
// Precise t value: step back one step using sideDist
float t = dot(sideDist - deltaDist, vec3(mask));
vec3 hitPos = rayPos + rayDir * t;

// Face UV (for texturing, AO interpolation)
vec3 uvw = hitPos - vec3(mapPos);  // Voxel-local coordinates [0,1]^3
vec2 uv = vec2(dot(vec3(mask) * uvw.yzx, vec3(1.0)),
               dot(vec3(mask) * uvw.zxy, vec3(1.0)));
```### 步骤 7：邻近体素环境光遮挡 (AO)

**内容**：对命中面周围的 8 个相邻体素（4 个边 + 4 个角）进行采样，计算每个顶点的遮挡值，然后进行双线性插值。

**为什么**：这是 Minecraft 风格的平滑光照的核心技术。当相邻体素出现在边缘或角落时，这些顶点区域应该显得更暗。该 AO 不需要额外的光线追踪——它完全基于邻居查询，计算成本低且结果良好。

**算法细节**：
1.对于被击打面的每个顶点，检查相邻的2条边和1个角
2.`vertexAo(side,corner)`公式：`(side.x + side.y + max(corner, side.x * side.y)) / 3.0`
   - `side.x * side.y`：当两个边缘都被占用时，即使角落是空的，也应该有完全遮挡（防止漏光）
   - `max(corner, side.x * side.y)`：取角和边积中较大的一个
3. 将 4 个顶点 AO 值存储在 vec4 中
4.使用面UV进行双线性插值以获得连续的AO值
5.`pow(ao, gamma)`控制AO对比度

**代码**：```glsl
// Per-vertex AO: two edges + one corner
float vertexAo(vec2 side, float corner) {
    return (side.x + side.y + max(corner, side.x * side.y)) / 3.0;
}

// Sample AO for 4 vertices of a face
vec4 voxelAo(vec3 pos, vec3 d1, vec3 d2) {
    vec4 side = vec4(
        getVoxel(pos + d1), getVoxel(pos + d2),
        getVoxel(pos - d1), getVoxel(pos - d2));
    vec4 corner = vec4(
        getVoxel(pos + d1 + d2), getVoxel(pos - d1 + d2),
        getVoxel(pos - d1 - d2), getVoxel(pos + d1 - d2));
    vec4 ao;
    ao.x = vertexAo(side.xy, corner.x);
    ao.y = vertexAo(side.yz, corner.y);
    ao.z = vertexAo(side.zw, corner.z);
    ao.w = vertexAo(side.wx, corner.w);
    return 1.0 - ao;
}

// Bilinear interpolation using face UV
vec4 ambient = voxelAo(mapPos - rayStep * mask, mask.zxy, mask.yzx);
float ao = mix(mix(ambient.z, ambient.w, uv.x), mix(ambient.y, ambient.x, uv.x), uv.y);
ao = pow(ao, 1.0 / 3.0);  // Tunable: gamma correction controls AO intensity
```### 第 8 步：DDA 阴影射线

**内容**：从命中点向光源投射第二条 DDA 射线以检测遮挡。

**原因**：重复使用相同的 DDA 算法即可实现硬阴影，而无需额外的光线追踪基础设施。阴影光线通常使用较少的步骤（例如 16-32）来节省性能。

**实施细节**：
- 原点必须偏移 `normal * 0.01` 以避免自相交
- 阴影光线只需要确定0/1遮挡（硬阴影），不需要精确的相交
- 返回 0.0（被遮挡）或 1.0（未被遮挡）
- 步数可以低于主射线，因为只需要遮挡检测

**代码**：```glsl
#define MAX_SHADOW_STEPS 32  // Tunable: shadow ray steps

float castShadow(vec3 ro, vec3 rd) {
    vec3 pos = floor(ro);
    vec3 ri = 1.0 / rd;
    vec3 rs = sign(rd);
    vec3 dis = (pos - ro + 0.5 + rs * 0.5) * ri;

    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        if (getVoxel(ivec3(pos))) return 0.0;  // Occluded
        vec3 mm = step(dis.xyz, dis.yzx) * step(dis.xyz, dis.zxy);
        dis += mm * rs * ri;
        pos += mm * rs;
    }
    return 1.0;  // Unoccluded
}

// Usage during shading
vec3 sundir = normalize(vec3(-0.5, 0.6, 0.7));
float shadow = castShadow(hitPos + normal * 0.01, sundir);
float diffuse = max(dot(normal, sundir), 0.0) * shadow;
```## 变体详细信息

### 变体 1：发光体素（发光累积）

**与基础版本的区别**：在DDA遍历过程中，每一步都会累积基于距离的发光值，即使没有命中也会产生半透明的发光效果。

**用例**：霓虹灯效果、能量场、粒子云、科幻风格

**原理**：使用SDF距离场，体素表面附近的辉光贡献较大（距离小→大1/d²），远处的辉光贡献较小。累积所有步骤的贡献会产生连续的发光场。

**关键参数**：
- `0.015`：发光强度系数 — 越大 = 越亮
- `0.01`：最小距离阈值 — 防止被零除并控制发光“清晰度”
- 发光颜色`vec3(0.4, 0.6, 1.0)`：可以根据距离或材料而变化

**代码**：```glsl
float glow = 0.0;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    float d = sdSomeShape(vec3(mapPos));  // Distance to nearest surface
    glow += 0.015 / (0.01 + d * d);      // Tunable: glow falloff
    if (d < 0.0) break;
    // ... normal DDA stepping ...
}
vec3 col = baseColor + glow * vec3(0.4, 0.6, 1.0); // Overlay glow color
```### 变体 2：圆形体素（体素内 SDF 细化）

**与基础版本的区别**：DDA命中后，在体素内执行一些SDF射线行进步骤，渲染圆形块而不是完美的立方体。

**用例**：有机风格体素、积木/乐高效果、赤壁角色

**原理**：DDA命中后，我们知道射线进入了哪个体素，但里面的精确形状是由SDF定义的。从体素入口点开始 SDF 射线行进，使用“sdRoundedBox”定义圆形立方体，行进到表面产生精确的圆形交点和法线。

**关键参数**：
- `w`（圆角半径）：0.0 = 完美立方体，0.5 = 球体
- 6 个内部行进步骤通常足以收敛
- `hash31(mapPos)` 随机化每个体素的角半径，增加多样性

**代码**：```glsl
// Refine inside the voxel after DDA hit
float id = hash31(mapPos);
float w = 0.05 + 0.35 * id;  // Tunable: corner radius

float sdRoundedBox(vec3 p, float w) {
    return length(max(abs(p) - 0.5 + w, 0.0)) - w;
}

// Start 6-step SDF march from voxel entry
vec3 localP = hitPos - mapPos - 0.5;
for (int j = 0; j < 6; j++) {
    float h = sdRoundedBox(localP, w);
    if (h < 0.025) break;  // Hit rounded surface
    localP += rd * max(0.0, h);
}
```### 变体 3：混合 SDF-体素遍历

**与基本版本的区别**：远离表面时使用 SDF 球体追踪（大步长），靠近表面时切换到精确的 DDA 体素遍历。大大提高空旷区域的穿行效率。

**用例**：大型开放世界、长距离体素地形、需要高视距的场景

**原理**：
1. 在远离任何体素表面的开放区域，SDF 值很大，允许球体追踪一步跳过大距离
2. 当SDF值接近`sqrt(3) * voxelSize`（体素对角线长度）时，我们可能即将进入一个体素区域
3.切换到DDA以确保没有体素被跳过
4. 如果DDA发现光线离开了密集区域（SDF值再次增加），则切换回球体跟踪

**关键参数**：
- `VOXEL_SIZE`：体素尺寸
- `SWITCH_DIST = VOXEL_SIZE * 1.732`：切换阈值，sqrt(3) 是体素对角线安全系数

**代码**：```glsl
#define VOXEL_SIZE 0.0625       // Tunable: voxel size
#define SWITCH_DIST (VOXEL_SIZE * 1.732)  // sqrt(3) * voxelSize

bool useVoxel = false;
for (int i = 0; i < MAX_STEPS; i++) {
    vec3 pos = ro + rd * t;
    float d = mapSDF(useVoxel ? voxelCenter : pos);

    if (!useVoxel) {
        t += d;
        if (d < SWITCH_DIST) {
            useVoxel = true;              // Switch to DDA
            voxelPos = getVoxelPos(pos);
        }
    } else {
        if (d < 0.0) { /* hit */ break; }
        if (d > SWITCH_DIST) {
            useVoxel = false;             // Switch back to SDF
            t += d;
            continue;
        }
        // DDA step one cell
        vec3 exitT = (voxelPos - ro * ird + ird * VOXEL_SIZE * 0.5);
        // ... select minimum axis and advance ...
    }
}
```### 变体 4：体素锥追踪

**与基本版本的区别**：构建体素的多级 mipmap 层次结构（例如，64→32→16→8→4→2），从命中点投射锥形光线，随着距离的增加采样更粗糙的 LOD 级别，实现漫反射/镜面全局照明。

**用例**：高质量全局照明、彩色间接照明、动态场景的实时 GI

**原理**：
1. 预先计算体素数据的 mipmap 级别（每级别分辨率减半）
2. 从击中点向正常半球投射多条锥形射线（通常为 5-7 个锥形）
3. 每个圆锥体的直径在遍历过程中随着距离线性增加
4. 直径映射到 mipmap 级别：`lod = log2(diameter)`
5.对对应的mipmap级别进行采样
6.前后合成累积光照和遮挡

**关键参数**：
- `coneRatio`：锥角 — 漫反射使用宽锥体 (~1.0)，镜面反射使用窄锥体 (~0.1)
- 58步是常见的平衡值
- `voxelFetch(sp, lod)` 需要自定义 mipmap 查询函数

**代码**：```glsl
// Cone tracing: cast a cone-shaped ray along direction d
vec4 traceCone(vec3 origin, vec3 dir, float coneRatio) {
    vec4 light = vec4(0.0);
    float t = 1.0;
    for (int i = 0; i < 58; i++) {
        vec3 sp = origin + dir * t;
        float diameter = max(1.0, t * coneRatio);  // Cone diameter
        float lod = log2(diameter);                  // Corresponding mipmap level
        vec4 sample = voxelFetch(sp, lod);           // LOD sample
        light += sample * (1.0 - light.w);           // Front-to-back compositing
        t += diameter;
    }
    return light;
}
```### 变体 5：PBR 光照 + 多次反射

**与基础版本的区别**：使用 GGX BRDF 而不是 Lambert，支持金属/粗糙度材质参数，并投射第二条 DDA 射线进行反射。

**用例**：逼真的体素渲染、金属/玻璃材料、建筑可视化

**原理**：
1. GGX (Trowbridge-Reitz) 微面模型提供物理上正确的光分布
2. 粗糙度参数控制镜面锐度：0.0 = 完美镜面，1.0 = 完全漫反射
3. Schlick菲涅尔近似：`F = F0 + (1 - F0) * (1 - cos(theta))^5`
4. 反射光线重用了“castRay”函数，减少了步数（通常 64 步就足够了）
5.多次反弹反射可以递归调用，但通常1-2次反弹就足够了

**关键参数**：
- `粗糙度`: 粗糙度 [0, 1]
- `F0 = 0.04`：非金属的基本反射率
- 反射光线 64 个步骤（比主光线少以节省性能）

**代码**：```glsl
// GGX diffuse term
float ggxDiffuse(float NoL, float NoV, float LoH, float roughness) {
    float FD90 = 0.5 + 2.0 * roughness * LoH * LoH;
    float a = 1.0 + (FD90 - 1.0) * pow(1.0 - NoL, 5.0);
    float b = 1.0 + (FD90 - 1.0) * pow(1.0 - NoV, 5.0);
    return a * b / 3.14159;
}

// Reflection ray - needs a separate shading function to handle HitInfo
vec3 shadeHit(HitInfo h, vec3 rd, vec3 sunDir, vec3 skyColor) {
    if (!h.hit) return skyColor;
    vec3 matCol = getMaterialColor(h.mat, h.uv);
    float diff = max(dot(h.normal, sunDir), 0.0);
    return matCol * diff;
}

vec3 rd2 = reflect(rd, normal);
HitInfo reflHit = castRay(hitPos + normal * 0.001, rd2, 64);
vec3 reflColor = shadeHit(reflHit, rd2, sunDir, skyColor);

// Schlick Fresnel blending
float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(normal, -rd), 0.0), 5.0);
col += fresnel * reflColor;
```## 深入的性能优化

### 主要瓶颈

1. **DDA循环步数**：每个像素需要遍历数十到数百个单元——最大的性能成本。步数与场景大小和开放程度成正比。

2. **体素查询函数**：每步调用一次`getVoxel()`；如果使用噪声/纹理，纹理获取开销会很大。程序 SDF 函数的复杂性直接影响帧速率。

3. **AO 邻居采样**：每个生命点需要 8 个额外的 `getVoxel()` 查询。对于简单的场景来说是可以管理的，但是对于复杂的“getVoxel”，这 8 个查询可能会超出主要的遍历成本。

4. **Shadow Rays**：相当于第二次完整的 DDA 遍历。双遍历使像素着色器负担加倍。

### 优化技术

####提前退出
当`mapPos`超出场景边界时立即中断，避免在无意义的空间中继续遍历：```glsl
if (any(lessThan(mapPos, vec3(-GRID_SIZE))) || any(greaterThan(mapPos, vec3(GRID_SIZE)))) break;
```#### 减少阴影步数
阴影光线只需要确定遮挡——16-32步通常就足够了。不需要与主射线相同的步数：```glsl
#define MAX_SHADOW_STEPS 32  // Instead of MAX_RAY_STEPS of 128
```#### 基于距离的质量缩放
使用高步数进行近距离精确遍历，使用低步数或 LOD 进行远距离精确遍历。根据屏幕像素大小动态调整步数限制。

#### 混合遍历
对开放区域中的大台阶使用 SDF 球体追踪，在表面附近切换到 DDA（请参阅变体 3）。大场景下可减少80%以上的遍历步骤。

#### 避免循环内的复杂计算
材质查询、AO、法线等都是在命中后才完成。遍历循环应该只执行最简单的占用检测。

#### 利用 GPU 纹理硬件
用纹理采样（`texelFetch`）替换程序体素查询。 3D 纹理可以存储预先计算的体素数据，并且在硬件上对缓存友好。

#### 时间积累
多帧累积——每帧只需要少量样本，结合重投影以获得低噪声结果。适合需要大量光线的场景（GI、软阴影）。

## 完整的组合代码示例

### 程序噪声地形
在 `getVoxel()` 中使用 FBM/Perlin 噪声来生成高度图，产生 Minecraft 风格的无限地形：```glsl
// Recommended approach: use vec3 parameter (simple, no type conversion issues)
int getVoxel(vec3 c) {
    // FBM noise heightmap
    float height = 0.0;
    float amp = 8.0;
    float freq = 0.05;
    vec2 xz = c.xz;
    for (int i = 0; i < 4; i++) {
        height += amp * noise(xz * freq);
        amp *= 0.5;
        freq *= 2.0;
    }

    if (c.y > height) return 0;           // Air
    if (c.y > height - 1.0) return 1;     // Grass
    if (c.y > height - 4.0) return 2;     // Dirt
    return 3;                              // Stone
}

// ivec3 parameter version (requires type conversion)
int getVoxel(ivec3 c) {
    vec3 p = vec3(c);  // ivec3 → vec3 conversion
    float height = 0.0;
    float amp = 8.0;
    float freq = 0.05;
    // NOTE: p.xz returns vec2, must pass vec2 version of noise!
    // If noise only has vec3 version, use noise(vec3(p.xz * freq, 0.0))
    vec2 xz = p.xz;
    for (int i = 0; i < 4; i++) {
        height += amp * noise(xz * freq);
        amp *= 0.5;
        freq *= 2.0;
    }

    if (float(c.y) > height) return 0;           // int → float comparison
    if (float(c.y) > height - 1.0) return 1;    // int → float comparison
    if (float(c.y) > height - 4.0) return 2;    // int → float comparison
    return 3;
}
```### 纹理映射
命中后使用面部 UV 采样纹理，实现复古像素艺术风格：```glsl
// During the shading stage
vec2 texUV = hit.uv;
// 16x16 pixel texture atlas
int tileX = mat % 4;
int tileY = mat / 4;
vec2 atlasUV = (vec2(tileX, tileY) + texUV) / 4.0;
vec3 texCol = texture(iChannel0, atlasUV).rgb;
col *= texCol;
```### 大气散射/体积雾
在DDA遍历过程中累积介质密度，实现体积光照和雾效果：```glsl
float fogAccum = 0.0;
vec3 fogColor = vec3(0.0);
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    // ... DDA stepping ...
    float density = getDensity(mapPos);  // Atmospheric density
    if (density > 0.0) {
        float dt = length(vec3(mask) * deltaDist);  // Current step size
        fogAccum += density * dt;
        // Volumetric light: compute lighting within fog
        float shadowInFog = castShadow(vec3(mapPos) + 0.5, sunDir);
        fogColor += density * dt * shadowInFog * sunColor * exp(-fogAccum);
    }
    if (getVoxel(mapPos) > 0) break;
}
// Apply fog effect
col = col * exp(-fogAccum) + fogColor;
```### 水面渲染（体素水场景）
包含表面波反射、水下折射、沙子和海藻的完整体素水场景：```glsl
float waterY = 0.0;

// Underwater voxel scene (sand + seaweed)
// IMPORTANT: c.xz returns vec2, which only has .x/.y components — never use .z!
int getVoxel(vec3 c) {
    float sandHeight = -3.0 + 0.5 * sin(c.x * 0.3) * cos(c.z * 0.4);
    if (c.y < sandHeight) return 1;      // Sand interior
    if (c.y < sandHeight + 1.0) return 2; // Sand surface
    // Seaweed
    float grassHash = fract(sin(dot(floor(c.xz), vec2(12.9898, 78.233))) * 43758.5453);
    if (grassHash > 0.85 && c.y >= sandHeight + 1.0 && c.y < sandHeight + 1.0 + 3.0 * grassHash) {
        return 3;
    }
    return 0;
}

// Check if ray intersects water surface
float tWater = (waterY - ro.y) / rd.y;
bool hitWater = tWater > 0.0 && (tWater < hit.t || !hit.hit);

if (hitWater) {
    vec3 waterPos = ro + rd * tWater;
    vec3 waterNormal = vec3(0.0, 1.0, 0.0);
    // NOTE: waterPos.xz is vec2, access with .x/.y (not .x/.z)
    vec2 waveXZ = waterPos.xz;  // vec2: waveXZ.x = worldX, waveXZ.y = worldZ
    waterNormal.x += 0.05 * sin(waveXZ.x * 3.0 + iTime);
    waterNormal.z += 0.05 * cos(waveXZ.y * 2.0 + iTime * 0.7);
    waterNormal = normalize(waterNormal);

    // Fresnel
    float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(waterNormal, -rd), 0.0), 5.0);

    // Reflection
    vec3 reflDir = reflect(rd, waterNormal);
    HitInfo reflHit = castRay(waterPos + waterNormal * 0.01, reflDir, 64);
    vec3 reflCol = reflHit.hit ? getMaterialColor(reflHit.mat, reflHit.uv) : skyColor;

    // Refraction (underwater voxels: sand, seaweed)
    vec3 refrDir = refract(rd, waterNormal, 1.0 / 1.33);
    HitInfo refrHit = castRay(waterPos - waterNormal * 0.01, refrDir, 64);
    vec3 refrCol;
    if (refrHit.hit) {
        vec3 matCol = getMaterialColor(refrHit.mat, refrHit.uv);
        // Underwater color attenuation (bluer with distance)
        float underwaterDist = length(refrHit.pos - waterPos);
        refrCol = mix(matCol, vec3(0.0, 0.15, 0.3), 1.0 - exp(-0.1 * underwaterDist));
    } else {
        refrCol = vec3(0.0, 0.1, 0.3);  // Deep water color
    }

    col = mix(refrCol, reflCol, fresnel);
    col = mix(col, vec3(0.0, 0.3, 0.5), 0.2);
}
```### 全局照明（蒙特卡罗半球采样）
对漫反射间接照明使用随机半球方向采样：```glsl
vec3 indirectLight = vec3(0.0);
int numSamples = 4;  // Few samples per frame, accumulate across frames
for (int s = 0; s < numSamples; s++) {
    // Cosine-weighted hemisphere sampling
    vec2 xi = hash22(vec2(fragCoord) + float(iFrame) * 0.618 + float(s));
    float cosTheta = sqrt(xi.x);
    float sinTheta = sqrt(1.0 - xi.x);
    float phi = 6.28318 * xi.y;

    vec3 sampleDir = cosTheta * normal
                   + sinTheta * cos(phi) * tangent
                   + sinTheta * sin(phi) * bitangent;

    HitInfo giHit = castRay(hitPos + normal * 0.01, sampleDir, 32);
    if (giHit.hit) {
        vec3 giColor = getMaterialColor(giHit.mat, giHit.uv);
        float giDiff = max(dot(giHit.normal, sunDir), 0.0);
        indirectLight += giColor * giDiff;
    } else {
        indirectLight += skyColor;
    }
}
indirectLight /= float(numSamples);
col += matCol * indirectLight * 0.5;  // Indirect light contribution
```
