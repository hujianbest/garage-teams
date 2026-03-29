# SwiftUI 设计指南

基于 Apple 人机界面指南的设计规则，用于使用 SwiftUI 构建本机 iOS 界面。

---

## 设计理念

iOS 设计优先考虑 **内容而不是 chrome**。界面应该感觉不可见——用户专注于他们的任务，而不是用户界面。

**关键心态：**

1. **让内容呼吸** — 使用全屏布局，最小化边框和方框，让图像和文本占据中心舞台

2. **利用系统约定** — 用户已经了解 iOS 的工作原理；不要重新发明导航、手势或控件

3. **专为手指设计**——触摸不精准；慷慨的点击目标和宽容的手势识别比像素完美的布局更重要

4. **尊重用户选择** - 将动态类型、深色模式、减少运动和其他辅助功能设置视为一流要求

**iOS 26+ 液体玻璃：**
最新的 iOS 引入了半透明的 UI 元素，可以响应其背后的灯光和内容。排版更加粗体，文本倾向于左对齐，以便于扫描。

---

## 1. 布局和安全区域

**影响：** 严重

### 1.1 最小 44 点触摸目标

所有交互元素必须至少具有 44x44 **点**（不是像素 - 点随屏幕密度变化）。```swift
Button(action: handleTap) {
    Image(systemName: "heart.fill")
}
.frame(minWidth: 44, minHeight: 44)
```避免将关键交互放置在系统手势操作的屏幕边缘附近。

### 1.2 尊重安全区域

切勿将交互式或重要内容放置在状态栏、动态岛或主页指示器下方。 SwiftUI 默认情况下尊重安全区域。仅将 `.ignoresSafeArea()` 用于背景填充、图像或装饰元素，切勿用于文本或交互式控件。```swift
ZStack {
    LinearGradient(colors: [.blue, .purple], startPoint: .top, endPoint: .bottom)
        .ignoresSafeArea()
    
    VStack {
        Text("Welcome")
            .font(.largeTitle)
        Button("Get Started") { }
    }
}
```### 1.3 拇指区域的主要操作

将主要操作放置在用户拇指自然放置的屏幕底部。次要操作和导航位于顶部。```swift
VStack {
    ScrollView {
        // Content
    }
    
    Spacer()
    
    Button("Submit") { submit() }
        .buttonStyle(.borderedProminent)
        .padding(.horizontal)
        .padding(.bottom)
}
```### 1.4 支持所有屏幕尺寸

专为 iPhone SE (375pt) 到 iPad Pro (1024pt+) 设计。使用尺寸类别来适应：```swift
@Environment(\.horizontalSizeClass) private var sizeClass

var body: some View {
    if sizeClass == .compact {
        VStack { content }
    } else {
        HStack { content }
    }
}
```|尺码等级 |设备|
|------------|---------|
|紧凑宽度| iPhone 纵向、小 iPhone 横向 |
|常规宽度| iPad、iPhone大风景|

使用灵活的布局，避免硬编码宽度：```swift
HStack(spacing: 16) {
    ForEach(categories) { category in
        CategoryCard(category: category)
            .frame(maxWidth: .infinity)
    }
}
```### 1.5 8pt 网格对齐

将间距、填充和元素大小与 8 点的倍数（8、16、24、32、40、48）对齐。使用 4pt 进行微调。

### 1.6 景观支持

支持横向方向，除非应用程序是特定于任务的（例如相机）。使用“ViewThatFits”或“GeometryReader”进行自适应布局。```swift
ViewThatFits {
    HStack { contentViews }
    VStack { contentViews }
}
```---

## 2. 导航

**影响：** 严重

### 2.1 顶级部分的选项卡栏

使用屏幕底部的选项卡栏显示 3 到 5 个顶级部分。每个选项卡应代表不同类别的内容或功能。```swift
TabView(selection: $selectedTab) {
    HomeView()
        .tabItem {
            Label("Home", systemImage: "house")
        }
        .tag(Tab.home)
    
    DiscoverView()
        .tabItem {
            Label("Discover", systemImage: "magnifyingglass")
        }
        .tag(Tab.discover)
    
    AccountView()
        .tabItem {
            Label("Account", systemImage: "person")
        }
        .tag(Tab.account)
}
```### 2.2 导航架构

