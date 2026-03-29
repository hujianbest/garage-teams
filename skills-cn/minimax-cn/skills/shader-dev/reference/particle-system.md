# 粒子系统 — 详细参考

本文档是SKILL.md的详细补充，包含先决条件、每个步骤的深入解释、变体细节、性能优化分析以及组合建议的完整代码。

> **注意：** 本文档中的代码示例主要针对 ShaderToy 环境。 **对于独立的 HTML 部署，请参考 SKILL.md 中的 WebGL2 单文件模板**，其中包含完整的 HTML + JS + GLSL 代码。

## 先决条件

- GLSL基本语法（统一、变化、内置函数）
- 2D/3D 向量数学（点积、叉积、归一化、矩阵旋转）
- ShaderToy 架构（`mainImage`、`iTime`、`iResolution`、`iChannel`、多缓冲区通道）
- 基本物理概念：速度=位置的导数，加速度=力/质量
- 使用“texelFetch”（从缓冲区读取精确的像素数据）

## 详细实施步骤

### 步骤 1：哈希随机函数

**什么**：定义一个从浮点数（粒子 ID）生成伪随机数的函数。这是所有粒子系统的基础设施。

**为什么**：每个粒子都需要独特但确定性的属性（颜色、大小、初始方向等）；哈希函数提供可重复的“随机性”。

提供了三个哈希函数维度：
- `hash11`：1D → 1D，用于标量随机性（寿命、亮度等）
- `hash12`：1D → 2D，用于 2D 随机性（初始位置等）
- `hash33`：3D → 3D，用于 3D 速度扰动```glsl
// Standard 1D -> 1D hash, returns [0, 1)
float hash11(float p) {
    return fract(sin(p * 127.1) * 43758.5453);
}

// 1D -> 2D hash, for 2D randomness
vec2 hash12(float p) {
    vec3 p3 = fract(vec3(p) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

// 3D -> 3D hash, for 3D velocity perturbation
vec3 hash33(vec3 p) {
    p = fract(p * vec3(443.897, 397.297, 491.187));
    p += dot(p.zxy, p.yxz + 19.19);
    return fract(vec3(p.x * p.y, p.z * p.x, p.y * p.z)) - 0.5;
}
```### 第 2 步：粒子生命周期管理

**内容**：计算每个粒子的出生时间、寿命、当前年龄以及死亡后的自动重生。

**为什么**：生命周期是粒子系统的核心机制——诞生、运动、淡出、死亡和重生的循环。 `fract` 或 `mod` 实现无限循环，无需额外状态。

按键设计：
- `spawnTime`：每个粒子的出生时间不同，由ID的`hash11`生成，分布在`[0, START_TIME]`区间
- `lifetime`：每个粒子的寿命不同，在`[LIFETIME_MIN, LIFETIME_MAX]`区间内随机
- `mod(time -spawnTime,lifetime)`：自动循环；粒子在死亡后立即重生
- `floor(...)` 计算当前生命周期数，用于每个周期生成不同的随机属性```glsl
#define NUM_PARTICLES 100   // adjustable: particle count
#define LIFETIME_MIN 1.0    // adjustable: minimum lifespan (seconds)
#define LIFETIME_MAX 3.0    // adjustable: maximum lifespan (seconds)
#define START_TIME 2.0      // adjustable: time for all particles to be born

// Returns: x = current normalized age [0,1], y = current life cycle number
vec2 particleAge(int id, float time) {
    float spawnTime = START_TIME * hash11(float(id) * 2.0);
    float lifetime = mix(LIFETIME_MIN, LIFETIME_MAX, hash11(float(id) * 3.0 - 35.0));
    float age = mod(time - spawnTime, lifetime);
    float run = floor((time - spawnTime) / lifetime);
    return vec2(age / lifetime, run);
}
```### 步骤 3：无状态粒子位置计算

**什么**：仅根据粒子 ID 和时间计算 2D/3D 位置，而不依赖于任何缓冲区。

**为什么**：对于装饰效果（星空、烟花、轨道光点），无状态方法是最简单、最有效的。通过参数曲线（例如利萨如曲线）定义主轨迹，然后添加随机偏移和重力。

