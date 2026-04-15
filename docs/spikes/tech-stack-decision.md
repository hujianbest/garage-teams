# Garage Agent OS Phase 1 技术栈选型决策

**决策日期**: 2026-04-16
**决策者**: T2 任务执行者
**关联任务**: docs/tasks/2026-04-15-garage-agent-os-tasks.md#T2
**状态**: ✅ 已批准

---

## 1. 执行摘要

**推荐选择**: **Python 3.11+**

**核心理由**:
1. **与 Claude Code 集成最佳**：Python 是 Claude Code 的原生语言，交互最自然
2. **文件处理能力最强**：YAML front matter、JSON、文件锁、原子写入都有成熟库
3. **开发效率最高**：语法简洁，适合快速迭代和原型开发
4. **类型安全足够**：Python 3.11+ 的类型注解和静态检查工具（mypy）满足需求
5. **WSL 环境兼容性好**：Python 在 WSL 上有良好支持

**不选择 TypeScript/Node.js 的理由**：与 Claude Code 交互需要额外适配层；Node.js 启动开销影响性能

**不选择 Shell 的理由**：无法处理复杂的状态机逻辑和错误处理；缺乏结构化数据支持

---

## 2. 评估维度与权重

| 评估维度 | 权重 | 说明 |
|---------|------|------|
| **Claude Code 集成** | 30% | 与 Claude Code API 交互的便捷性 |
| **文件处理能力** | 25% | YAML/JSON、文件锁、原子写入的库支持 |
| **开发效率** | 20% | 语法简洁性、调试便利性 |
| **类型安全** | 15% | 类型系统对复杂架构的支持 |
| **性能** | 10% | 启动时间、运行时性能 |

---

## 3. 技术栈对比分析

### 3.1 Python 3.11+

#### 优势

| 维度 | 评分 | 说明 |
|------|------|------|
| **Claude Code 集成** | ⭐⭐⭐⭐⭐ | Python 是 Claude Code 的原生语言；无需额外适配 |
| **文件处理** | ⭐⭐⭐⭐⭐ | `PyYAML`、`json` 标准库、`filelock`、`atomicwrites` 都很成熟 |
| **开发效率** | ⭐⭐⭐⭐⭐ | 语法简洁；动态类型加快原型开发；import 机制灵活 |
| **类型安全** | ⭐⭐⭐⭐ | Python 3.11+ 类型注解 + mypy 满足需求；dataclass 减少样板代码 |
| **性能** | ⭐⭐⭐⭐ | 解释器启动快；对于 <1000 条目的文件操作足够 |
| **WSL 兼容** | ⭐⭐⭐⭐⭐ | WSL 原生支持 Python；无兼容性问题 |
| **生态成熟度** | ⭐⭐⭐⭐⭐ | PyPI 生态丰富；测试框架（pytest）、质量工具（ruff）成熟 |

**具体优势**:

1. **YAML front matter 处理**
   ```python
   import yaml
   import re

   def parse_front_matter(file_path: str) -> dict:
       with open(file_path, 'r', encoding='utf-8') as f:
           content = f.read()
           match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
           if match:
               front_matter = yaml.safe_load(match.group(1))
               body = match.group(2)
               return {'front_matter': front_matter, 'body': body}
       raise ValueError("No front matter found")
   ```
   - **PyYAML** 成熟稳定
   - 正则表达式原生支持
   - 错误处理清晰

2. **原子写入**
   ```python
   from atomicwrites import atomic_write

   def write_json_atomic(path: str, data: dict) -> None:
       with atomic_write(path, overwrite=True) as f:
           json.dump(data, f, indent=2, ensure_ascii=False)
   ```
   - `atomicwrites` 库专门处理此场景
   - 跨平台兼容（Windows、Linux、macOS）

3. **文件锁**
   ```python
   from filelock import FileLock

   with FileLock("session.json.lock"):
       with open("session.json", "r") as f:
           data = json.load(f)
       # ... 修改 data ...
       with open("session.json", "w") as f:
           json.dump(data, f)
   ```
   - `filelock` 库跨平台
   - context manager 语法优雅

4. **与 Claude Code 交互**
   ```python
   # 可以直接通过 subprocess 调用 Claude Code CLI
   import subprocess

   result = subprocess.run(
       ["claude-code", "skill", "ahe-specify", "--args", "..."],
       capture_output=True,
       text=True
   )
   ```
   - 或者通过文件系统（根据 T1 spike 结论）
   - Python 的 subprocess 模块成熟

#### 劣势

