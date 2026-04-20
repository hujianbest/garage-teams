# `packs/garage/` — Garage 占位 Pack

本 pack 是 Garage 自带的最小可分发能力集合，用于：

1. **验证 packs/ 目录契约**：让 `pack_discovery` 模块有可消费的真实 fixture。
2. **验证 host installer 端到端管道**：让 `garage init --hosts ...` 有可物化的源。
3. **作为下游用户的 'getting started' 入口**：用户首次跑 `garage init` 后能立刻在自己的 AI 工具里看到一个 "hello" skill，确认安装成功。

## 内容

| 类型 | id | 文件 | 说明 |
|---|---|---|---|
| skill | `garage-hello` | [`skills/garage-hello/SKILL.md`](skills/garage-hello/SKILL.md) | 最小欢迎 skill，演示 SKILL.md 形态 |
| agent | `garage-sample-agent` | [`agents/garage-sample-agent.md`](agents/garage-sample-agent.md) | 最小 sample agent，演示 agent.md 形态（无 front matter，覆盖 marker.inject 容错路径） |

## Pack 元数据

详见 [`pack.json`](pack.json)。

```json
{
  "schema_version": 1,
  "pack_id": "garage",
  "version": "0.1.0",
  ...
}
```

## 后续

未来 F008 cycle 会引入 `packs/coding/` 与 `packs/product-insights/`，把现有 `.agents/skills/` 下 30 个 HF workflow skills 搬过去。本 `packs/garage/` 仍将保留为最小入口示例。
