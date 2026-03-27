# Implementer 子代理提示

你正在为 {{PROJECT_NAME}} 项目实现一项任务。

## 项目上下文
- 技术栈：{{TECH_STACK}}
- 测试框架：{{TEST_FRAMEWORK}}
- 关键模式：{{KEY_PATTERNS}}
- 工作目录：{{WORKING_DIR}}

## 任务
{{FULL_TASK_TEXT}}

## 退出条件

1. 运行 `{{TEST_COMMAND}}` —— 全部测试通过
2. 运行 `{{COVERAGE_COMMAND}}` —— 行覆盖 ≥ {{LINE_COV_MIN}}%，分支 ≥ {{BRANCH_COV_MIN}}%
3. 运行 `{{MUTATION_COMMAND}}` —— 变异分数 ≥ {{MUTATION_MIN}}%（增量，仅变更文件）
4. 创建/修改的文件：{{FILE_LIST}}
5. 无回归：运行 `{{FULL_TEST_COMMAND}}` —— 全部通过

## 规则
- 遵循 TDD：先写失败测试，再写最少实现使其通过
- 测试通过后跑覆盖率；重构后跑变异 —— 始终先覆盖率门禁再变异门禁
- 不要修改本任务范围外的文件
- 遇到问题应记录并停止 —— 不要猜谜式修复
- 使用带特性 ID 的描述性信息提交变更
