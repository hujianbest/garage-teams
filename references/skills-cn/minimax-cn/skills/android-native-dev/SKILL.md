---
名称：android-native-dev
描述：Android原生应用程序开发和UI设计指南。涵盖 Material Design 3、Kotlin/Compose 开发、项目配置、可访问性和构建故障排除。在 Android 本机应用程序开发之前阅读本文。
许可证：麻省理工学院
元数据：
  版本：“1.0.0”
  类别： 手机
  来源：
    - Material Design 3 指南 (material.io)
    - Android 开发者文档 (developer.android.com)
    - Google Play 质量指南
    - WCAG 无障碍指南
---

## 1. 项目场景评估

在开始开发之前，评估当前的项目状态：

|场景|特点 |方法|
|----------|-----------------|----------|
| **空目录** |没有文件存在 |需要完整初始化，包括 Gradle Wrapper |
| **有 Gradle 包装器** | `gradlew` 和 `gradle/wrapper/` 存在 |直接使用 `./gradlew` 进行构建 |
| **Android Studio 项目** |完整的项目结构，可能缺少包装器 |检查包装器，如果需要，运行“gradle 包装器” |
| **未完成的项目** |存在部分文件 |检查缺失文件，完成配置 |

**关键原则**：
- 在编写业务逻辑之前，确保`./gradlew assembleDebug`成功
- 如果缺少 `gradle.properties`，请先创建它并配置 AndroidX

### 1.1 所需文件清单```
MyApp/
├── gradle.properties          # Configure AndroidX and other settings
├── settings.gradle.kts
├── build.gradle.kts           # Root level
├── gradle/wrapper/
│   └── gradle-wrapper.properties
├── app/
│   ├── build.gradle.kts       # Module level
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/example/myapp/
│       │   └── MainActivity.kt
│       └── res/
│           ├── values/
│           │   ├── strings.xml
│           │   ├── colors.xml
│           │   └── themes.xml
│           └── mipmap-*/       # App icons
```---

## 2. 项目配置

### 2.1 gradle.properties```properties
# Required configuration
android.useAndroidX=true
android.enableJetifier=true

# Build optimization
org.gradle.parallel=true
kotlin.code.style=official