职位由三部分组成：
1. **主轨迹**（谐振子）：多个余弦波叠加，形成平滑的利萨如曲线，控制粒子群的整体运动路径
2. **随机漂移**：每个粒子随时间从主轨迹位置线性扩散； `DRIFT_MAX` 控制扩散范围
3. **重力**：通过`0.5 * g * t²`进行抛物线下降； `age²` 是时间的标准化形式```glsl
#define GRAVITY vec2(0.0, -4.5)     // adjustable: gravity direction and strength
#define DRIFT_MAX vec2(0.28, 0.28)  // adjustable: maximum random drift amplitude

// Harmonic superposition for smooth main trajectory
float harmonics(vec3 freq, vec3 amp, vec3 phase, float t) {
    float val = 0.0;
    for (int h = 0; h < 3; h++)
        val += amp[h] * cos(t * freq[h] * 6.2832 + phase[h] / 360.0 * 6.2832);
    return (1.0 + val) / 2.0;
}

vec2 particlePosition(int id, float time) {
    vec2 ageInfo = particleAge(id, time);
    float age = ageInfo.x;
    float run = ageInfo.y;

    // Main trajectory (harmonic oscillator)
    float slowTime = time * 0.1; // time along main trajectory
    vec2 mainPos = vec2(
        harmonics(vec3(0.4, 0.66, 0.78), vec3(0.8, 0.24, 0.18), vec3(0.0, 45.0, 55.0), slowTime),
        harmonics(vec3(0.415, 0.61, 0.82), vec3(0.72, 0.28, 0.15), vec3(90.0, 120.0, 10.0), slowTime)
    );

    // Random drift (grows linearly with time)
    vec2 drift = DRIFT_MAX * (vec2(hash11(float(id) * 3.0 + run * 4.0),
                                    hash11(float(id) * 7.0 - run * 2.5)) - 0.5) * age;
    // Gravity effect
    vec2 grav = GRAVITY * age * age * 0.5;

    return mainPos + drift + grav;
}
```### 步骤 4：缓冲区存储的粒子状态（有状态系统）

**什么**：使用 Buffer 纹理中的一行像素来存储所有粒子，每个像素 = 一个粒子的 (pos.x, pos.y, vel.x, vel.y)。

**为什么**：当需要帧间持久状态时（物理碰撞、力场相互作用、N体模拟），粒子数据必须写入缓冲区并读回下一帧。在ShaderToy中，每个像素都是一个存储单元。

设计要点：
- `fragCoord.y > 0.5`：仅第一行像素存储粒子；剩余像素被丢弃
- `fragCoord.x`对应粒子ID；每个像素的 RGBA 存储 (pos.x, pos.y, vel.x, vel.y)
- `iFrame < 5`: 前几帧初始化，随机分布粒子位置
- 力累积：边界斥力+粒子间引力/斥力+摩擦力
- 积分后限制速度和加速度，防止数值爆炸```glsl
// === Buffer A: Particle physics update ===
#define NUM_PARTICLES 40    // adjustable: particle count
#define MAX_VEL 0.5         // adjustable: maximum velocity
#define MAX_ACC 3.0         // adjustable: maximum acceleration
#define RESIST 0.2          // adjustable: drag coefficient
#define DT 0.03             // adjustable: time step

// Read the i-th particle's data
vec4 loadParticle(float i) {
    return texelFetch(iChannel0, ivec2(i, 0), 0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    if (fragCoord.y > 0.5 || fragCoord.x > float(NUM_PARTICLES)) discard;

    float id = floor(fragCoord.x);
    vec2 res = iResolution.xy / iResolution.y;

    // Initialization
    if (iFrame < 5) {
        vec2 rng = hash12(id);
        fragColor = vec4(0.1 + 0.8 * rng * res, 0.0, 0.0);
        return;
    }

    // Read current state
    vec4 particle = loadParticle(id); // xy = pos, zw = vel
    vec2 pos = particle.xy;
    vec2 vel = particle.zw;

    // === Force accumulation ===
    vec2 force = vec2(0.0);

    // Boundary repulsion force
    force += 0.8 * (1.0 / abs(pos) - 1.0 / abs(res - pos));

    // Inter-particle interaction (attraction/repulsion)
    for (float i = 0.0; i < float(NUM_PARTICLES); i++) {
        if (i == id) continue;
        vec4 other = loadParticle(i);
        vec2 w = pos - other.xy;
        float d = length(w);
        if (d > 0.0)
            force -= w * (6.3 + log(d * d * 0.02)) / exp(d * d * 2.4) / d;
    }

    // Friction force
    force -= vel * RESIST / DT;

    // === Integration ===
    vec2 acc = force;
    float a = length(acc);
    acc *= a > MAX_ACC ? MAX_ACC / a : 1.0; // limit acceleration

    vel += acc * DT;
    float v = length(vel);
    vel *= v > MAX_VEL ? MAX_VEL / v : 1.0; // limit velocity

    pos += vel * DT;

    fragColor = vec4(pos, vel);
}
```### 步骤 5：粒子渲染 — 点光源/变形球风格

