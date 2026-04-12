# M040: Garage Feature Roadmap

- Document ID: `M040`
- 状态: 草稿
- 日期: 2026-04-11
- 定位: `docs/ROADMAP.md` 维护新的 feature families、它们和 architecture 主线的关系，以及这些 capability docs 当前由哪些任务切片承接。
- 关联文档:
  - `docs/README.md`
  - `docs/VISION.md`
  - `docs/GARAGE.md`
  - `docs/tasks/README.md`

## 1. 这份文档回答什么

这份文档主要回答 3 个问题：

- 新的 `docs/features/` 主线怎么切
- 各 capability family 对应哪些 architecture owner docs
- 当前任务链大致承接了哪些 capability family

它不替代：

- `docs/GARAGE.md` 的产品定义
- `docs/tasks/README.md` 的实施顺序索引
- 每篇 feature 文档自身的详细语义

## 2. 新的 feature 原则

- `docs/features/` 跟随新的 architecture 主线，不再继承旧 `F010-F230` 的切分逻辑。
- 它讲的是稳定 capability families，不是阶段性开发故事。
- 当 feature 语义和 task 语义冲突时，以 `docs/features/` 为准，再回头重切 `docs/tasks/`。
- feature 文档应回答 “系统需要具备什么能力语义”，而不是 “当前代码已经怎么写”。

## 3. 编号规则

新的 `docs/features/` 保留 `F` 前缀，但不再使用单层 `F100-F160` family 规则。

当前主线采用两层结构：

- `F10-F19`：顶层 capability families
- `F101-F199`：对应 family 下的具体 capability specs

也就是说：

- `F10` 负责定义一组 capability family 的边界
- `F101`、`F102`、`F103` 等负责展开该 family 的稳定细项

## 4. 当前 Feature Families

| Family | 作用 | 对应 architecture 主线 | 当前实施切片 |
| --- | --- | --- | --- |
| `F10` | Agent Teams product surface：团队对象、独立工作环境、能力注入层 | `1`、`10` | `T140`、`T150`、`T160` |
| `F11` | Runtime topology and entry bootstrap：runtime home、workspace、bootstrap、SessionApi | `10`、`11`、`101` | `T110`、`T120`、`T140`、`T150`、`T160`、`T170` |
| `F12` | Garage Team runtime core：records、session、handoff、review、registry | `2`、`11`、`102` | `T020`、`T030`、`T040` |
| `F13` | Governance and workspace truth：workspace facts、artifact routing、evidence、gates | `20`、`30`、`104`、`105` | `T040`、`T050`、`T100`、`T110` |
| `F14` | Continuity and growth：memory、skill、GrowthProposal、promotion | `21`、`31`、`106` | `T060`、`T080`、`T090`、`T130` |
| `F15` | Pack platform and collaboration：contracts、packs、registry、bridge | `40`、`41`、`107`、`111` | `T030`、`T070`、`T080`、`T090`、`T100` |
| `F16` | Execution and provider/tool plane：authority、execution、trace、outcomes | `12`、`103` | `T130`、`T170`、`T180`、`T200`、`T201` |

## 5. 当前 Feature Specs

### F10 Agent Teams Product Surface

- `F101` `Garage Team` 作为第一产品对象
- `F102` 独立工作环境入口
- `F103` HostBridge 作为 capability injection

### F11 Runtime Topology And Entry Bootstrap

- `F111` runtime home 与 workspace 拓扑
- `F112` bootstrap 与 runtime profile authority
- `F113` SessionApi 与 shared entry binding

### F12 Garage Team Runtime Core

- `F121` neutral runtime records
- `F122` session lifecycle
- `F123` handoff and review boundaries
- `F124` registry-backed capability discovery

### F13 Governance And Workspace Truth

- `F131` workspace-first facts
- `F132` artifact routing
- `F133` evidence surface
- `F134` governance gates, approval, and archive

### F14 Continuity And Growth

- `F141` evidence to continuity
- `F142` memory
- `F143` skill assets
- `F144` GrowthProposal and promotion

### F15 Pack Platform And Collaboration

- `F151` pack platform
- `F152` shared contracts and schemas
- `F153` pack runtime binding
- `F154` cross-pack bridge

### F16 Execution And Provider Tool Plane

- `F161` provider authority placement
- `F162` tool execution capability surface
- `F163` execution trace
- `F164` evidence-linked execution outcomes

## 6. 阅读顺序

建议这样读：

1. `docs/VISION.md`
2. `docs/GARAGE.md`
3. `docs/architecture/`
4. `docs/features/F10 -> F16`
5. `docs/tasks/README.md`

## 7. Feature 与 Task 的关系

`docs/features/` 负责稳定 capability cuts。  
`docs/tasks/` 负责把这些 capability cuts 按交付顺序拆成 implementation slices。

这意味着：

- 先用 features 理解系统应该具备什么能力
- 再用 tasks 理解当前先交付哪一部分

## 8. 后续 feature 扩展建议

未来新增 feature docs 时，建议继续按两层 capability family 结构扩展，而不是恢复旧的 runtime-first 清单式切法。

优先扩展方向包括：

- 更完整的 WebEntry capability family
- 更细的 host injection / host adapter family
- release / ops / diagnostics family
- 更明确的 runtime update / evolution family

## 9. 一句话总结

新的 `docs/ROADMAP.md` 不再维护旧 `F010-F230` feature map，也不再停留在临时的 `F100-F160` family 规则，而是维护正式的 `F10/F101` 两层 capability 主线，让 features 真正从产品与架构源头推导出来。
