# 测试反模式

## 目的

常见测试误区目录，易产生虚假信心。编写或评审测试质量时参考本文。

## 反模式目录

### 1. 测 Mock 行为而非真实行为

**现象**：测试全绿，但特性实际不工作。

**示例（错误）**：
```python
def test_user_login(mock_db):
    mock_db.get_user.return_value = User(id=1, name="test")
    result = login("test", "password")
    mock_db.get_user.assert_called_once_with("test")  # Testing the mock!
```

**为何失败**：你在验证代码是否「正确调用 mock」，而非登录是否真能用。

**修复**：尽量用真实依赖（测试库、内存实现）。仅 mock 不可控的外部服务。

### 2. 在生产代码中增加仅测试用的方法

**现象**：生产代码含 `_test_helper()`、`get_for_testing()` 等。

**为何失败**：生产代码不应感知测试。测试专用方法可能被生产调用，增加维护与风险。

**修复**：通过公开接口测试。若无后门就测不了，说明设计需重构。

### 3. 不理解依赖就 Mock

**现象**：每个测试 mock 一切，不清楚每个 mock 代表什么。

**为何失败**：过度 mock 使测试脆弱（实现一改就碎）且无意义（测的是接线，不是行为）。

**修复**：
- mock 前先理解依赖
- 在边界 mock（HTTP、文件系统、时间），不在内部层
- 复杂依赖优先 fake（内存实现）而非 mock

### 4. 测试实现细节

**现象**：未改行为仅重构，测试就挂。

**示例（错误）**：
```python
def test_sort():
    result = sort_list([3, 1, 2])
    # Testing that quicksort was used (implementation detail)
    assert mock_quicksort.called
```

**修复**：断言输出，而非如何算出：
```python
def test_sort():
    result = sort_list([3, 1, 2])
    assert result == [1, 2, 3]
```

### 5. 非确定性测试

**现象**：有时过有时挂。

**常见原因**：
- 依赖当前时间/日期
- 随机数无固定种子
- 异步竞态
- 测试间共享状态
- 对外网真实请求

**修复**：控制所有非确定性来源。固定时间戳、固定种子、正确处理异步、测试隔离、网络 mock。

### 6. 不可能失败的测试

**现象**：无论实现如何，测试总通过。

**示例（错误）**：
```python
def test_something():
    try:
        result = do_thing()
        assert result is not None
    except:
        pass  # Swallowing the failure!
```

**修复**：始终先做 TDD Red —— 实现前测试就通过，说明测试写错了。

### 7. 单测里塞太多行为

**现象**：一条测试 20+ 断言，覆盖多种行为。

**为何失败**：失败时不知道哪条行为坏了，难调试。

**修复**：一行为一测。测试名描述单一行为。

### 8. 测试间共享可变状态

**现象**：单跑通过，整包失败。

**为何失败**：一测改了另一测依赖的共享状态。

**修复**：每测自建自拆状态。新 fixture、事务、隔离容器。

### 9. 无断言测试

**现象**：跑了代码但没有有意义的断言。

**示例（错误）**：
```python
def test_create_user():
    create_user("test", "test@email.com")
    # No assertion! Just checking it doesn't throw.
```

**修复**：断言可观察结果：
```python
def test_create_user():
    user = create_user("test", "test@email.com")
    assert user.name == "test"
    assert user.email == "test@email.com"
```

### 10. 复制粘贴整份测试套件

**现象**：大量重复、微改的测试，难维护。

**修复**：变体用参数化测试。共享 setup 抽 fixture。但别过度抽象 —— 测试应易读。

### 11. 用无断言测试刷覆盖率

**现象**：覆盖率数字高，断言很弱或没有。

**示例（错误）**：
```python
def test_process_data():
    process_data(sample_input)  # 100% line coverage, 0% verification
```

**为何失败**：只跑路径不验正确性，虚假信心；实现返回垃圾也不会失败。

**修复**：每条测试必须断言可观察结果。变异测试能暴露 —— 若变异体存活，说明没在验结果。

```python
def test_process_data():
    result = process_data(sample_input)
    assert result.status == "success"
    assert result.count == 42
```

### 12. 忽略幸存变异体

**现象**：变异分数低于阈值仍标特性为 passing。

