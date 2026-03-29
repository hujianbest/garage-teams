# Long-Task Agent 架构

## 核心概念

长时任务会超出单个上下文窗口。做法是：将工作拆为 **需求阶段**（SRS）、**UCD 阶段**（UI 项目）、**设计阶段**、**ATS 阶段**（验收测试策略）、**初始化会话**（运行一次）与多个 **Worker 会话**（迭代运行），通过磁盘上的持久化产物串联。

### ATS 的下游影响

ATS 文档（`docs/plans/*-ats.md`）将每条 SRS 需求映射到带必选测试类别（`FUNC, BNDRY, SEC, UI, PERF`）的验收场景，并向下游流动：

- **SRS → ATS**：SRS 中编写的验收标准（Given/When/Then）驱动 ATS 场景推导。结构良好、含明确边界与错误用例的验收标准能产生更强的 ATS 覆盖。
- **UCD → ATS**：UCD 中定义的 UI 组件与页面在 ATS 阶段对应分配 UI 测试类别。含交互状态与可访问性约束的组件会成为 ATS 测试场景。
- **ATS → Init**：Init 使用 `srs_trace` → ATS 类别查找来设置 `ui` 标志并指导特性分解。
- **ATS → Feature-Design**：测试清单（§7）必须覆盖该特性相关需求在 ATS 中要求的全部主类别。
- **ATS → Feature-ST**：硬门禁——ST 测试用例必须覆盖 ATS 要求的类别。
- **ATS → System-ST**：硬门禁——`check_ats_coverage.py --strict` 必须退出码为 0。

## 持久化产物

### 1. `task-progress.md`

跨会话补齐上下文的会话日志。每个 worker 会话追加一条记录。

```markdown
# Task Progress Log

## Project: [name]
Created: [date]

---

### Session 1 — [date/time]
**Focus**: User authentication API endpoints
**Completed**:
- POST /auth/login with JWT
- POST /auth/register with validation
- Unit tests for auth module (12/12 passing)
**Issues**: None
**Next Priority**: Password reset flow (feature #5)
**Git Commits**: a1b2c3d, e4f5g6h
```

### 2. `feature-list.json`

结构化任务清单。JSON 格式降低模型意外破坏列表的风险。同时承载源自 SRS 的全局上下文（`constraints`、`assumptions`），供 Worker 在每个 Orient 阶段读取。

```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "constraints": [
    "Must run offline — no external API calls permitted",
    "Python 3.8+ only — no 3.10+ match syntax"
  ],
  "assumptions": [
    "JWT validation handled by API Gateway; business layer must NOT re-validate",
    "Input data is pre-sanitised before reaching this service"
  ],
  "features": [
    {
      "id": 1,
      "category": "core",
      "title": "User login with JWT",
      "description": "POST /auth/login returns JWT token on valid credentials",
      "priority": "high",
      "status": "passing",
      "srs_trace": ["FR-001"],
      "verification_steps": [
        "Send POST with valid credentials, verify 200 + token",
        "Send POST with invalid credentials, verify 401",
        "Verify token contains correct claims"
      ],
      "dependencies": []
    },
    {
      "id": 2,
      "category": "core",
      "title": "User registration",
      "description": "POST /auth/register creates new user account",
      "priority": "high",
      "status": "failing",
      "srs_trace": ["FR-002"],
      "verification_steps": [
        "Send POST with valid data, verify 201",
        "Send POST with duplicate email, verify 409",
        "Verify password is hashed in DB"
      ],
      "dependencies": []
    }
  ]
}
```

**规则**：
- 状态只能是 `"failing"` 或 `"passing"` —— 永远不要 `"partial"` 或 `"in-progress"`
- 每条特性必须 `srs_trace` —— 映射到 SRS 需求 ID，供 ATS 类别查找
- `verification_steps` 可选 —— 若存在，提供补充测试上下文
- 标记为 `"passing"` 的特性必须在会话开始时重新核验

### 3. `init.sh` / `init.ps1`

