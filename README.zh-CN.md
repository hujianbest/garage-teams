# garage-agent

[English](README.md) | **中文**

`garage-agent` 是一个本地优先的 Agent 能力之家，用来存放并积累你的技能、知识和经验。

它面向独立创作者，希望让 Agent 能力从一次次聪明对话，成长为真正跟着自己、服务自己、可以迁移的长期能力系统，而不是被锁在某个工具、某个 session、某台机器里。

- 把 Agent 能力留在仓库里，而不是锁进封闭云端
- 换宿主时不必推倒重来，已经积累的能力可以继续带着走
- 从结构化 workflow 起步，逐步长成运行时、记忆与复用能力
- 架构、范围、发布、部署和破坏性操作，始终由人拍板

## 为什么叫 garage-agent

车库是很多创业故事和作品起步的地方：离问题最近，资源不必豪华，但可以靠持续迭代把东西真正做出来。`garage-agent` 这个名字表达的就是这个意象。Agent 的能力应该从你的工作现场长出来，在仓库里不断积累，最后走出车库，但不会因为换工具或换环境而丢掉自己。

## 它是什么

`garage-agent` 当前由三层组成：

- 面向产品洞察和编码的 AHE workflow packs
- 面向 session、knowledge、experience 与 tool execution 的文件优先 runtime foundation
- Agent 和人都能阅读、检查、演化的仓库约定

它追求的不是把过程藏进黑箱，而是给 Agent 一个稳定的能力基座，让上下文、产物和习惯都能随着工作一起沉淀下来。

## 它不是什么

- 不是 SaaS 产品
- 不是绑定单一宿主的外壳
- 不是大而全的通用 AI 框架
- 不是把关键判断彻底交给自动化的全自动驾驶系统

## 核心原则

- 数据归你：数据留在仓库里，即使项目停止维护也依然可读
- 宿主可换：今天可以优先支持某个宿主，但不能永远绑定某个宿主
- 渐进增强：第一天就应该能用，而不是先经历一套复杂配置
- 透明可审计：系统知道什么、为什么这么做，都应该能在文件和产物里看见
- 人始终掌舵：系统可以辅助和自动化，但方向盘始终在人手里

## 当前已有内容

`garage-agent` 还处在早期阶段，但仓库里已经有：

- 位于 [packs/product-insights/skills/](packs/product-insights/skills/) 和 [packs/coding/skills/](packs/coding/skills/) 的 AHE workflow skills
- 位于 [src/garage_os/](src/garage_os/) 的早期 Python runtime package，目前包名仍是 `garage-os`
- 一个 `garage` CLI，已提供 `init`、`status`、`run`、`knowledge search`、`knowledge list`、`knowledge add`、`knowledge edit`、`knowledge show`、`knowledge delete`、`experience add`、`experience show`、`experience delete` 与 `memory review`
- 位于 [.garage/](.garage/) 的文件优先 runtime 数据结构
- [docs/features/F001-garage-agent-operating-system.md](docs/features/F001-garage-agent-operating-system.md) 中已批准的 Phase 1 方向，以及 [docs/guides/garage-os-user-guide.md](docs/guides/garage-os-user-guide.md) 和 [docs/guides/garage-os-developer-guide.md](docs/guides/garage-os-developer-guide.md) 两份运行时指南

## 三条开始路径

### 1. 先看 workflow packs

- 如果你从一个模糊想法出发，先看 [packs/product-insights/skills/using-ahe-product-workflow/SKILL.md](packs/product-insights/skills/using-ahe-product-workflow/SKILL.md)
- 如果你已经知道要做什么，先看 [packs/coding/skills/using-ahe-workflow/SKILL.md](packs/coding/skills/using-ahe-workflow/SKILL.md)
- 如果你想先看两个 pack 的全貌，读 [packs/product-insights/skills/README.md](packs/product-insights/skills/README.md) 和 [packs/coding/skills/README.md](packs/coding/skills/README.md)

### 2. 试用 runtime CLI

在仓库根目录执行：

```bash
uv pip install -e .
garage init
garage status
```

如果你的环境里已经安装并登录 Claude Code CLI，也可以继续探索当前的执行入口 `garage run <skill-name>`。不过 runtime 仍在早期，宿主驱动的 skill 执行更适合作为演进中的能力路径来看，而不是成熟的平台体验。

### 3. 阅读世界观与系统文档

- 灵魂文档：[docs/soul/manifesto.md](docs/soul/manifesto.md)、[docs/soul/user-pact.md](docs/soul/user-pact.md)、[docs/soul/design-principles.md](docs/soul/design-principles.md)、[docs/soul/growth-strategy.md](docs/soul/growth-strategy.md)
- 系统规格：[docs/features/F001-garage-agent-operating-system.md](docs/features/F001-garage-agent-operating-system.md)
- 用户指南：[docs/guides/garage-os-user-guide.md](docs/guides/garage-os-user-guide.md)
- 开发者指南：[docs/guides/garage-os-developer-guide.md](docs/guides/garage-os-developer-guide.md)

## 仓库地图

| 路径 | 用途 |
| --- | --- |
| [packs/](packs/) | 参考 workflow packs、pack-local 文档和相关 agent 资产 |
| [src/garage_os/](src/garage_os/) | runtime package 和 CLI 实现 |
| [.garage/](.garage/) | sessions、knowledge、experience、contracts 和 config 等运行时状态 |
| [docs/](docs/) | soul 文档、spec、guide、review 和设计制品 |
| [tests/](tests/) | 模块、集成、兼容性和安全测试 |
| [AGENTS.md](AGENTS.md) | 面向 Agent 的项目约定和 Garage OS 开发参考 |

## 开源化进展

`garage-agent` 正在为公开开源发布做整理。

- 对外项目名已经采用 `garage-agent`
- 仓库里的 Python package 和 CLI 当前仍叫 `garage-os` 与 `garage`
- 正式的 `LICENSE` 文件尚未加入，因此复用条款还没有最终确定
- `CONTRIBUTING.md`、`CODE_OF_CONDUCT.md` 和 `SECURITY.md` 也还在补齐中
- 当前最有价值的外部贡献方向，是 workflow 质量、可迁移性、文档清晰度、runtime 稳定性和示例完善
