# Garage Mainline Task Board

- Source Task Plan: `docs/tasks/2026-04-13-garage-mainline-tasks.md`
- Workflow Profile: `full`
- Execution Mode: `auto`
- Current Active Task: T101

## Task Queue

| Task ID | Status | Depends On | Ready When | Selection Priority |
| --- | --- | --- | --- | --- |
| T101 | in_progress | - | tasks plan approved | P1 |
| T103 | pending | T101 | T101=`done` | P2 |
| T102 | pending | T103 | T103=`done` | P3 |
| T111 | pending | T102 | T102=`done` | P4 |
| T112 | pending | T111 | T111=`done` | P5 |
| T113 | pending | T112 | T112=`done` | P6 |
| T121 | pending | T113 | T113=`done` | P7 |
| T122 | pending | T121 | T121=`done` | P8 |
| T131 | pending | T122 | T122=`done` | P9 |
| T132 | pending | T131 | T131=`done` | P10 |
| T141 | pending | T132 | T132=`done` | P11 |
| T142 | pending | T141 | T141=`done` | P12 |
| T143 | pending | T142 | T142=`done` | P13 |
| T151 | pending | T143 | T143=`done` | P14 |
| T152 | pending | T151 | T151=`done` | P15 |
| T153 | pending | T152 | T152=`done` | P16 |

## Queue Projection Rules

- 仅当且仅当一个任务满足 `ready` 条件时，router 才可将其锁定为 `Current Active Task`。
- 当 `Tn=done` 时，若 `Tn+1` 依赖满足，则将 `Tn+1` 从 `pending` 投影为 `ready`。
- 若任何时刻出现多个 `ready` 或依赖冲突，停止自动推进并回到 `ahe-workflow-router`。
