# 性能优化

Flutter 性能指南，涵盖分析、const 优化和 DevTools 分析。

## 分析命令```bash
# Run in profile mode (required for accurate measurements)
flutter run --profile

# Analyze code issues
flutter analyze

# Launch DevTools
flutter pub global activate devtools
flutter pub global run devtools

# Build release for testing
flutter build apk --release
flutter build ios --release
```## 常量小部件优化

防止不必要的重建的最重要的优化：```dart
// BAD - Creates new objects every build
Widget build(BuildContext context) {
  return Container(
    padding: EdgeInsets.all(16),  // New object each time
    child: Text('Hello'),          // New widget each time
  );
}

// GOOD - Const prevents rebuilds
Widget build(BuildContext context) {
  return Container(
    padding: const EdgeInsets.all(16),
    child: const Text('Hello'),
  );
}
```### 提取常量小部件```dart
// BAD - Inline static content
class MyScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(Icons.star, size: 48),
        Text('Welcome'),
        Text('Description text here'),
      ],
    );
  }
}

// GOOD - Extract to const classes
class MyScreen extends StatelessWidget {
  const MyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        _Header(),
        _Description(),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Icon(Icons.star, size: 48),
        Text('Welcome'),
      ],
    );
  }
}
```## 选择性观察提供商```dart
// BAD - Rebuilds on any user change
class UserAvatar extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(userProvider);
    return CircleAvatar(
      backgroundImage: NetworkImage(user.avatarUrl),
    );
  }
}

// GOOD - Only rebuilds when avatarUrl changes
class UserAvatar extends ConsumerWidget {
  const UserAvatar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final avatarUrl = ref.watch(userProvider.select((u) => u.avatarUrl));
    return CircleAvatar(
      backgroundImage: NetworkImage(avatarUrl),
    );
  }
}
```## 重绘边界

隔离昂贵的小部件以防止不必要的重新绘制：```dart
// Isolate complex animated widgets
RepaintBoundary(
  child: ComplexAnimatedWidget(),
)

// Isolate frequently updating widgets
RepaintBoundary(
  child: StreamBuilder<int>(
    stream: counterStream,
    builder: (context, snapshot) => Text('${snapshot.data}'),
  ),
)
```## 列表优化```dart
// BAD - Builds all items upfront
ListView(
  children: items.map((item) => ItemWidget(item: item)).toList(),
)

// GOOD - Lazy loading with builder
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ItemWidget(
      key: ValueKey(items[index].id),
      item: items[index],
    );
  },
)

// For heterogeneous content
ListView.separated(
  itemCount: items.length,
  separatorBuilder: (_, __) => const Divider(),
  itemBuilder: (context, index) => ItemWidget(item: items[index]),
)
```## 图像优化```dart
// Use cached_network_image for network images
CachedNetworkImage(
  imageUrl: url,
  placeholder: (_, __) => const ShimmerPlaceholder(),
  errorWidget: (_, __, ___) => const Icon(Icons.error),
  memCacheWidth: 200,
  memCacheHeight: 200,
)

// Resize images in memory
Image.network(
  url,
  cacheWidth: 200,   // Decode at smaller size
  cacheHeight: 200,  // Saves memory
)

// Precache images
precacheImage(NetworkImage(url), context);
```## 繁重计算```dart
// BAD - Blocks UI thread
void processData() {
  final result = heavyComputation(data);  // UI freezes
  updateUI(result);
}

// GOOD - Run in isolate
Future<void> processData() async {
  final result = await compute(heavyComputation, data);
  updateUI(result);
}

// For multiple operations
Future<void> processMultiple() async {
  final results = await Future.wait([
    compute(process1, data1),
    compute(process2, data2),
    compute(process3, data3),
  ]);
}
```## 动画表演```dart
// Use AnimatedBuilder for custom animations
AnimatedBuilder(
  animation: controller,
  builder: (context, child) {
    return Transform.rotate(
      angle: controller.value * 2 * pi,
      child: child,  // Child not rebuilt
    );
  },
  child: const ExpensiveWidget(),
)

// Prefer implicit animations for simple cases
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  width: expanded ? 200 : 100,
  child: const Content(),
)
```## DevTools 分析

### 关键指标

|公制|目标|超过时采取的行动 |
|--------|--------|--------------------|
|帧时间| < 16 毫秒 (60 帧/秒) |轮廓构建/油漆 |
|构建时间| < 8 毫秒 |添加 const，提取小部件 |
|绘画时间| < 8 毫秒 |添加重绘边界 |
|内存|稳定|检查是否有泄漏 |

### 常见问题

|问题 |症状|解决方案 |
|--------|---------|----------|
|昂贵的构建|构建时间长 |提取 const 小部件 |
|过度重涂 |喷漆时间长 |添加重绘边界 |
|内存泄漏 |记忆力增长|处置控制器 |
|詹克 |丢帧 |使用计算（） |

## 绩效检查表

|检查 |解决方案 |
|--------|----------|
|不必要的重建|添加 `const`，使用 `select()` |
|大清单 |使用`ListView.builder` |
|图片加载 |使用`cached_network_image` |
|繁重的计算 |使用 `compute()` |
|动画中的卡顿|使用“RepaintBoundary” |
|内存泄漏 |处置控制器，取消订阅 |
|网络通话|缓存响应、反跳请求 |
|启动时间|延迟初始化、延迟加载|

## 处理模式```dart
class MyWidget extends StatefulWidget {
  const MyWidget({super.key});

  @override
  State<MyWidget> createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  late final TextEditingController _controller;
  late final StreamSubscription _subscription;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _subscription = stream.listen(handleData);
  }

  @override
  void dispose() {
    _controller.dispose();
    _subscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Container();
}
```---

*Flutter 和 DevTools 是 Google LLC 的商标。*