## WebGL2 适配要求

本文档中的代码模板使用ShaderToy GLSL风格。生成独立 HTML 页面时，必须适应 WebGL2：

- 使用 `canvas.getContext("webgl2")` **（必需！WebGL1 不支持 in/out 关键字）**
- 着色器第一行：“#version 300 es”，将“ precision highp float;”添加到片段着色器
- **重要提示：#version 必须是着色器的第一行！前面没有字符（包括空行/注释/Unicode BOM）**
- 顶点着色器：`attribute`→`in`、`variing`→`out`
- 片段着色器：`variing`→`in`、`gl_FragColor`→自定义`out vec4 fragColor`、`texture2D()`→`texture()`
- ShaderToy 的 `void mainImage(out vec4 fragColor, in vec2 fragCoord)` 需要适应标准的 `void main()` 入口点

### WebGL2全适配示例```glsl
// === Vertex Shader ===
const vertexShaderSource = `#version 300 es
in vec2 a_position;
void main() {
    gl_Position = vec4(a_position, 0.0, 1.0);
}`;

// === Fragment Shader ===
const fragmentShaderSource = `#version 300 es
precision highp float;

uniform float iTime;
uniform vec2 iResolution;

// IMPORTANT: Important: WebGL2 must declare the output variable!
out vec4 fragColor;

// ... other functions ...

void main() {
    // IMPORTANT: Use gl_FragCoord.xy instead of fragCoord
    vec2 fragCoord = gl_FragCoord.xy;

    vec3 col = vec3(0.0);

    // ... rendering logic ...

    // IMPORTANT: Write to fragColor, not gl_FragColor!
    fragColor = vec4(col, 1.0);
}`;
```**重要：常见 GLSL 编译错误：**
- `仅 GLSL ES 3.00 支持输入/输出存储限定符` → 检查您是否使用 `getContext("webgl2")` 和 `#version 300 es`
- `#version 指令必须出现在第一行` → 检查着色器字符串是否以 #version 开头，前面没有任何字符
- **重要：GLSL 保留字**：`cast`、`class`、`template`、`namespace`、`union`、`enum`、`typedef`、`sizeof`、`input`、`output`、`filter`、`image`、`sampler`、`fixed`、`volatile`、`public`、`static`、`extern`、`external`、`interface`、`long`、`short`、`double`、 `half`、`unsigned`、`superp`、`inline`、`noinline` 等都是 GLSL 保留字，**绝不能用作变量或函数名**！常见陷阱：为光线投射命名函数“cast”→编译失败。 **使用诸如“castRay”、“castShadow”、“shootRay”之类的复合名称**。
- **重要：GLSL 严格类型**：float/int 不能混合。 `if (x > 0)` 对于 int，`if (y < 0.0)` 对于 float。将 ivec3 成员与 float 进行比较需要显式转换：`float(c.y) < height`。当 getVoxel 返回 int 时，与 `> 0` 进行比较，而不是与 `> 0.0` 进行比较。函数参数类型必须完全匹配。
- **重要：向量维度不匹配（vec2 与 vec3）**：`p.xz` 返回 `vec2` 并且**绝不能**添加到 `vec3` 或传递给需要 `vec3` 参数的函数（例如，`fbm(vec3)`、`noise(vec3)`）！常见错误：`fbm(p.xz * 0.08 + vec3(...))` — `vec2 + vec3` 编译失败。 **修复**：要么使用`vec2`版本的noise/fbm，要么构造一个完整的vec3：`fbm(vec3(p.xz * 0.08, p.y * 0.05))`。同样，`vec2`只有`.x`/`.y`，无法访问`.z`/`.w`。
- **重要：length() / 浮点精度**：`length(ivec2)` 必须首先转换为 `vec2`：`length(vec2(d))`。精确的浮点相等比较几乎永远不会起作用；使用范围比较：`floor(p.y) == Floor(height)`

# 体素渲染技巧

## 用例
- 在常规 3D 网格上渲染离散体积数据（Minecraft 风格的世界、医疗体积数据、建筑体素模型）
- 像素精确的块/立方体场景
- “块艺术”、“3D像素艺术”、“低多边形体素”视觉风格
- 纯片段着色器环境（如 ShaderToy）中的实时体素场景
- 高级光照效果，包括阴影、AO 和全局照明

## 核心原则

体素渲染的核心是**DDA（数字微分分析器）光线遍历算法**：从相机投射光线穿过每个像素，沿着光线方向逐个单元地穿过 3D 网格，直到击中占用的体素。

对于射线`P(t) = rayPos + t * rayDir`，DDA 维持：
- **`mapPos`** = `floor(rayPos)`: 当前网格坐标（整数）
- **`deltaDist`** = `abs(1.0 / rayDir)`: 穿过一个单元格的成本
- **`sideDist`** = `(sign(rayDir) * (mapPos - rayPos) + sign(rayDir) * 0.5 + 0.5) * deltaDist`: t 到每个轴上下一个边界的距离

每一步沿着具有最小“sideDist”的轴前进，更新“sideDist += deltaDist”和“mapPos += rayStep”。

命中时法线：`normal = -mask * rayStep`

面 UV 是通过将击中点投影到击中面的两个切轴上来获得的。

## 实施步骤

### 第 1 步：相机光线构造```glsl
vec2 screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0;
vec3 cameraDir = vec3(0.0, 0.0, 0.8);  // Focal length; larger = narrower FOV
vec3 cameraPlaneU = vec3(1.0, 0.0, 0.0);
vec3 cameraPlaneV = vec3(0.0, 1.0, 0.0) * iResolution.y / iResolution.x;
vec3 rayDir = cameraDir + screenPos.x * cameraPlaneU + screenPos.y * cameraPlaneV;
vec3 rayPos = vec3(0.0, 2.0, -12.0);
```### 步骤 2：DDA 初始化```glsl
ivec3 mapPos = ivec3(floor(rayPos));
vec3 rayStep = sign(rayDir);
vec3 deltaDist = abs(1.0 / rayDir);  // When ray is normalized, equivalent to abs(1.0/rd), no length() needed
vec3 sideDist = (sign(rayDir) * (vec3(mapPos) - rayPos) + (sign(rayDir) * 0.5) + 0.5) * deltaDist;
```### 步骤3：DDA遍历循环（无分支版本）```glsl
#define MAX_RAY_STEPS 64

bvec3 mask;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    if (getVoxel(mapPos)) break;
    // Branchless axis selection
    mask = lessThanEqual(sideDist.xyz, min(sideDist.yzx, sideDist.zxy));
    sideDist += vec3(mask) * deltaDist;
    mapPos += ivec3(vec3(mask)) * ivec3(rayStep);
}
```替代形式（步骤版本）：```glsl
vec3 mask = step(sideDist.xyz, sideDist.yzx) * step(sideDist.xyz, sideDist.zxy);
sideDist += mask * deltaDist;
mapPos += mask * rayStep;
```### 步骤 4：体素占用函数```glsl
// Basic version: solid block (most common; use this when user asks for "voxel cube")
// IMPORTANT: Important: getVoxel receives ivec3, but all internal calculations must use float!
bool getVoxel(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);  // ivec3 → vec3 conversion (required!)
    float d = sdBox(p, vec3(6.0));  // Solid 12x12x12 cube
    return d < 0.0;
}

