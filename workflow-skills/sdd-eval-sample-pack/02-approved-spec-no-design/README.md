# 场景 02：规格已批准，但尚无设计

## 目的

验证在存在 approved requirement spec，但不存在 approved design 时，是否会路由到 `sdd-work-design`。

## 用户 Prompt

```text
继续这个发布审批系统。需求规格已经确认过了，下一步该怎么走就怎么走。
```

## 期望

- 先命中 `sdd-workflow-starter`
- 识别 `docs/specs/2026-03-26-release-approval-srs.md` 已批准
- 因为没有 design doc，路由到 `sdd-work-design`
