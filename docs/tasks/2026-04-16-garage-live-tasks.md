# F002 任务计划: Garage Live

- 状态: 草稿
- 日期: 2026-04-16
- 关联规格: docs/features/F002-garage-live.md
- 关联设计: docs/designs/2026-04-16-garage-live-design.md

---

## 1. 概述

6 个任务，将 Phase 1 引擎接入真实宿主，完成端到端验证。

---

## 2. 里程碑

| 里程碑 | 目标 | 任务数 |
|--------|------|--------|
| M1: CLI + 真实适配器 | CLI 入口 + ClaudeCodeAdapter 真实调用 | 2 |
| M2: 执行链路 | run 命令 + experience 记录 + knowledge 查询 | 3 |
| M3: E2E 验证 | 真实跑通一个 AHE skill | 1 |

---

## 3. 任务列表

### M1: CLI + 真实适配器

---

### T1. CLI 框架 + init/status 命令

- **目标**: 实现 `garage` CLI 入口，支持 `init` 和 `status` 子命令
- **依赖**: Phase 1
- **Ready When**: Phase 1 = done
- **触碰工件**:
  - `src/garage_os/cli.py`（新建）
  - `pyproject.toml`（修改，添加 scripts 入口）
  - `tests/test_cli.py`（新建）
- **测试设计种子**:
  1. `garage init` → 创建完整 `.garage/` 目录结构
  2. `garage init` 幂等 → 已存在时不报错
  3. `garage status` → 显示知识库统计（条目数、最近 experience）
  4. `garage status` 空仓库 → 显示 "No sessions" 等
  5. 无参数 → 显示 help
  6. 未知命令 → 显示 help
- **完成条件**:
  - `garage init` 和 `garage status` 可正常执行
  - 416+ 测试全部通过

---

### T2. ClaudeCodeAdapter 真实调用

- **目标**: 让 invoke_skill 通过 `claude -p` 真正调用 Claude Code
- **依赖**: Phase 1
- **Ready When**: Phase 1 = done
- **触碰工件**:
  - `src/garage_os/adapter/claude_code_adapter.py`（修改）
  - `tests/adapter/test_host_adapter.py`（修改/新增）
- **测试设计种子**:
  1. invoke_skill 构造正确的 claude -p 命令（mock subprocess）
  2. 调用成功 → 返回 stdout 作为 output
  3. 调用失败（非零退出码）→ 抛出 SkillExecutionError
  4. 超时 → 抛出 SkillExecutionError
  5. skill 不存在 → 抛出 SkillNotFoundError
  6. 已有测试仍通过（mock adapter 不受影响）
- **完成条件**:
  - invoke_skill 通过 subprocess 调用 claude
  - 所有测试通过（mock subprocess，不依赖真实 API）

---

### M2: 执行链路

---

### T3. garage run 命令

- **目标**: 实现 `garage run <skill-name>` 完整执行链路
- **依赖**: T1, T2
- **Ready When**: T1=done AND T2=done
- **触碰工件**:
  - `src/garage_os/cli.py`（更新）
  - `tests/test_cli.py`（更新）
- **测试设计种子**:
  1. `garage run ahe-specify` → 创建 session → 执行 → 写 experience → 归档
  2. 执行成功 → archived session 状态为 completed
  3. 执行失败 → archived session 状态为 failed + 错误信息
  4. 超时参数传递 → adapter 使用指定 timeout
  5. mock 整个执行链路（不依赖真实 claude）
  6. 已归档 session 存在时，下一次 run 的 session id 继续递增
- **完成条件**:
  - run 命令完成 session 全生命周期管理（idle → running → completed/failed → archived）
  - active / archived 路径语义一致，状态转换正确

---

### T4. Experience 自动记录

- **目标**: skill 执行完成后自动写入 experience record
- **依赖**: T3
- **Ready When**: T3=done
- **触碰工件**:
  - `src/garage_os/cli.py`（更新，run 命令添加 experience 记录）
  - `tests/test_cli.py`（更新）
- **测试设计种子**:
  1. 成功执行后 → `.garage/experience/records/` 有新 JSON 文件
  2. experience 包含 skill_name、duration、outcome
  3. 失败执行 → 也记录 experience（outcome=failure）
  4. 多次执行 → 多条 experience
- **完成条件**:
  - 每次 run 自动产生 experience record
  - record 字段完整

---

### T5. knowledge search CLI

- **目标**: 实现 `garage knowledge search/list` 命令
- **依赖**: T1
- **Ready When**: T1=done
- **触碰工件**:
  - `src/garage_os/cli.py`（更新）
  - `tests/test_cli.py`（更新）
- **测试设计种子**:
  1. `garage knowledge search <query>` → 返回匹配的知识条目
  2. `garage knowledge list` → 列出所有知识条目
  3. 空知识库 → 提示 "No knowledge entries"
  4. 格式化输出包含标题、类型、日期
- **完成条件**:
  - search 和 list 命令可用

---

### M3: E2E 验证

---

### T6. 端到端 Demo 验证

- **目标**: 真实跑通一个 AHE skill，验证完整链路
- **依赖**: T3, T4, T5
- **Ready When**: T3=done AND T4=done AND T5=done
- **触碰工件**:
  - 无新文件，纯验证
- **验证步骤**:
  1. `garage init` — 初始化
  2. `garage run ahe-specify` — 真实执行（需要 claude CLI）
  3. `garage status` — 看到 session 归档记录
  4. `garage knowledge list` — 看到知识条目
  5. 验证 `.garage/` 下有真实数据
- **完成条件**:
  - 完整链路跑通
  - `.garage/` 有真实 session 和 experience 数据

---

## 4. 依赖图

```
Phase 1 ──┬──> T1 (CLI框架) ──┬──> T3 (run命令) ──> T4 (experience) ──> T6 (E2E)
          │                    │
          │                    └──> T5 (knowledge)
          │
          └──> T2 (真实Adapter) ──> T3
```

T1 和 T2 可并行，T5 只依赖 T1。
