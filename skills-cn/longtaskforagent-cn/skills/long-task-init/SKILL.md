---
name: long-task-init
description: "在 ATS 文档已存在（或已自动跳过）但尚未创建 feature-list.json 时使用 — 搭建项目产物并将需求拆解为可验证特性"
---

# 初始化长任务项目

在 SRS 与设计均获批后执行一次。搭建所有持久化产物，将需求拆解为可验证特性，并为迭代 Worker 周期做好准备。

**开始时宣告：**「我正在使用 long-task-init 技能搭建项目。」

## 输入文档

本技能读取**三份**已批准文档：

| 文档 | 位置 | 提供内容 |
|----------|----------|----------|
| **SRS** | `docs/plans/*-srs.md` | 功能需求（FR-xxx）、NFR（NFR-xxx）、约束（CON-xxx）、假设（ASM-xxx）、接口需求（IFR-xxx）、术语表、用户画像、验收标准 |
| **Design** | `docs/plans/*-design.md` | 技术栈、架构、数据模型、API 设计、测试策略 |
| **ATS** | `docs/plans/*-ats.md` | 需求→场景映射、各需求所需测试类别（通过 srs_trace 查找约束下游 feature-st） |

## 检查清单

你必须为每一步创建 TodoWrite 任务并按顺序完成：

1. **阅读已批准的 SRS、设计与 ATS 文档**（自 `docs/plans/`）
   - SRS：`docs/plans/*-srs.md` — 需求、约束、假设、NFR、术语表、画像
   - Design：`docs/plans/*-design.md` — 技术栈、架构决策
   - ATS：`docs/plans/*-ats.md` — 需求→类别映射（约束 `ui` 标志及下游 feature-st 类别要求，经 srs_trace）
2. **运行 `scripts/init_project.py`** 以搭建确定性产物：
   ```bash
   python scripts/init_project.py <project-name> --path . --lang <language>
   ```
   - `<project-name>` — 来自 SRS 标题
   - `<language>` — 来自设计文档技术栈，取 `python|java|typescript|c|cpp` 之一
   - 使用 `--line-cov`、`--branch-cov`、`--mutation-score` 可覆盖阈值（默认：90/80/80）
   - 创建：`feature-list.json`、`CLAUDE.md`（追加）、`task-progress.md`、`RELEASE_NOTES.md`、`examples/`、`docs/plans/`
   - 自动将辅助脚本（`validate_features.py`、`check_configs.py`、`check_devtools.py`、`check_jinja2.py`、`check_real_tests.py`、`validate_guide.py`、`get_tool_commands.py`、`validate_st_cases.py`、`validate_increment_request.py`、`validate_bugfix_request.py`、`check_st_readiness.py`、`check_ats_coverage.py`、`check_mcp_providers.py`）复制到项目 `scripts/`
3b. **MCP 提供方设置**（若无需企业 MCP 则跳过）：
   - 询问用户：「本项目是否使用企业 MCP 服务器进行测试/覆盖率/变异/UI 自动化？」
   - 若**是**：
     1. 按能力收集：MCP 服务器名、安装命令、工具名、结果字段路径
     2. 在项目根创建 `tool-bindings.json`，参考 `docs/templates/tool-bindings-template.json`
     3. 检查 Jinja2 是否可用（模板渲染必需）：
        ```bash
        python scripts/check_jinja2.py
        ```
        → 退出码 1：向用户展示安装说明（`pip install jinja2`）；等待用户安装后重新运行检查直至退出码 0
        → 退出码 0：继续
     4. 渲染技能模板：
        ```bash
        python scripts/apply_tool_bindings.py tool-bindings.json --output-dir .long-task-bindings
        ```
        → 校验：「N 个模板已渲染到 .long-task-bindings/」
     5. 检查 MCP 服务器可用性：
        ```bash
        python scripts/check_mcp_providers.py tool-bindings.json
        ```
        → 退出码 1：向用户展示安装说明（脚本会输出精确的 `claude mcp add` 命令）；等待用户安装并重启会话后重新检查直至退出码 0
        → 退出码 0：继续
   - 若**否**：跳过（技能使用插件默认 — UI 用 Chrome DevTools MCP，测试用 CLI 工具）

3. **校验 `feature-list.json` 中的 `tech_stack` 与 `quality_gates`**：
   - 确认 `language`、`test_framework`、`coverage_tool`、`mutation_tool` 与设计文档一致
   - 按需调整 `quality_gates` 阈值（默认：行 90%、分支 80%、变异 80%）
   - 校验工具命令可正确解析：
     ```bash
     python scripts/get_tool_commands.py feature-list.json
     ```
   - 校验 `feature-list.json` 中的 `real_test` 配置：
     - `marker_pattern` 与项目所选真实测试识别方式一致
     - `mock_patterns` 覆盖项目 mock 框架关键词
     - `test_dir` 指向正确测试目录
