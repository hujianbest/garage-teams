# Spec Review — F009 `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择

- 评审目标: `docs/features/F009-garage-init-scope-selection.md`（草稿 r1，2026-04-23）
- Reviewer: 独立 reviewer subagent（按 `hf-spec-review` skill 执行）
- 评审时间: 2026-04-24
- 上游证据基线:
  - `task-progress.md`（Stage=`hf-specify` / Profile=`full` / Mode=`auto`）
  - `docs/features/F008-garage-coding-pack-and-writing-pack.md`（已批准，§ 5 deferred 第 3 行明确指向 F009）
  - `docs/features/F007-garage-packs-and-host-installer.md`（已批准；FR-705 manifest schema / CON-703 / FR-708 marker / FR-704 5-phase 管道）
  - `src/garage_os/adapter/installer/{pipeline,host_registry}.py` + `hosts/{claude,opencode,cursor}.py`（F007 实现入口，已确认 `target_skill_path` / `target_agent_path` 既有签名为 project-root-relative `Path`）
  - `.gitignore` L34 实测：`.garage/config/host-installer.json` 不入 git
  - `docs/soul/{manifesto,user-pact,design-principles,growth-strategy}.md`（workspace-first vs "你做主" / "数据归你" trade-off 锚点）

## Precheck

- [x] 存在稳定 spec 草稿：10 FR + 4 NFR + 4 CON + 4 ASM + 8 项 § 11 非阻塞开放问题，结构骨架对齐项目模板
- [x] route / stage / profile 明确：`task-progress.md` 显示 Stage=`hf-specify`, Profile=`full`, Mode=`auto`，Next Action=`hf-spec-review`
- [x] 上游证据不冲突：F008 closeout 633 测试通过 + spec § 5 deferred 第 3 行 + F007 安装管道实测代码与 spec 描述一致

Precheck **PASS**，进入正式 rubric 审查。

## 结论

需修改

verdict 理由：F009 spec 范围清晰、动机充分（solo creator 跨多客户项目摩擦实测可验证）、与 F007/F008 既有契约边界明确（§ 4.3 表逐项标注影响 / 不变）、deferred backlog 完整、ASM/CON 显式可回读、11 项 success criteria 可派生为验收、8 项 § 11 非阻塞 design 决策每项均带默认值（设计可消化）。但发现 **4 条 important LLM-FIXABLE** finding 集中在 (a) **CON-901/NFR-901 "字节级一致" 与 FR-905 manifest schema migration 的概念边界模糊**、(b) **CON-902 "phase 5 算法字节级保持" 与 FR-905 manifest schema 升级的执行时序未澄清**、(c) **FR-903 交互式两轮提示缺 "all P / all u" 快捷路径的设计决策点未列**、(d) **dogfood 不破坏的硬约束缺独立验收 anchor**；以及 5 条 minor LLM-FIXABLE 边界细化。无 critical、无 USER-INPUT、无 route/stage/证据冲突。所有 finding 都能在 1 轮定向回修内闭合，不破坏核心范围、不引入新业务事实，因此判 `需修改` 而非 `阻塞`。

## 发现项

### Critical

无 critical 级 finding。

### Important

- [important][LLM-FIXABLE][C2/C7] **CON-901 / NFR-901 "字节级一致" 与 FR-905 manifest schema migration 的概念边界模糊**：
  - NFR-901 验收 #1 写 "F008 cycle 期间录制的 `garage init --hosts claude` 端到端 stdout/stderr 副本... F009 实施后再跑同样命令... 字节级一致（除 stdout 中可变 path 部分）"，验收 #2 写 "F007/F008 既有 30+ installer 测试 100% 通过且 0 改写"。
  - 但 FR-905 同时承诺 "F008 用户已落下的 schema 1 manifest，F009 第一次 init 自动迁移到 schema 2，旧 entry 全部 `scope: "project"` + dst 由 relative 转 absolute"。
  - 矛盾点：(a) F008 用户首次跑 F009 init 时 `.garage/config/host-installer.json` 文件**内容必然变化**（schema_version 1→2、dst relative→absolute、新增 scope 字段），与 NFR-901 "`.garage/` 目录创建" 字节级一致措辞冲突；(b) F007/F008 既有测试若含 manifest 字段断言（如 `dst: ".claude/skills/garage-hello/SKILL.md"` 这种 relative path 字面值），在 F009 schema 2 下必然失败，与 NFR-901 验收 #2 "0 改写" 冲突。
  - 修复指引：在 NFR-901 验收陈述中显式枚举 "字节级一致" 的 manifest 例外，明确 `.garage/config/host-installer.json` 的内容会因 schema migration 而变化，但 stdout / stderr / exit code / `<cwd>/.{host}/skills/<id>/SKILL.md` 文件落盘字节不变；并把 "0 改写" 松绑为 "0 语义退绿，schema migration 引起的 manifest 字段断言可机械适配"。
  - 锚点：F009 spec L391-399（NFR-901）、L322-336（FR-905）、L437-442（CON-901）。

