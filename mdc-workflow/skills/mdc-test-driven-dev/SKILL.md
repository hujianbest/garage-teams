---
name: mdc-test-driven-dev
description: 作为 MDC 系列唯一的实现入口使用。适用于任务计划已批准后的实现阶段，或受控修复已进入实现阶段时；本 skill 负责单任务推进、测试设计确认、TDD 执行，以及把 fresh evidence、风险和推荐下一步写回工件。当前默认覆盖 C++/GoogleTest 场景；若项目不是 C++，需显式说明当前未覆盖，而不是假定存在其他实现。
---

# MDC 测试驱动开发与实现入口

## 角色定位

这个 skill 现在承担两层职责：

1. 作为 `mdc` 系列唯一的实现入口
2. 作为实现阶段内部统一的 TDD 执行入口

它不再只是旧式的“TDD 路由器”。

对于已批准任务计划的主链实现，以及 `mdc-hotfix` 中需要复现和最小修复的场景，都应进入本 skill。

## 与 MDC 主链的关系

- 在 full / standard / lightweight profile 中，任务计划获批后进入本 skill
- 受控热修复在进入实际修复实现时，也会进入本 skill
- 本 skill 完成后，不在本节点内部决定下游质量节点；由 `mdc-workflow-starter` 按当前 profile 恢复后续编排

## 非节点说明

在新的 `mdc-workflow` 设计里，本 skill 应被视为实现阶段的统一执行入口，而不是 starter 独立路由出的并列“子流程套娃”。

也就是说：

- `mdc-workflow-starter` 可以直接把会话路由到本 skill
- 本 skill 内部只执行测试设计确认、TDD、实现、状态更新和评审输入准备
- 不再保留单独的 `mdc-implement` 节点

## 硬性门禁

任务计划未获批准前，不得开始实现。

当前任务在实现、评审、验证完成之前，不得切换到下一个任务。

在进入 Red-Green-Refactor 之前，必须先让真人确认当前任务的测试用例设计满足预期。

## 核心规则

一次只允许有一个活跃任务。

实现阶段的活跃任务不应依赖聊天记忆推断。优先从 `task-progress.md` 或等价状态工件读取：