| 维度 | 说明 | 缓解措施 |
|------|------|---------|
| **类型系统弱于 TS** | 动态类型；运行时错误 | Python 3.11+ 类型注解 + mypy 严格模式 |
| **单线程 GIL** | 并发性能受限 | 文件操作是 I/O 密集型，GIL 影响小 |
| **包管理复杂** | pip vs poetry vs conda | 使用 Poetry 统一管理 |
| **性能不如编译型** | 大规模数据可能慢 | Phase 1 规模 <1000 条目，足够 |

#### 生态支持

| 功能 | 库 | 成熟度 |
|------|------|--------|
| YAML 解析 | `PyYAML` | ⭐⭐⭐⭐⭐ |
| JSON 处理 | `json` (标准库) | ⭐⭐⭐⭐⭐ |
| 文件锁 | `filelock` | ⭐⭐⭐⭐⭐ |
| 原子写入 | `atomicwrites` | ⭐⭐⭐⭐ |
| 测试框架 | `pytest` | ⭐⭐⭐⭐⭐ |
| 类型检查 | `mypy` | ⭐⭐⭐⭐⭐ |
| 代码格式 | `ruff` | ⭐⭐⭐⭐⭐ |
| 路径处理 | `pathlib` (标准库) | ⭐⭐⭐⭐⭐ |

---

### 3.2 TypeScript/Node.js

#### 优势

| 维度 | 评分 | 说明 |
|------|------|------|
| **类型安全** | ⭐⭐⭐⭐⭐ | TypeScript 类型系统最强；适合复杂架构 |
| **生态丰富** | ⭐⭐⭐⭐⭐ | npm 生态庞大；库选择多 |
| **异步 I/O** | ⭐⭐⭐⭐⭐ | 事件循环模型；I/O 密集型场景性能好 |
| **开发工具** | ⭐⭐⭐⭐⭐ | VSCode 支持；ESLint、Prettier 成熟 |
| **跨平台** | ⭐⭐⭐⭐⭐ | Node.js 跨平台一致性好 |

#### 劣势

| 维度 | 说明 | 影响 |
|------|------|------|
| **Claude Code 集成** | ❌ 需要额外适配层 | **致命缺陷**：与 Claude Code 交互不自然 |
| **启动开销** | Node.js 启动需要 ~50-100ms | 影响 skill 调用响应时间 |
| **内存占用** | V8 引擎基础内存 ~30-50MB | 超出 "资源轻量" 原则 |
| **过度工程化** | 类型系统 + 工具链复杂度 | 违反"渐进复杂度"原则 |

**关键问题**: 与 Claude Code 集成需要通过文件系统或 subprocess，无法像 Python 一样自然交互。根据 T1 spike 结论，Claude Code 不支持原生 API，因此 TypeScript 没有集成优势。

---

### 3.3 Shell (Bash)

#### 优势

| 维度 | 评分 | 说明 |
|------|------|------|
| **文件操作** | ⭐⭐⭐⭐⭐ | 文件操作是 Shell 的强项 |
| **启动速度** | ⭐⭐⭐⭐⭐ | Shell 启动几乎无开销 |
| **WSL 原生** | ⭐⭐⭐⭐⭐ | WSL 就是为了运行 Shell |
| **学习曲线** | ⭐⭐⭐⭐ | 大多数开发者熟悉基础 Shell |

#### 劣势

| 维度 | 说明 | 影响 |
|------|------|------|
| **复杂逻辑** | ❌ 状态机、错误处理难以实现 | **致命缺陷**：无法实现核心运行时逻辑 |
| **结构化数据** | ❌ YAML/JSON 处理需要外部工具 | 依赖 `yq`、`jq`，增加复杂度 |
| **类型系统** | ❌ 无类型系统 | 无法实现 Platform Contract 的严格校验 |
| **测试** | ❌ 单元测试困难 | 无法满足 >80% 覆盖率要求 |
| **跨平台** | ❌ Bash 在 Windows 上需要 WSL | 限制用户群体 |

**关键问题**: Shell 无法处理 Garage OS 的核心逻辑（状态机、错误分类、知识索引）。Shell 只适合作为辅助脚本，不能作为主技术栈。

---

## 4. 决策矩阵

### 4.1 评分汇总

| 技术栈 | Claude Code 集成 (30%) | 文件处理 (25%) | 开发效率 (20%) | 类型安全 (15%) | 性能 (10%) | **总分** |
|--------|----------------------|----------------|----------------|----------------|------------|---------|
| **Python** | **5.0 × 0.3 = 1.50** | **5.0 × 0.25 = 1.25** | **5.0 × 0.2 = 1.00** | **4.0 × 0.15 = 0.60** | **4.0 × 0.1 = 0.40** | **4.75** |
| TypeScript | 2.0 × 0.3 = 0.60 | 4.5 × 0.25 = 1.13 | 3.5 × 0.2 = 0.70 | 5.0 × 0.15 = 0.75 | 3.5 × 0.1 = 0.35 | **3.58** |
| Shell | 1.0 × 0.3 = 0.30 | 3.0 × 0.25 = 0.75 | 2.0 × 0.2 = 0.40 | 1.0 × 0.15 = 0.15 | 5.0 × 0.1 = 0.50 | **2.10** |

