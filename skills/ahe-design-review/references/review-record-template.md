# 评审记录模板

## 记录格式

评审完成后，将结论写入：

- `docs/reviews/design-review-<topic>.md`
- 如 `AGENTS.md` 声明了等价路径，按映射路径保存

若项目尚未形成固定 review 记录格式，默认使用当前 skill pack 的共享模板 `templates/review-record-template.md`。

## 评审记录结构

```markdown
## 结论

通过 | 需修改 | 阻塞

## 发现项

- [critical|important|minor] 问题

## 薄弱或缺失的设计点

- 条目

## 下一步

- `通过`：`设计真人确认`
- `需修改`：`ahe-design`
- `阻塞`：`ahe-design` 或 `ahe-workflow-router`

## 记录位置

- `docs/reviews/design-review-<topic>.md` 或映射路径

## 交接说明

- `设计真人确认`：仅当结论为 `通过`；`interactive` 下等待真人，`auto` 下由父会话写 approval record
- `ahe-design`：用于所有需要回修设计内容的场景
- `ahe-workflow-router`：仅在需求漂移、route / stage / 证据链冲突时使用
```

## 结构化返回（JSON）

reviewer subagent 完成后返回给父会话：

```json
{
  "conclusion": "通过",
  "next_action_or_recommended_skill": "设计真人确认",
  "record_path": "实际写入的 review 记录路径",
  "key_findings": ["关键发现 1", "关键发现 2"],
  "needs_human_confirmation": true,
  "reroute_via_router": false
}
```

`next_action_or_recommended_skill` 必须只写一个 canonical 值，不得拼多个候选。

## 返回规则

| 结论 | next_action | needs_human_confirmation | reroute_via_router |
|------|------------|------------------------|-------------------|
| `通过` | `设计真人确认` | true | false |
| `需修改` | `ahe-design` | false | false |
| `阻塞`（设计内容回修） | `ahe-design` | false | false |
| `阻塞`（需求漂移/规格冲突） | `ahe-workflow-router` | false | true |

## 状态同步

如果使用 `task-progress.md` 驱动 workflow，approval step 完成后由父会话同步更新：

- 设计文档中的状态字段
- `task-progress.md` 中的 `Current Stage`
- `task-progress.md` 中的 `Next Action Or Recommended Skill`

reviewer subagent 不代替父会话写入批准结论。

## 结论判定规则

- **通过**：可追溯到已批准规格、关键决策和接口足够清晰、约束和 NFR 被吸收、无阻塞任务规划的设计空洞
- **需修改**：核心设计可用，但有局部缺口、决策说明不足、接口偏弱、测试准备度不足，可通过一轮定向修订补齐
- **阻塞**：设计无法清晰支撑需求规格、存在无法追溯的关键新增内容、关键架构决策缺失、或 route/stage/证据链冲突

## Severity 等级

- `critical`：阻塞任务规划，或会直接导致错误任务输入
- `important`：应在批准前修复
- `minor`：不阻塞，但建议改进

## Finding 格式

每条发现应包含完整信息，便于设计者定位和修复：

```markdown
**发现：** [清楚描述问题]
**严重度：** Critical | Important | Minor
**影响：** [具体后果]
**建议：** [可操作的修复方案]
**工作量：** [预估修复时间/复杂度]
**优先级：** 必须修复 | 应修复 | 建议改进
```

### Finding 写法对比

✅ 具体："`Order→Payment` 调用缺少熔断器（平均 50 calls/sec）。建议添加 Resilience4j，50% 错误阈值触发。"
❌ 模糊："需要更好的错误处理"

✅ 具体："`UserService` 有 15 个方法涵盖认证、资料、权限三个领域（上帝模块）。建议拆分为 AuthService、ProfileService、RBACService，预估 3 周。"
❌ 模糊："考虑改善服务边界"

## 评审原则

评审应基于项目上下文，不做脱离实际的评判：

- Startup MVP 和企业系统的评审标准不同
- 100 用户的系统不需要微服务复杂度
- 评审适当性：对规模、团队和时间的匹配度
- 发现应可操作，不只指出问题还要给出建议
