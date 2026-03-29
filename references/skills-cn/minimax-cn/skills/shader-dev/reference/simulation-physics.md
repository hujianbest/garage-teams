# GPU 物理模拟 — 详细参考

本文档是[SKILL.md](SKILL.md)的完整参考资料，包含分步教程、数学推导和高级用法。

## 先决条件

- **GLSL 基础**：制服、纹理采样（`texture`/`texelFetch`）、`fragCoord`/`iResolution` 坐标系
- **ShaderToy 多通道机制**：缓冲区 A/B/C/D 相互之间读/写，`iChannel0~3` 绑定，共享代码的公共通道
- **矢量微积分基础**：梯度、散度、旋度、拉普拉斯算子
- **数值积分**：前向欧拉，半隐式方法（Semi-implicit / Verlet）
- **纹理作为数据存储**：将位置/速度/密度等物理量编码到纹理像素的 RGBA 通道中

## 核心原则详细信息

GPU物理模拟的核心范例是**缓冲区反馈**：利用ShaderToy的多通道架构将物理状态（位置、速度、密度、压力等）存储在纹理缓冲区中。每个帧读取前一帧的状态，计算新状态，然后将其写回。每个像素独立并行计算，实现GPU级大规模并行物理求解。

### 关键数学工具详细信息

**1.离散拉普拉斯算子**（用于波动方程、粘性力、扩散）：```
∇²f ≈ f(x+1,y) + f(x-1,y) + f(x,y+1) + f(x,y-1) - 4·f(x,y)
```拉普拉斯算子测量一个点的值与其邻居的平均值之间的差异。在波动方程中，它驱动波的传播；在流体模拟中，提供粘性力（速度扩散）；在热方程中，它驱动温度均衡。

**2.半拉格朗日平流**（用于流体求解）：```
f_new(x) = f_old(x - v·dt)    // backward tracing along the velocity field
```平流是流体模拟中最关键的步骤。半拉格朗日方法通过“向后追踪”实现无条件稳定平流——从目标位置出发，沿着速度场向后追踪找到源位置，然后在源处采样值。这避免了前向欧拉平流的 CFL 条件限制。

**3.弹簧阻尼力**（用于布料、软体）：```
F_spring = k · (|Δx| - L₀) · normalize(Δx)
F_damper = c · dot(normalize(Δx), Δv) · normalize(Δx)
```弹簧力将两个质点拉回到静止长度L₀；刚度k决定恢复力的强度。阻尼力沿连接方向衰减相对速度；系数c决定能量耗散率。它们结合起来产生稳定的弹性运动。

**4.涡度限制**（用于保留流体细节）：```
curl = ∂v_x/∂y - ∂v_y/∂x
vorticity_force = ε · (∇|curl| × curl) / |∇|curl||
```数值粘度过度平滑小规模涡流。涡度限制通过在高涡度区域施加额外的力来补偿这种人为耗散，将小涡流推入更集中的旋转结构并保持流体的视觉丰富度。

## 详细实施步骤

### 步骤 1：乒乓双缓冲区结构

**什么**：创建两个交替读/写的缓冲区（A 和 B）以实现状态持久性。

**为什么**：GPU 着色器无法同时读取和写入同一缓冲区。乒乓策略从一个缓冲区读取（前一帧的数据）并每帧写入另一个缓冲区，然后交换下一帧。

**重要：ShaderToy 和 WebGL2 之间的主要区别**：在 ShaderToy 中，缓冲区 A/B 是两个独立的通道，具有单独的写入目标，因此“iChannel0=self, iChannel1=other”不会冲突。然而，在WebGL2中只有一个着色器程序在打乒乓球，并且写入的目标纹理无法同时读取。解决方案是**双通道编码**（R=当前高度，G=上一帧高度）。

