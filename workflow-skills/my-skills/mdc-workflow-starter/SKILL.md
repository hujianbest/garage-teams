---
name: mdc-workflow-starter
description: 在执行任何其他动作之前，把软件工作路由到正确阶段。适用于需求、规格、设计、任务规划、实现、变更、缺陷修复等软件交付请求的起点，或用户说 continue/start/推进/继续开发 的场景。
---

# MDC 工作流入口

在进入任何阶段工作前，先使用这个 skill。

## 目的

你的职责不是直接实现，而是判断当前所处阶段、识别正确的下一步 skill，并阻止乱序推进。

这个 skill 用于把软件作业按这套 skills 体系路由到正确阶段。

它是作业流的入口门禁：

`mdc-specify -> mdc-spec-review -> mdc-design -> mdc-design-review -> mdc-tasks -> mdc-tasks-review -> mdc-implement -> mdc-bug-patterns -> mdc-test-review -> mdc-code-review -> mdc-traceability-review -> mdc-regression-gate -> mdc-completion-gate`

变更请求和热修复会被路由到专门的支线流程。

## 铁律

在把会话正确路由到合适阶段之前，不要开始澄清需求、深入读代码、做设计、做规划或直接实现。

如果有任何不确定，先解决“当前阶段是什么”这个问题。

## 优先读取内容

只读取完成路由所需的最少内容：

1. 项目的作业契约中映射出的工件位置（如果存在）
2. 当前需求、缺陷、变更或继续推进的用户请求
3. 现有已批准的规格、设计、任务工件，但只读取判断“是否存在、是否已批准”所需的最少内容
4. 当前进度记录、发布说明、评审记录、验证记录等可作为阶段证据的工件

路由阶段不要开始大范围探索代码库。

## 附加资源

当项目还没有稳定的作业契约，或交付件布局与阶段判断方式不清晰时，阅读以下参考文档：

- `references/routing-evidence-guide.md`
- `references/mdc-contract-template.md`

用它们来先标准化工件位置和阶段证据来源，避免后续工作流越来越混乱。

## 路由顺序

严格按以下顺序检查：

1. 若用户明确提出紧急缺陷修复，或现有工件清楚表明当前处于热修复场景，优先进入 `mdc-hotfix`
2. 否则若用户明确提出需求变更、范围调整、验收标准变化，进入 `mdc-increment`
3. 若没有已批准需求规格，进入 `mdc-specify`
4. 若没有已批准实现设计，进入 `mdc-design`
5. 若没有已批准任务计划，进入 `mdc-tasks`
6. 若仍有未完成计划任务，进入 `mdc-implement`
7. 若当前任务已实现，但缺少缺陷模式排查证据，进入 `mdc-bug-patterns`
8. 若当前任务缺少测试、代码或追溯性评审结论，依次进入 `mdc-test-review`、`mdc-code-review`、`mdc-traceability-review`
9. 若当前任务缺少回归或完成验证证据，进入 `mdc-regression-gate` 或 `mdc-completion-gate`
10. 否则进入 `mdc-finalize`

## 什么叫“已批准”

不要只根据聊天记录推断“已批准”。优先寻找工件中的显式证据：

- `Status: Approved` 或 `状态: 已批准`
- 审批章节或评审记录
- 进度记录、任务状态或验证记录中的阶段性标记

如果状态不清楚，就按“未批准”处理。

## 输出约定

完成路由后，报告以下内容：

1. 当前识别阶段
2. 作出判断所依据的证据
3. 唯一正确的下一步 skill
4. 缺失或阻塞的工件（如有）

请用简洁表达。示例：

```markdown
当前阶段：需求尚未批准。

证据：
- 未发现已批准的需求规格
- 当前请求也未提供足以进入变更或热修复支线的证据

下一步 skill：`mdc-specify`
```

## 风险信号

- 用户说“继续”，你却直接开始写代码
- 规格虽然存在，但仍是草稿，你却当成已批准
- 还没判断阶段，就先去读实现文件
- 因为图快，就直接把流程路由到实现阶段

## 交接

一旦路由完成，就立刻使用对应 skill，并严格遵循它。