**什么**：迭代图像通道中的所有粒子并将每个粒子渲染为柔和的发光点。

**为什么**： `1/dot(p,p)` 产生自然的平方反比距离衰减；当多个粒子重叠时，结果类似于元球融合。这是最经典的粒子渲染方法。

渲染原理：
- `dot(p, p)` 是 `dist²`；使用它作为分母会产生平方反比距离衰减
- “亮度”控制点大小 - 值越大产生越大的发光点
- `totalWeight` 累积所有粒子的元球贡献
- 根据粒子速度在“COLOR_START”和“COLOR_END”之间插值颜色
- `mix(col, pcol, mb / totalWeight)` 实现贡献加权颜色混合，附近的粒子具有更高的颜色权重
- 最终标准化+钳位防止过度曝光```glsl
#define BRIGHTNESS 0.002        // adjustable: particle brightness
#define COLOR_START vec3(0.0, 0.64, 0.2)  // adjustable: start color
#define COLOR_END vec3(0.06, 0.35, 0.85)  // adjustable: end color

vec3 renderParticles(vec2 uv) {
    vec3 col = vec3(0.0);
    float totalWeight = 0.0;

    for (int i = 0; i < NUM_PARTICLES; i++) {
        vec4 particle = loadParticle(float(i));
        vec2 p = uv - particle.xy;

        // Metaball-style falloff: radius / distance²
        float mb = BRIGHTNESS / dot(p, p);
        totalWeight += mb;

        // Interpolate color based on particle attributes
        float ratio = length(particle.zw) / MAX_VEL;
        vec3 pcol = mix(COLOR_START, COLOR_END, ratio);
        col = mix(col, pcol, mb / totalWeight);
    }

    totalWeight /= float(NUM_PARTICLES);
    col = normalize(col) * clamp(totalWeight, 0.0, 0.4);
    return col;
}
```### 步骤 6：帧反馈运动模糊

**什么**：将当前帧与前一帧的缓冲区混合以产生运动轨迹。

**为什么**：单帧粒子只是离散的点；通过时间积累（反馈混合），产生连续的痕迹/残像效果。混合系数控制轨迹长度。

设计要点：
- `TRAIL_DECAY` 接近 1 会产生更长的轨迹（0.99 = 非常长的轨迹，0.9 = 短轨迹）
- 需要额外的缓冲区传递：缓冲区 B 处理轨迹累积，图像传递从缓冲区 B 读取
- `prev * TRAIL_DECAY + current`: 衰减旧帧 + 覆盖新帧
- 该方法还可以用很少的粒子+长的轨迹来模拟高粒子密度```glsl
#define TRAIL_DECAY 0.95  // adjustable: trail decay rate, closer to 1 = longer trail

// In the rendering Buffer's mainImage:
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // Read previous frame
    vec3 prev = texture(iChannel0, uv).rgb * TRAIL_DECAY;

    // Draw current frame particles
    vec3 current = renderParticles(fragCoord / iResolution.y);

    // Overlay
    fragColor = vec4(prev + current, 1.0);
}
```### 步骤 7：HSV 着色和星光效果

**内容**：使用 HSV 颜色空间对粒子进行着色并添加十字/星形衍射尖峰线。

**为什么**：HSV 可以轻松旋转色调以获得彩虹效果；星光眩光（衍射尖峰）模拟真实镜头光学效果，赋予光点更多视觉质量。

HSV着色原理：
- `hsv.x` = 色调，0-1 映射到色轮的一圈
- `hsv.y` = 饱和度，0 = 灰色，1 = 纯色
- `hsv.z` = 值，0 = 黑色，1 = 最亮
- 余弦波近似 RGB 通道色调响应曲线