环境启动脚本。**由 LLM 在 Initializer 阶段**依据设计文档技术栈生成——不由 `init_project.py` 硬编码。必须包含真实可执行命令（非注释占位）。

须支持项目实际的环境管理器（conda/miniconda/mamba、venv、poetry、uv、nvm、fnm、sdkman、docker 等）。参见 `skills/long-task-init/references/init-script-recipes.md` 中各工具模板。

**要求**：幂等、跨平台（`init.sh` + `init.ps1`）、快速失败、版本钉死、无交互提示。

Python + conda 示例：
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_NAME="my-project"
PYTHON_VERSION="3.11"

# Detect conda/mamba
if command -v mamba &>/dev/null; then CONDA_CMD="mamba"
elif command -v conda &>/dev/null; then CONDA_CMD="conda"
else echo "ERROR: conda not found. Install Miniconda."; exit 1; fi

eval "$($CONDA_CMD shell.bash hook 2>/dev/null || true)"

# Create env if not exists (idempotent)
if ! conda env list | grep -q "^${ENV_NAME} "; then
    $CONDA_CMD create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
fi
conda activate "$ENV_NAME"

# Install deps
pip install -r requirements.txt
pip install pytest pytest-cov mutmut

echo "=== Environment Check ==="
echo "python: $(python --version) | pytest: $(pytest --version 2>&1 | head -1)"
echo "Environment ready. Run: conda activate ${ENV_NAME}"
```

Python + venv 示例：
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ ! -d ".venv" ] && python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Environment ready. Run: source .venv/bin/activate"
```

### 4. `RELEASE_NOTES.md`

跟踪所有用户可见变更的持续更新文档。在**每次 git commit 后**更新，确保发布说明与代码同步。

```markdown
# Release Notes

## [Unreleased]

### Added
- User login with JWT authentication (#1)
- User registration with email validation (#2)

### Changed
- (none yet)

### Fixed
- (none yet)

---

## [0.1.0] — 2025-01-15
### Added
- Initial project scaffold
```

