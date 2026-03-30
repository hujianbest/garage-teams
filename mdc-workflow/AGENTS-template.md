# AGENTS.md 模板

下面是一份面向 `mdc-workflow` 的 `AGENTS.md` 样板。

使用方式：

- 把尖括号中的占位符替换成你们团队的真实内容
- 删除不适用的小节
- 若某项没有团队特定要求，可以保留空白或直接删掉，skill 会回落到默认行为

---

# <项目或团队名称> — Agent 指引

## 仓库工作方式

1. 所有软件交付类请求，优先进入 `skills/mdc-workflow/`。
2. 进入任一 `mdc-*` skill 前，先读取本文件中的 `MDC Workflow` 小节。
3. `mdc-workflow` 的工件映射、审批别名、模板覆盖、编码规范、设计规范、测试规范，统一以本文件为准。
4. 不要再引入与本文件平行的映射配置文件。

## MDC Workflow

### 命名空间

- 默认产品线: `<默认产品或模块名>`
- 若仓库包含多个产品或子系统，在下方工件映射中按产品分别列出

### 工件映射

先按 artifact model 声明三类工件：

- `baseline artifacts`: `<例如 已批准 specs/designs 与长期团队规范>`
- `change workspace`: `<例如 单次需求、increment 或 hotfix 的在制工件集合>`
- `archive`: `<例如 已完成 change 的 review / verification / release 归档位置>`

然后再声明实际路径：

- 需求规格: `<例如 docs/specs/<topic>.md>`
- 设计文档: `<例如 docs/designs/<topic>.md>`
- 任务计划: `<例如 docs/tasks/<topic>.md>`
- 评审目录: `<例如 docs/reviews/>`
- 验证目录: `<例如 docs/verification/>`
- 进度文件: `<例如 task-progress.md>`
- 发布说明: `<例如 RELEASE_NOTES.md>`
- 归档目录: `<例如 docs/archive/>`

### Change Workspace 约定

- workspace 命名方式: `<例如 feature-<topic> / hotfix-<issue> / change-<date>-<topic>>`
- workspace 标识记录位置: `<例如 task-progress.md 的 Current Workspace 字段>`
- 哪些工件默认属于 workspace: `<例如 spec delta / design delta / tasks / review / verification / release notes>`
- 哪些工件只在 finalize 后才能提升为 baseline: `<例如 已批准 spec / design 最终稿>`
- 哪些记录完成后进入 archive: `<例如 review / verification / finalize summary / release snapshot>`

### 审批别名

- 已批准:
  - `状态: 已批准`
  - `Status: Approved`
  - `<团队自定义别名>`
- 通过:
  - `通过`
  - `PASS`
  - `<团队自定义别名>`
- 需修改:
  - `需修改`
  - `REVISE`
  - `<团队自定义别名>`
- 阻塞:
  - `阻塞`
  - `BLOCKED`
  - `<团队自定义别名>`

### 真人确认证据

可接受的真人确认等价证据：

- 评审记录中包含 `<例如 Human Confirmation: Yes>`
- 指定审批人的 PR 审批已通过
- 工单状态变为 `<例如 Design Approved>`
- `<其他团队认可的人审证据>`

### 模板覆盖

- 规格模板: `<例如 docs/templates/spec-template.md>`
- 设计模板: `<例如 docs/templates/design-template.md>`
- 任务模板: `<例如 docs/templates/tasks-template.md>`
- 评审记录模板: `<例如 docs/templates/review-template.md>`
- 验证记录模板: `<例如 docs/templates/verification-template.md>`

### 编码规范

- `<例如 service 层依赖方向必须先于 handler 层>`
- `<例如 优先使用显式错误映射，而不是通用兜底捕获>`
- `<例如 禁止在业务逻辑中直接拼接 SQL>`

### 设计规范

- `<例如 每份设计必须包含候选方案、最终取舍和回滚影响>`
- `<例如 异步任务必须说明重试、超时和幂等策略>`
- `<例如 外部接口必须明确错误语义和兼容性影响>`

### 测试规范

- `<例如 后端任务先运行 pnpm test:unit，再运行 pnpm test:integration>`
- `<例如 handler 行为优先使用契约级测试>`
- `<例如 集成测试中避免 mock repository 层>`
- `<例如 非代码配置变更允许豁免 TDD，但必须记录理由>`

### Workflow Profiles

- 默认 profile: `full`
- 强制 full 规则:
  - `<例如 涉及支付、权限、并发状态机的改动>`
  - `<例如 跨模块接口变更>`
  - `<例如 数据迁移>`
- 允许 lightweight 的条件:
  - `<例如 docs/ 下的纯文档改动>`
  - `<例如 README、CHANGELOG 更新>`
  - `<例如 配置文件调整（不影响运行时行为）>`
- 禁止 lightweight 的条件:
  - `<例如 涉及测试基础设施变更>`
  - `<例如 CI/CD 配置变更>`
  - `<例如 安全相关配置变更>`

### 门禁与例外

- `<例如 docs-only 改动可以跳过 mdc-test-review，但不能跳过 completion gate>`
- `<例如 紧急 hotfix 仍需先复现再修复>`
- `<例如 若使用异步审批系统，PR approval 可作为真人确认等价证据>`

### Archive 与收口策略

- finalize 时哪些结果回写到 baseline: `<例如 已批准 spec / design 的最终版>`
- finalize 时哪些结果进入 archive: `<例如 review 记录 / verification 记录 / release note snapshot>`
- archive 是否允许参与恢复上下文: `<例如 允许，但不能替代当前 workspace 的批准证据或 fresh verification evidence>`

## 额外项目约定

### 技术栈

- 主要语言: `<例如 TypeScript / Go / Java>`
- 包管理器: `<例如 pnpm / npm / poetry>`
- 常用验证命令:
  - `<例如 pnpm lint>`
  - `<例如 pnpm test:unit>`
  - `<例如 pnpm test:integration>`

### 风险提醒

- `<例如 涉及支付、权限、并发状态机的改动必须补充边界测试>`
- `<例如 数据迁移脚本必须附带回滚说明>`

### 非目标或禁止事项

- `<例如 未经批准不得引入新基础设施>`
- `<例如 不要把临时排障脚本提交到主代码目录>`

---

维护建议：

- 当路径、审批词汇、模板或团队规范变化时，优先更新本文件
- 保持这里的规则短而稳定，避免写成冗长过程文档
- 若某项规则只适用于个别目录，可在本文件继续补充更细的文件或模块约定
