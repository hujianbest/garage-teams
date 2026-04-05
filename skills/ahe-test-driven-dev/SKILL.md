---
name: ahe-test-driven-dev
description: 作为 AHE 系列唯一的实现入口使用。适用于任务计划已批准后的单任务实现、受控 hotfix 已进入修复实现、或 review / gate 回流后的受控修订；本 skill 负责锁定当前活跃任务、完成真人测试设计确认、执行有效 TDD、写回 fresh evidence，并用 canonical 下一步交接给 `ahe-workflow-starter`。当前附录提供 C++/GoogleTest 深度示例，但非 C++ 场景也必须遵守同一实现契约。
---

# AHE 测试驱动开发与实现入口

## 角色定位

这个 skill 现在承担三层职责：

1. 作为 `ahe` 系列唯一的实现入口
2. 作为实现阶段内部统一的 TDD 执行入口
3. 作为实现完成后向后续 review / gate 输出实现证据与显式 handoff 的交接入口

它不再只是旧式的“TDD 路由器”，也不是另一个独立于主链之外的子工作流。

对于已批准任务计划的主链实现，以及 `ahe-hotfix` 中需要复现和最小修复的场景，都应进入本 skill。

## 与 AHE 主链的关系

- 在 full / standard / lightweight profile 中，任务计划获批后进入本 skill
- 受控热修复在进入实际修复实现时，也会进入本 skill
- 来自 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`、`ahe-regression-gate`、`ahe-completion-gate` 的回流修订，只要仍属于当前活跃任务，也会重新进入本 skill
- 本 skill 完成后，不在本节点内部私自重排质量链；由 `ahe-workflow-starter` 按当前 profile 恢复后续编排

## 非节点说明

在新的 `ahe-workflow` 设计里，本 skill 应被视为实现阶段的统一执行入口，而不是 starter 独立路由出的并列“子流程套娃”。

也就是说：

- `ahe-workflow-starter` 可以直接把会话路由到本 skill
- 本 skill 内部只执行测试设计确认、TDD、实现、状态更新和评审输入准备
- 不再保留单独的 `ahe-implement` 节点

## 高质量实现基线

高质量的 `ahe-test-driven-dev` 执行结果，至少应满足：

- 全程只围绕一个已批准、可追溯的活跃任务推进
- 动手实现前，已读取任务计划、状态记录、相关规格 / 设计锚点，以及必要的回流来源记录
- 测试设计不仅经过真人确认，而且能说明要验证的行为、边界、反向场景和预期失败点
- RED 和 GREEN 都有当前会话中的新鲜证据，而不是靠口头描述或旧日志
- 实现完成后能产出稳定的“实现交接块”，让下游 review / gate 直接消费
- 明确知道自己不替代 `ahe-bug-patterns`、`ahe-test-review`、`ahe-regression-gate`

## 硬性门禁

主链实现时，任务计划未获批准前，不得开始实现。

hotfix 实现时，至少要有来自 `ahe-hotfix` 的复现路径、最小修复边界和显式 handoff 记录，才可进入本 skill。

当前任务在实现、评审、验证完成之前，不得切换到下一个任务。

在进入 Red-Green-Refactor 之前，必须先让真人确认当前任务的测试用例设计满足预期。

如果 `task-progress.md`、任务计划、规格 / 设计批准状态之间存在冲突，不得直接继续实现；应先按更保守的上游证据处理。

在写回 fresh evidence 和 canonical handoff 之前，不得声称“当前任务已完成”。

## 核心规则

一次只允许有一个活跃任务。

实现阶段的活跃任务不应依赖聊天记忆推断。优先从 `task-progress.md` 或等价状态工件读取：

- `Current Stage`
- `Current Active Task`
- `Pending Reviews And Gates`
- `Next Action Or Recommended Skill`

如果进度记录与任务计划冲突，按更保守的上游工件处理，不直接继续实现。

当你写回 `Next Action Or Recommended Skill` 时，优先写 canonical `ahe-*` skill ID，而不是自由文本。

常见合法值包括：

- `ahe-bug-patterns`
- `ahe-test-review`
- `ahe-code-review`
- `ahe-traceability-review`
- `ahe-regression-gate`
- `ahe-completion-gate`

如果当前是因为后续质量能力或门禁返回 `需修改` / `阻塞` 而重新进入本 skill：

- 先读取评审或门禁结论中的发现项、风险和修订建议
- 明确本次回流来源以及当前要修的发现项 / 风险 / 失败用例
- 定位需要修正的具体代码或测试区域
- 优先修复 `critical` 与 `important` 级别的问题
- 修复完成后，应把 fresh evidence、剩余风险和 canonical 推荐下一步写回工件，并从触发回流的那个质量能力或门禁恢复后续编排，而不是从质量链起点重走
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

## 非 C++ 最小执行契约

若项目不是 C++ / GoogleTest，也不能把当前 skill 降级成“先随便实现，再看情况”：

- 仍然必须锁定唯一活跃任务
- 仍然必须先做测试设计并等待真人确认
- 仍然必须完成有效 RED / GREEN / REFACTOR
- 仍然必须写回 fresh evidence、剩余风险和 canonical 下一步
- 仍然必须在交接块中写明当前语言 / 框架 / 命令入口

当前这份 skill 只在附录部分为 C++ / GoogleTest 提供深度示例；这不等于非 C++ 项目可以跳过实现契约本身。

## 与下游质量节点的边界

- `ahe-bug-patterns` 负责在实现完成后做缺陷模式排查，不替代本 skill 的 TDD 与实现证据
- `ahe-test-review` 重点检查 fail-first 纪律、测试质量和当前任务级证据；本 skill 要为它准备证据，而不是代它出 verdict
- `ahe-code-review` 重点检查实现级正确性、状态安全性和局部设计一致性；本 skill 要为它准备实现交接块、测试证据和必要上下文，而不是代它做实现质量裁决
- `ahe-traceability-review` 重点检查规格、设计、任务、实现、测试和验证证据之间的链路一致性；本 skill 只提供实现交接块与 fresh evidence，不代替它完成 evidence-chain 判断
- `ahe-regression-gate` 负责更广义的回归验证和 gate 记录；本 skill 只负责当前任务级证明命令和 fresh evidence
- `ahe-completion-gate` 之前，不得因为当前任务已经实现就提前宣布“整个工作完成”

对下游 review 型节点，父会话不应在当前实现上下文里直接内联评审。应由当前父会话按 review dispatch protocol 派发独立 reviewer subagent 去执行 `ahe-test-review`、`ahe-code-review`、`ahe-traceability-review`；当当前父会话是 `ahe-workflow-starter` 时，由 starter 完成该派发。本 skill 只负责把它们需要消费的输入准备好。

## 工作流

### 1. 对齐上下文并锁定唯一活跃任务

阅读：

- `AGENTS.md` 中与当前任务相关的 testing / coding 约定（如果存在）
- 主链实现读取已批准任务计划；hotfix 实现读取 `ahe-hotfix` 产出的复现路径、最小修复边界与 handoff 记录
- 当前进度或状态记录
- 当前任务对应的规格和设计片段
- 若当前是 hotfix 或回流修订，追加阅读对应来源节点的发现项、失败用例、复现路径或阻塞证据

只选定一个活跃任务。

默认顺序：

1. 先读 `task-progress.md` 中的 `Current Active Task`
2. 若当前是主链实现，再用已批准任务计划校验该任务是否真实存在、仍然有效，并读取其中的测试设计种子
3. 若当前是 hotfix 实现，则用 `ahe-hotfix` 产出的复现路径、最小修复边界和 handoff 记录校验当前任务；只有当该 hotfix 已关联任务计划时，才补读对应测试设计种子
4. 如果当前是回流修订，再补读来源节点的发现项、失败用例或阻塞证据
5. 若这些证据冲突，暂停实现并先修正状态记录或回到上游编排，不直接继续编码

### 2. 产出测试设计，并先做轻量自检

在进入 TDD 之前，先输出当前任务的测试设计，至少说明：

- 要验证哪些行为
- 关键正向 / 反向场景
- 边界条件
- 预期输入与输出
- 哪些测试应先失败
- 若 `AGENTS.md` 要求分层测试，当前哪些测试属于单测 / 集成测 / 其它层次
- 若任务计划中已给出测试设计种子，当前设计与种子是否一致；若不一致，差异是什么

在把测试设计展示给真人前，先做一轮轻量自检：

- 是否覆盖了当前任务最关键的成功行为
- 是否覆盖了关键反向或边界场景（如果适用）
- 当前测试能抓住哪类“错误但看起来像是完成了”的实现
- 是否把 mock 限定在真正的边界，而不是 mock 自己要验证的逻辑

测试设计应优先反映 `AGENTS.md` 中声明的测试分层、命令入口和覆盖要求。

然后：

1. 把测试用例设计展示给真人
2. 邀请真人确认“这些测试是否满足当前预期”
3. 如果真人提出意见，继续对话并修改测试设计
4. 只有在真人明确确认后，才能进入下一步

### 3. 执行有效 TDD

对于当前任务：

1. 先写失败测试
2. 运行并确认失败原因符合预期
3. 写最小实现让测试通过
4. 运行当前任务级证明命令，并确认新的通过结果来自本次会话
5. 在全绿后做必要的最小重构

有效 RED 至少满足：

- 当前会话里真的执行过测试或等价验证命令
- 失败直接对应当前要实现 / 修复的行为缺口
- 你能说清失败为何符合预期，并留下可复用的失败摘要

以下情况不算有效 RED：

- 只写了测试，但没有运行
- 测试一跑就是绿的
- 与当前任务无关的旧失败、环境故障或无关编译错误
- 你看不出失败到底在证明什么

有效 GREEN 至少满足：

- 当前任务对应的测试已经转绿
- `AGENTS.md` 或当前项目要求的最小证明命令在本次会话里成功执行
- 你保留了 fresh evidence，而不是引用旧的通过结果

### 4. 生成实现交接块并同步状态

在声称任务完成之前，至少写回一个稳定的实现交接块，供后续 review / gate 直接消费。

对 review 型下游节点，这个交接块也是 reviewer subagent 的最小核心输入之一：

```md
## 实现交接块