// Advanced version: SDF boolean operations (sphere carved from box = only corners remain)
bool getVoxelCarved(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);
    float d = max(-sdSphere(p, 7.5), sdBox(p, vec3(6.0)));  // box ∩ ¬sphere
    return d < 0.0;
}

// Advanced version: height map terrain with material IDs
// IMPORTANT: Key: all comparisons must use float! c.y is int and must be converted to float for comparison
// IMPORTANT: Important: must use range comparison, not exact equality (floating-point precision issues)
int getVoxelMaterial(ivec3 c) {
    vec3 p = vec3(c);  // ivec3 → vec3 conversion (required!)
    float groundHeight = getTerrainHeight(p.xz);  // p.xz is vec2, passes float parameters
    if (float(c.y) < groundHeight) return 1;       // int → float comparison
    if (float(c.y) < groundHeight + 4.0) return 7;  // int → float comparison
    return 0;
}

// Pure float version (simpler, recommended):
int getVoxelMaterial(vec3 c) {
    float groundHeight = getTerrainHeight(c.xz);
    // IMPORTANT: Use range comparison, never exact equality!
    if (c.y >= groundHeight && c.y < groundHeight + 1.0) return 1;  // Grass top layer
    if (c.y >= groundHeight - 3.0 && c.y < groundHeight) return 2; // Dirt layer
    if (c.y < groundHeight - 3.0) return 3;  // Stone layer
    return 0;
}

// Advanced version: mountain terrain (height-based coloring: grass green → rock gray → snow white)
// IMPORTANT: Key 1: color thresholds must be based on heightRatio (normalized height 0~1), not absolute height!
// IMPORTANT: Key 2: maxH must match the actual maximum return value of getMountainHeight!
//           If getMountainHeight returns at most 15.0, maxH must be 15.0, not arbitrarily 20.0
// IMPORTANT: Key 3: threshold spacing must be large enough (at least 0.2), otherwise color bands are too narrow to see
// IMPORTANT: Key 4: grass area typically covers the largest terrain area (low elevation); set grass threshold high (0.4) to ensure green is clearly visible
float maxH = 15.0;  // IMPORTANT: Must equal the actual max value of getMountainHeight!
int getMountainVoxel(vec3 c) {
    float height = getMountainHeight(c.xz);  // Returns 0 ~ maxH
    if (c.y > height) return 0;  // Air
    float heightRatio = c.y / maxH;  // Normalize to 0~1
    // IMPORTANT: Thresholds from low to high: grass < 0.4, rock 0.4~0.7, snow > 0.7
    if (heightRatio < 0.4) return 1;  // Grass (green) — largest area
    if (heightRatio < 0.7) return 2;  // Rock (gray)
    return 3;                          // Snow cap (white)
}
// IMPORTANT: Corresponding material colors must have sufficient saturation and clear contrast:
// mat==1: vec3(0.25, 0.55, 0.15)  Grass green (saturated green, must not be grayish!)
// mat==2: vec3(0.5, 0.45, 0.4)   Rock gray-brown
// mat==3: vec3(0.92, 0.93, 0.96) Snow white
// IMPORTANT: Lighting must not be too bright or it washes out colors! Sun intensity ≤ 2.0, sky light ≤ 1.0
// IMPORTANT: Gamma correction pow(col, vec3(0.4545)) brightens dark colors and reduces saturation;
//    if colors look grayish-white, make grass green more saturated: vec3(0.2, 0.5, 0.1)

// IMPORTANT: Rotating objects: to rotate a voxel object, apply inverse rotation to the sample point in getVoxel!
// Do not rotate the camera to simulate object rotation (that only changes the viewpoint)
bool getVoxelRotating(ivec3 c) {
    vec3 p = vec3(c) + vec3(0.5);
    // Rotate around Y axis: apply inverse rotation to sample point
    float angle = -iTime;  // Negative sign = inverse transform
    float s = sin(angle), co = cos(angle);
    p.xz = vec2(p.x * co - p.z * s, p.x * s + p.z * co);
    float d = sdBox(p, vec3(6.0));  // Rotated solid cube
    return d < 0.0;
}
```### 步骤 5：面部阴影（普通 + 底色）```glsl
vec3 normal = -vec3(mask) * rayStep;
vec3 color;
if (mask.x) color = vec3(0.5);   // Side faces darkest
if (mask.y) color = vec3(1.0);   // Top face brightest
if (mask.z) color = vec3(0.75);  // Front/back faces medium
fragColor = vec4(color, 1.0);
```### 步骤 6：精确的击球位置和面部 UV```glsl
float t = dot(sideDist - deltaDist, vec3(mask));
vec3 hitPos = rayPos + rayDir * t;
vec3 uvw = hitPos - vec3(mapPos);
vec2 uv = vec2(dot(vec3(mask) * uvw.yzx, vec3(1.0)),
               dot(vec3(mask) * uvw.zxy, vec3(1.0)));
```### 步骤 7：邻近体素 AO```glsl
float vertexAo(vec2 side, float corner) {
    return (side.x + side.y + max(corner, side.x * side.y)) / 3.0;
}

vec4 voxelAo(vec3 pos, vec3 d1, vec3 d2) {
    vec4 side = vec4(
        getVoxel(pos + d1), getVoxel(pos + d2),
        getVoxel(pos - d1), getVoxel(pos - d2));
    vec4 corner = vec4(
        getVoxel(pos + d1 + d2), getVoxel(pos - d1 + d2),
        getVoxel(pos - d1 - d2), getVoxel(pos + d1 - d2));
    vec4 ao;
    ao.x = vertexAo(side.xy, corner.x);
    ao.y = vertexAo(side.yz, corner.y);
    ao.z = vertexAo(side.zw, corner.z);
    ao.w = vertexAo(side.wx, corner.w);
    return 1.0 - ao;
}

// Bilinear interpolation
vec4 ambient = voxelAo(mapPos - rayStep * mask, mask.zxy, mask.yzx);
float ao = mix(mix(ambient.z, ambient.w, uv.x), mix(ambient.y, ambient.x, uv.x), uv.y);
ao = pow(ao, 1.0 / 3.0);  // Gamma correction to control AO intensity
```### 第 8 步：DDA 阴影射线```glsl
// IMPORTANT: Shadow steps must be capped at 16; total main ray + shadow ray steps should not exceed 80
#define MAX_SHADOW_STEPS 16

