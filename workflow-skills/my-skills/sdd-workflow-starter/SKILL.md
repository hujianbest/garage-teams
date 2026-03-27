---
name: mdc-workflow-starter
description: 在执行任何其他动作之前，把 MDC 驱动的软件工作路由到正确阶段。适用于需求、规格、设计、任务规划、实现、变更、缺陷修复等软件交付请求的起点，或用户在 MDC 项目中说 continue/start/推进/继续开发 的场景。
---

# MDC 工作流入口

在进入任何 MDC 阶段工作前，先使用这个 skill。

## 目的

你的职责不是直接实现，而是判断当前所处阶段、识别正确的下一步 skill，并阻止乱序推进。

这个 skill 是 MDC 工作流的入口门禁：

`work-specify -> spec-review -> work-design -> design-review -> work-tasks -> work-implement -> test/code/regression/completion gates`

变更请求和热修复会被路由到专门的支线流程。

## 铁律

在把会话正确路由到合适阶段之前，不要开始澄清需求、深入读代码、做设计、做规划或直接实现。

如果有任何不确定，先解决“当前阶段是什么”这个问题。

## 优先读取内容

只读取完成路由所需的最少内容：

1. `workflow-state.json` if it exists
2. `change-request.json` if it exists
3. `hotfix-request.json` if it exists
4. 项目的 MDC 契约中映射出的工件位置（如果存在）
5. 现有已批准的规格、设计、任务工件，但只读取判断“是否存在、是否已批准”所需的最少内容

路由阶段不要开始大范围探索代码库。

## 附加资源

当项目还没有稳定的 MDC 契约，或信号文件/状态文件格式不清晰时，阅读以下参考文档：

- `references/sdd-entry-guide.md`
- `references/sdd-contract-template.md`
- `references/signal-file-templates.md`

用它们来先标准化工件位置和状态文件，避免后续工作流越来越混乱。

## 路由顺序

严格按以下顺序检查：

1. If `hotfix-request.json` exists -> route to `mdc-hotfix`
2. Else if `change-request.json` exists -> route to `mdc-increment`
3. Else if there is no approved requirement spec -> route to `mdc-specify`
4. Else if there is no approved implementation design -> route to `mdc-design`
5. Else if there is no approved task plan -> route to `mdc-tasks`
6. Else if there are unfinished planned tasks -> route to `mdc-implement`
7. Else if implementation exists but lacks fresh verification evidence -> route to `mdc-completion-gate`
8. Else route to `mdc-finalize`

## 什么叫“已批准”

不要只根据聊天记录推断“已批准”。优先寻找工件中的显式证据：

- `Status: Approved`
- 审批章节或评审记录
- `workflow-state.json` 中的状态标记

如果状态不清楚，就按“未批准”处理。

## 输出约定

完成路由后，报告以下内容：

1. Current detected phase
2. 作出判断所依据的证据
3. 唯一正确的下一步 skill
4. 缺失或阻塞的工件（如有）

请用简洁表达。示例：

```markdown
当前阶段：需求尚未批准。

证据：
- 未发现已批准的需求规格
- 未发现变更或热修复信号文件

下一步 skill：`mdc-specify`
```

## 风险信号

- 用户说“继续”，你却直接开始写代码
- 规格虽然存在，但仍是草稿，你却当成已批准
- 还没判断阶段，就先去读实现文件
- 因为图快，就直接把流程路由到实现阶段

## 交接

一旦路由完成，就立刻使用对应 skill，并严格遵循它。