- [important][LLM-FIXABLE][C2/A3] **CON-902 "phase 5 算法主体字节级保持" 与 FR-905 manifest schema 升级的执行时序未澄清**：
  - CON-902 + FR-906 验收 #1 写 "phase 5 (apply + manifest) 的算法主体字节级保持原状（仅 type signatures 因 `_Target` 增 scope 字段而扩展）"。
  - FR-905 同时承诺 manifest schema 1→2 升级 by `VersionManager` 自动 migration。
  - 但 spec 未明确：(a) `VersionManager.migrate` 调用时机 — 是 `garage init` 入口的 phase 0（pipeline 之前预处理）？还是 phase 5 manifest write 内部？(b) phase 5 写出的 manifest 字段集合（schema_version、dst 形态、scope 新字段）已发生改变，"字节级保持" 的语义边界是 "phase 5 的核心循环 / 错误分支结构不变" 还是其他？仅说 "type signatures 扩展" 在 phase 5 这里似乎覆盖不足 — 写入 schema 与序列化形式都变了，并非只是签名扩展。
  - 修复指引：在 FR-906 / CON-902 / FR-905 之间加一条 ordering anchor，例如 "FR-905 migration 发生在 pipeline 入口（phase 0），写入 manifest 时 phase 5 直接按 schema 2 写"；并把 FR-906 验收 #1 中 "字节级保持原状" 改为 "phase 5 的核心循环结构 / 写入顺序 / 错误分支与 F007/F008 等价，仅写入的 schema 升至 2 + 字段集合按 FR-905 扩展"。这样 design 阶段 reviewer 不会因 "phase 5 字面字节级 vs 写出 schema 必然变" 的冲突把 design 拒回 spec。
  - 锚点：F009 spec L444-449（CON-902）、L337-345（FR-906）、L322-336（FR-905）、L83-85（§ 2.2 #11）。

- [important][LLM-FIXABLE][Q3/C2] **FR-903 交互式 per-host scope 选择缺 "全选 P / 全选 u" 快捷路径设计决策点**：
  - FR-903 + § 3.2 场景 #5 描述：用户选 N 个宿主后，对每个宿主独立提示 `[P/u]`。N=3（claude + cursor + opencode）时，用户需要回答 3 次 P/u；FR-903 验收 #2 默认全部回车 = 全 project。
  - 缺口：(a) 没有 "all P" / "all u" 一键快捷选项；(b) § 11 非阻塞 #5 留 "两轮 vs 一轮带 scope 后缀" 给 design，但没显式列出 "是否提供 all-project / all-user / per-host 三选一开关" 这第三个 design 决策点 — design 阶段 reviewer 可能反问 "为何没考虑批量"。
  - 修复指引：把 § 11 非阻塞 #5 wording 扩展为 "两轮 vs 一轮带 scope 后缀 vs 三选一开关（all-project / all-user / per-host），design 决定"；或在 FR-903 验收 / 边界中显式声明 "design 可选择是否引入批量快捷选项，spec 不强约束"。这是 LLM-FIXABLE wording 微调，不需要新业务输入。
  - 锚点：F009 spec L297-306（FR-903）、L141-149（§ 3.2 场景 #5）、L515（§ 11 非阻塞 #5）。