星光眩光原理：
- 星光眩光是由实际摄影中镜头光圈叶片的衍射引起的
- 通过在特定方向上拉伸距离场来实现：一个水平方向，一个垂直方向，每个 45 度对角线方向一个
- `stretch`参数控制拉伸比例；较大的值会产生更细、更长的线条
- `0.707` 是 `cos(45°)` = `sin(45°)` 的近似值，用于旋转到对角线方向```glsl
// HSV -> RGB conversion
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// Star glare effect: produces elongated light rays in horizontal/vertical/diagonal directions
float starGlare(vec2 relPos, float intensity) {
    // Horizontal/vertical branches
    vec2 stretch = vec2(9.0, 0.32); // adjustable: stretch ratio
    float dh = length(relPos * stretch);
    float dv = length(relPos * stretch.yx);

    // Diagonal branches
    vec2 diagPos = 0.707 * vec2(dot(relPos, vec2(1, 1)), dot(relPos, vec2(1, -1)));
    float dd1 = length(diagPos * vec2(13.0, 0.61));
    float dd2 = length(diagPos * vec2(0.61, 13.0));

    float glare = 0.25 / (dh * 3.0 + 0.01)
                + 0.25 / (dv * 3.0 + 0.01)
                + 0.19 / (dd1 * 3.0 + 0.01)
                + 0.19 / (dd2 * 3.0 + 0.01);
    return glare * intensity;
}
```## 常见变体详细信息

### 变体 1：元球极坐标粒子

**与基础版本的区别**：粒子在极坐标中均匀分布并向外扩展，使用`1/dot(p,p)`元球融合而不是点光源，产生有机的“斑点状”效果。

设计要点：
- 粒子位置从笛卡尔坐标变为极坐标：角度均匀分布在圆周围，距离随着时间的推移以“fract”循环
- `fract(time * speed + hash)` 产生从中心向外扩展然后重生的粒子
- 元球渲染：“0.84 / dot(p, p)”值在粒子重叠处自然累积，形成融合的有机形状
- 颜色根据距离“d”在开始颜色和结束颜色之间进行插值
- `mb/totalSum` 确保颜色混合按贡献进行加权```glsl
// Particle position changed to polar coordinate expansion
float d = fract(time * 0.51 + 48934.4238 * sin(float(i) * 692.7398));
float angle = TAU * float(i) / float(NUM_PARTICLES);
vec2 particlePos = d * vec2(cos(angle), sin(angle)) * 4.0;

// Metaball rendering replaces point light
vec2 p = uv - particlePos;
float mb = 0.84 / dot(p, p);  // adjustable: 0.84 = metaball radius
col = mix(col, mix(startColor, endColor, d), mb / totalSum);
```### 变体 2：缓冲存储 + Boids 聚集行为

**与基础版本的区别**：从无状态更改为有状态，每个粒子存储在缓冲区像素中，从而实现 N 体吸引/排斥相互作用和 Boid 涌现行为。

设计要点：
- 每个粒子迭代所有其他粒子，计算净吸引力/排斥力
- 力公式“(6.3 + log(d² * 0.02)) / exp(d² * 2.4)”产生：
  - 短程排斥（指数衰减占主导）
  - 中等范围的吸引力（对数项占主导地位）
  - 长距离无影响（指数衰减接近零）
- 摩擦`vel * 0.2 / dt`防止无限加速
- 总体效果：粒子自组织成群体运动模式，表现出鱼群/鸟群的涌现行为```glsl
// Buffer A: force accumulation
vec2 sumForce = vec2(0.0);
for (float j = 0.0; j < NUM_PARTICLES; j++) {
    if (j == id) continue;
    vec4 other = texelFetch(iChannel0, ivec2(j, 0), 0);
    vec2 w = pos - other.xy;
    float d = length(w);
    // Combined attraction+repulsion: short-range repulsion, long-range attraction
    sumForce -= w * (6.3 + log(d * d * 0.02)) / exp(d * d * 2.4) / d;
}
sumForce -= vel * 0.2 / dt; // friction
```### 变体 3：Verlet 集成布料模拟

**与基础版本的区别**：粒子通过弹簧约束（网格拓扑）连接，使用 Verlet 积分而不是欧拉方法 - 不需要显式存储速度。

设计要点：
- Verlet 集成：`newPos = 2 * 当前 - 上一个 + acc * dt²`
  - 速度隐含在“当前 - 上一个”中
  - 无需单独的速度存储； RGBA可以存储(current.xy, previous.xy)
  - 约束求解比欧拉更稳定（不会因高频振荡而爆炸）
