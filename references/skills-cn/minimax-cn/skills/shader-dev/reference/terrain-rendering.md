# Heightfield Ray Marching 地形渲染 - 详细参考

> 本文档是对 [SKILL.md](SKILL.md) 的详细补充，涵盖先决条件、每个步骤的完整说明（内容/原因）、变体详细信息、深入的性能优化分析以及组合建议的完整代码示例。

## 先决条件

- **GLSL 基础知识**：uniforms、variations、内置函数（mix、smoothstep、clamp、fract、floor）
- **向量数学**：点积、叉积、矩阵变换、法线计算
- **基本光线行进概念**：从相机投射光线，沿着光线前进，检测交叉点
- **噪声函数**：值噪声/梯度噪声的基本原理（网格采样+插值）
- **FBM（分形布朗运动）**：分层多个噪声八度音阶以构建分形细节

## 实施步骤

### 步骤 1：噪声和哈希函数

**内容**：实施 2D 值噪声，为 FBM 提供基本采样功能。

**为什么**：地形着色器根据噪声构建地形。 Value Noise通过网格点哈希+双线性插值生成连续的伪随机场。基于旋转的哈希避免了某些 GPU 上“sin()”的精度问题。插值使用 Hermite smoothstep `3t²-2t³` 来确保 C1 连续性。

**代码**：```glsl
// === Hash Function ===
// High-quality hash without sin
// Uses fract-dot pattern, avoiding sin() precision issues
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}

// === 2D Value Noise ===
// Grid sampling + Hermite interpolation, returns [0,1]
float noise(in vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f); // Hermite smoothstep

    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
```### 步骤 2：噪声与分析导数（高级）

**内容**：返回噪声值及其解析偏导数 `∂n/∂x` 和 `∂n/∂y`。

**为什么**：分析导数是实现“侵蚀地形”的关键 - 在 FBM 中累积导数可以抑制陡坡上的细节分层（在步骤 3 中使用）。该技术广泛应用于地形着色器中。导数公式来自 Hermite 插值的链式法则微分：“du = 6f(1-f)”。

**代码**：```glsl
// === 2D Value Noise with Analytical Derivatives ===
// Returns vec3: .x = noise value, .yz = partial derivatives (dn/dx, dn/dy)
vec3 noised(in vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);

    // Hermite interpolation and its derivative
    vec2 u  = f * f * (3.0 - 2.0 * f);
    vec2 du = 6.0 * f * (1.0 - f);

    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    float value = a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
    vec2  deriv = du * (vec2(b - a, c - a) + (a - b - c + d) * u.yx);

    return vec3(value, deriv);
}
```### 步骤 3：FBM 地形高度场（带有导数侵蚀）

**内容**：将多个噪声八度音阶分层以构建地形高度场，使用导数累积来模拟侵蚀效果。

**为什么**：FBM 是地形生成核心。主要区别在于**是否使用导数抑制**：
- **没有衍生品**：简单的分层，地形显得更加“粗糙”
- **具有导数抑制**：“1/(1+dot(d,d))”项抑制陡坡上的高频细节，产生真实的山脊/山谷结构

旋转矩阵“m2”在每层之间旋转采样坐标，打破轴对齐的视觉条带。 `mat2(0.8,-0.6, 0.6,0.8)` 旋转大约 37°，单位行列式（纯旋转，无缩放）——地形 FBM 的标准选择。

**代码**：```glsl
#define TERRAIN_OCTAVES 9   // Tunable: 3=rough outline, 9=medium detail, 16=highest precision (for normals)
#define TERRAIN_SCALE 0.003 // Tunable: controls terrain spatial frequency, smaller = "wider" terrain
#define TERRAIN_HEIGHT 120.0 // Tunable: terrain elevation scale

// Per-layer rotation matrix: ~37° pure rotation, eliminates axis-aligned banding
const mat2 m2 = mat2(0.8, -0.6, 0.6, 0.8);

// === FBM Terrain Heightfield (Derivative Erosion Version) ===
// Input: 2D world coordinates (xz plane)
// Output: scalar height value
float terrain(in vec2 p) {
    p *= TERRAIN_SCALE;

    float a = 0.0;   // Accumulated height
    float b = 1.0;   // Current amplitude
    vec2  d = vec2(0.0); // Accumulated derivatives

    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        vec3 n = noised(p);          // .x=value, .yz=derivatives
        d += n.yz;                    // Accumulate gradient
        a += b * n.x / (1.0 + dot(d, d)); // Derivative suppression: contribution reduced on steep slopes
        b *= 0.5;                     // Amplitude halved per layer
        p = m2 * p * 2.0;            // Rotate + double frequency
    }

    return a * TERRAIN_HEIGHT;
}
```### 步骤 4：LOD 多分辨率地形函数

