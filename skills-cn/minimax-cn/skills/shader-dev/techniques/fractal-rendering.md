# 分形渲染技巧

## 用例
- 渲染自相似数学结构：Mandelbrot/Julia 集 (2D)、Mandelbulb (3D)、IFS 分形 (Menger/Apollonian)
- 需要无限细节的程序纹理或背景
- 实时生成复杂的几何视觉效果（音乐可视化、科幻场景、抽象艺术）
- 适用于ShaderToy、演示场景、程序内容生成

## 核心原则

分形渲染本质上是**迭代系统的可视化**，分为三类：

### 1.逃逸时间算法
迭代 `Z <- Z^2 + c`，计算转义步骤。通过同时跟踪导数“Z”来估计距离：```
Z  <- Z^2 + c
Z' <- 2*Z*Z' + 1
d(c) = |Z|*log|Z| / |Z'|
```### 2.迭代函数系统（IFS / KIFS）
折叠排序尺度偏移迭代产生自相似结构：```
p = abs(p)                          // fold
sort p.xyz descending               // sort
p = Scale * p - Offset * (Scale-1)  // scale and offset
```### 3. 球形反演分形
`fract()`空间折叠+球面反转`p *= s/dot(p,p)`：```
p = -1.0 + 2.0 * fract(0.5*p + 0.5)
k = s / dot(p, p)
p *= k; scale *= k
```所有 3D 分形均通过 **球体追踪（光线行进）** 渲染。

## 实施步骤

### 第 1 步：坐标标准化```glsl
vec2 p = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
```### 步骤 2：2D Mandelbrot 逃逸时间迭代```glsl
float distanceToMandelbrot(in vec2 c) {
    vec2 z  = vec2(0.0);
    vec2 dz = vec2(0.0);
    float m2 = 0.0;

    for (int i = 0; i < MAX_ITER; i++) {
        if (m2 > BAILOUT * BAILOUT) break;
        // Z' -> 2*Z*Z' + 1
        dz = 2.0 * vec2(z.x*dz.x - z.y*dz.y,
                         z.x*dz.y + z.y*dz.x) + vec2(1.0, 0.0);
        // Z -> Z^2 + c
        z = vec2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
        m2 = dot(z, z);
    }
    return 0.5 * sqrt(dot(z,z) / dot(dz,dz)) * log(dot(z,z));
}
```### 步骤 3：曼德尔球距离场（球坐标 N 次方）```glsl
float mandelbulb(vec3 p) {
    vec3 z = p;
    float dr = 1.0;
    float r;

    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > BAILOUT) break;
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;
        r = pow(r, POWER);
        theta *= POWER;
        phi *= POWER;
        z = r * vec3(cos(theta)*cos(phi),
                      sin(theta)*cos(phi),
                      sin(phi)) + p;
    }
    return 0.5 * log(r) * r / dr;
}
```### 步骤 4：门格尔海绵距离场 (KIFS)```glsl
float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));  // infinite tiling
    float d = 1000.0;

    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);
        if (z.x < z.y) z.xy = z.yx;
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0);
        if (z.z < -0.5 * OFFSET.z * (SCALE - 1.0))
            z.z += OFFSET.z * (SCALE - 1.0);
        d = min(d, length(z) * pow(SCALE, float(-n) - 1.0));
    }
    return d - 0.001;
}
```### 步骤 5：阿波罗距离场（球面反演）```glsl
vec4 orb;  // orbit trap

