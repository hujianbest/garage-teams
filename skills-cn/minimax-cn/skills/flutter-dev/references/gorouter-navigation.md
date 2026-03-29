# GoRouter 导航

GoRouter 导航指南，涵盖路由设置、防护、深度链接和 shell 路由。

## 基本设置```dart
import 'package:go_router/go_router.dart';

final goRouter = GoRouter(
  initialLocation: '/',
  debugLogDiagnostics: true,
  redirect: (context, state) {
    final isLoggedIn = /* check auth state */;
    final isAuthRoute = state.matchedLocation.startsWith('/auth');
    
    if (!isLoggedIn && !isAuthRoute) {
      return '/auth/login';
    }
    if (isLoggedIn && isAuthRoute) {
      return '/';
    }
    return null;
  },
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'details/:id',
          name: 'details',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            final extra = state.extra as Map<String, dynamic>?;
            return DetailsScreen(id: id, title: extra?['title']);
          },
        ),
      ],
    ),
    GoRoute(
      path: '/auth/login',
      name: 'login',
      builder: (context, state) => const LoginScreen(),
    ),
  ],
);
```### 应用程序集成```dart
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      routerConfig: goRouter,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
    );
  }
}
```## 导航方法```dart
// Navigate and replace entire stack
context.go('/details/123');

// Navigate and add to stack (can go back)
context.push('/details/123');

// Go back
context.pop();

// Go back with result
context.pop(result);

// Replace current route
context.pushReplacement('/home');

// Navigate with extra data
context.push('/details/123', extra: {'title': 'Item Title'});

// Navigate by name
context.goNamed('details', pathParameters: {'id': '123'});
context.pushNamed('details', pathParameters: {'id': '123'}, extra: data);
```### 导航参考

|方法|行为 |
|--------|----------|
| `context.go()` |导航、替换整个堆栈 |
| `context.push()` |导航、添加到堆栈 |
| `context.pop()` |返回上一级 |
| `context.pushReplacement()` |替换当前路线 |
| `context.goNamed()` |按路线名称导航 |
| `context.canPop()` |检查是否可以返回 |

## Shell 路由（持久 UI）```dart
final goRouter = GoRouter(
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        return ScaffoldWithNavBar(child: child);
      },
      routes: [
        GoRoute(
          path: '/home',
          builder: (_, __) => const HomeScreen(),
        ),
        GoRoute(
          path: '/search',
          builder: (_, __) => const SearchScreen(),
        ),
        GoRoute(
          path: '/profile',
          builder: (_, __) => const ProfileScreen(),
        ),
      ],
    ),
  ],
);

class ScaffoldWithNavBar extends StatelessWidget {
  final Widget child;
  
  const ScaffoldWithNavBar({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _calculateSelectedIndex(context),
        onDestinationSelected: (index) => _onItemTapped(index, context),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
  
  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/home')) return 0;
    if (location.startsWith('/search')) return 1;
    if (location.startsWith('/profile')) return 2;
    return 0;
  }
  
  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0: context.go('/home');
      case 1: context.go('/search');
      case 2: context.go('/profile');
    }
  }
}
```## 查询参数```dart
GoRoute(
  path: '/search',
  builder: (context, state) {
    final query = state.uri.queryParameters['q'] ?? '';
    final page = int.tryParse(state.uri.queryParameters['page'] ?? '1') ?? 1;
    return SearchScreen(query: query, page: page);
  },
),

// Navigate with query params
context.go('/search?q=flutter&page=2');
context.goNamed('search', queryParameters: {'q': 'flutter', 'page': '2'});
```## Riverpod 集成```dart
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  
  return GoRouter(
    refreshListenable: authState,
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');
      
      if (!isLoggedIn && !isAuthRoute) return '/auth/login';
      if (isLoggedIn && isAuthRoute) return '/';
      return null;
    },
    routes: [...],
  );
});

// In app.dart
class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(routerConfig: router);
  }
}
```## 错误处理```dart
final goRouter = GoRouter(
  errorBuilder: (context, state) {
    return ErrorScreen(error: state.error);
  },
  routes: [...],
);
```## 深层链接

当路由配置了路径参数时，深层链接会自动工作：```dart
// URL: myapp://details/123
// or: https://myapp.com/details/123
GoRoute(
  path: '/details/:id',
  builder: (context, state) => DetailsScreen(id: state.pathParameters['id']!),
),
```## 最佳实践

|做|不要|
|----|--------|
|使用命名路由以实现可维护性 |到处都硬编码路径|
|使用“push()”查看详细信息屏幕 |使用 `go()` 进行所有导航 |
|通过 `extra` 传递简单数据 |通过 URL 传递复杂对象 |
|使用重定向进行身份验证守卫 |检查每个屏幕中的身份验证 |
|使用 ShellRoute 实现持久 UI |在每个屏幕中重建导航栏 |

---

*GoRouter是Flutter的开源导航包。*