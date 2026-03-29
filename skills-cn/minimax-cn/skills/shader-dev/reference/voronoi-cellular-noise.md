# Voronoi 和蜂窝噪声 — 详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含先决条件、分步说明、变体描述、性能分析和完整的组合代码。

## 先决条件

- **GLSL基本语法**：`vec2/vec3`、`floor/fract`、`dot`、`smoothstep`等内置函数
- **向量数学**：点积、距离计算、向量归一化
- **伪随机哈希函数概念**：输入坐标 -> 伪随机值，确定性但看似随机
- **fBm（分数布朗运动）基础**：多层噪声求和，用于高级变体

## 核心原则详细信息

Voronoi噪声的本质是**空间分区**：将一组特征点分散在2D/3D空间上，每个像素都属于由其最近的特征点定义的“单元”。

**核心算法流程：**

1. 将空间划分为一个整数网格（`floor`），在每个网格单元中放置一个随机偏移的特征点
2. 对于当前像素，搜索周围3x3（2D）或3x3x3（3D）邻域内的所有特征点
3.计算到每个特征点的距离，记录最近距离F1（以及可选的第二最近距离F2）
4. 使用F1、F2或其组合（例如F2-F1）作为输出值，映射到颜色/高度/形状

**关键数学：**
- 距离度量：欧几里德“长度（r）”或“点（r，r）”（平方距离，更快），曼哈顿“abs（r.x）+abs（r.y）”，切比雪夫“max（abs（r.x），abs（r.y））”
- 精确边界距离（两次通过算法）：`dot(0.5*(mr+r), normalize(r-mr))`（垂直平分线投影）
- 圆形边框（调和平均值）：`1/(1/(d2-d1) + 1/(d3-d1))`

## 实现步骤——详细说明

### 步骤 1：哈希函数 — 生成伪随机特征点

**什么**：定义一个哈希函数，将 2D 整数坐标映射到 [0,1] 范围内的伪随机“vec2”。

**为什么**：每个网格单元内的特征点位置需要是确定性的，但看起来是随机的。哈希函数提供了这种“可再现的随机性”。不同的哈希函数会影响分布均匀性和视觉质量。

**代码**：```glsl
// Classic sin-dot hash (concise and efficient, suitable for most scenarios)
vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

// 3D version (for 3D Voronoi)
vec3 hash3(vec3 p) {
    float n = sin(dot(p, vec3(7.0, 157.0, 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

// High-quality integer hash (more uniform distribution, for production-grade noise)
vec3 hash3_uint(vec3 p) {
    uvec3 q = uvec3(ivec3(p)) * uvec3(1597334673U, 3812015801U, 2798796415U);
    q = (q.x ^ q.y ^ q.z) * uvec3(1597334673U, 3812015801U, 2798796415U);
    return vec3(q) / float(0xffffffffU);
}
```### 步骤 2：网格划分和邻域搜索 — F1 距离

**什么**：将输入坐标拆分为整数部分（网格 ID）和小数部分（单元内的位置），迭代 3x3 邻域以计算到所有特征点的距离，并找到最近的距离 F1。

**为什么**：`floor/fract` 将连续空间离散成网格。由于特征点在[0,1]范围内偏移，最近的点只能在当前单元或其8个邻居中，因此3x3搜索涵盖了所有情况。

**代码**：```glsl
// Basic 2D Voronoi — returns (F1 distance, cell ID)
vec2 voronoi(vec2 x) {
    vec2 n = floor(x);   // Current grid coordinate
    vec2 f = fract(x);   // Offset within cell [0,1)

    vec3 m = vec3(8.0);  // (min distance, corresponding hash value) — initialized to large value

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));       // Neighbor offset
        vec2 o = hash2(n + g);                    // Feature point position in that cell [0,1)
        vec2 r = g - f + o;                       // Vector from current pixel to that feature point
        float d = dot(r, r);                      // Squared distance (avoids sqrt)

        if (d < m.x) {
            m = vec3(d, o);                       // Update nearest distance and cell ID
        }
    }

    return vec2(sqrt(m.x), m.y + m.z);  // (distance, ID)
}
```### 步骤 3：F1 + F2 跟踪 — 边缘检测

