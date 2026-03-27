---
name: mdc-test-driven-dev
description: 使用 GoogleTest 进行 C++ 测试驱动开发。当用户要编写 C++ 代码、实现新功能、修复 Bug、重构 C++ 项目时，请务必使用此技能——即使用户没有明确提到 TDD 或测试。只要涉及 C++ 实现代码的编写，就应先写测试再写实现。同样适用于用户提到 gtest、gmock、ctest、CMake 测试、C++ 单元测试等场景。
---

# C++ 测试驱动开发（TDD with GoogleTest）

## 概述

先写测试，看着它失败，再写最少的代码让它通过。

**核心原则：** 如果你没有亲眼看到测试失败，你就不知道它到底测的是什么。

## 何时使用

**始终使用：**
- 新功能实现
- Bug 修复
- 重构
- 行为变更

**例外（需要与用户确认）：**
- 一次性原型
- 自动生成的代码
- 纯配置文件

想着"就这一次不写测试"？停下来，那是在给自己找借口。

## 铁律

```
没有失败的测试，就不写产品代码
```

先写了实现代码？删掉它，从头来过。

**没有例外：**
- 不要把它留作"参考"
- 不要"一边写测试一边改它"
- 不要偷看它
- 删除就是删除

从测试出发，重新实现。

## 红-绿-重构

### RED — 写一个失败的测试

写一个最小的测试，描述期望的行为。

<Good>
```cpp
TEST(RetryTest, RetriesFailedOperations3Times) {
  int attempts = 0;
  auto operation = [&]() -> std::string {
    ++attempts;
    if (attempts < 3) throw std::runtime_error("fail");
    return "success";
  };

  auto result = retry_operation(operation);

  EXPECT_EQ(result, "success");
  EXPECT_EQ(attempts, 3);
}
```
名字清晰，测试真实行为，只测一件事
</Good>

<Bad>
```cpp
TEST(RetryTest, RetryWorks) {
  MockOperation mock;
  EXPECT_CALL(mock, execute())
      .WillOnce(testing::Throw(std::runtime_error("fail")))
      .WillOnce(testing::Throw(std::runtime_error("fail")))
      .WillOnce(testing::Return("success"));
  retry_operation([&]{ return mock.execute(); });
  // 只验证了 mock 调用次数，没测真实逻辑
}
```
名字含糊，测的是 mock 而非代码
</Bad>

**要求：**
- 只测一个行为
- 测试名说明行为（`RejectsEmptyInput`，不是 `Test1`）
- 用真实代码，mock 只在不得已时使用

### 验证 RED — 看着它失败

**必须执行，绝不跳过。**

```bash
cd build && cmake --build . && ctest --output-on-failure -R RetryTest
```

确认：
- 测试**失败**（不是编译错误）
- 失败原因符合预期
- 失败是因为功能缺失（不是因为拼错了）

**测试直接通过了？** 你在测已有的行为，修改测试。

**编译报错？** 先修编译，再运行直到看见正确的失败。

### GREEN — 最少的实现代码

写最简单的代码让测试通过。

<Good>
```cpp
template <typename F>
auto retry_operation(F&& fn, int max_retries = 3) -> decltype(fn()) {
  for (int i = 0; i < max_retries; ++i) {
    try {
      return fn();
    } catch (...) {
      if (i == max_retries - 1) throw;
    }
  }
  throw std::logic_error("unreachable");
}
```
刚好够让测试通过
</Good>

<Bad>
```cpp
template <typename F>
auto retry_operation(
    F&& fn,
    int max_retries = 3,
    std::chrono::milliseconds backoff = std::chrono::milliseconds(100),
    BackoffStrategy strategy = BackoffStrategy::Exponential,
    std::function<void(int, const std::exception&)> on_retry = nullptr
) -> decltype(fn()) {
  // YAGNI — 没有测试要求这些参数
}
```
过度设计
</Bad>

不要加功能、不要顺手重构别的代码、不要"改进"超出测试要求的范围。

### 验证 GREEN — 看着它通过

**必须执行。**

```bash
cd build && cmake --build . && ctest --output-on-failure
```

确认：
- 当前测试通过
- 其他测试依然通过
- 编译输出干净（没有 warning）

**测试失败了？** 改实现代码，不改测试。

**其他测试挂了？** 立刻修。

