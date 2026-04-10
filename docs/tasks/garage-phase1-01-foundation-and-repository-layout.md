# Garage Phase 1 01 Foundation And Repository Layout

- 状态: 待执行
- 日期: 2026-04-11
- 定位: 把 `Garage` 的 phase 1 设计先落成可开发的仓库骨架，冻结实现边界、目录归属、入口规则和与现有 AHE 资产的关系。
- 当前阶段: phase 1
- 关联设计文档:
  - `docs/garage/README.md`
  - `docs/garage/garage-extensible-architecture.md`
  - `docs/garage/garage-core-subsystems-architecture.md`
  - `docs/garage/garage-phase1-reference-packs.md`

## 1. 任务目标

在真正写 core、contracts 和 packs 之前，先把 phase 1 的实现边界固定下来：

- 哪些目录属于 `Garage Core`
- 哪些目录属于 shared contracts
- 哪些目录属于 reference packs
- 现有 `ahe-*` 资产在 phase 1 中扮演什么角色

## 2. 输入设计文档

这一篇主要承接：

- `Garage` 的总架构
- core 与 pack 的层级边界
- phase 1 只先做两个 reference packs 的收敛判断

## 3. 本文范围

本文只拆下面这些执行任务：

- phase 1 代码与文档骨架目录
- `Garage Core`、contracts、packs 的归属边界
- 入口索引与阅读入口
- 与现有 AHE assets 的映射关系

## 4. 非目标

- 不实现 core runtime objects
- 不实现 contracts 校验器
- 不实现 session lifecycle
- 不实现 pack 内部节点流

## 5. 交付物

- 一套稳定的 phase 1 仓库骨架
- 一份清晰的目录归属说明
- `Garage` 与现有 `ahe-*` 资产的边界说明
- 主入口文档的索引更新

## 6. 实施任务拆解

### 6.1 冻结 phase 1 实现边界

- 为 `Garage Core`、shared contracts、reference packs、host adapter stubs 预留明确实现区域。
- 明确哪些目录是 phase 1 的新增实现面，哪些目录仍是现有 AHE 资产面。
- 明确 `artifacts / evidence / sessions / archives / .garage` 在实现期的主事实面角色。

### 6.2 搭最小仓库骨架

- 创建 phase 1 需要的最小目录骨架或占位入口。
- 保证 core、pack、host 三类内容不混放。
- 保证 pack-specific 文档或资产不被塞回 core 目录。

### 6.3 处理现有 AHE 资产的定位

- 把 `ahe-coding-skills/` 与 `ahe-product-skills/` 明确为当前阶段的重要来源资产，而不是直接等同于 `Garage` runtime。
- 标注哪些内容可以迁移、哪些内容只作为参考、哪些内容后续通过 pack 转译。
- 避免在 phase 1 一开始就做大规模路径重命名。

### 6.4 更新入口文档

- 让 `docs/README.md`、`docs/garage/README.md`、必要时 `README.md` 能正确指向 `Garage` 设计链与 task 链。
- 明确“先读设计，再读任务”的阅读路径。

### 6.5 冻结 phase 1 的留白

- 未来 `writing`、`video`、多 host profile、重型 registry 市场等只保留 seam，不进入首轮实现。
- 对还没有决定的技术细节，写成占位而不是隐式假定。

## 7. 依赖与并行建议

- 这是 `01`，应最先完成。
- 完成后，`02` 和 `03` 可以并行推进。

## 8. 验收与验证

完成这篇任务后，应能回答：

- phase 1 的实现会落在哪些目录
- `Garage Core` 与 packs 的边界是否清楚
- 现有 AHE 资产是来源资产还是目标 runtime
- 后续文档和实现是否已经有稳定落点

## 9. 完成后进入哪一篇

- `docs/tasks/garage-phase1-02-core-runtime-records.md`
- `docs/tasks/garage-phase1-03-shared-contracts-and-registry.md`