**标签栏（平面）** — 用于 3-5 个同等重要的部分
- 始终可见，除非被模态框覆盖
- 每个选项卡维护自己的导航堆栈
- 最重要的内容位于最左边（更容易拇指访问）

**分层（向下钻取）** — 用于树结构信息
- 带后退按钮的推送/弹出导航
- 最小化深度（最多 3-4 层）
- 提供搜索作为深树的逃生口

**模态（重点任务）** — 用于独立的工作流程
- 全屏显示关键任务
- 可忽略任务的页表（向下滑动）
- 如果可能丢失数据，则清除“完成/取消”并进行确认

切勿使用汉堡菜单——它们会显着降低功能的可发现性。

### 2.3 主要视图中的大标题

对顶级视图使用“.navigationBarTitleDisplayMode(.large)”。当用户滚动时，标题会转换为内联。```swift
NavigationStack {
    List(conversations) { conversation in
        ConversationRow(conversation: conversation)
    }
    .navigationTitle("Inbox")
    .navigationBarTitleDisplayMode(.large)
}
```### 2.4 切勿覆盖向后滑动

用于返回导航的从左边缘滑动手势是系统级的期望。切勿附加干扰它的自定义手势识别器。

### 2.5 使用 NavigationStack 进行分层内容

使用“NavigationStack”（而不是已弃用的“NavigationView”）来深入了解内容。使用“NavigationPath”进行编程导航。```swift
@State private var navPath = NavigationPath()

NavigationStack(path: $navPath) {
    List(products) { product in
        NavigationLink(value: product) {
            ProductRow(product: product)
        }
    }
    .navigationDestination(for: Product.self) { product in
        ProductDetailView(product: product)
    }
}
```### 2.6 跨导航保留状态

当用户向后导航然后向前导航或切换选项卡时，恢复之前的滚动位置和输入状态。```swift
@SceneStorage("selectedTab") private var selectedTab = Tab.home
@SceneStorage("scrollPosition") private var scrollPosition: String?
```---

## 3. 版式和动态类型

**影响：** 高

### 3.1 使用内置文本样式

始终使用语义文本样式 - 它们会自动根据动态类型进行缩放：

|风格|用途 |
|--------|--------|
| `.largeTitle` |屏幕标题 |
| `.title`、`.title2`、`.title3` |节标题 |
| `.headline` |强调正文 |
| `.body` |主要内容（默认 17pt）|
| `.callout` |次要强调 |
| `.副标题` |配套标签|
| `.footnote`、`.caption` |三级信息|
| `.caption2` |最小尺寸（11pt）|```swift
VStack(alignment: .leading, spacing: 8) {
    Text("Article Title")
        .font(.headline)
    
    Text("Published by Author Name")
        .font(.subheadline)
        .foregroundStyle(.secondary)
    
    Text(articleBody)
        .font(.body)
}
```### 3.2 支持动态类型，包括可访问性大小

动态类型可以在最大辅助尺寸下将文本缩放至大约 200%。布局必须重排——切勿截断或剪辑重要文本。```swift
@Environment(\.dynamicTypeSize) private var typeSize

var body: some View {
    if typeSize.isAccessibilitySize {
        VStack(alignment: .leading) { content }
    } else {
        HStack { content }
    }
}
```### 3.3 自定义字体必须缩放

如果您使用自定义字体，请使用 Font.custom(_:size:relativeTo:) 缩放它，以便它响应动态类型。```swift
Text("Brand Text")
    .font(.custom("Avenir-Medium", size: 17, relativeTo: .body))
```### 3.4 SF Pro 作为系统字体

除非品牌要求另有规定，否则请使用系统字体 (SF Pro)。 SF Pro 针对 Apple 显示屏上的易读性进行了优化。

### 3.5 最小 11pt 文本

切勿显示小于 11pt 的文本。正文最好使用 17pt。使用“caption2”样式（11pt）作为绝对最小值。

### 3.6 通过重量和尺寸划分的层次结构

