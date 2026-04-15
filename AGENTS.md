# AGENTS

## AHE 文档约定

- 在本仓库的 AHE workflow 中，`docs/features/` 下的 `Fxxx` 文档就是 `specs`。
- 当提到 `spec`、`specs` 或"规格"时，默认指 `docs/features/` 的 feature specs，而不是 `docs/tasks/`。

## Skill 写作原则

`docs/principles/skill-anatomy.md` 定义所有 Garage skill 的目标态写法，包括：

- 核心 7 原则（description 是分类器、主文件要短、边界必须显式等）
- 目录 anatomy（SKILL.md、references/、evals/、scripts/、assets/）
- 章节骨架（When to Use、Workflow、Output Contract、Red Flags、Verification 等）
- 演化与版本管理机制

新增或重写任何 skill 时，必须遵循此文档。

## 项目灵魂

`docs/soul/` 下存放 Garage 的核心信念和承诺，是所有设计决策的价值锚点：

- `manifesto.md` — 愿景宣言：Garage 为什么存在
- `user-pact.md` — 用户契约：Garage 对用户的承诺
- `design-principles.md` — 设计原则：架构决策的判断标准
- `growth-strategy.md` — 成长策略：系统怎么从简单变复杂

当设计决策出现价值冲突时，回溯到这里做判断。

## Garage OS

- 运行时数据存储: .garage/
- 平台配置: .garage/config/platform.json
- 宿主适配器配置: .garage/config/host-adapter.json
- 平台契约: .garage/contracts/
- 技术栈: Python 3.11+ (Poetry)
