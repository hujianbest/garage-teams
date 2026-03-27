# My Skills 名称与职责清单

这个文档用于统一查看 `my-skills` 下各个 skill 的当前名称与职责。

你可以直接修改“拟改名”这一列；改完后告诉我，我会基于你修改后的命名继续调整对应 skill 内容。

## 使用说明

- 只需要改“拟改名”列即可。
- 如果你也想顺手调整职责描述，可以直接改“职责”列。
- 改完后告诉我具体是这个文件已更新，我会继续按你的命名进行后续修改。

## 清单


| 目录                     | 当前 skill 名称            | 拟改名                    | 职责                                                       |
| ---------------------- | ---------------------- | ---------------------- | -------------------------------------------------------- |
| `mdc-workflow-starter` | `sdd-workflow-starter` | `mdc-workflow-starter` | 在任何 SDD 软件交付请求开始时，先识别当前所处阶段，并把工作路由到正确的下一步 skill，避免跳阶段执行。 |
| `mdc-specify`          | `sdd-work-specify`     | `mdc-specify`          | 负责产出需求规格说明，明确要做什么、给谁做、范围边界、约束、验收标准与非目标内容。                |
| `mdc-spec-review`      | `sdd-spec-review`      | `mdc-spec-review`      | 负责审核需求规格说明是否完整、清晰、可测试、可进入设计阶段。                           |
| `mdc-design`           | `sdd-work-design`      | `mdc-design`           | 基于已批准的需求规格，产出实现设计，明确架构、模块边界、接口、数据流、技术决策与测试策略。            |
| `mdc-design-review`    | `sdd-design-review`    | `mdc-design-review`    | 负责审核实现设计是否覆盖需求、架构一致、接口清晰，并足以支撑任务拆解。                      |
| `mdc-tasks`            | `sdd-work-tasks`       | `mdc-tasks`            | 将已批准的设计拆解成可执行任务计划，明确里程碑、依赖、完成条件和验证方式。                    |
| `mdc-tasks-review`     | `sdd-tasks-review`     | `mdc-tasks-review`     | 负责审核任务计划是否粒度合适、顺序合理、依赖正确、可验证，并可进入实现阶段。                   |
| `mdc-implement`        | `sdd-work-implement`   | `mdc-implement`        | 按已批准任务计划逐项实现，遵循一次一个任务、TDD、评审与验证闭环，不得跳步。                  |
| `mdc-bug-patterns`     |                        | `mdc-bug-patterns`     | 负责基于团队历史错误案例和常见缺陷模式，对当前实现进行专项排查，补充风险防护与针对性验证。         |
| `mdc-test-review`      | `sdd-test-review`      | `mdc-test-review`      | 负责审核当前任务相关测试是否真正验证行为、是否体现 fail-first、覆盖是否有意义。            |
| `mdc-code-review`      | `sdd-code-review`      | `mdc-code-review`      | 负责审核当前任务实现代码的正确性、可维护性、错误处理与设计一致性。                        |
| `mdc-traceability-review` |                     | `mdc-traceability-review` | 负责检查规格、设计、任务、实现、测试与验证证据之间是否仍然一致，防止设计漂移和无记录偏离。      |
| `mdc-regression-gate`  | `sdd-regression-gate`  | `mdc-regression-gate`  | 负责执行回归门禁，确认当前改动没有破坏相关行为、构建、类型检查或集成面。                     |
| `mdc-completion-gate`  | `sdd-completion-gate`  | `mdc-completion-gate`  | 负责在宣告任务完成前检查是否有最新、直接、足够的验证证据支持完成结论。                      |
| `mdc-finalize`         | `sdd-work-finalize`    | `mdc-finalize`         | 在当前工作项通过完成门禁后，负责更新进度记录、发布说明、验证证据与下一步交接信息。                |
| `mdc-increment`        | `sdd-work-increment`   | `mdc-increment`        | 处理需求变更请求，分析其对规格、设计、任务计划、验证策略和已实现内容的影响，并同步刷新受影响工件后路由回正确阶段。 |
| `mdc-hotfix`           | `sdd-work-hotfix`      | `mdc-hotfix`           | 处理紧急缺陷修复，在保证先复现、最小修复、回归验证和完成门禁的前提下完成热修复。                 |