**为何失败**：幸存变异体是测试抓不住的缺陷。把 `>` 改成 `>=` 若无测试失败，说明边界逻辑未测。

**修复**：对每个幸存变异体：
- **真缺口**：加测试杀死它
- **等价变异**：文档说明为何行为等价（如 `# equivalent mutant: condition is always true due to precondition on line X`）
- **绝不无视**：每个幸存者须处理（修或文档）

### 13. 在未覆盖代码上做变异测试

**现象**：未达覆盖率阈值就跑变异，大量变异显示「无覆盖」。

**为何失败**：未覆盖代码上的变异会产生大量假幸存、浪费时间 —— 本来就没有测试去杀变异体。

**修复**：始终先过覆盖率门禁，再跑变异。先覆盖，后变异。

### 14. 低价值断言（存在性/类型/导入测试）

**现象**：断言存在、类型或导入成功 —— 这些往往只有语言运行时彻底坏了才会失败，实现有 bug 仍可能过。

**示例（均属错误）**：

```python
# BAD: Testing that a function returns something (not WHAT it returns)
def test_get_user():
    result = get_user(1)
    assert result is not None

# BAD: Testing that import works
def test_import():
    from mymodule import MyClass
    assert MyClass is not None

# BAD: Testing type instead of behavior
def test_create_user():
    result = create_user("Alice", "alice@example.com")
    assert isinstance(result, User)

# BAD: Testing that a list has items (but not WHICH items)
def test_list_users():
    result = list_users()
    assert len(result) > 0

# BAD: Testing that a dict has a key (but not WHAT value)
def test_get_profile():
    result = get_profile(1)
    assert "name" in result

# BAD: Testing truthiness instead of value
def test_validate():
    result = validate_email("test@example.com")
    assert bool(result)

# BAD: Testing that no exception is raised (without checking result)
def test_process():
    result = process_data(sample)  # No assertion on result at all
```

**危害**：
- 只要返回*某个东西*就容易过，不管实际返回什么
- 虚增覆盖率与用例数，几乎无找 bug 能力
- 变异测试也未必全抓住 —— 部分变异仍保持类型/存在性
- 挤占有意义断言，造成对套件质量的虚假信心

**「错误实现」测试**：对每条断言问：*「哪种错误实现这条测试抓不到？」* 若答案是「几乎任何错误实现」→ 低价值断言。

示例：`assert result is not None` —— 返回 `User(name="WRONG", email="WRONG")`、`42`、`""` 都能过。几乎只抓 `None`。

**修复 —— 断言具体可观察结果**：

```python
# GOOD: Assert specific values
def test_get_user():
    result = get_user(1)
    assert result.name == "Alice"
    assert result.email == "alice@example.com"

# GOOD: Assert specific items in collection
def test_list_users():
    result = list_users()
    assert len(result) == 3
    assert result[0].name == "Alice"

# GOOD: Assert specific response structure AND content
def test_get_profile():
    result = get_profile(1)
    assert result["name"] == "Alice"
    assert result["role"] == "admin"

# GOOD: Assert specific boolean outcome for specific input
def test_validate():
    assert validate_email("test@example.com") is True
    assert validate_email("not-an-email") is False

# GOOD: Assert specific error for specific invalid input
def test_create_user_invalid():
    with pytest.raises(ValidationError, match="email is required"):
        create_user(name="test", email="")

# GOOD: Assert specific state change
def test_process():
    result = process_data(sample)
    assert result.status == "completed"
    assert result.processed_count == 42
```

**量化规则**：低价值断言数 / 总断言数不得超过 **20%**：

```
low_value_count / total_assertion_count <= 0.20
```

低价值模式（计数用）：
- `assert x is not None` / `assert x is None`（测默认值而非行为时）
- `assert isinstance(x, SomeType)`
- `assert len(x) > 0`（未检查元素）
- `assert "key" in dict`（未检查值）
- `assert bool(x)` / `assert x`（仅真值）
- `from module import X; assert X is not None`（导入测试）
- 完全无断言的测试（见反模式 #9）

**与其它反模式关系**：比 #9、#11 更具体。可有断言但仍低价值。变异（#12）能抓部分但非全部 —— 20% 规则在写测时提供额外约束。

### 15. 全 Mock 的「真实测试」（Mock 标签洗钱）

**现象**：测试被标为真实测试（marker/命名/标签），但函数体 mock 了其所声称要验证的主外部依赖。