# JVM memory settings (adjust based on project size)
# Small projects: 2048m, Medium: 4096m, Large: 8192m+
# org.gradle.jvmargs=-Xmx4096m -Dfile.encoding=UTF-8
```> **注意**：如果在构建过程中遇到 `OutOfMemoryError`，请增加 `-Xmx` 值。具有许多依赖项的大型项目可能需要 8GB 或更多。

### 2.2 依赖声明标准```kotlin
dependencies {
    // Use BOM to manage Compose versions
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    
    // Activity & ViewModel
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
}
```### 2.3 构建变体和产品风味

产品风格允许您创建应用程序的不同版本（例如免费/付费、开发/登台/产品）。

**app/build.gradle.kts 中的配置**：```kotlin
android {
    // Define flavor dimensions
    flavorDimensions += "environment"
    
    productFlavors {
        create("dev") {
            dimension = "environment"
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
            
            // Different config values per flavor
            buildConfigField("String", "API_BASE_URL", "\"https://dev-api.example.com\"")
            buildConfigField("Boolean", "ENABLE_LOGGING", "true")
            
            // Different resources
            resValue("string", "app_name", "MyApp Dev")
        }
        
        create("staging") {
            dimension = "environment"
            applicationIdSuffix = ".staging"
            versionNameSuffix = "-staging"
            
            buildConfigField("String", "API_BASE_URL", "\"https://staging-api.example.com\"")
            buildConfigField("Boolean", "ENABLE_LOGGING", "true")
            resValue("string", "app_name", "MyApp Staging")
        }
        
        create("prod") {
            dimension = "environment"
            // No suffix for production
            
            buildConfigField("String", "API_BASE_URL", "\"https://api.example.com\"")
            buildConfigField("Boolean", "ENABLE_LOGGING", "false")
            resValue("string", "app_name", "MyApp")
        }
    }
    
    buildTypes {
        debug {
            isDebuggable = true
            isMinifyEnabled = false
        }
        release {
            isDebuggable = false
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}
```**构建变体命名**：`{flavor}{BuildType}` → 例如，`devDebug`、`prodRelease`

**Gradle 构建命令**：```bash
# List all available build variants
./gradlew tasks --group="build"

# Build specific variant (flavor + buildType)
./gradlew assembleDevDebug        # Dev flavor, Debug build
./gradlew assembleStagingDebug    # Staging flavor, Debug build
./gradlew assembleProdRelease     # Prod flavor, Release build

# Build all variants of a specific flavor
./gradlew assembleDev             # All Dev variants (debug + release)
./gradlew assembleProd            # All Prod variants

# Build all variants of a specific build type
./gradlew assembleDebug           # All flavors, Debug build
./gradlew assembleRelease         # All flavors, Release build

# Install specific variant to device
./gradlew installDevDebug
./gradlew installProdRelease

# Build and install in one command
./gradlew installDevDebug && adb shell am start -n com.example.myapp.dev/.MainActivity
```**在代码中访问BuildConfig**：

> **注意**：从 AGP 8.0 开始，默认情况下不再生成 `BuildConfig`。您必须在“build.gradle.kts”中显式启用它：
>```kotlin
> android {
>     buildFeatures {
>         buildConfig = true
>     }
> }
> ```

```kotlin
// Use build config values in your code
val apiUrl = BuildConfig.API_BASE_URL
val isLoggingEnabled = BuildConfig.ENABLE_LOGGING

if (BuildConfig.DEBUG) {
    // Debug-only code
}
```**特定口味的源集**：```
app/src/
├── main/           # Shared code for all flavors
├── dev/            # Dev-only code and resources
│   ├── java/
│   └── res/
├── staging/        # Staging-only code and resources
├── prod/           # Prod-only code and resources
├── debug/          # Debug build type code
└── release/        # Release build type code
```**多种风味维度**（例如，环境+层级）：```kotlin
android {
    flavorDimensions += listOf("environment", "tier")
    
    productFlavors {
        create("dev") { dimension = "environment" }
        create("prod") { dimension = "environment" }
        
        create("free") { dimension = "tier" }
        create("paid") { dimension = "tier" }
    }
}
// Results in: devFreeDebug, devPaidDebug, prodFreeRelease, etc.
```---

## 3.Kotlin 开发标准

### 3.1 命名约定

|类型 |大会 |示例|
|------|------------|---------|
|类/接口 |帕斯卡案例 | `UserRepository`、`MainActivity` |
|函数/变量|驼峰式 | `getUserName()`, `isLoading` |
|恒定| SCREAMING_SNAKE | 尖叫蛇`MAX_RETRY_COUNT` |
|套餐 |小写| `com.example.myapp` |
|可组合 |帕斯卡案例 | `@Composable fun UserCard()` |

### 3.2 代码标准（重要）

**空安全性**：```kotlin
// ❌ Avoid: Non-null assertion !! (may crash)
val name = user!!.name

// ✅ Recommended: Safe call + default value
val name = user?.name ?: "Unknown"

// ✅ Recommended: let handling
user?.let { processUser(it) }
```**异常处理**：```kotlin
// ❌ Avoid: Random try-catch in business layer swallowing exceptions
fun loadData() {
    try {
        val data = api.fetch()
    } catch (e: Exception) {
        // Swallowing exception, hard to debug
    }
}

// ✅ Recommended: Let exceptions propagate, handle at appropriate layer
suspend fun loadData(): Result<Data> {
    return try {
        Result.success(api.fetch())
    } catch (e: Exception) {
        Result.failure(e)  // Wrap and return, let caller decide handling
    }
}

// ✅ Recommended: Unified handling in ViewModel
viewModelScope.launch {
    runCatching { repository.loadData() }
        .onSuccess { _uiState.value = UiState.Success(it) }
        .onFailure { _uiState.value = UiState.Error(it.message) }
}
```### 3.3 线程和协程（关键）

**线程选择原则**：

|操作类型 |主题 |描述 |
|----------------|--------|-------------|
|用户界面更新 | `Dispatchers.Main` |更新视图、状态、LiveData |
|网络请求| `Dispatchers.IO` | HTTP 调用、API 请求 |
|文件输入/输出 | `Dispatchers.IO` |本地存储、数据库操作|
|计算密集型 | `Dispatchers.Default` | | `Dispatchers.Default` JSON解析、排序、加密 |

**正确用法**：```kotlin
// In ViewModel
viewModelScope.launch {
    // Default Main thread, can update UI State
    _uiState.value = UiState.Loading
    
    // Switch to IO thread for network request
    val result = withContext(Dispatchers.IO) {
        repository.fetchData()
    }
    
    // Automatically returns to Main thread, update UI
    _uiState.value = UiState.Success(result)
}

// In Repository (suspend functions should be main-safe)
suspend fun fetchData(): Data = withContext(Dispatchers.IO) {
    api.getData()
}
```**常见错误**：```kotlin
// ❌ Wrong: Updating UI on IO thread
viewModelScope.launch(Dispatchers.IO) {
    val data = api.fetch()
    _uiState.value = data  // Crash or warning!
}

// ❌ Wrong: Executing time-consuming operation on Main thread
viewModelScope.launch {
    val data = api.fetch()  // Blocking main thread! ANR
}

// ✅ Correct: Fetch on IO, update on Main
viewModelScope.launch {
    val data = withContext(Dispatchers.IO) { api.fetch() }
    _uiState.value = data
}
```### 3.4 可见性规则```kotlin
// Default is public, declare explicitly when needed
class UserRepository {           // public
    private val cache = mutableMapOf<String, User>()  // Visible only within class
    internal fun clearCache() {} // Visible only within module
}

// data class properties are public by default, be careful when used across modules
data class User(
    val id: String,       // public
    val name: String
)
```### 3.5 常见语法陷阱```kotlin
// ❌ Wrong: Accessing uninitialized lateinit
class MyViewModel : ViewModel() {
    lateinit var data: String
    fun process() = data.length  // May crash
}

// ✅ Correct: Use nullable or default value
class MyViewModel : ViewModel() {
    var data: String? = null
    fun process() = data?.length ?: 0
}

// ❌ Wrong: Using return in lambda
list.forEach { item ->
    if (item.isEmpty()) return  // Returns from outer function!
}

// ✅ Correct: Use return@forEach
list.forEach { item ->
    if (item.isEmpty()) return@forEach
}
```### 3.6 服务器响应数据类字段必须可为空```kotlin
// ❌ Wrong: Fields declared as non-null (server may not return them)
data class UserResponse(
    val id: String = "",
    val name: String = "",
    val avatar: String = ""
)

// ✅ Correct: All fields declared as nullable
data class UserResponse(
    @SerializedName("id")
    val id: String? = null,
    @SerializedName("name")
    val name: String? = null,
    @SerializedName("avatar")
    val avatar: String? = null
)
```### 3.7 生命周期资源管理```kotlin
// ❌ Wrong: Only adding Observer, not removing
class MyView : View {
    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        activity?.lifecycle?.addObserver(this)
    }
    // Memory leak!
}

// ✅ Correct: Paired add and remove
class MyView : View {
    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        activity?.lifecycle?.addObserver(this)
    }

    override fun onDetachedFromWindow() {
        activity?.lifecycle?.removeObserver(this)
        super.onDetachedFromWindow()
    }
}
```### 3.8 日志级别使用```kotlin
import android.util.Log