**什么**：为不同的目的创建不同精度级别的地形函数。

**为什么**：这是一个经典的优化 - 光线行进只需要粗略的高度（更少的 FBM 层），正常计算需要细节（更多的 FBM 层），而相机放置只需要最粗略的估计。双功能方案（行进时粗略，法线精细）是地形着色器的标准做法。

**代码**：```glsl
#define OCTAVES_LOW 3     // Tunable: for camera placement, fastest
#define OCTAVES_MED 9     // Tunable: for ray marching
#define OCTAVES_HIGH 16   // Tunable: for normal calculation, finest detail

// Low precision (camera height, far distance)
float terrainL(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < OCTAVES_LOW; i++) {
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}

// Medium precision (ray marching)
float terrainM(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < OCTAVES_MED; i++) {
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}

// High precision (normal calculation)
float terrainH(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0, b = 1.0;
    vec2  d = vec2(0.0);
    for (int i = 0; i < OCTAVES_HIGH; i++) {
        vec3 n = noised(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}
```### 步骤 5：自适应步长射线行进

**内容**：从相机投射光线，并以自适应步骤沿着光线前进，找到与地形高度场的交点。

**为什么**：地形是一个高度场（不是任意的 SDF），因此“ray.y - 地形（ray.xz）”可以用作保守的步长估计。常见的地形着色器采用三种策略：
- **保守因子方法**：`step = 0.4 × h`（保守因子 0.4，防止超过尖锐的山脊，300 步）
- **放松行进**：`step = h × max(t×0.02, 1.0)`，步长随着距离自动增加（90步覆盖更大范围）
- **自适应行进 + 二元细化**：自适应行进 + 5 个二元细化步骤（150 步 + 精确交集）

该模板采用保守因子法+距离自适应精度阈值，平衡精度和效率。

**代码**：```glsl
#define MAX_STEPS 300       // Tunable: march steps, 80=fast, 300=high quality
#define MAX_DIST 5000.0     // Tunable: maximum render distance
#define STEP_FACTOR 0.4     // Tunable: march conservative factor, 0.3=safe, 0.8=aggressive

// === Ray Marching ===
// ro: ray origin, rd: ray direction (normalized)
// Returns: intersection distance t (-1.0 means miss)
float raymarch(in vec3 ro, in vec3 rd) {
    float t = 0.0;

    // Upper bound clipping: skip if ray cannot possibly hit terrain
    // Assumes terrain max height is TERRAIN_HEIGHT
    if (ro.y > TERRAIN_HEIGHT && rd.y >= 0.0) return -1.0;
    if (ro.y > TERRAIN_HEIGHT) {
        t = (ro.y - TERRAIN_HEIGHT) / (-rd.y); // Fast jump to terrain height upper bound
    }

    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 pos = ro + t * rd;
        float h = pos.y - terrainM(pos.xz); // Height difference = ray y - terrain height

        // Adaptive precision: tolerate larger error at distance (screen-space equivalent)
        if (abs(h) < 0.0015 * t) break;
        if (t > MAX_DIST) return -1.0;

        t += STEP_FACTOR * h; // Advance proportionally to height difference
    }

    return t;
}
```### 步骤 6：二值化细化（可选）

**什么**：在光线行进找到的粗略交叉点附近执行二分搜索，以精确定位地形表面。

**为什么**：射线行进仅保证相交在某个区间内；二分查找将误差收敛为 2^5=32x。这对于尖锐的山脊轮廓尤其重要。类似的“后退一半”策略在地形着色器中很常见。