float castShadow(vec3 ro, vec3 rd) {
    vec3 pos = floor(ro);
    vec3 ri = 1.0 / rd;
    vec3 rs = sign(rd);
    vec3 dis = (pos - ro + 0.5 + rs * 0.5) * ri;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        if (getVoxel(ivec3(pos))) return 0.0;
        vec3 mm = step(dis.xyz, dis.yzx) * step(dis.xyz, dis.zxy);
        dis += mm * rs * ri;
        pos += mm * rs;
    }
    return 1.0;
}

vec3 sundir = normalize(vec3(-0.5, 0.6, 0.7));
float shadow = castShadow(hitPos + normal * 0.01, sundir);
float diffuse = max(dot(normal, sundir), 0.0) * shadow;
```## 完整的代码模板```glsl
// === Voxel Rendering - Complete ShaderToy Template ===
// Includes: DDA traversal, face shading, neighbor AO, hard shadows

// IMPORTANT: Performance critical: SwiftShader software renderer (headless browser evaluation environment) cannot handle too many loop iterations
// Default 64+16=80 steps, suitable for most scenes. Simple scenes (single cube) can increase to 96+24
// Multi-building/character/Minecraft scenes must keep 64+16 or lower!
#define MAX_RAY_STEPS 64
#define MAX_SHADOW_STEPS 16
#define GRID_SIZE 16.0

// ---- Math Utilities ----
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdBox(vec3 p, vec3 b) {
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}
float hash31(vec3 n) { return fract(sin(dot(n, vec3(1.0, 113.0, 257.0))) * 43758.5453); }

vec2 rotate2d(vec2 v, float a) {
    float s = sin(a), c = cos(a);
    return vec2(v.x * c - v.y * s, v.y * c + v.x * s);
}

// ---- Voxel Scene Definition ----
// IMPORTANT: Default solid cube. Use sdBox for "voxel cube"; add SDF boolean ops for carved/sculpted shapes
int getVoxel(vec3 c) {
    vec3 p = c + 0.5;
    float d = sdBox(p, vec3(6.0));  // Solid 12x12x12 block
    if (d < 0.0) {
        if (p.y < -3.0) return 2;
        return 1;
    }
    return 0;
}

// ---- Neighbor AO ----
float getOccupancy(vec3 c) { return float(getVoxel(c) > 0); }

float vertexAo(vec2 side, float corner) {
    return (side.x + side.y + max(corner, side.x * side.y)) / 3.0;
}

vec4 voxelAo(vec3 pos, vec3 d1, vec3 d2) {
    vec4 side = vec4(
        getOccupancy(pos + d1), getOccupancy(pos + d2),
        getOccupancy(pos - d1), getOccupancy(pos - d2));
    vec4 corner = vec4(
        getOccupancy(pos + d1 + d2), getOccupancy(pos - d1 + d2),
        getOccupancy(pos - d1 - d2), getOccupancy(pos + d1 - d2));
    vec4 ao;
    ao.x = vertexAo(side.xy, corner.x);
    ao.y = vertexAo(side.yz, corner.y);
    ao.z = vertexAo(side.zw, corner.z);
    ao.w = vertexAo(side.wx, corner.w);
    return 1.0 - ao;
}

// ---- DDA Traversal Core ----
struct HitInfo {
    bool  hit;
    float t;
    vec3  pos;
    vec3  normal;
    vec3  mapPos;
    vec2  uv;
    int   mat;
};

HitInfo castRay(vec3 ro, vec3 rd, int maxSteps) {
    HitInfo info;
    info.hit = false;
    info.t = 0.0;

    vec3 mapPos = floor(ro);
    vec3 rayStep = sign(rd);
    vec3 deltaDist = abs(1.0 / rd);
    vec3 sideDist = (rayStep * (mapPos - ro) + rayStep * 0.5 + 0.5) * deltaDist;
    vec3 mask = vec3(0.0);

    for (int i = 0; i < maxSteps; i++) {
        int vox = getVoxel(mapPos);
        if (vox > 0) {
            info.hit = true;
            info.mat = vox;
            info.normal = -mask * rayStep;
            info.mapPos = mapPos;
            info.t = dot(sideDist - deltaDist, mask);
            info.pos = ro + rd * info.t;
            vec3 uvw = info.pos - mapPos;
            info.uv = vec2(dot(mask * uvw.yzx, vec3(1.0)),
                           dot(mask * uvw.zxy, vec3(1.0)));
            return info;
        }
        mask = step(sideDist.xyz, sideDist.yzx) * step(sideDist.xyz, sideDist.zxy);
        sideDist += mask * deltaDist;
        mapPos += mask * rayStep;
    }
    return info;
}

// ---- Shadow Ray ----
// IMPORTANT: Shadow steps at 16 (combined with main ray 64 = 80, within SwiftShader safe range)
float castShadow(vec3 ro, vec3 rd) {
    vec3 pos = floor(ro);
    vec3 ri = 1.0 / rd;
    vec3 rs = sign(rd);
    vec3 dis = (pos - ro + 0.5 + rs * 0.5) * ri;
    for (int i = 0; i < MAX_SHADOW_STEPS; i++) {
        // IMPORTANT: getVoxel returns int; comparison must use int constant (0), not float (0.0)
        if (getVoxel(pos) > 0) return 0.0;
        vec3 mm = step(dis.xyz, dis.yzx) * step(dis.xyz, dis.zxy);
        dis += mm * rs * ri;
        pos += mm * rs;
    }
    return 1.0;
}

// ---- Material Colors ----
// IMPORTANT: Texture coloring key: "low saturation" does not mean "near white/gray"!
// Low saturation = colorful but not vivid, must retain clear hue differences (e.g., brick red 0.55,0.35,0.3 not gray-white 0.8,0.8,0.8)
// Brick/stone textures: use UV periodic patterns (mortar lines = dark lines), never use solid colors!
vec3 getMaterialColor(int mat, vec2 uv) {
    vec3 col = vec3(0.6);
    if (mat == 1) col = vec3(0.7, 0.7, 0.75);
    if (mat == 2) col = vec3(0.4, 0.55, 0.3);
    float checker = mod(floor(uv.x * 4.0) + floor(uv.y * 4.0), 2.0);
    col *= 0.85 + 0.15 * checker;
    return col;
}

