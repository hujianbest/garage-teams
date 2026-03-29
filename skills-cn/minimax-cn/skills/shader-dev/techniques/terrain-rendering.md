# Heightfield 射线行进地形渲染

## 用例

- 在 ShaderToy / Fragment Shaders 中程序生成自然景观（山脉、峡谷、沙丘等）
- 在单个像素着色器中完成 3D 地形飞行场景，无需几何体
- 电影般的空中视角、柔和的阴影和分层材质效果

## 核心原则

渲染流程：高度场定义→光线行进相交→法线和材质→照明→大气效果

- **FBM**：`f(p) = Σ (aⁿ × 噪声(2ⁿ × R × p))`，a=0.5，R=旋转矩阵，2ⁿ=倍频
- **导数侵蚀**：`f(p) = Σ (aⁿ × 噪声(p) / (1 + dot(d,d)))`，d=累积梯度，抑制陡坡上的细节
- **自适应步长**：`步长 = 因子 × (ray.y -terrain_height)`

## 实施步骤

1. **噪声和哈希** — 无罪哈希 + 具有解析导数的值噪声（“噪声”返回值 + 偏导数）
2. **FBM地形**——导数侵蚀FBM，`mat2(0.8,-0.6,0.6,0.8)`每层旋转以消除条带； LOD 层（L=3/M=9/H=16 个八度）
3. **射线行进** - 上限裁剪 + 自适应步长 `STEP_FACTOR * h` + 距离自适应精度 `abs(h) < 0.0015*t`
4. **法线** — 有限差分，epsilon 随着距离的增加而增加，以避免远处的混叠，使用高精度 `terrainH`
5. **软阴影** - 向太阳行进，跟踪“min(k*h/t)”来估计半影
6. **材质** - 按高度+坡度+噪音混合岩石/草/雪/沙
7. **照明** — 兰伯特漫反射 + 半球环境光 + 背光 + 菲涅尔边缘光 + Blinn-Phong 镜面反射
8. **大气雾** — 与波长相关的衰减 `exp(-t*k*vec3(1,1.5,4))` + 太阳散射雾颜色
9. **天空** — 天顶到地平线梯度 + 太阳盘/光晕
10. **相机** — Look-At矩阵+路径跟随飞行，高度跟踪地形

## 完整的代码模板```glsl
// =====================================================
// Heightfield Terrain Rendering - Complete Template
// =====================================================
#define TERRAIN_OCTAVES 9     // FBM octave count (3~16)
#define TERRAIN_SCALE 0.003   // Terrain spatial frequency
#define TERRAIN_HEIGHT 120.0  // Terrain elevation scale
#define MAX_STEPS 300         // Ray march step count (80~400)
#define MAX_DIST 5000.0       // Maximum render distance
#define STEP_FACTOR 0.4       // March conservative factor (0.3~0.8)
#define SHADOW_STEPS 80       // Shadow step count (32~128)
#define SHADOW_K 16.0         // Penumbra softness (8~64)
#define FOG_DENSITY 0.00025   // Fog density
#define SNOW_HEIGHT 80.0      // Snow line height
#define CAM_ALTITUDE 20.0     // Camera height above ground
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6))
#define SUN_COL vec3(8.0, 5.0, 3.0)
#define SKY_COL vec3(0.5, 0.7, 1.0)

// ---- Hash & Noise ----
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}

vec3 noised(in vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u  = f * f * (3.0 - 2.0 * f);
    vec2 du = 6.0 * f * (1.0 - f);
    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    float v = a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
    vec2  g = du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx);
    return vec3(v, g);
}

float noise(in vec2 p) { return noised(p).x; }

// ---- FBM Terrain (derivative erosion) + LOD ----
const mat2 m2 = mat2(0.8, -0.6, 0.6, 0.8);

float terrainFBM(in vec2 p, int octaves) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < 16; i++) {
        if (i >= octaves) break;
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}

float terrainL(vec2 p) { return terrainFBM(p, 3); }
float terrainM(vec2 p) { return terrainFBM(p, TERRAIN_OCTAVES); }
float terrainH(vec2 p) { return terrainFBM(p, 16); }

