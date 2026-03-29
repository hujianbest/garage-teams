# 测试策略

Flutter 测试指南涵盖小部件测试、单元测试、集成测试和模拟模式。

## 测试类型

|类型 |目的|速度|范围 |
|------|---------|--------|--------|
|单元测试 |业务逻辑、实用程序 |快|单一功能/类 |
|小部件测试 |用户界面组件 |中等|单个小部件 |
|集成测试|完整的用户流程 |慢|多屏|

## 小部件测试

### 基本小部件测试```dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Counter increments when button tapped', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: CounterScreen()));

    // Verify initial state
    expect(find.text('0'), findsOneWidget);
    expect(find.text('1'), findsNothing);

    // Tap the increment button
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();

    // Verify state changed
    expect(find.text('0'), findsNothing);
    expect(find.text('1'), findsOneWidget);
  });
}
```### 使用 Riverpod 进行测试```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('displays user name from provider', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          userProvider.overrideWithValue(
            AsyncValue.data(User(name: 'Test User')),
          ),
        ],
        child: const MaterialApp(home: UserScreen()),
      ),
    );

    expect(find.text('Test User'), findsOneWidget);
  });

  testWidgets('shows loading indicator', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          userProvider.overrideWithValue(const AsyncValue.loading()),
        ],
        child: const MaterialApp(home: UserScreen()),
      ),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('shows error message', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          userProvider.overrideWithValue(
            AsyncValue.error('Network error', StackTrace.current),
          ),
        ],
        child: const MaterialApp(home: UserScreen()),
      ),
    );

    expect(find.text('Network error'), findsOneWidget);
  });
}
```### 使用 Bloc 进行测试```dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockCounterBloc extends MockBloc<CounterEvent, CounterState>
    implements CounterBloc {}

void main() {
  late MockCounterBloc mockBloc;

  setUp(() {
    mockBloc = MockCounterBloc();
  });

  testWidgets('displays current count', (tester) async {
    when(() => mockBloc.state).thenReturn(const CounterState(value: 42));

    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider<CounterBloc>.value(
          value: mockBloc,
          child: const CounterScreen(),
        ),
      ),
    );

    expect(find.text('42'), findsOneWidget);
  });

  testWidgets('calls increment on button tap', (tester) async {
    when(() => mockBloc.state).thenReturn(const CounterState(value: 0));

    await tester.pumpWidget(
      MaterialApp(
        home: BlocProvider<CounterBloc>.value(
          value: mockBloc,
          child: const CounterScreen(),
        ),
      ),
    );

    await tester.tap(find.byIcon(Icons.add));

    verify(() => mockBloc.add(CounterIncremented())).called(1);
  });
}
```## 块测试```dart
import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockUserRepository extends Mock implements UserRepository {}

void main() {
  late MockUserRepository mockRepository;

  setUp(() {
    mockRepository = MockUserRepository();
  });

  group('UserBloc', () {
    blocTest<UserBloc, UserState>(
      'emits loading then success when user loaded',
      setUp: () {
        when(() => mockRepository.getUser())
            .thenAnswer((_) async => User(name: 'Test'));
      },
      build: () => UserBloc(repository: mockRepository),
      act: (bloc) => bloc.add(UserRequested()),
      expect: () => [
        const UserState(status: UserStatus.loading),
        UserState(status: UserStatus.success, user: User(name: 'Test')),
      ],
    );

    blocTest<UserBloc, UserState>(
      'emits loading then failure when error occurs',
      setUp: () {
        when(() => mockRepository.getUser())
            .thenThrow(Exception('Network error'));
      },
      build: () => UserBloc(repository: mockRepository),
      act: (bloc) => bloc.add(UserRequested()),
      expect: () => [
        const UserState(status: UserStatus.loading),
        isA<UserState>()
            .having((s) => s.status, 'status', UserStatus.failure),
      ],
    );
  });
}
```## 单元测试```dart
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Validator', () {
    test('returns error for empty email', () {
      expect(Validator.email(''), 'Email is required');
    });

    test('returns error for invalid email', () {
      expect(Validator.email('invalid'), 'Invalid email format');
    });

    test('returns null for valid email', () {
      expect(Validator.email('test@example.com'), isNull);
    });
  });

  group('Calculator', () {
    late Calculator calculator;

    setUp(() {
      calculator = Calculator();
    });

    test('adds two numbers', () {
      expect(calculator.add(2, 3), 5);
    });

    test('throws on division by zero', () {
      expect(() => calculator.divide(10, 0), throwsArgumentError);
    });
  });
}
```## 用 Mocktail 进行嘲笑```dart
import 'package:mocktail/mocktail.dart';

// Create mock classes
class MockApiService extends Mock implements ApiService {}
class MockStorageService extends Mock implements StorageService {}

// Register fallback values for complex types
setUpAll(() {
  registerFallbackValue(User(name: 'fallback'));
});

void main() {
  late MockApiService mockApi;

  setUp(() {
    mockApi = MockApiService();
  });

  test('fetches user from API', () async {
    // Arrange
    when(() => mockApi.getUser(any()))
        .thenAnswer((_) async => User(name: 'Test'));

    // Act
    final repository = UserRepository(api: mockApi);
    final user = await repository.getUser('123');

    // Assert
    expect(user.name, 'Test');
    verify(() => mockApi.getUser('123')).called(1);
  });
}
```## 集成测试```dart
// integration_test/app_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:my_app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('complete login flow', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Navigate to login
    await tester.tap(find.text('Login'));
    await tester.pumpAndSettle();

    // Enter credentials
    await tester.enterText(
      find.byKey(const Key('email_field')),
      'test@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('password_field')),
      'password123',
    );

    // Submit form
    await tester.tap(find.text('Sign In'));
    await tester.pumpAndSettle();

    // Verify navigation to home
    expect(find.text('Welcome'), findsOneWidget);
  });
}
```运行集成测试：```bash
flutter test integration_test/app_test.dart
```## 测试助手```dart
// test/helpers/pump_app.dart
extension PumpApp on WidgetTester {
  Future<void> pumpApp(Widget widget, {List<Override>? overrides}) {
    return pumpWidget(
      ProviderScope(
        overrides: overrides ?? [],
        child: MaterialApp(
          home: widget,
        ),
      ),
    );
  }
}

// Usage
await tester.pumpApp(const MyWidget());
```## 黄金测试```dart
testWidgets('matches golden', (tester) async {
  await tester.pumpWidget(const MaterialApp(home: MyWidget()));

  await expectLater(
    find.byType(MyWidget),
    matchesGoldenFile('goldens/my_widget.png'),
  );
});
```更新金币：```bash
flutter test --update-goldens
```## 测试清单

|测试类型|测试什么 |
|------------|--------------|
|小部件测试 | UI 渲染、用户交互、状态变化 |
|块测试 |事件 → 状态转换、异步操作 |
|单元测试 |验证器、格式化程序、实用程序、模型 |
|集成测试|关键用户流、导航 |

---

*Flutter 和 flutter_test 是 Google LLC 的商标。*