- Task ID:
- 回流来源: 主链实现 | `ahe-hotfix` | `ahe-bug-patterns` | `ahe-test-review` | `ahe-code-review` | `ahe-traceability-review` | `ahe-regression-gate` | `ahe-completion-gate`
- 触碰工件:
- 测试设计确认证据:
- RED 证据: <命令 + 失败摘要 + 为什么这是预期失败>
- GREEN 证据: <命令 + 通过摘要 + 关键结果>
- 与任务计划测试种子的差异:
- 剩余风险 / 未覆盖项:
- Pending Reviews And Gates:
- Next Action Or Recommended Skill:
```

交接块中的 `Next Action Or Recommended Skill` 应使用 canonical skill ID：

- 正常主链实现完成后：
  - full / standard 通常写 `ahe-bug-patterns`
  - lightweight 通常写 `ahe-regression-gate`
- 若当前是下游 quality node 回流修订完成后再恢复，则通常写回触发回流的那个 node，例如 `ahe-bug-patterns`、`ahe-test-review`、`ahe-code-review`、`ahe-regression-gate`

当后续 canonical 下一步是 review 节点时，含义是：

- 父会话应把该节点视为 review dispatch 目标
- 由当前父会话派发独立 reviewer subagent
- 当前父会话可以是 `ahe-workflow-starter`，也可以是当前上游产出 skill
- reviewer subagent 消费当前实现交接块并执行对应 `ahe-*review`

同步更新 `task-progress.md` 中当前任务的进展与待处理质量节点，但不要在本 skill 内替代 starter 做完整路由判断。

### 5. 回流修订协议

如果当前是因为 hotfix、review 或 gate 回流重新进入本 skill：

1. 明确回流来源
2. 明确当前只修哪一个活跃任务、哪一组发现项或失败用例
3. 若修订改变了行为预期或测试设计，需要重新做测试设计确认
4. 若只是修正文档化缺陷、实现遗漏或已知错误实现，则在当前任务范围内补 RED / GREEN 证据
5. 修订完成后，把新的 fresh evidence 和 canonical 下一步写回交接块，而不是把质量链从头再走一遍

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
| “不是 C++，那这套规则先不管了” | 非 C++ 也必须遵守同一实现契约，只是附录示例深度不同。 |
| “下一步先写成一句自然语言，starter 自己会猜” | `Next Action Or Recommended Skill` 优先写 canonical `ahe-*` skill ID。 |
| “现在已经差不多了，可以先说完成” | 完成要等评审、回归和完成门禁都走完。 |
| “这些 review 太重了，先跳过一个” | 后续质量能力与门禁由 `ahe-workflow-starter` 按当前 profile 恢复编排，不能在本节点内擅自省略或重排。 |
| “旧的绿测结果也能证明这次改动没问题” | 必须有当前任务对应的新鲜证据。 |

## C++ / GoogleTest 深度附录

如果当前项目是 C++ / GoogleTest / CMake 栈，按以下更细的语言级指南执行。

如果当前项目不是 C++，跳过本附录，但不要跳过上文的实现契约、测试设计确认、有效 RED / GREEN 和实现交接块要求。

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

以下情况不算有效 RED：

- 与当前任务无关的既有失败
- 环境损坏、依赖缺失或基础构建链本身异常
- 你看不出失败到底对应哪条行为预期

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
- 通过结果来自本次会话，而不是引用旧日志
- 已记录当前任务级 proving command 和关键输出摘要，便于写入实现交接块

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

如果你不清楚如何运行当前项目的测试命令，优先查看 `AGENTS.md` 中关于编译、构建和验证的相关信息。

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
- [ ] 已写回实现交接块，并包含 canonical `Next Action Or Recommended Skill`

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

只有在测试设计已经过真人确认，且当前任务已经完成实现，并把 fresh verification evidence、剩余风险和 canonical 推荐下一步写回实现交接块与状态工件，或明确报告了阻塞问题后，这个 skill 才算完成。
