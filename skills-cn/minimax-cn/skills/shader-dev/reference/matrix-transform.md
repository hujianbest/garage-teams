# 矩阵变换和相机 — 详细参考

本文档是[SKILL.md](SKILL.md)的完整详细版本，涵盖分步教程、数学推导、详细解释和高级用法。

## 先决条件

- **矢量基础知识**：`vec2/vec3/vec4`、点积`dot()`、叉积`cross()`、`normalize()`的含义
- **矩阵基础知识**：GLSL 中 `mat2/mat3/mat4` 的列主存储，矩阵乘法 `m * v` 的语义
- **坐标系**：NDC（标准化设备坐标）、屏幕空间到世界空间映射、宽高比校正
- **三角函数**：`sin()`/`cos()`与旋转之间的关系
- **ShaderToy 内置变量**：`iResolution`、`iTime`、`iMouse`、`fragCoord`

## 核心原则

矩阵变换的本质是**坐标系变换**。在 ShaderToy 的光线行进管道中，变换矩阵起着两个关键作用：

1. **相机矩阵**：将屏幕像素坐标转换为世界空间中的光线方向（视图到世界）
2. **对象变换矩阵**：将采样点从世界空间转换到对象的局部空间（世界到局部，即“域变换”）

### 关键数学公式

**2D 旋转矩阵**（绕原点旋转角度 θ）：```
R(θ) = | cos θ  -sin θ |
       | sin θ   cos θ |
```**3D单轴旋转**（绕Y轴旋转为例）：```
Ry(θ) = | cos θ   0   sin θ |
        |   0     1     0   |
        | -sin θ  0   cos θ |
```**罗德里格斯旋转公式**（绕任意轴**k**旋转角度θ）：```
R = cos θ · I + (1 - cos θ) · k⊗k + sin θ · K
```其中 K 是轴向量 k 的斜对称矩阵。

**注视相机**（从眼睛看向目标）：```
forward = normalize(target - eye)
right   = normalize(cross(forward, worldUp))
up      = cross(right, forward)
viewMatrix = mat3(right, up, forward)
```**透视光线生成**：```
rayDir = normalize(camMatrix * vec3(uv, focalLength))
```其中“uv”是纵横比校正后的屏幕坐标，“focalLength”控制视野（值越大，FOV 越小）。

## 实施步骤

### 第 1 步：屏幕坐标标准化和长宽比校正

**什么**：将像素坐标“fragCoord”转换为以屏幕中心为中心的归一化 UV 坐标，Y 轴朝上且长宽比正确。

**为什么**：所有后续光线生成都取决于正确标准化的屏幕坐标。如果不校正纵横比，圆形就会变成椭圆形。

**代码**：```glsl
// Method A: range [-aspect, aspect] x [-1, 1] (most common)
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

// Method B: step-by-step approach (equivalent)
vec2 uv = fragCoord / iResolution.xy * 2.0 - 1.0;
uv.x *= iResolution.x / iResolution.y;
```### 步骤 2：构建旋转矩阵

**什么**：根据需求选择合适的旋转矩阵构建方法。

**为什么**：旋转是所有 3D 变换的核心。不同的场景适合不同的旋转表示。

**方法 A：2D 旋转 (mat2)**

最简单的形式，通常用于相机轨道中的两平面旋转：```glsl
mat2 rot2D(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c); // Note GLSL column-major order
}
```**方法 B：3D 单轴旋转 (mat3)**

独立的X/Y/Z轴旋转功能，可自由组合：```glsl
mat3 rotX(float a) {
    float s = sin(a), c = cos(a);
    return mat3(1, 0, 0,  0, c, s,  0, -s, c);
}
mat3 rotY(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c, 0, s,  0, 1, 0,  -s, 0, c);
}
mat3 rotZ(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c, s, 0,  -s, c, 0,  0, 0, 1);
}
```**方法 C：欧拉角到 mat3**

一步构建三个角度（偏航/俯仰/滚动）的完整旋转矩阵：```glsl
mat3 fromEuler(vec3 ang) {
    vec2 a1 = vec2(sin(ang.x), cos(ang.x));
    vec2 a2 = vec2(sin(ang.y), cos(ang.y));
    vec2 a3 = vec2(sin(ang.z), cos(ang.z));
    mat3 m;
    m[0] = vec3( a1.y*a3.y + a1.x*a2.x*a3.x,
                  a1.y*a2.x*a3.x + a3.y*a1.x,
                 -a2.y*a3.x);
    m[1] = vec3(-a2.y*a1.x, a1.y*a2.y, a2.x);
    m[2] = vec3( a3.y*a1.x*a2.x + a1.y*a3.x,
                  a1.x*a3.x - a1.y*a3.y*a2.x,
                  a2.y*a3.y);
    return m;
}
```**方法 D：Rodrigues 任意轴旋转 (mat3)**

