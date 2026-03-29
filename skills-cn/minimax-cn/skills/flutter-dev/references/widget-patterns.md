# 小部件模式

Flutter 小部件最佳实践涵盖常量优化、响应式布局、挂钩和条子模式。

## 优化的 Widget 模式

始终对静态小部件使用“const”构造函数，以防止不必要的重建：```dart
class OptimizedCard extends StatelessWidget {
  final String title;
  final VoidCallback onTap;

  const OptimizedCard({
    super.key,
    required this.title,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
        ),
      ),
    );
  }
}
```### 提取常量小部件```dart
class MyScreen extends StatelessWidget {
  const MyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: const [
        _Header(),
        _Body(),
        _Footer(),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return const Text('Header');
  }
}
```## 响应式布局```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    required this.desktop,
  });

  static const double mobileBreakpoint = 650;
  static const double desktopBreakpoint = 1100;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= desktopBreakpoint) return desktop;
        if (constraints.maxWidth >= mobileBreakpoint) return tablet ?? mobile;
        return mobile;
      },
    );
  }
}
```### 断点参考

|类型 |宽度|用途 |
|------|--------|--------|
|手机 | < 650 点 |单栏，底部导航 |
|平板电脑| 650-1100 点 |两栏，侧边导航可选 |
|桌面| > 1100 点 |多栏、持久导航 |

## 自定义挂钩 (flutter_hooks)```dart
import 'package:flutter_hooks/flutter_hooks.dart';

class CounterWidget extends HookWidget {
  const CounterWidget({super.key});

  @override
  Widget build(BuildContext context) {
    final counter = useState(0);
    final controller = useTextEditingController();
    final isMounted = useIsMounted();

    useEffect(() {
      debugPrint('Widget mounted');
      return () {
        debugPrint('Widget disposed');
      };
    }, const []);

    return Column(
      children: [
        Text('Count: ${counter.value}'),
        ElevatedButton(
          onPressed: () => counter.value++,
          child: const Text('Increment'),
        ),
        TextField(controller: controller),
      ],
    );
  }
}
```### 常用钩子

|钩|目的|
|------|---------|
| `useState` |地方国家管理|
| `使用效果` |清理的副作用|
| `useMemoized` |昂贵的计算缓存|
| `useTextEditingController` |文本字段控制器 |
| `useAnimationController` |动画控制器|
| `useFocusNode` |焦点管理|
| `useIsMounted` |检查小部件是否已安装 |

## 条子图案```dart
CustomScrollView(
  slivers: [
    SliverAppBar(
      expandedHeight: 200,
      pinned: true,
      flexibleSpace: FlexibleSpaceBar(
        title: const Text('Title'),
        background: Image.network(imageUrl, fit: BoxFit.cover),
      ),
    ),
    SliverPadding(
      padding: const EdgeInsets.all(16),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, index) => ListTile(
            key: ValueKey(items[index].id),
            title: Text(items[index].title),
          ),
          childCount: items.length,
        ),
      ),
    ),
    const SliverToBoxAdapter(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('Footer'),
      ),
    ),
  ],
)
```### 棉条类型

|条子|用途 |
|--------|--------|
| `SliverAppBar` |折叠应用栏 |
| `SliverList` |懒惰清单|
| `SliverGrid` |懒惰网格|
| `SliverToBoxAdapter` |单个非银条小部件 |
| `SliverPadding` |添加填充棉条 |
| `剩余的条子填充` |填补剩余空间 |

## 关键使用模式```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    final item = items[index];
    return Dismissible(
      key: ValueKey(item.id),
      child: ListTile(
        key: ValueKey('tile_${item.id}'),
        title: Text(item.title),
      ),
    );
  },
)
```|钥匙类型 |何时使用 |
|----------|-------------|
| `值键` |可用唯一ID |
| `对象键` |对象身份很重要|
| `唯一密钥` |强制重建|
| `全局密钥` |跨树访问状态 |

## 优化清单

|图案|实施 |
|---------|----------------|
|常量小部件 |将 `const` 添加到静态小部件 |
|按键|对列表项使用“ValueKey” |
|选择 | `ref.watch(provider.select(...))` |
|重新绘制边界 |隔离昂贵的重漆|
|列表视图.builder |列表的延迟加载|
|常量构造函数 |尽可能使用 |

---

*Flutter 和 Material Design 是 Google LLC 的商标。*