// ---- Ray Marching ----
float raymarch(in vec3 ro, in vec3 rd) {
    float t = 0.0;
    if (ro.y > TERRAIN_HEIGHT && rd.y >= 0.0) return -1.0;
    if (ro.y > TERRAIN_HEIGHT) t = (ro.y - TERRAIN_HEIGHT) / (-rd.y);
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 pos = ro + t * rd;
        float h = pos.y - terrainM(pos.xz);
        if (abs(h) < 0.0015 * t) break;
        if (t > MAX_DIST) return -1.0;
        t += STEP_FACTOR * h;
    }
    return t;
}

// ---- Normals ----
vec3 calcNormal(in vec3 pos, float t) {
    float eps = 0.02 + 0.00005 * t * t;
    float hC = terrainH(pos.xz);
    float hR = terrainH(pos.xz + vec2(eps, 0.0));
    float hU = terrainH(pos.xz + vec2(0.0, eps));
    return normalize(vec3(hC - hR, eps, hC - hU));
}

// ---- Soft Shadows ----
float calcShadow(in vec3 pos, in vec3 sunDir) {
    float res = 1.0, t = 1.0;
    for (int i = 0; i < SHADOW_STEPS; i++) {
        vec3 p = pos + t * sunDir;
        float h = p.y - terrainM(p.xz);
        if (h < 0.001) return 0.0;
        res = min(res, SHADOW_K * h / t);
        t += clamp(h, 2.0, 100.0);
    }
    return clamp(res, 0.0, 1.0);
}

// ---- Materials ----
vec3 getMaterial(in vec3 pos, in vec3 nor) {
    float slope = nor.y, h = pos.y;
    float nz = noise(pos.xz * 0.04) * noise(pos.xz * 0.005);
    vec3 rock  = vec3(0.10, 0.09, 0.08);
    vec3 grass = mix(vec3(0.10, 0.08, 0.04), vec3(0.05, 0.09, 0.02), nz);
    vec3 snow  = vec3(0.62, 0.65, 0.70);
    vec3 sand  = vec3(0.50, 0.45, 0.35);
    vec3 col = rock;
    col = mix(col, grass, smoothstep(0.5, 0.8, slope));
    float snowMask = smoothstep(SNOW_HEIGHT - 20.0 * nz, SNOW_HEIGHT + 10.0, h)
                   * smoothstep(0.3, 0.7, slope);
    col = mix(col, snow, snowMask);
    float beachMask = smoothstep(2.5, 0.0, h) * smoothstep(0.5, 0.9, slope);
    col = mix(col, sand, beachMask);
    return col;
}

// ---- Lighting ----
vec3 calcLighting(in vec3 pos, in vec3 nor, in vec3 rd, float shadow) {
    float dif = clamp(dot(nor, SUN_DIR), 0.0, 1.0);
    float amb = 0.5 + 0.5 * nor.y;
    vec3 backDir = normalize(vec3(-SUN_DIR.x, 0.0, -SUN_DIR.z));
    float bac = clamp(0.2 + 0.8 * dot(nor, backDir), 0.0, 1.0);
    float fre = pow(clamp(1.0 + dot(rd, nor), 0.0, 1.0), 2.0);
    vec3 hal = normalize(SUN_DIR - rd);
    float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0)
              * (0.04 + 0.96 * pow(1.0 + dot(hal, rd), 5.0));
    vec3 lin = vec3(0.0);
    lin += dif * shadow * SUN_COL * 0.1;
    lin += amb * SKY_COL * 0.2;
    lin += bac * vec3(0.15, 0.05, 0.04);
    lin += fre * SKY_COL * 0.3;
    lin += spe * shadow * SUN_COL * 0.05;
    return lin;
}

// ---- Atmosphere ----
vec3 applyFog(in vec3 col, float t, in vec3 rd) {
    vec3 ext = exp(-t * FOG_DENSITY * vec3(1.0, 1.5, 4.0));
    float sundot = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    vec3 fogCol = mix(vec3(0.55, 0.55, 0.58), vec3(1.0, 0.7, 0.3), 0.3 * pow(sundot, 8.0));
    return col * ext + fogCol * (1.0 - ext);
}

