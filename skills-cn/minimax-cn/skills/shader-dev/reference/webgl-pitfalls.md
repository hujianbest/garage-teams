# WebGL2 陷阱参考

这是 [webgl-pitfalls](../techniques/webgl-pitfalls.md) 技术的参考文档。

## 完整错误消息参考

|错误信息 |可能的原因 |解决方案 |
|---|---|---|
| `'fragCoord'：未声明的标识符` |在 WebGL2 中使用 `fragCoord` 代替 `gl_FragCoord.xy` |替换为 `gl_FragCoord.xy` |
| `'' : 缺少 main()` |片段着色器没有 `main()` 函数 |添加 `void main() { mainImage(fragColor, gl_FragCoord.xy); }` 包装 |
| `'functionName'：找不到匹配的重载函数` |使用后声明的参数类型或函数错误 |检查类型；重新排序或前向声明函数 |
| `'return' : 函数返回与类型不匹配：` |返回表达式类型与声明的返回类型不匹配 |验证 `vec3 foo()` 返回 `vec3`，而不是 `float` |
| `#version` 必须是第一个 |从脚本标记中提取时的前导空格 |在着色器源字符串上使用 `.trim()`
| Uniform 从 `getUniformLocation` 返回 `null` |制服因未使用而被优化|确保在着色器代码中实际引用了uniform |

## 类型不匹配示例```glsl
// ERROR: terrainM expects vec2, passing vec3
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos + h * nor);  // Wrong: pos + h*nor is vec3
}
// FIX: Extract xz components
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos.xz + h * nor.xz);  // Correct: vec2
}
```

```glsl
// ERROR: can't access .z on vec2
vec2 uv = vec2(1.0, 2.0);
float z = uv.z;  // Wrong: vec2 has no .z
// FIX: use proper swizzle or conversion
float z = uv.y;  // Or if you need third component, use vec3
```## GLSL ES 3.0 具体说明

- 所有声明的“uniform”变量必须在着色器代码中使用，否则编译器可能会优化它们
- 当 `gl.getUniformLocation()` 返回 `null` 时，设置统一触发 `INVALID_OPERATION`
- 循环计数器在运行时必须是确定性的——避免编译时常量折叠问题