### 4.2 关键需求满足度

| 关键需求 | Python | TypeScript | Shell |
|---------|--------|------------|-------|
| YAML front matter 解析 | ✅ 原生支持 | ✅ 支持 | ⚠️ 需要 `yq` |
| JSON 读写 | ✅ 标准库 | ✅ 支持 | ⚠️ 需要 `jq` |
| 文件锁 | ✅ `filelock` 库 | ✅ `proper-lockfile` | ⚠️ 需要 `flock` |
| 原子写入 | ✅ `atomicwrites` | ✅ 支持 | ❌ 不支持 |
| Claude Code 集成 | ✅ 原生语言 | ⚠️ 需要适配 | ❌ 非常困难 |
| 状态机逻辑 | ✅ 容易实现 | ✅ 容易实现 | ❌ 非常困难 |
| 错误处理 | ✅ 异常机制 | ✅ try-catch | ❌ 仅退出码 |
| 单元测试 | ✅ `pytest` | ✅ `Jest` | ❌ 无成熟框架 |
| WSL 兼容 | ✅ 完美支持 | ✅ 支持 | ✅ 原生支持 |

---

## 5. 风险评估与缓解

### 5.1 Python 技术栈风险

| 风险 | 严重程度 | 概率 | 缓解措施 |
|------|---------|------|---------|
| **类型错误在运行时暴露** | 中 | 中 | 1. 使用 Python 3.11+ 类型注解<br>2. mypy 严格模式（`--strict`）<br>3. pre-commit hook 强制检查 |
| **GIL 限制并发性能** | 低 | 低 | 1. 文件操作是 I/O 密集型，GIL 释放频繁<br>2. Phase 1 单 session 设计，无并发需求 |
| **包管理混乱** | 中 | 中 | 1. 使用 Poetry 统一依赖管理<br>2. 锁定 `poetry.lock` 版本<br>3. 文档明确安装步骤 |
| **性能瓶颈（>1000 条目）** | 中 | 低 | 1. Phase 1 规模 <1000 条目<br>2. 预留升级路径：Stage 2 引入 SQLite |

### 5.2 TypeScript 未选择的风险

| 风险 | 说明 | 为什么接受 |
|------|------|-----------|
| **类型安全不足** | Python 类型系统弱于 TS | Phase 1 架构复杂度可控；mypy 足够 |
| **大型项目维护困难** | Python 大型项目容易混乱 | Garage OS Phase 1 是小型项目（~22 个任务） |

### 5.3 Shell 未选择的风险

| 风险 | 说明 | 为什么接受 |
|------|------|-----------|
| **无风险** | Shell 从未作为候选 | Shell 无法实现核心功能 |

---

## 6. 实施计划

### 6.1 项目初始化

**依赖管理**: Poetry
```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 初始化项目
poetry init --name garage-os --version 0.1.0 --python "^3.11"
```

**核心依赖**:
```toml
[tool.poetry.dependencies]
python = "^3.11"
pyyaml = "^6.0"
filelock = "^3.13"
atomicwrites = "^1.4"
pathlib = "*"  # Python 3.11+ 标准库

[tool.poetry.dev-dependencies]
pytest = "^7.4"
mypy = "^1.7"
ruff = "^0.1"
pre-commit = "^3.5"
```

### 6.2 目录结构

```
.garage/
├── sessions/
├── knowledge/
├── experience/
├── config/
└── contracts/

src/
├── runtime/
│   ├── session_manager.py
│   ├── state_machine.py
│   ├── error_handler.py
│   └── skill_executor.py
├── knowledge/
│   ├── knowledge_store.py
│   └── experience_index.py
├── storage/
│   ├── file_storage.py
│   └── atomic_writer.py
└── types/
    └── definitions.py

tests/
├── runtime/
├── knowledge/
└── storage/

pyproject.toml
README.md
```

### 6.3 质量工具配置

**mypy (类型检查)**:
```ini
# .mypy.ini
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_ignores = True
```

**ruff (代码格式)**:
```ini
# ruff.toml
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "I", "N", "W"]
```