围绕任何标准化轴旋转，基于罗德里格斯公式：```glsl
mat3 rotationMatrix(vec3 axis, float angle) {
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    return mat3(
        oc*axis.x*axis.x + c,          oc*axis.x*axis.y - axis.z*s, oc*axis.z*axis.x + axis.y*s,
        oc*axis.x*axis.y + axis.z*s,   oc*axis.y*axis.y + c,        oc*axis.y*axis.z - axis.x*s,
        oc*axis.z*axis.x - axis.y*s,   oc*axis.y*axis.z + axis.x*s, oc*axis.z*axis.z + c
    );
}
```### 第 3 步：构建 LookAt 相机

**什么**：从相机位置（眼睛）和观察目标（目标）构造一个视图到世界矩阵。

**为什么**：LookAt 是最直观的相机定义——只需指定“站在哪里”和“看向哪里”，矩阵就会自动计算三个正交基向量。

**经典 setCamera (mat3)**：```glsl
// cr = camera roll, usually pass 0.0
// Returns mat3 that transforms local ray direction to world space
mat3 setCamera(in vec3 ro, in vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);                   // forward
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);           // world up with roll
    vec3 cu = normalize(cross(cw, cp));               // right
    vec3 cv = normalize(cross(cu, cw));               // up
    return mat3(cu, cv, cw);
}
```**Gram-Schmidt 正交化版本 (mat3)**：

沿着 camDir 投影 camUp 的分量以确保严格的正交性：```glsl
vec3 camDir   = normalize(target - camPos);
vec3 camUp    = normalize(camUp - dot(camDir, camUp) * camDir); // Gram-Schmidt
vec3 camRight = normalize(cross(camDir, camUp));
```**mat4 LookAt（带翻译）**：

返回一个 4x4 矩阵，相机世界位置存储在第 4 列中。适合需要齐次坐标的场景：```glsl
mat4 LookAt(vec3 pos, vec3 target, vec3 up) {
    vec3 dir = normalize(target - pos);
    vec3 x = normalize(cross(dir, up));
    vec3 y = cross(x, dir);
    return mat4(vec4(x, 0), vec4(y, 0), vec4(dir, 0), vec4(pos, 1));
}
```### 步骤 4：生成透视光线

**什么**：通过相机矩阵将标准化屏幕坐标转换为世界空间光线方向。

**为什么**：透视投影通过在UV后附加固定的Z分量（焦距）来模拟近大远小的效果。焦距越大意味着 FOV 越小。

**方法A：mat3相机+归一化**：```glsl
// focalLength controls FOV: 1.0 ≈ 90°, 2.0 ≈ 53°, 4.0 ≈ 28°
#define FOCAL_LENGTH 2.0 // Adjustable: focal length, larger = narrower FOV
mat3 cam = setCamera(ro, ta, 0.0);
vec3 rd = cam * normalize(vec3(uv, FOCAL_LENGTH));
```**方法B：手动基向量组合**：```glsl
// FieldOfView controls ray divergence
#define FOV 1.0 // Adjustable: field of view scale factor
vec3 rd = normalize(camDir + (uv.x * camRight + uv.y * camUp) * FOV);
```**方法C：mat4相机+齐次坐标**：```glsl
// Direction vectors use w=0, positions use w=1
mat4 viewToWorld = LookAt(camPos, camTarget, camUp);
vec3 rd = (viewToWorld * normalize(vec4(uv, 1.0, 0.0))).xyz;
```### 步骤 5：鼠标交互相机

**什么**：将“iMouse”输入映射到相机轨道角度。

**为什么**：交互式相机是调试和展示 3D 着色器的基本需求。将鼠标 X 轴映射到水平旋转，将 Y 轴映射到俯仰角是最通用的模式。

