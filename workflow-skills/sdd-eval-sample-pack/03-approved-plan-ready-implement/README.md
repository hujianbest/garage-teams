# 场景 03：任务计划已批准，可进入实现

## 目的

验证在 spec、design、task plan 都已批准，且 `workflow-state.json` 指向实现阶段时，是否路由到 `sdd-work-implement`。

## 用户 Prompt

```text
继续这个项目。按照已经确认好的任务计划，先做当前该做的那一项，不要自己扩 scope。
```

## 期望

- 先命中 `sdd-workflow-starter`
- 读取 `workflow-state.json`
- 路由到 `sdd-work-implement`
- 后续应明确 review/gate 顺序
