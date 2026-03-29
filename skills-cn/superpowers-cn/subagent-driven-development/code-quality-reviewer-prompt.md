# 代码质量评审者提示模板

派发代码质量评审子代理时使用本模板。

**目的：** 核实实现是否构建得当（清晰、有测试、可维护）

**仅在规格符合性评审通过后再派发。**

```
Task 工具（superpowers:code-reviewer）：
  使用模板：requesting-code-review/code-reviewer.md

  WHAT_WAS_IMPLEMENTED: [来自实现者报告]
  PLAN_OR_REQUIREMENTS: 任务 N，来源 [plan-file]
  BASE_SHA: [任务开始前提交]
  HEAD_SHA: [当前提交]
  DESCRIPTION: [任务摘要]
```

**除常规代码质量关注点外，评审者还应检查：**
- 每个文件是否职责单一且接口明确？
- 单元是否拆解到可独立理解与测试？
- 实现是否遵循计划中的文件结构？
- 本次实现是否新增已偏大的文件，或显著撑大现有文件？（不要纠结变更前已存在的体积——聚焦本次变更带来的部分。）

**代码评审回报：** 优点、问题（Critical/Important/Minor）、评估