**球坐标轨道相机**：```glsl
#define CAM_DIST 5.0     // Adjustable: camera-to-origin distance
#define CAM_HEIGHT 1.0   // Adjustable: default height offset

vec2 mouse = iMouse.xy / iResolution.xy;
float angleH = mouse.x * 6.2832;         // Horizontal: 0 ~ 2π
float angleV = mouse.y * 3.1416 - 1.5708; // Vertical: -π/2 ~ π/2

// Use auto-rotation when mouse is not clicked
if (iMouse.z <= 0.0) {
    angleH = iTime * 0.5;
    angleV = 0.3;
}

vec3 ro = vec3(
    CAM_DIST * cos(angleH) * cos(angleV),
    CAM_DIST * sin(angleV) + CAM_HEIGHT,
    CAM_DIST * sin(angleH) * cos(angleV)
);
vec3 ta = vec3(0.0, 0.0, 0.0); // Look-at target
```**欧拉角驱动相机**：```glsl
vec3 ang = vec3(0.0, 0.2, iTime * 0.3); // Default animation
if (iMouse.z > 0.0) {
    ang = vec3(0.0, clamp(2.0 - iMouse.y * 0.01, 0.0, 3.1416), iMouse.x * 0.01);
}
mat3 rot = fromEuler(ang);
vec3 ori = vec3(0.0, 0.0, 2.8) * rot;
vec3 dir = normalize(vec3(uv, -2.0)) * rot;
```### 步骤 6：SDF 对象域变换（平移、旋转、缩放）

**什么**：在光线行进距离函数中，对采样点应用逆变换，以实现对象平移/旋转/缩放。

**为什么**：SDF域变换原理是“变换空间，而不是物体”——将采样点逆变换到物体的局部坐标系中来评估距离，相当于变换物体本身。

**基本变换**：```glsl
// ===== Translation: offset the sampling point =====
float sdTranslated = sdSphere(p - vec3(2.0, 0.0, 0.0), 1.0);

// ===== Rotation: transform sampling point with rotation matrix =====
// Note: for orthogonal matrices (rotations), inverse = transpose
float sdRotated = sdBox(rotY(0.5) * p, vec3(1.0));

// ===== Scaling: divide by scale factor, multiply back into distance =====
#define SCALE 2.0 // Adjustable: object scale factor
float sdScaled = sdSphere(p / SCALE, 1.0) * SCALE;
```**SRT 组合（缩放 → 旋转 → 平移）**：

mat4版本，使用opTx进行域变换：```glsl
mat4 Loc4(vec3 d) {
    d *= -1.0;
    return mat4(1,0,0,d.x, 0,1,0,d.y, 0,0,1,d.z, 0,0,0,1);
}

mat4 transposeM4(in mat4 m) {
    return mat4(
        vec4(m[0].x, m[1].x, m[2].x, m[3].x),
        vec4(m[0].y, m[1].y, m[2].y, m[3].y),
        vec4(m[0].z, m[1].z, m[2].z, m[3].z),
        vec4(m[0].w, m[1].w, m[2].w, m[3].w)
    );
}

vec3 opTx(vec3 p, mat4 m) {
    return (transposeM4(m) * vec4(p, 1.0)).xyz;
}

// Usage example: translate to (3,0,0), then rotate 45° around Y axis
mat4 xform = Rot4Y(0.785) * Loc4(vec3(3.0, 0.0, 0.0));
float d = sdBox(opTx(p, xform), vec3(1.0));
```### 步骤 7：四元数旋转（高级）

**什么**：使用四元数绕任意轴旋转，适合关节动画等需要频繁旋转合成的场景。

**为什么**：四元数避免万向节锁定，并且插值（slerp）比矩阵更自然。双叉积公式“p + 2·cross(q.xyz, cross(q.xyz, p) + q.w·p)”是计算效率最高的四元数旋转实现。```glsl
// Axis-angle → quaternion
vec4 axisAngleToQuat(vec3 axis, float angleDeg) {
    float half_angle = angleDeg * 3.14159265 / 360.0; // degrees to half-radians
    vec2 sc = sin(vec2(half_angle, half_angle + 1.5707963));
    return vec4(normalize(axis) * sc.x, sc.y);
}

// Quaternion rotation (double cross product form)
vec3 quatRotate(vec3 pos, vec3 axis, float angleDeg) {
    vec4 q = axisAngleToQuat(axis, angleDeg);
    return pos + 2.0 * cross(q.xyz, cross(q.xyz, pos) + q.w * pos);
}

// Usage example: hierarchical rotation in joint animation
vec3 limbPos = quatRotate(p - shoulderOffset, vec3(1,0,0), swingAngle);
float d = sdEllipsoid(limbPos, limbSize);
```## 变体详细信息

