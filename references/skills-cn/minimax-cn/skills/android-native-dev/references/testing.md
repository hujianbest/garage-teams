# 测试

每个 Android 测试层的详细示例和模式。阅读与您正在使用的图层相关的部分。

## 目录

1. [本地单元测试（JUnit + Robolectric）](#1-local-unit-tests-junit--robolectric)
2. [仪器测试（浓缩咖啡）](#2-仪器测试-浓缩咖啡)
3. [UI Automator（跨应用程序和系统 UI）](#3-ui-automator-cross-app--system-ui)
4. [撰写 UI 测试](#4-compose-ui-testing)
5. [Gradle 托管设备](#5-gradle-management-devices)

---

## 1. 本地单元测试（JUnit + Robolectric）

本地测试位于“src/test/”中并在 JVM 上运行——不需要模拟器，因此速度很快（每个测试都是毫秒）。将它们用于 ViewModel、存储库、映射器、验证器和任何纯逻辑。

### 基本 ViewModel 测试```kotlin
class CounterViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()  // see below

    private lateinit var viewModel: CounterViewModel

    @Before
    fun setup() {
        viewModel = CounterViewModel()
    }

    @Test
    fun `increment updates count`() = runTest {
        viewModel.increment()
        assertEquals(1, viewModel.uiState.value.count)
    }
}
```### 测试协程（关键）

JVM 上不存在主调度程序。将其替换为“TestDispatcher”，或将测试崩溃替换为“IllegalStateException”。```kotlin
// Reusable rule — put in a shared test-util module
class MainDispatcherRule(
    private val dispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

```kotlin
// ❌ Wrong: No Main dispatcher replacement → crash
@Test
fun `load data`() = runTest {
    val vm = MyViewModel(repo)
    vm.load()  // launches on Dispatchers.Main → IllegalStateException
}

// ✅ Correct: Use MainDispatcherRule
@get:Rule
val mainDispatcherRule = MainDispatcherRule()

@Test
fun `load data`() = runTest {
    val vm = MyViewModel(repo)
    vm.load()
    assertEquals(UiState.Success, vm.uiState.value)
}
```### 使用 Turbine 测试 StateFlow```kotlin
@Test
fun `loading then success states`() = runTest {
    val vm = MyViewModel(fakeRepo)

    vm.uiState.test {   // Turbine extension
        assertEquals(UiState.Idle, awaitItem())
        vm.load()
        assertEquals(UiState.Loading, awaitItem())
        assertEquals(UiState.Success(data), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```### 使用 MockK 进行模拟```kotlin
@Test
fun `repository calls api and caches`() = runTest {
    val api = mockk<UserApi>()
    coEvery { api.getUser("42") } returns User("42", "Alice")

    val repo = UserRepository(api)
    val user = repo.getUser("42")

    assertEquals("Alice", user.name)
    coVerify(exactly = 1) { api.getUser("42") }
}
```|模拟K函数|目的|
|----------------|------------------------|
| `mock<T>()` |创建模拟实例 |
| `每个{}` |存根同步调用 |
| `coEvery {}` |存根挂起函数 |
| `验证{}` |验证通话发生 |
| `coVerify {}` |验证挂起呼叫 |
| `槽<T>()` |捕获参数值 |

### Robolectric — 当您需要 Android 类时

Robolectric 在 JVM 上模拟 Android 框架，因此在访问“Context”、“SharedPreferences”、资源等时测试保持快速。```kotlin
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class PreferencesManagerTest {

    private lateinit var context: Context

    @Before
    fun setup() {
        context = ApplicationProvider.getApplicationContext()
    }

    @Test
    fun `saves and reads theme preference`() {
        val prefs = PreferencesManager(context)
        prefs.setDarkMode(true)
        assertTrue(prefs.isDarkMode())
    }
}
```### 常见的本地测试错误```kotlin
// ❌ Wrong: Testing implementation details (fragile)
@Test
fun `check internal cache map size`() {
    repo.load()
    assertEquals(1, repo.cacheMap.size)  // breaks if cache strategy changes
}

// ✅ Correct: Test observable behavior
@Test
fun `second call returns cached result without network`() = runTest {
    coEvery { api.fetch() } returns data

    repo.load()
    repo.load()

    coVerify(exactly = 1) { api.fetch() }  // only one network call
}
```---

## 2. 仪器测试（Espresso）

仪器测试位于“src/androidTest/”中，并在真实设备或模拟器上运行。比本地测试慢，但它们运用了实际的 Android 堆栈 - 将它们用于 UI 流、数据库集成和跨组件交互。

### 测试运行器设置

在 `app/build.gradle.kts` 中：```kotlin
android {
    defaultConfig {
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
}
```### 浓缩咖啡基础知识

Espresso 的 API 遵循一致的模式：**查找→行动→断言**。```kotlin
@RunWith(AndroidJUnit4::class)
class LoginScreenTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(LoginActivity::class.java)

    @Test
    fun validLogin_navigatesToHome() {
        // Find and act
        onView(withId(R.id.email_input))
            .perform(typeText("user@example.com"), closeSoftKeyboard())
        onView(withId(R.id.password_input))
            .perform(typeText("secret123"), closeSoftKeyboard())
        onView(withId(R.id.login_button))
            .perform(click())

        // Assert
        onView(withId(R.id.home_container))
            .check(matches(isDisplayed()))
    }
}
```|类别 |常见匹配器/操作 |
|------------|------------------------------------------------------------------------------------------------|
| **查找** | `withId(R.id.x)`、`withText("x")`、`withContentDescription("x")`、`withHint("x")` |
| **行动** | `click()`、`typeText("x")`、`clearText()`、`scrollTo()`、`swipeUp()` |
| **断言** | `isDisplayed()`、`withText("x")`、`isEnabled()`、`isChecked()`、`doesNotExist()` |

### 测试意图

Espresso-Intents 允许您验证传出意图和存根响应（例如相机、文件选择器）。```kotlin
@get:Rule
val intentsRule = IntentsRule()

@Test
fun shareButton_launchesShareIntent() {
    onView(withId(R.id.share_button)).perform(click())

    intended(allOf(
        hasAction(Intent.ACTION_SEND),
        hasType("text/plain")
    ))
}

@Test
fun cameraButton_handlesResult() {
    val resultData = Intent().apply { putExtra("photo_uri", "content://mock") }
    intending(hasAction(MediaStore.ACTION_IMAGE_CAPTURE))
        .respondWith(Instrumentation.ActivityResult(RESULT_OK, resultData))

    onView(withId(R.id.camera_button)).perform(click())
    onView(withId(R.id.photo_preview)).check(matches(isDisplayed()))
}
```### 用于异步操作的 IdlingResource

Espresso 默认情况下等待 UI 线程和 AsyncTask，但不等待自定义异步工作（Retrofit、协程等）。当您的应用程序繁忙时，“IdlingResource”会通知 Espresso。```kotlin
// In production code (thin wrapper)
object NetworkIdlingResource {
    private val counter = CountingIdlingResource("Network")
    fun increment() = counter.increment()
    fun decrement() = counter.decrement()
    fun get(): IdlingResource = counter
}

// In test setup
@Before
fun registerIdling() {
    IdlingRegistry.getInstance().register(NetworkIdlingResource.get())
}

@After
fun unregisterIdling() {
    IdlingRegistry.getInstance().unregister(NetworkIdlingResource.get())
}
```---

## 3. UI Automator（跨应用程序和系统 UI）

UI Automator 可以与任何可见的 UI 交互——系统对话框、通知、其他应用程序。当 Espresso 无法到达应用程序进程之外时使用它。

|使用案例|为什么选择 UI Automator |
|------------------------------------------|----------------------------------------|
|运行时权限对话框 |系统UI，外部应用程序进程|
|通知操作 |系统通知栏 |
|设备设置交互 |设置应用程序|
|多应用工作流程 |例如，分享到另一个应用程序并返回 |```kotlin
@RunWith(AndroidJUnit4::class)
class PermissionFlowTest {

    private lateinit var device: UiDevice

    @Before
    fun setup() {
        device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
    }

    @Test
    fun grantsCameraPermission_andOpensCamera() {
        // Trigger permission request from within your app
        onView(withId(R.id.camera_button)).perform(click())

        // Handle the system permission dialog via UI Automator
        val allowButton = device.findObject(
            By.res("com.android.permissioncontroller:id/permission_allow_foreground_only_button")
        )
        allowButton?.click()

        // Back in Espresso territory — verify the camera view appeared
        onView(withId(R.id.camera_preview)).check(matches(isDisplayed()))
    }

    @Test
    fun notificationTap_opensDetail() {
        // Open notification shade
        device.openNotification()
        device.wait(Until.hasObject(By.textStartsWith("New message")), 5000)

        // Tap the notification
        val notification = device.findObject(By.textStartsWith("New message"))
        notification.click()

        // Verify deep-link target
        onView(withId(R.id.message_detail)).check(matches(isDisplayed()))
    }
}
```---

## 4. 编写 UI 测试

Compose 有自己的测试框架，该框架使用语义树而不是视图层次结构。测试可以作为本地测试（使用 Robolectric）或仪器测试运行——API 是相同的。

### 基本设置```kotlin
@RunWith(AndroidJUnit4::class)
class GreetingScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun displaysGreeting_andRespondsToClick() {
        composeTestRule.setContent {
            MyAppTheme {
                GreetingScreen(name = "World")
            }
        }

        composeTestRule.onNodeWithText("Hello, World!")
            .assertIsDisplayed()

        composeTestRule.onNodeWithText("Say Hi")
            .performClick()

        composeTestRule.onNodeWithText("Hi back!")
            .assertIsDisplayed()
    }
}
```### 查找器、断言和操作

|类别 |应用程序接口 |示例|
|------------------------|------------------------------------------------------------------------|--------------------------------|
| **查找** | `onNodeWithText("x")` |匹配可见文本 |
|            | `onNodeWithTag("x")` |匹配 `Modifier.testTag("x")` |
|            | `onNodeWithContentDescription("x")` |匹配语义标签 |
|            | `onAllNodesWithTag("x")` |返回匹配列表 |
| **断言** | `assertIsDisplayed()` |节点可见 |
|            | `assertTextEquals("x")` |精确的文本匹配 |
|            | `assertIsEnabled()` / `assertIsNotEnabled()` |启用状态 |
|            | `assertDoesNotExist()` |节点不在树中 |
|            | `assertCountEquals(n)` |对于`onAllNodes` |
| **行动** | `执行单击()` |点击 |
|            | `performTextInput("x")` |在文本字段中输入 |
|            | `performScrollTo()` |将节点滚动到视图中 |
|            | `performTouchInput { swipeUp() }` |手势|

### 使用 testTag 实现可靠的选择器

基于文本的查找器会因本地化或副本更改而中断。使用“testTag”作为稳定的选择器：```kotlin
// ❌ Fragile: breaks if text changes or app is localized
composeTestRule.onNodeWithText("Submit Order").performClick()

// ✅ Stable: testTag doesn't change with locale
composeTestRule.onNodeWithTag("submit_order_button").performClick()
```

```kotlin
// In production Composable
Button(
    onClick = { /* ... */ },
    modifier = Modifier.testTag("submit_order_button")
) {
    Text(stringResource(R.string.submit_order))
}
```### 使用 Activity 上下文进行测试

当您的 Composable 需要“ComponentActivity”（例如，用于“viewModel()”或导航）时，请使用“createAndroidComposeRule”：```kotlin
@get:Rule
val composeTestRule = createAndroidComposeRule<MainActivity>()

@Test
fun fullScreen_endToEnd() {
    // Activity is already launched — interact with the real content
    composeTestRule.onNodeWithTag("login_email")
        .performTextInput("user@test.com")
    composeTestRule.onNodeWithTag("login_password")
        .performTextInput("pass123")
    composeTestRule.onNodeWithTag("login_submit")
        .performClick()

    composeTestRule.waitUntil(timeoutMillis = 5000) {
        composeTestRule.onAllNodesWithTag("home_screen")
            .fetchSemanticsNodes().isNotEmpty()
    }

    composeTestRule.onNodeWithTag("home_screen")
        .assertIsDisplayed()
}
```### 测试导航```kotlin
@Test
fun navigatesToDetail_onItemClick() {
    val navController = TestNavHostController(ApplicationProvider.getApplicationContext())

    composeTestRule.setContent {
        navController.navigatorProvider.addNavigator(ComposeNavigator())
        MyAppNavHost(navController = navController)
    }

    // Click item on list screen
    composeTestRule.onNodeWithTag("item_0").performClick()

    // Verify navigation destination
    assertEquals("detail/0", navController.currentBackStackEntry?.destination?.route)
}
```### 常见的 Compose 测试错误```kotlin
// ❌ Wrong: Asserting immediately after async operation
composeTestRule.onNodeWithTag("submit").performClick()
composeTestRule.onNodeWithText("Success").assertIsDisplayed()  // may fail — UI hasn't updated yet

// ✅ Correct: Wait for the UI to settle
composeTestRule.onNodeWithTag("submit").performClick()
composeTestRule.waitForIdle()
composeTestRule.onNodeWithText("Success").assertIsDisplayed()

// ✅ Also correct: waitUntil for longer async work
composeTestRule.onNodeWithTag("submit").performClick()
composeTestRule.waitUntil(timeoutMillis = 3000) {
    composeTestRule.onAllNodesWithText("Success")
        .fetchSemanticsNodes().isNotEmpty()
}
```---

## 5. Gradle 管理的设备

在“build.gradle.kts”中定义模拟器配置文件，以便任何人（包括 CI）都可以运行仪器测试，而无需手动创建 AVD。 Gradle 下载系统映像、创建模拟器、运行测试并自动将其拆除。

### 设备配置

在 `app/build.gradle.kts` 中：```kotlin
android {
    testOptions {
        managedDevices {
            localDevices {
                create("pixel6Api34") {
                    device = "Pixel 6"
                    apiLevel = 34
                    systemImageSource = "aosp-atd"  // ATD = faster, headless
                }
                create("pixel4Api30") {
                    device = "Pixel 4"
                    apiLevel = 30
                    systemImageSource = "aosp-atd"
                }
                create("smallTabletApi34") {
                    device = "Nexus 7"
                    apiLevel = 34
                    systemImageSource = "google"     // full Google APIs image
                }
            }

            // Group devices for matrix testing
            groups {
                create("phoneTests") {
                    targetDevices.add(devices["pixel6Api34"])
                    targetDevices.add(devices["pixel4Api30"])
                }
                create("allDevices") {
                    targetDevices.add(devices["pixel6Api34"])
                    targetDevices.add(devices["pixel4Api30"])
                    targetDevices.add(devices["smallTabletApi34"])
                }
            }
        }
    }
}
```### 系统镜像源

|来源 |描述 |最适合 |
|----------------|----------------------------------------------------------------|------------------------------------------|
| `"aosp-atd"` |自动测试设备 - 最小化，无 Play 服务 |快速CI，纯逻辑测试|
| `"google-atd"` | ATD 与 Google API |需要 Maps、Firebase 的测试 |
| `“aosp”` |完整的 AOSP 图像 |标准仿真器测试|
| `“谷歌”` | Google Play 服务的完整图像 | Play 服务集成 |

ATD 映像启动速度更快，消耗的内存更少，因为它们去除了与测试无关的 UI 镶边和预装应用程序。对于 CI 管道，首选 `aosp-atd` 或 `google-atd`。

### 运行测试```bash
# Run on a single managed device
./gradlew pixel6Api34DebugAndroidTest

# Run on a device group (all devices in parallel if hardware allows)
./gradlew phoneTestsGroupDebugAndroidTest
./gradlew allDevicesGroupDebugAndroidTest

# With specific flavor
./gradlew pixel6Api34DevDebugAndroidTest

# Enable test sharding across devices (speeds up large suites)
./gradlew allDevicesGroupDebugAndroidTest \
    -Pandroid.experimental.androidTest.numManagedDeviceShards=2

# Generate HTML test report
./gradlew pixel6Api34DebugAndroidTest \
    --continue   # don't stop on first failure
```测试结果写入“app/build/reports/androidTests/managedDevice/”。