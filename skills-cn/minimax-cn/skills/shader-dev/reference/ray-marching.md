# Ray Marching 详细参考

本文档作为 Ray Marching Skill 的详细参考，涵盖先决条件、分步教程、数学推导和高级用法。

## 先决条件

- **GLSL 基础**：uniforms、variations、内置函数（`mix`、`clamp`、`smoothstep`、`normalize`、`dot`、`cross`、`reflect`、`refract`）
- **向量数学**：点积、叉积、向量归一化、矩阵乘法
- **坐标系**：从屏幕空间到 NDC 到视图空间到世界空间的转换
- **基本光照模型**：漫反射（Lambertian）、镜面反射（Phong/Blinn-Phong）

## 详细实施步骤

### 步骤 1：UV 坐标归一化和光线方向计算

**什么**：将像素坐标转换为 [-1,1] 范围内的标准化坐标，并计算来自相机的光线方向。

**为什么**：这建立了从屏幕像素到 3D 世界的映射。除以“iResolution.y”保留纵横比； z 分量控制视野。```glsl
// Method A: Concise version (common for quick prototyping)
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
vec3 ro = vec3(0.0, 0.0, -3.0);             // Ray origin (camera position)
vec3 rd = normalize(vec3(uv, 1.0));          // Ray direction, z=1.0 gives ~90° FOV

// Method B: Precise FOV control
vec2 xy = fragCoord - iResolution.xy / 2.0;
float z = iResolution.y / tan(radians(FOV) / 2.0); // FOV is adjustable: field of view in degrees
vec3 rd = normalize(vec3(xy, -z));
```### 步骤 2：构建相机矩阵（观察）

**什么**：从相机位置、目标点和向上方向构造一个视图矩阵，然后将视图空间光线方向转换到世界空间。

**为什么**：没有相机矩阵，光线方向固定沿-Z。通过 Look-At 矩阵，相机可以自由定位和旋转。```glsl
mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);                     // Forward direction
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);            // Up reference (cr controls roll)
    vec3 cu = normalize(cross(cw, cp));                // Right direction
    vec3 cv = cross(cu, cw);                           // Up direction
    return mat3(cu, cv, cw);
}

// Usage:
mat3 ca = setCamera(ro, ta, 0.0);
vec3 rd = ca * normalize(vec3(uv, FOCAL_LENGTH)); // FOCAL_LENGTH adjustable: 1.0~3.0, larger = narrower FOV
```### 步骤 3：定义场景 SDF

**什么**：编写一个函数，返回从空间中任意点到最近表面的有符号距离。

**为什么**：SDF 是 Ray Marching 的核心 - 它同时定义几何形状和步距。```glsl
// --- Basic SDF Primitives ---
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float sdTorus(vec3 p, vec2 t) {
    return length(vec2(length(p.xz) - t.x, p.y)) - t.y;
}

// --- CSG Boolean Operations ---
float opUnion(float a, float b)        { return min(a, b); }
float opSubtraction(float a, float b)  { return max(a, -b); }
float opIntersection(float a, float b) { return max(a, b); }

// --- Smooth Boolean Operations (organic blending) ---
float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0);
    return min(a, b) - h * h * 0.25 / k;  // k adjustable: blend radius, 0.1~0.5
}

// --- Spatial Transforms ---
// Translation: apply inverse translation to the sample point
// Rotation: multiply the sample point by a rotation matrix
// Scaling: p /= s, result *= s

// --- Scene Composition Example ---
float map(vec3 p) {
    float d = sdSphere(p - vec3(0.0, 0.5, 0.0), 0.5);   // Sphere
    d = opUnion(d, p.y);                                    // Add ground plane
    d = smin(d, sdBox(p - vec3(1.0, 0.3, 0.0), vec3(0.3)), 0.2); // Smooth blend with box
    return d;
}
```### 步骤 4：核心射线行进循环

**什么**：沿着射线方向迭代步进，使用每一步的 SDF 值来确定前进距离，并检查射线是否击中表面或超出最大范围。

