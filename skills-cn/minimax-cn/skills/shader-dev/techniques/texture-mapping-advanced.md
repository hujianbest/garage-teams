# 高级纹理映射技术

## 用例
- 无 UV 接缝的 3D 表面纹理化（三平面/双平面映射）
- 消除大表面上可见的重复瓷砖
- 光线行进场景中的正确纹理过滤（Mip 级别选择）
- 结合程序纹理和采样纹理

## 技巧

### 1. 双平面映射（优化的三平面）

仅使用 2 次纹理获取而不是 3 次，选择两个最相关的投影轴：```glsl
vec4 biplanar(sampler2D sam, vec3 p, vec3 n, float k) {
    vec3 dpdx = dFdx(p);
    vec3 dpdy = dFdy(p);
    n = abs(n);

    // Determine major, minor, median axes
    ivec3 ma = (n.x > n.y && n.x > n.z) ? ivec3(0,1,2) :
               (n.y > n.z)              ? ivec3(1,2,0) : ivec3(2,0,1);
    ivec3 mi = (n.x < n.y && n.x < n.z) ? ivec3(0,1,2) :
               (n.y < n.z)              ? ivec3(1,2,0) : ivec3(2,0,1);
    ivec3 me = ivec3(3) - mi - ma;

    // Two texture fetches (major and median projections)
    vec4 x = textureGrad(sam, vec2(p[ma.y], p[ma.z]),
                         vec2(dpdx[ma.y], dpdx[ma.z]),
                         vec2(dpdy[ma.y], dpdy[ma.z]));
    vec4 y = textureGrad(sam, vec2(p[me.y], p[me.z]),
                         vec2(dpdx[me.y], dpdx[me.z]),
                         vec2(dpdy[me.y], dpdy[me.z]));

    // Blend weights with local support
    vec2 w = vec2(n[ma.x], n[me.x]);
    w = clamp((w - 0.5773) / (1.0 - 0.5773), 0.0, 1.0);  // 0.5773 = 1/sqrt(3)
    w = pow(w, vec2(k / 8.0));

    return (x * w.x + y * w.y) / (w.x + w.y);
}
// Usage: vec4 col = biplanar(tex, worldPos * scale, worldNormal, 8.0);
```**为什么是双平面而不是三平面**：节省一次纹理获取（带宽限制优势），k=8 视觉上相当于三平面。 “dFdx/dFdy”梯度传播可防止轴切换边界处的 mipmap 接缝。

### 2.避免纹理重复

消除可见平铺图案的三种方法：

#### 方法 A：每图块随机偏移（4 次获取）```glsl
vec4 textureNoTile(sampler2D sam, vec2 uv) {
    vec2 iuv = floor(uv);
    vec2 fuv = fract(uv);

    // Generate 4 random offsets for the 4 surrounding tiles
    vec4 ofa = hash42(iuv + vec2(0, 0));
    vec4 ofb = hash42(iuv + vec2(1, 0));
    vec4 ofc = hash42(iuv + vec2(0, 1));
    vec4 ofd = hash42(iuv + vec2(1, 1));

    // Transform UVs per tile
    vec2 uva = uv + ofa.xy;
    vec2 uvb = uv + ofb.xy;
    vec2 uvc = uv + ofc.xy;
    vec2 uvd = uv + ofd.xy;

    // Blend near borders with smooth weights
    vec2 b = smoothstep(0.25, 0.75, fuv);
    return mix(mix(texture(sam, uva), texture(sam, uvb), b.x),
               mix(texture(sam, uvc), texture(sam, uvd), b.x), b.y);
}
```#### 方法 B：虚拟模式（2 次获取，最便宜）```glsl
vec4 textureNoTileCheap(sampler2D sam, vec2 uv) {
    float k = texture(iChannel1, 0.005 * uv).x;  // low-freq variation index
    float index = k * 8.0;
    float i = floor(index);
    float f = fract(index);

    // Two offset lookups based on index
    vec2 offa = sin(vec2(3.0, 7.0) * (i + 0.0));
    vec2 offb = sin(vec2(3.0, 7.0) * (i + 1.0));

    return mix(texture(sam, uv + offa), texture(sam, uv + offb), smoothstep(0.2, 0.8, f));
}
```### 3.光线差分纹理过滤

对于光线行进的场景，使用光线微分计算适当的 mip 级别：```glsl
// After finding hit point pos with normal nor:
// 1. Compute neighbor pixel ray directions
vec3 rdx = normalize(rd + dFdx(rd));  // x-neighbor ray
vec3 rdy = normalize(rd + dFdy(rd));  // y-neighbor ray

// 2. Intersect neighbors with tangent plane at hit point
float dt_dx = -dot(pos - ro, nor) / dot(rdx, nor);
float dt_dy = -dot(pos - ro, nor) / dot(rdy, nor);
vec3 posDx = ro + rdx * dt_dx;
vec3 posDy = ro + rdy * dt_dy;

// 3. World-space position derivatives = pixel footprint
vec3 dposdx = posDx - pos;
vec3 dposdy = posDy - pos;

// 4. Transform to texture derivatives and use textureGrad
// For simple planar mapping (e.g. ground plane):
vec2 duvdx = dposdx.xz * textureScale;
vec2 duvdy = dposdy.xz * textureScale;
vec4 color = textureGrad(tex, pos.xz * textureScale, duvdx, duvdy);
```这为光线行进表面上的程序和采样纹理提供了正确的 Mip 级别选择，消除了远处的闪烁和锯齿。

→ 更深入的细节请参见 [reference/texture-mapping-advanced.md](../reference/texture-mapping-advanced.md)