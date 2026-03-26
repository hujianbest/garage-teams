# 场景 05：紧急热修复

## 目的

验证在主链工件已存在且根目录存在 `hotfix-request.json` 时，是否优先路由到 `sdd-work-hotfix`。

## 用户 Prompt

```text
线上有个紧急问题：审批通过以后没发通知，这个今天必须修。你按热修复流程来，但不要省略验证。
```

## 期望

- 先命中 `sdd-workflow-starter`
- 优先识别 `hotfix-request.json`
- 路由到 `sdd-work-hotfix`
- 保留复现、回归和 completion gate