float apollonianDE(vec3 p, float s) {
    float scale = 1.0;
    orb = vec4(1000.0);

    for (int i = 0; i < INVERSION_ITER; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));
        float k = s / r2;
        p *= k;
        scale *= k;
    }
    return 0.25 * abs(p.y) / scale;
}
```### 第 6 步：射线行进```glsl
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.01;
    for (int i = 0; i < MAX_STEPS; i++) {
        float precis = PRECISION * t;
        float h = map(ro + rd * t);
        if (h < precis || t > MAX_DIST) break;
        t += h * FUDGE_FACTOR;
    }
    return (t > MAX_DIST) ? -1.0 : t;
}
```###第七步：正常计算```glsl
// 4-tap tetrahedral method (recommended)
vec3 calcNormal(vec3 pos, float t) {
    float precis = 0.001 * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy) +
        e.yyx * map(pos + e.yyx) +
        e.yxy * map(pos + e.yxy) +
        e.xxx * map(pos + e.xxx));
}
```### 第 8 步：着色和照明```glsl
vec3 shade(vec3 pos, vec3 nor, vec3 rd, vec4 trap) {
    vec3 light1 = normalize(LIGHT_DIR);
    float diff = clamp(dot(light1, nor), 0.0, 1.0);
    float amb  = 0.7 + 0.3 * nor.y;
    float ao   = pow(clamp(trap.w * 2.0, 0.0, 1.0), 1.2);

    vec3 brdf = vec3(0.4) * amb * ao + vec3(1.0) * diff * ao;

    vec3 rgb = vec3(1.0);
    rgb = mix(rgb, vec3(1.0, 0.8, 0.2), clamp(6.0*trap.y, 0.0, 1.0));
    rgb = mix(rgb, vec3(1.0, 0.55, 0.0), pow(clamp(1.0-2.0*trap.z, 0.0, 1.0), 8.0));
    return rgb * brdf;
}
```### 步骤 9：相机```glsl
void setupCamera(vec2 uv, vec3 ro, vec3 ta, float cr, out vec3 rd) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = normalize(cross(cu, cw));
    rd = normalize(uv.x * cu + uv.y * cv + 2.0 * cw);
}
```## 完整的代码模板

具有全光线行进管道、轨道陷阱着色和 AO 的 3D 阿波罗分形（球形反转类型）。准备在 ShaderToy 中运行。```glsl
// Fractal Rendering — Apollonian (Spherical Inversion) Template

#define MAX_STEPS 200
#define MAX_DIST 30.0
#define PRECISION 0.001
#define INVERSION_ITER 8    // Tunable: 5-12
#define AA 1                // Tunable: 1=no AA, 2=4xSSAA

vec4 orb;

float map(vec3 p, float s) {
    float scale = 1.0;
    orb = vec4(1000.0);

    for (int i = 0; i < INVERSION_ITER; i++) {
        p = -1.0 + 2.0 * fract(0.5 * p + 0.5);
        float r2 = dot(p, p);
        orb = min(orb, vec4(abs(p), r2));
        float k = s / r2;
        p     *= k;
        scale *= k;
    }
    return 0.25 * abs(p.y) / scale;
}

float trace(vec3 ro, vec3 rd, float s) {
    float t = 0.01;
    for (int i = 0; i < MAX_STEPS; i++) {
        float precis = PRECISION * t;
        float h = map(ro + rd * t, s);
        if (h < precis || t > MAX_DIST) break;
        t += h;
    }
    return (t > MAX_DIST) ? -1.0 : t;
}

vec3 calcNormal(vec3 pos, float t, float s) {
    float precis = PRECISION * t;
    vec2 e = vec2(1.0, -1.0) * precis;
    return normalize(
        e.xyy * map(pos + e.xyy, s) +
        e.yyx * map(pos + e.yyx, s) +
        e.yxy * map(pos + e.yxy, s) +
        e.xxx * map(pos + e.xxx, s));
}

