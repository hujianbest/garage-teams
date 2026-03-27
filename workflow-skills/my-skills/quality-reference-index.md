# MDC 质量模板索引

这个索引用于统一查看 `my-skills` 下与质量防护、变更同步相关的参考模板。

目标是让团队在执行 `MDC` 工作流时，能快速找到对应 skill 的记录模板，而不是临时自行组织格式。

## 使用建议

- 先根据当前所处 skill 找到对应模板。
- 小改动可用简化版模板，大改动、高风险改动、热修复优先使用标准版模板。
- 模板不是强制生成长文档，而是帮助团队留下可审计、可交接、可回溯的最小证据。

## 模板总览

| skill | 模板路径 | 用途 | 推荐使用时机 |
| --- | --- | --- | --- |
| `mdc-bug-patterns` | `my-skills/mdc-bug-patterns/references/bug-pattern-catalog-template.md` | 沉淀团队历史缺陷模式、复发问题和预防动作 | 团队要开始建立缺陷模式库，或在复盘后把经验固化为排查清单时 |
| `mdc-traceability-review` | `my-skills/mdc-traceability-review/references/traceability-review-record-template.md` | 记录规格、设计、任务、实现、测试与验证之间的追溯关系检查结果 | 代码评审后、回归前，或收尾前做一致性收口时 |
| `mdc-increment` | `my-skills/mdc-increment/references/change-impact-sync-record-template.md` | 记录需求变更的影响分析、同步项和下一步路由 | 需求范围、验收标准、设计假设或任务计划发生变化时 |
| `mdc-hotfix` | `my-skills/mdc-hotfix/references/hotfix-repro-and-sync-record-template.md` | 记录热修复的复现、修复、验证与同步闭环 | 紧急修复缺陷并需要保留最小证据链时 |

## 推荐使用路径

### 1. 缺陷模式沉淀

当团队发现“这类问题反复出现”时：

- 使用 `mdc-bug-patterns`
- 维护缺陷模式库模板
- 后续在实现评审链中复用这些模式

### 2. 追溯性收口

当实现已经基本完成，担心出现设计漂移或断链时：

- 使用 `mdc-traceability-review`
- 记录当前链路是否完整
- 再进入回归和完成门禁

### 3. 需求变更同步

当需求、范围、验收标准或设计边界发生变化时：

- 使用 `mdc-increment`
- 记录影响面与同步项
- 再决定回到规格评审、设计评审、任务评审或实现阶段

### 4. 紧急修复闭环

当问题需要快速修复，但仍要保留基本工程证据时：

- 使用 `mdc-hotfix`
- 记录复现、最小修复、验证结果和同步项
- 再进入后续质量门

## 维护建议

- 统一把模板保存在各 skill 目录下的 `references/` 里。
- 如果某类模板长期被频繁复用，可以继续拆成“标准版 / 简化版 / 示例版”。
- 如果团队后续增加新的质量 skill，也建议在这里补一条索引，保持入口统一。
