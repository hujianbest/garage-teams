# SDF 正态估计——详细参考

本文档是对[SKILL.md](SKILL.md)的详细补充，包含必备知识、分步讲解、数学推导、变体分析以及完整的组合代码示例。

---

## 先决条件

### GLSL 基础知识

- **矢量类型**：`vec2`/`vec3` 运算，swizzle 语法（`.xyy`、`.yxy`、`.yyx`）
- Swizzle用于法线估计，从`vec2(h, 0.0)`快速构造三轴偏移向量

### 向量微积分

- **梯度概念**：标量场`f(x, y, z)`的梯度`∇f`是指向函数值增长最快方向的向量
- 对于SDF，梯度方向是**外表面法线方向**
- 梯度的数学定义：`∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z)`

### 自卫队概念

- `map(p)` 返回从点 `p` 到最近表面的有符号距离
- 正值 = 在表面之外，负值 = 在内部，零 = 恰好在表面上
- 理想的 SDF 的梯度大小恰好为 1（Eikonal 方程），但实际上，在布尔运算或变形后，这可能会出现偏差

### 数值微分

- **有限差分**近似导数：`f'(x) ≈ (f(x+h) - f(x-h)) / 2h`（中心差）
- 或 `f'(x) ≈ (f(x+h) - f(x)) / h` （前向差分）
- 前向差分精度为 O(h)，中心差分精度为 O(h²)

---

## 详细实施步骤

### 第 1 步：定义 SDF 场景函数

**什么**：创建一个 `map(vec3 p) -> float` 函数，返回空间中任意点到场景表面的有符号距离。

**为什么**：所有正常的估计方法都需要重复调​​用这个函数来对距离场进行采样。法线函数本身并不关心 SDF 形状——它只需要查询空间中不同位置的距离值。```glsl
float map(vec3 p) {
    float d = length(p) - 1.0; // Unit sphere
    // Can compose more SDF primitives
    return d;
}
```### 步骤 2：选择差分方法并实现正规函数

#### 方法 A：前向差分 — 4 个样本

**内容**：在点“p”和三个轴对齐偏移处对 SDF 进行采样，使用差异来构建梯度。

**为什么**：最简单、最直观的方法。需要4个样本（`map(p)`一次+三个偏移量各一次），适合初学者和精度要求较低的性能敏感场景。

**数学推导**：
- `∂f/∂x ≈ (f(x+ε, y, z) - f(x, y, z)) / ε`
- 由于我们在最后进行了“normalize()”，因此常数分母“ε”可以省略
- 因此 `n = 归一化(map(p+εx̂) - map(p),map(p+εŷ) -map(p),map(p+εẑ) -map(p))````glsl
// Classic forward difference
const float EPSILON = 1e-3;

vec3 getNormal(vec3 p) {
    vec3 n;
    n.x = map(vec3(p.x + EPSILON, p.y, p.z));
    n.y = map(vec3(p.x, p.y + EPSILON, p.z));
    n.z = map(vec3(p.x, p.y, p.z + EPSILON));
    return normalize(n - map(p));
}
```#### 方法 B：中心差异 — 6 个样本

**什么**：在每个轴的每个正向和负向上采样一次，取差值。

**原因**：对称采样消除了一阶误差项，将精度从 O(ε) 提高到 O(ε²)。成本为 6 次 SDF 呼叫。

**数学推导**：
- 泰勒展开式：`f(x+ε) = f(x) + εf'(x) + ε²f''(x)/2 + ...`
- `f(x-ε) = f(x) - εf'(x) + ε²f''(x)/2 - ...`
- 减法：`f(x+ε) - f(x-ε) = 2εf'(x) + O(ε³)`
- 消除一阶误差项，精度提高一个阶```glsl
// Compact swizzle notation
vec3 getNormal(vec3 p) {
    vec2 o = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + o.xyy) - map(p - o.xyy),
        map(p + o.yxy) - map(p - o.yxy),
        map(p + o.yyx) - map(p - o.yyx)
    ));
}
```#### 方法 C：四面体技术 — 4 个样本（推荐）

**什么**：沿正四面体的 4 个顶点对 SDF 进行采样，计算加权和以获得梯度。

**为什么**：仅需要 4 个样本（比中心差分少 2 个），但比前向差分更准确、更对称。