**代码**：```glsl
#define BISECT_STEPS 5 // Tunable: binary search steps, 5 steps = 32x precision improvement

// === Binary Refinement ===
// ro: ray origin, rd: ray direction
// tNear: last t above terrain, tFar: first t below terrain
float bisect(in vec3 ro, in vec3 rd, float tNear, float tFar) {
    for (int i = 0; i < BISECT_STEPS; i++) {
        float tMid = 0.5 * (tNear + tFar);
        vec3 pos = ro + tMid * rd;
        float h = pos.y - terrainM(pos.xz);
        if (h > 0.0) {
            tNear = tMid; // Still above terrain, advance forward
        } else {
            tFar = tMid;  // Below terrain, pull back
        }
    }
    return 0.5 * (tNear + tFar);
}
```###第七步：正常计算

**什么**：使用有限差分计算交点处的地形表面法线。

**为什么**：法线是所有光照计算的基础。一个关键的优化是 **epsilon 随着距离而增加** - 在距离处使用较粗的 epsilon 可以避免高频噪声造成的混叠。此处使用高精度地形函数“terrainH”来获取正常细节。

**代码**：```glsl
// === Normal Calculation (Finite Differences) ===
// pos: surface intersection point, t: distance (for adaptive epsilon)
vec3 calcNormal(in vec3 pos, float t) {
    // Adaptive epsilon: fine up close, coarse at distance (avoids aliasing)
    float eps = 0.02 + 0.00005 * t * t;

    float hC = terrainH(pos.xz);
    float hR = terrainH(pos.xz + vec2(eps, 0.0));
    float hU = terrainH(pos.xz + vec2(0.0, eps));

    // Finite difference normal
    return normalize(vec3(hC - hR, eps, hC - hU));
}
```### 第 8 步：材质和颜色分配

**内容**：根据高度、坡度、噪音和其他条件混合不同的材质颜色。

**原因**：自然地形颜色分层是视觉说服力的关键。几乎所有地形着色器都遵循以下分层逻辑：
- **岩石**：陡峭的表面（法向 y 分量较小）→ 灰色岩石
- **草**：平坦的低海拔表面→绿色
- **雪**：高海拔平坦表面→白色
- **沙子**：接近水位→沙子颜色

使用“smoothstep”在层之间实现平滑过渡，并使用 FBM 噪声来打破过渡线规律性。

**代码**：```glsl
#define SNOW_HEIGHT 80.0     // Tunable: snow line altitude
#define TREE_HEIGHT 45.0     // Tunable: tree line altitude
#define BEACH_HEIGHT 1.5     // Tunable: beach height

// === Material Color ===
// pos: world coordinates, nor: normal
vec3 getMaterial(in vec3 pos, in vec3 nor) {
    // Slope factor: nor.y=1 means horizontal, nor.y=0 means vertical
    float slope = nor.y;
    float h = pos.y;

    // Noise to break up transition lines
    float nz = noise(pos.xz * 0.04) * noise(pos.xz * 0.005);

    // Base rock color
    vec3 rock = vec3(0.10, 0.09, 0.08);

    // Dirt/grass color (flat surfaces)
    vec3 grass = mix(vec3(0.10, 0.08, 0.04), vec3(0.05, 0.09, 0.02), nz);

    // Snow color
    vec3 snow = vec3(0.62, 0.65, 0.70);

    // Sand color
    vec3 sand = vec3(0.50, 0.45, 0.35);

    // --- Layered blending ---
    vec3 col = rock;

    // Flat areas: rock → grass
    col = mix(col, grass, smoothstep(0.5, 0.8, slope));

    // High altitude: → snow (slope + height + noise)
    float snowMask = smoothstep(SNOW_HEIGHT - 20.0 * nz, SNOW_HEIGHT + 10.0, h)
                   * smoothstep(0.3, 0.7, slope);
    col = mix(col, snow, snowMask);

    // Low altitude: → sand
    float beachMask = smoothstep(BEACH_HEIGHT + 1.0, BEACH_HEIGHT - 0.5, h)
                    * smoothstep(0.5, 0.9, slope);
    col = mix(col, sand, beachMask);

    return col;
}
```### 步骤 9：光照模型

**内容**：实现多分量光照：太阳漫反射 + 半球环境光 + 背光填充 + 镜面反射。

**为什么**：地形光照模型共享一致的核心组件：
- **兰伯特漫反射**：`dot(N, L)` — 基本成分
- **半球环境**：`0.5 + 0.5 * N.y` — 标准地形环境照明
- **背光**：从与太阳相反的水平方向补光
- **菲涅尔边缘光**：`pow(1+dot(rd,N), 2~5)` — 边缘发光效果
- **镜面反射**：Phong/Blinn-Phong，功率范围从 3 到 500