// ---- Brick/Stone Texture Coloring (use this to replace getMaterialColor when user requests "brick texture") ----
// IMPORTANT: Key: brick texture = UV periodic pattern (staggered rows + mortar dark lines), not solid color!
vec3 getBrickColor(vec2 uv, vec3 baseColor, vec3 mortarColor) {
    vec2 brickUV = uv * vec2(4.0, 8.0);
    float row = floor(brickUV.y);
    brickUV.x += mod(row, 2.0) * 0.5;  // Staggered row offset
    vec2 f = fract(brickUV);
    float mortar = step(f.x, 0.06) + step(f.y, 0.08);  // Mortar joints
    mortar = clamp(mortar, 0.0, 1.0);
    float noise = fract(sin(dot(floor(brickUV), vec2(12.9898, 78.233))) * 43758.5453);
    vec3 brickVariation = baseColor * (0.85 + 0.3 * noise);  // Slight color variation per brick
    return mix(brickVariation, mortarColor, mortar);
}
// Usage example (maze walls):
// if (mat == 1) col = getBrickColor(uv, vec3(0.55, 0.35, 0.3), vec3(0.4, 0.38, 0.35)); // Brick red + mortar
// if (mat == 2) col = getBrickColor(uv, vec3(0.5, 0.48, 0.42), vec3(0.35, 0.33, 0.3)); // Gray stone brick

// ---- Main Function ----
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 screenPos = (fragCoord.xy / iResolution.xy) * 2.0 - 1.0;
    screenPos.x *= iResolution.x / iResolution.y;

    vec3 ro = vec3(0.0, 2.0 * sin(iTime * 0.5), -12.0);
    vec3 forward = vec3(0.0, 0.0, 0.8);
    vec3 rd = normalize(forward + vec3(screenPos, 0.0));

    ro.xz = rotate2d(ro.xz, iTime * 0.3);
    rd.xz = rotate2d(rd.xz, iTime * 0.3);

    vec3 sunDir = normalize(vec3(-0.5, 0.6, 0.7));
    vec3 skyColor = vec3(0.6, 0.75, 0.9);

    HitInfo hit = castRay(ro, rd, MAX_RAY_STEPS);

    vec3 col;
    if (hit.hit) {
        vec3 matCol = getMaterialColor(hit.mat, hit.uv);

        vec3 mask = abs(hit.normal);
        vec4 ambient = voxelAo(hit.mapPos, mask.zxy, mask.yzx);
        float ao = mix(
            mix(ambient.z, ambient.w, hit.uv.x),
            mix(ambient.y, ambient.x, hit.uv.x),
            hit.uv.y);
        ao = pow(ao, 0.5);

        float shadow = castShadow(hit.pos + hit.normal * 0.01, sunDir);

        float diff = max(dot(hit.normal, sunDir), 0.0);
        float sky = 0.5 + 0.5 * hit.normal.y;

        vec3 lighting = vec3(0.0);
        // IMPORTANT: Mountain/terrain scenes: sun light ≤ 2.0, sky light ≤ 1.0; too bright washes out material color differences
        lighting += 2.0 * diff * vec3(1.0, 0.95, 0.8) * shadow;
        lighting += 1.0 * sky * skyColor;
        lighting *= ao;

        col = matCol * lighting;

        // IMPORTANT: Fog: coefficient should not be too large, otherwise nearby objects get swallowed into pure sky color
        // 0.0002 suits GRID_SIZE=16 scenes; use smaller coefficients for larger scenes
        float fog = 1.0 - exp(-0.0002 * hit.t * hit.t);
        col = mix(col, skyColor, clamp(fog, 0.0, 0.7));  // Clamp prevents objects from disappearing entirely
    } else {
        col = skyColor - rd.y * 0.2;
    }

    col = pow(clamp(col, 0.0, 1.0), vec3(0.4545));
    fragColor = vec4(col, 1.0);
}
```## 常见变体

### 变体 1：发光体素（发光累积）
在 DDA 遍历期间累积基于距离的发光值；即使未命中也会产生半透明的发光。```glsl
float glow = 0.0;
for (int i = 0; i < MAX_RAY_STEPS; i++) {
    float d = sdSomeShape(vec3(mapPos));
    glow += 0.015 / (0.01 + d * d);
    if (d < 0.0) break;
    // ... normal DDA stepping ...
}
vec3 col = baseColor + glow * vec3(0.4, 0.6, 1.0);
```### 变体 2：圆形体素（体素内 SDF 细化）
DDA 命中后，在体素内执行 SDF 射线行进以渲染圆形块。```glsl
float id = hash31(mapPos);
float w = 0.05 + 0.35 * id;

float sdRoundedBox(vec3 p, float w) {
    return length(max(abs(p) - 0.5 + w, 0.0)) - w;
}

vec3 localP = hitPos - mapPos - 0.5;
for (int j = 0; j < 6; j++) {
    float h = sdRoundedBox(localP, w);
    if (h < 0.025) break;
    localP += rd * max(0.0, h);
}
```### 变体 3：混合 SDF-体素遍历
远距离大步长的 SDF 球体追踪，切换到接近表面的精确 DDA。```glsl
#define VOXEL_SIZE 0.0625
#define SWITCH_DIST (VOXEL_SIZE * 1.732)

bool useVoxel = false;
for (int i = 0; i < MAX_STEPS; i++) {
    vec3 pos = ro + rd * t;
    float d = mapSDF(useVoxel ? voxelCenter : pos);
    if (!useVoxel) {
        t += d;
        if (d < SWITCH_DIST) { useVoxel = true; voxelPos = getVoxelPos(pos); }
    } else {
        if (d < 0.0) break;
        if (d > SWITCH_DIST) { useVoxel = false; t += d; continue; }
        vec3 exitT = (voxelPos - ro * ird + ird * VOXEL_SIZE * 0.5);
        // ... select minimum axis to advance ...
    }
}
```### 变体 4：体素锥追踪
构建多级 mipmap，从命中点投射锥形光线以实现全局照明。```glsl
vec4 traceCone(vec3 origin, vec3 dir, float coneRatio) {
    vec4 light = vec4(0.0);
    float t = 1.0;
    for (int i = 0; i < 58; i++) {
        vec3 sp = origin + dir * t;
        float diameter = max(1.0, t * coneRatio);
        float lod = log2(diameter);
        vec4 sample = voxelFetch(sp, lod);
        light += sample * (1.0 - light.w);
        t += diameter;
    }
    return light;
}
```### 变体 5：PBR 光照 + 多次反射
GGX BRDF 取代 Lambert，具有金属/粗糙度参数；投射第二条 DDA 射线进行反射。```glsl
float ggxDiffuse(float NoL, float NoV, float LoH, float roughness) {
    float FD90 = 0.5 + 2.0 * roughness * LoH * LoH;
    float a = 1.0 + (FD90 - 1.0) * pow(1.0 - NoL, 5.0);
    float b = 1.0 + (FD90 - 1.0) * pow(1.0 - NoV, 5.0);
    return a * b / 3.14159;
}

vec3 rd2 = reflect(rd, normal);
HitInfo reflHit = castRay(hitPos + normal * 0.001, rd2, 64);
vec3 reflColor = reflHit.hit ? shade(reflHit) : skyColor;

