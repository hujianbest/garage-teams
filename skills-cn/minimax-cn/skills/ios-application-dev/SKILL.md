---
名称：ios-应用程序-dev
描述：|
  iOS 应用程序开发指南，涵盖 UIKit、SnapKit 和 SwiftUI。包括触摸目标、安全区域、导航模式、动态类型、深色模式、辅助功能、集合视图、常见 UI 组件和 SwiftUI 设计指南。有关特定主题的详细参考，请参阅参考文件。
  使用场合：开发 iOS 应用程序、实现 UI、审查 iOS 代码、使用 UIKit/SnapKit/SwiftUI 布局、构建 iPhone 界面、Swift 移动开发、Apple HIG 合规性、iOS 辅助功能实现。
许可证：麻省理工学院
元数据：
  作者：MiniMax-OpenSource
  版本：“1.0.0”
  类别： 手机
  来源：
    - Apple 人机界面指南
    - 苹果开发者文档
---

# iOS 应用程序开发指南

使用 UIKit、SnapKit 和 SwiftUI 构建 iOS 应用程序的实用指南。专注于经过验证的模式和 Apple 平台惯例。

## 快速参考

### UIKit

|目的|组件|
|--------|------------|
|主要部分 | `UITabBarController` |
|深入探究 | `UINavigationController` |
|重点任务|表格演示 |
|关键选择| `UIAlertController` |
|次要行动| `UIContextMenuInteraction` |
|列表内容 | `UICollectionView` + `DiffableDataSource` |
|分段列表 | `DiffableDataSource` + `headerMode` |
|网格布局| `UICollectionViewCompositionalLayout` |
|搜索 | `UISearchController` |
|分享 | `UIActivityViewController` |
|地点（一次）| `CLLocationButton` |
|反馈 | `UIImpactFeedbackGenerator` |
|线性布局 | `UIStackView` |
|定制形状| `CAShapeLayer` + `UIBezierPath` |
|渐变| `CAGradientLayer` |
|现代按钮| `UIButton.Configuration` |
|动态文本| `UIFontMetrics` + `preferredFont` |
|深色模式 |语义颜色（`.systemBackground`、`.label`）|
|权限 |上下文请求 + `AVCaptureDevice` |
|生命周期| `UIApplication` 通知 |

### SwiftUI

|目的|组件|
|--------|------------|
|主要部分 | `TabView` + `tabItem` |
|深入探究 | `NavigationStack` + `NavigationPath` |
|重点任务| `.sheet` + `presentationDetents` |
|关键选择| `.alert` |
|次要行动| `.contextMenu` |
|列表内容 | `列表` + `.insetGrouped` |
|搜索 | `.可搜索` |
|分享 | `共享链接` |
|地点（一次）| `位置按钮` |
|反馈 | `UIImpactFeedbackGenerator` |
|进展（已知）| `ProgressView(值:总计:)` |
|进展（未知）| `ProgressView()` |
|动态文本| `.font(.body)` 语义样式 |
|深色模式 | `.primary`、`.secondary`、`颜色（.systemBackground）` |
|场景生命周期 | `@Environment(\.scenePhase)` |
|减少运动| `@Environment(\.accessibilityReduceMotion)` |
|动态型| `@Environment(\.dynamicTypeSize)` |

## 核心原则

### 布局
- 触摸目标 >= 44pt
- 安全区域内的内容（SwiftUI 默认情况下尊重，仅对背景使用 `.ignoresSafeArea()`）
- 使用 8 点间距增量（8、16、24、32、40、48）
- 拇指区域的主要动作
- 支持所有屏幕尺寸（iPhone SE 375pt 至 Pro Max 430pt）

### 版式
- UIKit: `preferredFont(forTextStyle:)` + `adjustsFontForContentSizeCategory = true`
- SwiftUI：语义文本样式 `.headline`、`.body`、`.caption`
- 自定义字体：`UIFontMetrics` / `Font.custom(_:size:relativeTo:)`
- 根据可访问性大小调整布局（最小 11pt）

### 颜色
- 使用语义系统颜色（`.systemBackground`、`.label`、`.primary`、`. secondary`）
- 自定义颜色的资产目录变体（任何/深色外观）
- 没有纯颜色信息（与图标或文本配对）
- 普通文本对比度 >= 4.5:1，大文本对比度 >= 3:1