**原因**：球体追踪可保证每一步都前进最大安全距离（不穿透表面），在开放区域中迈出大步，并在靠近表面时自动减速。```glsl
#define MAX_STEPS 128   // Adjustable: max step count, 64~256, more = more precise but slower
#define MAX_DIST 100.0  // Adjustable: max travel distance
#define SURF_DIST 0.001 // Adjustable: surface hit threshold, 0.0001~0.01

float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (d < SURF_DIST) return t;   // Surface hit
        t += d;
        if (t > MAX_DIST) break;        // Out of range
    }
    return -1.0; // No hit
}
```### 步骤 5：正常估计

**什么**：使用 SDF 的数值梯度计算命中点处的表面法线。

**为什么**：法线是光照计算的基础。 SDF的梯度方向是表面法线方向。```glsl
// Method A: Central differences (6 SDF calls, straightforward)
vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);  // e.x adjustable: differentiation step size
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// Method B: Tetrahedron trick (4 SDF calls, prevents compiler inline bloat, recommended)
vec3 calcNormal(vec3 pos) {
    vec3 n = vec3(0.0);
    for (int i = 0; i < 4; i++) {
        vec3 e = 0.5773 * (2.0 * vec3((((i+3)>>1)&1), ((i>>1)&1), (i&1)) - 1.0);
        n += e * map(pos + 0.001 * e);
    }
    return normalize(n);
}
```### 第 6 步：照明和阴影

**内容**：计算命中点处的 Phong 光照（环境 + 漫反射 + 镜面反射）。

**为什么**：为 SDF 表面提供带有高光和阴影渐变的逼真阴影。```glsl
vec3 shade(vec3 p, vec3 rd) {
    vec3 nor = calcNormal(p);
    vec3 lightDir = normalize(vec3(0.6, 0.35, 0.5));   // Light direction (adjustable)
    vec3 viewDir = -rd;
    vec3 halfDir = normalize(lightDir + viewDir);

    // Diffuse
    float diff = clamp(dot(nor, lightDir), 0.0, 1.0);
    // Specular
    float spec = pow(clamp(dot(nor, halfDir), 0.0, 1.0), SHININESS); // SHININESS adjustable: 8~64
    // Ambient + sky light
    float sky = sqrt(clamp(0.5 + 0.5 * nor.y, 0.0, 1.0));

    vec3 col = vec3(0.2, 0.2, 0.25);             // Material base color (adjustable)
    vec3 lin = vec3(0.0);
    lin += diff * vec3(1.3, 1.0, 0.7) * 2.2;     // Main light
    lin += sky  * vec3(0.4, 0.6, 1.15) * 0.6;    // Sky light
    lin += vec3(0.25) * 0.55;                      // Fill light
    col *= lin;
    col += spec * vec3(1.3, 1.0, 0.7) * 5.0;     // Specular highlight

    return col;
}
```### 步骤 7：后处理（伽玛校正和色调映射）

**内容**：将线性照明结果转换为 sRGB 空间并应用色调映射以防止曝光过度。

**为什么**：GPU 计算是在线性空间中完成的，但显示需要伽玛校正值。色调映射将 HDR 值压缩到 [0,1] 范围内。```glsl
// Gamma correction
col = pow(col, vec3(0.4545));  // i.e., 1/2.2

// Optional: Reinhard tone mapping (before gamma)
col = col / (1.0 + col);

// Optional: Vignette
vec2 q = fragCoord / iResolution.xy;
col *= 0.5 + 0.5 * pow(16.0 * q.x * q.y * (1.0 - q.x) * (1.0 - q.y), 0.25);
```## 常见变体详细信息

### 1.体积射线行进

**与基本版本的区别**：光线不是寻找表面交点，而是以**固定的步骤**前进，在每一步累积密度/颜色。用于火焰、烟雾和云彩。