vec3 render(vec3 ro, vec3 rd, float anim) {
    vec3 col = vec3(0.0);
    float t = trace(ro, rd, anim);

    if (t > 0.0) {
        vec4 tra = orb;
        vec3 pos = ro + t * rd;
        vec3 nor = calcNormal(pos, t, anim);

        vec3 light1 = normalize(vec3(0.577, 0.577, -0.577));
        vec3 light2 = normalize(vec3(-0.707, 0.0, 0.707));
        float key = clamp(dot(light1, nor), 0.0, 1.0);
        float bac = clamp(0.2 + 0.8 * dot(light2, nor), 0.0, 1.0);
        float amb = 0.7 + 0.3 * nor.y;
        float ao  = pow(clamp(tra.w * 2.0, 0.0, 1.0), 1.2);

        vec3 brdf = vec3(0.40) * amb * ao
                  + vec3(1.00) * key * ao
                  + vec3(0.40) * bac * ao;

        vec3 rgb = vec3(1.0);
        rgb = mix(rgb, vec3(1.0, 0.80, 0.2), clamp(6.0 * tra.y, 0.0, 1.0));
        rgb = mix(rgb, vec3(1.0, 0.55, 0.0), pow(clamp(1.0 - 2.0*tra.z, 0.0, 1.0), 8.0));

        col = rgb * brdf * exp(-0.2 * t);
    }
    return sqrt(col);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 0.25;
    float anim = 1.1 + 0.5 * smoothstep(-0.3, 0.3, cos(0.1 * iTime));

    vec3 tot = vec3(0.0);

    #if AA > 1
    for (int jj = 0; jj < AA; jj++)
    for (int ii = 0; ii < AA; ii++)
    #else
    int ii = 1, jj = 1;
    #endif
    {
        vec2 q = fragCoord.xy + vec2(float(ii), float(jj)) / float(AA);
        vec2 p = (2.0 * q - iResolution.xy) / iResolution.y;

        vec3 ro = vec3(2.8*cos(0.1 + 0.33*time),
                       0.4 + 0.3*cos(0.37*time),
                       2.8*cos(0.5 + 0.35*time));
        vec3 ta = vec3(1.9*cos(1.2 + 0.41*time),
                       0.4 + 0.1*cos(0.27*time),
                       1.9*cos(2.0 + 0.38*time));
        float roll = 0.2 * cos(0.1 * time);

        vec3 cw = normalize(ta - ro);
        vec3 cp = vec3(sin(roll), cos(roll), 0.0);
        vec3 cu = normalize(cross(cw, cp));
        vec3 cv = normalize(cross(cu, cw));
        vec3 rd = normalize(p.x*cu + p.y*cv + 2.0*cw);

        tot += render(ro, rd, anim);
    }

    tot /= float(AA * AA);
    fragColor = vec4(tot, 1.0);
}
```## 常见变体

### 1. 2D Mandelbrot（距离估计着色）
纯 2D，无需光线行进。复杂迭代+距离着色。```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 p = (2.0*fragCoord - iResolution.xy) / iResolution.y;
    float tz = 0.5 - 0.5*cos(0.225*iTime);
    float zoo = pow(0.5, 13.0*tz);
    vec2 c = vec2(-0.05, 0.6805) + p * zoo; // Tunable: zoom center point

    vec2 z = vec2(0.0), dz = vec2(0.0);
    for (int i = 0; i < 300; i++) {
        if (dot(z,z) > 1024.0) break;
        dz = 2.0*vec2(z.x*dz.x-z.y*dz.y, z.x*dz.y+z.y*dz.x) + vec2(1.0,0.0);
        z  = vec2(z.x*z.x-z.y*z.y, 2.0*z.x*z.y) + c;
    }

    float d = 0.5*sqrt(dot(z,z)/dot(dz,dz))*log(dot(z,z));
    d = clamp(pow(4.0*d/zoo, 0.2), 0.0, 1.0);
    fragColor = vec4(vec3(d), 1.0);
}
```### 2. 曼德尔球电源-N
球坐标三角函数； ‘POWER’参数控制形态。```glsl
#define POWER 8.0       // Tunable: 2-16
#define FRACTAL_ITER 4  // Tunable: 2-8

float mandelbulbDE(vec3 p) {
    vec3 z = p;
    float dr = 1.0, r;
    for (int i = 0; i < FRACTAL_ITER; i++) {
        r = length(z);
        if (r > 2.0) break;
        float theta = atan(z.y, z.x);
        float phi   = asin(z.z / r);
        dr = pow(r, POWER - 1.0) * dr * POWER + 1.0;
        r = pow(r, POWER);
        theta *= POWER; phi *= POWER;
        z = r * vec3(cos(theta)*cos(phi), sin(theta)*cos(phi), sin(phi)) + p;
    }
    return 0.5 * log(r) * r / dr;
}
```### 3.门格尔海绵（KIFS）
`abs()`折叠+条件排序，正则几何分形。```glsl
#define SCALE 3.0
#define OFFSET vec3(0.92858,0.92858,0.32858)
#define IFS_ITER 7