### 变体 1：正交投影相机

**与基础版的区别**：光线方向固定（平行光线）；通过改变光线原点位置来实现不同的像素采样。适用于2D风格渲染、工程图、等轴测视图。

**关键修改代码**：```glsl
// Replace the perspective ray generation section
#define ORTHO_SIZE 5.0 // Adjustable: orthographic view size

mat3 cam = setCamera(ro, ta, 0.0);
// Orthographic: offset origin, fixed direction
vec3 rd = cam * vec3(0.0, 0.0, 1.0);  // Fixed direction
ro += cam * vec3(uv * ORTHO_SIZE, 0.0); // Offset origin
```### 变体 2：全欧拉角旋转相机

**与基础版的区别**：不使用LookAt；相反，直接从三个欧拉角构建旋转矩阵。适合第一人称视角或者需要翻滚的场景。

**关键修改代码**：```glsl
mat3 fromEuler(vec3 ang) {
    vec2 a1 = vec2(sin(ang.x), cos(ang.x));
    vec2 a2 = vec2(sin(ang.y), cos(ang.y));
    vec2 a3 = vec2(sin(ang.z), cos(ang.z));
    mat3 m;
    m[0] = vec3(a1.y*a3.y+a1.x*a2.x*a3.x, a1.y*a2.x*a3.x+a3.y*a1.x, -a2.y*a3.x);
    m[1] = vec3(-a2.y*a1.x, a1.y*a2.y, a2.x);
    m[2] = vec3(a3.y*a1.x*a2.x+a1.y*a3.x, a1.x*a3.x-a1.y*a3.y*a2.x, a2.y*a3.y);
    return m;
}

// In mainImage:
vec3 ang = vec3(pitch, yaw, roll);
mat3 rot = fromEuler(ang);
vec3 ori = vec3(0.0, 0.0, 3.0) * rot;
vec3 rd = normalize(vec3(uv, -2.0)) * rot;
```### 变体 3：四元数联合旋转

**与基本版本的区别**：在域变换中使用四元数而不是矩阵进行旋转，适用于分层关节动画（多肢生物系统）。

**关键修改代码**：```glsl
vec4 axisAngleToQuat(vec3 axis, float angleDeg) {
    float ha = angleDeg * 3.14159265 / 360.0;
    vec2 sc = sin(vec2(ha, ha + 1.5707963));
    return vec4(normalize(axis) * sc.x, sc.y);
}

vec3 quatRotate(vec3 p, vec3 axis, float angleDeg) {
    vec4 q = axisAngleToQuat(axis, angleDeg);
    return p + 2.0 * cross(q.xyz, cross(q.xyz, p) + q.w * p);
}

// Usage in scene:
vec3 legP = quatRotate(p - hipOffset, vec3(1,0,0), legAngle);
float dLeg = sdEllipsoid(legP, vec3(0.2, 0.6, 0.25));
```### 变体 4：mat4 SRT 管道（完整 4x4 变换）

**与基本版本的区别**：使用“mat4”齐次坐标将缩放-旋转-平移组合成单个矩阵，对采样点应用“opTx()”域变换。适用于需要管理许多对象变换的复杂场景。

**关键修改代码**：```glsl
mat4 Rot4Y(float a) {
    float c = cos(a), s = sin(a);
    return mat4(c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1);
}

mat4 Loc4(vec3 d) {
    d *= -1.0;
    return mat4(1,0,0,d.x, 0,1,0,d.y, 0,0,1,d.z, 0,0,0,1);
}

mat4 transposeM4(mat4 m) {
    return mat4(
        vec4(m[0].x,m[1].x,m[2].x,m[3].x),
        vec4(m[0].y,m[1].y,m[2].y,m[3].y),
        vec4(m[0].z,m[1].z,m[2].z,m[3].z),
        vec4(m[0].w,m[1].w,m[2].w,m[3].w));
}

vec3 opTx(vec3 p, mat4 m) {
    return (transposeM4(m) * vec4(p, 1.0)).xyz;
}

// Usage: translate then rotate (note matrix multiplication order is right-to-left)
mat4 xform = Rot4Y(angle) * Loc4(vec3(3.0, 0.0, 0.0));
float d = sdBox(opTx(p, xform), boxSize);
```### 变体 5：路径相机（动画飞行）