**关键修改代码**：```glsl
#define VOL_STEPS 150       // Adjustable: volume sample count
#define VOL_STEP_SIZE 0.05  // Adjustable: step size

// Density field (built with FBM noise)
float fbmDensity(vec3 p) {
    float den = 0.2 - p.y;                                    // Base height falloff
    vec3 q = p - vec3(0.0, 1.0, 0.0) * iTime;
    float f  = 0.5000 * noise(q); q = q * 2.02 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.2500 * noise(q); q = q * 2.03 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.1250 * noise(q); q = q * 2.01 - vec3(0.0, 1.0, 0.0) * iTime;
          f += 0.0625 * noise(q);
    return den + 4.0 * f;
}

// Volumetric marching main function
vec3 volumetricMarch(vec3 ro, vec3 rd) {
    vec4 sum = vec4(0.0);
    float t = 0.05;
    for (int i = 0; i < VOL_STEPS; i++) {
        vec3 pos = ro + t * rd;
        float den = fbmDensity(pos);
        if (den > 0.0) {
            den = min(den, 1.0);
            vec3 col = mix(vec3(1.0, 0.5, 0.05), vec3(0.48, 0.53, 0.5),
                           clamp(pos.y * 0.5, 0.0, 1.0));  // Fire-to-smoke color gradient
            col *= den;
            col.a = den * 0.6;
            col.rgb *= col.a;
            sum += col * (1.0 - sum.a);                     // Front-to-back compositing
            if (sum.a > 0.99) break;                         // Early exit
        }
        t += VOL_STEP_SIZE;
    }
    return clamp(sum.rgb, 0.0, 1.0);
}
```### 2.CSG场景构建（Constructive Solid Geometry）

**与基本版本的区别**：使用“min”（并集）、“max”（交集）和“max(a,-b)”（减法）组合多个 SDF 基元，以及旋转/平移变换来创建复杂的机械零件。

**关键修改代码**：```glsl
float sceneSDF(vec3 p) {
    p = rotateY(iTime * 0.5) * p;                                // Rotate entire scene

    float sphere = sdSphere(p, 1.2);
    float cube = sdBox(p, vec3(0.9));
    float cyl = sdCylinder(p, vec2(0.4, 2.0));                   // Vertical cylinder
    float cylX = sdCylinder(p.yzx, vec2(0.4, 2.0));              // X-axis cylinder (swizzled)
    float cylZ = sdCylinder(p.xzy, vec2(0.4, 2.0));              // Z-axis cylinder

    // Sphere ∩ Cube - three-axis cylinders = nut shape
    return opSubtraction(
        opIntersection(sphere, cube),
        opUnion(cyl, opUnion(cylX, cylZ))
    );
}
```### 3. 基于物理的体积散射

**与基本版本的区别**：使用物理上正确的消光系数、散射系数和透射率公式，以及体积阴影（向光源行进以计算透射率）。基于Frostbite引擎的节能积分公式。

**关键修改代码**：```glsl
void getParticipatingMedia(out float sigmaS, out float sigmaE, vec3 pos) {
    float heightFog = 0.3 * clamp((7.0 - pos.y), 0.0, 1.0);  // Height fog
    sigmaS = 0.02 + heightFog;                                  // Scattering coefficient
    sigmaE = max(0.000001, sigmaS);                              // Extinction coefficient (includes absorption)
}

// Energy-conserving scattering integral (Frostbite improved version)
vec3 S = lightColor * sigmaS * phaseFunction() * volShadow;     // Incoming light
vec3 Sint = (S - S * exp(-sigmaE * stepLen)) / sigmaE;          // Integrate current step
scatteredLight += transmittance * Sint;                          // Accumulate
transmittance *= exp(-sigmaE * stepLen);                         // Update transmittance
```### 4. 发光累积

**与基本版本的区别**：在 Ray March 循环期间，另外跟踪从光线到表面“dM”的最近距离。即使没有击中，也会产生发光效果。常用于发光球体和等离子体。