**代码**（WebGL2 安全版本，仅从 iChannel0 读取，采用 RGBA8 兼容编码）：```glsl
// IMPORTANT: Only use iChannel0 (read currentBuf), write to nextBuf (must be different!)
// IMPORTANT: encode/decode ensure signed values aren't clipped on RGBA8 (no float textures/SwiftShader)
uniform int useFloatTex;
float decode(float v) { return useFloatTex == 1 ? v : v * 2.0 - 1.0; }
float encode(float v) { return useFloatTex == 1 ? v : v * 0.5 + 0.5; }

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 texel = 1.0 / iResolution.xy;

    float current = decode(texture(iChannel0, uv).x);
    float previous = decode(texture(iChannel0, uv).y);

    float left  = decode(texture(iChannel0, uv - vec2(texel.x, 0.0)).x);
    float right = decode(texture(iChannel0, uv + vec2(texel.x, 0.0)).x);
    float down  = decode(texture(iChannel0, uv - vec2(0.0, texel.y)).x);
    float up    = decode(texture(iChannel0, uv + vec2(0.0, texel.y)).x);

    float laplacian = left + right + down + up - 4.0 * current;
    float next = 2.0 * current - previous + 0.25 * laplacian;

    next *= 0.995; // damping decay
    next *= min(1.0, float(iFrame)); // zero on frame 0

    fragColor = vec4(encode(next), encode(current), 0.0, 0.0);
}
```### 步骤2：交互驱动（外力注入）

**什么**：通过鼠标点击或编程生成将能量注入模拟。

**为什么**：物理模拟需要外部激励来启动和维持。鼠标交互是最直观的驾驶方式；编程方法可以模拟雨滴、爆炸等。

**代码**（在波动方程计算之前插入）：```glsl
float d = 0.0;

if (iMouse.z > 0.0)
{
    // Mouse click: create ripple at mouse position
    d = smoothstep(4.5, 0.5, length(iMouse.xy - fragCoord));
}
else
{
    // Programmatic raindrop: pseudo-random position + impulse
    float t = iTime * 2.0;
    vec2 pos = fract(floor(t) * vec2(0.456665, 0.708618)) * iResolution.xy;
    float amp = 1.0 - step(0.05, fract(t));
    d = -amp * smoothstep(2.5, 0.5, length(pos - fragCoord));
}
```### 步骤 3：渲染层（高度场可视化）

**内容**：读取图像通道中的模拟结果，通过梯度计算计算法线，并渲染光照效果。

**为什么**：模拟结果是高度场纹理，需要转化为可见的表面效果。通过法线有限差分计算梯度可以实现折射、漫反射、镜面高光和其他水面效果。

**代码**（图像通行证）：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec3 e = vec3(vec2(1.0) / iResolution.xy, 0.0);

    // Read four-neighbor height values from Buffer A
    float left  = texture(iChannel0, uv - e.xz).x;
    float right = texture(iChannel0, uv + e.xz).x;
    float down  = texture(iChannel0, uv - e.zy).x;
    float up    = texture(iChannel0, uv + e.zy).x;

    // Construct normal from gradient
    vec3 normal = normalize(vec3(right - left, up - down, 1.0));

    // Lighting computation
    vec3 light = normalize(vec3(0.2, -0.5, 0.7));
    float diffuse = max(dot(normal, light), 0.0);
    float spec = pow(max(-reflect(light, normal).z, 0.0), 32.0);

    // Refraction-offset background texture sampling
    vec4 bg = texture(iChannel1, uv + normal.xy * 0.35);
    vec3 waterTint = vec3(0.7, 0.8, 1.0);

    fragColor = mix(bg, vec4(waterTint, 1.0), 0.25) * diffuse + spec;
}
```### 步骤 4：链式多缓冲区迭代（提高准确性）

**什么**：将多个缓冲区链接在一起以每帧多次执行相同的求解器。

**为什么**：许多物理求解器（流体压力投影、约束求解）需要多次迭代才能收敛。在ShaderToy中，您可以链接Buffer A→B→C来执行相同的代码，相当于每帧迭代3次。这对于欧拉流体（压力发散消除）和刚体（脉冲约束求解）至关重要。

**完整的欧拉流体求解器代码**（缓冲区 A/B/C 共享公共通道）：```glsl
// === Common Pass ===
#define dt 0.15                        // adjustable: time step
#define viscosityThreshold 0.64        // adjustable: viscosity coefficient (larger = thinner)
#define vorticityThreshold 0.25        // adjustable: vorticity confinement strength