**代码**：```glsl
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6)) // Tunable: sun direction
#define SUN_COL vec3(8.0, 5.0, 3.0)              // Tunable: sun color temperature (warm light)
#define SKY_COL vec3(0.5, 0.7, 1.0)              // Tunable: sky color

// === Lighting Calculation ===
vec3 calcLighting(in vec3 pos, in vec3 nor, in vec3 rd, float shadow) {
    vec3 sunDir = SUN_DIR;

    // Diffuse (Lambert)
    float dif = clamp(dot(nor, sunDir), 0.0, 1.0);

    // Hemisphere ambient: facing up=full brightness, facing down=half brightness
    float amb = 0.5 + 0.5 * nor.y;

    // Backlight fill (horizontal direction opposite the sun)
    vec3 backDir = normalize(vec3(-sunDir.x, 0.0, -sunDir.z));
    float bac = clamp(0.2 + 0.8 * dot(nor, backDir), 0.0, 1.0);

    // Fresnel rim light
    float fre = pow(clamp(1.0 + dot(rd, nor), 0.0, 1.0), 2.0);

    // Specular (Blinn-Phong)
    vec3 hal = normalize(sunDir - rd);
    float spe = pow(clamp(dot(nor, hal), 0.0, 1.0), 16.0)
              * (0.04 + 0.96 * pow(1.0 + dot(hal, rd), 5.0)); // Fresnel term

    // Combine
    vec3 lin = vec3(0.0);
    lin += dif * shadow * SUN_COL * 0.1;          // Sun diffuse
    lin += amb * SKY_COL * 0.2;                    // Sky ambient
    lin += bac * vec3(0.15, 0.05, 0.04);           // Backlight (warm tone)
    lin += fre * SKY_COL * 0.3;                    // Rim light
    lin += spe * shadow * SUN_COL * 0.05;          // Specular

    return lin;
}
```### 第10步：软阴影

**什么**：从表面交点向太阳投射阴影光线，计算带有半影的柔和阴影。

**为什么**：柔和的阴影极大地增强了地形的空间深度。经典技术 - 在阴影射线行进期间，跟踪“min(k*h/t)”，其中 h 是距地形的高度距离，t 是行进距离。较小的比率 = 射线掠过地形表面 = 半影区域。 k 参数控制半影柔软度（k=16 表示软，k=64 表示硬）。

**代码**：```glsl
#define SHADOW_STEPS 80     // Tunable: shadow ray steps, 32=fast, 80=high quality
#define SHADOW_K 16.0       // Tunable: penumbra softness, 8=very soft, 64=very hard

// === Soft Shadows ===
// pos: surface point, sunDir: sun direction
float calcShadow(in vec3 pos, in vec3 sunDir) {
    float res = 1.0;
    float t = 1.0; // Start slightly above the surface to avoid self-intersection

    for (int i = 0; i < SHADOW_STEPS; i++) {
        vec3 p = pos + t * sunDir;
        float h = p.y - terrainM(p.xz);

        if (h < 0.001) return 0.0; // Full shadow

        // Penumbra estimate: smaller h/t = ray closer to occlusion
        res = min(res, SHADOW_K * h / t);
        t += clamp(h, 2.0, 100.0); // Adaptive step size
    }

    return clamp(res, 0.0, 1.0);
}
```### 第 11 步：空中透视和雾

**什么**：随着距离的增加，将地形颜色与雾颜色混合，实现空中透视效果。

**为什么**：大气效果是将像素“推”到远处的关键视觉提示。常见的方法从简单到复杂：
- **指数雾**：`exp(-0.00005 * t^2)` — 最简单
- **指数 + 高度衰减雾**：`exp(-pow(k*t, 1.5))` — 低海拔较密，高海拔较薄
- **依赖于波长的雾**：`exp(-t * vec3(1,1.5,4) * k)` — 蓝光衰减更快，红光传播更远，逼真的大气色散
- **完全瑞利+米氏散射**：物理上准确但昂贵