4. **生成 `long-task-guide.md`** — 创建面向本项目的 Worker 会话指南：
   - 参考阅读：
     - `skills/long-task-work/SKILL.md` — Worker 工作流
     - `skills/long-task-quality/SKILL.md` — 验证强制执行
     - `skills/long-task-quality/coverage-recipes.md` — 覆盖率/变异工具配置
     - `skills/using-long-task/references/architecture.md` — TDD 工作流细节
   - **仅**包含本项目语言对应的覆盖率/变异命令（来自 `python scripts/get_tool_commands.py feature-list.json`）
   - **仅当**项目含 UI 特性（`"ui": true`）时包含 UI 测试小节：
     - 若存在 `tool-bindings.json` 且含 `capability_bindings.ui_tools.tool_mapping`：全文使用企业工具名（非 Chrome DevTools MCP 名称）
     - 否则：使用 Chrome DevTools MCP 工具名（`navigate_page`、`click` 等）
   - **必须包含全部必选小节**：Orient、Bootstrap、Config Gate、TDD Red、TDD Green、Coverage Gate、TDD Refactor、Mutation Gate、Verification Enforcement、Inline Compliance Check、Persist、Critical Rules
   - **必须包含 `Environment Commands` 小节**，含：
     - 环境激活命令（如 `source .venv/bin/activate`、`conda activate myenv`、`nvm use 20`）
     - 直接执行测试命令（如 `pytest --cov=src tests/`）
     - 直接变异测试命令（如 `mutmut run`）
     - 直接生成覆盖率报告命令
     - 以上取代已移除的 test.sh/mutate.sh 包装 — Claude 直接运行这些命令
   - **必须包含 `Service Commands` 小节**（仅当项目有服务端进程）：以 `env-guide.md` 为启动/停止/重启命令的权威来源；列出健康检查 URL；提醒 Restart Protocol
   - **必须包含 `Config Management` 小节**：说明如何为本项目新增/更新配置值（如 dotenv 项目「向 `.env` 追加 `KEY=value`」、Spring Boot「在 `application.properties` 设置 `key=value`」、仅系统环境「`export KEY=value`」）。Worker Config Gate 在提示缺失值时会引用本小节。
   - **必须包含 `Real Test Convention` 小节**：识别方式（marker/目录/命名，随语言调整）、仅运行真实测试的命令、与本项目技术栈对应的真实测试示例
   - 校验：
     ```bash
     python scripts/validate_guide.py long-task-guide.md --feature-list feature-list.json
     ```
5. **生成 `env-guide.md`** — 在项目根创建明确的服务生命周期指南（可由用户编辑）：

   - 从设计文档读取服务端口声明、健康检查 URL、服务名（API 设计/架构小节）
   - 从 `.env.example` 读取 `*_PORT=` 变量
   - 生成 `env-guide.md`，包含以下小节：

   **页首说明**（文件顶部）：
   > 可由用户编辑。Claude 在管理服务前会阅读本文件。端口变更或新增服务时请更新。

   **服务表**：
   | Service Name | Port | Start Command | Stop Command | Verify URL |
   |---|---|---|---|---|
   | （每服务一行） | | | | |

   **Start All Services** — 每个服务：
   ```bash
   # Unix/macOS
   [start command] > /tmp/svc-<slug>-start.log 2>&1 &
   sleep 3
   head -30 /tmp/svc-<slug>-start.log
   # → 从输出提取 PID 与端口；二者均记入 task-progress.md

   # Windows 替代
   cmd /c "start /b [command] > %TEMP%\svc-<slug>-start.log 2>&1"
   timeout /t 3 /nobreak >nul
   powershell "Get-Content $env:TEMP\svc-<slug>-start.log -TotalCount 30"
   ```

   **Verify Services Running** — 每个服务：
   ```bash
   curl -f http://localhost:<port>/health   # 或相应健康端点
   ```

   **Stop All Services** — 优先按 PID，备选按端口：
   ```bash
   # 按 PID（优先 — 使用 task-progress.md 中记录的 PID）
   kill <PID>                              # Unix/macOS
   taskkill /F /PID <PID>                  # Windows

   # 按端口（备选）
   lsof -ti :<port> | xargs kill -9        # Unix/macOS
   for /f "tokens=5" %a in ('netstat -ano ^| findstr :<port>') do taskkill /F /PID %a  # Windows
   ```

   **Verify Services Stopped** — 端口应无输出：
   ```bash
   lsof -i :<port>                         # Unix/macOS — 预期无输出
   netstat -ano | findstr :<port>           # Windows — 预期无输出
   ```

   **Restart Protocol（4 步）**：
   1. **Kill** — Stop All Services（按 task-progress.md 的 PID，或按端口）
   2. **Verify dead** — 运行 Verify Services Stopped；轮询端口最多 5 秒 — 必须无响应
   3. **Start** — 运行 Start All Services 并捕获输出 → `head -30` → 提取新 PID/端口 → 更新 task-progress.md
   4. **Verify alive** — 运行 Verify Services Running；轮询健康端点最多 10 秒 — 必须有响应

   - **复杂启动序列**：若某服务需 >2 条 shell 命令才能启动（如 DB 迁移 + 种子 + 服务器），生成 `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-start.ps1` 包含完整序列；更新 env-guide.md 中「Start All Services」为调用 `bash scripts/svc-<slug>-start.sh` 而非内联命令；停止序列同理（`scripts/svc-<slug>-stop.sh`）。保持 env-guide.md 可读，逻辑版本化在 `scripts/` 中
   - 若项目仅为 CLI 或库（无服务端进程）：生成极简 `env-guide.md`，页首说明为「无服务端进程 — 仅环境激活」，并仅含来自 `long-task-guide.md` 的激活命令