- 弹簧约束：每对相邻粒子都有一个“静止长度”
  - 计算当前距离和静止长度之间的差异
  - 将粒子向静止长度移动一小步（0.1是松弛系数）
  - 多次约束求解迭代收敛到稳定状态
- 网格拓扑：按行和列排列的粒子 ID，每个粒子与其上/下/左/右邻居相连```glsl
// Verlet integration: velocity is implicit in (current position - previous position)
// particle.xy = current position, particle.zw = previous position
vec2 newPos = 2.0 * particle.xy - particle.zw + vec2(0.0, -0.6) * dt * dt;
particle.zw = particle.xy;
particle.xy = newPos;

// Spring constraint solving
vec4 neighbor = texelFetch(iChannel0, neighborId, 0);
vec2 delta = neighbor.xy - particle.xy;
float dist = length(delta);
float restLength = 0.1; // adjustable: rest length
particle.xy += 0.1 * (dist - restLength) * (delta / dist);
```### 变体 4：3D 粒子 + 射线渲染

**与基础版本的区别**：粒子存储在3D空间中；渲染使用从相机投射的光线，计算每条光线到每个粒子的最近距离以进行着色。

设计要点：
- 相机位于“(0, 0, 2.5)”，光线方向由屏幕 UV 确定
- 点到线距离公式：`|cross(P-O, D)|`，其中O为射线原点，D为射线方向，P为粒子位置
- `dot(cross(...), cross(...))` 计算平方距离（避免 sqrt）
- `× 1000.0` 是控制视觉颗粒大小的距离缩放因子
- 与 2D 渲染的区别：2D 使用“uv - pos”的长度，3D 使用从射线到点的最近距离```glsl
// 3D rendering: closest distance from ray to particle
vec3 ro = vec3(0.0, 0.0, 2.5);
vec3 rd = normalize(vec3(uv, -0.5));
for (int i = 0; i < numParticles; i++) {
    vec3 pos = texture(iChannel0, vec2(i, 100.0) * w).rgb;
    // Squared distance from point to line
    float d = dot(cross(pos - ro, rd), cross(pos - ro, rd));
    d *= 1000.0;
    float glow = 0.14 / (pow(d, 1.1) + 0.03);
    col += glow * particleColor;
}
```### 变体 5：雨滴粒子（3D 场景集成）

**与基础版本的区别**：粒子在 3D 世界空间（重力 + 风 + 抖动）中移动，渲染为屏幕空间水滴，并使用法线贴图来模拟折射。生命周期结束后随机重生。

设计要点：
- `speedScale` 包含 `sin(π/2 * pow(age/lifetime, 2))` 以加速下降
- 风力通过点积投射到相机的右/上方向
- 抖动 `randVec2 * jitterSpeed` 模拟空气湍流
- 死亡和重生：`article.z` 累积年龄；当它超过“article.a”（寿命）时，位置和寿命将被重置
- 渲染可以叠加雨滴SDF+折射法线贴图来模拟真实的雨滴光学```glsl
// 3D force accumulation
float speedScale = 0.0015 * (0.1 + 1.9 * sin(PI * 0.5 * pow(age / lifetime, 2.0)));
particle.x += (windShieldOffset.x + windIntensity * dot(rayRight, windDir)) * fallSpeed * speedScale * dt;
particle.y += (windShieldOffset.y + windIntensity * dot(rayUp, windDir)) * fallSpeed * speedScale * dt;
// Jitter
particle.xy += 0.001 * (randVec2(particle.xy + iTime) - 0.5) * jitterSpeed * dt;
// Death and respawn
if (particle.z > particle.a) {
    particle.xy = vec2(rand(seedX), rand(seedY)) * iResolution.xy;
    particle.a = lifetimeMin + rand(pid) * (lifetimeMax - lifetimeMin);
    particle.z = 0.0;
}
```### 变体 6：涡流/风暴粒子系统

**与基础版本的区别**：粒子沿着螺旋轨迹移动，形成风暴/沙尘暴/暴风雪效果。无状态单次传递。

设计要点：
- 差速旋转：内圈比外圈旋转得更快（`angleSpeed = k / (offset + radius)`），产生自然涡流
- 粒子颜色必须比背景明显亮 (2-3x)，否则在相似颜色的背景下不可见
- 亮度预算：150个粒子时，“分子=0.002，epsilon=0.008”（峰值=0.25）是安全的
- 使用“smoothstep(innerR,outerR,dist)”掩模实现涡中心暗区