// Info: Key checkpoints in normal flow
Log.i(TAG, "loadData: started, userId = $userId")

// Warning: Abnormal but recoverable situations
Log.w(TAG, "loadData: cache miss, fallback to network")

// Error: Failure/error situations
Log.e(TAG, "loadData failed: ${error.message}")
```|水平|使用案例|
|--------|----------|
| `我`（信息）|正常流程、方法入口、关键参数 |
| `w`（警告）|可恢复的异常、回退处理、null 返回 |
| `e`（错误）|请求失败、捕获异常、不可恢复的错误

---

## 4. Jetpack Compose 标准

### 4.1 @Composable 上下文规则```kotlin
// ❌ Wrong: Calling Composable from non-Composable function
fun showError(message: String) {
    Text(message)  // Compile error!
}

// ✅ Correct: Mark as @Composable
@Composable
fun ErrorMessage(message: String) {
    Text(message)
}

// ❌ Wrong: Using suspend outside LaunchedEffect
@Composable
fun MyScreen() {
    val data = fetchData()  // Error!
}

// ✅ Correct: Use LaunchedEffect
@Composable
fun MyScreen() {
    var data by remember { mutableStateOf<Data?>(null) }
    LaunchedEffect(Unit) {
        data = fetchData()
    }
}
```### 4.2 状态管理```kotlin
// Basic State
var count by remember { mutableStateOf(0) }