6. **生成 `init.sh` / `init.ps1`** — 创建真实可运行的引导脚本：
   - 阅读 `references/init-script-recipes.md`（long-task-init 技能目录内）获取各工具模板与最佳实践
   - **从**设计文档技术栈与项目约束**检测**环境管理器：
     - Python：miniconda/conda/mamba、venv、poetry、pipenv、uv、pyenv
     - Node.js：nvm、fnm、volta、corepack
     - Java：sdkman、jenv
     - 通用：devcontainer、docker、nix
   - **必须处理**：环境创建、激活、依赖安装、工具版本校验
   - **必须幂等** — 重复运行不破坏已有环境
   - **必须跨平台** — Unix/macOS 用 `init.sh`，Windows 用 `init.ps1`
   - **必须包含**：错误处理、版本检查、明确的成功/失败输出
   - 实际依赖安装命令（非注释占位）
   - `git clone` 后应能立即执行
   - **说明**：不需要 psutil — 服务生命周期通过 `env-guide.md` 中的命令管理，而非钩子
7. **在 `feature-list.json` 中填写 SRS 字段** — 来自 **SRS 文档**：
   - `constraints[]` — 从 SRS「Constraints」复制 CON-xxx；每项为简短字符串
   - `assumptions[]` — 从 SRS「Assumptions & Dependencies」复制 ASM-xxx；每项为简短字符串
   - NFR-xxx 行 → 创建 `category: "non-functional"` 的特性，带 `srs_trace`（如 `["NFR-001"]`）及可选可度量 `verification_steps`；覆盖率/变异门禁不适用于 NFR 特性