- `Current Stage`
- `Current Active Task`
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`

如果进度记录与任务计划冲突，按更保守的上游工件处理，不直接继续实现。

如果当前是因为后续质量能力或门禁返回 `需修改` / `阻塞` 而重新进入本 skill：

- 先读取评审或门禁结论中的发现项、风险和修订建议
- 定位需要修正的具体代码或测试区域
- 优先修复 `critical` 与 `important` 级别的问题
- 修复完成后，应把 fresh evidence、剩余风险和推荐下一步写回工件，并从触发回流的那个质量能力或门禁恢复后续编排，而不是从质量链起点重走
- 不要因为回流修订就重新执行整个 TDD 流程，除非修订涉及行为变更，需要新增或修改测试

## `AGENTS.md` 测试约定

进入实现阶段后，先检查 `AGENTS.md` 是否为当前项目声明了 testing 规范。

优先读取：

- 测试命令与执行顺序
- 单测 / 集成测 / 端到端测试的分层要求
- mock、fixture、外部依赖替身的边界
- 覆盖率门槛或必须覆盖的风险类型
- 哪些非代码或纯配置变更可例外豁免 fail-first 纪律

若 `AGENTS.md` 没有声明这些约定，再回落到本 skill 与项目现有默认测试方式。

## 当前路由规则

- 若项目是 C++ / GoogleTest / CMake 测试栈，按本文后续规则执行
- 若项目不是 C++，明确说明当前 `mdc-test-driven-dev` 仅已覆盖 C++，需要后续补对应语言实现

当前仓库中的这份内容同时承担：

- `mdc` 系列的实现入口
- `mdc` 系列级 TDD 入口
- C++ / GoogleTest 的具体 TDD 指南

## 工作流

### 1. 对齐上下文

阅读：

- `AGENTS.md` 中与当前任务相关的 testing / coding 约定（如果存在）
- 已批准任务计划
- 当前进度或状态记录
- 当前任务对应的规格和设计片段

只选定一个活跃任务。

默认顺序：

1. 先读 `task-progress.md` 中的 `Current Active Task`
2. 再用任务计划校验该任务是否真实存在且仍然有效
3. 若两者冲突，暂停实现并先修正状态记录或回到上游阶段

### 2. 设计测试用例并与真人确认

在进入 TDD 之前，先输出当前任务的测试设计，至少说明：

- 要验证哪些行为
- 关键正向 / 反向场景
- 边界条件
- 预期输入与输出
- 哪些测试应先失败

测试设计应优先反映 `AGENTS.md` 中声明的测试分层、命令入口和覆盖要求。

然后：

1. 把测试用例设计展示给真人
2. 邀请真人确认“这些测试是否满足当前预期”
3. 如果真人提出意见，继续对话并修改测试设计
4. 只有在真人明确确认后，才能进入下一步

### 3. 执行 TDD

对于当前任务：

1. 先写失败测试
2. 运行并确认失败原因符合预期
3. 写最小实现让测试通过
4. 运行验证并确认没有引入回归
5. 在全绿后做必要的最小重构

### 4. 准备评审输入

在声称任务完成之前：

- 明确本次改了什么
- 明确哪些测试在证明它
- 明确还存在哪些风险区域
- 同步更新 `task-progress.md` 中当前任务的进展与待处理的质量检查 / gate

### 5. 准备后续质量能力与门禁所需输入

当前任务实现完成后，不在本 skill 内直接决定下游质量节点。应至少写回：

1. 当前任务的实现摘要
2. 对应的测试与验证结果
3. 尚未消除的风险与阻塞
4. `task-progress.md` 中的推荐下一步动作或 skill

然后由 `mdc-workflow-starter` 按当前 profile 恢复后续编排：

- full / standard 通常先判断是否进入 `mdc-bug-patterns`
- lightweight 通常先判断是否进入 `mdc-regression-gate`

## workflow 默认顺序

```text
实现入口 -> 测试用例设计 -> 真人确认测试设计 -> Red-Green-Refactor -> 写回 fresh evidence 与推荐下一步 -> 由外部调度恢复质量链
```

不要因为任务看起来简单就跳过后续质量检查或门禁。

## 红旗信号

出现以下想法时，先停下。这通常说明你正在为跳步找理由：

| 想法 | 实际要求 |
|---|---|
| “这个任务很小，直接改掉更快” | 任务再小，也必须先经过本 skill 的 fail-first 纪律。 |
| “测试用例大概可以，先跑起来再说” | 先让真人确认测试用例设计，再进入 TDD。 |
| “测试后面再补也行” | 先有失败测试，再写生产代码。 |
| “我先顺手把相邻任务一起做了” | 一次只允许一个活跃任务。 |
| “现在已经差不多了，可以先说完成” | 完成要等评审、回归和完成门禁都走完。 |
| “这些 review 太重了，先跳过一个” | 后续质量能力与门禁由 `mdc-workflow-starter` 按当前 profile 恢复编排，不能在本节点内擅自省略或重排。 |
| “旧的绿测结果也能证明这次改动没问题” | 必须有当前任务对应的新鲜证据。 |

## C++ 测试驱动开发（TDD with GoogleTest）

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

## 构建与运行测试：

如果你不清楚如何运行HDT用例，查看 Agents.md 中关于编译构建的相关信息。

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

## 反模式

- 并行处理多个任务
- 未经真人确认测试用例设计，就直接开始写失败测试
- 不经过 fail-first 过程就直接开始实现
- 先写实现，再补失败测试
- 把旧的绿测结果当成当前证据
- 在完成门禁前就说“做完了”
- 因为当前任务变麻烦就切换任务
- 因为赶进度而跳过缺陷模式排查、评审或门禁
- 不读取 `task-progress.md` 就靠会话印象决定当前活跃任务

## 最终规则

```
产品代码 → 必须先有一个失败的测试
否则 → 不是 TDD
```

没有用户许可，不得例外。

## 完成条件

只有在测试设计已经过真人确认，且当前任务已经完成实现，并把验证结果、剩余风险和推荐下一步写回工件以供外部调度恢复编排，或明确报告了阻塞问题后，这个 skill 才算完成。
