---
name: test-driven-development
description: 在实现任何功能或修复任何 bug 时使用，在编写实现代码之前
---

# 测试驱动开发（TDD）

## 概述

先写测试。看它失败。写最少代码让它通过。

**核心原则：**若你没看到测试失败，就不知道它测的是不是对的东西。

**违背规则的字面要求，就是违背规则的精神。**

## 何时使用

**始终：**
- 新功能
- Bug 修复
- 重构
- 行为变更

**例外（先问你协作的人）：**
- 用完即弃的原型
- 生成代码
- 配置文件

心想「就这一次跳过 TDD」？停。那是自我辩解。

## 铁律

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

测试之前就写了实现？删掉。重来。

**没有例外：**
- 不要留着当「参考」
- 不要边写测试边「改编」它
- 不要去看它
- 删就是删

完全依据测试重新实现。没有商量。

## 红-绿-重构

```dot
digraph tdd_cycle {
    rankdir=LR;
    red [label="RED\nWrite failing test", shape=box, style=filled, fillcolor="#ffcccc"];
    verify_red [label="Verify fails\ncorrectly", shape=diamond];
    green [label="GREEN\nMinimal code", shape=box, style=filled, fillcolor="#ccffcc"];
    verify_green [label="Verify passes\nAll green", shape=diamond];
    refactor [label="REFACTOR\nClean up", shape=box, style=filled, fillcolor="#ccccff"];
    next [label="Next", shape=ellipse];

    red -> verify_red;
    verify_red -> green [label="yes"];
    verify_red -> red [label="wrong\nfailure"];
    green -> verify_green;
    verify_green -> refactor [label="yes"];
    verify_green -> green [label="no"];
    refactor -> verify_green [label="stay\ngreen"];
    verify_green -> next;
    next -> red;
}
```

### 红 — 写失败的测试

写一个最小测试，展示**应该**发生什么。

<Good>
```typescript
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```
名称清晰、测真实行为、只测一件事
</Good>

<Bad>
```typescript
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```
名称模糊、测的是 mock 不是代码
</Bad>

**要求：**
- 一种行为
- 名称清楚
- 真实代码（除非不得已不要用 mock）

### 验证红 — 看它失败

**强制。绝不跳过。**

```bash
npm test path/to/test.test.ts
```

确认：
- 测试是**失败**（不是报错）
- 失败信息与预期一致
- 因**缺少功能**而失败（不是拼写错误）

**测试通过了？**你在测已有行为。改测试。

**测试报错？**先修错误，重跑到**正确**失败为止。

### 绿 — 最少代码

写能通过测试的最简实现。

<Good>
```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```
刚好够通过
</Good>

<Bad>
```typescript
async function retryOperation<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number) => void;
  }
): Promise<T> {
  // YAGNI
}
```
过度设计
</Bad>

不要加功能、不要重构别处、不要超出测试「改进」。

### 验证绿 — 看它通过

**强制。**

```bash
npm test path/to/test.test.ts
```

确认：
- 测试通过
- 其他测试仍通过
- 输出干净（无错误、无警告）

**测试失败？**改代码，别改测试。

**其他测试挂？**立刻修。

### 重构 — 整理

仅在变绿之后：
- 去重
- 改进命名
- 抽取辅助函数

保持测试绿色。不要加行为。

### 重复

下一个失败测试对应下一项功能。

## 好测试

| 质量 | 好 | 差 |
|---------|------|-----|
| **最小** | 一件事。名称里有「并且」？拆开。 | `test('validates email and domain and whitespace')` |
| **清晰** | 名称描述行为 | `test('test1')` |
| **表达意图** | 展示期望的 API | 掩盖代码应做什么 |

## 为什么顺序重要

**「我写完再补测试验证」**

后写的测试一上来就通过。立刻通过说明不了任何事：
- 可能测错对象
- 可能测实现而不是行为
- 可能漏掉你忘记的边界
- 你从没看到它抓住 bug

测试先行强迫你看到失败，证明测试**确实在测东西**。

**「我已经手动测过所有边界了」**

手动测试是随意的。你以为都测了，但：
- 没有测了什么记录
- 代码一改不能重跑
- 压力下容易忘 case
- 「我当时试是可以的」≠ 全面

自动化测试是系统化的。每次同样方式运行。

**「删掉 X 小时工作是浪费」**

沉没成本谬误。时间已经花掉。你现在只能选：
- 删掉按 TDD 重写（再花 X 小时，信心高）
- 留着后补测试（30 分钟，信心低，易出 bug）

