# 矩阵变换和相机

## 用例

- 3D场景中的相机系统（轨道相机、飞行相机、路径相机）
- SDF 对象域通过平移、旋转和缩放矩阵进行变换
- 从屏幕像素生成 3D 射线（透视/正交投影）
- 关节动画的分层旋转变换
- 噪声域扭曲中的旋转、IFS 分形迭代

## 核心原则

矩阵变换的本质是坐标系变换。在光线行进管道中：

1. **相机矩阵**：屏幕像素→世界空间光线方向（视图到世界）
2. **物体变换矩阵**：世界空间样本点→物体局部空间（世界到局部，域变换）

### 关键公式

**2D 旋转** R(θ) = `[[cosθ, -sinθ], [sinθ, cosθ]]`

**绕 Y 轴 3D 旋转** Ry(θ) = `[[cosθ, 0, sinθ], [0, 1, 0], [-sinθ, 0, cosθ]]`

**罗德里格斯（任意轴 k，角度 θ）**：`R = cosθ·I + (1-cosθ)·k⊗k + sinθ·K`

**看相机**：```
forward = normalize(target - eye)
right   = normalize(cross(forward, worldUp))
up      = cross(right, forward)
viewMatrix = mat3(right, up, forward)
```**透视光线**：`rd = 归一化（camMatrix * vec3（uv，focalLength））`

## 实施步骤

### 第 1 步：屏幕坐标标准化```glsl
// Range [-aspect, aspect] x [-1, 1]
vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
```### 步骤 2：旋转矩阵```glsl
// 2D rotation (mat2)
mat2 rot2D(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}

// 3D single-axis rotation (mat3)
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

// Euler angles → mat3 (yaw/pitch/roll)
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

// Rodrigues arbitrary-axis rotation (mat3)
mat3 rotationMatrix(vec3 axis, float angle) {
    axis = normalize(axis);
    float s = sin(angle), c = cos(angle), oc = 1.0 - c;
    return mat3(
        oc*axis.x*axis.x + c,          oc*axis.x*axis.y - axis.z*s, oc*axis.z*axis.x + axis.y*s,
        oc*axis.x*axis.y + axis.z*s,   oc*axis.y*axis.y + c,        oc*axis.y*axis.z - axis.x*s,
        oc*axis.z*axis.x - axis.y*s,   oc*axis.y*axis.z + axis.x*s, oc*axis.z*axis.z + c
    );
}
```### 步骤 3：查看相机```glsl
// Classic setCamera, cr = camera roll
mat3 setCamera(in vec3 ro, in vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = normalize(cross(cu, cw));
    return mat3(cu, cv, cw);
}

// mat4 LookAt (with translation, for homogeneous coordinate scenes)
mat4 LookAt(vec3 pos, vec3 target, vec3 up) {
    vec3 dir = normalize(target - pos);
    vec3 x = normalize(cross(dir, up));
    vec3 y = cross(x, dir);
    return mat4(vec4(x, 0), vec4(y, 0), vec4(dir, 0), vec4(pos, 1));
}
```### 步骤 4：透视光线生成```glsl
// mat3 camera — focalLength controls FOV: 1.0≈90°, 2.0≈53°, 4.0≈28°
#define FOCAL_LENGTH 2.0
mat3 cam = setCamera(ro, ta, 0.0);
vec3 rd = cam * normalize(vec3(uv, FOCAL_LENGTH));

// Manual basis vector composition
#define FOV 1.0
vec3 rd = normalize(camDir + (uv.x * camRight + uv.y * camUp) * FOV);

// mat4 homogeneous coordinates
mat4 viewToWorld = LookAt(camPos, camTarget, camUp);
vec3 rd = (viewToWorld * normalize(vec4(uv, 1.0, 0.0))).xyz;
```### 步骤 5：鼠标交互相机```glsl
// Spherical coordinate orbit camera
#define CAM_DIST 5.0
#define CAM_HEIGHT 1.0

vec2 mouse = iMouse.xy / iResolution.xy;
float angleH = mouse.x * 6.2832;
float angleV = mouse.y * 3.1416 - 1.5708;

if (iMouse.z <= 0.0) {
    angleH = iTime * 0.5;
    angleV = 0.3;
}

vec3 ro = vec3(
    CAM_DIST * cos(angleH) * cos(angleV),
    CAM_DIST * sin(angleV) + CAM_HEIGHT,
    CAM_DIST * sin(angleH) * cos(angleV)
);
vec3 ta = vec3(0.0);
```### 步骤 6：SDF 域变换```glsl
// Translation
float d = sdSphere(p - vec3(2.0, 0.0, 0.0), 1.0);

// Rotation (orthogonal matrix inverse = transpose)
float d = sdBox(rotY(0.5) * p, vec3(1.0));

