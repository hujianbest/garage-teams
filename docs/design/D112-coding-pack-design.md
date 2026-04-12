# D112: Coding Pack Design

- Design ID: `D112`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: 展开 `Coding` 作为 `Garage Team` 能力面的具体设计。
- 关联文档:
  - `docs/design/D11-reference-pack-designs.md`
  - `docs/features/F15-pack-platform-and-collaboration.md`
  - `docs/features/F16-execution-and-provider-tool-plane.md`

## 1. 设计目标

- 定义 coding agents / roles / outputs
- 说明它如何与 execution、review 和 bridge 主线结合

## 2. 主要工作对象

`Coding` pack 主要处理：

- implementation goals
- code changes
- verification work
- closeout-ready outputs

## 3. 最小角色面

至少应存在这些 team-facing roles：

- 实现角色
- 复查 / reviewer 角色
- closeout / closer 角色

## 4. 最小输出面

至少应产生可被系统消费的：

- implementation artifacts
- verification outputs
- review / approval supporting evidence
- closeout-ready outputs

## 5. execution 与 bridge 结合

- Coding pack 明确依赖 shared execution plane
- Coding pack 通过 shared bridge seam 接收外部能力面的 handoff
- Coding pack 不拥有 provider authority，只声明需要什么 capability

## 6. 非目标

- 不把 Coding pack 设计成平台本身
- 不让它直接定义 provider/vendor truth
- 不让它私有化 review 或 bridge 语义

## 7. 设计完成标准

- coding roles / outputs / verification hooks 清楚
- 与 shared execution、review、bridge 的关系清楚
- 下游 implementation task 不再需要猜 coding pack 的最小能力面