通过字体粗细和大小建立视觉层次结构。不要仅仅依靠颜色来区分文本级别。

### 3.7 SF 符号

使用 SF Symbols（6,900+ 图标）而不是自定义图像资源：```swift
// Basic usage with automatic text alignment
Label("Favorites", systemImage: "star.fill")

// Rendering modes
Image(systemName: "cloud.sun.rain")
    .symbolRenderingMode(.hierarchical)  // or .multicolor, .palette
    .imageScale(.large)  // .small, .medium, .large
```SF 符号自动匹配文本粗细、使用动态类型缩放并与文本基线对齐。让它们自然地调整大小——不要强迫它们放入固定尺寸的容器中。

---

## 4. 彩色和深色模式

**影响：** 高

### 4.1 使用语义系统颜色

切勿直接使用硬编码的 RGB、十六进制或“.black”/“.white”。使用语义颜色：

**标签：**
- `.primary`、`.secondary`、`.tertiary`、`.quaternary`

**背景：**
- `Color(.systemBackground)` — 主表面
- `Color(.secondarySystemBackground)` — 卡片，分组
- `Color(.tertiarySystemBackground)` — 嵌套元素

**系统颜色（适应外观）：**
- `.blue`、`.red`、`.green`、`.orange`、`.yellow`、`.purple`、`.pink`、`.cyan`、`.mint`、`.teal`、`.indigo`、`.brown`、`.gray````swift
VStack {
    Text("Primary content")
        .foregroundStyle(.primary)
    
    Text("Supporting info")
        .foregroundStyle(.secondary)
}
.background(Color(.systemBackground))
```### 4.2 自定义颜色需要 4 种变体

对于自定义颜色，请在资产目录中定义所有外观组合：
1. 灯光模式
2.深色模式
3. 灯光模式+高对比度
4.深色模式+高对比度```swift
Text("Branded element")
    .foregroundStyle(Color("AccentBrand"))
```对于代码中的动态颜色：```swift
let dynamicColor = UIColor { traits in
    traits.userInterfaceStyle == .dark 
        ? UIColor(red: 0.9, green: 0.9, blue: 1.0, alpha: 1.0)
        : UIColor(red: 0.1, green: 0.1, blue: 0.2, alpha: 1.0)
}
```### 4.3 切勿仅依赖颜色

始终将颜色与文本、图标或形状配对以传达含义。大约 8% 的男性患有某种形式的色觉缺陷。```swift
HStack(spacing: 6) {
    Image(systemName: "exclamationmark.triangle.fill")
    Text("Connection failed")
}
.foregroundStyle(.red)
```### 4.4 4.5:1 对比度最小值

所有文本必须符合 WCAG AA 对比度：普通文本为 4.5:1，大文本为 3:1（18pt+ 或 14pt+ 粗体）。

### 4.5 支持显示 P3 广色域

使用 Display P3 色彩空间在现代 iPhone 上呈现鲜艳、准确的色彩。使用 Display P3 色域定义资产目录中的颜色。

### 4.6 背景层次结构

分层背景以创建视觉深度：```swift
// Level 1: Main view background
Color(.systemBackground)

// Level 2: Cards, grouped sections
Color(.secondarySystemBackground)

// Level 3: Nested elements within cards
Color(.tertiarySystemBackground)
```### 4.7 交互元素的一种强调色

为所有交互元素（按钮、链接、切换）选择单一色调/强调色。这创造了一种一致的、可学习的视觉语言。```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .tint(.orange)
        }
    }
}
```---

## 5. 辅助功能

**影响：** 严重

### 5.1 所有交互元素上的 VoiceOver 标签

每个按钮、控件和交互元素都必须有一个有意义的辅助功能标签。```swift
Button(action: toggleFavorite) {
    Image(systemName: isFavorite ? "heart.fill" : "heart")
}
.accessibilityLabel(isFavorite ? "Remove from favorites" : "Add to favorites")
```### 5.2 逻辑 VoiceOver 导航顺序