「浪费」是留着无法信任的代码。没有真正测试的能跑代码是技术债。

**「TDD 太教条，务实就要灵活」**

TDD **就是**务实：
- 提交前发现 bug（比上线后调试快）
- 防止回归（测试立刻发现破坏）
- 文档化行为（测试展示如何用代码）
- 支持重构（大胆改，测试抓破坏）

「务实」捷径 = 生产环境调试 = 更慢。

**「后写测试目标一样——重要的是精神不是仪式」**

不。后写回答「这代码在干啥？」先行回答「这代码**应该**干啥？」

后写会被你的实现带偏。你测的是你写的，不是需求。你验证记得的边界，不是发现的边界。

先行迫使在实现**前**发现边界 case。后写验证你是否记得一切（你并没有）。

后写 30 分钟 ≠ TDD。你有覆盖率，但失去了「测试真的有效」的证明。

## 常见自我辩解

| 借口 | 现实 |
|--------|---------|
| 「太简单不用测」 | 简单代码也会坏。测只要 30 秒。 |
| 「我等会再测」 | 立刻通过的测试证明不了什么。 |
| 「后写目标一样」 | 后写 =「干啥？」先行 =「该干啥？」 |
| 「已经手动测过」 | 随意 ≠ 系统化。无记录、不可重跑。 |
| 「删 X 小时是浪费」 | 沉没成本。留着未验证代码是债。 |
| 「留着参考，测试先行写」 | 你会改编它。那就是后写。删就是删。 |
| 「需要先探索」 | 可以。探索完扔掉，从 TDD 开始。 |
| 「难测 = 设计不清」 | 听测试的。难测 = 难用。 |
| 「TDD 会拖慢我」 | TDD 比调试快。务实 = 先行。 |
| 「手动更快」 | 手动证明不了边界。每次改都要重测。 |
| 「老代码没测试」 | 你在改进它。给现有代码补测试。 |

## 红旗——停下重来

- 先写实现再写测试
- 实现之后才写测试
- 测试一跑就过
- 说不清测试为什么失败
- 测试「以后再补」
- 自我辩解「就这一次」
- 「我已经手动测过了」
- 「后写目的也一样」
- 「重要的是精神不是仪式」
- 「留着参考」或「改编现有代码」
- 「已经花了 X 小时，删是浪费」
- 「TDD 教条，我务实」
- 「这次不一样因为……」

**以上任意一条都表示：删代码。用 TDD 重来。**

## 示例：修 Bug

**Bug：**接受空邮箱

**红**
```typescript
test('rejects empty email', async () => {
  const result = await submitForm({ email: '' });
  expect(result.error).toBe('Email required');
});
```

**验证红**
```bash
$ npm test
FAIL: expected 'Email required', got undefined
```

**绿**
```typescript
function submitForm(data: FormData) {
  if (!data.email?.trim()) {
    return { error: 'Email required' };
  }
  // ...
}
```

**验证绿**
```bash
$ npm test
PASS
```

**重构**
若有多字段校验可再抽取。

## 完成前核对清单

在宣称工作完成之前：

- [ ] 每个新函数/方法都有测试
- [ ] 实现前看过每个测试失败
- [ ] 每个测试因预期原因失败（缺功能，不是笔误）
- [ ] 每个测试只用最少代码喂饱
- [ ] 全部测试通过
- [ ] 输出干净（无错误、无警告）
- [ ] 测试用真实代码（除非不得已才 mock）
- [ ] 边界与错误有覆盖

不能全勾？你跳过了 TDD。重来。

## 卡住时

| 问题 | 对策 |
|---------|----------|
| 不知怎么测 | 写你期望的 API。先写断言。问你协作的人。 |
| 测试太复杂 | 设计太复杂。简化接口。 |
| 必须全 mock | 耦合太重。用依赖注入。 |
| 测试 setup 巨大 | 抽辅助函数。仍复杂？简化设计。 |

## 与调试衔接

发现 bug？写失败测试复现。走 TDD 循环。测试既证明修复也防回归。

没有测试不要修 bug。

## 测试反模式

加 mock 或测试工具时，阅读 @testing-anti-patterns.md，避免常见坑：
- 测 mock 行为而不是真实行为
- 在生产类上加仅测试用的方法
- 未理解依赖就 mock

## 最后一条

```
Production code → test exists and failed first
Otherwise → not TDD
```

没有你协作的人许可，没有例外。