**数学推导**：
- 正四面体的 4 个顶点：`(+,+,+)`、`(+,-,-)`、`(-,+,-)`、`(-,-,+)`
- 系数“0.5773 ≈ 1/√3”将顶点归一化到单位球体上
- 加权和`Σ eᵢ·map(p + eᵢ·ε)`相当于4个对称方向的梯度估计
- 由于四面体的完美对称性，误差分布比前向差分更均匀
- 实际精度介于前向差和中心差之间，但只需要 4 个样本```glsl
// Classic tetrahedron technique
vec3 calcNormal(vec3 pos) {
    float eps = 0.0005; // Adjustable: sample offset
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    return normalize(
        e.xyy * map(pos + e.xyy * eps) +
        e.yyx * map(pos + e.yyx * eps) +
        e.yxy * map(pos + e.yxy * eps) +
        e.xxx * map(pos + e.xxx * eps)
    );
}
```### 第 3 步：标准化并应用于照明

**什么**：对梯度向量调用 `normalize()` 以获得后续光照计算的单位法线。

**为什么**：有限差分得到的梯度长度取决于SDF的局部梯度大小。光照计算需要单位向量。对于理想的SDF（梯度幅值为1），归一化几乎不会改变方向，但对于经过布尔运算或变形的SDF，梯度幅值可能会偏离1，而归一化可以确保结果正确。```glsl
// After a raymarching hit
vec3 pos = ro + rd * t;        // Hit point
vec3 nor = calcNormal(pos);    // Surface normal

// Basic Lambertian diffuse
vec3 lightDir = normalize(vec3(1.0, 4.0, -4.0));
float diff = max(dot(nor, lightDir), 0.0);
vec3 col = vec3(0.8) * diff;
```---

## 变体详细信息

### 变体 1：反向偏移正向差值

**与基础版本的区别**：使用中心点减去三个负方向偏移样本，而不是正方向偏移减去中心。功能上相当于前向差分，但代码结构更紧凑。

**原理**：`map(p) - map(p - εx̂)` 相当于 `map(p + εx̂) - map(p)` 的镜像版本。由于我们最后进行了归一化，因此方向没有改变。```glsl
// Reverse offset variant
vec2 noff = vec2(0.001, 0.0);
vec3 normal = normalize(
    map(pos) - vec3(
        map(pos - noff.xyy),
        map(pos - noff.yxy),
        map(pos - noff.yyx)
    )
);
```### 变体 2：自适应 Epsilon（距离缩放）

**与基本版本的差异**：Epsilon 乘以光线行进距离“t”，对远处表面使用较大的偏移（避免浮点噪声），对附近表面使用较小的偏移（保留细节）。

**原理**：光线距离越远，浮点精度越低（因为绝对误差与值的大小成正比）。同时，远处的像素覆盖更大的世界空间区域，并且不需要高精度法线。自适应 epsilon 自然满足这两个要求。

**典型系数**：`0.001 * t`，其中`0.001`可以根据场景复杂程度进行调整。```glsl
// Adaptive epsilon with tetrahedron technique
vec3 calcNormal(vec3 pos, float t) {
    float precis = 0.001 * t; // Adjustable: base coefficient 0.001

    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx)
    );
}
// Usage: vec3 nor = calcNormal(pos, t);
```### 变体 3：大 Epsilon 舍入/抗锯齿技巧

**与基本版本的区别**：故意使用较大的 epsilon（例如，`0.015`），导致法线在几何边缘处“模糊”，产生视觉舍入和抗锯齿效果。

**原理**：epsilon越大，意味着正态采样跨越的空间范围越大。在几何体的锐边处，两侧的 SDF 值变化会被平均，从而导致法线在边缘处平滑过渡，类似于倒角/圆角效果。

**用例**：程序架构、机械零件和其他需要视觉舍入而不修改 SDF 几何形状的场景。```glsl
// Large epsilon rounding technique
vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.015, -0.015); // Intentionally enlarged epsilon
    return normalize(
        e.xyy * map(p + e.xyy) +
        e.yyx * map(p + e.yyx) +
        e.yxy * map(p + e.yxy) +
        e.xxx * map(p + e.xxx)
    );
}
```### 变体 4：反内联循环技巧

**与基础版本的区别**：将四面体的4个样本编写为“for”循环，并使用位操作生成顶点方向，防止GLSL编译器内联“map()”4次，显着减少复杂场景的编译时间。

**原理**：
- GLSL 编译器通常展开小循环和内联函数调用
- 对于复杂的 `map()` 函数（例如数百行），内联 4 次会导致代码膨胀
- `#define ZERO (min(iFrame, 0))` 使循环绑定一个运行时值（尽管实际上它始终为 0），从而防止编译器在编译时展开
- 位运算`(((i+3)>>1)&1)`等在运行时生成4个四面体顶点方向，相当于手写的`e.xyy`，`e.yyx`，`e.yxy`，`e.xxx`