确保 VoiceOver 按逻辑顺序读取元素。当视觉布局与阅读顺序不匹配时，使用 .accessibilitySortPriority() 进行调整。```swift
HStack {
    Text("$49.99")
        .accessibilitySortPriority(2)
    Text("Premium Plan")
        .accessibilitySortPriority(1)
}
```### 5.3 支持粗体文本

当用户在“设置”中启用粗体文本时，SwiftUI 文本样式会自动处理此问题。自定义文本必须响应“UIAccessibility.isBoldTextEnabled”。

### 5.4 支持减少运动

启用“减少运动”时禁用装饰动画和视差。```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

var body: some View {
    CardView()
        .animation(reduceMotion ? nil : .spring(duration: 0.4), value: expanded)
}
```### 5.5 支持增加对比度

当用户启用“增加对比度”时，请确保自定义颜色具有更高对比度的变体。使用`@Environment(\.colorSchemeContrast)`进行检测。

### 5.6 不要仅通过颜色、形状或位置传达信息

必须通过多种渠道获取信息。将视觉指示器与文本或辅助功能描述配对。

### 5.7 所有手势的替代交互

每个自定义手势都必须为无法执行复杂手势的用户提供等效的基于点击或基于菜单的替代方案。

### 5.8 支持开关控制和全键盘访问

确保所有交互均适用于开关控制（外部开关）和完整键盘访问（蓝牙键盘）。测试导航顺序和焦点行为。

---

## 6. 手势和输入

**影响：** 高

### 6.1 使用标准手势

坚持用户已经知道的手势：

- **点击** — 选择项目，触发按钮
- **长按** — 显示上下文菜单，进入编辑模式
- **水平滑动** — 列出行操作（删除/存档）、后退导航
- **垂直滑动** - 滚动内容，关闭工作表
- **捏合** — 缩放图像/地图
- **旋转** — 调整角度（照片、地图）

### 6.2 切勿覆盖系统手势

iOS 保留这些边缘手势——不拦截：

- 左边缘滑动 → 返回导航
- 左上拉→通知中心
- 右上角拉→控制中心
- 底部边缘滑动→主页/应用程序切换器

### 6.3 自定义手势必须是可发现的

如果您添加自定义手势，请提供视觉提示（例如抓取手柄），并确保该操作也可以通过可见的按钮或菜单项进行操作。

### 6.4 支持所有输入法

首先针对触摸进行设计，但也支持硬件键盘、辅助设备（开关控制、头部跟踪）和指针输入。

---

## 7. 组件

**影响：** 高

### 7.1 按钮样式

适当使用内置按钮样式：```swift
VStack(spacing: 16) {
    Button("Checkout") { checkout() }
        .buttonStyle(.borderedProminent)
    
    Button("Add to Wishlist") { addToWishlist() }
        .buttonStyle(.bordered)
    
    Button("Remove Item", role: .destructive) { removeItem() }
}
```### 7.2 警报 — 仅重要信息

对于需要做出决策的关键信息，请谨慎使用警报。更喜欢 2 个按钮；最多 3 个。```swift
.alert("Discard Draft?", isPresented: $showDiscardAlert) {
    Button("Discard", role: .destructive) { discardDraft() }
    Button("Keep Editing", role: .cancel) { }
} message: {
    Text("Your unsaved changes will be lost.")
}
```### 7.3 范围任务表

提供独立任务的工作表。始终提供一种关闭方式（关闭按钮或向下滑动）。```swift
.sheet(isPresented: $showEditor) {
    NavigationStack {
        EditorView()
            .navigationTitle("Edit Profile")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showEditor = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { saveProfile() }
                }
            }
    }
    .presentationDetents([.medium, .large])
    .presentationDragIndicator(.visible)
}
```### 7.4 列表 — iOS 应用程序的基础

大多数 iOS 应用程序都是列表（“90% 的移动设计是列表设计”）。

**列表样式：**
- `.insetGrouped` — 现代默认值（圆角、边距）
- `.grouped` — 传统分组部分
- `.plain` — 边到边的行
- `.sidebar` — 三列 iPad 布局

**滑动操作：**
- 引导滑动 → 积极行动（标记已读、存档）
- 尾随滑动 → 破坏性操作（最右侧删除）
- 每侧最多 3-4 个动作