**代码**：```glsl
#define FOG_DENSITY 0.00025  // Tunable: fog density
#define FOG_HEIGHT 0.001     // Tunable: height decay coefficient (0=no height dependency)

// === Atmospheric Fog ===
// col: original color, t: distance, rd: ray direction
vec3 applyFog(in vec3 col, float t, in vec3 rd) {
    // Wavelength-dependent attenuation: blue attenuates 4x faster than red
    vec3 extinction = exp(-t * FOG_DENSITY * vec3(1.0, 1.5, 4.0));

    // Fog color: base blue-gray + sun direction scattering (warm tones)
    float sundot = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    vec3 fogCol = mix(vec3(0.55, 0.55, 0.58),         // Base fog color
                      vec3(1.0, 0.7, 0.3),              // Sun scatter color
                      0.3 * pow(sundot, 8.0));

    return col * extinction + fogCol * (1.0 - extinction);
}
```### 第 12 步：天空渲染

**内容**：绘制背景天空，包括渐变、日盘和地平线辉光。

**为什么**：天空是大气情绪的重要组成部分。所有具有 3D 视点的地形着色器都包含天空渲染。关键部件：
- 天顶到地平线蓝色→白色渐变
- 地平线辉光带（`pow(1-rd.y, n)`系列）
- 太阳盘和光环（`pow(sundot, high power)`系列）

**代码**：```glsl
// === Sky Color ===
vec3 getSky(in vec3 rd) {
    // Base sky gradient: zenith blue → horizon white
    vec3 col = vec3(0.3, 0.5, 0.85) - rd.y * vec3(0.2, 0.15, 0.0);

    // Horizon glow
    float horizon = pow(1.0 - max(rd.y, 0.0), 4.0);
    col = mix(col, vec3(0.8, 0.75, 0.7), 0.5 * horizon);

    // Sun
    float sundot = clamp(dot(rd, SUN_DIR), 0.0, 1.0);
    col += vec3(1.0, 0.7, 0.3) * 0.3 * pow(sundot, 8.0);   // Large halo
    col += vec3(1.0, 0.9, 0.7) * 0.5 * pow(sundot, 64.0);   // Small halo
    col += vec3(1.0, 1.0, 0.9) * min(pow(sundot, 1150.0), 0.3); // Sun disk

    return col;
}
```### 第 13 步：相机设置

**内容**：构建观察相机矩阵并定义飞行路径。

**为什么**：地形飞越摄像机通常遵循利萨如曲线或弧线路径，高度跟随地形。 Look-At 矩阵将屏幕坐标映射到世界空间光线方向。

**代码**：```glsl
#define CAM_ALTITUDE 20.0   // Tunable: camera height above ground
#define CAM_SPEED 0.5       // Tunable: flight speed

// === Camera Path ===
vec3 cameraPath(float t) {
    return vec3(
        100.0 * sin(0.2 * t),  // x: sine curve
        0.0,                     // y: determined by terrain height
        -100.0 * t               // z: forward direction
    );
}

// === Camera Matrix ===
mat3 setCamera(in vec3 ro, in vec3 ta) {
    vec3 cw = normalize(ta - ro);
    vec3 cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0)));
    vec3 cv = cross(cu, cw);
    return mat3(cu, cv, cw);
}
```## 常见变体

### 变式 1：放松行进

**与基本版本的区别**：步长随着距离自动增加，覆盖范围更大，但精度略有降低。保守因子被距离自适应松弛因子取代，同时高度估计被缩小以防止穿透。

**关键代码**：```glsl
#define RELAX_MAX_STEPS 90       // Fewer steps needed to cover greater distance
#define RELAX_FAR 400.0

float raymarchRelax(in vec3 ro, in vec3 rd) {
    float t = 0.0;
    float d = (ro + rd * t).y - terrainM((ro + rd * t).xz);

    for (int i = 0; i < RELAX_MAX_STEPS; i++) {
        if (abs(d) < t * 0.0001 || t > RELAX_FAR) break;

        float rl = max(t * 0.02, 1.0); // Relaxation factor: larger steps at distance
        t += d * rl;
        vec3 pos = ro + rd * t;
        d = (pos.y - terrainM(pos.xz)) * 0.7; // 0.7 attenuation prevents penetration
    }
    return t;
}
```### 变体 2：符号交替 FBM

**与基础版本的区别**：翻转每层的幅度符号（`w = -w * 0.4`），产生独特的交替脊/谷图案。不使用导数抑制 - 风格与侵蚀版本明显不同，产生更加“锯齿状和扭曲”的外观。