// Derived State (avoid redundant computation)
val isEven by remember { derivedStateOf { count % 2 == 0 } }

// Persist across recomposition (e.g., scroll position)
val scrollState = rememberScrollState()

// State in ViewModel
class MyViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
}
```### 4.3 常见的撰写错误```kotlin
// ❌ Wrong: Creating objects in Composable (created on every recomposition)
@Composable
fun MyScreen() {
    val viewModel = MyViewModel()  // Wrong!
}

// ✅ Correct: Use viewModel() or remember
@Composable
fun MyScreen(viewModel: MyViewModel = viewModel()) {
    // ...
}
```---

## 5. 资源和图标

### 5.1 应用程序图标要求

必须提供多分辨率图标：

|目录 |尺寸|目的|
|------------|------|---------|
| mipmap-mdpi | 48x48 | 48x48基线|
| mipmap-hdpi | 72x72 | 72x72 1.5 倍 |
| mipmap-xhdpi | 96x96 | 96x96 2x |
| mipmap-xxhdpi | 144x144 | 144x144 3x |
| mipmap-xxxhdpi | 192x192 | 192x192 4x |

推荐：使用自适应图标（Android 8+）：```xml
<!-- res/mipmap-anydpi-v26/ic_launcher.xml -->
<adaptive-icon>
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
```### 5.2 资源命名约定

|类型 |前缀 |示例|
|------|--------|---------|
|布局|布局_ | `layout_main.xml` |
|图片| ic_、img_、bg_ | `ic_user.png` |
|颜色 |颜色_ | `颜色_原色` |
|字符串| - | `app_name`、`btn_submit` |

### 5.3 避免使用 Android 保留名称（重要）

变量名称、资源 ID、颜色、图标和 XML 元素**不得**使用 Android 保留字或系统资源名称。使用保留名称会导致构建错误或资源冲突。

**要避免的常见保留名称**：

|类别 |保留名称（请勿使用）|
|----------|----------------------------------------|
|颜色 | `背景`、`前景`、`透明`、`白色`、`黑色` |
|图标/绘图| `图标`、`徽标`、`图像`、`可绘制` |
|意见 | `视图`、`文本`、`按钮`、`布局`、`容器` |
|属性| `id`、`name`、`type`、`style`、`theme`、`color` |
|系统| `app`、`android`、`content`、`data`、`action` |

**示例**：```xml
<!-- ❌ Wrong: Using reserved names -->
<color name="background">#FFFFFF</color>
<color name="icon">#000000</color>

<!-- ✅ Correct: Add prefix or specific naming -->
<color name="app_background">#FFFFFF</color>
<color name="icon_primary">#000000</color>
```

```kotlin
// ❌ Wrong: Variable names conflict with system
val icon = R.drawable.my_icon
val background = Color.White

// ✅ Correct: Use descriptive names
val appIcon = R.drawable.my_icon
val screenBackground = Color.White
```

```xml
<!-- ❌ Wrong: Drawable name conflicts -->
<ImageView android:src="@drawable/icon" />