vec4 fluidSolver(sampler2D field, vec2 uv, vec2 step,
                 vec4 mouse, vec4 prevMouse)
{
    float k = 0.2, s = k / dt;

    // Sample center and four neighbors
    vec4 c  = textureLod(field, uv, 0.0);
    vec4 fr = textureLod(field, uv + vec2(step.x, 0.0), 0.0);
    vec4 fl = textureLod(field, uv - vec2(step.x, 0.0), 0.0);
    vec4 ft = textureLod(field, uv + vec2(0.0, step.y), 0.0);
    vec4 fd = textureLod(field, uv - vec2(0.0, step.y), 0.0);

    // Divergence and density gradient
    vec3 ddx = (fr - fl).xyz * 0.5;
    vec3 ddy = (ft - fd).xyz * 0.5;
    float divergence = ddx.x + ddy.y;
    vec2 densityDiff = vec2(ddx.z, ddy.z);

    // Density solve
    c.z -= dt * dot(vec3(densityDiff, divergence), c.xyz);

    // Viscous force (Laplacian)
    vec2 laplacian = fr.xy + fl.xy + ft.xy + fd.xy - 4.0 * c.xy;
    vec2 viscosity = viscosityThreshold * laplacian;

    // Semi-Lagrangian advection
    vec2 densityInv = s * densityDiff;
    vec2 uvHistory = uv - dt * c.xy * step;
    c.xyw = textureLod(field, uvHistory, 0.0).xyw;

    // Mouse external force
    vec2 extForce = vec2(0.0);
    if (mouse.z > 1.0 && prevMouse.z > 1.0)
    {
        vec2 drag = clamp((mouse.xy - prevMouse.xy) * step * 600.0,
                          -10.0, 10.0);
        vec2 p = uv - mouse.xy * step;
        extForce += 0.001 / dot(p, p) * drag;
    }

    c.xy += dt * (viscosity - densityInv + extForce);

    // Velocity decay
    c.xy = max(vec2(0.0), abs(c.xy) - 5e-6) * sign(c.xy);

    // Vorticity confinement
    c.w = (fd.x - ft.x + fr.y - fl.y); // curl
    vec2 vorticity = vec2(abs(ft.w) - abs(fd.w),
                          abs(fl.w) - abs(fr.w));
    vorticity *= vorticityThreshold / (length(vorticity) + 1e-5) * c.w;
    c.xy += vorticity;

    // Boundary conditions
    c.y *= smoothstep(0.5, 0.48, abs(uv.y - 0.5));
    c.x *= smoothstep(0.5, 0.49, abs(uv.x - 0.5));

    // Stability clamping
    c = clamp(c, vec4(-24.0, -24.0, 0.5, -0.25),
                 vec4( 24.0,  24.0, 3.0,  0.25));

    return c;
}

// === Buffer A / B / C (identical code) ===
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 stepSize = 1.0 / iResolution.xy;
    vec4 prevMouse = textureLod(iChannel0, vec2(0.0), 0.0);
    fragColor = fluidSolver(iChannel0, uv, stepSize, iMouse, prevMouse);

    // Bottom row stores mouse state
    if (fragCoord.y < 1.0) fragColor = iMouse;
}
```### 步骤 5：粒子/质点系统的纹理数据布局

**内容**：对纹理中特定像素位置的粒子位置、速度和其他属性进行编码。

**为什么**：在GPU物理模拟中，每个粒子/质量点需要存储多个属性（位置、速度、力等）。通过将纹理划分为多个区域（例如，左半部分表示位置，右半部分表示速度），或将不同的属性编码到不同的 RGBA 通道中，可以实现紧凑的数据布局。

**代码**（布料模拟数据布局示例）：```glsl
#define SIZX 128.0  // adjustable: cloth width (particle count)
#define SIZY 64.0   // adjustable: cloth height (particle count)

// Left half [0, SIZX) stores positions, right half [SIZX, 2*SIZX) stores velocities
// IMPORTANT: In WebGL2, getpos/getvel both read from iChannel0 (currentBuf, read-only),
//    write target is nextBuf (separate buffer), avoiding read-write conflict
vec3 getpos(vec2 id)
{
    return texture(iChannel0, (id + 0.5) / iResolution.xy).xyz;
}

vec3 getvel(vec2 id)
{
    return texture(iChannel0, (id + 0.5 + vec2(SIZX, 0.0)) / iResolution.xy).xyz;
}

// In mainImage, decide whether to output position or velocity based on fragCoord
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 fc = floor(fragCoord);
    vec2 c = fc;
    c.x = fract(c.x / SIZX) * SIZX; // mass point ID

    vec3 pos = getpos(c);
    vec3 vel = getvel(c);

    // ... physics computation ...

    // Output: left half stores position, right half stores velocity
    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}