8. **将需求拆解为特性** — 来自 **SRS 文档** 与 **设计文档开发计划**（第 11 节），填写 `feature-list.json` 的 `features[]`：
   - 每个 FR-xxx → 一个或多个特性，含 `id`、`category`、`title`、`description`、`priority`、`status`（始终 `"failing"`）、`srs_trace`、`dependencies`
   - 每个特性**必须**含 `srs_trace`：实现该特性所覆盖的 SRS 需求 ID 数组（如 `["FR-001", "FR-002"]`）
   - `verification_steps` **可选** — 若提供，应追溯到 SRS 验收标准（Given/When/Then）
   - UI 特性：设 `"ui": true`，可选 `"ui_entry": "/path"`；若提供 verification_steps，含 `[devtools]` 前缀步骤
   - **若提供 verification_steps** — 质量规则（驱动下游 ST 用例与 TDD 质量）：
     - 每步**必须**为含 Given/When/Then 的行为场景，而非简单断言
     - 差：`"Login page displays correctly"` → 无动作、无断言
     - 好：`"[devtools] Navigate /login → EXPECT: email input, password input, 'Sign In' button; fill valid creds → click Sign In → EXPECT: redirect to /dashboard, user name in header; REJECT: console errors, broken images"`
     - 差：`"API returns 200 on valid input"` → 断言而非场景
     - 好：`"Given a registered user, when POST /api/orders with valid payload, then response 201 with order ID; and GET /api/orders/{id} returns the created order with correct fields"`
     - 对 `"ui": true` 特性：每个 `[devtools]` 步骤**必须**描述多步交互链（navigate → interact → verify → interact → verify）
     - 对依赖后端的特性：至少一步**必须**验证跨依赖边界的真实数据流
     - **最低复杂度**：每个特性**应**有 ≥1 条含 3+ 串联动作的 verification_step
   - **ATS 类别约束**（若存在 ATS 文档）：对每个特性用 srs_trace 查找 ATS 要求的类别。若**任意** srs_trace 需求在 ATS 中含 UI，则设 `ui: true`。
   - **前后端配对规则**：前端特性（`"ui": true`）**必须**在 `dependencies[]` 中列出所依赖的后端 API 特性。此外，`features[]` 数组**必须**按**成对分组**排序：每个后端特性之后，紧接其对应前端特性。确保 Worker 开发顺序为 Backend A → Frontend A → Backend B → Frontend B，而非先全部后端再全部前端。
   - 目标 10–200+ 特性；每项可独立验证且可在一个会话内完成
   - **优先级排序**：遵循设计文档任务分解表（11.2 节）— P0/P1/P2/P3 映射为 high/high/medium/low
   - **依赖链**：遵循设计文档依赖链图（11.3 节）填写各特性 `dependencies[]`
   - **里程碑映射**：按设计文档里程碑对特性逻辑排序
   - **优先级内成对排序**：在同一优先级内，使每个后端特性紧接其前端对应项。框架/基础设施特性（P0）优先且无需配对。示例顺序：
     - P0：框架/基础设施（无需配对）
     - P1：[Backend Auth API, Frontend Auth Pages, Backend Orders API, Frontend Orders Pages, ...]
     - P2：[Backend Reports API, Frontend Reports Dashboard, ...]
     - 依赖机制保证 Frontend A 在 Backend A 通过前不能开始；数组顺序保证 Backend A 通过后 Frontend A 为下一候选。
9. **填写 `required_configs`** — 来自 **SRS**（IFR-xxx 接口需求）与设计文档：
   - API 密钥、服务 URL → 类型 `env`
   - 配置文件、证书 → 类型 `file`
   - 通过 `required_by` 关联特性；提供含设置说明的 `check_hint`
9b. **生成 `scripts/check_configs.py`** — 项目专用配置检查器（由 LLM 生成，非从插件复制）：
    - 根据 `tech_stack.language` 与设计文档分析项目配置格式：
      - Python + `.env` 模式 → 使用类 `load_dotenv` 的 KEY=VALUE 解析
      - Java/Spring → 解析 `src/main/resources/application.properties` 或 `application.yml`
      - Node.js → 读取 `.env` 或 `config/` 目录
      - Go / Rust → 读取 TOML / YAML，或依赖系统环境
      - 仅依赖系统环境变量的项目 → 无需文件加载
    - 生成脚本，**标准接口**为：
      - 用法：`python scripts/check_configs.py feature-list.json [--feature <id>]`
      - 从 `feature-list.json` 读取 `required_configs[]`
      - 使用项目原生格式加载配置（为本项目硬编码）
      - `env` 类型经 `os.environ` 检查，`file` 类型经 `os.path.exists` 检查
      - 打印每项缺失配置的 `name` 与 `check_hint`
      - 退出码 0 = 所需配置齐全；退出码 1 = 至少一项缺失
    - **无需** `--dotenv` 或格式开关 — 加载逻辑内建于本项目
    - 插件的 `scripts/check_configs.py` 可作参考模板
10. **生成 `.env.example`** — 来自 `required_configs`：
    - 对每个 `env` 类型配置写注释模板行：
      ```
      # <name> — <description>
      # Hint: <check_hint>
      # Required by features: <required_by ids>
      <KEY>=
      ```
    - 将密钥配置文件加入 `.gitignore`（如 `.env`）；`.env.example` 可安全提交
    - 本模板列出所需环境变量；用户按项目所用配置格式加载；Worker Config Gate 会对缺失值提示
11. **校验**：
    ```bash
    python scripts/validate_features.py feature-list.json
    ```
12. **搭建项目骨架**（目录、配置、依赖清单）— 基于**设计文档**架构
13. **Git init + 初始提交**
14. **运行 init 脚本并校验环境**：
    - 运行 `init.sh`（或 `init.ps1`），确认环境搭建无错
    - 校验测试执行：激活环境 → 按 `long-task-guide.md` 运行测试命令 → 确认测试能跑（此时可能全部失败 — 属预期）
    - 校验变异测试命令可用：激活环境 → 运行变异工具版本检查
    - 任一项失败：诊断根因，修复脚本或配置后重跑
    - **不要**在此启动服务 — 服务在 ST 测试阶段按 `env-guide.md` 定义启动
