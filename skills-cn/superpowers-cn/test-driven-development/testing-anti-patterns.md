# 测试反模式

**在以下情况加载本参考：**编写或修改测试、添加 mock，或忍不住想在生产代码上加仅测试用的方法时。

## 概述

测试必须验证**真实行为**，不是 mock 的行为。Mock 用于隔离，不是被测对象。

**核心原则：**测代码**做什么**，不要测 mock **做什么**。

**严格遵循 TDD 能避免这些反模式。**

## 铁律

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
```

## 反模式 1：测 Mock 行为

**违规：**
```typescript
// ❌ BAD: Testing that the mock exists
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**为何错误：**
- 你在验证 mock 能用，而不是组件真能用
- mock 在就过、不在就挂
- 对真实行为一无所知

**与你协作的人的纠正：**「我们是在测 mock 的行为吗？」

**修正：**
```typescript
// ✅ GOOD: Test real component or don't mock it
test('renders sidebar', () => {
  render(<Page />);  // Don't mock sidebar
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});

// OR if sidebar must be mocked for isolation:
// Don't assert on the mock - test Page's behavior with sidebar present
```

### 门禁函数

```
BEFORE asserting on any mock element:
  Ask: "Am I testing real component behavior or just mock existence?"

  IF testing mock existence:
    STOP - Delete the assertion or unmock the component

  Test real behavior instead
```

## 反模式 2：生产类中的仅测试方法

**违规：**
```typescript
// ❌ BAD: destroy() only used in tests
class Session {
  async destroy() {  // Looks like production API!
    await this._workspaceManager?.destroyWorkspace(this.id);
    // ... cleanup
  }
}

// In tests
afterEach(() => session.destroy());
```

**为何错误：**
- 生产类被仅测试代码污染
- 若在生产误调用很危险
- 违背 YAGNI 与关注点分离
- 混淆对象生命周期与实体生命周期

**修正：**
```typescript
// ✅ GOOD: Test utilities handle test cleanup
// Session has no destroy() - it's stateless in production

// In test-utils/
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) {
    await workspaceManager.destroyWorkspace(workspace.id);
  }
}

// In tests
afterEach(() => cleanupSession(session));
```

### 门禁函数

```
BEFORE adding any method to production class:
  Ask: "Is this only used by tests?"

  IF yes:
    STOP - Don't add it
    Put it in test utilities instead

  Ask: "Does this class own this resource's lifecycle?"

  IF no:
    STOP - Wrong class for this method
```

## 反模式 3：未理解就 Mock

**违规：**
```typescript
// ❌ BAD: Mock breaks test logic
test('detects duplicate server', () => {
  // Mock prevents config write that test depends on!
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));

  await addServer(config);
  await addServer(config);  // Should throw - but won't!
});
```

**为何错误：**
- 被 mock 的方法有测试依赖的副作用（写配置）
- 为「保险」过度 mock 破坏了真实行为
- 测试因错误原因通过或神秘失败

**修正：**
```typescript
// ✅ GOOD: Mock at correct level
test('detects duplicate server', () => {
  // Mock the slow part, preserve behavior test needs
  vi.mock('MCPServerManager'); // Just mock slow server startup

  await addServer(config);  // Config written
  await addServer(config);  // Duplicate detected ✓
});
```

### 门禁函数

```
BEFORE mocking any method:
  STOP - Don't mock yet

  1. Ask: "What side effects does the real method have?"
  2. Ask: "Does this test depend on any of those side effects?"
  3. Ask: "Do I fully understand what this test needs?"

  IF depends on side effects:
    Mock at lower level (the actual slow/external operation)
    OR use test doubles that preserve necessary behavior
    NOT the high-level method the test depends on

  IF unsure what test depends on:
    Run test with real implementation FIRST
    Observe what actually needs to happen
    THEN add minimal mocking at the right level

  Red flags:
    - "I'll mock this to be safe"
    - "This might be slow, better mock it"
    - Mocking without understanding the dependency chain
```

## 反模式 4：不完整的 Mock

**违规：**
```typescript
// ❌ BAD: Partial mock - only fields you think you need
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' }
  // Missing: metadata that downstream code uses
};

// Later: breaks when code accesses response.metadata.requestId
```

**为何错误：**
- **部分 mock 掩盖结构假设** — 只 mock 你知道的字段
- **下游可能依赖你没带的字段** — 静默失败
- **测试过、集成挂** — mock 不完整，真实 API 完整
- **虚假信心** — 测试证明不了真实行为

**铁律：**按**现实中**的完整数据结构 mock，不要只 mock 当前测试立刻用到的字段。

**修正：**
```typescript
// ✅ GOOD: Mirror real API completeness
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 }
  // All fields real API returns
};
```

### 门禁函数

```
BEFORE creating mock responses:
  Check: "What fields does the real API response contain?"

  Actions:
    1. Examine actual API response from docs/examples
    2. Include ALL fields system might consume downstream
    3. Verify mock matches real response schema completely

  Critical:
    If you're creating a mock, you must understand the ENTIRE structure
    Partial mocks fail silently when code depends on omitted fields

  If uncertain: Include all documented fields
```

## 反模式 5：集成测试当后话

**违规：**
```
✅ Implementation complete
❌ No tests written
"Ready for testing"
```

**为何错误：**
- 测试是实现的一部分，不是可选收尾
- TDD 本会拦住这种情况
- 没有测试不能叫完成

**修正：**
```
TDD cycle:
1. Write failing test
2. Implement to pass
3. Refactor
4. THEN claim complete
```

## Mock 过于复杂时

**警示信号：**
- Mock setup 比测试逻辑还长
- 为让测试通过而 mock 一切
- Mock 缺少真实组件有的方法
- Mock 一变测试就挂

**与你协作的人会问：**「这里真的需要 mock 吗？」

**考虑：**用真实组件的集成测试往往比复杂 mock 更简单

## TDD 如何预防

**TDD 的帮助：**
1. **先写测试** → 迫使你想清到底在测什么
2. **看它失败** → 确认测的是真实行为而非 mock
3. **最少实现** → 不易渗入仅测试方法
4. **真实依赖** → mock 之前你已看到测试真正需要什么

**若你在测 mock 行为，你已违背 TDD** — 你在未先对真实代码看到失败的情况下就加了 mock。

## 速查

| 反模式 | 修正 |
|--------------|-----|
| 对 mock 元素断言 | 测真实组件或取消 mock |
| 生产类里仅测试方法 | 移到测试工具 |
| 不理解就 mock | 先理解依赖，最小化 mock |
| Mock 不完整 | 完整镜像真实 API |
| 测试当后话 | TDD — 测试先行 |
| Mock 过度复杂 | 考虑集成测试 |

## 红旗

- 断言在查 `*-mock` 测试 ID
- 方法只在测试文件里被调用
- Mock setup 占测试一半以上
- 去掉 mock 测试就挂
- 说不清为什么需要 mock
- 「为保险 mock 一下」

## 结论

**Mock 是隔离工具，不是被测对象。**

若 TDD 让你发现自己在测 mock 行为，你已经走偏了。

修正：测真实行为，或质疑是否根本不该在这里 mock。