```### 步骤 6：弹簧阻尼器约束系统

**内容**：在质点之间施加弹簧力和阻尼力。

**为什么**：弹簧阻尼器是布料和软体模拟的核心。每个质点通过弹簧与相邻质点连接——弹簧力维持结构形状，阻尼力消散振荡能量。使用近邻（结构弹簧）+对角线（剪切弹簧）+跳跃连接（弯曲弹簧）提供完整的约束。

**完整代码**：```glsl
const float SPRING_K = 0.15;  // adjustable: spring stiffness
const float DAMPER_C = 0.10;  // adjustable: damping coefficient
const float GRAVITY  = 0.0022; // adjustable: gravitational acceleration

vec3 pos, vel, ovel;
vec2 c; // current mass point ID

void edge(vec2 dif)
{
    // Boundary check
    if ((dif + c).x < 0.0 || (dif + c).x >= SIZX ||
        (dif + c).y < 0.0 || (dif + c).y >= SIZY) return;

    float restLen = length(dif); // rest length = initial distance
    vec3 posdif = getpos(dif + c) - pos;
    vec3 veldif = getvel(dif + c) - ovel;

    // IMPORTANT: Must check for zero length, otherwise normalize(vec3(0)) produces NaN
    float plen = length(posdif);
    if (plen < 0.0001) return;
    vec3 dir = posdif / plen;

    // Spring force: restore to rest length
    vel += dir
         * clamp(plen - restLen, -1.0, 1.0)
         * SPRING_K;

    // Damping force: attenuate relative velocity along connection direction
    vel += dir
         * dot(dir, veldif)
         * DAMPER_C;
}

// In mainImage, call 12 edges (near-neighbors + diagonals + skip-connections)
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // ... initialize pos, vel, c ...
    ovel = vel;

    // Structural springs (4 near-neighbors)
    edge(vec2( 0.0, 1.0));
    edge(vec2( 0.0,-1.0));
    edge(vec2( 1.0, 0.0));
    edge(vec2(-1.0, 0.0));

    // Shear/bending springs (diagonals + skip-connections)
    edge(vec2( 1.0, 1.0));
    edge(vec2(-1.0,-1.0));
    edge(vec2( 0.0, 2.0));
    edge(vec2( 0.0,-2.0));
    edge(vec2( 2.0, 0.0));
    edge(vec2(-2.0, 0.0));
    edge(vec2( 2.0,-2.0));
    edge(vec2(-2.0, 2.0));

    // Collision detection (sphere)
    // ... ballcollis() ...

    // Integration
    pos += vel;
    vel.y += GRAVITY;

    // Air resistance (normal wind force)
    vec3 norm = findnormal(c);
    vec3 windvel = vec3(0.01, 0.0, -0.005); // adjustable: wind direction and speed
    vel -= norm * (dot(norm, vel - windvel) * 0.05);

    // Fixed boundary (top row pinned as curtain rod)
    if (c.y == 0.0)
    {
        pos = vec3(fc.x * 0.85, fc.y, fc.y * 0.01);
        vel = vec3(0.0);
    }

    fragColor = vec4(fc.x >= SIZX ? vel : pos, 0.0);
}
```### 步骤 7：N 体粒子相互作用（毕奥-萨伐尔涡旋法）

**什么**：在所有粒子之间实现全对相互作用力。

**为什么**：某些物理系统（例如涡动力学、引力 N 体问题）要求每个粒子与所有其他粒子相互作用。比奥-萨伐尔定律给出了涡量产生的速度场，这是二维涡模拟的核心。使用半牛顿（Verlet 型）两步积分来提高精度。

**完整代码**：```glsl
#define N 20           // adjustable: N×N total particles
#define Nf float(N)
#define MARKERS 0.90   // adjustable: passive marker particle ratio

// STRENGTH automatically scales with particle count and marker ratio
float STRENGTH = 1e3 * 0.25 / (1.0 - MARKERS) * sqrt(30.0 / Nf);

#define tex(i,j) texture(iChannel1, (vec2(i,j) + 0.5) / iResolution.xy)
#define W(i,j)   tex(i, j + N).z  // vorticity stored in tile(0,1) z channel