<!-- ✅ Correct: Add prefix -->
<ImageView android:src="@drawable/ic_home" />
```---

## 6. 构建错误诊断和修复

### 6.1 常见错误快速参考

|错误关键字|原因 |修复 |
|----------------|--------|-----|
| `未解决的参考` |缺少导入或未定义 |检查导入，验证依赖关系 |
| `类型不匹配` |类型不兼容 |检查参数类型，添加转换|
| `无法访问` |可见性问题 |检查公共/私人/内部 |
| `@Composable 调用` |可组合上下文错误 |确保调用者也是 @Composable |
| `重复类` |依赖冲突 |使用`./gradlew依赖项`来调查 |
| `AAPT：错误` |资源文件错误 |检查 XML 语法和资源引用 |

### 6.2 修复最佳实践

1. **首先阅读完整的错误消息**：找到文件和行号
2. **检查最近的更改**：问题通常出现在最新的修改中
3. **干净构建**：`./gradlew clean assembleDebug`
4. **检查依赖版本**：版本冲突是常见原因
5. **如果需要，刷新依赖关系**：清除缓存并重建

### 6.3 调试命令```bash
# Clean and build
./gradlew clean assembleDebug

# View dependency tree (investigate conflicts)
./gradlew :app:dependencies

# View detailed errors
./gradlew assembleDebug --stacktrace

