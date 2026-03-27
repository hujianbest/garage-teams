# 子代理驱动开发

## 目的

为每个实现任务派发全新子代理。避免上下文污染（一项细节干扰下一项），并支持每项独立验证。

## 何时使用

- 含多项任务的复杂特性
- 担心上下文污染的特性
- 已完成特性详细设计（通过 `long-task:long-task-feature-design` 技能）

简单特性（1–2 项任务）自行执行更快且足够。

## 架构

```
Controller (main agent)
  │
  ├─ Dispatch Subagent: Task 1 (implementer)
  │   └─ Returns: code changes + test results
  │
  └─ Repeat for Task 2, Task 3, ...
```

## 控制者职责

主代理作为控制者：

1. **从 `docs/plans/` 加载实现计划**
2. **每项任务派发一个子代理**，附带完整任务正文
3. **每项之后评审结果**
4. **跟踪进度**——标记任务完成、更新特性状态
5. **处理失败**——若任务失败，为重试提供上下文

## 派发 Implementer 子代理

### 关键规则

1. **提供完整任务正文**——将整个任务描述复制进提示。不要说「读文件 X」——子代理可能没有上下文。

2. **包含项目上下文**——告知子代理：
   - 项目是什么
   - 使用什么技术栈
   - 关键文件在哪
   - 遵循何种模式

3. **定义明确退出条件**——明确「完成」含义：
   - 哪些测试必须通过
   - 应创建/修改哪些文件
   - 运行什么验证命令

### 提示模板

```markdown
You are implementing a task for the [project-name] project.

## Project Context
- Tech stack: [stack]
- Key patterns: [patterns]
- Test framework: [framework]

## Task
[Full task text from the plan, including exact file paths, code, and verification steps]

## Exit Criteria
1. Run [test command] — all tests pass
2. Files created/modified: [list]
3. No regressions: run [full test command] — all pass

## Rules
- Follow TDD: write failing tests first, then implement
- Do not modify files outside the scope of this task
- Commit your changes with a descriptive message
```

## 并行派发（高级）

多项任务相互独立（无共享文件、无依赖）时：

1. 在计划中识别独立任务
2. 使用 Task 工具并行派发 implementer 子代理
3. 等待全部完成
4. 运行完整测试套件检查冲突
5. 评审每项变更
6. 解决冲突（若有）

**约束**：
- 仅对真正独立的任务并行
- 并行完成后始终运行完整测试套件
- 若发现冲突，改为顺序解决

## 反模式

| 反模式 | 为何失败 | 正确做法 |
|---|---|---|
| 用文件引用代替完整正文 | 子代理可能无权限或上下文 | 将完整任务正文复制进提示 |
| 无清晰退出条件就派发 | 子代理不知何时算完成 | 明确验证命令 |
| 对依赖任务并行 | 竞态、冲突变更 | 仅对真正独立任务并行 |
| 忽略评审意见 | 质量问题累积 | 继续前先处理 Critical/Important |
