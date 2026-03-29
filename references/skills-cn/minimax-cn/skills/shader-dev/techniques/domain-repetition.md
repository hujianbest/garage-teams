# 域重复和空间折叠

## 用例

- **无限重复场景**：从单个 SDF 图元渲染无限延伸的几何体（走廊、城市、星空）
- **万花筒/对称效果**：N重旋转对称、镜像对称、多面体对称
- **分形几何**：通过迭代空间折叠生成自相似结构（Apollonian、Kali-set）
- **建筑/机械结构**：使用重复+变化构建复杂但规则的场景
- **螺旋/环形拓扑**：沿极坐标或螺旋路径重复几何形状

核心价值：**在单个单元格中定义几何体，渲染无限空间**。

## 核心原则

域重复的本质是**坐标变换**：在计算SDF之前，将点“p”折叠/映射到有限的“基本域”中。

**三个基本操作：**

|运营|公式|效果|
|------------|---------|--------|
| **模组重复** | `p = mod(p + c/2, c) - c/2` |沿轴无限平移重复 |
| **abs 镜像** | `p = 绝对值(p)` |沿轴平面镜像对称 |
| **旋转折叠** | `角度 = mod(atan(p.y,p.x), TAU/N)` | N 重旋转对称 |

关键数学：`mod(x,c)` -> 周期性映射到`[0,c)`； `abs(x)` -> 反射对称； `fract(x)` = `mod(x,1.0)` -> 标准化周期。

## 实施步骤

### 步骤 1：笛卡尔域重复（mod 重复）```glsl
// Infinite translational repetition along one or more axes
vec3 domainRepeat(vec3 p, vec3 period) {
    return mod(p + period * 0.5, period) - period * 0.5;
}

float map(vec3 p) {
    vec3 q = domainRepeat(p, vec3(4.0)); // repeat every 4 units
    return sdBox(q, vec3(0.5));
}
```### 步骤 2：对称折叠（abs-mod 三角波）```glsl
// Boundary-continuous symmetric folding, coordinates oscillate 0->tile->0
vec3 symmetricFold(vec3 p, float tile) {
    return abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
}

// Star Nest classic usage
p = abs(vec3(tile) - mod(p, vec3(tile * 2.0)));
```### 步骤 3：角域重复（极坐标折叠）```glsl
// N-way rotational symmetry (kaleidoscope)
vec2 pmod(vec2 p, float count) {
    float angle = atan(p.x, p.y) + PI / count;
    float sector = TAU / count;
    angle = floor(angle / sector) * sector;
    return p * rot(-angle);
}

p1.xy = pmod(p1.xy, 5.0); // 5-fold symmetry
```### 步骤 4：分形域折叠（分形迭代）```glsl
// Apollonian fractal core loop
float map(vec3 p, float s) {
    float scale = 1.0;
    vec4 orb = vec4(1000.0);

    for (int i = 0; i < 8; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5); // centered fract folding
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));
        float k = s / r2;    // spherical inversion scaling
        p *= k;
        scale *= k;
    }
    return 0.25 * abs(p.y) / scale;
}
```### 步骤 5：迭代 abs 折叠（IFS / Kali-set）```glsl
// IFS abs folding fractal
float ifsBox(vec3 p) {
    for (int i = 0; i < 5; i++) {
        p = abs(p) - 1.0;
        p.xy *= rot(iTime * 0.3);
        p.xz *= rot(iTime * 0.1);
    }
    return sdBox(p, vec3(0.4, 0.8, 0.3));
}

// Kali-set variant: mod repetition + IFS + dot(p,p) scaling
vec2 de(vec3 pos) {
    vec3 tpos = pos;
    tpos.xz = abs(0.5 - mod(tpos.xz, 1.0));
    vec4 p = vec4(tpos, 1.0);               // w tracks scaling
    for (int i = 0; i < 7; i++) {
        p.xyz = abs(p.xyz) - vec3(-0.02, 1.98, -0.02);
        p = p * (2.0) / clamp(dot(p.xyz, p.xyz), 0.4, 1.0)
            - vec4(0.5, 1.0, 0.4, 0.0);
        p.xz *= rot(0.416);
    }
    return vec2(length(max(abs(p.xyz)-vec3(0.1,5.0,0.1), 0.0)) / p.w, 0.0);
}
```### 步骤 6：反射折叠（多面体对称）```glsl
// Plane reflection
float pReflect(inout vec3 p, vec3 planeNormal, float offset) {
    float t = dot(p, planeNormal) + offset;
    if (t < 0.0) p = p - (2.0 * t) * planeNormal;
    return sign(t);
}

// Icosahedral folding
void pModIcosahedron(inout vec3 p) {
    vec3 nc = vec3(-0.5, -cos(PI/5.0), sqrt(0.75 - cos(PI/5.0)*cos(PI/5.0)));
    p = abs(p);
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
    p.xy = abs(p.xy);
    pReflect(p, nc, 0.0);
}
```### 步骤 7：环形/圆柱形域扭曲```glsl
// Bend the xz plane into a toroidal topology
vec2 displaceLoop(vec2 p, float radius) {
    return vec2(length(p) - radius, atan(p.y, p.x));
}