**什么**：在搜索过程中同时记录最近距离F1和次近距离F2，使用F2-F1提取细胞边界。

**为什么**：F2-F1的值在细胞内部（远离边界）很大，在细胞连接处（两个特征点等距）接近0。这是最常见的 Voronoi 边缘检测方法。

**代码**：```glsl
// F1 + F2 Voronoi — returns vec2(F1, F2)
vec2 voronoi_f1f2(vec2 x) {
    vec2 p = floor(x);
    vec2 f = fract(x);

    vec2 res = vec2(8.0); // res.x = F1, res.y = F2

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 b = vec2(i, j);
        vec2 r = b - f + hash2(p + b);
        float d = dot(r, r); // Can substitute other distance metrics

        if (d < res.x) {
            res.y = res.x;   // Previous F1 becomes F2
            res.x = d;       // Update F1
        } else if (d < res.y) {
            res.y = d;       // Update F2
        }
    }

    res = sqrt(res);
    return res;
    // Edge value = res.y - res.x (F2 - F1)
}
```### 步骤 4：精确边界距离 — 两次通过算法

**什么**：第一遍找到最近的特征点；第二遍计算到所有相邻单元边界的精确距离。

**为什么**：简单的F2-F1只是边界的近似值。对于几何上精确的等距线和平滑的边界渲染，必须计算到垂直平分线的距离。第二遍需要 5x5 的搜索范围以确保几何正确性。

**代码**：```glsl
// Exact border distance Voronoi — returns vec3(border distance, nearest point offset)
vec3 voronoi_border(vec2 x) {
    vec2 ip = floor(x);
    vec2 fp = fract(x);

    // === Pass 1: Find nearest feature point ===
    vec2 mg, mr;
    float md = 8.0;

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        vec2 g = vec2(float(i), float(j));
        vec2 o = hash2(ip + g);
        vec2 r = g + o - fp;
        float d = dot(r, r);

        if (d < md) {
            md = d;
            mr = r;    // Vector to nearest point
            mg = g;    // Grid offset of nearest point
        }
    }

    // === Pass 2: Calculate shortest distance to border ===
    md = 8.0;

    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec2 g = mg + vec2(float(i), float(j));
        vec2 o = hash2(ip + g);
        vec2 r = g + o - fp;

        // Skip self
        if (dot(mr - r, mr - r) > 0.00001)
            // Distance to perpendicular bisector = midpoint projected onto direction vector
            md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
    }

    return vec3(md, mr);
}
```### 步骤 5：特征点动画

**什么**：使特征点随着时间的推移平滑移动，产生有机的动态效果。

**为什么**：静态Voronoi适合纹理贴图，但实时效果通常需要动画。使用 `sin(iTime + 6.2831*hash)` 使每个点在不同的相位上振荡，同时保持在 [0,1] 范围内。

**代码**：```glsl
// Within the neighborhood search loop, replace static hash with animated version:
vec2 o = hash2(n + g);
o = 0.5 + 0.5 * sin(iTime + 6.2831 * o); // Animation: each point has a different phase
vec2 r = g - f + o;
```### 第 6 步：着色和可视化

**内容**：将 Voronoi 距离值映射到颜色、渲染单元格填充、边界线和特征点标记。

**为什么**：不同的映射方法会产生截然不同的视觉效果。距离值可以直接用作灰度，也可以通过调色板功能转换为丰富的颜色。

