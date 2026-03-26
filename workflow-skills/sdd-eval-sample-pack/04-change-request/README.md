# 场景 04：需求变更

## 目的

验证在主链工件已存在且根目录存在 `change-request.json` 时，是否优先路由到 `sdd-work-increment`。

## 用户 Prompt

```text
需求有变化。审批通过以后，除了通知申请人，还要自动抄送项目经理。你按正确流程处理，不要直接偷偷改代码。
```

## 期望

- 先命中 `sdd-workflow-starter`
- 优先识别 `change-request.json`
- 路由到 `sdd-work-increment`
- 做 impact analysis，而不是直接进入实现
