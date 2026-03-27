---
name: long-task-work
description: "当存在 feature-list.json 时使用——编排特性走完完整 TDD 流水线、质量门禁与代码评审"
---

# Worker —— 每周期一条特性

通过**每周期实现一条特性**来执行多会话软件项目。每周期严格遵循流水线：Orient → Gate → Plan → TDD → Quality → ST 验收 → 行内检查 → Persist。

**开场声明：**「我正在使用 long-task-work 技能，先完成定向（Orient）。」

**核心原则：** 每个子步骤有独立技能。严格按编排顺序执行。

## 检查清单

**必须**为每一步创建 TodoWrite 任务并按序完成：

### 1. Orient
- 若适用则加载配置值 —— 按 `long-task-guide.md` 激活项目环境；若项目使用文件型配置（如 `.env`），须先 source，确保运行检查前所需环境变量已设置
- 阅读 `task-progress.md` 的 `## Current State` —— 进度统计、最近完成特性、下一条特性
- 阅读 `feature-list.json` —— 注意 `constraints[]`、`assumptions[]`、`required_configs[]`、各特性状态
- 阅读 `long-task-guide.md` —— 项目专属工作流指引
- 阅读 `env-guide.md`（若存在）—— 记录服务名、端口、健康检查 URL；目标特性有服务依赖时**必填**
- **判定服务依赖**：若以下**任一**成立，则该特性有服务依赖：
  1. `required_configs[]` 中含连接串类键（键名含 `URL`、`URI`、`DSN`、`CONNECTION`、`HOST` 或 `PORT` —— 如 `DATABASE_URL`、`REDIS_HOST`）
  2. `dependencies[]` 所含特性的标题涉及数据库搭建、schema 迁移或服务初始化
  3. 设计小节（`{design_section}`）描述对外部服务的交互（DB 查询、对本服务的 HTTP、消息队列等）

  将判定结果（是/否 + 哪些服务）记入 `task-progress.md` 当前特性标题下。该判定驱动 Bootstrap 步骤 2 与 Config Gate 步骤 3。
- 阅读设计文档 **第 1 节**（`docs/plans/*-design.md`）—— 项目概览与全局架构快照
- 运行 `git log --oneline -10` —— 近期提交上下文
- 按优先级再在 `features[]` 中按数组位置选取下一条 `"status": "failing"` 特性（首个符合条件者）—— **跳过 `"deprecated": true` 的特性**
- **依赖满足检查**：选定候选特性后，核验其 `dependencies[]` 中**所有**特性 ID 在 `feature-list.json` 中均为 `"status": "passing"`。若某依赖仍为 `"failing"`：
  - 记录：「Feature #{id} ({title}) skipped — unsatisfied deps: #{dep1}, #{dep2}」
  - 选取下一条符合条件的 `"failing"` 特性（按优先级 + 依赖顺序），且其依赖均已满足
  - 若**没有**任何特性满足全部依赖 → 通过 `AskUserQuestion` 警告用户：「All remaining features have unsatisfied dependencies. Circular or over-constrained dependency graph detected.」→ 由用户选择强制启动哪条特性（覆盖依赖检查）
  - 将跳过特性及原因记入 `task-progress.md`
- 若目标特性为 `"ui": true` 且存在 UCD 文档（`docs/plans/*-ucd.md`），阅读 UCD 风格指南 —— 参照样式 token、组件提示与页面提示，确保前端实现与已批准视觉一致

**文档查找协议（步骤 5、10、11 使用）：**

需要某特性的设计小节或 SRS 需求时，**不要**对特性标题 grep。应：

1. **设计文档**（`docs/plans/*-design.md`）：
   - 阅读设计文档 **第 4 节标题区**（用 Read 工具 offset/limit 扫第 4 节标题 —— 查找匹配 `### 4.N Feature:` 的行）
   - 通过特性标题或 FR-ID 匹配，确定哪段 `### 4.N` 对应目标特性
   - 从 `### 4.N` 读到 `### 4.(N+1)` 之前一行（或第 4 节末尾）的**整段子节** —— 含 Overview、Class Diagram、Sequence Diagram、Flow Diagram、Design Decisions
   - 将全文存为 `{design_section}`，供 Plan（步骤 5）与 ST 验收（步骤 9）使用