**行配件：**
- V 形 → 表示导航
- 复选标记 → 显示选择
- 详细信息按钮 → 不带导航的附加信息```swift
List {
    Section("Notifications") {
        ForEach(notifications) { notification in
            NotificationRow(notification: notification)
                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                    Button(role: .destructive) {
                        delete(notification)
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                    
                    Button {
                        markRead(notification)
                    } label: {
                        Label("Read", systemImage: "envelope.open")
                    }
                    .tint(.blue)
                }
                .swipeActions(edge: .leading) {
                    Button {
                        pin(notification)
                    } label: {
                        Label("Pin", systemImage: "pin")
                    }
                    .tint(.orange)
                }
        }
    }
}
.listStyle(.insetGrouped)
```### 7.5 选项卡栏行为

- 使用 SF 符号作为选项卡图标 — 所选选项卡的填充变体，未选择的轮廓
- 在选项卡内更深层次导航时切勿隐藏选项卡栏
- 使用“.badge()”标记重要计数```swift
NotificationsView()
    .tabItem {
        Label("Notifications", systemImage: "bell")
    }
    .badge(unreadCount)
```### 7.6 搜索

使用“.searchable()”进行搜索。提供搜索建议并支持最近的搜索。```swift
NavigationStack {
    List(searchResults) { item in
        ItemRow(item: item)
    }
    .searchable(text: $query, prompt: "Search products")
    .searchSuggestions {
        ForEach(recentSearches, id: \.self) { term in
            Text(term)
                .searchCompletion(term)
        }
    }
}
```### 7.7 上下文菜单

使用上下文菜单（长按）进行辅助操作。切勿使用上下文菜单作为访问操作的唯一方式。```swift
ImageThumbnail(image: image)
    .contextMenu {
        Button { shareImage(image) } label: {
            Label("Share", systemImage: "square.and.arrow.up")
        }
        Button { copyImage(image) } label: {
            Label("Copy", systemImage: "doc.on.doc")
        }
        Divider()
        Button(role: .destructive) { deleteImage(image) } label: {
            Label("Delete", systemImage: "trash")
        }
    }
```### 7.8 表格和输入

**文本字段：**
- 最小高度 44pt
- 将键盘类型与输入相匹配（`.emailAddress`、`.numberPad`、`.URL`）
- 输入文本时清除按钮
- 占位符使用“.quaternary”标签颜色```swift
Form {
    Section("Account") {
        TextField("Email", text: $email)
            .textContentType(.emailAddress)
            .keyboardType(.emailAddress)
            .autocapitalization(.none)
        
        SecureField("Password", text: $password)
            .textContentType(.password)
    }
    
    Section {
        Button("Sign In") { signIn() }
            .disabled(email.isEmpty || password.isEmpty)
    }
}
```**选择器：**
- 内联 → 3-7 个选项
- 菜单 → 2-5 个选项 (iOS 14+)
- 轮盘 → 日期/时间或长列表

### 7.9 进度指标

- 确定具有已知持续时间的操作的“ProgressView(value:total:)”
- 不确定的“ProgressView()”持续时间未知
- 切勿用旋转器挡住整个屏幕```swift
VStack {
    ProgressView(value: uploadProgress, total: 1.0)
        .progressViewStyle(.linear)
    
    Text("\(Int(uploadProgress * 100))% uploaded")
        .font(.caption)
        .foregroundStyle(.secondary)
}
```---

## 8. 模式

**影响：** 中

### 8.1 入门 — 最多 3 页，可跳过

保持引导页数不超过 3 页。始终提供跳过选项。推迟登录，直到用户需要经过身份验证的功能。```swift
TabView(selection: $currentPage) {
    OnboardingPage(icon: "sparkles", title: "Smart Features", description: "...")
        .tag(0)
    OnboardingPage(icon: "bell.badge", title: "Stay Notified", description: "...")
        .tag(1)
    OnboardingPage(icon: "lock.shield", title: "Private & Secure", description: "...")
        .tag(2)
}
.tabViewStyle(.page)
.overlay(alignment: .topTrailing) {
    Button("Skip") { finishOnboarding() }
        .padding()
}
```### 8.2 加载 — 骨架视图，无阻塞旋转器