**规则**：
- 使用 [Keep a Changelog](https://keepachangelog.com/) 格式：Added、Changed、Deprecated、Removed、Fixed、Security
- 每条记录引用 `feature-list.json` 中的特性 ID
- 达到里程碑时将条目从 `[Unreleased]` 移到带版本的小节
- 每次 git commit 后立即更新——不要推迟到会话结束

### 5. `examples/` 目录

面向外部开发者与 AI 编程助手的基于场景的使用示例。在系统测试 Go 判定后，由 `long-task-finalize` 元技能与 `example-generator` SubAgent 一次性批量生成。

```
examples/
├── README.md                    # Index of all examples with descriptions
├── 01-user-login.py             # Feature #1: login flow demo
├── 02-user-registration.py      # Feature #2: registration demo
├── 05-password-reset.sh         # Feature #5: curl commands for password reset API
└── ui/
    └── 03-dashboard-tour.md     # Feature #3: step-by-step UI walkthrough
```

**规则**：
- 以场景为中心，而非以特性为中心——一个示例可跨多个特性
- 示例必须可运行或可跟做——不能只是代码片段
- 命名模式：`<NN>-<scenario-name>.<ext>`（例如 `01-quick-start.py`）
- `examples/README.md` 索引列出全部示例及前置条件与运行命令
- 跳过不可对外展示的特性（基础设施、内部逻辑、配置脚手架）
- 完整生成规则见 `agents/example-generator.md`

### 6. Git 历史

- 每个会话使用描述性信息提交
- 便于回滚破坏性变更
- 为后续会话通过 `git log` 提供上下文

### 7. `long-task-guide.md`

**由 LLM 在 Initializer 阶段**根据项目技术栈与特征生成的 Worker 会话指南。包含每个上下文周期的完整工作流。位于项目根目录。由 `validate_guide.py` 校验结构完整性。

## 需求阶段（Phase 0a）

在**设计阶段之前**运行。产出与 ISO/IEC/IEEE 29148 对齐的结构化 SRS。

**硬门禁**：在 SRS 获批前，不得进行设计、特性分解、脚手架或编码。

1. **探索上下文** —— 阅读需求文档、现有代码；识别 SRS 模板
2. **结构化获取** —— 一次只问一个澄清问题；用 8 项质量属性（正确、无歧义、完整、一致、可排序、可验证、可修改、可追溯）审视每条需求
3. **需求分类** —— 功能（FR-xxx）/ NFR（NFR-xxx）/ 约束（CON-xxx）/ 假设（ASM-xxx）/ 接口（IFR-xxx）/ 排除（EXC-xxx）
4. **编写需求** —— 应用 EARS 模板，分配唯一 ID，编写 Given/When/Then 验收标准
5. **校验 SRS** —— 反模式检测（含糊词、复合需求、设计泄漏、不可测 NFR），完整性交叉检查
6. **按节获批** —— 向用户展示 SRS，逐节获得批准
7. **保存 SRS 文档** —— `docs/plans/YYYY-MM-DD-<topic>-srs.md`

## 设计阶段（Phase 0b）

在 SRS 获批后、Initializer **之前**运行。以 SRS 为输入，聚焦 HOW。

**硬门禁**：在设计获批前，不得进行特性分解、脚手架或编码。

1. **阅读 SRS** —— 提取设计驱动因素（NFR 阈值、约束、接口需求）
2. **探索技术上下文** —— 现有代码、框架、部署环境
3. **提出 2–3 种方案** —— 明确权衡，对照 SRS 约束与 NFR 评估
4. **按节获批** —— 架构、数据模型、API、UI、测试、部署
5. **保存设计文档** —— `docs/plans/YYYY-MM-DD-<topic>-design.md`（若提供则使用自定义模板）

## Initializer 会话工作流

Initializer 在 SRS 与设计**均**获批后**运行一次**。读取**两份**已批准文档：
- **SRS**（`docs/plans/*-srs.md`）—— 功能需求、NFR、约束、假设、术语表、用户画像
- **Design**（`docs/plans/*-design.md`）—— 技术栈、架构、测试策略

其职责：

1. **阅读已批准 SRS + 设计文档** —— 自 `docs/plans/`
2. **运行 `init_project.py`** —— 脚手架确定性产物：`feature-list.json`、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`scripts/`、`docs/plans/`
3. **LLM 生成 `long-task-guide.md`** —— 基于 SKILL.md + references + 设计文档的项目定制 Worker 指南；仅包含项目语言相关命令；由 `validate_guide.py` 校验
4. **LLM 生成 `init.sh`/`init.ps1`** —— 基于设计文档技术栈的真实可运行引导脚本；须支持项目环境管理器（conda/miniconda/mamba、venv、poetry、uv、nvm、fnm、sdkman、docker 等）；参见 `skills/long-task-init/references/init-script-recipes.md`；须幂等且跨平台
5. **填充 `feature-list.json`** —— 自 SRS：`constraints[]`（CON-xxx）、`assumptions[]`（ASM-xxx），NFR-xxx → 非功能特性，FR-xxx → 功能特性并带 `srs_trace`（需求 ID）及可选 `verification_steps`；自设计：外部依赖的 `required_configs`
7. **搭建项目骨架** —— 目录结构、配置文件、package.json / pyproject.toml 等（依设计文档架构）
8. **初始 git commit** —— 建立基线
9. **校验环境** —— 运行 init 脚本，确认基本可用

### 产物生成：脚本 vs LLM

| 产物 | 生成方 | 来源文档 | 理由 |
|----------|-------------|-----------------|-----------|
| `feature-list.json`（schema） | 脚本 | — | 校验工具需要确定性结构 |
| `task-progress.md` | 脚本 | — | 通用格式模板 |
| `RELEASE_NOTES.md` | 脚本 | — | 通用 Keep a Changelog 模板 |
| `examples/README.md` | 脚本 | — | 通用格式模板 |
| `long-task-guide.md` | **LLM** | Design | 项目定制；仅相关语言/工具；`validate_guide.py` 校验 |
| `init.sh` / `init.ps1` | **LLM** | Design | 完全项目相关；通用占位无用 |
| `features[]` 内容 | **LLM** | **SRS** | FR-xxx → 带 `srs_trace` 与可选 `verification_steps` 的特性 |
| `constraints[]` 内容 | **LLM** | **SRS** | 自 SRS「约束」节（CON-xxx）抽取 |
| `assumptions[]` 内容 | **LLM** | **SRS** | 自 SRS「假设」节（ASM-xxx）抽取 |
| `required_configs[]` | **LLM** | **SRS** + Design | 接口需求（IFR-xxx）+ 设计集成点 |

## Worker 会话工作流（上下文周期）

每个 worker 周期严格按下列顺序执行。

### Phase 1: Orient（理解当前状态）
1. `pwd` —— 确认工作目录
2. 阅读 `task-progress.md` —— 了解此前进展
3. 阅读 `feature-list.json` —— 找下一优先级的 failing 特性；注意根级 `constraints[]`、`assumptions[]`
4. `git log --oneline -20` —— 近期提交
5. `git diff HEAD~3` —— 如需则查看近期变更
6. 阅读设计文档 **第 1 节**（项目概览）—— 全局架构快照

### Phase 2: Bootstrap（恢复环境）
6. 运行 `init.sh` / `init.ps1` —— 启动开发服务器/服务
7. 运行冒烟测试 —— 确认此前通过的特性仍可用

### Phase 2.5: Config Gate（校验必选配置）
7a. 自 `feature-list.json` 读取 `required_configs`  
7b. 过滤出 `required_by` 含目标特性 ID 的配置项  
7c. `env` 类型：检查环境变量已设置且非空  
7d. `file` 类型：检查 `path` 文件存在且非空  
7e. 若有缺失：报告 name、description、check_hint；通过 `AskUserQuestion` 询问用户；用户响应后重新检查  
7f. 仅当全部必选配置通过后才进入 Phase 3  
7g. 快捷：`python scripts/check_configs.py feature-list.json --feature <id>`

### Phase 3: TDD Red —— 先写失败测试
8. 选取依赖均已 `"passing"` 的最高优先级 `"failing"` 特性  
9. 编写覆盖 Feature Design 测试清单（§7）的单元测试 —— 测试**必须失败**（尚无实现）  
   - 遵循测试场景规则（见 [test-scenario-rules.md](test-scenario-rules.md)）：  
     - 含主路径、错误处理、边界、安全场景  
     - 负例比例 ≥ 40%  
     - 低价值断言比例 ≤ 20%  
     - 对每条测试做「错误实现」挑战  
10. 若含 UI：编写 Chrome DevTools MCP 功能测试（快照、点击、填充、截图断言）—— 测试**必须失败**  
    - 在 `[devtools]` 验证步骤中使用 EXPECT/REJECT 格式  
    - 通过 `evaluate_script()` 运行自动化 UI 错误检测脚本  
    - 通过 `list_console_messages(types=["error"])` 做控制台错误门禁  
    - 完整规范见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)

