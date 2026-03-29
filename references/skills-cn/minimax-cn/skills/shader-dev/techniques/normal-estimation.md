## WebGL2 适配要求

**重要：GLSL 类型严格警告**：
- GLSL 是一种强类型语言，**没有“字符串”类型**；禁止使用字符串类型
- 常见非法类型：`string`、`int`（只能使用`int`文字，不能将变量类型声明为`int`）
- vec2/vec3/vec4 之间不能隐式转换；需要显式构造
- 浮点精度：`highp float`（推荐）、`mediump float`、`lowp float`

本文档中的代码模板使用ShaderToy GLSL风格。生成独立 HTML 页面时，必须适应 WebGL2：

- 使用`canvas.getContext("webgl2")`
- 着色器第一行：`#version 300 es`，在片段着色器中添加` precision highp float;`
- 顶点着色器：`attribute` -> `in`、`variing` -> `out`
- 片段着色器：`variing` -> `in`、`gl_FragColor` -> 自定义`out vec4 fragColor`、`texture2D()` -> `texture()`
- ShaderToy 的 `void mainImage(out vec4 fragColor, in vec2 fragCoord)` 必须适应标准的 `void main()` 入口点

# SDF 正态估计

## 用例

- 光线行进渲染管道中的光照计算（漫反射、镜面反射、菲涅耳等）
- 任何基于 SDF 距离场的 3D 场景（分形、参数化曲面、布尔几何、程序地形）
- 边缘检测和轮廓渲染（拉普拉斯值作为正常采样的副产品）
- 环境光遮挡 (AO) 计算的先决条件

## 核心原则

SDF `nabla f(p)` 的梯度指向距离增加最快的方向，即向外的表面法线。数值微分近似梯度：

$$\vec{n} = \text{标准化}\left(\nabla f(p)\right)$$

三个主要策略：

|方法|样品|准确度|推荐|
|--------|---------|----------|----------------|
|远期差价| 4 | O(ε) |简单的场景|
|中心差异| 6 | O(epsilon^2) |当需要对称时 |
| **四面体法** | **4** | **两者之间** | **首选** |

关键参数epsilon：常用`0.0005 ~ 0.001`；对于高级场景，乘以光线距离“t”以进行自适应缩放。

## 实施步骤

### 第 1 步：定义 SDF 场景函数```glsl
float map(vec3 p) {
    float d = length(p) - 1.0; // unit sphere
    return d;
}
```### 第2步：选择差异化方法

#### 方法 A：前向差分 -- 4 个样本```glsl
const float EPSILON = 1e-3;

vec3 getNormal(vec3 p) {
    vec3 n;
    n.x = map(vec3(p.x + EPSILON, p.y, p.z));
    n.y = map(vec3(p.x, p.y + EPSILON, p.z));
    n.z = map(vec3(p.x, p.y, p.z + EPSILON));
    return normalize(n - map(p));
}
```#### 方法 B：中心差 -- 6 个样本```glsl
vec3 getNormal(vec3 p) {
    vec2 o = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + o.xyy) - map(p - o.xyy),
        map(p + o.yxy) - map(p - o.yxy),
        map(p + o.yyx) - map(p - o.yyx)
    ));
}
```#### 方法 C：四面体方法 -- 4 个样本（推荐）```glsl
// Classic tetrahedron method, coefficient 0.5773 ~ 1/sqrt(3)
vec3 calcNormal(vec3 pos) {
    float eps = 0.0005;
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    return normalize(
        e.xyy * map(pos + e.xyy * eps) +
        e.yyx * map(pos + e.yyx * eps) +
        e.yxy * map(pos + e.yxy * eps) +
        e.xxx * map(pos + e.xxx * eps)
    );
}
```### 第 3 步：应用于照明```glsl
vec3 pos = ro + rd * t;        // hit point
vec3 nor = calcNormal(pos);    // surface normal

vec3 lightDir = normalize(vec3(1.0, 4.0, -4.0));
float diff = max(dot(nor, lightDir), 0.0);
vec3 col = vec3(0.8) * diff;
```## 完整的代码模板```glsl
// SDF Normal Estimation — Complete ShaderToy Template

#define MAX_STEPS 128
#define MAX_DIST 100.0
#define SURF_DIST 0.001
#define NORMAL_METHOD 2      // 0=forward diff, 1=central diff, 2=tetrahedron

// ---- SDF Scene Definition ----
float map(vec3 p) {
    float sphere = length(p - vec3(0.0, 1.0, 0.0)) - 1.0;
    float ground = p.y;
    return min(sphere, ground);
}

// ---- Normal Estimation ----

vec3 normalForward(vec3 p) {
    float eps = 0.001;
    float d = map(p);
    return normalize(vec3(
        map(p + vec3(eps, 0.0, 0.0)),
        map(p + vec3(0.0, eps, 0.0)),
        map(p + vec3(0.0, 0.0, eps))
    ) - d);
}