使用与正在加载的内容的布局相匹配的骨架/占位符视图。切勿显示全屏阻塞旋转器。```swift
if isLoading {
    ForEach(0..<5, id: \.self) { _ in
        ArticleRowPlaceholder()
            .redacted(reason: .placeholder)
    }
} else {
    ForEach(articles) { article in
        ArticleRow(article: article)
    }
}
```### 8.3 启动屏幕 — 匹配第一个屏幕

启动故事板必须在视觉上与应用程序的初始屏幕匹配。没有醒目的徽标，没有品牌屏幕。这创造了即时启动的感觉。

### 8.4 情态——谨慎使用

仅当用户必须完成或放弃重点任务时才显示模式视图。始终提供明确的解雇行动。切勿将模态框堆叠在模态框之上。

### 8.5 通知 — 仅高价值

仅发送用户真正关心的内容的通知。支持可操作的通知。对通知进行分类，以便用户可以精细地控制它们。

### 8.6 设置放置

- 常用设置：可通过个人资料或齿轮图标访问应用程序内设置屏幕
- 隐私/权限设置：通过 URL 方案遵循系统设置应用程序
- 切勿在应用程序内重复系统级控件

### 8.7 行动表

对于破坏性或多项选择操作：```swift
.confirmationDialog("Delete Photo?", isPresented: $showDelete, titleVisibility: .visible) {
    Button("Delete", role: .destructive) { deletePhoto() }
    Button("Cancel", role: .cancel) { }
} message: {
    Text("This action cannot be undone.")
}
```- 顶部的破坏性动作（红色）
- 在底部取消
- 点击外部即可关闭

### 8.8 下拉刷新

内容更新的标准模式：```swift
List(items) { item in
    ItemRow(item: item)
}
.refreshable {
    await loadNewItems()
}
```### 8.9 触觉反馈

为重要动作提供触觉响应：

|发电机|用途 |
|----------|------|
| `UIImpactFeedbackGenerator` |物理影响（.轻、.中、.重）|
| `UINotificationFeedbackGenerator` |成功、警告、错误 |
| `UISelectionFeedbackGenerator` |选择更改 |```swift
Button("Complete") {
    let feedback = UINotificationFeedbackGenerator()
    feedback.notificationOccurred(.success)
    markComplete()
}
```---

## 9. 隐私和权限

**影响：** 高

### 9.1 在上下文中请求权限

在用户执行需要的操作时请求权限，而不是在应用程序启动时请求权限。```swift
Button("Take Photo") {
    AVCaptureDevice.requestAccess(for: .video) { granted in
        if granted {
            showCamera = true
        }
    }
}
```### 9.2 系统提示前说明

在触发系统权限对话框之前显示自定义说明屏幕。系统对话框仅出现一次 - 如果用户拒绝，应用程序必须将他们引导至“设置”。```swift
struct LocationPermissionView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "location.fill")
                .font(.system(size: 48))
                .foregroundStyle(.blue)
            
            Text("Find Nearby Places")
                .font(.title2.bold())
            
            Text("We use your location to show relevant results. Your location is never stored or shared.")
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            
            Button("Enable Location") {
                locationManager.requestWhenInUseAuthorization()
            }
            .buttonStyle(.borderedProminent)
            
            Button("Not Now") { dismiss() }
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}
```### 9.3 支持使用 Apple 登录

如果应用程序提供任何第三方登录（Google、Facebook），则还必须提供“使用 Apple 登录”。将其作为第一个选项呈现。

### 9.4 除非必要，否则不需要帐户

让用户在要求登录之前探索该应用程序。仅控制真正需要身份验证的功能（购买、同步、社交功能）。

### 9.5 应用程序跟踪透明度

如果您跨应用程序或网站跟踪用户，请显示 ATT 提示。尊重拒绝——不要降低选择退出的用户的体验。

### 9.6 一次性访问的位置按钮