### 变体 7：流星/拖尾线渲染

**与基础版本的区别**：粒子渲染为细长的发光线而不是圆形光点。

设计要点：
- **必须有清晰可见的静态星场背景**：调用`starField()`函数；使用“exp(-dist²*k)”将恒星渲染为锐高斯点，峰值亮度 >= 0.3
- 流星轨迹必须足够亮：`core`倍数 >= 0.15；除以样本数后，每一步仍需要 >= 0.005 可见贡献
- **不要对线条使用 `1/(distPerp² + tiny_epsilon)`** — 使用 `exp(-distPerp / width)` 以获得安全发光
- 流星头 `headGlow = 0.005 / (dist² + 0.0008)` 确保明亮的可见度
- TrailLen范围0.15-0.35确保足够的轨迹长度

### 变体 8：喷泉/向上喷射粒子系统

**与基础版本的区别**：粒子从一个点向上喷射，遵循抛物线弧线，然后落回。无状态单次传递。

设计要点：
- **必须包含三层**： (1) 主要水柱粒子（向上喷射 + 抛物线） (2) 飞溅粒子（击中水面时向侧面飞行） (3) 水面/水池视觉效果
- **粒子必须是尖锐的、可见的单个点**：使用小 epsilon (<= 0.002) 和小分子；不仅必须产生漫射发光
- 抛物线运动：`pos = base + vel0 * t + 0.5 * 重力 * t²`
- 地面裁剪：`if (pos.y < waterLevel) continue;`
- 亮度预算：60 个主粒子 + 40 个飞溅粒子，每个粒子的 epsilon 在 0.001-0.002 范围内

### 变体 10：螺旋阵列/魔法粒子系统

**与基础版本的区别**：粒子排列成螺旋或几何阵列，产生魔法阵、魔法尘埃和类似的效果。颗粒具有虹彩颜色变化。无状态单次传递。

设计要点：
- **必须具有离散的可见粒子**：每个粒子必须是单独可见的小光点，而不仅仅是模糊的发光斑点。使用小 epsilon (0.0004-0.0006) 以获得足够的清晰度
- 螺旋轨迹：`角度 = 底角 + 范数 *spiralTurns + time * rotSpeed`，`半径`随范数增加
- 魔法阵采用角度均匀分布的独立环形粒子层+时间旋转，利用椭圆投影模拟3D透视
- 彩虹效果：`hue = fract(articleId / Total + time * speed +norm * shift)`，hue随ID和时间连续变化，覆盖整个色轮
- 星光闪烁：`shimmer = 0.7 + 0.3 * sin(time * freq + molecularId * Phase)`控制每个粒子的亮度脉动
- 两层结构：（1）螺旋上升粒子流（2）水平旋转魔法阵光点环

## 亮度预算快速参考

单程系统：**N ×（分子/epsilon）< 5.0**

|粒子计数|推荐分子|推荐的epsilon |单粒子峰|总峰值（无褪色）|
|--------|-------------|-------------|------------------------|--------------------|
| 40 | 40 0.015 | 0.015 0.03 | 0.03 0.5 | 0.5 20 → 莱因哈德 好的 |
| 80| 0.008 | 0.008 0.015 | 0.015 0.53 | 0.53 42 → 莱因哈德 好的 |
| 150 | 150 0.002 | 0.008 | 0.008 0.25 | 0.25 37 → 莱因哈德 好的 |
| 200 | 200 0.001 | 0.001 0.005 | 0.005 0.2 | 0.2 40 → 莱因哈德 好的 |

多通道乒乓球系统：**N ×（分子/ε）× 1/(1-衰减) < 10.0**

|腐烂|放大系数| 20 粒子峰值限制 | 50 粒子峰值限制 | 100 粒子峰值限制 |
|--------|---------|----------------|---------------|----------------|
| 0.88 | 0.88 8.3 倍 | 0.06 | 0.06 0.024 | 0.024 0.012 |
| 0.92 | 0.92 12.5 倍 | 0.04 | 0.04 0.016 | 0.008 | 0.008
| 0.95 | 0.95 20 倍 | 0.025 | 0.025 0.01 | 0.01 0.005 | 0.005

## 性能优化深度分析

