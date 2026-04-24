# Vision Gap Analysis & Next Cycle Plan (F010+)

- **日期**: 2026-04-24
- **作者**: Cursor Agent (auto, in `cursor/vision-gap-analysis-bf33`)
- **基线**: main @ `fa3cab2` (F009 closed + PR#25 coding pack reverse-sync + PR#26 README roadmap snapshot + search hotfix)
- **状态**: 715 passed (0 regressions)

## 0. 这份文档是什么

这是一份 **planning artifact**, 不是 spec / design / tasks. 目的:
- 重读 `docs/soul/{manifesto, user-pact, growth-strategy, design-principles}.md` 4 个灵魂文档, 把"愿景说什么"翻译成可量化的当前完成度
- 把 README.md "Roadmap" 段 (PR#26 落地) 的 P0/P1/P2 在更细粒度上展开
- 给出**下一 cycle 的具体推荐**: F010 是什么, 候选 candidate 排序, 第一步该启什么 skill

下一 cycle 的真正 spec/design/tasks 仍走 `hf-specify` → `hf-design` → `hf-tasks` 链路, 本文档只是上游输入.

## 1. 重读愿景 — 5 信念 / 5 promise / 4 stage 三轴

### 1.1 5 核心信念 (manifesto.md § 核心信念)

| 信念 | 当前完成度 | 证据 / 缺口 |
|---|---|---|
| **B1 数据归你** | **5/5 ✅** | `.garage/` 全部 git-tracked; 无云端 lock-in; F002 零配置启动; 全部 contract 都是 markdown + YAML, 无私有 binary 格式 |
| **B2 宿主可换** | **3/5 ⚠️** | F007 完成三家 first-class adapter (Claude / OpenCode / Cursor), F009 加 user scope; **缺**: 第四家宿主必须改 Garage 源码 (`HOST_REGISTRY` 是硬编码字典); 没有 plug-in 机制让用户/社区注册新宿主 |
| **B3 渐进增强** | **5/5 ✅** | F002 零配置启动; F007 host installer optional; F009 scope 默认 project (CON-901 字节级兼容); 每层 schema 都用 `schema_version` 加 VersionManager 守门 |
| **B4 人机共生** | **3/5 ⚠️** | F003 自动知识提取 + F005 CLI authoring + F006 recall 都在; **缺**: memory 飞轮的 push 端 (系统主动建议"这个模式可以变成 skill"); F003 trigger 是 `archive_session()` 但日常 Cursor / Claude Code 对话从不变成 Garage session — 飞轮不闭合 |
| **B5 可传承** | **2/5 ⚠️** | git clone 是唯一分享路径; **缺**: `garage pack install <git-url>` / `garage pack publish` / 知识脱敏导出 / 跨用户 merge; 一个人的 skills 沉淀无法变成社区资源 |

### 1.2 5 终极形态承诺 (manifesto.md § 终极形态)

| Promise | 完成度 | 阻塞点 |
|---|---|---|
| **P① 几秒变成你的 Agent** | ⚠️ 3/5 | `garage init --hosts <list>` 把 skills 物化到宿主目录工作 (F007/F008/F009), 但**新对话开始时宿主不会自动 load `.garage/knowledge/` 和 `.garage/experience/`** — 用户每次还要手动复述 context |
| **P② 知道你的编码风格** | ❌ 0/5 | F003 的 4 个 KnowledgeEntry 类型 (`decision` / `pattern` / `solution` / `experience_summary`) **没有 style 维度**; 既无"用户偏好"类型, 又无"个人风格指纹"提取流程 |
| **P③ 记得上个月的架构决策** | ⚠️ 4/5 | F003 自动从 archived session 提取 decision-class entry + F006 recall 工作; **缺**: 召回是 pull (用户主动 `garage recall ...`), 不是 push (新对话开始时自动注入) |
| **P④ 调用积累的 50 个 skills** | ✅ 5/5 | F007/F008/F009 把 31 个 skill 装到 3 家宿主的原生 skill surface; 跨过 growth-strategy "Skills > 30" 触发 Stage 3 信号 |
| **P⑤ 知道怎么写你的博客** | ✅ 5/5 | `packs/writing/` 4 skills (blog-writing / humanizer-zh / hv-analysis / khazix-writer) + `packs/search/` ai-weekly 已能端到端覆盖"AI 周报 → 公众号长文" workflow |

### 1.3 4 成长阶段 (growth-strategy.md § 成长阶段)

| Stage | 完成度 | 状态判定 |
|---|---|---|
| **Stage 1 工具箱** | **100% ✅** | `.agents/skills/` 已删除 (F008 ADR-D8-2 candidate C), 全部走 packs/, 31 skills × 3 hosts 端到端工作 |
| **Stage 2 记忆体** | **60% ⚠️** | F003 自动知识提取 ✅ + F004 publication identity ✅ + F005 CLI authoring ✅ + F006 recall + knowledge graph ✅; **缺**: 会话上下文持续化 (Garage session ≠ 宿主 conversation) |
| **Stage 3 工匠** | **5% ⚠️** | "Skills > 30" 触发信号已达成 (current 31); **缺**: 自动 skill 提炼流程 + agent 组装层 (`packs/garage/agents/garage-sample-agent.md` 是占位); growth-strategy 明确说"Stage 3 启动条件已达, 进入此阶段" |
| **Stage 4 生态** | **0%** | growth-strategy 标注"远景, 当前不做详细规划"; 但 B5 信念评分 2/5 暗示 pack 分享机制已是 P1 prerequisite |

```
            完成度
            ┌─────────────────────────────────┐
B1 数据归你 │█████████████████████████████████│ 5/5  ✅
B2 宿主可换 │███████████████████              │ 3/5  ⚠️ HOST_REGISTRY 硬编码
B3 渐进增强 │█████████████████████████████████│ 5/5  ✅
B4 人机共生 │███████████████████              │ 3/5  ⚠️ 飞轮 push 端缺失
B5 可传承   │████████████                     │ 2/5  ⚠️ git clone only
            └─────────────────────────────────┘

P① "几秒变成你的 Agent"      ⚠️ 3/5  ← P0 缺自动 context handoff
P② "知道你的编码风格"        ❌ 0/5  ← P1 style 维度根本不存在
P③ "记得上月架构决策"        ⚠️ 4/5  ← P0 召回是 pull, 不是 push
P④ "调用 50 个 skills"       ✅ 5/5
P⑤ "写你的博客"              ✅ 5/5

Stage 1 工具箱   ████████████████████ 100%
Stage 2 记忆体   ████████████          60%   ← session ingest 缺
Stage 3 工匠    █                       5%   ← 自动提炼 + agent 组装 = 0
Stage 4 生态    ░                       0%
```

## 2. Vision-Gap 倒推 — F010+ 候选清单

把"信念缺口 + promise 缺口 + stage 信号"翻译成具体的待开 cycle. 这里只列 candidate, 不做 spec, 留给 `hf-specify` 阶段.

### 2.1 P0 — 直接卡住愿景交付的 hard blocker

#### F010-A — 自动 context handoff pipeline (`garage sync` + 宿主 context surface)

**愿景影响**: 同时复活 P① + P③ + 让 B4 飞轮真正能转

**问题陈述**:
- 用户在 Cursor / Claude Code 开新对话时, 宿主不会读 `.garage/knowledge/` 也不会读 `.garage/experience/`
- F003-F006 整个 memory 子系统在用户**真实工作流里 invisible**
- 即使知识库里有"上个月做的 ADR-12 选了方案 A 因为 X", 新对话开始时 Agent 不知道

**预期形态**:
- `garage sync` 命令: 把 top-N knowledge + recent experience 编译成宿主原生 context surface
  - Claude Code → `CLAUDE.md` (项目根) + `~/.claude/CLAUDE.md` (用户级)
  - Cursor → `.cursor/rules/garage-context.mdc` (使用 always-apply)
  - OpenCode → 等价路径 (research 阶段确定)
- 触发时机: 显式 `garage sync` + (后续) 可选的 file-watcher
- top-N 选择策略: design ADR 阶段决定 (recent + relevance + size budget)

**预估改动范围**:
- 新增 `src/garage_os/sync/` 模块 (compiler + budget + format)
- 三家 host adapter 各加 `target_context_path` method (与 F007/F009 `target_skill_path` 对称)
- CLI 加 `garage sync` 子命令
- 新增 `.garage/config/sync.json` 配置 (top_n, max_tokens, exclude_kinds)
- 测试: 端到端 sync → context surface 字节级 verify + 宿主原生格式合规

**预估难度**: 中 (依赖 F003 既有 KnowledgeStore + F006 KnowledgeIntegration; 主要工作是 host adapter 扩展 + budget 算法 + 三家 surface 格式调研)

**为什么 P0**: 是 manifesto promise ① + ③ 的最终决定性环节. 不做这件事, F003-F006 投入产出比为零.

#### F010-B — 宿主 session ingestion (`garage session import --from <host-history>`)

**愿景影响**: 闭合 B4 人机共生飞轮的 input 端

**问题陈述**:
- F003 的提取触发是 `SessionManager.archive_session()`
- 但用户日常在 Cursor / Claude Code 的对话**从不变成 Garage session**
- 飞轮的 input 端 (使用 → 积累) 完全断了
- F003 自动提取再厉害, 没有 input 就空转

**预期形态**:
- `garage session import --from claude-code` 读 Claude Code conversation history → 转成 Garage SessionState → 触发 F003 自动提取
- Cursor / OpenCode 类似 (各家 conversation history 路径需调研)
- 配套: `garage session ls` / `garage session show <id>` 增强

**预估改动范围**:
- 新增 `src/garage_os/ingest/` 模块 (per-host history reader)
- CLI `garage session import` 子命令
- 复用既有 SessionManager + 既有 F003 自动提取链
- 三家 host history schema 调研 (research-heavy)

**预估难度**: 中 (依赖各家 history JSON schema 是否稳定 + 是否 documented; 可能需要 reverse-engineer)

**为什么 P0**: 必须在 F010-A 之后 (没有 context inject 没必要把 session ingest 进来), 但缺少这个就让 F010-A inject 的内容静态化 (一次 sync 后再无新知识进来).

### 2.2 P1 — vision completeness, 不卡延期

#### F011-A — Personal style / preference KnowledgeEntry 维度

**愿景影响**: P② 从 0/5 → 5/5

**问题陈述**:
- F003 的 4 个 entry kind (`decision` / `pattern` / `solution` / `experience_summary`) 没有 style 维度
- "用户偏爱 functional 风格" / "用户的中文长文遵循卡兹克风格 (短句+长句节奏 + ...)" / "用户在 Python 里偏好 dataclass 而非 Pydantic" — 这类知识无处存放
- 直接导致 P② "知道你的编码风格" 从 0%

**预期形态**:
- KnowledgeEntry 加 `style` kind (与现有 4 类 schema 对称, 字段扩展同一类)
- 配套自动提取规则: 从 archived session 识别"用户做了 N 次相同选择"模式 → 建议为 style entry
- 半自动 (F003 candidate set + 用户审批)

**预估改动范围**:
- `src/garage_os/types/knowledge_entry.py` 加 `style` enum
- F003 提取规则扩展
- F006 recall 加 style 维度过滤
- 文档 + RELEASE_NOTES

**预估难度**: 低-中 (schema 扩展 + 提取规则 patterns)

#### F011-B — `packs/garage/agents/` 真正落 1-2 个 production agent

**愿景影响**: 启动 Stage 3 工匠 (从占位 sample → 真正可用 agent)

**问题陈述**:
- `packs/garage/agents/garage-sample-agent.md` 是 placeholder
- manifesto 终极形态承诺 "代码审查 agent" / "博客写作 agent" 一个都没有
- Skills > 30 信号已达 (current 31), Stage 3 启动条件已满足

**预期形态**:
- `packs/garage/agents/code-review-agent.md` — 组合 hf-code-review + hf-traceability-review + 用户的 style entry
- `packs/garage/agents/blog-writing-agent.md` — 组合 blog-writing + humanizer-zh + (可选) hv-analysis
- 这两个 agent 是 Stage 3 capability 的最小可证 (proof of capability), 不是完整组装层

**预估改动范围**:
- 写 2 个 agent.md (内容设计为主, 代码改动小)
- INV-1 (current 31 skills) + AGENTS.md packs 表格同步
- 可选: 加 `packs/garage/agents/README.md` 解释组合规则

**预估难度**: 低 (内容创作 + 文档同步; 但 agent 组装本身需要 Stage 3 spec 的 ADR)

#### F011-C — `garage pack install <git-url>` (社区分享最小可用)

**愿景影响**: B5 可传承 2/5 → 3.5/5

**预期形态**:
- `garage pack install https://github.com/<user>/<repo>` 等价于 `git clone <repo> packs/<pack-id>/` + 重跑 `discover_packs` + 写 manifest
- pack.json 加 `source_url` 字段记录来源
- `garage pack ls` 列出已装 pack + source

**预估难度**: 低-中 (主要是 CLI + discover_packs 集成)

### 2.3 P2 — 长期债, 等触发信号

#### F012-A — `HOST_REGISTRY` 改 plug-in 注册

**愿景影响**: B2 宿主可换 3/5 → 5/5

**触发信号** (建议 wait): 出现第 4 家宿主 (Hermes / Aider / 新工具) 用户实际想用

**预期形态**:
- entry-point based 注册 (Python `pkg_resources` / `importlib.metadata`)
- 第三方 pip install 自己的 host adapter package, 自动出现在 `garage init --hosts <name>`

#### F012-B — `garage uninstall --scope` / `garage update --scope`

**愿景影响**: F009 deferred 候选 (与 garage init 反向操作)

**触发信号**: F010-A + F010-B 落地后, 用户开始想"把某 pack 卸掉"或"升级 pack"

#### F012-C — Memory flywheel push 端 ("这个模式可以变成 skill" 主动建议)

**愿景影响**: B4 人机共生 3/5 → 5/5; growth-strategy "自我成长事件" 信号

**触发信号**: F010-B 落地后, Garage session 数 > 50; 重复模式才有统计意义

#### F012-D — `garage sync` 自动化 (file-watcher / git hook)

**触发信号**: F010-A 落地后, 用户嫌每次手跑 `garage sync` 烦

#### F012-E — D7 安装管道扩展为递归 `references/` / `evals/` (F008 deferred)

**触发信号**: 用户反馈"装到 .claude/skills/<id>/ 后 references 没装进来不能加载"

#### F012-F — F009 carry-forward (CON-902 phase 1+3 body 守门 + VersionManager host-installer migration 链注册)

**触发信号**: 与 F012-B 同 cycle 修 (反向操作天然要重审 phase 3 + VersionManager API)

## 3. 推荐下一步路径

### 3.1 单一最优选择

如果只能做一件事, 做 **F010-A (自动 context handoff)**.

理由:
- **杠杆最大**: 同时复活 P① + P③ + 让 B4 飞轮能转
- **沉睡资本 ROI 立刻打开**: F003-F006 已经 build 但用户日常工作流看不到, F010-A 让他们一夜之间被 host see 到
- **复用既有架构**: F007/F009 host adapter pattern 已成熟, 只是从 "skill 装到 .claude/skills/" 扩展到 "context 装到 .claude/CLAUDE.md"; 没有架构性重构成本
- **manifesto-aligned**: "几秒变成你的 Agent" 是 Garage 最响亮的 promise, 当前 3/5 的状态明显是欠交付

### 3.2 推荐组合

如果做 2-3 个 cycle:

```
F010-A (context handoff)  →  F010-B (session ingest)  →  F011-B (2 个 production agent)
        P0                          P0                         P1
        ~ 中等改动                    ~ 中等改动 (research-heavy)    ~ 小改动 (内容创作)
```

逻辑:
1. **F010-A**: 让 inject 能力上线 (用户感知)
2. **F010-B**: 让 inject 内容能持续更新 (闭合飞轮)
3. **F011-B**: 用 inject 后的 context 做 2 个真正可用 agent (Stage 3 启动证据)

之后再回来做 F011-A (style 维度) + F011-C (pack 分享) 把 P② + B5 补齐.

### 3.3 不推荐先做的

- **F011-A (style 维度) 先做**: 没有 F010-A, style 提出来也没人 read (新对话不 inject context)
- **F012-B (uninstall) 先做**: pack 数还少 (4 个), 用户没有强需求; 等用户有 30 个 pack 装在身上才痛
- **F012-A (HOST_REGISTRY 插件化) 先做**: 第 4 家宿主还没出现, 提前抽象有过度设计风险

## 4. 决策提议

**建议在下一对话起 `hf-specify` 起草 F010 spec**, 范围:
- F010-A 核心 (`garage sync` + 三家 host context surface)
- F010-B 暂列 deferred 子功能 (或拆 F010 vs F011 分两个 cycle)

启动顺序:
1. 用户确认本文档 P0/P1/P2 优先级
2. 决定 F010 是只做 A 还是 A+B 一起
3. 启 `hf-specify` 起草 F010 spec
4. 走完整 spec → design → tasks → impl → review/gate → finalize 链路

## 5. 关联文档

- 灵魂: `docs/soul/{manifesto, user-pact, growth-strategy, design-principles}.md`
- README Roadmap (PR#26): `README.md` § Roadmap (短版)
- 已完成 cycles: `RELEASE_NOTES.md` F001-F009
- F009 finalize approval (carry-forward 列表): `docs/approvals/F009-finalize-approval.md`
- F008 candidate C dogfood 路径 (本文档继续遵守): `docs/designs/2026-04-22-garage-coding-pack-and-writing-pack-design.md` ADR-D8-2

---

> **本文档是 planning artifact, 不是 spec**. 真正的 F010 spec 由 `hf-specify` 起草, 并经 `hf-spec-review` 评审后落 `docs/features/F010-...md`.