**位操作对应关系**：
|我| `(((i+3)>>1)&1)` | `((i>>1)&1)` | `(i&1)` |方向 |
|---|---|---|---|---|
| 0 | 1 | 0 | 0 | (+,-,-)|
| 1 | 0 | 0 | 1 | (-,-,+) |
| 2 | 0 | 1 | 0 | (-,+,-) |
| 3 | 1 | 1 | 1 | (+,+,+)|```glsl
// Anti-inlining loop trick
#define ZERO (min(iFrame, 0)) // Prevent compile-time constant folding

vec3 calcNormal(vec3 p, float t) {
    vec3 n = vec3(0.0);
    for (int i = ZERO; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3(
            (((i + 3) >> 1) & 1),
            ((i >> 1) & 1),
            (i & 1)
        ) - 1.0);
        n += e * map(p + e * 0.001 * t);
    }
    return normalize(n);
}
```### 变体 5：正常 + 边缘检测（双用途采样）

**与基本版本的差异**：除了中心差异的 6+1 个样本之外，还计算拉普拉斯近似（每轴样本平均值与中心值的偏差）以检测表面不连续性（边缘）。

**原理**：
- 拉普拉斯算子“∇²f = ∂²f/∂x² + ∂²f/∂y² + ∂²f/∂z²”测量局部曲率
- 数值近似：`∂²f/∂x² ≈ (f(x+h) + f(x-h) - 2f(x)) / h²`
- 在表面不连续处（边缘、裂缝），拉普拉斯值出现峰值
- 代码中，“abs(d - 0.5*(d2+d1))”是x轴上的拉普拉斯近似（省略常数因子）
- `pow(edge, 0.55) * 15.0` 是经验对比度调整```glsl
// Normal + edge detection (dual-purpose sampling)
float edge = 0.0;
vec3 normal(vec3 p) {
    vec3 e = vec3(0.0, det * 5.0, 0.0); // det = detail level

    float d1 = de(p - e.yxx), d2 = de(p + e.yxx);
    float d3 = de(p - e.xyx), d4 = de(p + e.xyx);
    float d5 = de(p - e.xxy), d6 = de(p + e.xxy);
    float d  = de(p);

    // Laplacian edge detection: deviation of center value from per-axis averages
    edge = abs(d - 0.5 * (d2 + d1))
         + abs(d - 0.5 * (d4 + d3))
         + abs(d - 0.5 * (d6 + d5));
    edge = min(1.0, pow(edge, 0.55) * 15.0);

    return normalize(vec3(d1 - d2, d3 - d4, d5 - d6));
}
```---

## 性能优化深度分析

### 瓶颈 1：SDF 样本计数

正常估计是光线行进管道中的**第二大 SDF 调用热点**，仅次于行进循环本身。每个像素在触及表面时都会调用一次法线函数，法线函数在内部调用“map()”4~7次。

|方法|样品|准确度|推荐|
|--------|---------|----------|----------------|
|远期差价| 4 | O(ε) |简单的场景|
|反向偏移差| 4 | O(ε) |与forward相同，代码更紧凑 |
|四面体技术| 4 |前部和中央之间| **首选** |
|中心差异| 6 | O(ε²) |当需要对称时 |
|中心差+边缘| 7 | O(ε²) + 额外信息 |当需要边缘检测时 |

**建议**：默认使用四面体技术；仅当出现视觉伪像（例如锯齿状法线）时才切换到中心差异。

### 瓶颈2：编译时间爆炸

复杂的 SDF（例如，具有数百行的“map()”函数）通过普通函数内联 4~6 次可能会导致编译时间从几秒增长到几分钟。

**根本原因**：GLSL 编译器尝试展开小循环和内联函数调用，将 `map()` 代码复制 4~6 次。

**解决方案**：使用反内联循环技巧（变体 4），结合 `#define ZERO (min(iFrame, 0))` 来防止编译器在编译时展开。这仅保留在运行时循环中调用的“map()”代码的一份副本。

### 瓶颈 3：Epsilon 选择

|埃普西隆范围 |效果|
|----------------|--------|
| < 1e-5 |浮点精度不足，法线显示噪声点 |
| 0.0005~0.001| **推荐默认** |
| 0.01 ~ 0.02 |轻微的平滑/圆角效果 |
| > 0.05 |细节丢失，几何边缘过度平滑 |