float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(normal, -rd), 0.0), 5.0);
col += fresnel * reflColor;
```### 变体 6：体素水场景（水 + 水下体素）
水面波纹反射、水下折射、沙子和海藻构成完整的水景。```glsl
float waterY = 0.0;

// Underwater voxel scene definition (sand + seaweed)
// IMPORTANT: All coordinate operations must use correct vector dimensions!
// c.xz returns vec2, only has .x/.y components, cannot use .z!
int getVoxel(vec3 c) {
    float sandHeight = -3.0 + 0.5 * sin(c.x * 0.3) * cos(c.z * 0.4);
    if (c.y < sandHeight) return 1;      // Sand interior
    if (c.y < sandHeight + 1.0) return 2; // Sand surface
    // Seaweed: only grows underwater, above sand
    float grassHash = fract(sin(dot(floor(c.xz), vec2(12.9898, 78.233))) * 43758.5453);
    // IMPORTANT: floor(c.xz) is vec2; the second argument to dot() must also be vec2
    if (grassHash > 0.85 && c.y >= sandHeight + 1.0 && c.y < sandHeight + 1.0 + 3.0 * grassHash) {
        return 3;  // Seaweed
    }
    return 0;
}

// Handle water surface in main rendering
float tWater = (waterY - ro.y) / rd.y;
bool hitWater = tWater > 0.0 && (tWater < hit.t || !hit.hit);

if (hitWater) {
    vec3 waterPos = ro + rd * tWater;
    vec3 waterNormal = vec3(0.0, 1.0, 0.0);
    // IMPORTANT: waterPos.xz is vec2; access with .x/.y (not .x/.z)
    vec2 waveXZ = waterPos.xz;  // vec2: waveXZ.x = worldX, waveXZ.y = worldZ
    waterNormal.x += 0.05 * sin(waveXZ.x * 3.0 + iTime);
    waterNormal.z += 0.05 * cos(waveXZ.y * 2.0 + iTime * 0.7);
    waterNormal = normalize(waterNormal);

    float fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(waterNormal, -rd), 0.0), 5.0);

    // Reflection
    vec3 reflDir = reflect(rd, waterNormal);
    HitInfo reflHit = castRay(waterPos + waterNormal * 0.01, reflDir, 64);
    vec3 reflCol = reflHit.hit ? getMaterialColor(reflHit.mat, reflHit.uv) : skyColor;

    // Refraction (underwater voxels: sand, seaweed)
    vec3 refrDir = refract(rd, waterNormal, 1.0 / 1.33);
    HitInfo refrHit = castRay(waterPos - waterNormal * 0.01, refrDir, 64);
    vec3 refrCol;
    if (refrHit.hit) {
        vec3 matCol = getMaterialColor(refrHit.mat, refrHit.uv);
        float underwaterDist = length(refrHit.pos - waterPos);
        refrCol = mix(matCol, vec3(0.0, 0.15, 0.3), 1.0 - exp(-0.1 * underwaterDist));
    } else {
        refrCol = vec3(0.0, 0.1, 0.3);
    }

    col = mix(refrCol, reflCol, fresnel);
    col = mix(col, vec3(0.0, 0.3, 0.5), 0.2);
}
```### 变体 7：旋转体素对象
将体素对象作为一个整体进行旋转。核心：对getVoxel中的样本点应用逆旋转。```glsl
// IMPORTANT: Correct way to rotate objects: apply inverse rotation to sample coordinates in getVoxel
// Wrong approach: only rotate the camera (that just changes the viewpoint, not the object)
int getVoxel(vec3 c) {
    vec3 p = c + 0.5;
    // Rotate around Y axis
    float angle = -iTime * 0.5;
    float s = sin(angle), co = cos(angle);
    p.xz = vec2(p.x * co - p.z * s, p.x * s + p.z * co);
    // Can also rotate around multiple axes:
    // p.yz = vec2(p.y * co2 - p.z * s2, p.y * s2 + p.z * co2);  // X axis rotation
    float d = sdBox(p, vec3(6.0));
    if (d < 0.0) return 1;
    return 0;
}
```### 变体 8：室内/洞穴/封闭场景（点光源 + 高环境照明）
室内、洞穴、地下、科幻基地等封闭或半封闭场景都需要点光源和高环境照明。```glsl
// IMPORTANT: Key points for enclosed/semi-enclosed scenes (caves, interiors, sci-fi bases, mazes, etc.):
// 1. Camera must be placed inside the cavity (a position where getVoxel returns 0)
// 2. Must use point lights, not just directional light (directional light blocked by walls/ceiling = total darkness!)
// 3. Ambient light must be high enough (at least 0.2-0.3) to prevent scene from being too dark to see details
// 4. Can use multiple point lights + emissive voxels to simulate torches/fluorescence/holographic displays
// 5. Sci-fi scene metallic walls need bright enough light sources to show reflections
// 6. Emissive elements (holographic screens, indicator lights, magic circles) use emissive materials: add emissive color directly to lighting

// Cave scene: cavity = area where getVoxel returns 0
// IMPORTANT: Cave/terrain noise functions must respect vector dimensions!
// p.xz is vec2; if noise/fbm function takes vec3, construct a full vec3:
//   Correct: fbm(vec3(p.xz, p.y * 0.5))  or use vec2 version of noise
//   Wrong: fbm(p.xz + vec3(...))  ← vec2 + vec3 compile failure!
int getVoxel(vec3 c) {
    float cave = sdSphere(c + 0.5, 12.0);
    // IMPORTANT: For noise-carved detail, use c's components directly (all float)
    cave += 2.0 * sin(c.x * 0.3) * sin(c.y * 0.4) * sin(c.z * 0.35);
    if (cave > 0.0) return 1;  // Rock wall
    return 0;  // Cavity (camera goes here)
}

// Point light attenuation
vec3 pointLightPos = vec3(0.0, 3.0, 0.0);
vec3 toLight = pointLightPos - hit.pos;
float lightDist = length(toLight);
vec3 lightDir = toLight / lightDist;
float attenuation = 1.0 / (1.0 + 0.1 * lightDist + 0.01 * lightDist * lightDist);

float diff = max(dot(hit.normal, lightDir), 0.0);
float shadow = castShadow(hit.pos + hit.normal * 0.01, lightDir);

vec3 lighting = vec3(0.0);
// IMPORTANT: High ambient light to prevent total darkness (required for enclosed scenes! at least 0.2)
lighting += vec3(0.25, 0.22, 0.2);  // Warm ambient light
lighting += 3.0 * diff * attenuation * vec3(1.0, 0.8, 0.5) * shadow;  // Point light

