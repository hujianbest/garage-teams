---
名称：flutter-dev
描述：|
  Flutter 跨平台开发指南，涵盖 widget 模式、Riverpod/Bloc 状态管理、GoRouter 导航、性能优化和特定于平台的实现。包括 const 优化、响应式布局、测试策略和 DevTools 分析。
  使用场合：构建 Flutter 应用程序、实现状态管理（Riverpod/Bloc）、设置 GoRouter 导航、创建自定义小部件、优化性能、编写小部件测试、跨平台开发。
许可证：麻省理工学院
元数据：
  版本：“1.0.0”
  类别： 手机
  来源：
    - 颤动文档
    - Riverpod 文档
    - Bloc 库文档
---

# Flutter 开发指南

使用 Flutter 3 和 Dart 构建跨平台应用程序的实用指南。专注于经过验证的模式、状态管理和性能优化。

## 快速参考

### 小部件模式

|目的|组件|
|--------|------------|
|状态管理（简单）| `StateProvider` + `ConsumerWidget` |
|状态管理（复杂） | `NotifierProvider` / `Bloc` |
|异步数据 | `FutureProvider` / `AsyncNotifierProvider` |
|实时流 | `StreamProvider` |
|导航 | `GoRouter` + `context.go/push` |
|响应式布局 | `LayoutBuilder` + 断点 |
|列表展示| `ListView.builder` |
|复杂的滚动 | `CustomScrollView` + 条子 |
|挂钩| `HookWidget` + `useState/useEffect` |
|表格 | `Form` + `TextFormField` + 验证 |

### 性能模式

|目的|解决方案 |
|---------|----------|
|防止重建 | `const` 构造函数 |
|选择性更新 | `ref.watch(provider.select(...))` |
|隔离重涂| `重画边界` |
|惰性列表 | `ListView.builder` |
|繁重的计算 | `compute()` 隔离 |
|图像缓存 | `缓存网络图像` |

## 核心原则

### 小部件优化
- 尽可能使用 `const` 构造函数
- 提取静态小部件以单独的 const 类
- 对列表项使用“Key”（ValueKey、ObjectKey）
- 对于状态，更喜欢使用“ConsumerWidget”而不是“StatefulWidget”

### 状态管理
- 用于依赖注入和简单状态的 Riverpod
- Bloc/Cubit 用于事件驱动的工作流程和复杂的逻辑
- 永远不要直接改变状态（创建新实例）
- 使用`select()`来最小化重建

### 布局
- 8 点间距增量（8、16、24、32、48）
- 响应断点：移动设备 (<650)、平板电脑 (650-1100)、桌面设备 (>1100)
- 支持所有屏幕尺寸，布局灵活
- 遵循 Material 3/Cupertino 设计指南

### 性能
- 在优化之前使用 DevTools 进行分析
- 60fps 的目标帧时间 <16ms
- 使用“RepaintBoundary”进行复杂动画
- 使用“compute()”卸载繁重的工作

## 清单

### 小部件最佳实践
- [ ] 所有静态小部件上的 `const` 构造函数
- [ ] 列表项上正确的“Key”
- [ ] `ConsumerWidget` 用于状态相关的小部件
- [ ] `build()` 方法中没有构建小部件
- [ ] 将可重用的小部件提取到单独的文件中

### 状态管理
- [ ] 不可变状态对象
- [ ] `select()` 用于粒度重建
- [ ] 正确的提供商范围
- [ ] 处置控制器和订阅
- [ ] 处理加载/错误状态

### 导航
- [ ] 具有类型化路由的 GoRouter
- [ ] 通过重定向进行身份验证守卫
- [ ] 深层链接支持
- [ ] 跨路线状态保存

### 性能
- [ ] Profile模式测试（`flutter run --profile`）
- [ ] <16ms 帧渲染时间
- [ ] 没有不必要的重建（DevTools 检查）
- [ ] 缓存图像并调整大小
- [ ] 隔离中的大量计算

### 测试
- [ ] UI 组件的 Widget 测试
- [ ] 业务逻辑单元测试
- [ ] 用户流程集成测试
- [ ] 使用 `blocTest()` 进行 Bloc 测试

## 参考文献

|主题 |参考|
|------|----------|
|小部件模式、const 优化、响应式布局 | [小部件模式](references/widget-patterns.md) |
| Riverpod 提供程序、通知程序、异步状态 | [Riverpod 状态管理](references/riverpod-state.md) |
|块、肘、事件驱动状态 | [Bloc 状态管理](references/bloc-state.md) |
| GoRouter 设置、路由、深度链接 | [GoRouter 导航](references/gorouter-navigation.md) |
|基于特征的结构、依赖关系 | [项目结构](references/project-struct.md) |
|分析、const 优化、DevTools | [性能优化](references/performance.md) |
|小部件测试、集成测试、模拟 | [测试策略](references/testing.md) || iOS/Android/Web 特定实现 | [平台集成](参考资料/平台特定.md) |
|隐式/显式动画、英雄、过渡 | [动画](references/animations.md) |
| Dio、拦截器、错误处理、缓存 | [网络](参考文献/networking.md) |
|表单验证、FormField、输入格式化程序 | [表单](references/forms.md) |
| i18n、flutter_localizations、国际 | [本地化](references/localization.md) |

---

Flutter、Dart、Material Design 和 Cupertino 分别是 Google LLC 和 Apple Inc. 的商标。 Riverpod、Bloc 和 GoRouter 是各自维护者的开源软件包。