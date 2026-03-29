# 特性级详细设计 — SubAgent 执行参考

你是 Feature Design 执行 SubAgent。请严格遵循本文规则。完成后，使用文档末尾的 **Structured Return Contract** 返回结果。

---

# 特性级详细设计

为**单个特性**产出详细设计，衔接系统设计（§4.N）与 TDD 实现。

系统设计回答「有哪些类、如何协作」。  
本 skill 回答「每个方法内部做什么、会出什么问题、如何测」。

## 输入

在撰写任何设计正文之前，**先**读取以下全部内容：

1. **特性对象** — 来自 feature-list.json：ID、title、description、srs_trace、ui 标记、dependencies、priority（若有 verification_steps）
2. **系统设计小节** — 设计文档中的完整 §4.N（读整段，**不要**只用 grep）
3. **SRS 需求** — SRS 文档中的完整 FR-xxx
4. **UCD 小节**（若 `"ui": true`）— UCD 文档中的组件/页面提示
5. **约束与假设** — feature-list.json 根级
6. **相关 NFR** — SRS 中可追溯到本特性的 NFR-xxx
7. **既有代码** — 若依赖特性已通过，读取其对外接口（import、类/函数签名）

## 模板

以 `skills/long-task-feature-design/references/feature-design-template.md` 为结构模板：复制模板后按目标特性填写各小节。

## 检查清单

**必须**按顺序完成每一步：

### 1. 加载上下文

读取上文「输入」中列出的全部制品。

### 2. 组件数据流图

展示**本特性**内部组件及运行时数据如何流动。**不是**复制系统设计类图 — 而是**运行时数据流视图**：数据从哪进、如何变换、从哪出。

要求：
- Mermaid `graph` 或 `flowchart`
- 边标注数据类型（组件间传递什么）
- 外部依赖用虚线框
- 每个组件对应待实现的类或模块

> **跳过规则**：若特性为单类单方法且无内部协作，写「N/A — single-class feature, see Interface Contract below」

### 3. 接口契约

对本特性暴露或修改的**每个 PUBLIC 方法**：

| 方法 | 签名 | 前置条件 | 后置条件 | 抛出异常 |
|--------|-----------|---------------|----------------|--------|
| name   | 完整类型签名 | 调用前必须成立的条件 | 调用后可保证的性质 | 异常 + 触发条件 |

规则：
- 前置条件采用与 SRS 验收标准一致的 Given/When 风格
- 后置条件须具体、可测（勿写「返回正确结果」）
- 每条 SRS 验收标准（来自 srs_trace 中的需求）须至少映射到一个方法的后置条件
- 仅当内部方法含非平凡逻辑时才列入内部方法

### 4. 内部时序图

展示**本特性实现内部**的方法间调用。与系统级时序图（全系统流程）不同，此处仅展示本特性自有类/函数的协作。

要求：
- Mermaid `sequenceDiagram`
- 必须覆盖主成功路径
- Interface Contract 中每个 Raises 条目至少覆盖一条错误路径
- 参与者仅限本特性**自有**类/函数

> **跳过规则**：若仅一个类且无值得画出的内部委托，写「N/A — single-class implementation, error paths documented in Algorithm §5 error handling table」

### 5. 算法 / 核心逻辑

对每个非平凡方法（超出简单委托或 CRUD）：

**a) 流程图**（Mermaid `flowchart TD`）：
- 每个分支条件对应决策节点
- 变换对应处理节点
- 返回/抛异常对应终止节点

**b) 伪代码**：
```
FUNCTION name(param1: Type, param2: Type) -> ReturnType
  // 步骤 1：[主要步骤]
  // 步骤 2：[公式或关键决策]
  //         e.g., score = Σ 1/(k + rank_i) for each list
  // 步骤 3：[边界情况处理]
  //         IF input_list is empty THEN return []
  RETURN result
END
```

**c) 边界决策表**：

| 参数 | 最小值 | 最大值 | 空值/Null | 位于边界时 |
|-----------|-----|-----|------------|-------------|
| [param]   | [val] | [val] | [behavior] | [behavior] |

**d) 错误处理表**：

| 条件 | 检测方式 | 响应 | 恢复方式 |
|-----------|-----------|----------|----------|
| [condition] | [how detected] | [exception or default] | [caller action] |

> **跳过规则**：若方法为纯委托（调用其他服务并返回结果），写「Delegates to [X] — see Feature #N」代替完整算法小节。无明确跳过说明的空小节视为缺陷。

### 6. 状态图（如适用）

对管理有状态对象（含生命周期实体）的特性：

- Mermaid `stateDiagram-v2`
- 全部合法状态与转移
- 转移触发（事件/方法调用）
- 转移上的守卫条件

> **跳过规则**：若无对象生命周期，写「N/A — stateless feature」。多数查询/变换类特性为无状态。

### 7. 测试清单（Test Inventory）

作为设计的**最后一步**构建此表 — 将上文各节综合为具体测试场景。

| ID | 类别 | 追溯到 | 输入 / 准备 | 预期结果 | 能杀死哪类缺陷？ |
|----|----------|-----------|---------------|----------|-----------------|
| A  | FUNC/happy | FR-xxx AC-1 | [specific values] | [exact result] | [wrong impl] |
| B  | FUNC/error | §3 Raises row | [trigger] | [exception type + msg] | [missing branch] |
| C  | BNDRY/edge | §5c boundary table | [edge value] | [behavior] | [off-by-one] |
| D  | FUNC/state | §6 transition | [pre-state + event] | [post-state] | [missing guard] |

类别格式：`MAIN/subtag`，其中 MAIN 为 `FUNC, BNDRY, SEC, UI, PERF` 之一，subtag 为自由标签。