// Multiple torches/emissive objects (use sin for flicker animation)
vec3 torch1 = vec3(5.0, 2.0, 3.0);
vec3 torch2 = vec3(-4.0, 1.0, -5.0);
float flicker1 = 0.8 + 0.2 * sin(iTime * 5.0 + 1.0);
float flicker2 = 0.8 + 0.2 * sin(iTime * 4.3 + 2.7);
lighting += calcPointLight(hit.pos, hit.normal, torch1, vec3(1.0, 0.6, 0.2)) * flicker1;
lighting += calcPointLight(hit.pos, hit.normal, torch2, vec3(0.2, 1.0, 0.5)) * flicker2;

// Emissive materials (holographic displays, fluorescent moss, indicator lights, magic circles, etc.)
// IMPORTANT: Emissive colors are added directly to lighting, unaffected by shadows
if (hit.mat == 2) {
    lighting += vec3(0.1, 0.4, 0.15);  // Fluorescent moss (faint green)
}
if (hit.mat == 3) {
    float pulse = 0.7 + 0.3 * sin(iTime * 2.0);
    lighting += vec3(0.2, 0.6, 1.0) * pulse;  // Blue pulse light
}

col = matCol * lighting;
```### 变体 9：体素角色动画
使用时间驱动的偏移和旋转的简单体素角色动画。```glsl
// IMPORTANT: Voxel character animation core approach:
// 1. Split the character into multiple body parts (head, torso, left arm, right arm, left leg, right leg)
// 2. Each part is an sdBox with independent offset/rotation parameters
// 3. iTime drives limb swinging (sin/cos periodic motion)
// 4. Combine all parts using SDF min()
// IMPORTANT: SwiftShader performance critical: character function is called at every DDA step!
//    Must add AABB bounding box check in getVoxel: first check if c is near the character,
//    skip sdBox calculations for that character if not nearby. Otherwise frame timeout → black screen
//    Reduce MAX_RAY_STEPS to 64, MAX_SHADOW_STEPS to 16

int getCharacter(vec3 p, vec3 charPos, float animPhase) {
    vec3 lp = p - charPos;
    float limbSwing = sin(iTime * 4.0 + animPhase) * 0.5;

    // Torso
    float body = sdBox(lp - vec3(0, 3, 0), vec3(1.5, 2.0, 1.0));
    // Head
    float head = sdBox(lp - vec3(0, 6, 0), vec3(1.2, 1.2, 1.2));

    // Arm swing (offset y coordinate around shoulder joint to simulate rotation)
    vec3 armOffset = vec3(0, limbSwing * 2.0, limbSwing);
    float leftArm = sdBox(lp - vec3(-2.5, 3, 0) - armOffset, vec3(0.5, 2.0, 0.5));
    float rightArm = sdBox(lp - vec3(2.5, 3, 0) + armOffset, vec3(0.5, 2.0, 0.5));

    // Alternating leg swing
    vec3 legOffset = vec3(0, 0, limbSwing * 1.5);
    float leftLeg = sdBox(lp - vec3(-0.7, 0, 0) - legOffset, vec3(0.5, 1.5, 0.5));
    float rightLeg = sdBox(lp - vec3(0.7, 0, 0) + legOffset, vec3(0.5, 1.5, 0.5));

    float d = min(body, min(head, min(leftArm, min(rightArm, min(leftLeg, rightLeg)))));
    if (d < 0.0) {
        if (head < 0.0) return 10;  // Head (skin color)
        if (leftArm < 0.0 || rightArm < 0.0) return 11;  // Arms
        return 12;  // Torso/legs
    }
    return 0;
}

// Combine scene + characters in getVoxel
// IMPORTANT: Must add AABB bounding box early exit! Character sdBox calculations are expensive
int getVoxel(vec3 c) {
    // Scene (floor, walls, etc.)
    int scene = getSceneVoxel(c);
    if (scene > 0) return scene;
    // IMPORTANT: AABB check: only call getCharacter near the character
    // Character 1: warrior (at position (5,0,0)), bounding box ±5 cells
    if (abs(c.x - 5.0) < 5.0 && c.y >= 0.0 && c.y < 10.0 && abs(c.z) < 5.0) {
        int char1 = getCharacter(c, vec3(5, 0, 0), 0.0);
        if (char1 > 0) return char1;
    }
    // Character 2: mage (at position (-5,0,3)), bounding box ±5 cells
    if (abs(c.x + 5.0) < 5.0 && c.y >= 0.0 && c.y < 10.0 && abs(c.z - 3.0) < 5.0) {
        int char2 = getCharacter(c, vec3(-5, 0, 3), 3.14);
        if (char2 > 0) return char2;
    }
    return 0;
}
```### 变体 10：瀑布/流水粒子效果
动态瀑布、飞溅粒子、水雾效果。核心：时间偏移噪声模拟水流，散列粒子模拟飞溅，指数衰减模拟雾气。```glsl
// IMPORTANT: Key points for waterfall/flowing water/particle effects:
// 1. Waterfall stream: noise + iTime vertical offset simulates water column flowing down
// 2. Splash particles: hash-distributed voxels at the bottom, positions change with iTime to simulate splashing
// 3. Water mist: semi-transparent accumulation (reduced alpha) or density field at the bottom simulates mist diffusion
// 4. Waterfall must have a clear high point (cliff/rock wall) and low point (pool), drop ≥ 10 cells
// 5. Water stream material uses light blue-white + brightness flicker to simulate flowing water feel

float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

int getVoxel(vec3 c) {
    // Cliff rock walls (both sides + back)
    if (c.x < -5.0 || c.x > 5.0) {
        if (c.y < 15.0 && c.z > -3.0 && c.z < 3.0) return 1;  // Rock
    }
    if (c.z > 2.0 && c.y < 15.0 && abs(c.x) < 6.0) return 1;  // Back wall

    // Cliff top platform
    if (c.y >= 13.0 && c.y < 15.0 && c.z > -1.0 && c.z < 3.0 && abs(c.x) < 5.0) return 1;

    // Bottom pool floor
    if (c.y < -2.0 && abs(c.x) < 8.0 && c.z > -6.0 && c.z < 3.0) return 2;  // Pool bottom

    // IMPORTANT: Waterfall stream: narrow band x ∈ [-2, 2], falling from y=13 to y=0
    //    Use iTime offset on y-coordinate noise to simulate downward water flow
    if (abs(c.x) < 2.0 && c.y >= 0.0 && c.y < 13.0 && c.z > -1.0 && c.z < 1.0) {
        float flowNoise = hash21(vec2(floor(c.x), floor(c.y - iTime * 8.0)));
        if (flowNoise > 0.25) return 3;  // Water (gaps simulate translucent water curtain)
    }

    // IMPORTANT: Splash particles: bottom y ∈ [-1, 3], x ∈ [-4, 4]
    //    Use hash + iTime to generate randomly bouncing voxel particles
    if (c.y >= -1.0 && c.y < 3.0 && abs(c.x) < 4.0 && c.z > -3.0 && c.z < 2.0) {
        float t = iTime * 3.0;
        float particleHash = hash21(vec2(floor(c.x * 2.0), floor(c.z * 2.0) + floor(t)));
        float yOffset = fract(t + particleHash) * 3.0;  // Particle upward trajectory
        if (abs(c.y - yOffset) < 0.6 && particleHash > 0.7) return 4;  // Splash particle
    }

    // IMPORTANT: Water mist: bottom y ∈ [-1, 2], wider range than splashes
    //    Density decreases with height and distance from waterfall center
    if (c.y >= -1.0 && c.y < 2.0 && abs(c.x) < 6.0 && c.z > -5.0 && c.z < 3.0) {
        float distFromCenter = length(vec2(c.x, c.z));
        float mistDensity = exp(-0.15 * distFromCenter) * exp(-0.5 * max(c.y, 0.0));
        float mistNoise = hash21(vec2(floor(c.x * 0.5 + iTime * 0.5), floor(c.z * 0.5)));
        if (mistNoise < mistDensity * 0.8) return 5;  // Water mist
    }

    return 0;
}

