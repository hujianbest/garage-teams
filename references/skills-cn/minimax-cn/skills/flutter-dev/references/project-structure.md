# 项目结构

Flutter 项目架构指南，涵盖基于功能的结构、依赖项和入口点设置。

## 基于特征的结构```
lib/
├── main.dart                       # Entry point
├── app.dart                        # App widget, MaterialApp.router
├── core/
│   ├── constants/
│   │   ├── app_colors.dart
│   │   ├── app_strings.dart
│   │   └── app_sizes.dart
│   ├── theme/
│   │   ├── app_theme.dart
│   │   └── text_styles.dart
│   ├── utils/
│   │   ├── extensions.dart
│   │   └── validators.dart
│   └── errors/
│       └── failures.dart
├── features/
│   ├── auth/
│   │   ├── data/
│   │   │   ├── repositories/
│   │   │   │   └── auth_repository_impl.dart
│   │   │   └── datasources/
│   │   │       ├── auth_remote_datasource.dart
│   │   │       └── auth_local_datasource.dart
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   └── user.dart
│   │   │   ├── repositories/
│   │   │   │   └── auth_repository.dart
│   │   │   └── usecases/
│   │   │       ├── login.dart
│   │   │       └── logout.dart
│   │   ├── presentation/
│   │   │   ├── screens/
│   │   │   │   ├── login_screen.dart
│   │   │   │   └── register_screen.dart
│   │   │   └── widgets/
│   │   │       └── auth_form.dart
│   │   └── providers/
│   │       └── auth_provider.dart
│   └── home/
│       ├── data/
│       ├── domain/
│       ├── presentation/
│       └── providers/
├── shared/
│   ├── widgets/
│   │   ├── buttons/
│   │   │   └── primary_button.dart
│   │   ├── inputs/
│   │   │   └── text_input.dart
│   │   └── cards/
│   │       └── info_card.dart
│   ├── services/
│   │   ├── api_service.dart
│   │   └── storage_service.dart
│   └── models/
│       └── api_response.dart
└── routes/
    └── app_router.dart
```## 功能层职责

|层|责任|
|--------|----------------|
| **数据/** | API 调用、本地存储、DTO、存储库实现 |
| **域名/** |业务逻辑、实体、抽象存储库、用例 |
| **演示/** | UI 屏幕、小部件、视图逻辑 |
| **提供商/** | Riverpod 提供商或 Bloc 定义 |

## pubspec.yaml 要点```yaml
name: my_app
description: A Flutter application.
version: 1.0.0+1
publish_to: 'none'

environment:
  sdk: '>=3.3.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # State Management (choose one)
  flutter_riverpod: ^2.5.0
  riverpod_annotation: ^2.3.0
  # OR
  flutter_bloc: ^8.1.0
  
  # Navigation
  go_router: ^14.0.0
  
  # Networking
  dio: ^5.4.0
  
  # Code Generation
  freezed_annotation: ^2.4.0
  json_annotation: ^4.9.0
  
  # Storage
  shared_preferences: ^2.2.0
  hive_flutter: ^1.1.0
  
  # Utilities
  flutter_hooks: ^0.20.0
  cached_network_image: ^3.3.0
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  
  # Code Generation
  build_runner: ^2.4.0
  riverpod_generator: ^2.4.0
  freezed: ^2.5.0
  json_serializable: ^6.8.0
  
  # Linting
  flutter_lints: ^4.0.0
  
  # Testing
  bloc_test: ^9.1.0
  mocktail: ^1.0.0

flutter:
  uses-material-design: true
```## 主入口点```dart
// main.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize services
  await Hive.initFlutter();
  
  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}
```

```dart
// app.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'My App',
      routerConfig: router,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      debugShowCheckedModeBanner: false,
    );
  }
}
```## 路由器提供商```dart
// routes/app_router.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      // Auth guard logic
      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
      // Add more routes
    ],
  );
});
```## 环境配置```dart
// core/constants/environment.dart
enum Environment { dev, staging, prod }

class EnvConfig {
  static Environment current = Environment.dev;
  
  static String get baseUrl {
    switch (current) {
      case Environment.dev:
        return 'https://dev-api.example.com';
      case Environment.staging:
        return 'https://staging-api.example.com';
      case Environment.prod:
        return 'https://api.example.com';
    }
  }
}
```## 使用 Riverpod 进行依赖注入```dart
// shared/services/api_service.dart
final apiServiceProvider = Provider<ApiService>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: EnvConfig.baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
  ));
  
  // Add interceptors
  dio.interceptors.add(AuthInterceptor(ref));
  dio.interceptors.add(LogInterceptor(responseBody: true));
  
  return ApiService(dio);
});

// features/auth/providers/auth_provider.dart
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final api = ref.watch(apiServiceProvider);
  final storage = ref.watch(storageServiceProvider);
  return AuthRepositoryImpl(api: api, storage: storage);
});
```## 最佳实践

|实践|描述 |
|----------|-------------|
|特征隔离|每个功能都是独立的 |
|依赖倒置|领域取决于抽象 |
|单一责任 |一堂课，一个目的 |
|命名约定|清晰、描述性的名称 |
|桶出口|每个文件夹一个index.dart |

---

*Flutter 是 Google LLC 的商标。*