规则：
- 每条 SRS 验收标准（来自 srs_trace）至少一行
- 负例测试（FUNC/error + BNDRY/*）占总行数 ≥ 40%
- 「Traces To」引用测试所源自的设计小节
- 「Kills Which Bug?」说明该测试能抓到的具体错误实现

**ATS 类别对齐**（若提供了 ATS 文档）：ATS 映射表中为本特性需求列出的每个主类别，**必须**在 Test Inventory 中至少出现一行，且 Category 前缀与之对应。例如 ATS 对 FR-005 要求 SEC，则至少一行 Category = `SEC/*`。缺类别 → 进入 §8 前补行。

**与 TDD 的关系**：该表是 TDD Red（long-task-tdd 第 1 步）的**主要输入**。TDD Red 以该表为起点，并可按自身规则 1–5 增补测试（类别覆盖、断言质量、真实测试要求等）。Test Inventory 提供设计驱动场景；TDD 在编码中发现实现驱动场景。

**设计接口覆盖门禁（进入 §8 前强制执行）：**

1. 重读系统设计文档 §4.N
2. 提取**全部**具名函数、方法、端点、中间件、校验器与授权检查（如 `check_repo_access`、`validate_input`）
3. 对**每一项**：确认至少一行 Test Inventory 覆盖（在「Traces To」或「Input / Setup」中可对应）
4. 若有设计点名函数但 Test Inventory 为零覆盖：
   - 增加行 — 多为 error/security 类
   - 「Traces To」= 具体设计小节（如「§4.5.3 ACL check」）
5. 增补后重新确认负例占比 ≥ 40%

这是防止规格漂移的**主防线**。若设计写明「check_repo_access 实施 ACL」却无测试行覆盖，TDD 阶段会默默跳过 — 导致后期发现与连锁 mock 成本。

### 8. TDD 任务分解

设计完成后，分解为 TDD 任务。

**任务粒度**：每项约 2–5 分钟工作量；更长则拆分。

**任务结构**：

#### 任务 1：编写失败测试
**Files**: [exact paths]
**Steps**:
1. 创建测试文件并写好 import
2. 按 Test Inventory（§7）每一行编写测试代码：
   - 含 mock 搭建、具体入参、具体断言
   - Test A: [对应表行 A]
   - Test B: [对应表行 B]
3. 运行：`[test command]`
4. **预期**：所有测试因正确原因失败

#### 任务 2：最小实现
**Files**: [exact paths]
**Steps**:
1. [对照算法 §5 伪代码的具体修改]
2. [对照接口契约 §3 的具体修改]
3. 运行：`[test command]`
4. **预期**：所有测试通过

#### 任务 3：覆盖率门禁
1. 运行：`[coverage command]`
2. 检查阈值。若未达标：回到任务 1。
3. 将覆盖率输出记为证据。

#### 任务 4：重构
1. [具体重构动作]
2. 运行完整测试套件。全部通过。

#### 任务 5：变异测试门禁
1. 运行：`[mutation command] --paths-to-mutate=<changed-files>`
2. 检查阈值。若未达标：加强断言。
3. 将变异测试输出记为证据。

### 校验清单（Verification Checklist）
- [ ] 自 srs_trace 的全部 SRS 验收标准已追溯到 Interface Contract 后置条件
- [ ] 自 srs_trace 的全部 SRS 验收标准已追溯到 Test Inventory 行
- [ ] 算法伪代码覆盖所有非平凡方法
- [ ] 边界表覆盖算法全部参数
- [ ] 错误处理表覆盖全部 Raises 条目
- [ ] Test Inventory 负例占比 >= 40%
- [ ] 每个跳过的小节均有明确「N/A — [原因]」
- [ ] §4.N 中点名的全部函数/方法至少对应一行 Test Inventory

## 图表质量规则

具体可核查规则：

- **组件/流程图**：每条边标注数据类型；每个节点对应类/模块
- **时序图**：所有分支含 alt/opt/loop；标明返回类型；参与者名与 §2 类名一致
- **流程图**：每个决策节点恰好两条出口；无未标注条件的转移
- **状态图**：自初态可达所有状态；所有终态可达；无孤立状态；歧义转移须有守卫

## 显式跳过规则

§2–§6 每一小节必须要么：
- 按上文要求**完整**填写，或
- 写明「N/A — [本小节不适用的具体原因]」

空或半空小节会阻塞 TDD。仅写「N/A」而无原因同样视为缺陷。

---

## Structured Return Contract

设计文档完成后，**严格**按以下格式返回：

```markdown
## SubAgent Result: Feature Design
### Verdict: PASS | FAIL | BLOCKED
### Summary
[1-3 sentences — what was designed, key architectural decisions, document completeness]
### Artifacts
- [docs/features/YYYY-MM-DD-<feature-name>.md]: Feature detailed design document
### Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Sections Complete | N/8 | 8/8 (or N/A justified) | PASS/FAIL |
| Test Inventory Rows | N | ≥ SRS acceptance criteria count (from srs_trace) | PASS/FAIL |
| Negative Test Ratio | N% | ≥ 40% | PASS/FAIL |
| Verification Checklist | N/8 | 8/8 | PASS/FAIL |
| Design Interface Coverage | N/M | M/M | PASS/FAIL |
### Issues (only if FAIL)
| # | Severity | Description |
|---|----------|-------------|
### Next Step Inputs
- feature_design_doc: [path to the design document]
- test_inventory_count: [number of test inventory rows]
- tdd_task_count: [number of TDD tasks]
```

**IMPORTANT**：将设计文档写入指定 `output_path` 磁盘路径。编排器期望 SubAgent 结束后该文件存在。