### Phase 4: TDD Green —— 实现至测试通过
11. 编写最少代码使**全部**测试通过（单元 + 功能）  
12. 运行完整测试套件 —— 确认新增测试全绿、无回归

### Phase 4.5: Coverage Gate —— 校验测试覆盖率
12a. 按项目语言运行覆盖率工具（见 [coverage-and-mutation.md](coverage-and-mutation.md)）  
12b. 检查：行覆盖 ≥ `quality_gates.line_coverage_min`（默认 90%），分支覆盖 ≥ `quality_gates.branch_coverage_min`（默认 80%）  
12c. 若**低于**阈值：补充测试（回到 Phase 3 新增用例）  
12d. 将覆盖率报告输出记录为证据

### Phase 5: TDD Refactor —— 整理
13. 在保持全部测试绿色的前提下重构  
14. 再次运行验证 —— **仅当**全部测试通过后，才将 `feature-list.json` 中特性标为 `"passing"`  
15. **验证强制执行**：执行每条 `verification_step`，阅读**完整**输出，确认全部绿色。若出现「应该过了」「大概能用」式想法 —— **停**并重跑。见 [verification-enforcement.md](verification-enforcement.md)。

### Phase 5.5m: Mutation Gate —— 校验测试有效性
15a. **范围决策**：若活跃特性数 ≤ `quality_gates.mutation_full_threshold`（默认 100）→ 运行 `mutation_full`；否则 → 运行 `mutation_feature`（变更文件 + 该特性测试）  
15b. 检查：变异分数 ≥ `quality_gates.mutation_score_min`（默认 80%）  
15c. 若**低于**阈值：强化断言以杀死幸存变异体（回到 Phase 3）  
15d. 将变异报告输出记录为证据  
15e. 完整变异测试（全部源文件、全部测试）在 ST 阶段（Step 3b）运行 —— 无需每特性里程碑再跑全量

