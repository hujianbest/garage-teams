# 场景 01：全新需求

## 目的

验证在没有任何已批准工件时，是否会先路由到 `sdd-work-specify`。

## 这个场景为什么几乎是空的

这是故意设计的。这个目录不提供：

- `workflow-state.json`
- 已批准 spec
- 已批准 design
- 已批准 task plan
- `change-request.json`
- `hotfix-request.json`

因为它要模拟一个真正的“从 0 开始”的项目起点。

## 用户 Prompt

```text
我们准备做一个内部发布审批系统。第一期只支持员工提交发布申请、直属主管审批、审批通过后通知申请人。先帮我开始推进这件事，后面会按你说的流程走。
```

## 期望

- 先命中 `sdd-workflow-starter`
- 然后路由到 `sdd-work-specify`
- 不直接进入 design、tasks 或 implementation