**关键代码**：```glsl
float terrainSignFlip(in vec2 p) {
    p *= TERRAIN_SCALE;
    float a = 0.0;
    float w = 1.0; // Initial weight

    for (int i = 0; i < TERRAIN_OCTAVES; i++) {
        a += w * noise(p);
        w = -w * 0.4;    // Sign flip + decay: alternating addition and subtraction
        p = m2 * p * 2.0;
    }
    return a * TERRAIN_HEIGHT;
}
```### 变体 3：纹理驱动的高度场 + 3D 位移

**与基础版本的区别**：使用纹理采样作为基础高度场，3D FBM 位移分层在顶部以产生悬崖、洞穴和其他非高度场地层。需要额外的纹理通道输入，但可以创建比纯 FBM 更多的地形多样性。行进成为真正的自卫队球体追踪。

**关键代码**：```glsl
// 3D Value Noise
float noise3D(in vec3 x) {
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    // 3D→2D flattening: offset UV by p.z, sample two texture layers and interpolate
    vec2 uv = (p.xy + vec2(37.0, 17.0) * p.z) + f.xy;
    vec2 rg = textureLod(iChannel0, (uv + 0.5) / 256.0, 0.0).yx;
    return mix(rg.x, rg.y, f.z);
}

// 3D FBM Displacement
const mat3 m3 = mat3(0.00, 0.80, 0.60,
                    -0.80, 0.36,-0.48,
                    -0.60,-0.48, 0.64);

float displacement(vec3 p) {
    float f = 0.5 * noise3D(p); p = m3 * p * 2.02;
    f += 0.25 * noise3D(p);    p = m3 * p * 2.03;
    f += 0.125 * noise3D(p);   p = m3 * p * 2.01;
    f += 0.0625 * noise3D(p);
    return f;
}

// SDF: heightfield + 3D displacement (supports cliffs/caves)
float mapCanyon(vec3 p) {
    float h = terrainM(p.xz);
    float dis = displacement(0.25 * p * vec3(1.0, 4.0, 1.0)) * 3.0;
    return (dis + p.y - h) * 0.25;
}
```### 变体 4：定向侵蚀噪声

**与基础版本的区别**：使用斜率方向作为Gabor噪声的投影方向。每个侵蚀层都会根据前一层的导数调整“水流方向”，产生逼真的树枝状排水模式。需要多通道高度图预计算。

**关键代码**：```glsl
#define EROSION_OCTAVES 5
#define EROSION_BRANCH 1.5 // Tunable: branching strength, 0=parallel, 2=strong branching

// Directional Gabor noise
vec3 erosionNoise(vec2 p, vec2 dir) {
    vec2 ip = floor(p); vec2 fp = fract(p) - 0.5;
    float va = 0.0; float wt = 0.0;
    vec2 dva = vec2(0.0);

    for (int i = -2; i <= 1; i++)
    for (int j = -2; j <= 1; j++) {
        vec2 o = vec2(float(i), float(j));
        vec2 h = hash2(ip - o) * 0.5; // Grid point random offset
        vec2 pp = fp + o + h;
        float d = dot(pp, pp);
        float w = exp(-d * 2.0);       // Gaussian weight
        float mag = dot(pp, dir);       // Directional projection
        va += cos(mag * 6.283) * w;     // Directional ripple
        dva += -sin(mag * 6.283) * dir * w;
        wt += w;
    }
    return vec3(va, dva) / wt;
}

// Erosion FBM: direction evolves with slope
float terrainErosion(vec2 p, vec2 baseSlope) {
    float e = 0.0, a = 0.5;
    vec2 dir = normalize(baseSlope + vec2(0.001));

    for (int i = 0; i < EROSION_OCTAVES; i++) {
        vec3 n = erosionNoise(p * 4.0, dir);
        e += a * n.x;
        // Branching: curl of previous layer's derivative modifies water flow direction
        dir = normalize(dir + n.zy * vec2(1.0, -1.0) * EROSION_BRANCH);
        a *= 0.5;
        p *= 2.0;
    }
    return e;
}
```### 变体 5：体积云 + 上帝射线

**与基础版本的区别**：使用前后 alpha 合成在地形上方添加体积云层，并在行进过程中累积上帝射线因子。需要 3D 噪声和更多步骤，显着增加成本，但具有出色的视觉效果。