### Phase 5.5: 行内合规检查
16. 运行机械合规检查（接口契约校验、测试清单交叉检查、依赖版本抽查、UI 特性的 UCD token grep）  
17. 就地修复发现项 —— 不派发 SubAgent

### Phase 6: Persist（为下一会话保存状态）
15. `git add` + `git commit`，信息描述清晰  
16. 更新 `RELEASE_NOTES.md` —— 在 `[Unreleased]` 下增加条目（特性标题、ID、变更类型）  
17. 向 `task-progress.md` 追加会话条目  
18. 校验：`python scripts/validate_features.py feature-list.json`  
19. 再次提交更新后的 `task-progress.md`、`feature-list.json`、`RELEASE_NOTES.md`

### Phase 7: 继续
20. 若**全部**特性为 `"passing"` → 宣布项目完成并停止  
21. 否则告知用户完成了哪条特性、下一条是什么  
22. 若上下文预算仍有余量，对下一条特性回到 Phase 1  
23. 若上下文耗尽，结束会话

**关键规则**：每周期一条特性。若完成一条后仍有上下文，选取下一条。绝不留存损坏代码。

## 上下文延续流

```
Requirements → SRS approved → Design → design approved → Initializer → scaffold → populate features → commit → begin first Worker cycle
                                                                                                                        ↓
                                                                                                                ┌─── Worker Cycle ───┐
                                                                                                                │ Orient             │
                                                                                                                │ Bootstrap          │
                                                                                                                │ Implement (1 feat) │
                                                                                                                │ Persist + commit   │
                                                                                                                │ Continue / End     │
                                                                                                                └────────┬───────────┘
                                                                                                                         │
                                                                                                                (repeat until all passing)
```

## 应避免的反模式