对于需要一次定位而不需要持续请求权限的操作，请使用“LocationButton”。```swift
LocationButton(.currentLocation) {
    fetchNearbyResults()
}
.symbolVariant(.fill)
.labelStyle(.titleAndIcon)
```---

## 10. 系统集成

**影响：** 中

### 10.1 用于查看数据的小部件

使用 WidgetKit 提供小部件，供用户经常检查的信息。小部件不具有交互性（除了点击打开应用程序之外），因此显示最有用的快照。

### 10.2 应用程序关键操作快捷方式

定义应用程序快捷方式，以便用户可以从 Siri、Spotlight 和快捷方式应用程序触发关键操作。```swift
struct MyAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: QuickAddIntent(),
            phrases: ["Add item in \(.applicationName)"],
            shortTitle: "Quick Add",
            systemImageName: "plus.circle"
        )
    }
}
```### 10.3 聚光灯索引

使用“CSSearchableItem”索引应用内容，以便用户可以从 Spotlight 搜索中找到它。

### 10.4 共享表集成

支持用户可能想要发送到其他地方的内容的系统共享表。```swift
ShareLink(item: article.url, subject: Text(article.title)) {
    Label("Share Article", systemImage: "square.and.arrow.up")
}
```### 10.5 现场活动

使用实时活动和动态岛进行实时、有时限的活动（交付跟踪、体育比分、锻炼）。

### 10.6 优雅地处理中断

当被电话、Siri 调用、通知、应用程序切换器或 FaceTime SharePlay 打断时，保存状态并优雅地暂停。```swift
@Environment(\.scenePhase) private var scenePhase

var body: some View {
    ContentView()
        .onChange(of: scenePhase) { _, newPhase in
            switch newPhase {
            case .active:
                resumeActivity()
            case .inactive:
                pauseActivity()
            case .background:
                saveState()
            @unknown default:
                break
            }
        }
}
```---

## 快速参考

### 导航和结构

|组件|何时使用 |
|------------|-------------|
| `TabView` | 3-5 主要应用程序部分 |
| `NavigationStack` |分层内容钻取 |
| `.sheet` |需要用户完成的重点任务 |
| `.alert` |阻碍工作流程的决策 |
| `.contextMenu` |额外的行动（始终提供替代方案）|

### 数据显示

|组件|何时使用 |
|------------|-------------|
| `列表` |带部分的可滚动行 |
| `LazyVGrid` / `LazyHGrid` |网格布局 |
| `.可搜索` |可过滤的内容 |
| `进度视图` |加载或任务进度|

### 用户输入

|组件|何时使用 |
|------------|-------------|
| `文本字段` |单行文本|
| `文本编辑器` |多行文本|
| `选择器` |从选项中选择 |
| `切换` |二进制开/关选择 |
| `步进器` |数字递增/递减|

### 系统特点

|组件|何时使用 |
|------------|-------------|
| `共享链接` |内容分享|
| `位置按钮` |一次性位置访问 |
| `照片选择器` |图片选择|
| `UIImpactFeedbackGenerator` |触觉反应 |

---

## 反模式

避免这些常见的 HIG 违规行为：

|图案|问题 |解决方案 |
|---------|---------|----------|
|汉堡/抽屉菜单|隐藏导航，用户错过功能 |使用具有 3-5 个选项卡的 TabView |
|断背滑动 |自定义手势阻止系统导航|保持NavigationStack默认行为|
|全屏旋转器 |应用程序感觉冻结，没有进度指示 |将骨架视图与“.redacted()”一起使用 |
|标志闪屏|人为延迟，浪费用户时间|将启动屏幕与第一个视图匹配 |
|启动时的权限 |用户在没有上下文的情况下否认|在需要采取行动时提出请求 |
|固定字体大小 |破坏动态类型、可访问性问题 |使用 `.font(.body)` 语义样式 |
|仅颜色状态 |色盲用户错过信息|添加图标或文本标签 |
|警惕过度使用 |中断次要信息流程 |使用内联消息或横幅 |
|隐藏标签栏 |用户失去导航上下文 |保持标签栏在推送时可见 |
|不安全区域的内容 |隐藏在缺口下的文字/动态岛|只忽略背景的安全区域 |
|无模式解雇 |用户被困在视野中|添加取消按钮并滑动关闭 |
|仅手势操作 |无障碍用户被阻止 |提供按钮/菜单替代方案 |
|小点击目标|频繁误按 |最小 44x44pt 命中区域 |
|嵌套情态动词 |导航混乱|在单个工作表中使用 NavigationStack |
|硬编码颜色 |深色模式下损坏 |使用语义颜色或资产变体 |