**示例（错误 —— Python）**：
```python
@pytest.mark.real_test
def test_real_db_connection(mock_session):  # mock_session replaces real connection!
    repo = UserRepository(mock_session)
    repo.save(User(name="Alice"))
    mock_session.add.assert_called_once()  # Testing the mock, not the real DB
```

**为何失败**：标签暗示测真实基础设施，实际全是 mock。ORM 映射错误、连接串、SQL schema 变更都测不到。`check_real_tests.py` 会 grep mock 关键字并 WARN。

**修复**：真实测试函数体**不得** mock 其所验证的主依赖。

**检测**：`python scripts/check_real_tests.py feature-list.json`。

**关系**：Rule 5a 在 TDD Red 预防；`long-task-quality/SKILL.md` Gate 0 用脚本 + LLM 抽样强制执行。

### 16. 静默跳过（环境守卫绕过）

**现象**：真实测试在函数开头检查基础设施，缺失时提前 return 或 skip —— 测试「通过」但未执行任何断言。

**示例（错误 —— Python）**：
```python
@pytest.mark.real_test
def test_real_db_write():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return  # Silently passes! No assertion executed.
    conn = connect(db_url)
    conn.execute("INSERT INTO users ...")
    assert conn.execute("SELECT count(*) FROM users").fetchone()[0] == 1
```

**示例（错误 —— TypeScript/Vitest）**：
```typescript
// @real_test feature_5
test("real db write", () => {
  if (!process.env.DATABASE_URL) return; // Silently passes!
  const db = connect(process.env.DATABASE_URL);
  db.execute("INSERT INTO users ...");
  expect(db.query("SELECT count(*) FROM users")[0]).toBe(1);
});
```

**为何失败**：测试报告显示 0 失败；覆盖工具把早退路径算覆盖；看似通过却什么也没验。缺基础设施才是问题 —— 静默忽略违背真实测试目的。

**检测模式**（与语言无关）：
- `if not env_var: return` / `if (!process.env.X) return`
- 基于环境变量的 `pytest.mark.skipif` / `unittest.skip` / `@Disabled` / `test.skip`
- 真实测试的 skipped/pending 计数 > 0
- C++ 测试体中的 `GTEST_SKIP()`

**修复**：基础设施不可用时真实测试必须**大声失败**。用显式断言失败：
```python
@pytest.mark.real_test
def test_real_db_write():
    db_url = os.environ.get("DATABASE_URL")
    assert db_url, "DATABASE_URL not set — real test infrastructure missing"
    # ... actual test logic
```

**检测**：`python scripts/check_real_tests.py feature-list.json` —— 对真实测试体做 skip 模式的静态扫描。

**关系**：与 #15 互补。#15 抓 mock 假真实；#16 抓静默跳过。二者都造成连通性虚假信心。`long-task-quality/SKILL.md` Gate 0 步骤 3 要求测试输出中 `skipped 0` 以在运行时检测 skip。

## 速查：测试编写检查清单

标记测试完成前：

- [ ] 无实现时测试失败（已验证 TDD Red）
- [ ] 测试名描述被测行为
- [ ] 有意义断言（非仅「无异常」）
- [ ] 确定性（结果稳定）
- [ ] 独立（不依赖其它测试状态）
- [ ] 测行为不测实现细节
- [ ] 未向生产代码加仅测试方法
- [ ] Mock 在边界，不在内部层
- [ ] 测试文件含 `check_real_tests.py` 可发现的真实测试（Rule 5a）
- [ ] `check_real_tests.py` 无 mock 警告（或已复核为非主依赖 mock）
- [ ] 基础设施不可用时真实测试大声失败（无静默跳过 —— 反模式 #16）
- [ ] 若声称纯函数豁免：已与设计节核对（无外部 I/O）
- [ ] 无低价值断言（None、isinstance、导入、len>0、key-in-dict、真值）
- [ ] 低价值断言比例 ≤ 总断言 20%
- [ ] 每条断言对某种 plausible 错误实现会失败（「错误实现」测试）
- [ ] 覆盖率达到项目阈值（行 ≥ 90%，分支 ≥ 80%）
- [ ] 变更文件变异分数达阈值（≥ 80%）
- [ ] 无未说明理由的幸存变异体