pDonut.xz = displaceLoop(pDonut.xz, donutRadius);
pDonut.z *= donutRadius; // unfold angle to linear length
```### 步骤 8：一维中心域重复（带有单元 ID）```glsl
// Returns cell index, usable for random variations
float pMod1(inout float p, float size) {
    float halfsize = size * 0.5;
    float c = floor((p + halfsize) / size);
    p = mod(p + halfsize, size) - halfsize;
    return c;
}

float cellID = pMod1(p.x, 2.0);
float salt = fract(sin(cellID * 127.1) * 43758.5453);
```## 完整代码模板

组合演示：笛卡尔重复+角度重复+IFS折叠。直接在 ShaderToy 中运行。```glsl
#define PI 3.14159265359
#define TAU 6.28318530718
#define MAX_STEPS 100
#define MAX_DIST 50.0
#define SURF_DIST 0.001
#define PERIOD 4.0
#define ANGULAR_COUNT 6.0
#define IFS_ITERS 5
#define IFS_OFFSET 1.2

mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, max(d.y, d.z)), 0.0);
}

vec3 domainRepeat(vec3 p, vec3 period) {
    return mod(p + period * 0.5, period) - period * 0.5;
}

vec2 pmod(vec2 p, float count) {
    float a = atan(p.x, p.y) + PI / count;
    float n = TAU / count;
    a = floor(a / n) * n;
    return p * rot(-a);
}

float map(vec3 p) {
    vec3 q = domainRepeat(p, vec3(PERIOD));
    q.xz = pmod(q.xz, ANGULAR_COUNT);
    for (int i = 0; i < IFS_ITERS; i++) {
        q = abs(q) - IFS_OFFSET;
        q.xy *= rot(0.785);
        q.yz *= rot(0.471);
    }
    return sdBox(q, vec3(0.15, 0.4, 0.15));
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

float raymarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        float d = map(ro + rd * t);
        if (d < SURF_DIST || t > MAX_DIST) break;
        t += d;
    }
    return t;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (fragCoord * 2.0 - iResolution.xy) / iResolution.y;

    float time = iTime * 0.5;
    vec3 ro = vec3(sin(time) * 6.0, 3.0 + sin(time * 0.7) * 2.0, cos(time) * 6.0);
    vec3 ta = vec3(0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.8 * ww);

    float t = raymarch(ro, rd);

    vec3 col = vec3(0.0);
    if (t < MAX_DIST) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        vec3 lightDir = normalize(vec3(0.5, 0.8, -0.6));
        float diff = clamp(dot(n, lightDir), 0.0, 1.0);
        float amb = 0.5 + 0.5 * n.y;
        vec3 baseColor = 0.5 + 0.5 * cos(p * 0.5 + vec3(0.0, 2.0, 4.0));
        col = baseColor * (0.2 * amb + 0.8 * diff);
        col *= exp(-0.03 * t * t);
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 1. 体积光/辉光渲染```glsl
float acc = 0.0, t = 0.0;
for (int i = 0; i < 99; i++) {
    float dist = map(ro + rd * t);
    dist = max(abs(dist), 0.02);
    acc += exp(-dist * 3.0);       // decay factor controls glow sharpness
    t += dist * 0.5;               // step scale <1 for denser sampling
}
vec3 col = vec3(acc * 0.01, acc * 0.011, acc * 0.012);
```### 2. 单轴/双轴选择性重复```glsl
q.xz = mod(q.xz + 2.0, 4.0) - 2.0; // repeat only xz, y stays unchanged
```### 3.分形分形域折叠（阿波罗型）```glsl
float scale = 1.0;
for (int i = 0; i < 8; i++) {
    p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
    float k = 1.2 / dot(p, p);
    p *= k;
    scale *= k;
}
return 0.25 * abs(p.y) / scale;
```### 4.多层嵌套重复```glsl
float indexX = amod(p.xz, segments); // outer layer: angular repetition
p.x -= radius;
p.y = repeat(p.y, cellSize);         // inner layer: linear repetition
float salt = rng(vec2(indexX, floor(p.y / cellSize)));
```### 5.有限域重复（Clamp Limited）```glsl
vec3 domainRepeatLimited(vec3 p, float size, vec3 limit) {
    return p - size * clamp(floor(p / size + 0.5), -limit, limit);
}
// Repeat 5 times along x, 3 times along y/z
vec3 q = domainRepeatLimited(p, 2.0, vec3(2.0, 1.0, 1.0));
```## 表演和构图技巧

**性能：**
- 5-8 次分形迭代通常就足够了；使用“vec4.w”来跟踪缩放并避免额外的变量
- 确保几何半径 < period/2 以防止单元边界处的 SDF 不准确
- 体积光步长应随距离增加：`t += dist * (0.3 + t * 0.02)`
- 使用“clamp(dot(p,p), min, max)”来防止数值爆炸
- 避免在循环内使用“normalize()”；改为手动除以长度

**成分：**
- **域重复 + 光线行进**：最基本的组合，所有参考着色器都使用
- **域重复+轨道陷阱着色**：在分形迭代期间记录“min(orb, abs(p))”以进行着色
- **域重复 + 环形扭曲**：“displaceLoop”在应用线性/角度重复之前弯曲空间
- **域重复 + 噪声变化**：单元 ID -> 伪随机数 -> 调制几何参数
- **域重复 + 极螺旋**：“cartToPolar”与“pMod1”组合用于螺旋路径重复

## 进一步阅读

[参考](../reference/domain-repetition.md) 中有完整的分步教程、数学推导和高级用法