# Design Review — F009 `garage init` 双 Scope 安装（project / user）+ 交互式 Scope 选择

- 评审目标: `docs/designs/2026-04-23-garage-init-scope-selection-design.md`（草稿 r1，2026-04-23）
- Reviewer: 独立 reviewer subagent（按 `hf-design-review` skill 执行）
- 评审时间: 2026-04-24
- 上游证据基线:
  - `task-progress.md`（Stage=`hf-design` / Profile=`full` / Mode=`auto` / Next=`hf-design-review`）
  - `docs/features/F009-garage-init-scope-selection.md`（已批准 r2 + auto approval；10 FR + 4 NFR + 4 CON + 4 ASM + § 11 非阻塞 7 项 + 9 ADR 待消化清单）
  - `docs/approvals/F009-spec-approval.md`（auto-mode approval；明确 9 项 ADR 决策范围）
  - `docs/reviews/spec-review-F009-garage-init-scope-selection.md`（r1 需修改 / r2 通过；含 1 条 narrative gap 已在 approval 顺手清理）
  - F008 baseline 633 测试 + 0 改写 + INV-5 + INV-6 + ADR-D8-2 候选 C dogfood 作为 D009 硬约束
  - F007 安装管道 5 phase + manifest schema 1 作为 CON-902 / FR-905 直接基线

## Precheck

- [x] 存在稳定 design 草稿：9 ADR + 6 类工程动作（T1-T6）+ 9 INV + 10 测试文件 + 7 失败模式 + § 17 排除项 14 条；§ 1-§ 18 章节骨架完整
- [x] 已批准规格可回读：F009 spec r2 通过 + auto approval，§ 4.2 关键边界 + NFR-901..904 + CON-901..904 + § 11 非阻塞 7 项均已稳定
- [x] route / stage / profile 一致：`task-progress.md` Stage=`hf-design`，Next=`hf-design-review`，无证据冲突
- [x] design 草稿与 spec approval 中明确的 9 项 ADR 决策清单一一对应（design ADR-D9-1 ↔ spec § 11 非阻塞 #1，..., D9-8 ↔ approval #8 ManifestMigrationError，D9-9 ↔ approval #9 host_id 命名）

Precheck **PASS**，进入正式 rubric 审查。

## 多维评分（0-10，内部参考）

| ID | 维度 | 分 | 关键观察 |
|---|---|---|---|
| D1 | 需求覆盖与追溯 | 9 | § 3 表完整覆盖 FR-901..910 + NFR-901..904 + CON-901..904 + § 11 非阻塞 7 项；9 ADR 与 spec approval 9 项决策清单一一对应；§ 17 与 spec § 5 deferred 14 条数量等价（仅 1 处 wording inconsistency，详 minor M4） |
| D2 | 架构一致性 | 8.5 | § 4 Strategy + Schema Versioning + Optional Protocol Methods 模式清楚；§ 8.1/8.2/8.3 三视图（pipeline 流图 + 交互 UX + manifest schema 对比）齐全；§ 11 模块职责边界表清楚；架构是连贯系统而非组件清单 |
| D3 | 决策质量与 trade-offs | 7.5 | 9 ADR 中 7 个有完整 Compare 表（候选数 2-3）+ Decision + Consequences + Reversibility；ADR-D9-9 仅给 Decision 缺 Compare 表（M1）；ADR-D9-4 与 D9-3 强联动，Compare 退化（M2）；ADR-D9-2 标题"phase 2 唯一改动点"与跨 phase 2/4/5 实际改动 narrative gap（详 minor M5） |
| D4 | 约束与 NFR 适配 | 7.5 | § 12 把 NFR/CON 落地到 commit 与模块；§ 11.1 9 个 INV 各带验证方式；§ 14 F1-F7 失败模式带触发 + 缓解；**但 § 14 F1 `UserHomeNotFoundError` 类型缺独立 ADR 锚定**（spec § 11 非阻塞 #2 是 design 决定项，与 ManifestMigrationError 在 ADR-D9-8 升级处理形成不对称，I1） |
| D5 | 接口与任务规划准备度 | 7.5 | § 11 模块表 + § 10.1 T1-T6 commit 分组 + § 15 readiness 段清楚，hf-tasks 可直接拆 6 task；但 § 10.1 T1 commit 描述说 "4 个新增测试文件" 实际只列 2 个，与 § 13 测试矩阵 10 文件对应关系数字对不上（M3） |
| D6 | 测试准备度与隐藏假设 | 7 | § 13.1 自动化 10 文件 + § 13.2 manual smoke 5 路径 + § 14 F1-F7 + § 18 非阻塞 3 项；**但 § 13 sentinel test 边界（dogfood SHA-256 在不同贡献者本地 cwd 下 manifest dst 含路径差异）未澄清**（与 ADR-D9-3 绝对展开 + spec NFR-901 验收 #4 manifest 等价语义边界 ordering 直接相关，I2）；test_full_init_user_scope.py vs test_dogfood_invariance_F009.py 边界（user scope tmp_path 全装 vs dogfood project scope baseline）未显式分清（M5）；ADR-D9-5 candidate C 第二轮 a/u/p 与 dogfood 走非交互的关系未 anchor（M7）|