void mainImage(out vec4 O, vec2 U)
{
    vec2 T = floor(U / Nf);   // tile index
    U = mod(U, Nf);            // particle ID

    // Pass 1 (Buffer A): half-step integration dt*0.5
    // Pass 2 (Buffer B): full-step integration using Pass 1 velocity

    vec2 F = vec2(0.0);

    // N×N all-pairs Biot-Savart summation
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
        {
            float w = W(i, j);
            vec2 d = tex(i, j).xy - O.xy;
            // Periodic boundary: take nearest image
            d = (fract(0.5 + d / iResolution.xy) - 0.5) * iResolution.xy;
            float l = dot(d, d);
            if (l > 1e-5)
                F += vec2(-d.y, d.x) * w / l; // Biot-Savart kernel
        }

    O.zw = STRENGTH * F;  // velocity
    O.xy += O.zw * dt;    // integrate position
    O.xy = mod(O.xy, iResolution.xy); // periodic boundary
}
```### 步骤 8：特定像素中的状态存储（全局变量技巧）

**什么**：将全局状态（当前位置、时间、鼠标历史记录）存储在纹理中的固定像素位置。

**为什么**：GPU 着色器没有全局变量。通过将状态存储在商定的像素坐标（通常是“(0,0)”或底行），下一帧可以读取这些“全局变量”。这对于 ODE 集成（例如洛伦兹吸引子）和需要跟踪鼠标历史记录的交互是必不可少的。

**完整代码**：```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Pixel (0,0) stores global state (e.g., Lorenz attractor's current 3D position)
    if (floor(fragCoord) == vec2(0, 0))
    {
        if (iFrame == 0)
        {
            fragColor = vec4(0.1, 0.001, 0.0, 0.0); // initial conditions
        }
        else
        {
            vec3 state = texture(iChannel0, vec2(0.0)).xyz;
            // Execute multi-step ODE integration
            for (float i = 0.0; i < 96.0; i++)
            {
                // Lorenz system: dx/dt = σ(y-x), dy/dt = x(ρ-z)-y, dz/dt = xy-βz
                vec3 deriv;
                deriv.x = 10.0 * (state.y - state.x);        // σ = 10
                deriv.y = state.x * (28.0 - state.z) - state.y; // ρ = 28
                deriv.z = state.x * state.y - 8.0/3.0 * state.z; // β = 8/3
                state += deriv * 0.016 * 0.2;
            }
            fragColor = vec4(state, 0.0);
        }
        return;
    }

    // Other pixels: accumulate trajectory distance field
    vec3 last = texture(iChannel0, vec2(0.0)).xyz;
    float d = 1e6;
    for (float i = 0.0; i < 96.0; i++)
    {
        vec3 next = Integrate(last, 0.016 * 0.2);
        d = min(d, dfLine(last.xz * 0.015, next.xz * 0.015, uv));
        last = next;
    }

    float c = 0.5 * smoothstep(1.0 / iResolution.y, 0.0, d);
    vec3 prev = texture(iChannel0, fragCoord / iResolution.xy).rgb;
    fragColor = vec4(vec3(c) + prev * 0.99, 0.0); // decaying accumulation
}
```## 常见变体详细信息

### 变体 1：欧拉流体模拟（烟雾/墨水）

**与基本版本的区别**：从标量波动方程扩展到完整的二维速度场求解 - 包括平流、粘度、涡度限制和密度跟踪。需要 3 次以上链式缓冲区迭代以增强收敛性。

**关键代码**：```glsl
// Buffer storage: xy = velocity, z = density, w = curl
// Key difference: semi-Lagrangian advection replaces simple neighborhood update
vec2 uvHistory = uv - dt * velocity.xy * stepSize;
vec4 advected = textureLod(field, uvHistory, 0.0);

// Vorticity confinement (preserve fluid detail)
float curl = (fd.x - ft.x + fr.y - fl.y);
vec2 vortGrad = vec2(abs(ft.w) - abs(fd.w), abs(fl.w) - abs(fr.w));
vec2 vortForce = vorticityThreshold / (length(vortGrad) + 1e-5) * curl * vortGrad;
velocity.xy += vortForce;
```### 变体 2：布料模拟（质量-弹簧-阻尼器）

**与基础版本的差异**：从基于网格的场方程更改为离散粒子系统。每个像素代表一个存储 3D 位置和速度的质点。通过弹簧阻尼器以及重力、风力和碰撞与邻居连接。多缓冲区链式迭代（4 遍）实现多个子步骤。

**关键代码**：```glsl
// Data layout: left half of texture = position, right half = velocity
// Spring force core
vec3 posdif = getpos(neighbor) - pos;
vec3 veldif = getvel(neighbor) - vel;
float restLen = length(neighborOffset);
force += normalize(posdif) * clamp(length(posdif) - restLen, -1.0, 1.0) * 0.15;
force += normalize(posdif) * dot(normalize(posdif), veldif) * 0.10;