// Material colors
vec3 getMaterialColor(int mat, vec2 uv) {
    if (mat == 1) return vec3(0.45, 0.4, 0.35);    // Rock
    if (mat == 2) return vec3(0.35, 0.3, 0.25);    // Pool bottom
    if (mat == 3) {                                  // Water stream (shimmering blue-white)
        float shimmer = 0.8 + 0.2 * sin(uv.y * 20.0 + iTime * 10.0);
        return vec3(0.6, 0.8, 1.0) * shimmer;
    }
    if (mat == 4) return vec3(0.85, 0.92, 1.0);    // Splash (bright white)
    if (mat == 5) return vec3(0.7, 0.82, 0.9);     // Water mist (pale blue-white)
    return vec3(0.5);
}

// IMPORTANT: Water mist material needs special lighting: high emissive + translucent feel
// During shading:
if (hit.mat == 5) {
    lighting += vec3(0.4, 0.5, 0.6);  // Water mist emissive (unaffected by shadows)
}

// Camera: side angle slightly elevated, showing the full waterfall (top to bottom + bottom splashes and mist)
// ro = vec3(12.0, 10.0, -10.0), lookAt = vec3(0.0, 6.0, 0.0)
```### 变体 11：多建筑/城镇/Minecraft 风格的场景（多结构城镇组合）
城镇、村庄、Minecraft 风格的世界以及其他需要在地面上放置多个离散结构（房屋、树木、灯柱等）的场景。
**重要提示：“类似 Minecraft 的体素场景”= 多建筑场景；必须遵循此模板的性能限制！**```glsl
// IMPORTANT: Key points for multi-building scenes:
// 1. Define the ground first (height map or flat plane), ensure ground getVoxel returns correct material
// 2. Each building uses an independent helper function, receiving local coordinates, returning material ID
// 3. In getVoxel, check each building sequentially (using offset coordinates), return on first hit
// 4. Camera must be outside the scene facing the center, far enough to see the full view
// 5. IMPORTANT: Building coordinate ranges must be within DDA traversal range (MAX_RAY_STEPS * cell ≈ reachable distance)
// 6. IMPORTANT: Scene range should not be too large! Concentrate all buildings within -20~20 range, camera 30-50 cells away
// 7. IMPORTANT: SwiftShader performance critical: getVoxel must have AABB bounding box early exit!
//    Above ground (c.y > 0), check AABB range first; return 0 immediately if outside building area
//    Otherwise every DDA step checks all buildings → frame timeout → black screen / only sky renders
// 8. IMPORTANT: MAX_RAY_STEPS reduced to 64, MAX_SHADOW_STEPS to 16 (complex getVoxel requires lower step counts)

// Single house: width w, depth d, height h, with triangular roof
int makeHouse(vec3 p, float w, float d, float h, int wallMat, int roofMat) {
    // Walls
    if (p.x >= 0.0 && p.x < w && p.z >= 0.0 && p.z < d && p.y >= 0.0 && p.y < h) {
        return wallMat;
    }
    // Triangular roof: starts from wall top, x range narrows by 1 per level
    float roofY = p.y - h;
    float roofInset = roofY;  // Inset by 1 cell per level
    if (roofY >= 0.0 && roofY < w * 0.5
        && p.x >= roofInset && p.x < w - roofInset
        && p.z >= 0.0 && p.z < d) {
        return roofMat;
    }
    return 0;
}

// Tree: trunk + spherical canopy
int makeTree(vec3 p, float trunkH, float crownR, int trunkMat, int leafMat) {
    // Trunk (1x1 column)
    if (p.x >= -0.5 && p.x < 0.5 && p.z >= -0.5 && p.z < 0.5
        && p.y >= 0.0 && p.y < trunkH) {
        return trunkMat;
    }
    // Spherical canopy
    vec3 crownCenter = vec3(0.0, trunkH + crownR * 0.5, 0.0);
    if (length(p - crownCenter) < crownR) {
        return leafMat;
    }
    return 0;
}

// Lamppost: thin pole + glowing top block
int makeLamp(vec3 p, float h, int poleMat, int lightMat) {
    if (p.x >= -0.3 && p.x < 0.3 && p.z >= -0.3 && p.z < 0.3
        && p.y >= 0.0 && p.y < h) {
        return poleMat;  // Pole
    }
    if (p.x >= -0.5 && p.x < 0.5 && p.z >= -0.5 && p.z < 0.5
        && p.y >= h && p.y < h + 1.0) {
        return lightMat;  // Lamp head (emissive)
    }
    return 0;
}

int getVoxel(vec3 c) {
    // 1. Ground (y < 0 is underground, y == 0 layer is surface)
    if (c.y < -1.0) return 0;
    if (c.y < 0.0) return 1;  // Ground (dirt/grass)

    // 2. Road (along z direction, x range -2~2)
    if (c.y < 1.0 && abs(c.x) < 2.0) return 2;  // Road surface

    // IMPORTANT: AABB bounding box early exit (required for SwiftShader!)
    // All buildings are within x:-15~15, y:0~12, z:-5~15
    // Return 0 immediately outside this range, avoiding per-building checks
    if (c.x < -15.0 || c.x > 15.0 || c.y > 12.0 || c.z < -5.0 || c.z > 15.0) return 0;

    // 3. Place buildings (each with offset coordinates)
    // IMPORTANT: House width/height must be ≥ 5 cells, otherwise they look like dots from far away! Use bright material colors
    int m;

    // House A: position (5, 0, 3), width 6, depth 5, height 5
    m = makeHouse(c - vec3(5.0, 0.0, 3.0), 6.0, 5.0, 5.0, 3, 4);
    if (m > 0) return m;

    // House B: position (-10, 0, 2), width 7, depth 5, height 5
    m = makeHouse(c - vec3(-10.0, 0.0, 2.0), 7.0, 5.0, 5.0, 5, 4);
    if (m > 0) return m;

    // Tree: position (0, 0, 8)
    m = makeTree(c - vec3(0.0, 0.0, 8.0), 4.0, 2.5, 6, 7);
    if (m > 0) return m;

    // Lamppost: position (3, 0, 0)
    m = makeLamp(c - vec3(3.0, 0.0, 0.0), 5.0, 8, 9);
    if (m > 0) return m;

    return 0;
}