**关键修改代码**：```glsl
vec2 rayMarchWithGlow(vec3 ro, vec3 rd) {
    float t = 0.0;
    float dMin = MAX_DIST;                    // Track minimum distance
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + t * rd;
        float d = map(p);
        if (d < dMin) dMin = d;               // Update closest distance
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }
    return vec2(t, dMin);
}

// Add glow based on dMin during shading
float glow = 0.02 / max(dMin, 0.001);        // Closer = brighter
col += glow * vec3(1.0, 0.8, 0.9);
```### 5.折射和双向行进（内部行进）

**与基本版本的区别**：撞击表面后，计算折射方向并在物体内部反向行进**（否定SDF）以找到退出点。可以实现玻璃、水和液态金属效果。

**关键修改代码**：```glsl
// Bidirectional marching: determine SDF sign based on whether the origin is inside or outside
float castRay(vec3 ro, vec3 rd) {
    float sign = (map(ro) < 0.0) ? -1.0 : 1.0;   // Negate distance if inside
    float t = 0.0;
    for (int i = 0; i < 120; i++) {
        float h = sign * map(ro + rd * t);
        if (abs(h) < 0.0001 || t > 12.0) break;
        t += h;
    }
    return t;
}

// Refraction: after hitting the outer surface, march inside along the refracted direction
vec3 refDir = refract(rd, nor, IOR);                // IOR adjustable: index of refraction, e.g., 0.9
float t2 = 2.0;
for (int i = 0; i < 50; i++) {
    float h = map(hitPos + refDir * t2);
    t2 -= h;                                         // Reverse marching (from inside outward)
    if (abs(h) > 3.0) break;
}
vec3 nor2 = calcNormal(hitPos + refDir * t2);        // Exit point normal
```## 性能优化细节

### 1. 减少 SDF 呼叫次数

- 使用四面体技巧进行正常计算（4 次调用而不是 6 次具有中心差异）
- 使用`min(iFrame,0)`作为循环起始值，以防止编译器多次展开和内联map()

### 2. 边界框加速

在行进之前执行 AABB 射线相交以跳过空白区域：```glsl
vec2 tb = iBox(ro - center, rd, halfSize);
if (tb.x < tb.y && tb.y > 0.0) { /* Only march inside the box */ }
```### 3.自适应精度

- 根据距离缩放命中阈值：`SURF_DIST * (1.0 + t * 0.1)` — 远处的表面不需要高精度
- 钳位步长：`t +=钳位(h, 0.01, 0.2)` — 防止单个步长太大或太小

### 4.提前退出

- 在体积渲染中：`if (sum.a > 0.99) break;` — 当不透明时立即停止
- 在阴影计算中：`if (res < 0.004) break;` — 完全遮挡时停止

### 5. 降低map()复杂度

- 对远处的物体使用简化的 SDF
- 使用廉价的边界 SDF 进行首次测试；仅当 sdBox(p,bound) < currentMin 时计算昂贵的精确 SDF

### 6. 抗锯齿

- 超级采样（AA=2 表示 2x2 采样，每像素 4 条光线），但性能成本为 4 倍
- 在体积渲染中，使用抖动而不是超级采样来减少条带伪影

## 详细组合建议

### 1. 光线行进 + FBM 噪声

使用分形噪声扰乱 SDF 表面的地形和岩石纹理，或构建体积密度场来渲染云/烟雾。

### 2. 光线行进 + 域扭曲

将空间扭曲（扭曲、弯曲、重复）应用于采样点，以创建无限重复的走廊或扭曲的超现实几何形状。

### 3. 光线行进 + PBR 材质

SDF提供几何图形；与 Cook-Torrance BRDF、环境贴图反射和菲涅耳项相结合，实现真实的金属/电介质材料。

### 4. 光线行进 + 后处理

Multi-pass架构：第一个Buffer执行Ray Marching并输出颜色+深度（存储在alpha通道中）；第二遍应用景深 (DOF)、运动模糊和色调映射。

### 5.光线行进+程序动画

使用时间参数驱动 SDF 基元位置/大小/混合系数，结合缓动函数（平滑步长、抛物线），无需骨骼系统即可创建角色动画。