- [important][LLM-FIXABLE][C6/C2] **dogfood 不破坏的硬约束缺独立验收 anchor**：
  - § 2.2 #9 + § 3.2 场景 #12 + § 4.3 表 "F008 ADR-D8-2 dogfood 候选 C — 保留" + CON-901 都从语义上承诺 "本仓库自身 `garage init --hosts cursor,claude` 仍 project scope，与 F008 完全等价"。
  - 但没有任何独立 FR / NFR 验收给出可机械守门的检查，例如 "在 `cwd=/workspace` 跑 `garage init --hosts cursor,claude` 后产物（`.cursor/skills/` + `.claude/skills/` + `.garage/config/host-installer.json` 的 schema 2 形态）与 F008 closeout commit 的 dogfood baseline 在 (a) skill SKILL.md 字节、(b) agent 字节、(c) manifest schema 2 等价语义下 diff 为空（除可变 path 部分）"。
  - 风险：到 design / regression-gate 时缺 anchor，reviewer 与实施者对 "dogfood 不变" 的具体含义可能各自理解；本仓库 IDE 加载入口若被 F009 静默改变（如某 marker 文本变化）会延迟到 PR review 才发现。
  - 修复指引：在 NFR-901 验收追加一条独立守门，例如 "**Dogfood 不变性守门**：在 `cwd=/workspace` 跑 `garage init --hosts cursor,claude` 后，`.cursor/skills/` + `.claude/skills/` + `.claude/agents/` 下所有文件字节与 F008 closeout commit `bafbd1c` 父链的 dogfood baseline 字节级一致；`.garage/config/host-installer.json` 在 schema 2 升级后语义等价（旧 entry 全部 `scope: "project"` + dst absolute；其它字段一致）"；或单独抽一条 NFR-905。
  - 锚点：F009 spec L83（§ 2.2 #9）、L196-202（§ 3.2 #12）、L248（§ 4.3 表 dogfood 行）、L391-399（NFR-901）、L437-442（CON-901）。

### Minor

- [minor][LLM-FIXABLE][C7/A3] **FR-909 多 scope stdout 附加段未约束行结构，可能影响 F007 下游 grep 兼容**：
  - FR-909 验收 #1 已守门 "单 scope 时不附加（与 F007 字节级一致，CON-901）"。但混合 scope 时附加段（spec 默认 wording `(N_user user-scope, N_project project-scope)`）的行结构未约束 — 接续在 `Installed N skills...` 同一行 vs 新起一行直接影响 F007/F008 下游脚本既有 grep `Installed.*skills` 是否还能命中且字段顺序不变。
  - 修复指引：在 FR-909 验收追加 "附加段必须独占新行，F007 既有 grep `Installed.*skills, .* agents into hosts:` 在单 scope 与混合 scope 下均一行命中且字段顺序不变；附加段作为独立可 grep 的新行（如 `Scope distribution: N_user user-scope, N_project project-scope`）"；具体 wording 仍可由 design 收敛，但 "独占新行 + F007 既有 grep 不破坏" 应作为 spec 层不变量。
  - 锚点：F009 spec L367-373（FR-909）、L513（§ 11 非阻塞 #3）。

- [minor][LLM-FIXABLE][Q3/C2] **per-host scope override 语法 `<host>:<scope>` 与未来宿主 host_id 含 `:` 的兼容性边界缺显式记录**：
  - F007 既有三家 host_id（claude / opencode / cursor）都不含 `:`，FR-902 语法在当前注册表下无歧义。但 spec § 4.2 关键边界未声明 "未来引入新宿主时 host_id 不得含 `:` 字符" 这条约束，将给后续宿主扩展留隐性陷阱。
  - 修复指引：在 § 4.2 关键边界加一行约束 "未来在 host registry 引入新宿主时，`host_id` 不得含 `:` 字符以保留 FR-902 per-host scope override 语法 `<host>:<scope>` 的无歧义解析"；或在 § 11 非阻塞列入 design 注意点。LLM 可写，无业务输入。
  - 锚点：F009 spec L286-295（FR-902）、L221-231（§ 4.2）。

- [minor][LLM-FIXABLE][C7] **NFR-902 测试基线 "≥ 633 + 新增" 缺增量量级预估**：
  - F008 增量是 +47（633 = 586 + 47）。F009 design 阶段会更精确，但 spec 是否需给个量级预期供 task-board 早期估算？当前 NFR-902 仅写 "≥ 633 + 新增"，没有量级 anchor。
  - 修复指引：在 NFR-902 详细说明加一句 "新增测试预期量级约 30-60 个（覆盖三家 adapter user scope path × 2 method + flag 解析 + per-host 语法 + 交互两轮 + manifest 1→2 migration + 幂等分 scope + status 分组 + Path.home() RuntimeError + fixture 隔离），最终数由 design / tasks 阶段精确化" 作为 informational 锚点。这不是硬约束，仅供 task-board 早期估算。
  - 锚点：F009 spec L401-409（NFR-902）。