**最佳实践**：使用自适应 epsilon `eps * t`，其中 `eps ≈ 0.001` 和 `t` 是光线距离。这样可以保留近距离的细节，并避免远距离的浮点噪声。

### 瓶颈 4：避免冗余采样

如果同一位置需要法线和其他信息（例如边缘检测、AO 预估计），请尽可能重复使用 SDF 采样结果。变体 5 就是一个很好的例子：除了用于法线计算的 6 个样本之外，边缘检测只需要 1 个额外的中心样本，与分别计算法线和边缘检测（总共 13 个样本）相比，节省了近一半。

---

## 带有完整代码的组合建议

### 1.普通+软阴影

法线确定表面方向后，从命中点到光源的辅助光线行进将计算软阴影。使用法线来偏移起点以避免自相交：```glsl
float shadow = calcSoftShadow(pos + nor * 0.01, sunDir, 16.0);
```完整的软阴影函数通常如下所示：```glsl
float calcSoftShadow(vec3 ro, vec3 rd, float k) {
    float res = 1.0;
    float t = 0.01;
    for (int i = 0; i < 64; i++) {
        float h = map(ro + rd * t);
        res = min(res, k * h / t);
        if (res < 0.001) break;
        t += clamp(h, 0.01, 0.2);
    }
    return clamp(res, 0.0, 1.0);
}
```### 2. 正常 + 环境光遮挡 (AO)

法线方向定义 AO 的采样半球。随着步长的增加，沿法线对 SDF 进行采样 - 如果实际距离小于预期距离（即附近的几何体被遮挡），则 AO 值会减小：```glsl
float calcAO(vec3 pos, vec3 nor) {
    float occ = 0.0;
    float sca = 1.0;
    for (int i = 0; i < 5; i++) {
        float h = 0.01 + 0.12 * float(i) / 4.0;
        float d = map(pos + nor * h);
        occ += (h - d) * sca;
        sca *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```**参数说明**：
- `0.01 + 0.12 * float(i) / 4.0`：采样步长从0.01到0.13，覆盖近距离遮挡
- `sca *= 0.95`：减少更远样本的权重
- `3.0 * occ`：对比度调整系数

### 3.普通+菲涅尔效应

法线方向和观察方向之间的角度控制菲涅耳反射强度。在掠射角（法线几乎垂直于视角）处，反射最强：```glsl
float fresnel = pow(clamp(1.0 + dot(nor, rd), 0.0, 1.0), 5.0);
col = mix(col, envColor, fresnel);
```**原理**：当表面直接面向观察者时（“rd”指向观察方向，法线指向外侧），“dot(nor, rd)”接近于-1，而在掠射角处接近于0。加 1 将范围移动到 [0, 1]；取 5 次方可增强对比度。

### 4. 法线 + 凹凸贴图

分层在 SDF 法线之上的程序扰动可在不修改几何体的情况下添加表面细节：```glsl
vec3 doBumpMap(vec3 pos, vec3 nor) {
    vec2 e = vec2(0.001, 0.0);
    float bump = texture(iChannel0, pos.xz * 0.5).x;
    float bx = texture(iChannel0, (pos.xz + e.xy) * 0.5).x;
    float bz = texture(iChannel0, (pos.xz + e.yx) * 0.5).x;
    vec3 grad = vec3(bx - bump, 0.0, bz - bump) / e.x;
    return normalize(nor + grad * 0.1); // 0.1 controls bump intensity
}
```**原理**：计算纹理空间中的高度图梯度，并将其添加到几何法线中。 “0.1”控制视觉凹凸强度 - 较大的值使表面显得更粗糙。

### 5.法线+三平面贴图

法向分量的绝对值用作三平面纹理的混合权重，实现无紫外线纹理：```glsl
vec3 triplanar(sampler2D tex, vec3 pos, vec3 nor) {
    vec3 w = pow(abs(nor), vec3(4.0));
    w /= (w.x + w.y + w.z);
    return texture(tex, pos.yz).rgb * w.x
         + texture(tex, pos.zx).rgb * w.y
         + texture(tex, pos.xy).rgb * w.z;
}
```**原理**：
- 法线沿 X 轴指向的面使用 YZ 平面投影
- 法线沿 Y 轴指向的面使用 ZX 平面投影
- 法线沿 Z 轴指向的面使用 XY 平面投影
- `pow(abs(nor), vec3(4.0))` 使混合更加清晰，减少过渡区域的模糊
- 归一化权重 `w /= (w.x + w.y + w.z)` 确保总权重总和为 1