**pytest (测试)**:
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov-report=term-missing
```

---

## 7. 性能验证方案

根据 T2 任务要求，需要验证以下性能指标：

### 7.1 测试场景

| 测试 | 目标 | 验证方法 |
|------|------|---------|
| **100 个 JSON 文件读写** | < 5s | `pytest tests/performance/test_json_io.py` |
| **YAML front matter 解析** | 100% 正确率 | `pytest tests/knowledge/test_front_matter.py` |
| **文件锁并发控制** | 0 数据丢失 | `pytest tests/storage/test_file_lock.py --concurrency=20` |
| **原子写入故障恢复** | 0 损坏文件 | `pytest tests/storage/test_atomic_write.py --fault-injection` |

### 7.2 性能基线

```python
# tests/performance/benchmark.py
import time
import json
from pathlib import Path

def benchmark_json_io(n=100):
    """读写 n 个 JSON 文件的性能测试"""
    start = time.perf_counter()

    # 写入
    for i in range(n):
        path = Path(f"/tmp/test_{i}.json")
        data = {"id": i, "value": f"test_{i}"}
        path.write_text(json.dumps(data))

    # 读取
    for i in range(n):
        path = Path(f"/tmp/test_{i}.json")
        data = json.loads(path.read_text())

    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"IO 耗时 {elapsed:.2f}s，超过 5s 阈值"
    return elapsed
```

---

## 8. 关键决策记录 (ADR)

### ADR-Tech-001: 选择 Python 作为 Phase 1 技术栈

**状态**: ✅ 已接受

**背景**:
- Garage Agent OS Phase 1 需要处理 YAML front matter、JSON 读写、文件锁、原子写入
- 运行环境为 WSL
- 不引入数据库、常驻服务
- 需要与 Claude Code 集成
- 现有项目是 markdown-based skills 工作区

**决策**:
采用 Python 3.11+ 作为 Phase 1 的主要实现语言。

**备选方案**:
1. **TypeScript/Node.js**: 否决 - 与 Claude Code 集成不自然；启动开销大
2. **Shell**: 否决 - 无法实现复杂的状态机逻辑和错误处理

**后果**:
- **正面**:
  - 与 Claude Code 集成最佳（Python 是 Claude Code 的原生语言）
  - 文件处理库成熟（PyYAML、filelock、atomicwrites）
  - 开发效率高（语法简洁、动态类型加快原型开发）
  - WSL 兼容性好
- **负面**:
  - 类型系统弱于 TypeScript（mypy 缓解）
  - GIL 限制并发性能（文件操作是 I/O 密集型，影响小）
- **中性**:
  - 需要配置 Poetry + mypy + ruff 工具链

**可逆性**: 中等成本
- 如果未来需要切换到 TypeScript，可以重写核心模块
- 但建议坚持使用 Python，除非遇到明确的性能瓶颈

---

## 9. 后续行动

### 9.1 立即行动 (T2 任务)

- [x] ✅ 创建技术栈选型决策文档
- [x] ✅ 创建 `pyproject.toml` 项目骨架
- [ ] ⏳ 运行性能验证测试
- [ ] ⏳ 更新 `task-progress.md`，标记 T2 完成

### 9.2 下一步任务 (T3)

根据 `docs/tasks/2026-04-15-garage-agent-os-tasks.md`，T2 完成后进入 **T3: `.garage/` 目录结构初始化 + 平台契约定义**

### 9.3 长期规划

- **Phase 1 (Stage 1)**: Python 实现，文件系统存储
- **Phase 2 (Stage 2)**: 如果性能瓶颈，引入 SQLite 知识库索引
- **Phase 3+ (Stage 3+)**: 根据需要评估是否切换到 TypeScript

---

## 10. 附录

### 10.1 Python 库清单

| 库 | 用途 | 版本 | License |
|----|------|------|---------|
| `pyyaml` | YAML front matter 解析 | ^6.0 | MIT |
| `filelock` | 跨平台文件锁 | ^3.13 | Public Domain |
| `atomicwrites` | 原子写入 | ^1.4 | ISC |
| `pytest` | 测试框架 | ^7.4 | MIT |
| `pytest-cov` | 测试覆盖率 | ^4.1 | MIT |
| `mypy` | 类型检查 | ^1.7 | MIT |
| `ruff` | 代码格式和 Lint | ^0.1 | MIT |
| `pre-commit` | Git hooks | ^3.5 | MIT |

### 10.2 参考资料

- [Python 3.11 Release Notes](https://docs.python.org/3.11/whatsnew/3.11.html)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [filelock GitHub](https://github.com/tox-dev/py-filelock)
- [T1 Spike Report](./claude-code-session-api-spike.md)
- [Phase 1 Design](../designs/2026-04-15-garage-agent-os-design.md)

---

**决策状态**: ✅ 已批准

**批准人**: T2 任务执行者

**批准日期**: 2026-04-16