---

## 审核清单

SwiftUI 应用程序的代码审查清单：

### 布局
- [ ] 交互元素的最小触摸面积为 44pt
- [ ] 基本内容保持在安全区域范围内
- [ ] 主要动作定位为单手使用（底部）
- [ ] UI 适用于 iPhone SE 到 Pro Max 屏幕尺寸
- [ ] 间距使用 8pt 增量

### 导航
- [ ] 主要部分使用底部 TabView（3-5 个选项卡）
- [ ] 无抽屉/汉堡导航
- [ ] 根视图显示大导航标题
- [ ] 系统返回手势不被阻止
- [ ] 切换时选项卡状态保持不变

### 文本和字体
- [ ] 文本使用语义样式（`.body`、`.headline` 等）
- [ ] 动态类型适用于所有尺寸，包括可访问性
- [ ] 内容重排，大尺寸时不截断
- [ ] 文字不得低于 11pt

### 颜色
- [ ] 使用 `.primary`、`.secondary`、`Color(.systemBackground)`
- [ ] 自定义颜色在资源中具有浅色/深色变体
- [ ] 状态指示器将颜色与图标/文本相结合
- [ ] 文本对比度符合 WCAG AA

### 辅助功能
- [ ] 图标按钮有 `.accessibilityLabel()`
- [ ] VoiceOver 顺序与逻辑流程匹配
- [ ] 动画尊重 `accessibilityReduceMotion`
- [ ] 所有动作都有非手势替代方案

### 模态框和警报
- [ ] 仅为关键决策保留的警报
- [ ] 工作表提供明确的解雇机制
- [ ] 无堆叠模态演示

### 权限
- [ ] 使用时请求的权限
- [ ] 使用预许可说明屏幕
- [ ] 核心功能无需登录即可使用

---

## iPad适配

iPad 用户期望不同的交互模式：

**布局：** 使用 `NavigationSplitView` 作为主从结构：```swift
NavigationSplitView(columnVisibility: $columnVisibility) {
    SidebarView()
} content: {
    ListContentView()
} detail: {
    DetailView()
}
.navigationSplitViewStyle(.balanced)
```**演示：** 操作表自动变为弹出窗口，但您可以强制弹出窗口：```swift
.popover(isPresented: $showOptions) {
    OptionsView()
}
```**键盘：** 为高级用户添加快捷键：```swift
.keyboardShortcut("n", modifiers: .command)  // Cmd+N
```**拖放：** 启用跨应用程序数据传输：```swift
.draggable(item)
.dropDestination(for: Item.self) { items, location in
    handleDrop(items)
    return true
}
```---

## 发布前验证

在发货前运行这些场景：

**视觉一致性：**
- 在亮/暗模式之间切换——所有内容都保持可读吗？
- 将动态类型调至最大——布局是否适应或破坏？
- 启用粗体文本 — 自定义字体是否有响应？

**交互质量：**
- 你能仅使用 VoiceOver 完成所有动作吗？
- 第一次尝试时所有按钮是否都感觉可以点击（没有误点击）？
- 向后滑动是否可以在导航中随处使用？

**边缘情况：**
- iPhone SE 的小屏幕上会发生什么？
- 连接键盘的 iPad 上会发生什么？
- 运行中网络出现故障时会出现什么情况？
- 如果用户拒绝权限会发生什么？

**平台合规性：**
- 您是否使用 SF 符号而不是自定义图标 PNG？
- 语义调色板或资产目录中的所有颜色是否都有变体？
- 破坏性行为是否需要明确确认？

---

*SwiftUI、SF Symbols、Dynamic Island 和 Apple 是 Apple Inc. 的商标。*