- [minor][LLM-FIXABLE][C2/C7] **manifest absolute path 跨用户不可移植性的预期未显式说明**：
  - § 11 非阻塞 #4 留 design 决定 "manifest serialization 时是否把 home 部分还原为 `~/...`"，但 spec 没显式说明 "manifest 在 git track 与否 / 跨用户 clone 场景的 F009 立场"。实测：本仓库 `.gitignore` L34 已排除 `.garage/config/host-installer.json`，dogfood 仓库不入 git；但下游用户场景多样，有人会 commit 该文件作为 "team baseline"。
  - 修复指引：在 ASM 段加一条 ASM-905（或在 § 4.2 加一行）："manifest 默认不入 git（与 dogfood 仓库 `.gitignore` 实测一致），跨用户 clone 不是 F009 必须支持的场景；下游用户若自行 commit manifest，跨用户 user-scope absolute path 不可移植由用户自行承担"。这是 LLM 可写的预期声明，避免 design / future bug 时被反问。
  - 锚点：F009 spec L514（§ 11 非阻塞 #4）、`.gitignore` L34 实测。

- [minor][LLM-FIXABLE][A6] **FR-903 non-TTY 退化路径是否在 stderr 提示 "scope 选择被跳过" 未约束**：
  - FR-903 验收 #4 写 "non-TTY 沿用 F007 FR-703 退化（`--hosts none` + stderr 提示），不进入第二轮 scope 提示"。但 stderr 提示是否提示 scope 选择被跳过 / 提示用户应显式传 `--scope` 未约束，影响 CI / Cloud Agent 用户调试体验。
  - 修复指引：在 FR-903 验收 #4 加一条 "non-TTY 退化时 stderr 提示文本应同时包含 `--hosts` 与 `--scope` 两个建议 flag（或显式说明 scope 默认 project 不需 flag），让 CI 用户从 stderr 直接看到完整非交互调用模板"。LLM 可写。
  - 锚点：F009 spec L297-306（FR-903 验收 #4）。

## 缺失或薄弱项

1. **CON-901/NFR-901 "字节级一致" 与 FR-905 manifest schema migration 的概念边界**（见 important #1）。spec 未显式枚举 manifest 是 "字节级一致" 的合法例外。
2. **CON-902 "phase 5 算法字节级保持" 与 FR-905 schema 升级的执行 ordering anchor**（见 important #2）。spec 未澄清 `VersionManager.migrate` 调用时机与 phase 5 写入 schema 2 的边界。
3. **FR-903 交互式批量快捷路径的 design 决策点未列**（见 important #3）。
4. **dogfood 不破坏的独立验收守门 anchor**（见 important #4）。
5. **per-host scope override 语法对 future host_id 命名的隐性约束未声明**（见 minor #2）。
6. **测试基线增量量级未给 informational anchor**（见 minor #3）。
7. **manifest 跨用户 / git track 立场未显式声明**（见 minor #4）。
8. **non-TTY 退化路径 stderr 提示完整性未约束**（见 minor #5）。

## 下一步

`hf-specify`（按本 review 的 4 important + 5 minor 做 1 轮定向回修；预计回修后即可 `通过`）

回修建议聚焦：
- 把 NFR-901 "字节级一致" 显式枚举 manifest 例外；旧测试 "0 改写" 松绑为 "0 语义退绿"（important #1）
- 把 CON-902 / FR-906 验收 #1 / FR-905 三处加 ordering anchor，澄清 migration 调用时机 + phase 5 字节级语义（important #2）
- 把 § 11 非阻塞 #5 wording 扩展三选一 design 决策点；FR-903 不强约束（important #3）
- 在 NFR-901 加 "Dogfood 不变性守门" 验收 anchor（或单独 NFR-905）（important #4）
- 5 条 minor 一并按修复指引微调

回修期间不需向真人提任何 USER-INPUT 问题——所有 finding 均 LLM-FIXABLE。8 项 § 11 非阻塞放权 design 与 spec 默认值合理，不需提前升级为 USER-INPUT。

## 记录位置

`docs/reviews/spec-review-F009-garage-init-scope-selection.md`

## 交接说明

- `规格真人确认`：本轮 verdict = `需修改`，不进入。
- `hf-specify`：父会话应把本 review 记录路径与 4 important + 5 minor 全部回传给负责 spec 修订的会话；预计 1 轮定向回修 + 1 轮 review 即可冻结进入 design。
- `hf-workflow-router`：route / stage / 证据无冲突，不需要 reroute（`reroute_via_router=false`）。
- 不修改 `task-progress.md`、不修改 F009 spec 文档、不 git commit / push（由父会话执行）。
