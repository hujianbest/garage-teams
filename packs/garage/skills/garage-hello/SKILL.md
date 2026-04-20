---
name: garage-hello
description: Use when verifying that Garage packs are correctly installed in the host. Not for actual workflow tasks; this is a sanity-check skill.
---

# Garage Hello

最小欢迎 skill。本文件唯一的目的是：当用户在自己项目运行 `garage init --hosts <host>` 后，能在对应宿主里看到这条 skill 出现，从而确认 Garage host installer 工作正常。

## When to Use

适用：

- 用户首次安装 Garage packs 后，想验证宿主集成是否就绪
- 排查 Garage host installer 的 dry-run / smoke-test 场景

不适用：

- 真实工作流任务 → 使用 `hf-*` 系列或其他 pack 内的 skill
- 自定义 skill 模板 → 见 `docs/principles/skill-anatomy.md`

## Workflow

1. 用户在宿主里调用 / 引用 `garage-hello`。
2. 输出一行欢迎文本：`Hello from Garage. Your packs are installed correctly.`
3. 结束。

## Verification

- 文件来自 `packs/garage/skills/garage-hello/SKILL.md`，由 `garage init` 物化到对应宿主目录。
- 安装清单 `.garage/config/host-installer.json` `files[]` 中应有指向本 SKILL.md 的 entry。
