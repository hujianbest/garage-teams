---
name: mdc-implement
description: 以受控方式执行已批准的 MDC 任务计划并完成实现。适用于任务计划已通过评审，且实现阶段应按任务逐项推进、遵循 TDD、验证与评审流程、不允许跳步的场景。
---

# MDC 实现

按已批准任务计划，一次实现一个任务。

## 硬性门禁

任务计划未通过评审前，不得开始实现。

当前任务在实现、评审、验证完成之前，不得切换到下一个任务。

## 核心规则

一次只允许有一个活跃任务。

## TDD 规则

除非当前任务明确属于非代码配置类工作且该例外已被记录，否则不得在没有失败测试的前提下编写生产代码。

## 工作流

### 1. 对齐上下文

阅读：

- 已批准任务计划
- 当前进度或状态记录
- 当前任务对应的规格和设计片段

只选定一个活跃任务。

### 2. 按 Red-Green-Refactor 执行

对于当前任务：

1. write or update a failing test
2. run it and confirm the failure is meaningful
3. implement the minimum change
4. rerun and confirm pass
5. refactor while keeping tests green

### 3. 准备评审输入

在声称任务完成之前：

- 明确本次改了什么
- 明确哪些测试在证明它
- 明确还存在哪些风险区域

### 4. 交给评审与门禁

当前任务实现完成后：

1. use `mdc-test-review`
2. then use `mdc-code-review`
3. then use `mdc-regression-gate`
4. then use `mdc-completion-gate`

这个顺序是强制的。

## 强制顺序

```text
实现 -> 测试评审 -> 代码评审 -> 回归门禁 -> 完成门禁
```

不要因为任务看起来简单就跳过评审。

## 反模式

- 并行处理多个任务
- 先写实现，再补失败测试
- 把旧的绿测结果当成当前证据
- 在完成门禁前就说“做完了”
- 因为当前任务变麻烦就切换任务

## 完成条件

只有在当前任务已经经过评审和完成门禁，或明确报告了阻塞问题后，这个 skill 才算完成。