**代码**：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Must use iTime, otherwise the compiler optimizes away this uniform
    float time = iTime * 1.0;
    vec2 p = fragCoord.xy / iResolution.xy;
    vec2 uv = p * SCALE; // SCALE controls cell density

    // Compute Voronoi
    vec2 c = voronoi(uv);
    float dist = c.x;   // F1 distance
    float id   = c.y;   // Cell ID

    // --- Cell coloring (ID-driven palette) ---
    vec3 col = 0.5 + 0.5 * cos(id * 6.2831 + vec3(0.0, 1.0, 2.0));

    // --- Distance falloff (cell center bright, edges dark) ---
    col *= clamp(1.0 - 0.4 * dist * dist, 0.0, 1.0);

    // --- Border lines (draw black line when distance below threshold) ---
    col -= (1.0 - smoothstep(0.08, 0.09, dist));

    fragColor = vec4(col, 1.0);
}
```## 变体详细说明

### 变体 1：3D Voronoi + fBm Fire

与基础版本的区别：将2D Voronoi扩展到3D空间，多层fBm求和产生体积感，结合黑体辐射调色板渲染火/星云。

关键修改代码：```glsl
#define NUM_OCTAVES 5  // Tunable: fBm layer count

vec3 hash3(vec3 p) {
    float n = sin(dot(p, vec3(7.0, 157.0, 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n);
}

float voronoi3D(vec3 p) {
    vec3 g = floor(p);
    p = fract(p);
    float d = 1.0;

    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++)
    for (int k = -1; k <= 1; k++) {
        vec3 b = vec3(i, j, k);
        vec3 r = b - p + hash3(g + b);
        d = min(d, dot(r, r));
    }
    return d;
}

float fbmVoronoi(vec3 p) {
    vec3 t = vec3(0.0, 0.0, p.z + iTime * 1.5);
    float tot = 0.0, sum = 0.0, amp = 1.0;
    for (int i = 0; i < NUM_OCTAVES; i++) {
        tot += voronoi3D(p + t) * amp;
        p *= 2.0;
        t *= 1.5; // Time frequency differs from spatial frequency -> parallax effect
        sum += amp;
        amp *= 0.5;
    }
    return tot / sum;
}

// Blackbody radiation palette
vec3 firePalette(float i) {
    float T = 1400.0 + 1300.0 * i;
    vec3 L = vec3(7.4, 5.6, 4.4);
    L = pow(L, vec3(5.0)) * (exp(1.43876719683e5 / (T * L)) - 1.0);
    return 1.0 - exp(-5e8 / L);
}
```### 变体 2：圆形边框（三阶 Voronoi）

与基础版本的区别：同时跟踪 F1、F2 和 F3（三个最近距离），使用调和平均公式生成更平滑、更均匀的单元边界，而不是标准 Voronoi 的尖锐交叉点。

关键修改代码：```glsl
float voronoiRounded(vec2 p) {
    vec2 g = floor(p);
    p -= g;
    vec3 d = vec3(1.0); // d.x=F1, d.y=F2, d.z=F3

    for (int y = -1; y <= 1; y++)
    for (int x = -1; x <= 1; x++) {
        vec2 o = vec2(x, y);
        o += hash2(g + o) - p;
        float r = dot(o, o);

        // Maintain top 3 nearest distances simultaneously
        d.z = max(d.x, max(d.y, min(d.z, r))); // F3
        d.y = max(d.x, min(d.y, r));             // F2
        d.x = min(d.x, r);                       // F1
    }

    d = sqrt(d);

    // Harmonic mean formula -> rounded borders
    return min(2.0 / (1.0 / max(d.y - d.x, 0.001)
                    + 1.0 / max(d.z - d.x, 0.001)), 1.0);
}
```### 变体 3：Voronoise（统一噪声-Voronoi 框架）

与基础版本的区别：通过两个参数“u”（抖动量）和“v”（平滑度），在Cell Noise、Perlin Noise和Voronoi之间连续插值。使用加权累加而不是“min()”操作，需要 5x5 搜索范围。

关键修改代码：```glsl
#define JITTER 1.0    // Tunable: 0=regular grid, 1=fully random
#define SMOOTH 0.0    // Tunable: 0=sharp Voronoi, 1=smooth noise

float voronoise(vec2 p, float u, float v) {
    float k = 1.0 + 63.0 * pow(1.0 - v, 6.0); // Smoothness kernel

    vec2 i = floor(p);
    vec2 f = fract(p);

    vec2 a = vec2(0.0);
    for (int y = -2; y <= 2; y++)
    for (int x = -2; x <= 2; x++) {
        vec2 g = vec2(x, y);
        vec3 o = hash3(i + g) * vec3(u, u, 1.0); // u controls jitter
        vec2 d = g - f + o.xy;
        float w = pow(1.0 - smoothstep(0.0, 1.414, length(d)), k);
        a += vec2(o.z * w, w); // Weighted accumulation
    }

    return a.x / a.y;
}

// hash3 needs to return vec3
vec3 hash3(vec2 p) {
    vec3 q = vec3(dot(p, vec2(127.1, 311.7)),
                  dot(p, vec2(269.5, 183.3)),
                  dot(p, vec2(419.2, 371.9)));
    return fract(sin(q) * 43758.5453);
}
```### 变体 4：裂纹纹理（多层递归 Voronoi）

与基础版本的区别：使用扩展的抖动范围生成不规则单元，使用两遍算法精确边界，然后在裂纹路径上叠加 Perlin fBm 扰动。多层递归（旋转+缩放）产生分形裂纹网络。

关键修改代码：```glsl
#define CRACK_DEPTH 3.0    // Tunable: recursion depth
#define CRACK_WIDTH 0.0    // Tunable: crack width
#define CRACK_SLOPE 50.0   // Tunable: crack sharpness

// Extended jitter range makes cell shapes more irregular
float ofs = 0.5;
#define disp(p) (-ofs + (1.0 + 2.0 * ofs) * hash2(p))

// Main loop: multi-layer crack overlay
vec4 O = vec4(0.0);
vec2 U = uv;
for (float i = 0.0; i < CRACK_DEPTH; i++) {
    vec2 D = fbm22(U) * 0.67;           // fBm perturbation of crack paths
    vec3 H = voronoiBorder(U + D);       // Exact border distance
    float d = H.x;
    d = min(1.0, CRACK_SLOPE * pow(max(0.0, d - CRACK_WIDTH), 1.0));
    O += vec4(1.0 - d) / exp2(i);       // Layer weight decay
    U *= 1.5 * rot(0.37);               // Rotate + scale into next layer
}
```### 变体 5：Tileable 3D Worley（云噪声）

与基础版本的区别：通过“mod()”实现域包装以生成无缝平铺的 3D Worley 噪声。与 Perlin-Worley 重新映射相结合以进行体积云渲染。使用高质量整数哈希。

关键修改代码：```glsl
#define TILE_FREQ 4.0  // Tunable: tiling frequency

float worleyTileable(vec3 uv, float freq) {
    vec3 id = floor(uv);
    vec3 p = fract(uv);
    float minDist = 1e4;

    for (float x = -1.0; x <= 1.0; x++)
    for (float y = -1.0; y <= 1.0; y++)
    for (float z = -1.0; z <= 1.0; z++) {
        vec3 offset = vec3(x, y, z);
        // mod() implements domain wrapping -> seamless tiling
        vec3 h = hash3_uint(mod(id + offset, vec3(freq))) * 0.5 + 0.5;
        h += offset;
        vec3 d = p - h;
        minDist = min(minDist, dot(d, d));
    }
    return 1.0 - minDist; // Inverted Worley
}

// Worley fBm (GPU Pro 7 cloud approach)
float worleyFbm(vec3 p, float freq) {
    return worleyTileable(p * freq, freq) * 0.625
         + worleyTileable(p * freq * 2.0, freq * 2.0) * 0.25
         + worleyTileable(p * freq * 4.0, freq * 4.0) * 0.125;
}

// Perlin-Worley remapping
float remap(float x, float a, float b, float c, float d) {
    return (((x - a) / (b - a)) * (d - c)) + c;
}
// cloud = remap(perlinNoise, worleyFbm - 1.0, 1.0, 0.0, 1.0);
```## 性能优化详情

### 1. 在距离比较中避免使用 sqrt

在比较阶段使用“dot(r,r)”（平方距离），仅将“sqrt”作为最终输出。每个像素节省 9 次“sqrt”调用。

### 2.展开 3D Voronoi 循环

GPU 对于深度嵌套循环效率不高。 3D 的 3x3x3 循环可以沿 z 轴手动展开：```glsl
// Instead of 3-level nesting, manually unroll z=-1, 0, 1
for (int j = -1; j <= 1; j++)
for (int i = -1; i <= 1; i++) {
    b = vec3(i, j, -1); r = b - p + hash3(g+b); d = min(d, dot(r,r));
    b.z = 0.0;          r = b - p + hash3(g+b); d = min(d, dot(r,r));
    b.z = 1.0;          r = b - p + hash3(g+b); d = min(d, dot(r,r));
}
```### 3. 最小化搜索范围

- 基本F1：3x3就足够了
- 精确边框/圆形边框：第二遍需要 5x5
- Voronoise（平滑混合）：需要 5x5 来覆盖内核半径
- 扩展抖动（`ofs>0`）：必须使用 5x5
- 不要盲目使用5x5；搜索 16 个额外的单元意味着 16 次额外的哈希计算

### 4.哈希函数选择

- `sin(dot(...))` 哈希：最快，但在某些 GPU 上精度不足
- 纹理查找哈希（`textureLod(iChannel0, ...)`）：高质量但需要纹理资源
- 整数哈希（`uvec3`）：无纹理的高质量，但需要 ES 3.0+

### 5. 多层 fBm 的层数控制

每个额外的 fBm 层都会添加一个完整的 Voronoi 搜索。 3 层通常提供足够的细节，5 层是视觉上限，超过 5 层很少值得性能成本。

## 详细组合建议

### 1. Voronoi + fBm 扰动

使用 fBm 噪声扰乱 Voronoi 输入坐标，产生有机的、不规则的单元形状（如石头纹理、岩浆）：```glsl
vec2 distorted_uv = uv + 0.5 * fbm22(uv * 2.0);
vec2 v = voronoi(distorted_uv * SCALE);
```### 2. Voronoi + 凹凸贴图

使用 Voronoi 距离值作为高度图，通过有限差分计算法线以获得伪 3D 凹凸效果：```glsl
float h0 = voronoiRounded(uv);
float hx = voronoiRounded(uv + vec2(0.004, 0.0));
float hy = voronoiRounded(uv + vec2(0.0, 0.004));
float bump = max(hx - h0, 0.0) * 16.0; // Simple bump value
```### 3. Voronoi + 调色板映射

使用单元格 ID 或距离值来驱动余弦调色板，快速生成丰富的程序颜色：```glsl
vec3 palette(float t) {
    return 0.5 + 0.5 * cos(6.2831 * (t + vec3(0.0, 0.33, 0.67)));
}
col = palette(cellId * 0.1 + iTime * 0.1);
```### 4. Voronoi + Raymarching

在光线行进场景中使用 Voronoi 距离作为 SDF 的一部分来雕刻细胞表面纹理或裂纹效果。

### 5. 多尺度 Voronoi 堆叠

以不同的频率计算多个 Voronoi 层并将它们堆叠以获得丰富的细节。低频层控制大型结构，高频层添加精细细节：```glsl
float detail = voronoiRounded(uv * 6.0);       // Main structure
float fine   = voronoiRounded(uv * 16.0) * 0.5; // Fine detail
float result = detail + fine * detail;           // Stacking (detail modulated by main structure)
```