// Sphere collision response
if (length(pos - ballPos) < ballRadius) {
    vel -= normalize(pos - ballPos) * dot(normalize(pos - ballPos), vel);
    pos = ballPos + normalize(pos - ballPos) * ballRadius;
}
```> **重要：常见陷阱**：
> - **布料图像通道必须将世界坐标投影到屏幕**：您不能使用 `uv * vec2(SIZX, SIZY)` 将屏幕 UV 映射到网格 ID，因为粒子已从其初始位置移动，产生分散的碎片。您必须迭代网格面，将顶点世界坐标投影到屏幕空间以进行三角形光栅化
> - GLSL 是严格类型的；你不能写`float / vec2`。错误示例：“length(dif) / vec2(SIZX, SIZY).x”将首先执行 float/vec2 导致编译错误；使用 `length(dif) / SIZX` 代替
> - `normalize(vec3(0))` 产生 NaN；所有“normalize()”调用必须事先包含长度检查
> - 在Image Pass中，`getpos`/`getvel`必须使用模拟分辨率（`iSimResolution`）进行UV计算，而不是屏幕分辨率`iResolution`
> - Texel中心采样应使用“+0.5”偏移（而不是“+0.01”）

### 变体 3：刚体物理引擎（GPU 上的 Box2D-lite）

**与基本版本的区别**：最复杂的变体。使用结构化像素寻址（ECS 数据布局）将刚体属性、关节、接触点等序列化为纹理。缓冲区 A 处理积分 + 碰撞检测，缓冲区 B/C/D 处理脉冲约束迭代。需要Common pass来封装完整的物理库。

**关键代码**：```glsl
// Structured memory addressing: map structs to consecutive pixels
int bodyAddress(int b_id) {
    return pixel_count_of_Globals + pixel_count_of_Body * b_id;
}
Body loadBody(sampler2D buff, int b_id) {
    int addr = bodyAddress(b_id);
    vec4 d0 = texelFetch(buff, address2D(res, addr), 0);
    vec4 d1 = texelFetch(buff, address2D(res, addr+1), 0);
    b.pos = d0.xy; b.vel = d0.zw;
    b.ang = d1.x; b.ang_vel = d1.y; // ...
}

// Contact impulse solving
float v_n = dot(dv, contact.normal);
float dp_n = contact.mass_n * (-v_n + contact.bias);
dp_n = max(0.0, dp_n);
body.vel += body.inv_mass * dp_n * contact.normal;
```### 变体 4：N 体涡旋粒子模拟

**与基础版本的差异**：从场（欧拉）方法更改为粒子（拉格朗日）方法。每个粒子都带有涡量，毕奥-萨伐尔定律计算全场速度。使用半牛顿两步积分（Buffer A 半步 → Buffer B 全步）。 O(N²) 全对相互作用。

**关键代码**：```glsl
// Biot-Savart kernel: velocity induced by vorticity w at distance d
// v = w * (-dy, dx) / |d|²
for (int j = 0; j < N; j++)
    for (int i = 0; i < N; i++) {
        float w = W(i, j);
        vec2 d = tex(i, j).xy - pos;
        d = (fract(0.5 + d / res) - 0.5) * res; // periodic boundary
        float l = dot(d, d);
        if (l > 1e-5) F += vec2(-d.y, d.x) * w / l;
    }
```### 变体 5：3D SPH 粒子流体

**与基础版本的差异**：扩展到 3D。使用粒子簇网格 (PCG) 进行空间邻域管理，自定义位打包（5 位指数 + 9 位分量）将粒子数据压缩为 4 个浮点。缓冲区 A 处理平流 + 聚类，缓冲区 B 计算密度，缓冲区 C 计算力 + 积分，缓冲区 D 计算阴影。

**关键代码**：```glsl
// Map 3D grid to 2D texture
vec2 dim2from3(vec3 p3d) {
    float ny = floor(p3d.z / SCALE.x);
    float nx = floor(p3d.z) - ny * SCALE.x;
    return vec2(nx, ny) * size3d.xy + p3d.xy;
}