2. **SRS 文档**（`docs/plans/*-srs.md`）：
   - 阅读 SRS **第 4 节（功能需求）**标题区，找到匹配目标特性的 `### FR-xxx` 子节
   - 阅读**完整** FR-xxx 子节，含 EARS 陈述、优先级、验收标准、Given/When/Then 场景
   - 存为 `{srs_section}` 供 Plan 使用

3. **UCD 文档**（`docs/plans/*-ucd.md`，仅 `"ui": true` 特性）：
   - 阅读 UCD 目录或节标题
   - 找到引用目标特性 UI 组件或页面的节
   - 阅读**完整相关节**，含样式 token、组件提示、页面提示

**原因：** Grep 只给孤立匹配行，缺少上下文。设计小节含跨多行的类图、时序图、流程图与设计依据 —— 正确实现与行内合规检查都需要这些。

### 2. Bootstrap
- **开发环境就绪**：检查环境是否已就绪
  - 若存在 `init.sh` / `init.ps1` 且环境未就绪：运行一次
  - 若执行了脚本，在 `task-progress.md` 中记录
- **确认测试命令可用**：按 `long-task-guide.md` 激活环境，确认测试/覆盖率/变异命令与技术栈一致；本周期内直接使用（不用封装脚本）
- **服务就绪**（条件化 —— 依 Orient 中的服务依赖判定）：
  - **无服务依赖**：跳过服务启动。Feature-ST（步骤 10）负责验收测试时的服务管理。
  - **有服务依赖**：真实测试（TDD Rule 5a）需要运行中基础设施。确保可用：
    1. 读 `env-guide.md` → 找到「Verify Services Running」健康检查
    2. 运行健康检查。若全部通过 → 在 `task-progress.md` 记录 PID/端口；继续
    3. 若失败 → 按 `env-guide.md`「Start All Services」启动并捕获输出：
       ```bash
       [start command] > /tmp/svc-<slug>-start.log 2>&1 &
       sleep 3
       head -30 /tmp/svc-<slug>-start.log
       ```
    4. 重新跑健康检查 —— 阻塞直至通过
    5. 若启动失败 → 按 `env-guide.md` 诊断；无法解决则通过 `AskUserQuestion` 上报
    6. 在 `task-progress.md` 记录运行中服务、PID、端口
  - Feature-ST（步骤 10）负责重启/清理。此处启动的服务在 TDD 与质量门禁期间保持运行。
- 对已 passing 特性做冒烟测试（按 `long-task-guide.md` 激活环境 → 直接运行测试命令）

### 3. Config Gate
```bash
python scripts/check_configs.py feature-list.json --feature <id>
```
`<id>` 为步骤 1 所选特性 ID。生成的 `check_configs.py` 自动按项目原生格式加载配置。

**若配置缺失 —— 提示文本输入并写入项目配置：**

1. 对每个缺失的 `env` 型配置，用 `AskUserQuestion` 请用户**键入值** —— **不要**提供预设选项按钮。问题中写明配置的 `name`、`description`、`check_hint`。
   - 示例：「Please enter the value for `OPENAI_API_KEY` (OpenAI API key for LLM integration). Hint: Get it from https://platform.openai.com/api-keys」
2. 对每个缺失的 `file` 型配置，请用户提供路径或手动创建文件。
3. 收齐值后，**按项目配置格式保存** env 型配置 —— 见 `long-task-guide.md` 中 `Config Management` 小节（如追加 `.env`、`application.properties`、系统环境变量等）。
4. 重新运行检查确认：
   ```bash
   python scripts/check_configs.py feature-list.json --feature <id>
   ```
5. 确保密钥配置文件已在 `.gitignore` 中（若尚未）。
6. **阻塞直至全部配置通过。**
7. **连通性验证**（仅含服务依赖的特性）：
   配置键通过存在性检查后，验证连接串类配置是否真能连通：
   - 对每个匹配连接串模式的 `env` 型配置（`DATABASE_URL`、`REDIS_URL` 等）：运行 `env-guide.md`「Verify Services Running」中对应健康检查
   - 若健康检查失败：值存在但服务不可达 —— 按上文 Bootstrap 服务就绪协议启动服务
   - **阻塞直至连通性确认** —— 指向死服务的配置在功能上等同缺失