> 任一关键维度低于 6 → 不得通过：**全部 ≥ 7**，未触发硬性拒。
> 任一维度 < 8 → 通常至少对应一条 finding：D3 / D4 / D5 / D6 均对应至少一条具体 finding ✓

## 结论

**需修改**

verdict 理由：D009 设计**整体扎实**，对 spec § 4.2 关键边界 / NFR-901 字节级 / CON-902 phase 1 + phase 3 严格不变 / CON-904 跨用户立场等多重硬约束均做出了正确的承接：9 ADR 全部带可逆性、8 个 ADR 给出 Compare 表、§ 8 三视图清晰、§ 11 9 个 INV 与验证方式对齐、§ 10.1 6 类提交分组直接对应 NFR-904。但发现 **2 条 important LLM-FIXABLE finding** 集中在 (a) **`UserHomeNotFoundError` 类型缺独立 ADR 锚定**（与 ManifestMigrationError 处理不对称，spec § 11 非阻塞 #2 是 design 显式决定项）+ (b) **§ 13 dogfood SHA-256 sentinel test 在 ADR-D9-3 绝对展开后 manifest 跨贡献者 cwd 差异的边界未澄清**，会直接导致 hf-tasks 阶段 sentinel test 实施时缺设计指引；以及 **6 条 minor LLM-FIXABLE** 边界细化与 wording 一致性。无 critical、无 USER-INPUT、无 route/stage/证据冲突，所有 finding 均能在 1 轮定向回修内闭合且不破坏 spec 范围、不引入新业务事实，因此判 **需修改** 而非 **阻塞**。

## 发现项

### Critical

无 critical 级 finding。

### Important

- **[important][LLM-FIXABLE][D4]** **§ 14 F1 `UserHomeNotFoundError` 类型缺独立 ADR 锚定**：
  - § 14 F1 写 "`Path.home()` 抛 RuntimeError → ... 应抛 `UserHomeNotFoundError` → CLI exit 1 + stderr 含 `Cannot determine user home directory: ...`（ASM-903 缓解）"。
  - 但 spec § 11 **非阻塞 #2** 明确写 "`Path.home()` 抛 `RuntimeError` 的退出码：spec 默认 1（与 unknown host 同级），design 决定是否需要专用退出码（如 3）"——这是 design 显式决定项。
  - **不对称证据**：另一条同级 design 决定项 ManifestMigrationError 在 design 中升级到了 ADR-D9-8（带 Compare / Decision / Consequences / Reversibility 完整结构），而 `UserHomeNotFoundError` 仅在 § 14 失败模式表里出现一行，缺 ADR 形式锚定。
  - **影响**：hf-tasks 阶段拆 task 时，开发者需要决定 (a) 是新增 `UserHomeNotFoundError(RuntimeError)` 类型还是直接 catch + 重新 raise (b) exit 1 是 CLI 层捕获还是 pipeline 层 (c) stderr wording 是否在 ADR 锚定。这些决策若不在 design 锚定，hf-tasks 会出现"design 没说，自己定" 的设计漏洞。
  - **修复指引**：新增 ADR-D9-10（或合并入 ADR-D9-8 Consequences）"`UserHomeNotFoundError` 类型与退出码"，给出 Compare（专用类型 vs 直接 RuntimeError，CLI 捕获 vs pipeline 捕获，exit 1 vs exit 3）+ Decision（建议默认 exit 1 + 专用类型 `UserHomeNotFoundError` 在 `pipeline` 或 `adapter` 抛出 + CLI 层捕获）+ Consequences；同时同步 § 11 模块职责表与 § 13 测试矩阵增补 `test_path_home_failure.py` 或合并到既有 user scope adapter 测试。
  - **锚点**：design § 14 F1（L576）、ADR-D9-8（L288-308）、spec § 11 非阻塞 #2（L525）、ASM-903（L497-503）。