// SPH pressure force
float pressure = max(rho / rest_density - 1.0, 0.0);
float SPH_F = force_coef_a * GD(d, 1.5) * pressure;
// Friction + surface tension
float Friction = 0.45 * dot(dir, dvel) * GD(d, 1.5);
float F = surface_tension * GD(d, surface_tension_rad);
p.force += force_k * dir * (F + SPH_F + Friction) * irho / rest_density;
```## 性能优化详情

### 1.邻域采样优化
- **瓶颈**：每个像素采样 4~12 个邻居；纹理带宽是主要瓶颈
- **优化**：使用`texelFetch`代替`texture`（跳过过滤），预先计算`1.0/iResolution.xy`以避免重复除法

### 2. N 体 O(N²) 循环优化
- **瓶颈**：所有对交互的复杂度为 O(N²)； N=20 表示每帧 400 次迭代，N=50 表示 2500 次
- **优化**：
  - 限制N值（20~30足以获得良好的视觉效果）
  - 使用“廉价”周期性边界模式（“fract”而不是 3×3 循环遍历）
  - 被动标记粒子（90%）不参与力计算，仅被动流动

### 3. 迭代次数与准确性平衡
- **瓶颈**：流体/刚体求解器需要多次迭代，但每个缓冲区只能执行一次
- **优化**：
  - 使用 3 个链接缓冲区 (A→B→C) 进行 3 次迭代/帧
  - 4 个布料链式缓冲区（4 个子步骤/帧，时间步 = 1/4/60）
  - 更多的缓冲区消耗更多的GPU内存；平衡准确性和资源

### 4. 自适应精度
- **优化**：对屏幕边缘或远处区域使用更大的步长```glsl
// Kelvin wave example: distant pixels use 8× step size
if (abs(U.y * R.y) > 100.0) dx *= 8.0 * abs(U.y);
```### 5.数据打包压缩
- **优化**：当每个粒子的float属性超过4个时，使用位运算进行打包```glsl
// 3D SPH example: 3 floats compressed into 1 uint (5-bit exponent + 3×9-bit components)
uint packvec3(vec3 v) {
    int exp = clamp(int(ceil(log2(max(...)))), -15, 15);
    float scale = exp2(-float(exp));
    uvec3 sv = uvec3(round(clamp(v*scale, -1.0, 1.0) * 255.0) + 255.0);
    return uint(exp + 15) | (sv.x << 5) | (sv.y << 14) | (sv.z << 23);
}
```### 6. 稳定性保障
- 对速度/密度应用“clamp”以防止数值爆炸
- 使用“smoothstep”进行软边界衰减而不是硬截止
- 阻尼系数保持在0.95~0.999范围内

## 详细组合建议

### 1.物理模拟+后处理渲染
最常见的组合。缓冲区通道处理物理计算，图像通道处理可视化：
- **波 + 折射/焦散**：高度场梯度驱动折射偏移采样
- **流体 + 墨水着色**：速度场平流彩色墨水颗粒（缓冲液 D），具有 HSV 随机着色
- **布料+光线追踪**：体素化空间树加速布料表面光线相交

### 2.物理模拟+SDF渲染
刚体/粒子位置数据传递到图像通道，使用 SDF 函数渲染为几何体：
- `sdBox(p - bodyPos, bodySize)` 渲染刚体
- `length(p - molecularPos) - radius` 渲染粒子
- 适用于Box2D-lite刚体引擎可视化

### 3.物理模拟+体绘制
3D 模拟（例如，SPH）需要体积渲染管道：
- 密度场三线性插值→光线行进→法线计算→光照
- 阴影通过单独的缓冲区沿着光线累积光密度
- 环境贴图反射+菲涅耳混合

### 4. 多物理系统耦合
- **流体+刚体**：流体速度场驱动刚体运动；刚体占据改变流体边界
- **布料+碰撞器**：用于碰撞检测的球体/盒子形状，布料弹性响应
- **粒子+场**：粒子产生场（密度/涡度），场反过来驱动粒子（SPH / Biot-Savart）

### 5.物理模拟+音频可视化
- 通过“iChannel”绑定音频纹理，将频谱能量映射到外力或参数
- 低频驱动大规模运动，高频驱动小规模涡流/波纹