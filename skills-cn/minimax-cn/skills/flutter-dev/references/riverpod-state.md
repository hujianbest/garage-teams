# Riverpod 状态管理

Riverpod 2.0 状态管理指南，涵盖提供程序类型、通知程序模式和小部件集成。

## 提供商类型```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Simple computed value
final greetingProvider = Provider<String>((ref) {
  final name = ref.watch(userNameProvider);
  return 'Hello, $name';
});

// Simple mutable state
final counterProvider = StateProvider<int>((ref) => 0);

// Async state (API calls)
final usersProvider = FutureProvider<List<User>>((ref) async {
  final api = ref.read(apiProvider);
  return api.getUsers();
});

// Stream state (real-time)
final messagesProvider = StreamProvider<List<Message>>((ref) {
  return ref.read(chatServiceProvider).messagesStream;
});
```### 提供者类型参考

|供应商|使用案例|
|----------|----------|
| `提供者` |计算/导出值、依赖注入 |
| `状态提供者` |简单的可变状态（计数器、切换）|
| `未来提供者` |异步操作（一次性获取）|
| `StreamProvider` |实时数据流 |
| `NotifierProvider` |具有方法的复杂状态 |
| `AsyncNotifierProvider` |方法的异步状态 |

## 通知程序模式（Riverpod 2.0）

### 同步通知程序```dart
@riverpod
class TodoList extends _$TodoList {
  @override
  List<Todo> build() => [];

  void add(Todo todo) {
    state = [...state, todo];
  }

  void toggle(String id) {
    state = [
      for (final todo in state)
        if (todo.id == id) 
          todo.copyWith(completed: !todo.completed) 
        else 
          todo,
    ];
  }

  void remove(String id) {
    state = state.where((t) => t.id != id).toList();
  }
}
```### 异步通知```dart
@riverpod
class UserProfile extends _$UserProfile {
  @override
  Future<User> build() async {
    return ref.read(apiProvider).getCurrentUser();
  }

  Future<void> updateName(String name) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final updated = await ref.read(apiProvider).updateUser(name: name);
      return updated;
    });
  }

  Future<void> refresh() async {
    ref.invalidateSelf();
    await future;
  }
}
```## 在小部件中的用法

### ConsumerWidget（推荐）```dart
class TodoScreen extends ConsumerWidget {
  const TodoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final todos = ref.watch(todoListProvider);

    return ListView.builder(
      itemCount: todos.length,
      itemBuilder: (context, index) {
        final todo = todos[index];
        return ListTile(
          key: ValueKey(todo.id),
          title: Text(todo.title),
          leading: Checkbox(
            value: todo.completed,
            onChanged: (_) => ref.read(todoListProvider.notifier).toggle(todo.id),
          ),
        );
      },
    );
  }
}
```### 使用 select 进行选择性重建```dart
class UserAvatar extends ConsumerWidget {
  const UserAvatar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Only rebuilds when avatarUrl changes
    final avatarUrl = ref.watch(userProvider.select((u) => u?.avatarUrl));

    return CircleAvatar(
      backgroundImage: avatarUrl != null ? NetworkImage(avatarUrl) : null,
    );
  }
}
```### 异步状态处理```dart
class UserProfileScreen extends ConsumerWidget {
  const UserProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(userProfileProvider);

    return userAsync.when(
      data: (user) => UserProfileContent(user: user),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => ErrorView(
        message: err.toString(),
        onRetry: () => ref.invalidate(userProfileProvider),
      ),
    );
  }
}
```### 范围重建的消费者```dart
class MyScreen extends StatelessWidget {
  const MyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Text('Static content'),
        Consumer(
          builder: (context, ref, child) {
            final count = ref.watch(counterProvider);
            return Text('Count: $count');
          },
        ),
      ],
    );
  }
}
```## 提供者修饰符```dart
// Auto-dispose when no longer used
@riverpod
class AutoDisposeExample extends _$AutoDisposeExample {
  @override
  String build() => 'value';
}

// Family - parameterized providers
@riverpod
Future<User> userById(UserByIdRef ref, String id) async {
  return ref.read(apiProvider).getUser(id);
}

// Usage
final user = ref.watch(userByIdProvider('123'));
```## 最佳实践

|做|不要|
|----|--------|
|在构建中使用 `ref.watch()`在回调中使用 `ref.watch()`
|在回调中使用 `ref.read()`在构建中使用 `ref.read()`
|使用“select()”进行粒度重建 |无需监视整个状态 |
|创建新的状态实例 |直接改变状态 |
|使用 `AsyncValue.guard()` 来处理错误 |手动捕获错误 |

## 快速参考

|方法|何时使用 |
|--------|-------------|
| `ref.watch()` |在构建方法中，根据更改进行重建 |
| `ref.read()` |在回调中，一次性读取 |
| `ref.listen()` |改变的副作用|
| `ref.invalidate()` |强制提供程序刷新 |
| `ref.refresh()` |失效并获得新值|

---

*Riverpod 是 Remi Rousselet 的开源状态管理库。*