// ---- Sky ----
vec3 getSky(in vec3 rd) {
    vec3 col = vec3(0.3, 0.5, 0.85) - rd.y * vec3(0.2, 0.15, 0.0);
    float horizon = pow(1.0 - max(rd.y, 0.0), 4.0);
    col = mix(col, vec3(0.8, 0.75, 0.7), 0.5 * horizon);
    float sundot = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    col += vec3(1.0, 0.7, 0.3) * 0.3 * pow(sundot, 8.0);
    col += vec3(1.0, 0.9, 0.7) * 0.5 * pow(sundot, 64.0);
    col += vec3(1.0, 1.0, 0.9) * min(pow(sundot, 1150.0), 0.3);
    return col;
}

// ---- Camera ----
vec3 cameraPath(float t) {
    return vec3(100.0 * sin(0.2 * t), 0.0, -100.0 * t);
}

mat3 setCamera(in vec3 ro, in vec3 ta) {
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}

// ======== Main Function ========
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
    float time = iTime * 0.5;
    vec3 ro = cameraPath(time);
    ro.y = terrainL(ro.xz) + CAM_ALTITUDE;
    vec3 ta = cameraPath(time + 2.0);
    ta.y = terrainL(ta.xz) + CAM_ALTITUDE * 0.5;
    mat3 cam = setCamera(ro, ta);
    vec3 rd = cam * normalize(vec3(uv, 1.5));

    float t = raymarch(ro, rd);
    vec3 col;
    if (t > 0.0) {
        vec3 pos = ro + t * rd;
        vec3 nor = calcNormal(pos, t);
        vec3 mate = getMaterial(pos, nor);
        float sha = calcShadow(pos + nor * 0.5, SUN_DIR);
        vec3 lin = calcLighting(pos, nor, rd, sha);
        col = mate * lin;
        col = applyFog(col, t, rd);
    } else {
        col = getSky(rd);
    }
    col = 1.0 - exp(-col * 2.0);
    col = pow(col, vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```### Binary Refinement（可选，在 raymarch 之后调用）```glsl
float bisect(in vec3 ro, in vec3 rd, float tNear, float tFar) {
    for (int i = 0; i < 5; i++) {
        float tMid = 0.5 * (tNear + tFar);
        vec3 pos = ro + tMid * rd;
        float h = pos.y - terrainM(pos.xz);
        if (h > 0.0) tNear = tMid; else tFar = tMid;
    }
    return 0.5 * (tNear + tFar);
}
```## 常见变体

### 放松行进

在远距离时自动增加步长，以 90 步覆盖更大的范围。```glsl
float raymarchRelax(in vec3 ro, in vec3 rd) {
    float t = 0.0;
    float d = (ro + rd * t).y - terrainM((ro + rd * t).xz);
    for (int i = 0; i < 90; i++) {
        if (abs(d) < t * 0.0001 || t > 400.0) break;
        float rl = max(t * 0.02, 1.0);
        t += d * rl;
        vec3 pos = ro + t * rd;
        d = (pos.y - terrainM(pos.xz)) * 0.7;
    }
    return t;
}
```### 符号交替 FBM

振幅翻转每一层的符号，产生崎岖的交替山脊/山谷图案。```glsl
float terrainSignFlip(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, w = 1.0;
    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        a += w * noise(p);
        w = -w * 0.4;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}
```### 峡谷风格（纹理驱动 + 3D 位移）

纹理采样 + 3D FBM 位移，支持悬崖/洞穴和其他非高度场地层。```glsl
float noise3D(in vec3 x) {
    vec3 p = floor(x); vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    vec2 uv = (p.xy + vec2(37.0, 17.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z);
}

const mat3 m3 = mat3(0.00, 0.80, 0.60, -0.80, 0.36,-0.48, -0.60,-0.48, 0.64);

float displacement(vec3 p) {
    float f = 0.5 * noise3D(p); p = m3 * p * 2.02;
    f += 0.25 * noise3D(p);    p = m3 * p * 2.03;
    f += 0.125 * noise3D(p);   p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p);
    return f;
}

float mapCanyon(vec3 p) {
    float h = terrainM(p.xz);
    float dis = displacement(0.25 * p * vec3(1.0, 4.0, 1.0)) * 3.0;
    return (dis + p.y - h) * 0.25;
}
```### 定向侵蚀噪声

坡度方向驱动 Gabor 噪声投影，产生逼真的树突排水模式。```glsl
#define EROSION_BRANCH 1.5

vec3 erosionNoise(vec2 p, vec2 dir) {
    vec2 ip = floor(p); vec2 fp = fract(p) - 0.5;
    float va = 0.0, wt = 0.0; vec2 dva = vec2(0.0);
    for (int i = -2; i <= 1; i++)
    for (int j = -2; j <= 1; j++) {
        vec2 o = vec2(float(i), float(j));
        vec2 h = hash2(ip - o) * 0.5;
        vec2 pp = fp + o + h;
        float d = dot(pp, pp);
        float w = exp(-d * 2.0);
        float mag = dot(pp, dir);
        va += cos(mag * 6.283) * w;
        dva += -sin(mag * 6.283) * dir * w;
        wt += w;
    }
    return vec3(va, dva) / wt;
}

float terrainErosion(vec2 p, vec2 baseSlope) {
    float e = 0.0, a = 0.5;
    vec2 dir = normalize(baseSlope + vec2(0.001));
    for (int i = 0; i < 5; i++) {
        vec3 n = erosionNoise(p * 4.0, dir);
        e += a * n.x;
        dir = normalize(dir + n.zy * vec2(1.0, -1.0) * EROSION_BRANCH);
        a *= 0.5; p *= 2.0;
    }
    return e;
}
```### 体积云 + 上帝射线

云片从前到后的alpha合成，累积神光因子。```glsl
#define CLOUD_BASE 200.0
#define CLOUD_TOP 300.0

vec4 raymarchClouds(vec3 ro, vec3 rd) {
    float tmin = (CLOUD_BASE - ro.y) / rd.y;
    float tmax = (CLOUD_TOP  - ro.y) / rd.y;
    if (tmin > tmax) { float tmp = tmin; tmin = tmp; tmax = tmp; }
    if (tmin < 0.0) tmin = 0.0;
    float t = tmin;
    vec4 sum = vec4(0.0); float rays = 0.0;
    for (int i = 0; i < 64; i++) {
        if (sum.a > 0.99 || t > tmax) break;
        vec3 pos = ro + t * rd;
        float hFrac = (pos.y - CLOUD_BASE) / (CLOUD_TOP - CLOUD_BASE);
        float shape = 1.0 - 2.0 * abs(hFrac - 0.5);
        float den = shape - 1.6 * (1.0 - noise(pos.xz * 0.01));
        if (den > 0.0) {
            float shadowDen = shape - 1.6 * (1.0 - noise((pos.xz + SUN_DIR.xz * 30.0) * 0.01));
            float shadow = clamp(1.0 - shadowDen * 2.0, 0.0, 1.0);
            vec3 cloudCol = mix(vec3(0.4, 0.4, 0.45), vec3(1.0, 0.95, 0.8), shadow);
            float alpha = clamp(den * 0.4, 0.0, 1.0);
            rays += 0.02 * shadow * (1.0 - sum.a);
            cloudCol *= alpha;
            sum += vec4(cloudCol, alpha) * (1.0 - sum.a);
        }
        t += max(0.5, 0.05 * t);
    }
    sum.rgb += pow(rays, 3.0) * 0.4 * vec3(1.0, 0.8, 0.7);
    return sum;
}
```## 表演与作曲

**性能：**
- LOD 层：低八度用于行进 (3-9)，高八度用于法线 (16)，最低用于摄像机 (3)
- 上限裁剪：行进前将光线与地形最大高度平面相交
- 自适应精度：达到阈值`abs(h) < k * t`，在距离上容忍较大的误差
- 纹理而不是噪声：预烘焙噪声的“textureLod”采样，2-3 倍速度
- 提前退出：`t > MAX_DIST`、`alpha > 0.99`、阴影`h < 0`
- 抖动开始：`t += hash(fragCoord) * step_size`以消除条带伪影

**成分：**
- 地形 + 水：固定 y 平面上的水、扰乱法线的多频噪声、控制反射/折射的菲涅耳
- 地形+体积云：先渲染地形，然后行云板，前后alpha合成
- 地形+体积雾：额外采样沿光线的 3D FBM 密度场，随距离衰减
- 地形+SDF对象：`floor(p.xz/gridSize)`网格放置，`hash(cell)`随机化
- 地形 + TAA：帧间重投影混合，~10% 新帧 + 90% 历史帧

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/terrain-rendering.md)