// Scale (divide by scale factor, multiply back into distance)
#define SCALE 2.0
float d = sdSphere(p / SCALE, 1.0) * SCALE;

// mat4 SRT composition
mat4 Loc4(vec3 d) {
    d *= -1.0;
    return mat4(1,0,0,d.x, 0,1,0,d.y, 0,0,1,d.z, 0,0,0,1);
}

mat4 transposeM4(in mat4 m) {
    return mat4(
        vec4(m[0].x, m[1].x, m[2].x, m[3].x),
        vec4(m[0].y, m[1].y, m[2].y, m[3].y),
        vec4(m[0].z, m[1].z, m[2].z, m[3].z),
        vec4(m[0].w, m[1].w, m[2].w, m[3].w));
}

vec3 opTx(vec3 p, mat4 m) {
    return (transposeM4(m) * vec4(p, 1.0)).xyz;
}

// First translate to (3,0,0), then rotate 45° around Y-axis
mat4 xform = Rot4Y(0.785) * Loc4(vec3(3.0, 0.0, 0.0));
float d = sdBox(opTx(p, xform), vec3(1.0));
```### 步骤 7：四元数旋转```glsl
vec4 axisAngleToQuat(vec3 axis, float angleDeg) {
    float half_angle = angleDeg * 3.14159265 / 360.0;
    vec2 sc = sin(vec2(half_angle, half_angle + 1.5707963));
    return vec4(normalize(axis) * sc.x, sc.y);
}

vec3 quatRotate(vec3 pos, vec3 axis, float angleDeg) {
    vec4 q = axisAngleToQuat(axis, angleDeg);
    return pos + 2.0 * cross(q.xyz, cross(q.xyz, pos) + q.w * pos);
}

// Hierarchical rotation in joint animation
vec3 limbPos = quatRotate(p - shoulderOffset, vec3(1,0,0), swingAngle);
float d = sdEllipsoid(limbPos, limbSize);
```## 完整的代码模板

可以直接在ShaderToy中运行，演示LookAt相机+多对象域变换+鼠标交互。```glsl
// === Matrix Transforms & Camera - Complete Template ===

#define PI 3.14159265
#define MAX_STEPS 128
#define MAX_DIST 50.0
#define SURF_DIST 0.001
#define FOCAL_LENGTH 2.0
#define CAM_DIST 6.0
#define AUTO_SPEED 0.4

// ---------- Rotation Matrix Utilities ----------

mat2 rot2D(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}

mat3 rotX(float a) {
    float s = sin(a), c = cos(a);
    return mat3(1,0,0, 0,c,s, 0,-s,c);
}

mat3 rotY(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c,0,s, 0,1,0, -s,0,c);
}

mat3 rotZ(float a) {
    float s = sin(a), c = cos(a);
    return mat3(c,s,0, -s,c,0, 0,0,1);
}

mat3 rotAxis(vec3 axis, float angle) {
    axis = normalize(axis);
    float s = sin(angle), c = cos(angle), oc = 1.0 - c;
    return mat3(
        oc*axis.x*axis.x+c,         oc*axis.x*axis.y-axis.z*s, oc*axis.z*axis.x+axis.y*s,
        oc*axis.x*axis.y+axis.z*s,  oc*axis.y*axis.y+c,        oc*axis.y*axis.z-axis.x*s,
        oc*axis.z*axis.x-axis.y*s,  oc*axis.y*axis.z+axis.x*s, oc*axis.z*axis.z+c
    );
}

// ---------- LookAt Camera ----------

mat3 setCamera(vec3 ro, vec3 ta, float cr) {
    vec3 cw = normalize(ta - ro);
    vec3 cp = vec3(sin(cr), cos(cr), 0.0);
    vec3 cu = normalize(cross(cw, cp));
    vec3 cv = normalize(cross(cu, cw));
    return mat3(cu, cv, cw);
}

// ---------- SDF Primitives ----------

float sdSphere(vec3 p, float r) { return length(p) - r; }

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

// ---------- Scene (Domain Transform Demo) ----------

float map(vec3 p) {
    float d = p.y + 1.0; // Ground plane

    // Static sphere
    d = min(d, sdSphere(p, 0.5));

    // Rotating box (spinning around Y-axis)
    vec3 p2 = p - vec3(2.5, 0.0, 0.0);
    p2 = rotY(iTime * 0.8) * p2;
    d = min(d, sdBox(p2, vec3(0.6)));

    // Arbitrary-axis rotating torus
    vec3 p3 = p - vec3(-2.5, 0.5, 0.0);
    p3 = rotAxis(vec3(1,1,0), iTime * 0.6) * p3;
    d = min(d, sdTorus(p3, vec2(0.6, 0.2)));

    // Scaled + rotated sphere
    vec3 p4 = p - vec3(0.0, 0.5, 2.5);
    p4 = rotZ(iTime * 1.2) * rotX(iTime * 0.7) * p4;
    float scale = 1.5;
    d = min(d, sdSphere(p4 / scale, 0.4) * scale);

    return d;
}

