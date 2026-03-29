# 动画

Flutter 动画模式涵盖隐式动画、显式动画、英雄过渡和页面过渡。

## 隐式动画

使用隐式动画进行简单的属性更改：```dart
class ImplicitAnimationExample extends StatefulWidget {
  const ImplicitAnimationExample({super.key});

  @override
  State<ImplicitAnimationExample> createState() => _ImplicitAnimationExampleState();
}

class _ImplicitAnimationExampleState extends State<ImplicitAnimationExample> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => setState(() => _expanded = !_expanded),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
        width: _expanded ? 200 : 100,
        height: _expanded ? 200 : 100,
        decoration: BoxDecoration(
          color: _expanded ? Colors.blue : Colors.red,
          borderRadius: BorderRadius.circular(_expanded ? 16 : 8),
        ),
        child: const Center(child: Text('Tap me')),
      ),
    );
  }
}
```### 常见的隐式小部件

|小部件 |动画 |
|--------|----------|
| `动画容器` |尺寸、颜色、填充物、装饰 |
| `动画不透明度` |不透明度|
| `动画填充` |衬垫|
| `动画定位` |在堆栈中的位置 |
| `动画对齐` |对齐|
| `动画交叉淡入淡出` |两个小部件之间的交叉淡入淡出 |
| `动画切换器` |子部件之间的转换 |
| `AnimatedDefaultTextStyle` |文字样式|
| `动画比例` |尺度变换 |
| `动画旋转` |旋转变换|
| `动画幻灯片` |滑动偏移|

### 动画切换器```dart
AnimatedSwitcher(
  duration: const Duration(milliseconds: 300),
  transitionBuilder: (child, animation) {
    return FadeTransition(
      opacity: animation,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 0.1),
          end: Offset.zero,
        ).animate(animation),
        child: child,
      ),
    );
  },
  child: _showFirst
      ? const Icon(Icons.check, key: ValueKey('check'))
      : const Icon(Icons.close, key: ValueKey('close')),
)
```## 显式动画

对复杂、自定义或受控动画使用显式动画：```dart
class ExplicitAnimationExample extends StatefulWidget {
  const ExplicitAnimationExample({super.key});

  @override
  State<ExplicitAnimationExample> createState() => _ExplicitAnimationExampleState();
}

class _ExplicitAnimationExampleState extends State<ExplicitAnimationExample>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scaleAnimation;
  late final Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    _rotationAnimation = Tween<double>(begin: 0, end: 0.1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.elasticOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _controller.forward(),
      onTapUp: (_) => _controller.reverse(),
      onTapCancel: () => _controller.reverse(),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: Transform.rotate(
              angle: _rotationAnimation.value,
              child: child,
            ),
          );
        },
        child: const Card(child: Padding(padding: EdgeInsets.all(24), child: Text('Press me'))),
      ),
    );
  }
}
```### 带 Hook 的动画```dart
import 'package:flutter_hooks/flutter_hooks.dart';

class AnimatedButtonHook extends HookWidget {
  const AnimatedButtonHook({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = useAnimationController(
      duration: const Duration(milliseconds: 300),
    );
    final scale = useAnimation(
      Tween<double>(begin: 1.0, end: 0.95).animate(
        CurvedAnimation(parent: controller, curve: Curves.easeInOut),
      ),
    );

    return GestureDetector(
      onTapDown: (_) => controller.forward(),
      onTapUp: (_) => controller.reverse(),
      onTapCancel: () => controller.reverse(),
      child: Transform.scale(
        scale: scale,
        child: const Card(child: Text('Animated Button')),
      ),
    );
  }
}
```### 交错动画```dart
class StaggeredAnimation extends StatefulWidget {
  const StaggeredAnimation({super.key});

  @override
  State<StaggeredAnimation> createState() => _StaggeredAnimationState();
}

class _StaggeredAnimationState extends State<StaggeredAnimation>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final List<Animation<double>> _itemAnimations;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _itemAnimations = List.generate(5, (index) {
      final start = index * 0.1;
      final end = start + 0.4;
      return Tween<double>(begin: 0, end: 1).animate(
        CurvedAnimation(
          parent: _controller,
          curve: Interval(start, end.clamp(0, 1), curve: Curves.easeOut),
        ),
      );
    });

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(5, (index) {
        return AnimatedBuilder(
          animation: _itemAnimations[index],
          builder: (context, child) {
            return Opacity(
              opacity: _itemAnimations[index].value,
              child: Transform.translate(
                offset: Offset(0, 20 * (1 - _itemAnimations[index].value)),
                child: child,
              ),
            );
          },
          child: ListTile(title: Text('Item $index')),
        );
      }),
    );
  }
}
```## 英雄动画```dart
class HeroSourcePage extends StatelessWidget {
  const HeroSourcePage({super.key});

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
      ),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return GestureDetector(
          onTap: () => context.push('/detail/${item.id}'),
          child: Hero(
            tag: 'hero-${item.id}',
            child: Image.network(item.imageUrl, fit: BoxFit.cover),
          ),
        );
      },
    );
  }
}