**对有外部依赖的特性，Config Gate 不可跳过。** 若配置缺失：
- **必须**用 `AskUserQuestion` 向用户索取值
- **不得**在配置未齐时进入 TDD
- **不得**对含连接串类 `required_configs[]`（URL、HOST、PORT、DSN、URI、CONNECTION、ENDPOINT）的特性声称「纯函数豁免」
- 质量门禁（Gate 0）将通过 `check_real_tests.py --require-for-deps` 机械强制执行

### 4. Feature Detailed Design
**必选子技能：** 调用 `long-task:long-task-feature-design` 并严格遵循。

Feature Design 技能会派发 SubAgent 产出详细设计文档。主代理**不**阅读设计/SRS/UCD 节或撰写设计文档 —— SubAgent 在独立新上下文中完成并返回结构化摘要。

> **`category: "bugfix"` 特性**：feature-design 压缩。SubAgent 聚焦：(1) 根因文档，(2) 针对性修复思路，(3) 回归测试清单。除非缺陷直接涉及这些表面，否则跳过完整图示。

仅传递路径（SubAgent 自行 Read）：
- 特性对象（紧凑 JSON）
- `quality_gates` 与 `tech_stack`（紧凑 JSON）
- 文件路径 + 节行范围：设计文档（§4.N）、SRS（FR-xxx）、UCD（若 ui:true）
- ATS 文档路径：`docs/plans/*-ats.md`（若存在）—— SubAgent 用 ATS 映射对齐测试清单类别
- feature-list.json 根部的约束与假设
- 输出路径：`docs/features/YYYY-MM-DD-<feature-name>.md`

输出：`docs/features/YYYY-MM-DD-<feature-name>.md`（由 SubAgent 写入）—— 含接口契约、算法伪代码、图示、测试清单、TDD 任务分解。

### 5–7. TDD 周期（红 → 绿 → 重构）
**必选子技能：** 调用 `long-task:long-task-tdd` 并严格遵循。

传递上下文：
- feature-list.json 中当前特性对象
- `quality_gates`、`tech_stack`
- 步骤 4 的特性详细设计（含测试清单表、接口契约、算法伪代码）—— **第 7 节测试清单是 TDD 规约主输入**
- 文档查找协议得到的完整 `{srs_section}` —— TDD Red 与 Feature Design 测试清单并列作为规约输入；`verification_steps` 为可选补充
- 文档查找协议得到的完整 `{design_section}` —— 架构约束与接口契约
- **测试命令**：来自 `long-task-guide.md` —— 直接使用（无封装脚本）

### 8. Quality Gates
**必选子技能：** 调用 `long-task:long-task-quality` 并严格遵循。

Quality 技能派发 SubAgent 执行全部 4 道门禁（Real Test → Coverage → Mutation → Verify）。主代理**不**阅读覆盖率报告、变异输出或测试运行器输出 —— SubAgent 在独立上下文中完成并返回结构化摘要。

最小传递（SubAgent 自行读文件）：
- feature-list.json 中的特性 ID
- `quality_gates` 阈值（紧凑 JSON）
- `tech_stack`（紧凑 JSON）
- 工作目录路径
- 本特性 TDD 期间编写/修改的测试文件路径（用于 mutation_feature 范围）
- 活跃特性数量（feature-list.json 中非弃用特性总数 —— 用于 mutation_full_threshold 决策）

### 9. ST 验收测试用例
**必选子技能：** 调用 `long-task:long-task-feature-st` 并严格遵循。

在 TDD 与质量门禁通过后，对该特性执行黑盒验收测试。技能派发 SubAgent，在其新上下文中阅读 SRS/Design/UCD/ATS，生成符合 ISO/IEC/IEEE 29119 的测试用例文档，执行用例并管理服务生命周期。主代理**不**阅读文档节、用例内容或执行输出 —— 仅接收结构化摘要。

仅传路径（SubAgent 自读内容）：
- 特性 ID 与特性对象（紧凑 JSON）
- `quality_gates`、`tech_stack`（紧凑 JSON）
- 文件路径：设计、SRS、UCD（若 ui:true）、ATS（若存在）、步骤 4 计划文档、`env-guide.md`
- 工作目录路径
- feature-list.json 根部的 `st_case_template_path`、`st_case_example_path`（若设置）