| 反模式 | 为何失败 | 正确做法 |
|---|---|---|
| 并行推进多条特性 | 实现中途上下文耗尽、级联失败 | 每周期一条特性 |
| 未充分测试即宣称完成 | 表面完成实际易坏 | 用真实测试验证每条特性 |
| 先写代码再测（跳过 TDD Red） | 测试易沦为测实现而非行为；遗漏边界 | 始终先写失败测试再实现 |
| UI 跳过 Chrome DevTools 功能测试 | UI 可能能渲染但对用户不可用 | 每条 UI 特性（ui=true）需要 `[devtools]` 验证步骤；规划前跑 DevTools Gate |
| 不更新 RELEASE_NOTES.md | 发布说明与实际漂移；后期补成本高 | 每次 git commit 后更新 |
| 面向用户特性跳过示例 | 用户不知如何集成；降低项目价值 | 每条面向用户特性增加可运行示例 |
| 删除 srs_trace 条目 | 破坏 ATS 类别可追溯性 | srs_trace 映射特性到 SRS 需求 —— 保持完整 |
| 跳过覆盖率检查 | 测试可能整段路径未覆盖 | 每次 TDD Green 后跑覆盖率 |
| 跳过变异测试 | 测试可能绿但抓不住真实缺陷 | 每次 TDD Refactor 后跑变异 |
| 用无断言测试刷覆盖率 | 覆盖率高但测试无用 | 变异测试可暴露；加强断言 |
| 跳过进度文件更新 | 下一会话浪费 token 重发现状态 | 结束前务必更新 |
| 会话结束不提交 | 工作可能丢失，下一会话无法 diff | 始终提交可工作代码 |
| 用 Markdown 做特性列表 | 模型易破坏/重排列表 | 结构化数据用 JSON |
| 应真实存在的配置却 mock | 测试通过真实环境失败 | 在 `required_configs` 声明，规划前过门禁 |
| 特性工作前跳过配置检查 | 规划/TDD 一圈后发现缺配置 | 有外部依赖的特性始终运行 Config Gate |
| 跳过需求阶段 | 需求不完整/有歧义导致返工 | 先跑需求获取，产出获批 SRS |
| 跳过设计阶段 | 临时设计不一致、返工 | SRS 后跑设计阶段并获批 |
| 猜谜式调试 | 随机修复耗时且可能引入新缺陷 | 系统化调试 —— 追踪根因。见 [systematic-debugging.md](../../long-task-work/references/systematic-debugging.md) |
| 无证据声称「能用」 | 未验证的断言导致虚假信心 | 标 passing 前展示真实测试输出。见 [verification-enforcement.md](verification-enforcement.md) |
| 接受低价值断言 | None/isinstance/import 类检查几乎抓不到 bug | 强制执行低价值断言比例 ≤ 20%。见 [testing-anti-patterns.md](../../long-task-tdd/testing-anti-patterns.md) #14 |
| UI 测试缺少 REJECT 子句 | LLM 只确认正向预期，漏掉明显 UI 错误 | 所有 `[devtools]` 步骤要求 EXPECT/REJECT 格式。见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md) |

## 验证策略

### 全部特性（强制 TDD）：
1. **Red**：先写失败测试 —— 测试定义预期行为  
   - 遵循测试场景规则：类别覆盖、负例比例 ≥ 40%、低价值断言 ≤ 20%  
2. **Green**：最少实现使测试通过  
3. **Refactor**：保持绿色前提下整理  
4. **质量门禁**：覆盖率门禁（行 ≥90%、分支 ≥80%）+ 变异门禁（分数 ≥80%）客观验证测试质量

### API / 后端特性：
- 业务逻辑单元测试（pytest、jest 等）
- 集成测试：真实 HTTP 请求并检查响应
- 适用时校验数据库状态

### UI / 前端特性（需要 Chrome DevTools MCP）：
- 组件逻辑单元测试
- **经 Chrome DevTools MCP 的功能测试**（三层错误检测）：  
  - **Layer 1**：`evaluate_script()` 自动化错误检测脚本 —— 发现错误即 **硬失败**  
  - **Layer 2**：验证步骤中 EXPECT/REJECT 格式 —— 强制找错  
  - **Layer 3**：`list_console_messages(types=["error"])` 控制台错误门禁 —— 有错误即 **硬失败**  
  - 完整规范见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)  
- 测试流：navigate → wait → error detection → snapshot → EXPECT/REJECT → interact → error detection → snapshot → console check

### 全部特性（强制覆盖率与变异）：
- **Coverage**：运行语言专属覆盖率工具，验证行/分支阈值  
- **Mutation**：大项目跑特性范围变异，小项目（活跃特性 ≤ `mutation_full_threshold`）跑全量变异，验证变异分数阈值  
- 各语言工具与命令见 [coverage-and-mutation.md](coverage-and-mutation.md)

### 数据 / 管道特性：
- 用样本数据运行并校验输出  
- 显式检查边界情况  
- 将输出与预期结果对比

## TDD 工作流细部