**关键代码**：```glsl
#define CLOUD_STEPS 64        // Tunable: cloud march steps
#define CLOUD_BASE 200.0      // Tunable: cloud layer base height
#define CLOUD_TOP 300.0       // Tunable: cloud layer top height

vec4 raymarchClouds(vec3 ro, vec3 rd) {
    // Calculate intersections with cloud slab
    float tmin = (CLOUD_BASE - ro.y) / rd.y;
    float tmax = (CLOUD_TOP  - ro.y) / rd.y;
    if (tmin > tmax) { float tmp = tmin; tmin = tmp; tmax = tmp; } // swap
    if (tmin < 0.0) tmin = 0.0;

    float t = tmin;
    vec4 sum = vec4(0.0); // rgb=color, a=opacity
    float rays = 0.0;     // God ray accumulation

    for (int i = 0; i < CLOUD_STEPS; i++) {
        if (sum.a > 0.99 || t > tmax) break;
        vec3 pos = ro + t * rd;

        // Cloud density: slab shape × FBM carving
        float hFrac = (pos.y - CLOUD_BASE) / (CLOUD_TOP - CLOUD_BASE);
        float shape = 1.0 - 2.0 * abs(hFrac - 0.5); // Densest in the middle
        float den = shape - 1.6 * (1.0 - noise(pos.xz * 0.01)); // Simplified FBM

        if (den > 0.0) {
            // Cloud lighting: offset sample toward sun direction (self-shadowing)
            float shadowDen = shape - 1.6 * (1.0 - noise((pos.xz + SUN_DIR.xz * 30.0) * 0.01));
            float shadow = clamp(1.0 - shadowDen * 2.0, 0.0, 1.0);

            vec3 cloudCol = mix(vec3(0.4, 0.4, 0.45), vec3(1.0, 0.95, 0.8), shadow);
            float alpha = clamp(den * 0.4, 0.0, 1.0);

            // God rays: brightness of sunlight passing through thin areas
            rays += 0.02 * shadow * (1.0 - sum.a);

            // Front-to-back compositing
            cloudCol *= alpha;
            sum += vec4(cloudCol, alpha) * (1.0 - sum.a);
        }

        float dt = max(0.5, 0.05 * t);
        t += dt;
    }

    // Add god rays to color
    sum.rgb += pow(rays, 3.0) * 0.4 * vec3(1.0, 0.8, 0.7);
    return sum;
}
```## 深入的性能优化

### 1. LOD分层（最重要的优化）
**瓶颈**：每个FBM层都需要独立的噪声样本；倍频程数是直接的性能乘数。
**优化**：使用低八度进行光线行进（3-9 层），使用高八度进行正常计算（16 层），使用最低八度进行相机放置（3 层）。这是地形着色器的标准做法。

### 2. 上限裁剪（边界平面）
**瓶颈**：光线在露天中浪费迭代。
**优化**：预先计算最大地形高度，并在开始行进之前使射线与该平面相交。```glsl
if (ro.y > maxHeight && rd.y >= 0.0) return -1.0; // Skip entirely
t = (ro.y - maxHeight) / (-rd.y); // Jump to upper bound
```### 3.自适应精度阈值
**瓶颈**：远距离像素仍然使用近场精度，浪费迭代。
**优化**：命中阈值随着距离的增加而增长：`abs(h) < 0.001 * t`。这是常见做法，系数通常介于 0.0001 到 0.002 之间。

### 4. 纹理代替程序噪声
**瓶颈**：程序噪声需要多次哈希和插值操作。
**优化**：预烘焙 256x256 噪声纹理并使用“textureLod”进行采样。与程序噪声相比，速度提高了大约 2-3 倍。

### 5.提前退出
**瓶颈**：光线超出范围后继续迭代。
**优化**：
- `t > MAX_DIST` 爆发
- 体积渲染中“alpha > 0.99”爆发
- `h < 0` 在阴影光线中立即返回 0

### 6. 启动抖动
**瓶颈**：均匀步进会产生可见的条带伪影。
**优化**：将每像素随机偏移添加到起始 t：`t += hash(fragCoord) * step_size`。不增加计算成本，但显着提高视觉质量。

## 完整的组合代码示例