- **[important][LLM-FIXABLE][D6]** **§ 13 dogfood SHA-256 sentinel test 边界与 ADR-D9-3 绝对展开 + spec NFR-901 验收 #4 manifest 等价语义未对齐**：
  - ADR-D9-3 选 **绝对展开**（POSIX `/home/<user>/...`），并在 Consequences 显式承认 "manifest 跨用户不可移植"。
  - § 13 测试矩阵 `test_dogfood_invariance_F009.py` 触发 `INV-F9-1`，§ 11 INV-F9-1 验证方式写 "SHA-256 对比 F008 baseline"。
  - **gap**：spec NFR-901 验收 #4 显式声明 dogfood SHA-256 比对范围是 `.cursor/skills/` + `.claude/skills/` + `.claude/agents/` 三目录文件，**manifest 字段稳定语义**是 "schema_version 允许 1→2 但 `files[].host` + `files[].scope: "project"` + `files[].content_hash` 必须保持稳定（migration 后内容不变只是字段更名）"——明确豁免 `files[].dst` 字段（因为升级到 absolute path，含 cwd / home 部分必然不同）。但 design § 13 sentinel test 描述 + ADR-D9-3 Consequences 没有把这条 manifest 等价语义边界 anchor 下来，hf-tasks 阶段实施 sentinel 时会卡在 "manifest 到底比 SHA-256 还是字段集合等价" 的设计空洞。
  - **额外风险**：在不同贡献者本地 clone 路径不同（CI 是 `/workspace`，本地可能是 `/home/alice/repo/garage/`），sentinel test 若直接 SHA-256 比 manifest，必然在所有贡献者本地都失败。design 必须显式锚定 sentinel test 的 manifest 比对策略：(a) 仅测三目录字节 + manifest 字段集合等价（按 NFR-901 验收 #4 拆出 host/scope/content_hash 三字段稳定） (b) 或先 normalize 路径再比 SHA-256 (c) 或固定本仓库 fixture cwd 跑 dogfood。
  - **修复指引**：在 § 13 表 `test_dogfood_invariance_F009.py` 行后或 ADR-D9-3 Consequences 加段，显式锚定："sentinel test 字节级比对范围：(a) `.cursor/skills/` + `.claude/skills/` + `.claude/agents/` 三目录所有文件 SHA-256 与 F008 dogfood baseline `/opt/cursor/artifacts/f008_dogfood_init.log` 一致；(b) `.garage/config/host-installer.json` 仅比 `files[].host` + `files[].scope == "project"` + `files[].content_hash` + `installed_hosts` + `installed_packs` 字段集合稳定，**`files[].dst`（含 cwd 绝对路径部分）+ `installed_at` + `schema_version` 三字段不参与比对**（NFR-901 验收 #4 明确豁免）；(c) sentinel test 通过 `monkeypatch.chdir(workspace_root)` 固定 cwd 为本仓库根，避免本地不同贡献者 clone 路径差异。"
  - **锚点**：design § 13 测试矩阵（L548-557）、ADR-D9-3 Consequences（L179-184）、§ 11 INV-F9-1（L512）、spec NFR-901 验收 #4（L404）。

### Minor

- **[minor][LLM-FIXABLE][D3]** **ADR-D9-9 host_id 命名约束缺 Compare 表**：design § 7 ADR-D9-9 仅给 Decision（双层守门：import-time assert + Protocol docstring），但没正式列出 "运行时静态 assert vs 静态文档 vs 双层" 三候选的 trade-off 矩阵；与 D3 评分 rule "至少比较两个可行方案" 偏差。修复指引：补一个简短 Compare 表（候选 A 仅运行时 assert / 候选 B 仅 docstring / 候选 C 双层），各列优点 + 风险 + 可逆性。**锚点**：ADR-D9-9（L310-324）。

- **[minor][LLM-FIXABLE][D3]** **ADR-D9-4 跨用户立场 Compare 表退化为单选**：ADR-D9-4 与 ADR-D9-3 强联动，在 § 5 总览表写 "2（追求可移植 / 不追求）" 但 § 7 ADR-D9-4 只给 Decision 没列 Compare 表，与 ADR-D9-3 的 `~/` 候选已比较过有重叠但形式上仍宜简短列出 "追求可移植" 的代价（serialization 复杂度 + 反序列化 expanduser + 与 NFR-903 POSIX 序列化一致性偏差），让 reviewer 能冷读 trade-off 而不需跳到 ADR-D9-3。修复指引：ADR-D9-4 加 1-2 行 Compare 表或显式注 "trade-off 已在 ADR-D9-3 论证，此处仅锚定结论"。**锚点**：ADR-D9-4（L187-198）、ADR-D9-3（L165-185）。