# Refresh dependencies
./gradlew --refresh-dependencies
```---

## 7. 材料设计 3 指南

检查 Android UI 文件是否符合 Material Design 3 指南和 Android 最佳实践。

### 设计理念

#### M3核心原则

|原理|描述 |
|------------|-------------|
| **个人** |基于用户偏好和壁纸的动态颜色|
| **自适应** |响应所有屏幕尺寸和外形尺寸 |
| **富有表现力** |大胆的色彩和个性的版式|
| **无障碍** |面向所有用户的包容性设计 |

#### M3 Expressive（最新）

最新的演变通过以下方式添加了情感驱动的用户体验：
- 充满活力的动态色彩
- 直观的运动物理学
- 自适应组件
- 灵活的排版
- 对比形状（35 个新形状选项）

### 应用风格选择

**关键决策**：将视觉风格与应用类别和目标受众相匹配。

|应用类别 |视觉风格|主要特点 |
|--------------|--------------|----------|
|实用程序/工具 |极简主义|干净、高效、中性的色彩 |
|金融/银行|专业信赖|色彩保守，注重安全 |
|健康/保健 |平静自然 |柔和的色彩，有机的形状|
|儿童（3-5）|俏皮简单|色彩鲜艳，目标大 (56dp+) |
|儿童（6-12 岁）|有趣且引人入胜|充满活力、游戏化的反馈 |
|社交/娱乐 |富有表现力|品牌驱动，姿态丰富 |
|生产力 |干净、专注 |最小，高对比度|
|电子商务|以转化为中心 |清晰的 CTA，可扫描 |

详细的风格配置文件请参见【设计风格指南】(references/design-style-guide.md)。

### 快速参考：主要规格

#### 色彩对比度要求

|元素|最低比率|
|--------|----------------|
|正文 | **4.5:1** |
|大文本 (18sp+) | **3:1** |
|用户界面组件 | **3:1** |

#### 触摸目标

|类型 |尺寸|
|------|------|
|最低 | 48 × 48dp |
|建议（主要行动）| 56 × 56dp |
|儿童应用程序 | 56dp+ |
|目标之间的间距 |最小 8dp |

#### 8dp 网格系统

|代币|价值|用途 |
|--------|--------|--------|
| xs | 4dp |图标填充 |
| SM | 8dp |紧密间距|
|医学博士 | 16dp |默认填充 |
| LG | 24dp |截面间距|
| XL | 32dp |间隙大|
| xxl | xxl | 48dp |屏幕边距 |

#### 版式比例（摘要）

|类别 |尺寸 |
|----------|--------|
|显示| 57sp、45sp、36sp |
|标题| 32sp、28sp、24sp |
|标题 | 22sp、16sp、14sp |
|身体| 16sp、14sp、12sp |
|标签| 14sp、12sp、11sp |

#### 动画持续时间

|类型 |持续时间 |
|------|----------|
|微（涟漪）| 50-100 毫秒 |
|简短（简单）| 100-200 毫秒 |
|中（展开/折叠）| 200-300 毫秒 |
|长（复杂）| 300-500 毫秒 |

#### 组件尺寸

|组件|身高|最小宽度|
|------------|--------|------------|
|按钮| 40dp | 64dp |
| FAB | 56dp | 56dp |
|文本字段 | 56dp | 280dp |
|应用栏 | 64dp | - |
|底部导航 | 80dp | - |

### 反模式（必须避免）

#### UI 反模式
- 超过5个底部导航项
- 同一屏幕上有多个FAB
- 触摸目标小于 48dp
- 间距不一致（非 8dp 倍数）
- 缺少深色主题支持
- 彩色背景上的文本无需对比度检查

#### 性能反模式
- 启动时间 > 2 秒，无进度指示器
- 帧速率 < 60 FPS（每帧 > 16 毫秒）
- 崩溃率 > 1.09%（Google Play 阈值）
- ANR 率 > 0.47%（Google Play 阈值）

#### 可访问性反模式
- 缺少交互元素的内容描述
- 标签中的元素类型（例如，“保存按钮”而不是“保存”）
- 儿童应用程序中的复杂手势
- 适合非读者的纯文本按钮

### 审核清单

- [ ] 8dp 间距网格合规性
- [ ] 最小触摸目标 48dp
- [ ] 正确的排版比例使用
- [ ] 颜色对比度合规性（文本为 4.5:1+）
- [ ] 深色主题支持
- [ ] 所有交互元素的内容描述
- [ ] 启动 < 2 秒或显示进度
- [ ] 视觉风格与应用类别匹配

### 设计参考

|主题 |参考|
|------|----------|
|颜色、版式、间距、形状 | [视觉设计](references/visual-design.md) |
|动画和过渡 | [运动系统](references/motion-system.md) |
|无障碍指南 | [辅助功能](参考文献/accessibility.md) |
|大屏幕和可折叠设备 | [自适应屏幕](references/adaptive-screens.md) |
| Android 生命体征与性能 | [性能与稳定性](references/performance-stability.md) ||隐私与安全 | [隐私与安全](references/privacy-security.md) |
|音频、视频、通知 | [功能需求](参考资料/功能需求.md) |
|按类别划分的应用程序风格 | [设计风格指南](references/design-style-guide.md) |

---

## 8. 测试

> **注意**：仅当用户明确要求测试时才添加测试依赖项。

经过良好测试的 Android 应用程序使用分层测试：针对逻辑的快速本地单元测试、针对 UI 和集成的仪器测试以及 Gradle 托管设备，以便在任何机器（包括 CI）上重复运行模拟器。

### 8.1 测试依赖关系

在添加测试依赖项之前，请检查项目的现有版本以避免冲突：

1. 检查 `gradle/libs.versions.toml` — 如果存在，则使用项目的版本目录样式添加测试 deps
2. 检查现有的 `build.gradle.kts` 是否已固定的依赖版本
3. 使用下表匹配版本系列

**版本对齐规则**：

|测试依赖性|必须与 | 对齐如何检查 |
|----------------------------------------------------------|----------------------------------------------------------------|------------------------------------------------------------------------|
| `kotlinx 协程测试` |项目的“kotlinx-coroutines-core”版本 |在构建文件或版本目录中搜索“kotlinx-coroutines” |
| `compose-ui-test-junit4` |项目的 Compose BOM 或 `compose-compiler` |在构建文件中搜索“compose-bom”或“compose.compiler” |
| `浓缩咖啡-*` |所有 Espresso 工件必须使用相同版本 |在构建文件中搜索“espresso” |
| `androidx.test:runner`、`rules`、`ext:junit` |应该使用兼容的AndroidX测试版本|在构建文件中搜索“androidx.test” |
| `模拟` |必须支持项目的Kotlin版本 |检查根 `build.gradle.kts` 或版本目录中的 `kotlin` 版本 |

**依赖项参考** — 仅添加您需要的组：```kotlin
dependencies {
    // --- Local unit tests (src/test/) ---
    testImplementation("junit:junit:<version>")                          // 4.13.2+
    testImplementation("org.robolectric:robolectric:<version>")          // 4.16.1+
    testImplementation("io.mockk:mockk:<version>")                      // match Kotlin version
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:<version>")  // match coroutines-core
    testImplementation("androidx.arch.core:core-testing:<version>")      // InstantTaskExecutorRule for LiveData
    testImplementation("app.cash.turbine:turbine:<version>")             // Flow/StateFlow testing

    // --- Instrumentation tests (src/androidTest/) ---
    androidTestImplementation("androidx.test.ext:junit:<version>")
    androidTestImplementation("androidx.test:runner:<version>")
    androidTestImplementation("androidx.test:rules:<version>")
    androidTestImplementation("androidx.test.espresso:espresso-core:<version>")
    androidTestImplementation("androidx.test.espresso:espresso-contrib:<version>")   // RecyclerView, Drawer
    androidTestImplementation("androidx.test.espresso:espresso-intents:<version>")   // Intent verification
    androidTestImplementation("androidx.test.espresso:espresso-idling-resource:<version>")
    androidTestImplementation("androidx.test.uiautomator:uiautomator:<version>")

    // --- Compose UI tests (only if project uses Compose) ---
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")      // version from Compose BOM
    debugImplementation("androidx.compose.ui:ui-test-manifest")          // required for createComposeRule
}
```> **注意**：如果项目使用 Compose BOM，则 `ui-test-junit4` 和 `ui-test-manifest` 不需要显式版本 - BOM 管理它们。

在“android”块中启用 Robolectric 资源支持：```kotlin
android {
    testOptions {
        unitTests.isIncludeAndroidResources = true  // required for Robolectric
    }
}
```### 8.2 分层测试

|层 |地点 |运行 |速度|用于 |
|--------------------------------|--------------------|-------------------------------------|------------------------------------------------|----------------------------------------------------|
|单元（JUnit）| `src/测试/` | JVM | 〜女士| ViewModel、存储库、映射器、验证器 |
|单位+Robolectric | `src/测试/` | JVM + 模拟Android |约 100 毫秒 |需要上下文、资源、SharedPrefs 的代码 |
|撰写 UI（本地）| `src/测试/` | JVM + Robolectric | JVM + Robolectric约 100 毫秒 |可组合渲染和交互 |
|浓缩咖啡| `src/androidTest/` |设备/模拟器 | 〜秒|基于视图的 UI 流程、意图、数据库集成 |
|撰写 UI（设备）| `src/androidTest/` |设备/模拟器 | 〜秒|具有真实渲染的完整 Compose UI 流程 |
|用户界面自动化 | `src/androidTest/` |设备/模拟器 | 〜秒|系统对话框、通知、多应用程序 |
|受管设备 | `src/androidTest/` | Gradle 管理的 AVD | 〜分钟（第一次运行）| CI、跨 API 级别的矩阵测试 |

有关详细示例、代码模式和 Gradle 托管设备配置，请参阅[测试](references/testing.md)。

### 8.3 测试命令```bash
# Local unit tests (fast, no emulator)
./gradlew test                          # all modules
./gradlew :app:testDebugUnitTest        # app module, debug variant

# Single test class
./gradlew :app:testDebugUnitTest --tests "com.example.myapp.CounterViewModelTest"

# Instrumentation tests (requires device or managed device)
./gradlew connectedDebugAndroidTest     # on connected device
./gradlew pixel6Api34DebugAndroidTest   # on managed device

# Both together
./gradlew test connectedDebugAndroidTest

# Test with coverage report (JaCoCo)
./gradlew testDebugUnitTest jacocoTestReport
```