**与基本版本的区别**：相机沿着预定义的路径（例如隧道、赛道）移动，使用“LookAt”跟踪前方目标点。常见于隧道类型着色器。

**关键修改代码**：```glsl
// Path function (can be replaced with any curve)
vec2 pathCenter(float z) {
    return vec2(sin(z * 0.17) * 3.0, sin(z * 0.1 + 4.0) * 2.0);
}

// In mainImage:
float z_offset = iTime * 10.0; // Speed
vec3 camPos = vec3(pathCenter(z_offset), 0.0);
vec3 camTarget = vec3(pathCenter(z_offset + 5.0), 5.0);
vec3 camUp = vec3(sin(iTime * 0.3), cos(iTime * 0.3), 0.0);

mat4 viewToWorld = LookAt(camPos, camTarget, camUp);
vec3 rd = (viewToWorld * normalize(vec4(uv, 1.0, 0.0))).xyz;
```## 性能优化详情

### 1. 预先计算三角函数

仅计算一次相同角度的“sin/cos”，存储在“vec2”中：```glsl
// Bad: sin/cos each called once
mat2(cos(a), sin(a), -sin(a), cos(a));

// Good: compute both with sincos in one step
vec2 sc = sin(vec2(a, a + 1.5707963)); // sin(a), cos(a)
mat2(sc.y, sc.x, -sc.x, sc.y);
```### 2. 更喜欢 mat3 而不是 mat4

如果不需要平移（纯旋转），请始终使用“mat3”而不是“mat4”。 `mat3*vec3` 比 `mat4*vec4` 需要少 7 次乘加运算。

### 3. 旋转矩阵的逆 = 转置

正交旋转矩阵 R 满足“R⁻1 = Rᵀ”。当需要逆变换时，直接使用 transpose(m) 或交换乘法顺序 v * m（等价于 transpose(m) * v），避免一般矩阵求逆。

### 4. 避免在 SDF 内重建矩阵

如果旋转角度不依赖于采样点“p”，请将矩阵构造移到“map()”函数外部或将其缓存在全局变量中：```glsl
// Bad: rebuild matrix on every map() call
float map(vec3 p) {
    mat3 r = rotY(iTime); // Recomputed per pixel × per step
    return sdBox(r * p, vec3(1.0));
}

// Good: precompute in mainImage
mat3 g_rot; // Global
void mainImage(...) {
    g_rot = rotY(iTime); // Computed only once
    // ... rayMarch ...
}
float map(vec3 p) {
    return sdBox(g_rot * p, vec3(1.0));
}
```### 5. 合并连续旋转

多个旋转矩阵的乘积仍然是旋转矩阵。预乘并存储为单个矩阵：```glsl
// Bad: two matrix multiplications per sample
p = rotX(a) * (rotY(b) * p);

// Good: pre-multiply
mat3 combined = rotX(a) * rotY(b);
p = combined * p;
```## 组合建议

### 与 Ray Marching / SDF 结合（最常见）

矩阵变换几乎总是与 SDF 光线行进一起使用。相机矩阵生成光线，域变换矩阵放置对象。这是所有 3D ShaderToy 着色器的基础管道。

### 与噪声/fBm 结合

使用旋转矩阵将域扭曲应用于噪声采样坐标，打破轴对齐规律：```glsl
mat3 rot = rotAxis(vec3(0,0,1), 0.5 * iTime);
float n = fbm(rot * p);  // Rotate noise sampling direction
```使用时变旋转矩阵使水面噪声看起来更自然。

### 与分形/IFS 结合

在分形的每次迭代中添加旋转变换以创建更复杂的几何图案：```glsl
for (int i = 0; i < Iterations; i++) {
    z.xy = rot2D(angle) * z.xy; // Rotate each iteration
    z = abs(z);
    z = Scale * z - Offset * (Scale - 1.0);
}
```在 IFS 迭代中嵌入“mat2”旋转会产生更复杂的分形几何。

### 与灯光/材质相结合

在法线计算之后，可以使用变换矩阵将法线从局部空间转换回世界空间（用于照明计算）。对于纯旋转矩阵，法线变换与顶点变换相同。

### 与后处理结合

相机参数（如FOV）可用于景深计算； `mat2` 旋转可用于屏幕空间色差或运动模糊方向。