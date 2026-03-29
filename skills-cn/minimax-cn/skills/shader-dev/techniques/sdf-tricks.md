# SDF 高级技巧和优化

## 用例
- 优化复杂的 SDF 场景以实现实时性能
- 在不增加几何复杂性的情况下向 SDF 表面添加精细细节
- 通过 SDF 操作创建特殊效果（空心、分层边缘、内部结构）
- 调试和可视化 SDF 字段

## 核心技术

### 空心（外壳创建）
将任何固体 SDF 转换为薄壳：```glsl
float hollowed = abs(sdf) - thickness;
// Example: hollow sphere with 0.02 wall thickness
float d = abs(sdSphere(p, 1.0)) - 0.02;
```### 分层边缘（同心轮廓线）
从任何 SDF 创建等距轮廓环：```glsl
float spacing = 0.2;
float thickness = 0.02;
float layered = abs(mod(d + spacing * 0.5, spacing) - spacing * 0.5) - thickness;
```Useful for: topographic map effects, neon outlines, energy shields, wireframe-like rendering.

### SDF（基于距离的 LOD）的 FBM 详细信息
仅在可见的地方（靠近相机）添加程序噪点细节：```glsl
float map(vec3 p) {
    float d = sdBasicShape(p);
    // Only add expensive FBM detail when close to surface
    if (d < 1.0) {
        d += 0.02 * fbm(p * 8.0) * smoothstep(1.0, 0.0, d);
    }
    return d;
}
```**关键**：“平滑步”淡出可防止 FBM 破坏远离表面的 SDF 的 Lipschitz 连续性，这会导致光线行进超调。

### SDF 包围体（性能优化）
当点远离物体时，跳过昂贵的 SDF 评估：```glsl
float map(vec3 p) {
    // Cheap bounding sphere test first
    float bound = sdSphere(p - objectCenter, boundingRadius);
    if (bound > 0.1) return bound;  // far away — return bounding distance
    // Expensive detailed SDF only when close
    return complexSDF(p);
}
```对于具有多个远处物体的场景，这可以提供 5-10 倍的加速。

### 二分搜索细化
光线行进找到近似命中后，通过二分搜索进行亚像素精度优化：```glsl
// After ray march loop finds t where map(ro+rd*t) < epsilon:
for (int i = 0; i < 6; i++) {
    float mid = map(ro + rd * t);
    t += mid * 0.5;  // or use proper bisection:
    // float dt = step * 0.5^i;
    // t += (map(ro+rd*t) > 0.0) ? dt : -dt;
}
```特别适用于：锐利边缘渲染、精确阴影终止、精确反射点。

### 异或布尔运算
通过将 SDF 与 XOR 结合起来创建有趣的几何图案：```glsl
float opXor(float d1, float d2) {
    return max(min(d1, d2), -max(d1, d2));
}
// Creates a "difference of unions" — geometry exists where exactly one shape is present
```### SDF 内部结构
使用 SDF 的符号创建内部几何体：```glsl
float interiorPattern(vec3 p) {
    float outer = sdSphere(p, 1.0);
    float inner = sdBox(fract(p * 4.0) - 0.5, vec3(0.1)); // repeating inner pattern
    return (outer < 0.0) ? max(outer, inner) : outer;      // inner visible only inside
}
```## SDF 调试可视化```glsl
// Visualize SDF distance as color bands
vec3 debugSDF(float d) {
    vec3 col = (d > 0.0) ? vec3(0.9, 0.6, 0.3) : vec3(0.4, 0.7, 0.85);  // outside/inside
    col *= 1.0 - exp(-6.0 * abs(d));                    // darken near surface
    col *= 0.8 + 0.2 * cos(150.0 * d);                  // distance bands
    col = mix(col, vec3(1.0), 1.0 - smoothstep(0.0, 0.01, abs(d)));  // white at surface
    return col;
}
```→ 更深入的细节请参见 [reference/sdf-tricks.md](../reference/sdf-tricks.md)