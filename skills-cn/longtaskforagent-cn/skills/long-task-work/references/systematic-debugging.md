# 系统化调试

## 铁律

**未先做根因调查，不得修复。**

切勿凭猜测改代码。始终将缺陷追踪到根因，再修复该根因。

## 适用范围

- TDD Green 或 Refactor 阶段测试失败
- 冒烟测试发现回归
- Chrome DevTools MCP 功能测试运行时错误
- Bootstrap 阶段构建或环境失败
- 实现过程中任何意外行为

## 四阶段调试流程

### 阶段 1：根因调查

**目标**：理解**发生什么**、**在何处**。

1. **收集错误证据**：
   - 阅读完整错误信息（不要只看第一行）
   - 记录堆栈——哪个文件、哪一行、哪个函数
   - 记录触发错误的具体命令/动作

2. **稳定复现**：
   - 能否一致触发？
   - 最小复现是什么？
   - 孤立运行才出现，还是与其他特性一起才出现？

3. **检查近期变更**：
   - `git diff` —— 自上次正常以来改了什么？
   - `git log --oneline -10` —— 最近提交？
   - 当前改动之前错误就存在吗？

4. **追踪数据流**：
   - 从入口到错误位置跟踪失败输入
   - 必要时记录中间值
   - 找出实际行为与预期何处分叉

### 阶段 2：模式分析

**目标**：理解**为何**发生。

1. **找正常示例**：
   - 是否有类似但正确的代码？
   - 正常路径与损坏路径有何不同？

2. **检查依赖**：
   - 依赖是否齐全且版本正确？
   - 上游 API 或 schema 是否变更？
   - 环境变量/配置是否正确？

3. **对比上下文**：
   - 本地通过、测试失败（或相反）？
   - 某种输入通过、另一种失败？
   - 是否依赖时序（竞态）？

### 阶段 3：假设与验证

**目标**：形成**一个**假设并验证。

1. **形成单一假设**：
   - 例如：「错误因 X 为 null 而 Y 期望非 null」
   - 要具体——模糊假设导致模糊修复

2. **设计最小测试**：
   - 最小改动如何证实或证伪假设？
   - 能否加针对性断言或日志？

3. **验证假设**：
   - **仅**做诊断性改动
   - 运行失败用例
   - 假设成立吗？

4. **若假设错误**：
   - 记录所学
   - 带着新信息回到阶段 1
   - **不要**随机尝试修复

### 阶段 4：实现

**目标**：用已验证方案修复根因。

1. **为缺陷编写失败测试**：
   - 测试应因与原 bug 相同原因失败
   - 防止回归

2. **实施单一、针对性修复**：
   - 只修阶段 3 认定的根因
   - 避免「顺便」改动

3. **验证修复**：
   - 新测试通过
   - 既有测试仍通过
   - 原错误不再出现

4. **若尝试 3 次仍失败**：
   - 停止并重新审视根因
   - 可能根因判断错误
   - 考虑向用户求助或补充上下文

## 辅助技术

### 根因回溯

沿调用栈反向追踪：

```
Error at line N in file F
  ← Called from line M in file G
    ← Called from line K in file H
      ← Root cause: incorrect value set at line K in file H
```

从错误向回找到错误值引入点。

### 纵深防御

修复根因后，可考虑在多层增加校验：

```
Layer 1: Input validation     → Reject bad data early
Layer 2: Function preconditions → Assert expected state
Layer 3: Output verification   → Confirm correct results
```

仅添加有目的的校验——不要为不可能状态堆防御代码。

### 基于条件的等待（时序类缺陷）

用条件轮询替代任意 sleep：

```
# BAD: sleep(5) and hope the server is ready
# GOOD: Poll until condition is met or timeout expires

wait_for("Expected text", timeout=10000)
```

非 UI 时序问题：
```python
# Poll with backoff
for attempt in range(max_retries):
    result = check_condition()
    if result:
        break
    time.sleep(backoff * attempt)
else:
    raise TimeoutError("Condition not met")
```

### 测试污染检测

单测通过、整包失败时，通常是共享状态被其他测试污染。

二分思路：
1. 失败用例与套件前半一起跑 → 仍失败？
2. 若是 → 污染源在前半；再二分
3. 若否 → 污染源在后半；再二分
4. 重复直至定位单条污染测试
5. 修复污染者（清理其共享状态）

## 危险信号（停手反思）

| 危险信号 | 含义 | 正确应对 |
|----------|----------------|-----------------|
| "Let me just try this quick fix" | 跳过根因分析 | 回到阶段 1 |
| "It's probably X, let me change it" | 无证据猜测 | 形成可检验假设 |
| "I'll add a try/catch to suppress the error" | 掩盖症状非修因 | 找到并修复根因 |
| "Let me restart everything and try again" | 指望问题自己消失 | 先稳定复现 |
| "This worked before, not sure what changed" | 需要看 git diff | 对比当前与最后已知良好状态 |
| 第三次修复仍失败 | 根因可能认错 | 停，从阶段 1 重新评估 |

## 调试决策树

```
Error encountered
  │
  ├─ Can reproduce? ─── No ──→ Add logging, try again
  │                              (make it reproducible first)
  ├─ Yes
  │
  ├─ Recent change caused it? ─── Yes ──→ git diff, focus on changes
  │
  ├─ No / Unknown
  │
  ├─ Trace to root cause ──→ Found cause? ─── Yes ──→ Write test → Fix → Verify
  │
  ├─ No
  │
  ├─ Find working example ──→ Compare differences ──→ Form hypothesis
  │
  └─ Hypothesis holds? ─── Yes ──→ Write test → Fix → Verify
                          No ──→ Record learning → Return to trace
```