### 1. 粒子计数和循环开销- **瓶颈**：每个像素迭代所有粒子 (O(W×H×N))；颗粒计数是最大的性能杠杆。
- **优化**：将粒子数从 200 减少到 80 可能几乎没有视觉差异，但性能加倍。提前退出优化还可以帮助：```glsl
float dist = length(uv - ppos);
if (dist > 0.1) continue; // adjustable: skip particles beyond influence range
```- 注意：提前退出阈值必须根据粒子亮度/影响半径进行调整；太小会导致颗粒边缘突然切断

### 2. 帧反馈替代高粒子计数
- **技术**：少量粒子 + 帧反馈轨迹（“上一个 * 0.95 + 当前”）在视觉上等于更多粒子。每帧绘制50个粒子+累积=视觉密度远超50。
- 这种方法具有产生自然运动模糊的额外好处
- 需要额外的缓冲通道来累积帧

### 3. N 体交互复杂性
- **瓶颈**：每个粒子与所有其他粒子相互作用 = O(N²)。当 N > 100 时变得非常慢。
- **优化A**：仅与K个最近邻交互（使用Voronoi跟踪加速结构，请参阅下面的“与Voronoi空间加速结构结合”）。
- **优化B**：将空间划分为网格单元，仅检查相邻单元中的粒子。在 GPU 上实现网格需要额外的缓冲区传递来维护网格数据。

### 4. 子框架步进
- **问题**：高速粒子每帧移动多个像素，留下不连续的轨迹。
- **优化**：为每个粒子每帧执行多个小步骤，沿途累积渲染：```glsl
const int stepsPerFrame = 7; // adjustable
for (int j = 0; j < stepsPerFrame; j++) {
    // Render particle contribution at this position
    pos += vel * 0.002 * 0.2;
}
col /= float(stepsPerFrame);
```- 更多的子帧产生更多的连续轨迹，但会线性增加计算成本
- 适用于烟花爆炸、高速弹幕等。

### 5. 精度和数值稳定性
- 速度和加速度需要钳位以防止数值爆炸：```glsl
float v = length(vel);
vel *= v > MAX_VEL ? MAX_VEL / v : 1.0;
```- Verlet积分在约束求解方面比Euler更稳定，特别是对于布料和弹簧网络
- 对于长时间运行的模拟，请注意浮点精度误差随着时间的推移而累积

## 组合建议与完整代码

### 与 Raymarching 场景相结合
粒子系统通常嵌入到 Raymarching 场景中（例如，雨、火花、灰尘）。方法：在 Raymarching 步骤循环期间，同时采样粒子密度/位置并叠加到场景颜色上。或者将粒子渲染到单独的缓冲区并在最终合成期间混合。

### 与噪声/流场结合
使用Simplex/Perlin噪声生成速度场；粒子沿着噪声梯度移动：```glsl
// Use noise to drive particle velocity
vel += hash33(vel + time) * 7.0; // random perturbation
vel = mix(vel, -pos * pow(length(pos), 0.75), 0.5 + 0.5 * sin(time)); // center attraction
```这种组合适合“神经突触”、“烟雾流动”等有机效果。

### 与后处理结合
- **Bloom**：将高斯模糊应用于粒子渲染输出和叠加，增强发光效果。
- **色差**：分别偏移采样 R/G/B 通道，添加镜头效果。
- **色调映射**：将 Reinhard 映射 `col = col / (1.0 + col)` 应用于 HDR 粒子亮度。

### 与SDF形状渲染结合
将粒子渲染为特定的 SDF 形状（鱼、水滴、火花）而不是抽象的光点。方法：根据粒子速度方向旋转局部坐标，然后计算该坐标系中的SDF距离：```glsl
float sdFish(vec2 p, float angle) {
    float c = cos(angle), s = sin(angle);
    p *= 20.0 * mat2(c, s, -s, c);
    return max(min(length(p), length(p - vec2(0.56, 0.0))) - 0.3, -min(length(p - vec2(0.8, 0.0)) - 0.45, length(p + vec2(0.14, 0.0)) - 0.12)) * 0.05;
}
```### 结合Voronoi空间加速结构
对于大规模粒子（数千个），使用Voronoi跟踪加速结构而不是暴力遍历。每个像素维护 4 个最近粒子的 ID，并通过邻域传播进行更新。这将渲染和物理查询从 O(N) 减少到 O(1)（每个像素固定邻域查询）。适用于流体模拟和大规模群体行为。