### 1.地形+水面
最常见的地形渲染组合。水面作为固定的y平面——先行进地形，如果光线与水面以下的地形相交，则渲染水下效果；否则渲染水面反射/折射。
- 重点：水面法线使用多频噪声扰动来模拟波浪；菲涅尔控制反射/折射混合```glsl
#define WATER_LEVEL 5.0

// Water surface normal (multi-frequency noise perturbation)
vec3 waterNormal(vec2 p, float t) {
    float eps = 0.1;
    float h0 = noise(p * 0.5 + iTime * 0.3) * 0.5
             + noise(p * 1.5 - iTime * 0.2) * 0.25;
    float hx = noise((p + vec2(eps, 0.0)) * 0.5 + iTime * 0.3) * 0.5
             + noise((p + vec2(eps, 0.0)) * 1.5 - iTime * 0.2) * 0.25;
    float hz = noise((p + vec2(0.0, eps)) * 0.5 + iTime * 0.3) * 0.5
             + noise((p + vec2(0.0, eps)) * 1.5 - iTime * 0.2) * 0.25;
    return normalize(vec3(h0 - hx, eps, h0 - hz));
}

// In the main function:
// 1. Check water surface intersection first
float tWater = (ro.y - WATER_LEVEL) / (-rd.y);
// 2. Compare with terrain intersection
float tTerrain = raymarch(ro, rd);

vec3 col;
if (tWater > 0.0 && (tTerrain < 0.0 || tWater < tTerrain)) {
    // Hit water surface
    vec3 wpos = ro + tWater * rd;
    vec3 wnor = waterNormal(wpos.xz, tWater);

    // Fresnel
    float fresnel = pow(1.0 - max(dot(-rd, wnor), 0.0), 5.0);
    fresnel = 0.02 + 0.98 * fresnel;

    // Reflection
    vec3 refl = reflect(rd, wnor);
    vec3 reflCol = getSky(refl);

    // Underwater color
    vec3 waterCol = vec3(0.0, 0.04, 0.04);

    col = mix(waterCol, reflCol, fresnel);
    col = applyFog(col, tWater, rd);
} else if (tTerrain > 0.0) {
    // Hit terrain (same as original code)
    // ...
}
```### 2.地形+体积云
首先渲染地形以获得颜色和深度，然后沿着光线行进云板，使用从前到后的 Alpha 混合将其合成到地形上。
- 关键：云自阴影（向光方向偏移采样）、上帝射线累积```glsl
// In the main function:
vec3 col;
float t = raymarch(ro, rd);

if (t > 0.0) {
    // Render terrain...
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

// Overlay volumetric clouds
vec4 clouds = raymarchClouds(ro, rd);
col = col * (1.0 - clouds.a) + clouds.rgb;
```### 3.地形+体积雾/灰尘
体积尘雾可以在主行进完成后添加，另外沿着射线采样 3D FBM 密度场，并进行基于距离的衰减。适合沙漠、火山等类似场景。
- 关键：步长适应密度 - 密集区域中的步长较小

### 4. 地形 + SDF 对象放置
SDF 椭球可以像树木一样放置在地形上。地形行进和物体行进可以分开或组合。对象被放置在具有基于哈希的抖动的二维网格上。
- 键：“floor(p.xz/gridSize)”确定网格单元，“hash(cell)”确定树位置/大小```glsl
#define TREE_GRID 30.0

// Place tree SDFs in a grid
float mapTrees(vec3 p) {
    vec2 cell = floor(p.xz / TREE_GRID);
    vec2 cellCenter = (cell + 0.5) * TREE_GRID;

    // Hash to randomize position
    vec2 jitter = (hash2(cell) - 0.5) * TREE_GRID * 0.6;
    vec2 treePos = cellCenter + jitter;

    // Tree trunk height
    float groundH = terrainL(treePos);

    // SDF: ellipsoid tree canopy
    vec3 treeCenter = vec3(treePos.x, groundH + 8.0, treePos.y);
    float treeSize = 4.0 + hash(cell) * 3.0;
    vec3 q = (p - treeCenter) / vec3(treeSize, treeSize * 1.5, treeSize);
    return (length(q) - 1.0) * treeSize * 0.8;
}
```### 5. 地形 + 时间抗锯齿 (TAA)
帧间重投影混合可用于时间抗锯齿。当前帧的相机矩阵存储在缓冲区像素中，下一帧使用它将 3D 点重新投影回前一帧的屏幕坐标，从而混合历史颜色。
- 关键：混合比例 ~10% 新帧 + 90% 历史帧，运动区域增加新帧权重