// IMPORTANT: Camera setup: must be far enough to overlook the entire town
// Recommended: ro = vec3(0, 15, -35), looking at scene center vec3(0, 3, 5)
vec3 ro = vec3(0.0, 15.0, -35.0);
vec3 lookAt = vec3(0.0, 3.0, 5.0);
vec3 forward = normalize(lookAt - ro);
vec3 right = normalize(cross(forward, vec3(0, 1, 0)));
vec3 up = cross(right, forward);
vec3 rd = normalize(forward * 0.8 + right * screenPos.x + up * screenPos.y);

// IMPORTANT: Sunset/side-lit scene key: when light comes from the side or at low angle, building fronts may be completely backlit turning into black silhouettes!
// Must satisfy all: (1) ambient light ≥ 0.3 (prevent backlit faces from going black); (2) house walls use bright materials (e.g., light yellow 0.85,0.75,0.55)
// (3) house dimensions must not be too small (width/height ≥ 5 cells), otherwise they look like dots from far away
vec3 sunDir = normalize(vec3(-0.8, 0.3, 0.5));  // Sunset low angle
vec3 sunColor = vec3(1.0, 0.6, 0.3);  // Warm orange
vec3 ambientColor = vec3(0.35, 0.3, 0.4);  // IMPORTANT: High ambient light (≥0.3) to prevent silhouettes
// lighting = ambientColor + diff * sunColor * shadow;
```## 表演与作曲

**性能提示：**
- 提前退出：当“mapPos”超出场景边界时立即中断
- 16-24 的阴影射线步长就足够了
- 在开放区域使用大台阶的 SDF 球体追踪，在表面附近切换到 DDA
- 材质查询、AO、法线等仅在命中后计算
- 用“texelFetch”纹理采样替换程序体素查询
- 多帧累积+重投影以获得低噪声结果
- **重要提示：MAX_RAY_STEPS 默认为 64，MAX_SHADOW_STEPS 默认为 16（总共 80）**。只有简单的场景（单个立方体/球体）才能增加到96+24。具有复杂 getVoxel 的多建筑/Minecraft/角色场景必须保持 64+16 或更低，否则 SwiftShader 帧超时→仅渲染天空背景

**构图技巧：**
- **程序噪声地形**：在 `getVoxel()` 中使用 FBM/Perlin 噪声高度图
- **SDF 程序建模**：在 `getVoxel()` 中使用 SDF 布尔运算来定义形状
- **纹理映射**：命中后，使用面部 UV * 16 采样 16x16 像素纹理
- **大气散射/体积雾**：DDA遍历期间累积介质密度
- **水面渲染**：特定 Y 平面上的菲涅耳反射/折射（参见上面的变体 6）
- **全局照明**：圆锥跟踪或蒙特卡罗半球采样
- **时间重投影**：多帧累积+前一帧重投影以实现抗锯齿和去噪

## 常见错误

1. **导致编译失败的GLSL保留字**：`cast`、`class`、`template`、`namespace`、`input`、`output`、`filter`、`image`、`sampler`、`half`、`fixed`等都是GLSL保留字，**绝对不能用作变量或函数名**。使用复合名称：“castRay”、“castShadow”、“shootRay”、“spellEffect”（不是“cast”）
2. **封闭/半封闭场景全黑**：洞穴、室内、科幻基地、迷宫等封闭场景不能仅依靠定向光（被墙壁/天花板完全遮挡）；必须使用点光源 + 高环境光 (≥0.2) + 发光材料（参见变体 8）
3. **摄像机位于体素内部导致渲染异常**：洞穴/室内场景摄像机原点必须位于腔体内部（其中 getVoxel 返回 0），否则第一个 DDA 步骤立即命中 = 场景不可见
4. **复杂的 getVoxel 导致 SwiftShader 黑屏（最常见于 Minecraft 风格/城镇/角色/多建筑场景！）**：每个 DDA 步骤都会调用 getVoxel 一次；如果它包含多个建筑物/角色/地形+树木而没有提前退出，则帧超时→仅渲染天空背景。 **必须完成所有**：（1）提前退出AABB边界框（先检查坐标范围，在建筑区域外立即返回0）； (2) MAX_RAY_STEPS ≤ 64，MAX_SHADOW_STEPS ≤ 16； (3)场景范围±20个单元格内。 **Minecraft风格的场景=多建筑场景**；必须遵循此规则（请参阅变体 9、11 模板代码）
5. **vec2/vec3 维度不匹配导致编译失败**：`p.xz` 返回 `vec2`，并且不能直接传递给需要 `vec3` 参数的噪声/fbm 函数或在使用 `vec3` 的操作中使用。使用 `vec3(p.xz, val)` 构造完整的 vec3，或使用 vec2 版本的函数
6. **山/地形基于高度的着色不可见**： (1) `maxH`必须等于地形噪声函数的实际最大返回值（不要随意使用20.0）； （2）草地阈值0.4（最大面积保证绿色可见），岩石0.4~0.7，雪>0.7； (3)草绿色必须足够饱和 `vec3(0.25, 0.55, 0.15)` 不能偏灰； (4) 太阳光强度≤2.0，天空光≤1.0，太亮洗掉颜色； （5）伽马校正降低饱和度，预补偿材质颜色（参见步骤4山地地形模板）
7. **瀑布/流水效果缺乏可识别性**：瀑布必须有明显的悬崖落差（≥10个单元）、可见的水柱（噪声+iTime偏移）、底部飞溅粒子（哈希随机弹跳）、雾气（指数衰减密度场）。只是渐变色块不是瀑布！请参阅变体 10 完整模板
8. **“低饱和度着色”变成纯白/灰色**：低饱和度≠近白！低饱和度意味着颜色不鲜艳，但仍具有清晰的色调（例如，砖红色 `vec3(0.55, 0.35, 0.3)` 而不是灰白色 `vec3(0.8, 0.8, 0.8)`）。砖/石纹理必须使用UV周期性图案（交错行+砂浆暗线），而不是纯色。请参阅完整模板中的“getBrickColor”函数9. **日落/侧光场景建筑物变成黑色剪影**：当低角度光（日落/黎明）从侧面照射时，建筑物正面完全背光→纯黑色剪影，没有可见细节。必须：（1）环境光≥0.3； （2）墙壁采用亮色材料（浅黄色、灰白色）而不是深色； (3) 建筑物足够大（宽/高≥5格）。请参阅变体 11 日落场景代码

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/voxel-rendering.md)