class HeroDetailPage extends StatelessWidget {
  final String itemId;

  const HeroDetailPage({super.key, required this.itemId});

  @override
  Widget build(BuildContext context) {
    final item = getItem(itemId);
    return Scaffold(
      body: Column(
        children: [
          Hero(
            tag: 'hero-${item.id}',
            child: Image.network(item.imageUrl, fit: BoxFit.cover),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(item.title, style: Theme.of(context).textTheme.headlineMedium),
          ),
        ],
      ),
    );
  }
}
```### 自定义飞行的英雄```dart
Hero(
  tag: 'avatar-$userId',
  flightShuttleBuilder: (
    flightContext,
    animation,
    flightDirection,
    fromHeroContext,
    toHeroContext,
  ) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        return Material(
          color: Colors.transparent,
          child: CircleAvatar(
            radius: lerpDouble(24, 48, animation.value),
            backgroundImage: NetworkImage(avatarUrl),
          ),
        );
      },
    );
  },
  child: CircleAvatar(radius: 24, backgroundImage: NetworkImage(avatarUrl)),
)
```## 页面转换

### GoRouter 自定义转换```dart
GoRoute(
  path: '/detail/:id',
  pageBuilder: (context, state) {
    return CustomTransitionPage(
      key: state.pageKey,
      child: DetailPage(id: state.pathParameters['id']!),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.05),
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOut,
            )),
            child: child,
          ),
        );
      },
    );
  },
)
```### 常见转换模式```dart
extension PageTransitions on CustomTransitionPage {
  static CustomTransitionPage<T> fade<T>({
    required LocalKey key,
    required Widget child,
  }) {
    return CustomTransitionPage<T>(
      key: key,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(opacity: animation, child: child);
      },
    );
  }

  static CustomTransitionPage<T> slideUp<T>({
    required LocalKey key,
    required Widget child,
  }) {
    return CustomTransitionPage<T>(
      key: key,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 1),
            end: Offset.zero,
          ).animate(CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutCubic,
          )),
          child: child,
        );
      },
    );
  }

  static CustomTransitionPage<T> scale<T>({
    required LocalKey key,
    required Widget child,
  }) {
    return CustomTransitionPage<T>(
      key: key,
      child: child,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return ScaleTransition(
          scale: Tween<double>(begin: 0.9, end: 1).animate(
            CurvedAnimation(parent: animation, curve: Curves.easeOut),
          ),
          child: FadeTransition(opacity: animation, child: child),
        );
      },
    );
  }
}
```### 共享轴过渡```dart
import 'package:animations/animations.dart';

GoRoute(
  path: '/settings',
  pageBuilder: (context, state) {
    return CustomTransitionPage(
      key: state.pageKey,
      child: const SettingsPage(),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return SharedAxisTransition(
          animation: animation,
          secondaryAnimation: secondaryAnimation,
          transitionType: SharedAxisTransitionType.horizontal,
          child: child,
        );
      },
    );
  },
)
```## 常用曲线

|曲线|用途 |
|--------|--------|
| `曲线.easeInOut` |通用（默认）|
| `曲线.easeOut` |减速度（进入）|
| `曲线.easeIn` |加速（退出）|
| `Curves.elasticOut` |弹力效果|
| `Curves.bounceOut` |结束时弹跳 |
| `Curves.fastOutSlowIn` |材质标准|
| `Curves.easeOutCubic` |平稳减速 |

## 动画表演```dart
class PerformantAnimation extends StatelessWidget {
  const PerformantAnimation({super.key});

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: animation,
        builder: (context, child) {
          return Transform.translate(
            offset: Offset(animation.value * 100, 0),
            child: child,
          );
        },
        child: const ExpensiveWidget(),
      ),
    );
  }
}
```### 性能提示

|提示 |实施 |
|-----|----------------|
|使用“child”参数 |将静态内容传递给“AnimatedBuilder”中的“child” |
| `重画边界` |隔离动画小部件 |
|避免“不透明度”小部件 |使用“FadeTransition”代替 |
|更喜欢变换 | “Transform”比布局更改更便宜 |
|预计算值 |在 `initState` 中计算，而不是在 `build` 中计算 |

## 动画清单

|项目 |实施 |
|------|----------------|
|简单的动画|使用隐式小部件 |
|复杂序列|使用`AnimationController` |
|小部件过渡 |带键的“AnimatedSwitcher” |
|跨页元素|具有独特标签的“英雄”|
|页面转换 | `自定义转换页面` |
|性能| `RepaintBoundary` + `child` 参数 |

---

*Flutter 和 Material Design 是 Google LLC 的商标。*