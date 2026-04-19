# Test Design Approval - F004 T4

- Task: T4 — `SessionManager._trigger_memory_extraction_safely` 三 phase 持久化
- Approval Type: `testDesignApproval`
- Approver: cursor cloud agent (auto-mode self-approval)
- Date: 2026-04-19
- Workflow Profile / Execution Mode: `full` / `auto`
- Workspace Isolation: `in-place`
- 关联任务计划: `docs/tasks/2026-04-19-garage-memory-v1-1-tasks.md` § T4
- 关联设计: `docs/designs/2026-04-19-garage-memory-v1-1-design.md` § 10.4 + § 11.3 + § 11.4 + ADR-404
- 上游依赖: 无（T4 与 T1/T2/T3 解耦）

## 测试设计

### Fail-first 测试（RED 阶段必须先失败）

1. **`test_archive_session_persists_extraction_error_orchestrator_init`** — monkeypatch `MemoryExtractionOrchestrator.__init__` 抛错；断言 `archive_session()` 返回 True；磁盘 `sessions/archived/<id>/memory-extraction-error.json` 存在；`phase="orchestrator_init"` + `error_type` + `error_message`。**预期失败原因**：当前 `_trigger_memory_extraction` 没有为 orchestrator 实例化路径加专门 try/except 写文件；只有 `extract_for_archived_session` 调用周围的 try/except 走 logger.warning。
2. **`test_archive_session_persists_extraction_error_enablement_check`** — monkeypatch `is_extraction_enabled` 抛错；断言文件存在 + `phase="enablement_check"`。**预期失败原因**：当前实现 `is_extraction_enabled` 在 try 之外调用，会让异常逃出函数。
3. **`test_archive_session_persists_extraction_error_extraction`** — monkeypatch `extract_for_archived_session` 抛错；断言文件存在 + `phase="extraction"`。**预期失败原因**：当前 try/except 只 logger.warning，不写文件。

### 关键边界覆盖

4. **`test_archive_session_no_error_file_when_extraction_succeeds`** — 不 monkeypatch；正常 happy path；断言 archive 后 `memory-extraction-error.json` **不存在**。
5. **`test_archive_session_no_error_file_when_extraction_disabled`** — `extraction_enabled=false` 路径；断言文件不存在；不抛错。
6. **`test_memory_extraction_error_json_has_full_schema`** — 任意失败 phase 触发后，文件含 6 个 schema 字段（`schema_version`, `session_id`, `phase`, `error_type`, `error_message`, `triggered_at`）。

### Mock 边界

- 用 `monkeypatch.setattr` 在测试范围内替换 `MemoryExtractionOrchestrator` 的方法
- 不 mock storage / SessionManager 本身 — 用 `tmp_path` fixture
- session 必须先 `start_session(...)` → `update_session(state="completed")` → `archive_session(...)`，让 `_trigger_memory_extraction` 触发

### 与任务计划测试种子的差异

完全一致；6 个种子 1:1 实现。

## RED→GREEN→REFACTOR 计划

1. **RED**：写 6 个测试 → 至少 3 个失败
2. **GREEN**：
   - 重构 `_trigger_memory_extraction`：
     - phase 1 (`orchestrator_init`)：把 orchestrator 实例化包在 try/except，失败 → `_persist_extraction_error(session_id, "orchestrator_init", exc)` + return
     - phase 2 (`enablement_check`)：把 `is_extraction_enabled()` 包在 try/except，失败 → `_persist_extraction_error(...)` + return；返回 False → 直接 return（不写文件）
     - phase 3 (`extraction`)：把 `extract_for_archived_session(...)` 包在 try/except，失败 → `_persist_extraction_error(...)` + return（保留现有 logger.warning 作为双层防护）
   - 新增 `_persist_extraction_error(session_id, phase, exc)`：
     - 写 `sessions/archived/<id>/memory-extraction-error.json`，含 6 个字段
     - 用 `FileStorage.write_json`
3. **REFACTOR**：
   - 抽出常量 `MEMORY_EXTRACTION_ERROR_FILENAME = "memory-extraction-error.json"`
   - 三 phase 异常处理代码结构对齐
   - 不引入新依赖

## Auto-mode self-approval rationale

- 测试设计完全在 design § 10.4 + § 11.3 + § 11.4 + ADR-404 范围内
- 6 个测试名 1:1 映射 task plan T4 测试种子 + design schema
- 不存在 USER-INPUT 类决策点

## Decision

**Approved**. T4 RGR 可立即开始。