输出：`docs/test-cases/feature-{id}-{slug}.md`（由 SubAgent 写入）

**硬门禁：**
- 任何执行失败（环境或用例）必须通过 `AskUserQuestion` 告知用户
- **不允许绕过** —— 不得以任何理由跳过 ST

### 10. 行内合规检查（无 SubAgent）

直接运行下列机械检查 —— 不派发 SubAgent。  
阅读步骤 4 产出的特性设计文档（`docs/features/YYYY-MM-DD-<feature-name>.md`）。

**a) 接口契约验证（P2 等价）：**  
读特性设计文档 §3 接口契约表。对每个列出的 PUBLIC 方法，在实现文件中 grep，确认存在且签名一致（名、参、返回类型）。标出缺失或不符。

**b) 测试清单 ↔ 测试文件交叉检查（T2 等价）：**  
读 §7 测试清单。对每一行，确认对应测试函数存在于测试文件：
```bash
grep -q "{test_function_name}" {test_file}
```
若找不到，搜索相似名并修正 ST 文档追溯矩阵引用。

**c) 设计依赖版本（D3 等价）：**  
若 §3 或 §5 指定第三方库版本，抽查 `requirements.txt` / `package.json` / `pom.xml` 是否一致。标出不一致。

**d) UCD 抽查（U1 等价，仅 ui:true）：**  
在 CSS/样式文件中 grep 硬编码色值是否落在 UCD 调色板 token 外。

**e) ST 文档完整性：**  
确认 Feature-ST（步骤 9）中 `validate_st_cases.py` 已通过。  
无需再验 —— Feature-ST 步骤 5b + 6 已覆盖 T1。

若全部通过 → 进入 Persist。  
若任一项失败 → 行内修复并重验。不派发 SubAgent。

记入 `task-progress.md`：
```
- Inline Check: PASS (P2: N/N methods verified, T2: N/N tests found, D3: OK)
```

### 11. Persist
- Git commit（含实现、测试、**测试用例文档**）
  > **`category: "bugfix"` 特性**：提交前缀用 `"fix:"` 而非 `"feat:"`。  
  > 格式：`fix: <feature title without the "Fix: " prefix> (#<fixed_feature_id>)`
- 更新 `RELEASE_NOTES.md`（Keep a Changelog）
  > **`category: "bugfix"` 特性**：条目写在 `### Fixed`（非 `### Added`）：  
  > `- [<bug_severity>] <title without "Fix: "> (fixes #<fixed_feature_id>) — <root_cause one-line>`
- 更新 `task-progress.md`：
  - 更新 `## Current State`：进度（X/Y passing）、最近完成特性（#id 标题、日期）、下一条（#id 标题）
  - 在日志分隔符下追加会话条目；格式：
    ```
    ### Feature #id: Title — PASS
    - Completed: YYYY-MM-DD
    - TDD: green ✓
    - Quality Gates: N% line, N% branch, N% mutation
    - Feature-ST: N cases, all PASS
    - Inline Check: PASS
    - Git: <sha> feat: title
    #### Risks                        ← 仅在有风险报告时包含
    - ⚠ [Mutant] file:line — reason
    - ⚠ [Coverage] metric N% — thin margin / uncovered boundary
    - ⚠ [Dependency] lib==ver — known patch / breaking change pending
    ```
  - **风险汇总**：步骤 8（Quality）与步骤 9（Feature-ST）完成后，将其 `### Risks` 表各行合并为列表；仅当非空时追加为 `#### Risks` 要点
- 在 `feature-list.json` 将特性标为 `"status": "passing"`
- 在特性对象上设置 `"st_case_path"`、`"st_case_count"`
- 校验：
  ```bash
  python scripts/validate_features.py feature-list.json
  ```
- 再次 git commit（进度类文件）

### 11.5 会话反思（条件）

若 `feature-list.json` 中 `retro_authorized` 为 `true`：
1. 阅读 `skills/long-task-retrospective/prompts/reflection-prompt.md`
2. 填充模板变量：特性 ID/标题、阶段、本会话 `task-progress.md` 条目、用户通过 `AskUserQuestion` 纠正技能输出的交互
3. 通过 `Agent(run_in_background=true)` 派发 Reflection SubAgent —— **不要**等待其结束
4. 立即进入「结束会话」

