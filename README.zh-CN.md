# garage-agent

[English](README.md) | **中文**

[![Tests](https://github.com/hujianbest/garage-agent/actions/workflows/test.yml/badge.svg)](https://github.com/hujianbest/garage-agent/actions/workflows/test.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-Contributor%20Covenant-ff69b4.svg)](CODE_OF_CONDUCT.md)

`garage-agent` 是一个本地优先的 Agent 能力之家，用来存放并积累你的技能、知识和经验。

它面向独立创作者，希望让 Agent 能力从一次次聪明对话，成长为真正跟着自己、服务自己、可以迁移的长期能力系统，而不是被锁在某个工具、某个 session、某台机器里。

- 把 Agent 能力留在仓库里，而不是锁进封闭云端
- 换宿主时不必推倒重来，已经积累的能力可以继续带着走
- 从结构化 workflow 起步，逐步长成运行时、记忆与复用能力
- 架构、范围、发布、部署和破坏性操作，始终由人拍板

## 为什么叫 garage-agent

车库是很多创业故事和作品起步的地方：离问题最近，资源不必豪华，但可以靠持续迭代把东西真正做出来。`garage-agent` 这个名字表达的就是这个意象。Agent 的能力应该从你的工作现场长出来，在仓库里不断积累，最后走出车库，但不会因为换工具或换环境而丢掉自己。

## 它是什么

`garage-agent` 当前由四层组成：

- 可分发的 **packs**（[`packs/`](packs/) 下的 Garage Coding、Garage Writing、Garage 核心三个 pack，加上一个 `search` 实验 pack）
- 面向 session、knowledge、experience、candidate review 与 tool execution 的**文件优先 runtime**（[`src/garage_os/`](src/garage_os/)）
- 一套**宿主 installer + sync 层**：把 packs 物化到 Claude Code、Cursor、OpenCode（支持项目级 / 用户级），把 top-N memory 推到每个宿主的 context surface，并把宿主对话历史回流为 Garage session
- 完整的 **pack lifecycle**（`install` / `ls` / `uninstall` / `update` / `publish`）以及匿名化 knowledge 导出，让能力能离开一个仓库，落地到另一个仓库

它追求的不是把过程藏进黑箱，而是给 Agent 一个稳定的能力基座，让上下文、产物和习惯都能随着工作一起沉淀下来，再把值得分享的部分分享出去。

## 它不是什么

- 不是 SaaS 产品
- 不是绑定单一宿主的外壳
- 不是大而全的通用 AI 框架
- 不是把关键判断彻底交给自动化的全自动驾驶系统

## 核心原则

- **数据归你**：数据留在仓库里，即使项目停止维护也依然可读
- **宿主可换**：今天可以优先支持某个宿主，但不能永远绑定某个宿主——目前 3 个 first-class adapter（Claude Code、Cursor、OpenCode）
- **渐进增强**：第一天就应该能用，而不是先经历一套复杂配置
- **透明可审计**：系统知道什么、为什么这么做，都应该能在文件和产物里看见
- **人始终掌舵**：系统可以辅助和自动化，但方向盘始终在人手里——破坏性 / 共享性操作必须 opt-in（`--yes` / `--anonymize` / `--force` 显式声明）

## 当前已有内容（F001 - F014 共 14 个 cycle）

经过 14 个已关闭的交付 cycle，仓库现在提供：

| Cycle | 能力 |
|---|---|
| F001 | Garage Agent 操作系统底座（`garage init` / `status` / `run` / contracts / VersionManager） |
| F002 | SessionManager + StateMachine + ErrorHandler |
| F003 | Memory 自动提取（signals → candidates → review queue） |
| F004 | Memory v1.1（KnowledgeStore + ExperienceIndex 整合） |
| F005 | Knowledge 写作 CLI（`knowledge add` / `edit` / `show` / `delete`） |
| F006 | 召回 + knowledge graph（`knowledge search` / `link` / `graph`） |
| F007 | Garage Packs + Host Installer（`garage init --hosts claude,cursor,opencode`） |
| F008 | Coding Pack + Writing Pack + dogfood layout |
| F009 | 多 scope 安装（`--scope project|user` + per-host override；manifest schema 2 自动迁移） |
| F010 | Memory Sync（`garage sync`） + 宿主 session 回流（`garage session import --from <host>`） |
| F011 | `KnowledgeType.STYLE` + 生产 agents（`code-review-agent` / `blog-writing-agent`） + `garage pack install <git-url>` + `pack ls` |
| F012 | Pack lifecycle 完整化（`pack uninstall` / `pack update` / `pack publish`） + `knowledge export --anonymize` + F009 carry-forward（VersionManager 注册） |
| F013-A | Skill Mining Push（`garage skill suggest` / `garage skill promote`，从重复模式建议生成 skill 草稿） |
| F014 | Workflow Recall（`garage recall workflow` + `hf-workflow-router` step 3.5 历史路径 advisory） |

具体交付物：

- **AHE / HF workflow skills** 在 [`packs/coding/skills/`](packs/coding/skills/)（24 个 `hf-*` skill + `using-hf-workflow`）和 [`packs/writing/skills/`](packs/writing/skills/)（5 个写作 skill）
- **生产 agents** 在 [`packs/garage/agents/`](packs/garage/agents/)：`code-review-agent`、`blog-writing-agent`、`garage-sample-agent`
- 一个 **Python runtime** package `garage-os`（[`src/garage_os/`](src/garage_os/)；兼容名保留），约 1045 个测试通过
- 一个 **`garage` CLI**，覆盖：`init`、`status`、`run`、`recommend`、`recall workflow`、`sync`、`session import`、`memory review`、`skill suggest`、`skill promote`；knowledge 子命令 `knowledge search`、`knowledge list`、`knowledge add`、`knowledge edit`、`knowledge show`、`knowledge delete`、`knowledge link`、`knowledge graph`、`knowledge export`；experience 子命令 `experience add`、`experience show`、`experience delete`；pack lifecycle `pack install`、`pack ls`、`pack uninstall`、`pack update`、`pack publish`
- 文件优先的 runtime 数据结构在 [`.garage/`](.garage/)（sessions、含 YAML front matter 的 knowledge 条目、experience records、sync manifest、host installer manifest）
- 每一个 cycle 的 spec / 评审 / 验收 在 [`docs/features/`](docs/features/)、[`docs/designs/`](docs/designs/)、[`docs/reviews/`](docs/reviews/)、[`docs/approvals/`](docs/approvals/)

## 三条开始路径

### 1. 先看 workflow packs

- 如果你从一个模糊想法出发，先跑 [`packs/coding/skills/hf-product-discovery/SKILL.md`](packs/coding/skills/hf-product-discovery/SKILL.md)
- 如果你已经知道要做什么，从 [`packs/coding/skills/using-hf-workflow/SKILL.md`](packs/coding/skills/using-hf-workflow/SKILL.md) 入口走，让 `hf-workflow-router` 路由到正确节点
- 如果你想先看 pack 全貌，读 [`packs/README.md`](packs/README.md)、[`packs/coding/README.md`](packs/coding/README.md)、[`packs/writing/README.md`](packs/writing/README.md)、[`packs/garage/README.md`](packs/garage/README.md)

### 2. 试用 runtime CLI

在仓库根目录执行：

```bash
uv pip install -e .

# 在当前项目初始化 Garage + 把 Garage Coding / Writing / Garage 三个 pack 物化到宿主目录
# --hosts 接受 claude,cursor,opencode 任意组合
garage init --hosts claude,cursor --yes

# 查看状态
garage status

# 把 top-N knowledge + recent experience 推送到每个宿主的 context surface
# (CLAUDE.md / .cursor/rules/garage-context.mdc / .opencode/AGENTS.md)
garage sync --hosts claude,cursor

# 把宿主对话历史回流为 Garage sessions, 触发 memory 提取
garage session import --from claude --all

# 查看系统从历史经验中建议的 workflow path
garage recall workflow --problem-domain cli-design

# 查看或提升系统挖出的 pattern → skill 建议
garage skill suggest --rescan
```

第一次贡献到本仓库的开发者，如果需要 cloud-agent 的 skill 挂载点，还要执行：

```bash
bash scripts/setup-agent-skills.sh    # 重生成 .agents/skills/ 软链 → packs/
```

如果你的环境里已经安装并登录 Claude Code CLI，也可以继续用 `garage run <skill-name>` 跑单个 skill。runtime 仍在早期，宿主驱动的 skill 执行更适合作为演进中的能力路径来看，而不是成熟的平台体验。

### 3. 分享或拉取 packs

```bash
# 从 git URL 安装别人的 pack
garage pack install https://github.com/<user>/<their-pack>.git

# 列出已安装 packs (从 URL 安装的会显示 source_url, 本地的显示 "local")
garage pack ls

# 从 source_url 重新拉取并更新已安装 pack
garage pack update <pack-id> --yes

# 把你的 pack 发到全新或已有的 git remote (会做 sensitive scan + force-push 提示)
garage pack publish <pack-id> --to https://github.com/<you>/<pack-name>.git --yes

# 从 packs/ 和所有宿主目录干净地移除一个 pack
garage pack uninstall <pack-id> --yes

# 把 knowledge 脱敏导出为 tarball (front matter 保留, body 脱敏)
garage knowledge export --anonymize
```

### 4. 阅读世界观与系统文档

- 灵魂文档：[`docs/soul/manifesto.md`](docs/soul/manifesto.md)、[`docs/soul/user-pact.md`](docs/soul/user-pact.md)、[`docs/soul/design-principles.md`](docs/soul/design-principles.md)、[`docs/soul/growth-strategy.md`](docs/soul/growth-strategy.md)
- 系统规格：[`docs/features/F001-garage-agent-operating-system.md`](docs/features/F001-garage-agent-operating-system.md)
- 用户指南：[`docs/guides/garage-agent-user-guide.md`](docs/guides/garage-agent-user-guide.md)
- Skill 写作原则（新增 / 重写 skill 必读）：[`docs/principles/skill-anatomy.md`](docs/principles/skill-anatomy.md)

## 仓库地图

| 路径 | 用途 |
| --- | --- |
| [`packs/`](packs/) | 可分发的 packs（single source of truth：`coding`、`writing`、`garage`、`search`） |
| [`src/garage_os/`](src/garage_os/) | runtime: types、storage、runtime（session manager + state machine + skill executor）、knowledge、adapter（host installer + sync）、tools、platform（VersionManager） |
| [`.agents/skills/`](#agents-skills-挂载点) | Cloud-agent skill 挂载点（指向 `packs/` 的相对软链；不入 git，本地 `scripts/setup-agent-skills.sh` 重生成） |
| [`.garage/`](.garage/) | 工作区运行时状态：sessions、knowledge、experience、sync manifest、host installer manifest、contracts、config |
| [`docs/`](docs/) | 灵魂文档、feature spec（`features/`）、design（`designs/`）、review（`reviews/`）、approval（`approvals/`）、planning（`planning/`）、guide、principle、manual smoke walkthrough |
| [`tests/`](tests/) | 约 1045 个 unit + integration + compatibility + security + sentinel 测试，目录结构与 `src/garage_os/` 模块一一对应 |
| [`AGENTS.md`](AGENTS.md) | 面向 Agent 的项目约定 + garage-agent 开发参考 + F009-F014 功能用法 |
| [`RELEASE_NOTES.md`](RELEASE_NOTES.md) | 每个 cycle 的用户可见变化（F001 → F014） |

### `.agents/skills/` 挂载点

某些 cloud-agent runtime 按 `.agents/skills/<name>/SKILL.md` 路径加载 skill。为了让 `packs/` 保持 single source of truth 又不重复文件，`.agents/skills/` 是一棵指向 `packs/<pack-id>/skills/` 的相对软链树。它在 `.gitignore` 里，本地用以下命令重生成：

```bash
bash scripts/setup-agent-skills.sh
```

详见 [`.agents/README.md`](.agents/README.md)。

## 开发计划

下面是「当前已实现内容」对照 [`docs/soul/manifesto.md`](docs/soul/manifesto.md) 愿景的差距盘点，作为后续 cycle 立项的依据。F012 完成后（2026-04-25）更新。

### 现状速览

```
              vision 完成度
              ┌─────────────────────────────────┐
信念 1 数据归你 │█████████████████████████████████│ 5/5  ✅
信念 2 宿主可换 │█████████████████████████        │ 4/5  ⚠️ 3 个 first-class 宿主, 第 4 个仍要改源码
信念 3 渐进增强 │█████████████████████████████████│ 5/5  ✅
信念 4 人机共生 │█████████████████████████████████│ 5/5  ✅ 飞轮闭环 (sync ↔ ingest ↔ memory)
信念 5 可传承   │█████████████████████████████████│ 5/5  ✅ install / update / publish / 匿名导出
              └─────────────────────────────────┘

承诺 ① 几秒变成你的 Agent  ✅ 5/5
承诺 ② 知道你的编码风格    ✅ 5/5  ← KnowledgeType.STYLE + 生产 agents
承诺 ③ 记得上月架构决策    ✅ 5/5  ← garage sync 推 + garage session import 拉
承诺 ④ 调用 50 个 skills   ✅ 5/5
承诺 ⑤ 帮你写博客          ✅ 5/5

Stage 1 工具箱  ████████████████████ 100%
Stage 2 记忆体  ████████████████████ 100%   ← F010 闭环
Stage 3 工匠    █████████████         65%   ← F011 生产 agents 上线; skill 自动提炼仍手动
Stage 4 生态    ████████              40%   ← F012 lifecycle 完整; 社区发现 / 签名仍 F013+
```

### 缺口与优先级（F013+ 候选）

#### P1 — 飞轮抛光

1. **`pack update --preserve-local-edits` 真 3-way merge**（D-1211）：当前 flag 仅 warn 后 overwrite，未来要解决 local edits 与 upstream changes 的合并
2. **Skill mining push 信号**：系统已能提取 knowledge 候选，但还不能主动指出"这个 pattern 可以变成 skill"；需要把 `.garage/memory/` 候选推到 `packs/<pack>/skills/` 的路径
3. **跨设备同步**：`garage sync` 写入宿主，但跨机器的 git-aware 合并（D-707 carry-forward）还要靠手动 `git push`

#### P2 — 社区 / 供应链

4. **宿主 registry 可插拔**（F007 D-705 carry-forward）：第 4 个宿主仍需改 `HOST_REGISTRY` 字面表
5. **Pack 签名 / GPG**（D-1212）：publish + install 还不验证 pack 来源
6. **Monorepo packs**（D-1213）：`pack install` 假设仓库根只有一个 `pack.json`
7. **Pack 发现**（D-1214）：还没有 `garage pack search` 或 pack 中央 registry
8. **反向 import + experience export**（D-1215）：`knowledge export --anonymize` 的镜像版本（experience records + 反向 import-from-tarball）
9. **Publish 自动跑 `hf-doc-freshness-gate`**（D-1216）：把本地 docs/spec 时效性和对外可分享性闭环

### 推荐下一 cycle

F012 后信念 1-5 + 承诺 ①-⑤ 都达 5/5，下一阶段杠杆最大的是 **Stage 3 skill mining**——把现有提取管道升级成"系统从你的模式里建议新 skill"信号；之后是 **Stage 4 社区 / 供应链**（D-1214 pack search + D-1212 签名），打开公共 pack 生态的门。

详细评分依据见 [`docs/soul/manifesto.md`](docs/soul/manifesto.md)、[`docs/soul/growth-strategy.md`](docs/soul/growth-strategy.md)、[`RELEASE_NOTES.md`](RELEASE_NOTES.md)（F001-F012）和 [`docs/planning/`](docs/planning/)。

## 开源

`garage-agent` 已采用 [Apache 2.0 License](LICENSE) 公开开源。

- **对外项目名**: `garage-agent`
- **Python package + import 路径**: `garage-os`（保持稳定，避免破坏既有 import）
- **CLI 命令**: `garage`
- **License**: [Apache-2.0](LICENSE)，明确含专利授权，对下游友好
- **贡献指南**: 提非琐碎 PR 前请先读 [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **行为准则**: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)（Contributor Covenant 2.1）
- **安全报告**: 漏洞请走 [`SECURITY.md`](SECURITY.md) 的私有渠道，不要在公共 issue 里披露
- **CI**: GitHub Actions 在每个 push 与 PR 上对 Python 3.11 + 3.12 跑完整 1044 个 `pytest` 用例

当前最有价值的外部贡献方向：workflow 质量、宿主可迁移性、文档清晰度、runtime 稳定性和真实使用示例。