- **[minor][LLM-FIXABLE][D5]** **§ 10.1 T1 commit 描述与 § 13 测试矩阵数字对不上**：§ 10.1 T1 commit 描述写 "4 个新增测试文件: test_adapter_user_scope.py / test_host_registry_colon_assert.py"——文字数 "4 个" 与列出的 2 个文件数不一致；§ 13 测试矩阵 10 文件与 § 10.1 T1-T5 分摊关系（T1 占 2、T2 占 1、T3 占 2、T4 占 4、T5 占 2 = 11 文件 vs 10 文件）也对不严格上。修复指引：把 T1 描述 "4 个" 改为 "2 个"；同时在 § 10.1 各 T 末尾显式列对应的测试文件名，让 hf-tasks 拆 task 时可一一对照。**锚点**：design § 10.1（L460-485）、§ 13.1（L548-557）。

- **[minor][LLM-FIXABLE][D1]** **§ 17 与 spec § 5 deferred 第 14 项候选编号 inconsistency**：spec § 5 第 14 行 "D7 管道扩展为递归 `references/` 子目录 — F008 已 deferred 为 D9 候选；与 F009 正交 — 仍是 **D9 候选**（与 F009 同 stage 但独立 cycle）"；design § 17 第 14 行写 "D7 管道扩展为递归 references/ — F008 已 deferred 为 D9 候选 — 仍是 **D10 候选**"。spec 意图是与本 F009/D9 同 stage 但独立 cycle，design 改成 D10 候选与 spec wording 不一致。修复指引：把 design § 17 末行候选编号改回 "D9 候选" 或显式注明 "deferred 至下一可用 cycle 编号"，与 spec § 5 wording 一致。**锚点**：design § 17（L613）、spec § 5（L271）。

- **[minor][LLM-FIXABLE][D3]** **ADR-D9-2 标题 wording "Phase 2 内部唯一改动点" 与跨 phase 2/4/5 实际改动 narrative gap**：ADR-D9-2 标题 + § 5 总览表 + § 7 Decision 都说 "Phase 2 内部唯一改动点"，但 §2.2 NFR/CON 落地表 + § 8.1 架构图 + § 10.2 验证表均显示实际跨 phase 2 (scope 分流) + phase 4 (5 元组比对) + phase 5 (schema 升级 + VersionManager.migrate 调用)。"唯一改动点" 实指 **scope-routing 这件事在 phase 2 唯一发生**（phase 4/5 的差异是 schema 升级派生的字段集合扩展），但读者从标题字面理解会误以为 phase 4/5 也字节级不动。修复指引：把 ADR-D9-2 标题改为 "Pipeline scope-routing 落点（phase 2）+ CON-902 phase 1/3 严格不变"；或在 Decision 段加一行 "本 ADR 锚定 scope-routing 这件事的落点；phase 4 5 元组扩展 + phase 5 schema 1→2 + VersionManager.migrate 调用是 CON-902 enum 已豁免的派生改动，不在本 ADR 范围"。**锚点**：design ADR-D9-2（L145-163）、§ 8.1（L344-360）、spec CON-902（L450-461）。

- **[minor][LLM-FIXABLE][D6]** **§ 13 `test_full_init_user_scope.py` 与 `test_dogfood_invariance_F009.py` 边界关系未显式说明**：两文件目的相邻：(a) `test_full_init_user_scope.py` 在 tmp_path 跑 `garage init --scope user` 三家宿主端到端 (user scope 全装 + manifest scope=="user")；(b) `test_dogfood_invariance_F009.py` 在本仓库 fixed cwd 跑 `garage init --hosts cursor,claude` (project scope SHA-256 baseline 比对)。设计意图清楚，但 § 13 表只列触发 INV，没显式分清两者。修复指引：在 § 13 表后加 1-2 行说明 "(a) `test_full_init_user_scope.py` 用 `monkeypatch.setattr(Path, 'home', lambda: tmp_path / 'fakehome')` 隔离 user scope 路径，验证 user scope 端到端落盘；(b) `test_dogfood_invariance_F009.py` 用 `monkeypatch.chdir(workspace_root)` 固定 cwd，验证 project scope dogfood SHA-256 baseline 不变；二者 fixture 隔离方式互不重叠"。**锚点**：design § 13（L548-557）。

