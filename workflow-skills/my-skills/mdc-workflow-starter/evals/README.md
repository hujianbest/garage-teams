# 工作流入口评测

这个目录包含 `mdc-workflow-starter` 的评测 prompts。

## 目的

这些评测用于验证路由质量，而不是实现质量。

它们主要检查入口 skill 是否：

- 被优先触发
- 读取了正确的路由证据
- 选择了正确的下游 skill
- 没有发生阶段跳步

## 重要说明

有些 eval 依赖项目状态，而不只是 prompt 文本本身。

运行前，请先准备好以下文档中描述的工件状态：

- `workflow-skills/mdc-skills-eval-prompts.md`

例如：

- 已有 approved spec，但没有 approved design
- prompt 明确表达需求变更
- prompt 明确表达紧急热修复

如果前置条件缺失，路由结果不同也可能是合理的。

## Eval 结构

- `id`：稳定标识
- `prompt`：贴近真实场景的用户请求
- `expected_output`：便于人工核对的期望路由结果
- `files`：当前为空，因为这些 eval 依赖项目工件状态，而不是打包文件
- `expectations`：评分时使用的检查清单

## 建议评分关注点

评分时重点看：

1. 是否先使用了 `mdc-workflow-starter`
2. 回答是否引用了路由证据
3. 下游 skill 是否正确
4. 是否避免了过早进入设计、任务或代码实现
