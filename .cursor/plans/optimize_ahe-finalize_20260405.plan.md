# 优化 `ahe-finalize` 方案

## 目标

把 `skills/ahe-finalize/SKILL.md` 从“做个收尾总结”的 skill，提升为“能稳定产出高质量 closeout 工件、完成状态收口、证据索引和后续交接信息”的 skill。

本次优化不改变 AHE 主链契约：

- 仍然只有在完成门禁通过后才进入 `ahe-finalize`
- 仍然不由 `ahe-finalize` 重新执行或替代 `ahe-regression-gate` / `ahe-completion-gate`
- 仍然不在收尾阶段混入新的实现工作
- 仍然由 `ahe-workflow-starter` 负责后续会话恢复编排

## 当前问题

当前 `ahe-finalize` 已经强调更新状态、发布说明和证据位置，但仍有几个高价值短板：

- 没有把 completion / regression gate 的落盘记录作为强输入来消费
- 没有区分 full / standard / lightweight profile 下实际存在的证据链
- 文档同步仍偏笼统，缺少“哪些入口文档需要与实际交付保持一致”的最小检查
- 输出更像 narrative summary，而不是可直接交接的 delivery pack
- `Next Action` 仍是自然语言选项，不够贴合 starter 的 canonical handoff
- 没有把“finalize 只做状态与文档收口，不再改实现”写成更硬的边界

## 优化方向

### 1. 增加 gate 证据优先读取

要求 finalize 先读取：

- `ahe-completion-gate` 的落盘记录
- `ahe-regression-gate` 的落盘记录
- 当前 profile 下实际存在的 review / verification 结果

为什么这么改：

- finalize 不应靠会话记忆收尾，而应锚定已经落盘的 gate 结论

主要参考：

- `skills/ahe-completion-gate/SKILL.md`
- `skills/ahe-regression-gate/SKILL.md`
- `references/superpowers-main/skills/verification-before-completion/SKILL.md`

### 2. 增加 profile-aware 证据矩阵

要求明确：

- 当前是 full / standard / lightweight 哪种 profile
- 哪些 review / gate 在该 profile 下适用
- 哪些证据项是 N/A 而不是遗漏

为什么这么改：

- finalize 不能隐含要求 lightweight 也提供 full 才有的证据

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-test-review/SKILL.md`
- `skills/ahe-code-review/SKILL.md`
- `skills/ahe-traceability-review/SKILL.md`

### 3. 增加最小文档一致性检查

收尾时至少检查：

- `RELEASE_NOTES.md`
- `task-progress.md`
- 与本轮变化直接相关的入口文档（如 `README.md`、`AGENTS.md` 或已有使用说明）

为什么这么改：

- 高质量 finalize 不只是说“文档已更新”，而是确认用户和下一位执行者会看到一致信息

主要参考：

- `references/gstack-main/document-release/SKILL.md`
- `references/longtaskforagent-main/skills/long-task-finalize/SKILL.md`

### 4. 把输出升级成 delivery / handoff pack

要求输出至少显式说明：

- 已完成范围
- 已更新记录
- 证据链与路径
- 用户可见变化
- 已知限制 / 剩余风险 / 延后项
- branch / PR / 集成状态（如项目使用）
- canonical `Next Action Or Recommended Skill`

为什么这么改：

- 这样 finalize 才是真正可交接的收尾节点，而不只是会话总结

主要参考：

- `references/longtaskforagent-main/skills/long-task-finalize/SKILL.md`
- `references/superpowers-main/skills/finishing-a-development-branch/SKILL.md`

### 5. 收紧 `task-progress.md` 字段写法

要求明确写回：

- `Current Stage`
- `Current Active Task`
- `Session Log`
- `Next Action Or Recommended Skill`

并优先使用 canonical handoff，而不是自然语言阶段名。

为什么这么改：

- finalize 是下一次会话最容易读取的状态节点之一，字段漂移会直接影响 starter 恢复编排

主要参考：

- `skills/ahe-workflow-starter/SKILL.md`
- `skills/ahe-finalize/SKILL.md`

### 6. 增加硬边界：finalize 不改实现

显式规定：

- finalize 只做状态、发布说明、证据索引和文档收口
- 若发现仍需改实现，应停止 finalize 并回到主链相应节点

为什么这么改：

- “顺手再修一点”是收尾阶段最常见的污染源之一

主要参考：

- `references/longtaskforagent-main/skills/long-task-finalize/SKILL.md`
- `references/superpowers-main/skills/verification-before-completion/SKILL.md`

### 7. 可选补充：使用 / 验证提示

若本轮交付改变了用户可见行为，可选补充：

- 简短使用说明
- 关键验证入口

为什么这么改：

- 这会让交付物对下一位操作者或用户更友好
- 但应保持可选，不能让所有 finalize 任务无限膨胀

主要参考：

- `references/longtaskforagent-main/skills/long-task-finalize/SKILL.md`

## 明确不做的事

- 不重新执行 completion / regression gate
- 不把 finalize 变成 release engineering 大全
- 不在收尾节点写新的实现代码
- 不新增 starter 之外的恢复编排权

## 计划中的实际改动

会对 `skills/ahe-finalize/SKILL.md` 做一轮聚焦增强，预计包括：

- 增加 gate 证据优先读取
- 增加 profile-aware 证据矩阵
- 补强文档一致性检查
- 输出升级为 delivery / handoff pack
- 收紧 `task-progress.md` 字段与 canonical handoff
- 增加 finalize 的硬边界与可选使用说明

## 预期效果

优化后的 `ahe-finalize` 应该具备这些特征：

- 不只是“写个总结”，而是能真正收住一轮 AHE 工作周期
- 更少出现证据在盘里、但 finalize 没有把它们串起来的情况
- 更容易让下一次会话或下一位执行者无须猜测地继续
- 与 completion / regression / review 链条的落盘契约更一致