vec3 normalCentral(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

vec3 normalTetra(vec3 p) {
    float eps = 0.0005;
    vec2 e = vec2(1.0, -1.0) * 0.5773;
    return normalize(
        e.xyy * map(p + e.xyy * eps) +
        e.yyx * map(p + e.yyx * eps) +
        e.yxy * map(p + e.yxy * eps) +
        e.xxx * map(p + e.xxx * eps)
    );
}

vec3 calcNormal(vec3 p) {
#if NORMAL_METHOD == 0
    return normalForward(p);
#elif NORMAL_METHOD == 1
    return normalCentral(p);
#else
    return normalTetra(p);
#endif
}

// ---- Raymarching ----
float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < SURF_DIST || t > MAX_DIST) break;
        t += d;
    }
    return t;
}

// ---- Main Function ----
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    vec3 ro = vec3(0.0, 2.0, -5.0);
    vec3 rd = normalize(vec3(uv, 1.5));

    float t = raymarch(ro, rd);
    vec3 col = vec3(0.0);

    if (t < MAX_DIST) {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos);

        vec3 sunDir = normalize(vec3(0.8, 0.4, -0.6));
        float diff = clamp(dot(nor, sunDir), 0.0, 1.0);
        float amb = 0.5 + 0.5 * nor.y;
        vec3 ref = reflect(rd, nor);
        float spec = pow(clamp(dot(ref, sunDir), 0.0, 1.0), 16.0);

        col = vec3(0.18) * amb + vec3(1.0, 0.95, 0.85) * diff + vec3(0.5) * spec;
    } else {
        col = vec3(0.5, 0.7, 1.0) - 0.5 * rd.y;
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：NuSan 反向偏移正向差分```glsl
// Reverse-offset forward difference
vec2 noff = vec2(0.001, 0.0);
vec3 normal = normalize(
    map(pos) - vec3(
        map(pos - noff.xyy),
        map(pos - noff.yxy),
        map(pos - noff.yyx)
    )
);
```### 变体 2：自适应 Epsilon（距离缩放）```glsl
// Adaptive epsilon based on ray distance
vec3 calcNormal(vec3 pos, float t) {
    float precis = 0.001 * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx)
    );
}
```### 变体 3：用于舍入/抗锯齿的大 Epsilon```glsl
// Large epsilon for rounding / anti-aliasing
vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.015, -0.015); // intentionally large epsilon
    return normalize(
        e.xyy * map(p + e.xyy) +
        e.yyx * map(p + e.yyx) +
        e.yxy * map(p + e.yxy) +
        e.xxx * map(p + e.xxx)
    );
}
```### 变体 4：反内联循环```glsl
// Anti-inlining loop — reduces compile time for complex SDFs
#define ZERO (min(iFrame, 0))

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
```### 变体 5：正常 + 边缘检测```glsl
// Central difference + Laplacian edge detection
float edge = 0.0;
vec3 normal(vec3 p) {
    vec3 e = vec3(0.0, det * 5.0, 0.0);

    float d1 = de(p - e.yxx), d2 = de(p + e.yxx);
    float d3 = de(p - e.xyx), d4 = de(p + e.xyx);
    float d5 = de(p - e.xxy), d6 = de(p + e.xxy);
    float d  = de(p);

    edge = abs(d - 0.5 * (d2 + d1))
         + abs(d - 0.5 * (d4 + d3))
         + abs(d - 0.5 * (d6 + d5));
    edge = min(1.0, pow(edge, 0.55) * 15.0);

    return normalize(vec3(d1 - d2, d3 - d4, d5 - d6));
}
```## 表演与作曲

**性能**：
- 默认为四面体方法（4个样本，比前向差分精度更好）
- 仅当出现锯齿状正常伪影时才切换到中心差异（6 个样本）
- 对复杂的 SDF 使用反内联循环（变体 4）以避免编译时间爆炸
- Epsilon推荐`0.0005 ~ 0.001`；最佳实践是自适应“eps * t”
- 太小（< 1e-5）会产生浮点噪声；太大 (> 0.05) 会丢失细节
- 当同一位置需要多种类型的信息时，重用 SDF 采样结果（例如变体 5）

**常见组合**：
- **Normal + Soft Shadow**: `calcSoftShadow(pos +nor * 0.01, sunDir, 16.0)` -- 起点处的法线偏移以避免自相交
- **法线 + AO**：沿法线进行多步 SDF 采样以估计遮挡
- **法线 + 菲涅耳**：`pow(clamp(1.0 + dot(nor, rd), 0.0, 1.0), 5.0)`
- **法线 + 凹凸贴图**：在 SDF 法线上叠加纹理梯度扰动
- **法线 + 三平面贴图**：使用 `abs(nor)` 组件作为三平面混合权重

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/normal-estimation.md)