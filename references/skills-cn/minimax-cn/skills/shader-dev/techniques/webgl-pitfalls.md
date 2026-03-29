# WebGL2 陷阱和常见错误

## 用例

- 生成独立的 WebGL2 着色器页面时避免常见的 GLSL 编译错误
- 调试着色器编译失败
- 确保 ShaderToy 的着色器模板在 WebGL2 中正常工作

## 关键的 WebGL2 规则

### 1. 片段坐标 — 使用 `gl_FragCoord.xy`

**错误**：`'fragCoord'：未声明的标识符`

在 WebGL2 片段着色器中，“fragCoord”不是内置变量。请改用“gl_FragCoord.xy”。```glsl
// WRONG
void main() {
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;
}

// CORRECT
void main() {
    vec2 uv = (2.0 * gl_FragCoord.xy - iResolution.xy) / iResolution.y;
}
```### 2. Shadertoy mainImage — 必须包裹在 `main()` 中

**错误**：`''：缺少 main()`

如果您的片段着色器使用“void mainImage(out vec4, in vec2)”，则必须提供“main()”包装器。```glsl
// WRONG — only defines mainImage but no main()
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // shader code...
    fragColor = vec4(col, 1.0);
}

// CORRECT
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // shader code...
    fragColor = vec4(col, 1.0);
}

void main() {
    mainImage(fragColor, gl_FragCoord.xy);
}
```### 3. 函数声明顺序——使用前声明

**错误**：`'functionName'：找不到匹配的重载函数`

GLSL 要求在使用函数之前先对其进行声明。需要前向声明或重新排序。```glsl
// WRONG — getAtmosphere() calls getSunDirection() which is defined after
vec3 getAtmosphere(vec3 dir) {
    return extra_cheap_atmosphere(dir, getSunDirection()) * 0.5;  // Error!
}
vec3 getSunDirection() {
    return normalize(vec3(-0.5, 0.8, -0.6));
}

// CORRECT — reorder functions
vec3 getSunDirection() {  // Define first
    return normalize(vec3(-0.5, 0.8, -0.6));
}
vec3 getAtmosphere(vec3 dir) {  // Now can call getSunDirection()
    return extra_cheap_atmosphere(dir, getSunDirection()) * 0.5;
}
```### 4. 宏限制 — `#define` 不能使用函数

**错误**：“#define”宏的各种编译错误

宏是文本替换，不能像C++那样调用函数或使用括号。```glsl
// WRONG
#define SUN_DIR normalize(vec3(0.8, 0.4, -0.6))
#define WORLD_TIME (iTime * speed())

// CORRECT — use const
const vec3 SUN_DIR = vec3(0.756, 0.378, -0.567);  // Pre-computed normalized value
const float WORLD_TIME = 1.0;
```### 5.矢量分量访问——地形函数

**错误**：“‘terrainM’：找不到匹配的重载函数”

将位置传递给需要“vec2”的地形函数时，请正确提取 XZ 分量。```glsl
// WRONG — terrainM expects vec2, but passing vec3
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos + h * nor);  // Error: pos + h*nor is vec3
    ...
}

// CORRECT — extract xz components
float calcAO(vec3 pos, vec3 nor) {
    float d = terrainM(pos.xz + h * nor.xz);
    ...
}
```### 6. 循环索引 — 使用运行时常量

**错误**：循环索引必须是运行时表达式

GLSL ES 要求循环索引在运行时可确定，而不是某些上下文中的编译时常量。```glsl
// WRONG — AA is a #define constant
for (int i = 0; i < AA; i++) { ... }

// CORRECT — use a runtime-safe approach
for (int i = 0; i < 4; i++) { ... }  // Or pass as uniform
```### 7. 制服使用——避免未使用的制服

**错误**：统一优化导致 `gl.getUniformLocation()` 返回 `null`

如果声明了统一但未使用，编译器可能会对其进行优化。```glsl
// WRONG — iTime declared but used in a conditional that might be false
uniform float iTime;
if (false) { x = iTime; }  // iTime optimized away

// CORRECT — always use the uniform in a way the compiler can't optimize out
uniform float iTime;
float t = iTime * 0.0;  // Always use iTime somehow
if (someCondition) { x = t; }
```## 完整的 WebGL2 适配清单

生成独立 HTML 页面时：

1. **Shader Version**：`#version 300 es`必须是第一行
2. **片段输出**：声明 `out vec4 fragColor;`
3. **入口点**：将`mainImage()`包装在`void main()`中，调用`mainImage(fragColor, gl_FragCoord.xy)`
4. **片段坐标**：使用`gl_FragCoord.xy`而不是`fragCoord`
5. **预处理器**：不要在`#define`宏中使用函数
6. **函数顺序**：在使用函数之前声明函数，或者使用前向声明
7. **纹理**：使用`texture()`而不是`texture2D()`
8. **属性**：`属性`→`in`、`variing`→`in`/`out`

## 常见错误信息参考

|错误信息 |可能的原因 |解决方案 |
|---|---|---|
| `'fragCoord'：未声明的标识符` |使用 `fragCoord` 而不是 `gl_FragCoord.xy` |替换为 `gl_FragCoord.xy` |
| `'' : 缺少 main()` |没有定义`main()`函数|添加包装器 `void main() { mainImage(...); }` |
| `'function'：没有匹配的重载函数` |错误的参数类型或函数顺序 |检查参数类型，重新排序函数 |
| `return' : 函数返回不匹配` |返回类型不匹配 |验证返回表达式与声明的返回类型匹配 |
| `#version` 必须是第一个 |着色器源中的前导空白 |从脚本标签中提取时使用 `.trim()` |
|来自“getUniformLocation”的统一“null” |制服优化走了|确保着色器代码中实际使用了uniform |

## 进一步阅读

有关其他调试技术，请参阅 [reference/webgl-pitfalls.md](../reference/webgl-pitfalls.md)。