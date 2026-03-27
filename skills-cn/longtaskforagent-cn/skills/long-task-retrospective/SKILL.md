---
name: long-task-retrospective
description: "在 ST 判定为 Go 且存在回顾记录且用户已授权反馈时使用 — 汇总记录并通过 REST API POST 上报"
---

# 回顾报告 — 汇总并上传 Skill 改进记录

由 `long-task-st` 第 12.5 步在 Go 判定之后、当存在回顾记录且已授权反馈时条件调用。本 skill 汇总已收集的记录并上传至配置的 REST API 端点。

**开始时宣告：**「我正在使用 long-task-retrospective skill，准备上报 Skill 改进记录。」

**核心原则：** 本 skill 仅负责上报 — **不修改** skill 文件。改进记录上传供分析与后续可能纳入新版 skill。

## 检查清单

### 1. 门禁检查

须同时满足：

**a) 授权：**
- 读取 `feature-list.json` — 检查 `retro_authorized` 字段
- 若缺失或为 `false` → 打印「Retrospective: not authorized — skipping」→ **停止**

**b) 服务可达：**
```bash
python scripts/check_retro_auth.py feature-list.json
```
- 退出码 0（就绪）→ 继续
- 退出码 1（不可用）→ 打印「Retrospective: endpoint unavailable — skipping」→ **停止**
- 退出码 2（未配置）→ 打印「Retrospective: no endpoint configured — skipping」→ **停止**

### 2. 读取记录

读取全部 `docs/retrospectives/*.md`（排除 `reported/` 子目录）：

```bash
python scripts/check_retrospective_readiness.py
```

对每条记录校验：
```bash
python scripts/validate_retrospective_record.py docs/retrospectives/<file>.md
```

- 有效记录 → 纳入报告
- 无效记录 → 记录警告，不参与上传

### 3. 摘要

根据记录 frontmatter 汇总统计：
- 总记录数（仅有效）
- 按严重程度：critical / important / minor
- 按类别：skill-gap / missing-rule / false-assumption / template-defect / process-gap
- 按分类：systemic / one-off

向用户展示摘要。

### 4. 用户确认

使用 `AskUserQuestion`：
```
"本项目共搜集 {N} 条 Skill 改进记录（critical: {X}, important: {Y}, minor: {Z}）。
 其中系统性问题 {S} 条，一次性问题 {O} 条。是否上报到 {endpoint}？"

Options: "确认上报 (Recommended)" / "跳过本次上报"
```

- 用户选择「跳过」→ 打印「Retrospective: user skipped upload」→ **停止**
- 用户选择「确认上报」→ 继续

### 5. 上传

```bash
python scripts/post_retrospective_report.py --feature-list feature-list.json
```

脚本将：
1. 将 `docs/retrospectives/*.md` 压缩为 `retrospectives.tar.gz`
2. 以 multipart/form-data POST 到已配置端点
3. 附带元数据：项目名称、日期、分支、记录条数

- 退出码 0 → 打印「Retrospective: {N} records uploaded successfully」
- 退出码 1 → 打印错误，**不要重试** — 将失败告知用户

### 6. 清理

- 将已上传记录移至 `docs/retrospectives/reported/`（审计留痕）
- Git 提交：`retro: upload {N} skill improvement records`
- 在 `task-progress.md` 中写入回顾条目

## 关键规则

- **不得修改 skill 文件** — 本 skill 仅收集与上报
- **门禁不可绕过** — 授权与服务可达须同时通过
- **须用户明确同意** — 未经用户确认不得上传
- **隐私优先** — 记录不得包含项目源码、业务数据或凭证
- **每个 ST 周期至多一次上传** — 不得在 Worker 会话中分批上传
- **失败不阻塞** — 上传失败不影响 ST 判定

## 集成

**调用方：** `long-task-st`（第 12.5 步，Persist 之后、Verdict 之前）  
**需要：** `feature-list.json` 中 `retro_authorized` = true 且端点可达  
**读取：** `docs/retrospectives/*.md`、`feature-list.json`  
**产出：** 将记录移至 `docs/retrospectives/reported/`  
**脚本：** `check_retro_auth.py`、`check_retrospective_readiness.py`、`validate_retrospective_record.py`、`post_retrospective_report.py`