### REFACTOR — 整理代码

只在全绿之后：
- 消除重复
- 改善命名
- 提取辅助函数

保持测试全绿。不添加新行为。

### 重复

为下一个行为写下一个失败的测试。

## 好测试的标准

| 品质 | 好 | 坏 |
|------|----|----|
| **最小** | 只测一件事。名字里有"并且"？拆开。 | `TEST(Validator, ValidatesEmailAndDomainAndWhitespace)` |
| **清晰** | 名字描述行为 | `TEST(Foo, Test1)` |
| **表达意图** | 展示理想的 API | 隐藏了代码该做什么 |

## GoogleTest 实用模式

### Test Fixture（共享 setup/teardown）

当多个测试需要相同的准备工作时，使用 fixture：

```cpp
class CalculatorTest : public ::testing::Test {
protected:
  void SetUp() override {
    calc = std::make_unique<Calculator>();
  }
  std::unique_ptr<Calculator> calc;
};

TEST_F(CalculatorTest, AddsPositiveNumbers) {
  EXPECT_EQ(calc->add(2, 3), 5);
}

TEST_F(CalculatorTest, ReturnsZeroForEmptyInput) {
  EXPECT_EQ(calc->sum({}), 0);
}
```

### 参数化测试

同一个逻辑、不同输入时，避免复制粘贴：

```cpp
struct EmailCase {
  std::string input;
  bool expected_valid;
};

class EmailValidationTest : public ::testing::TestWithParam<EmailCase> {};

TEST_P(EmailValidationTest, ValidatesCorrectly) {
  auto [input, expected] = GetParam();
  EXPECT_EQ(is_valid_email(input), expected);
}

INSTANTIATE_TEST_SUITE_P(Emails, EmailValidationTest, ::testing::Values(
    EmailCase{"user@example.com", true},
    EmailCase{"missing-at.com", false},
    EmailCase{"", false},
    EmailCase{"a@b.c", true}
));
```

### 断言选择

| 场景 | 推荐 | 说明 |
|------|------|------|
| 继续执行后续断言 | `EXPECT_*` | 失败后继续运行 |
| 失败则无法继续 | `ASSERT_*` | 失败后立即终止当前测试 |
| 浮点比较 | `EXPECT_NEAR(a, b, tol)` | 避免浮点精度问题 |
| 字符串包含 | `EXPECT_THAT(s, HasSubstr("x"))` | 需要 `#include <gmock/gmock-matchers.h>` |
| 异常 | `EXPECT_THROW(expr, ExType)` | 验证抛出指定类型异常 |
| 不抛异常 | `EXPECT_NO_THROW(expr)` | 验证无异常 |

### 依赖注入与接口

C++ 中通过抽象基类（接口）注入依赖，方便隔离测试：

```cpp
class ILogger {
public:
  virtual ~ILogger() = default;
  virtual void log(std::string_view message) = 0;
};

class Service {
public:
  explicit Service(std::shared_ptr<ILogger> logger) : logger_(std::move(logger)) {}
  void process(int value) {
    if (value < 0) {
      logger_->log("negative input");
      return;
    }
    // ...
  }
private:
  std::shared_ptr<ILogger> logger_;
};
```

测试时用 GoogleMock 提供假实现：

```cpp
class MockLogger : public ILogger {
public:
  MOCK_METHOD(void, log, (std::string_view message), (override));
};

TEST(ServiceTest, LogsWarningOnNegativeInput) {
  auto logger = std::make_shared<MockLogger>();
  Service service(logger);

  EXPECT_CALL(*logger, log(HasSubstr("negative")));
  service.process(-1);
}
```

**注意：** mock 是为了隔离外部依赖（网络、文件系统、数据库），不是为了省事。
如果一个类可以直接构造，就直接用真实对象。详见 @testing-anti-patterns.md。

## 为什么顺序重要

**"我先写完再补测试验证"**

后写的测试直接通过，直接通过什么也证明不了：
- 可能测的东西不对
- 可能测的是实现细节而非行为
- 可能遗漏了你没想到的边界
- 你从来没看到它抓住过 bug

先写测试，迫使你亲眼看到失败，证明测试确实在检查某件事。

**"删掉 X 小时的工作太浪费了"**