float mengerDE(vec3 z) {
    z = abs(1.0 - mod(z, 2.0));
    float d = 1000.0;
    for (int n = 0; n < IFS_ITER; n++) {
        z = abs(z);
        if (z.x < z.y) z.xy = z.yx;
        if (z.x < z.z) z.xz = z.zx;
        if (z.y < z.z) z.yz = z.zy;
        z = SCALE * z - OFFSET * (SCALE - 1.0);
        if (z.z < -0.5*OFFSET.z*(SCALE-1.0))
            z.z += OFFSET.z*(SCALE-1.0);
        d = min(d, length(z) * pow(SCALE, float(-n)-1.0));
    }
    return d - 0.001;
}
```### 4.四元数朱莉娅集
四元数 `Z <- Z^2 + c` (4D)，具有固定的 `c` 参数；通过拍摄 3D 切片来可视化。```glsl
vec4 qsqr(vec4 a) {
    return vec4(a.x*a.x - a.y*a.y - a.z*a.z - a.w*a.w,
                2.0*a.x*a.y, 2.0*a.x*a.z, 2.0*a.x*a.w);
}

float juliaDE(vec3 p, vec4 c) {
    vec4 z = vec4(p, 0.0);
    float md2 = 1.0, mz2 = dot(z, z);
    for (int i = 0; i < 11; i++) {
        md2 *= 4.0 * mz2;
        z = qsqr(z) + c;
        mz2 = dot(z, z);
        if (mz2 > 4.0) break;
    }
    return 0.25 * sqrt(mz2 / md2) * log(mz2);
}
// Animated c: vec4 c = 0.45*cos(vec4(0.5,3.9,1.4,1.1)+time*vec4(1.2,1.7,1.3,2.5))-vec4(0.3,0,0,0);
```### 5. 最小 IFS 场（2D，无光线行进）
`abs(p)/dot(p,p) + offset`迭代，加权累加产生密度场。```glsl
float field(vec3 p) {
    float strength = 7.0 + 0.03 * log(1.e-6 + fract(sin(iTime) * 4373.11));
    float accum = 0.0, prev = 0.0, tw = 0.0;
    for (int i = 0; i < 32; ++i) {
        float mag = dot(p, p);
        p = abs(p) / mag + vec3(-0.5, -0.4, -1.5); // Tunable: offset values
        float w = exp(-float(i) / 7.0);
        accum += w * exp(-strength * pow(abs(mag - prev), 2.3));
        tw += w;
        prev = mag;
    }
    return max(0.0, 5.0 * accum / tw - 0.7);
}
```## 表演与作曲

### 性能提示
- 核心瓶颈：外部光线行进 x 内部分形迭代（例如，每个像素“200 x 8 = 1600”地图调用）
- 将`MAX_STEPS`减少到60-100，用软化系数0.7-0.9进行补偿
- 命中阈值 `precis = 0.001 * t` 随着距离的增加而放松
- 分形迭代：当 `|z|^2 > bailout` 时立即中断
- 将迭代次数从 8 次减少到 4-5 次，对视觉影响最小
- 使用 4-tap 法线代替 6-tap 可节省 33%
- 开发期间使用 AA=1，发布时使用 AA=2（AA=3 = 9x 开销）
- 避免在循环内使用`pow()`；手动扩展低功率

### 构图技巧
- **体积光**：在上帝光线的光线行军期间累积“exp(-10.0 * h)”
- **色调映射**：ACES + sRGB gamma 用于处理高频细节
- **透明折射**：负距离场反向光线行进+比尔定律吸收
- **轨道陷阱着色**：将陷阱值映射到 HSV 或发射颜色
- **软阴影**：光线向光行进，累积“min(k * h / t)”以获得软阴影

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/fractal-rendering.md)