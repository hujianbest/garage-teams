# 块状态管理

Bloc 状态管理指南涵盖复杂业务逻辑的事件、状态、Cubit 和小部件集成。

## 何时使用 Bloc

当您需要时使用 **Bloc/Cubit**：
- 显式事件→状态转换
- 具有多个事件的复杂业务逻辑
- 可预测、可测试的状态流
- UI和逻辑之间清晰分离

|使用案例|推荐|
|----------|-------------|
|简单的可变状态 |河波德 |
|计算值 |河波德 |
|事件驱动的工作流程 |集团|
|表单、身份验证、向导 |集团|
|逻辑复杂的功能模块 |集团|

## 核心概念

|概念 |描述 |
|---------|-------------|
|活动 |触发状态改变的用户或系统输入 |
|状态| UI 状态的不可变表示 |
|集团|将事件映射到新状态 |
|肘|没有事件的简化块 |

## 肘节（推荐用于更简单的逻辑）```dart
import 'package:flutter_bloc/flutter_bloc.dart';

class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
  void reset() => emit(0);
}
```## 完整的块设置

### 事件定义```dart
sealed class CounterEvent {}

final class CounterIncremented extends CounterEvent {}
final class CounterDecremented extends CounterEvent {}
final class CounterReset extends CounterEvent {}
```### 状态定义```dart
class CounterState {
  final int value;
  final bool isLoading;

  const CounterState({
    required this.value,
    this.isLoading = false,
  });

  CounterState copyWith({int? value, bool? isLoading}) {
    return CounterState(
      value: value ?? this.value,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}
```### 集团实施```dart
class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(const CounterState(value: 0)) {
    on<CounterIncremented>(_onIncremented);
    on<CounterDecremented>(_onDecremented);
    on<CounterReset>(_onReset);
  }

  void _onIncremented(CounterIncremented event, Emitter<CounterState> emit) {
    emit(state.copyWith(value: state.value + 1));
  }

  void _onDecremented(CounterDecremented event, Emitter<CounterState> emit) {
    emit(state.copyWith(value: state.value - 1));
  }

  void _onReset(CounterReset event, Emitter<CounterState> emit) {
    emit(const CounterState(value: 0));
  }
}
```## 为 Widget Tree 提供 Bloc```dart
// Single bloc
BlocProvider(
  create: (_) => CounterBloc(),
  child: const CounterScreen(),
);

// Multiple blocs
MultiBlocProvider(
  providers: [
    BlocProvider(create: (_) => AuthBloc()),
    BlocProvider(create: (_) => ProfileBloc()),
    BlocProvider(create: (_) => SettingsBloc()),
  ],
  child: const AppRoot(),
);
```## 在小部件中使用 Bloc

### BlocBuilder（UI 重建）```dart
class CounterScreen extends StatelessWidget {
  const CounterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<CounterBloc, CounterState>(
      buildWhen: (prev, curr) => prev.value != curr.value,
      builder: (context, state) {
        return Text(
          state.value.toString(),
          style: Theme.of(context).textTheme.displayLarge,
        );
      },
    );
  }
}
```### BlocListener（副作用）```dart
BlocListener<AuthBloc, AuthState>(
  listenWhen: (prev, curr) => prev.status != curr.status,
  listener: (context, state) {
    if (state.status == AuthStatus.failure) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.errorMessage ?? 'Error')),
      );
    }
    if (state.status == AuthStatus.authenticated) {
      context.go('/home');
    }
  },
  child: const LoginForm(),
);
```### BlocConsumer（构建器+监听器）```dart
BlocConsumer<FormBloc, FormState>(
  listenWhen: (prev, curr) => prev.status != curr.status,
  listener: (context, state) {
    if (state.status == FormStatus.success) {
      context.pop();
    }
  },
  buildWhen: (prev, curr) => prev.isValid != curr.isValid,
  builder: (context, state) {
    return ElevatedButton(
      onPressed: state.isValid
          ? () => context.read<FormBloc>().add(FormSubmitted())
          : null,
      child: const Text('Submit'),
    );
  },
);
```### BlocSelector（粒度重建）```dart
BlocSelector<UserBloc, UserState, String>(
  selector: (state) => state.user.name,
  builder: (context, name) {
    return Text('Hello, $name');
  },
);
```## 异步块模式```dart
on<UserRequested>((event, emit) async {
  emit(state.copyWith(status: UserStatus.loading));

  try {
    final user = await repository.fetchUser(event.userId);
    emit(state.copyWith(status: UserStatus.success, user: user));
  } catch (e) {
    emit(state.copyWith(status: UserStatus.failure, error: e.toString()));
  }
});
```## Bloc + GoRouter 授权卫士```dart
redirect: (context, state) {
  final authState = context.read<AuthBloc>().state;
  final isAuthRoute = state.matchedLocation.startsWith('/auth');

  if (authState.status != AuthStatus.authenticated && !isAuthRoute) {
    return '/auth/login';
  }
  if (authState.status == AuthStatus.authenticated && isAuthRoute) {
    return '/';
  }
  return null;
}
```## 测试块```dart
import 'package:bloc_test/bloc_test.dart';

blocTest<CounterBloc, CounterState>(
  'emits incremented value when CounterIncremented added',
  build: () => CounterBloc(),
  act: (bloc) => bloc.add(CounterIncremented()),
  expect: () => [const CounterState(value: 1)],
);

blocTest<CounterBloc, CounterState>(
  'emits multiple states',
  build: () => CounterBloc(),
  act: (bloc) {
    bloc.add(CounterIncremented());
    bloc.add(CounterIncremented());
    bloc.add(CounterDecremented());
  },
  expect: () => [
    const CounterState(value: 1),
    const CounterState(value: 2),
    const CounterState(value: 1),
  ],
);
```## 最佳实践

|做|不要|
|----|--------|
|保持状态不变 |直接改变状态 |
|使用小而集中的团体 |用一切创造“上帝集团”|
|一项功能 = 一组 |跨不相关功能共享块 |
|对于简单情况使用肘节 | Bloc 不必要地过于复杂 |
|测试所有状态转换 |跳过块测试 |
|使用 `buildWhen`/`listenWhen` |每次状态更改时重建 |

## 小部件参考

|小部件 |目的|
|--------|---------|
| `块构建器` | UI根据状态重建|
| `块监听器` |副作用（导航、小吃栏）|
| `区块消费者` |既是构建者又是倾听者 |
| `块选择器` |粒度状态选择|
| `块提供者` |依赖注入 |
| `MultiBlocProvider` |多块注射 |
| `RepositoryProvider` |存储库注入 |

---

*Bloc 是 Felix Angelov 的开源状态管理库。*