// ---------- Normal ----------

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// ---------- Ray March ----------

float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }
    return t;
}

// ---------- Main Function ----------

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    // Mouse-interactive orbit camera
    float angleH, angleV;
    if (iMouse.z > 0.0) {
        vec2 m = iMouse.xy / iResolution.xy;
        angleH = m.x * 2.0 * PI;
        angleV = (m.y - 0.5) * PI;
    } else {
        angleH = iTime * AUTO_SPEED;
        angleV = 0.35;
    }

    vec3 ro = vec3(
        CAM_DIST * cos(angleH) * cos(angleV),
        CAM_DIST * sin(angleV) + 1.0,
        CAM_DIST * sin(angleH) * cos(angleV)
    );
    vec3 ta = vec3(0.0);

    mat3 cam = setCamera(ro, ta, 0.0);
    vec3 rd = cam * normalize(vec3(uv, FOCAL_LENGTH));

    float t = rayMarch(ro, rd);

    vec3 col = vec3(0.0);
    if (t < MAX_DIST) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        vec3 lightDir = normalize(vec3(1.0, 2.0, -1.0));
        float diff = max(dot(n, lightDir), 0.0);
        col = vec3(0.8, 0.85, 0.9) * (diff + 0.15);
        if (p.y < -0.99) {
            float checker = mod(floor(p.x) + floor(p.z), 2.0);
            col *= 0.5 + 0.3 * checker;
        }
    } else {
        col = vec3(0.4, 0.6, 0.9) - rd.y * 0.3;
    }

    col = pow(col, vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 正交投影相机```glsl
#define ORTHO_SIZE 5.0
mat3 cam = setCamera(ro, ta, 0.0);
vec3 rd = cam * vec3(0.0, 0.0, 1.0);   // Fixed direction
ro += cam * vec3(uv * ORTHO_SIZE, 0.0); // Offset origin
```### 欧拉角全旋转相机```glsl
vec3 ang = vec3(pitch, yaw, roll);
mat3 rot = fromEuler(ang);
vec3 ori = vec3(0.0, 0.0, 3.0) * rot;
vec3 rd = normalize(vec3(uv, -2.0)) * rot;
```### 四元数联合旋转```glsl
vec3 legP = quatRotate(p - hipOffset, vec3(1,0,0), legAngle);
float dLeg = sdEllipsoid(legP, vec3(0.2, 0.6, 0.25));
```### mat4 SRT 管道```glsl
mat4 Rot4Y(float a) {
    float c = cos(a), s = sin(a);
    return mat4(c,0,s,0, 0,1,0,0, -s,0,c,0, 0,0,0,1);
}

mat4 xform = Rot4Y(angle) * Loc4(vec3(3.0, 0.0, 0.0));
float d = sdBox(opTx(p, xform), boxSize);
```### 路径相机（动画飞行）```glsl
vec2 pathCenter(float z) {
    return vec2(sin(z * 0.17) * 3.0, sin(z * 0.1 + 4.0) * 2.0);
}

float z_offset = iTime * 10.0;
vec3 camPos = vec3(pathCenter(z_offset), 0.0);
vec3 camTarget = vec3(pathCenter(z_offset + 5.0), 5.0);
mat4 viewToWorld = LookAt(camPos, camTarget, camUp);
vec3 rd = (viewToWorld * normalize(vec4(uv, 1.0, 0.0))).xyz;
```## 表演与作曲

**性能**：
- 仅计算相同角度的 `sin/cos` 一次：`vec2 sc = sin(vec2(a, a + 1.5707963));`
- 使用 `mat3` 而不是 `mat4` 进行纯旋转（节省 7 次乘加）
- 正交旋转矩阵的逆=转置；使用“转置(m)”或“v * m”
- 预先计算不依赖于“map()”之外的“p”的矩阵
- 将多个旋转预乘到一个矩阵中

**成分**：
- **SDF / Ray Marching**：相机生成光线+域变换放置对象（基本管道）
- **噪声/fBm**：旋转采样坐标以打破轴对齐规律`fbm(rot * p)`
- **分形/IFS**：在迭代中嵌入旋转以创建复杂的几何形状
- **光照**：纯旋转矩阵的法线变换与顶点变换相同
- **后处理**：景深FOV； `mat2` 用于色差/运动模糊方向

## 进一步阅读

完整的分步教程、数学推导和高级用法，请参见 [参考](../reference/matrix-transform.md)