沉没成本谬误。时间已经花了，现在的选择：
- 删掉重来、用 TDD（再花 X 小时，高置信度）
- 保留它、补测试（30 分钟，低置信度，大概率有 bug）

"浪费"的是保留你无法信任的代码。

## 常见借口

| 借口 | 现实 |
|------|------|
| "太简单不用测" | 简单的代码也会坏，写个测试只要 30 秒 |
| "我先写完再补" | 后补的测试直接通过，什么也证明不了 |
| "手动测过了" | 临时测试 ≠ 系统测试。没有记录，不可重现 |
| "删掉 X 小时太浪费" | 沉没成本。保留不可信的代码才是负债 |
| "留着当参考" | 你会改它，那就是后补测试。删除就是删除 |
| "需要先探索一下" | 可以。探索完，扔掉探索代码，从 TDD 开始 |
| "测试写不出来 = 设计不清楚" | 正是如此。难测试 = 难使用，简化接口 |
| "TDD 太慢了" | TDD 比调 bug 快。先测试 = 务实 |

## 红灯 — 立即停下，从头来过

- 先写了实现代码
- 实现完了才补测试
- 测试直接通过
- 说不清测试为什么失败
- "回头再加测试"
- 给自己找"就这一次"的理由

**以上全部意味着：删除代码，用 TDD 重来。**

## 示例：修复 Bug

**Bug：** 空字符串被接受为有效输入

**RED**
```cpp
TEST(InputValidatorTest, RejectsEmptyString) {
  InputValidator validator;
  auto result = validator.validate("");
  EXPECT_FALSE(result.ok);
  EXPECT_EQ(result.error, "input must not be empty");
}
```

**验证 RED**
```bash
$ cd build && cmake --build . && ctest --output-on-failure -R RejectsEmptyString
[  FAILED  ] InputValidatorTest.RejectsEmptyString
Expected equality of these values:
  result.error
    Which is: ""
  "input must not be empty"
```

**GREEN**
```cpp
ValidationResult InputValidator::validate(std::string_view input) {
  if (input.empty()) {
    return {.ok = false, .error = "input must not be empty"};
  }
  // ...existing logic...
}
```

**验证 GREEN**
```bash
$ cd build && cmake --build . && ctest --output-on-failure
[  PASSED  ] 42 tests.
```

**REFACTOR**
如果有多个字段需要非空校验，提取通用验证函数。

## 项目搭建

使用 CMake + FetchContent 引入 GoogleTest 是目前最主流的方式。
详细配置参见 @references/cmake-setup.md。

快速参考：

```cmake
# CMakeLists.txt (项目根目录)
cmake_minimum_required(VERSION 3.14)
project(my_project LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

enable_testing()
add_subdirectory(src)
add_subdirectory(tests)
```

构建与运行测试：
```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
cd build && ctest --output-on-failure
```

## 验证清单

完成工作前逐项检查：

- [ ] 每个新函数/方法都有对应测试
- [ ] 每个测试都亲眼看到失败
- [ ] 每个测试的失败原因是功能缺失（不是拼写错误）
- [ ] 每次只写了让测试通过的最少代码
- [ ] 所有测试通过
- [ ] 编译输出干净（无 warning、无 error）
- [ ] 测试使用真实代码（mock 只在不得已时使用）
- [ ] 边界和错误情况已覆盖

不能全部打勾？你跳过了 TDD，从头来过。

## 遇到困难

| 问题 | 解决 |
|------|------|
| 不知道怎么测 | 先写你期望的 API，先写断言，问你的搭档 |
| 测试太复杂 | 设计太复杂，简化接口 |
| 必须 mock 一切 | 耦合太紧，使用依赖注入 |
| setup 代码太长 | 提取到 Test Fixture。仍然复杂？简化设计 |

## 调试集成

发现 bug？先写一个能重现它的失败测试，再走 TDD 循环。测试既证明了修复有效，又防止回归。

永远不要在没有测试的情况下修 bug。

## 测试反模式

添加 mock 或测试工具时，阅读 @testing-anti-patterns.md 避免常见陷阱：
- 测试的是 mock 行为而非真实行为
- 给产品类加只有测试才用的方法
- 不了解依赖关系就乱 mock

## 最终规则

```
产品代码 → 必须先有一个失败的测试
否则 → 不是 TDD
```

没有用户许可，不得例外。