```
┌─── Config Gate ──────────┐
│ 0a. Read required_configs │
│ 0b. Check env/file        │
│ 0c. If missing → prompt   │
│     user, block           │
└──────────┬───────────────┘
           ↓
┌─── DevTools Gate ────────┐
│ 0d. If ui=true:           │
│     check_devtools.py     │
│ 0e. If not detected →     │
│     prompt user, block    │
└──────────┬───────────────┘
           ↓
┌─── TDD Red ─────────────┐
│ 1. Read feature spec     │
│ 2. Write unit tests      │
│    (scenario rules:      │
│     40% negative,        │
│     ≤20% low-value)      │
│ 3. Write [devtools]      │
│    tests (if ui=true)    │
│    (EXPECT/REJECT +      │
│     error detection)     │
│ 4. Run tests → ALL FAIL  │
└──────────┬───────────────┘
           ↓
┌─── TDD Green ───────────┐
│ 5. Write minimal code    │
│ 6. Run tests → ALL PASS  │
└──────────┬───────────────┘
           ↓
┌─── Coverage Gate ────────┐
│ 7. Run coverage tool     │
│ 8. Line % >= threshold?  │
│    Branch % >= threshold │
│ 9. If below → more tests │
└──────────┬───────────────┘
           ↓
┌─── TDD Refactor ────────┐
│ 10. Clean up code        │
│ 11. Run tests → STILL    │
│     ALL PASS             │
└──────────┬───────────────┘
           ↓
┌─── Mutation Gate ────────┐
│ 12. Run mutation tool    │
│     (incremental)        │
│ 13. Score >= threshold?  │
│ 14. If below → improve   │
│     assertions           │
└──────────┬───────────────┘
           ↓
┌─── Verify & Mark ────────┐
│ 15. All evidence recorded │
│ 16. Mark "passing"        │
└───────────────────────────┘
```

### Chrome DevTools MCP 功能测试模式

**适用于**：`feature-list.json` 中 `"ui": true` 的特性。

**DevTools Gate**：规划 UI 特性前运行 `check_devtools.py` 校验 MCP 可用性：
```
python scripts/check_devtools.py feature-list.json --feature <id>
```

**`[devtools]` 验证步骤格式**：UI 特性可选地在 `verification_steps` 中包含以 `[devtools]` 开头的条目，使用 **EXPECT/REJECT 格式**（ST 测试用例经 `srs_trace` 从 SRS 验收标准推导 UI 场景）：
- `[devtools] <page-path> | EXPECT: <positive criteria> | REJECT: <negative criteria>`
- **EXPECT**：必须存在的元素、文本或状态
- **REJECT**：必须**不**存在的条件（强制找错行为）
- 两子句均必填 —— 细节见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)
- 示例：`"[devtools] /login | EXPECT: email input, password input, submit button | REJECT: placeholder 'TODO', overlapping elements, console errors"`

每条 `[devtools]` 步骤的**测试序列**：
```
1. Navigate to relevant page:      navigate_page(url)  (use ui_entry if set)
2. Wait for page load:             wait_for(expected_text)
3. Run automated error detection:  evaluate_script(ui_error_detector)  ← HARD FAIL if count > 0
4. Capture initial state:          take_snapshot()
5. Verify EXPECT criteria:         check uid/text presence in snapshot
6. Verify REJECT criteria:         confirm REJECT conditions are NOT present
7. Perform user action:            click(uid) / fill(uid, value)
8. Wait for response:              wait_for(text)
9. Run error detection again:      evaluate_script(ui_error_detector)  ← HARD FAIL if count > 0
10. Capture result state:          take_snapshot() / take_screenshot()
11. Assert expected outcome:       verify EXPECT elements, text, or visual state
12. Check for console errors:      list_console_messages(types=["error"])  ← HARD FAIL if count > 0
```

自动化检测脚本与三层检测模型见 [ui-error-detection.md](../../long-task-tdd/references/ui-error-detection.md)。

## 多语言工具速查

各语言的覆盖率与变异命令。完整配置食谱见 [coverage-and-mutation.md](coverage-and-mutation.md)。