15. **更新 `task-progress.md`** — 在 `## Current State` 写入初始进度（0/N 特性通过），并追加 Session 0 记录（含 SRS + 设计文档引用）
16. **开始首个 Worker 周期** — **必选子技能：** 调用 `long-task:long-task-work`

## 服务配置维护（Worker 周期）

当 Worker 周期引入新后端服务、变更服务端口，或发现实际启停命令与 env-guide.md 不符时，更新 `env-guide.md`：
- 增改服务表行（服务名、端口、启停/校验命令）
- 增改对应的 Start、Verify、Stop、Restart 命令
- 若启停序列需 >2 条 shell 步骤：抽取到 `scripts/svc-<slug>-start.sh` / `scripts/svc-<slug>-stop.sh`，并更新 env-guide.md 引用脚本
- 将 env-guide.md 及任意 `scripts/svc-*` 变更与特性置于同一 git 提交

**env-guide.md 必须始终反映实际可用的命令。** 每当某命令在 TDD Green 或修复失败后被验证正确，必须更新 env-guide.md 与之一致。

## feature-list 模式

根结构：
```json
{
  "project": "project-name",
  "created": "2025-01-15",
  "tech_stack": {
    "language": "python|java|typescript|c|cpp",
    "test_framework": "pytest|junit|vitest|gtest|...",
    "coverage_tool": "pytest-cov|jacoco|c8|gcov|...",
    "mutation_tool": "mutmut|pitest|stryker|mull|..."
  },
  "quality_gates": {
    "line_coverage_min": 90,
    "branch_coverage_min": 80,
    "mutation_score_min": 80
  },
  "constraints": ["Hard limit — one string per item"],
  "assumptions": ["Implicit belief — one string per item"],
  "required_configs": [
    {
      "name": "Display name",
      "type": "env|file",
      "key": "ENV_VAR (for env type)",
      "path": "path/to/file (for file type)",
      "description": "What this config is for",
      "required_by": [1, 3],
      "check_hint": "How to set it up"
    }
  ],
  "features": [...]
}
```

每个特性：
```json
{
  "id": 1,
  "category": "core",
  "title": "Feature title",
  "description": "What it does",
  "priority": "high|medium|low",
  "status": "failing|passing",
  "srs_trace": ["FR-001", "FR-002"],
  "verification_steps": ["step 1", "step 2"],
  "dependencies": [],
  "ui": false,
  "ui_entry": "/optional-path"
}
```

## 生成的持久化产物

| 文件 | 用途 |
|------|---------|
| `feature-list.json` | 含状态的结构化任务清单 |
| `CLAUDE.md` | 跨会话导航索引（追加） |
| `task-progress.md` | 按会话的进度日志 |
| `RELEASE_NOTES.md` | 持续更新发布说明（Keep a Changelog 格式） |
| `examples/` | 可运行示例目录 |
| `init.sh` / `init.ps1` | 环境引导（LLM 生成） |
| `env-guide.md` | 服务生命周期命令 — 启停/重启/校验与输出捕获；用户可编辑 |
| `long-task-guide.md` | Worker 会话指南：环境激活 + 直接测试命令（LLM 生成，已校验） |
| `.env.example` | 所需环境变量模板（可提交） |

## 回顾授权（最后一步）

在所有产物已搭建且 feature-list.json 已创建后：

```bash
python scripts/check_retro_auth.py feature-list.json
```

- **退出码 0**（端点已配置且可达）：使用 `AskUserQuestion` 询问用户：
  > "检测到 Skill 反馈 API 已配置（{endpoint}）。是否授权在本项目中搜集 Skill 改进建议并在项目结束后上报？搜集内容包括：用户反馈修正、技能缺陷分析。不包含项目代码或业务数据。"
  > 选项："授权 (Recommended)" / "不授权"
  - 用户授权 → 在 `feature-list.json` 根设置 `"retro_authorized": true`
  - 用户拒绝 → 在 `feature-list.json` 根设置 `"retro_authorized": false`
- **退出码 1 或 2**（不可用或已禁用）：静默跳过 — 不向用户提问

## 集成

**由…调用：** long-task-ats（第 12 步）或 using-long-task（当 ATS 文档存在且无 feature-list.json）  
**读取：** `docs/plans/*-srs.md`（需求）+ `docs/plans/*-design.md`（架构）+ `docs/plans/*-ats.md`（测试策略约束）  
**链接至：** long-task-work（初始化完成后）  
**产出：** feature-list.json + 上文所列全部搭建产物