- **[minor][LLM-FIXABLE][D6]** **ADR-D9-5 candidate C 第二轮 a/u/p 与 dogfood 走非交互的关系未 anchor**：ADR-D9-5 选定 candidate C 增加第二轮 a/u/p 提示。dogfood 在 CI / 本仓库贡献者本地都走非交互（`--hosts cursor,claude` 显式），不会触发 candidate C 第二轮，所以 NFR-901 Dogfood 不变性硬门槛 SHA-256 不受 candidate C 影响。但 ADR-D9-5 Consequences 没显式说这点，hf-tasks 实施时可能误以为 candidate C 会破坏 dogfood SHA-256 (CON-901 兼容性焦虑)。修复指引：在 ADR-D9-5 Consequences 加一条 "✅ Dogfood 不受影响：dogfood 走非交互 (`--hosts cursor,claude` 显式)，candidate C 第二轮提示仅在 TTY 无 `--hosts` 时触发，与 NFR-901 验收 #4 SHA-256 字节级硬门槛正交"。**锚点**：design ADR-D9-5（L200-220）、§ 13 sentinel（L556）、spec NFR-901 验收 #4（L404）。

## 缺失或薄弱项

1. **`UserHomeNotFoundError` 类型与退出码缺独立 ADR**（important I1）—— spec § 11 非阻塞 #2 显式 design 决定项，与 ManifestMigrationError 在 ADR-D9-8 处理不对称
2. **§ 13 dogfood SHA-256 sentinel test 在 ADR-D9-3 绝对展开 + 不同贡献者 cwd 差异下的 manifest 等价语义边界未澄清**（important I2）—— 直接影响 INV-F9-1 sentinel 实施可行性
3. **ADR-D9-9 缺 Compare 表**（minor M1）—— 与 D3 评分 rule "至少比较两个可行方案" 偏差
4. **ADR-D9-4 Compare 表退化**（minor M2）—— 与 D9-3 强联动但形式上单选
5. **§ 10.1 T1 测试文件数 "4 个" 文字与实际 2 个对不上**（minor M3）—— 数字 inconsistency
6. **§ 17 deferred 第 14 项 "D9 候选" vs "D10 候选" inconsistency**（minor M4）—— 与 spec § 5 wording 不一致
7. **ADR-D9-2 标题 "phase 2 唯一改动点" wording 与跨 phase 2/4/5 实际改动 narrative gap**（minor M5）
8. **§ 13 user scope 集成测试与 dogfood sentinel 边界未显式分清**（minor M6）
9. **ADR-D9-5 candidate C 与 dogfood 非交互关系未 anchor**（minor M7）

## 下一步

`hf-design`（按本 review 的 2 important + 7 minor 做 1 轮定向回修；预计回修后即可 `通过`）

回修建议聚焦：

- **I1**：新增 ADR-D9-10 "`UserHomeNotFoundError` 类型与退出码" 或合并入 ADR-D9-8 Consequences；同步 § 11 模块职责表（adapter 或 pipeline 抛出位置）+ § 13 测试矩阵增补 `test_path_home_failure.py` 或合并到既有 user scope adapter 测试
- **I2**：在 § 13 表 `test_dogfood_invariance_F009.py` 行后加段或 ADR-D9-3 Consequences 显式锚定 sentinel test 的 (a) 三目录字节 SHA-256 + (b) manifest 字段集合等价（按 NFR-901 验收 #4 拆出 host/scope/content_hash 稳定 + dst/installed_at/schema_version 豁免）+ (c) `monkeypatch.chdir(workspace_root)` 固定 cwd
- **M1-M7**：按各条修复指引微调，预计每条 1-3 行文字修订

回修期间不需向真人提任何 USER-INPUT 问题——所有 finding 均 LLM-FIXABLE。9 项 ADR 选定与 spec § 11 默认值一致（ADR-D9-1/3/5/6/7/8/9 全部按 spec 默认或 r1 升级方向收敛），不存在需要 USER-INPUT 升级的决策。

## 记录位置

`docs/reviews/design-review-F009-garage-init-scope-selection.md`

## 交接说明

- `设计真人确认`：本轮 verdict = `需修改`，不进入。
- `hf-design`：父会话应把本 review 记录路径与 2 important + 7 minor 全部回传给负责 design 修订的会话；预计 1 轮定向回修 + 1 轮 review 即可冻结进入 `设计真人确认`。
- `hf-workflow-router`：route / stage / 证据无冲突，不需要 reroute（`reroute_via_router=false`）。
- 不修改 `task-progress.md`、不修改 D009 design 文档、不 git commit / push（由父会话执行）。
- 不进入 `hf-tasks`（design 未通过 approval step 前不得拆任务）。