| 语言 | 覆盖率命令 | 变异命令（按特性） | 变异命令（全量） |
|----------|-----------------|---------------------------|------------------------|
| Python | `pytest --cov=src --cov-branch --cov-report=term-missing` | `mutmut run --paths-to-mutate=<files> --runner='<runner> <test-files>'` | `mutmut run` |
| Java | `mvn test jacoco:report` | `mvn pitest:mutationCoverage -DtargetClasses=<classes> -DtargetTests=<test-classes>` | `mvn pitest:mutationCoverage` |
| TypeScript | `npx c8 --branches --reporter=text npm test` | `npx stryker run --mutate='<files>' --coverageAnalysis perTest` | `npx stryker run` |
| C/C++ | `gcov -b src/*.c && lcov --capture -d . -o cov.info` | `mull-runner <feature-test-binary> --filters=<files>` | `mull-runner <test-binary>` |

## 发布说明维护

### 何时更新 `RELEASE_NOTES.md`：
- **每次**改变功能的 git commit 之后  
- 结束会话前（Persist 阶段的一部分）

### 格式（Keep a Changelog）：
```markdown
## [Unreleased]

### Added
- Feature description (feature #ID)

### Changed
- What changed and why (feature #ID)

### Fixed
- Bug description (feature #ID)
```

### 类别：
- **Added**：新功能  
- **Changed**：既有功能变更  
- **Deprecated**：即将移除  
- **Removed**：已移除  
- **Fixed**：缺陷修复  
- **Security**：安全漏洞修复  

## 示例创建

### 目的
示例作为**外部开发者与 AI Code Agents** 的使用文档——展示如何集成与使用项目。ST 之后由 `long-task-finalize` 元技能通过 `example-generator` SubAgent 生成（见 `agents/example-generator.md`）。

### 设计原则
- **以场景为中心，非以特性为中心**——一个示例可跨多条特性；按使用场景分组  
- **精简要**——重质不重量；多数项目 3–8 个示例  
- **跳过不可对外展示的特性**——基础设施、内部逻辑、配置脚手架无对外示例  
- **可运行或可跟做**——代码示例须能执行；UI 示例须为分步导览  

### 按项目规模的目标示例数

| 项目规模 | 特性数 | 目标示例数 |
|---|---|---|
| Tiny (1-5) | 1-5 | 1-2 |
| Small (5-15) | 5-15 | 2-4 |
| Medium (15-50) | 15-50 | 4-6 |
| Large (50+) | 50+ | 6-8 |

### 按场景类型的示例

| 场景类型 | 格式 | 内容 |
|---|---|---|
| **API usage** | `.py` / `.sh` / `.js` script | 初始化客户端、用样例数据调用端点并打印响应 |
| **Library usage** | `.py` / `.js` / `.ts` code | 导入模块并用样例数据演示关键函数 |
| **CLI usage** | `.sh` / `.ps1` script | 运行命令，并在注释中给出预期输出 |
| **UI workflow** | `.md` walkthrough | 按步骤说明操作流程与动作描述 |
| **Integration** | `.py` / `.js` script | 跨多个子系统的端到端工作流 |

### 示例目录结构
```
examples/
├── README.md                           # 索引：场景说明 + 运行方式
├── 01-quick-start.py                   # 基础使用流程
├── 02-data-import.sh                   # 数据导入流程
├── 03-advanced-config.py               # 高级配置场景
└── data/                               # 示例共享样本数据
    └── sample-input.json
```

### `examples/README.md` 格式
```markdown
# Examples

面向外部开发者与 AI Code Agents 的使用示例。

## Prerequisites

[列出前置条件：语言运行时、依赖、配置方式]

## Examples

| # | 场景 | 文件 | 运行方式 |
|---|----------|------|------------|
| 1 | 快速开始 | [01-quick-start.py](01-quick-start.py) | `python examples/01-quick-start.py` |
| 2 | 数据导入 | [02-data-import.sh](02-data-import.sh) | `bash examples/02-data-import.sh` |
```

### 示例质量检查清单
- [ ] 示例可运行（UI 导览为可跟做）
- [ ] 含简要注释说明演示内容
- [ ] 使用真实但安全的样本数据——无占位 "foo/bar"
- [ ] 已更新 `examples/README.md` 索引
- [ ] 命名符合 `<NN>-<scenario-name>.<ext>`
- [ ] 无密钥——使用明确占位（`YOUR_API_KEY`）
