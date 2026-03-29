# 纵深防御式校验

## 概述

当无效数据导致 bug 时，只在一处加校验往往觉得够了。但那条路径可能被其他代码路径、重构或 mock 绕过。

**核心原则：**在数据经过的**每一层**都校验。让这类 bug 在结构上不可能发生。

## 为什么要多层

单层校验：「我们修了这个 bug」  
多层校验：「我们让这类 bug 不可能再发生」

不同层捕获不同情况：
- 入口校验捕获大部分问题
- 业务逻辑捕获边界情况
- 环境守卫防止特定上下文下的危险
- 调试日志在其他层失效时仍有帮助

## 四层

### 第 1 层：入口校验
**目的：**在 API 边界拒绝明显无效输入

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  // ... proceed
}
```

### 第 2 层：业务逻辑校验
**目的：**确保数据对该操作有意义

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### 第 3 层：环境守卫
**目的：**在特定上下文中阻止危险操作

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

### 第 4 层：调试埋点
**目的：**为事后分析保留上下文

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // ... proceed
}
```

## 如何套用

当你发现一个 bug 时：

1. **追踪数据流** — 错误值从哪来？在哪被使用？
2. **列出所有检查点** — 数据经过的每一处
3. **在每一层加校验** — 入口、业务、环境、调试
4. **逐层测** — 试着绕过第 1 层，确认第 2 层能拦住

## 会话中的示例

Bug：空的 `projectDir` 导致在源码目录执行 `git init`

**数据流：**
1. 测试 setup → 空字符串
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` 在 `process.cwd()` 中运行

**增加的四层：**
- 第 1 层：`Project.create()` 校验非空/存在/可写
- 第 2 层：`WorkspaceManager` 校验 projectDir 非空
- 第 3 层：`WorktreeManager` 在测试中拒绝在 tmpdir 外 `git init`
- 第 4 层：`git init` 前记录堆栈

**结果：**全部 1847 个测试通过，bug 无法再现

## 要点

四层都有必要。测试过程中每层都拦住了其他层漏掉的问题：
- 不同代码路径绕过了入口校验
- Mock 绕过了业务逻辑检查
- 不同平台上的边界情况需要环境守卫
- 调试日志发现了结构性误用

**不要只停在一处校验。** 在每一层都加检查。