若 `retro_authorized` 缺失或为 `false` → 完全跳过（无输出、不派发）。

### 12. 结束会话
- 停止本周期内你**直接**启动的服务（步骤 10 ST 验收期间启动的服务由 `long-task-feature-st` 停止）
- 输出简明完成摘要：
  > **Feature #\<id\> (\<title\>) — DONE**
  >
  > Next: Feature #\<next_id\> (\<next_title\>)
- 若**无剩余 failing 的非弃用特性**：
  > All active features passing — next session begins System Testing.
- 结束会话 —— **切勿**回到步骤 1 循环

多特性自动化由外部脚本 `scripts/auto_loop.py` 处理 —— 每次调用为新上下文。

## 关键规则

- **每会话一条特性** —— 完成一条特性后结束会话；多特性由外部 `scripts/auto_loop.py` 处理
- **严格步骤顺序** —— 不跳步、不重排
- **子技能不可协商** —— ST 测试用例、TDD、Quality 必须通过 Skill 工具调用
- **规划前须过配置门禁** —— 必选配置缺失时不得规划或编码
- **无新证据不得标 passing** —— 先跑测试、读输出，再标记
- **仅系统化调试** —— 出错时阅读 `references/systematic-debugging.md`；追踪根因，禁止猜谜式修复
- **每次 git commit 后更新 RELEASE_NOTES.md**
- **结束前务必 commit + 更新进度** —— 弥合上下文断层
- **不留损坏代码** —— 未完成则回滚

## 危险信号

| 自我合理化 | 正确做法 |
|---|---|
| "I'll mock that config later" | 运行 Config Gate。需要真实配置。 |
| "This feature is trivial, skip test cases" | 调用 long-task-feature-st。每条特性都要。 |
| "This feature is trivial, skip TDD" | 调用 long-task-tdd。每条特性都要。 |
| "Tests pass, mark it done" | 先调用 long-task-quality。 |
| "Coverage looks close enough" | 阈值为硬门禁。运行工具。 |
| "Let me just try this quick fix" | 先系统化调试。 |
| "I'll generate examples during Worker" | 示例在 ST 后由 long-task-finalize 生成。 |
| "I'll update release notes at the end" | 每次 commit 后更新。 |
| "Mutation score is probably OK" | 运行变异测试并阅读报告。 |
| "The UI looks correct to me" | 运行自动化检测 + EXPECT/REJECT。 |
| "ST test case failed but the code is fine" | 上报用户。不可绕过。修代码或用 `long-task-increment` 改测试用例。 |
| "Port is busy, let me kill manually" | 用 env-guide.md「Stop All Services」（端口兜底）结束进程，再按 Start 重启 —— 若命令需修正则更新 env-guide.md。 |
| "Environment is down, skip ST cases" | **阻塞**，非跳过。修复环境或询问用户。 |
| "This deprecated feature still needs work" | 跳过。弃用特性排除在外。 |
| "Backend isn't ready but I'll mock it for now" | 依赖检查有其原因。先开发后端相关特性。 |
| "I'll skip the dependency check this once" | 永不跳过。重排特性使依赖先满足。 |

## 出错时

遵循系统化调试流程 —— **禁止猜谜式修复**：
1. 收集证据（错误信息、堆栈、git diff）
2. 复现问题
3. 追踪根因（详见 `references/systematic-debugging.md`）
4. 为缺陷写失败测试
5. 单次针对性修复
6. 尝试 3 次仍失败 → 上报用户

## 集成

**由谁调用：** using-long-task（当存在 feature-list.json）或 long-task-init（步骤 16）  
**按严格顺序调用：**
1. `long-task:long-task-tdd`（步骤 5–7）—— TDD 红-绿-重构
2. `long-task:long-task-quality`（步骤 8）—— 覆盖率 + 变异
3. `long-task:long-task-feature-st`（步骤 9）—— 黑盒特性验收测试（ISO/IEC/IEEE 29119，自管理生命周期）  
**读写：** feature-list.json、task-progress.md（含 `## Current State`）、RELEASE_NOTES.md  
**按需 Read（Read 工具，非 Skill）：** `references/systematic-debugging.md`
