# SDF技巧详细参考

## 先决条件
- 了解有符号距离场和射线行进
- 基本 SDF 原语和布尔运算
- FBM/程序噪声基础知识

## Lipschitz 条件和 FBM 详细信息

SDF 必须满足 **Lipschitz 条件**：`|f(a) - f(b)| ≤ |a - b|`（梯度大小 ≤ 1）。这保证了按 SDF 值步进始终是安全的——该半径内不存在表面。

将 FBM 噪声添加到 SDF 时，噪声导数可能会违反 Lipschitz：
- 频率为 20 的原始噪声幅度为 0.1，梯度为 ~2.0，打破了条件
- 这会导致光线行进过度，产生孔洞和伪影

**解决方案**：
1. **幅度限制**：在所有八度音阶上保持“幅度×频率 < 1.0”
2. **距离淡入淡出**：`d += amp * fbm(p * freq) * smoothstep(fadeStart, 0.0, d)` — 细节仅出现在超调距离较小的表面附近
3. **步长减小**：将射线步长乘以0.5-0.7，交易速度稳定

## 包围体策略

### 分层边界
对于具有 N 个对象的场景，按成本递增的顺序测试包围体：```
Level 1: Scene bounding sphere (1 evaluation)
Level 2: Object group bounds (few evaluations)
Level 3: Individual object SDF (full cost)
```### 空间分区
对于重复结构，将域重复与边界结合起来：```glsl
float map(vec3 p) {
    vec3 q = mod(p + 2.0, 4.0) - 2.0;  // repeat every 4 units
    // Only evaluate detail if within local bounding sphere
    float bound = length(q) - 1.5;
    if (bound > 0.2) return bound;
    return detailedSDF(q);
}
```## 二分查找收敛

经过 N 次二分查找迭代后，位置误差为 `initialStep / 2^N`：
- 4 次迭代：初始步长的 1/16
- 6 次迭代：初始步长的 1/64（典型分辨率下的子像素）
- 8 次迭代：1/256（对于大多数用途来说太过分了）

6 次迭代是实际的最佳点 - 提供子像素精度而不浪费 GPU 周期。

## 异或运算数学

`opXor(a, b) = max(min(a, b), -max(a, b))`

这相当于：“union(a, b) AND NOT junction(a, b)”——对称差。几何存在于只存在一种形状但不存在两种形状的地方。对于创建晶格结构和互锁图案很有用。

## 室内 SDF 图案技术

当相机位于 SDF (d < 0) 内部时，负距离仍然提供有用的信息：
- `abs(d)` 给出从内部到最近表面的距离
- 使用“fract()”结合重复图案来创建无限的内部结构
- 使用“max(outerSDF,innerSDF)”将内部图案限制在外壳内