### 辅助功能
- 图标按钮上的标签（`.accessibilityLabel()`）
- 减少运动（`@Environment(\.accessibilityReduceMotion)`）
- 逻辑阅读顺序（`.accessibilitySortPriority()`）
- 支持粗体文本，增加对比度偏好

### 导航
- 标签栏（3-5 个部分）在导航期间保持可见
- 向后滑动有效（切勿覆盖系统手势）
- 跨选项卡保存状态（`@SceneStorage`、`@State`）
- 切勿使用汉堡菜单

### 隐私和权限
- 在上下文中请求权限（不是在启动时）
- 系统对话框前的自定义解释
- 支持使用Apple登录
- 尊重 ATT 否认

## 清单

### 布局
- [ ] 触摸目标 >= 44pt
- [ ] 安全区域内的内容
- [ ] 拇指区域的主要动作（下半部分）
- [ ] 适用于所有屏幕尺寸的灵活宽度（SE 到 Pro Max）- [ ] 间距与 8pt 网格对齐

### 版式
- [ ] 语义文本样式或 UIFontMetrics 缩放的自定义字体
- [ ] 支持动态类型，最大可达可访问性大小
- [ ] 大尺寸布局回流（无截断）
- [ ] 最小文字大小 11pt

### 颜色
- [ ] 语义系统颜色或浅色/深色资产变体
- [ ] 深色模式是有意为之（不仅仅是倒置）
- [ ] 没有仅颜色信息
- [ ] 文本对比度 >= 4.5:1（正常）/3:1（大）
- [ ] 交互元素的单一强调色

### 辅助功能
- [ ] 所有交互元素上的 VoiceOver 标签
- [ ] 逻辑阅读顺序
- [ ] 尊重粗体文本偏好
- [ ] 减少运动禁用装饰动画
- [ ] 所有手势都有备用访问路径

### 导航
- [ ] 3-5 个顶级部分的选项卡栏
- [ ] 没有汉堡/抽屉菜单
- [ ] 标签栏在导航期间保持可见
- [ ] 向后滑动始终有效
- [ ] 跨选项卡保留状态

### 组件
- [ ] 仅针对关键决策发出警报
- [ ] 工作表具有关闭路径（按钮和/或滑动）
- [ ] 列表行 >= 44pt 高
- [ ] 破坏性按钮使用 `.destroy` 角色

### 隐私
- [ ] 在上下文中请求的权限（不是在启动时）
- [ ] 系统权限对话框前的自定义说明
- [ ] 使用其他提供商提供的 Apple 登录
- [ ] 无需帐户即可使用的基本功能
- [ ] 如果遵循跟踪、拒绝则显示 ATT 提示

### 系统集成
- [ ] 应用程序优雅地处理中断（通话、背景、Siri）
- [ ] 为 Spotlight 建立索引的应用内容
- [ ] 共享表可用于共享内容

## 参考文献

|主题 |参考|
|------|----------|
|触摸目标、安全区域、CollectionView | [布局系统](references/layout-system.md) |
| TabBar、NavigationController、模态 | [导航模式](references/navigation-patterns.md) |
| StackView、按钮、警报、搜索、上下文菜单 | [UIKit 组件](references/uikit-components.md) |
| CAShapeLayer、CAGradientLayer、核心动画 | [图形与动画](references/graphics-animation.md) |
|动态类型、语义颜色、旁白 | [辅助功能](参考文献/accessibility.md) |
|权限、位置、共享、生命周期、触觉 | [系统集成](references/system-integration.md) |
|金属着色器和 GPU | [金属着色器参考](references/metal-shader.md) |
| SwiftUI HIG、组件、模式、反模式 | [SwiftUI 设计指南](references/swiftui-design-guidelines.md) |
|可选、协议、异步/等待、ARC、错误处理 | [Swift 编码标准](references/swift-coding-standards.md) |

---

Swift、SwiftUI、UIKit、SF Symbols、Metal 和 Apple 是 Apple Inc. 的商标。SnapKit 是其各自所有者的商标。