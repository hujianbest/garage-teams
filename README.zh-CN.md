# Garage

[English](README.md) | **中文**

`Garage` 是一个面向 `solo creator` 的开源 `Agent Teams` 工作环境。

在产品层，`Garage` 应该首先被理解为一个让创作者能够直接进入、使用并培养自己 `Garage Team` 的工作环境。在系统层，它仍然是一个共享 runtime，但这个 runtime 的意义是支撑一个可直接使用的产品，而不是只服务开发者手工集成的基础设施。

它围绕一个核心判断设计：**one runtime, many entry surfaces**。`Garage` 应该先作为独立的 CLI / Web 工作环境成立，再把自己的 agents、skills 和长期能力注入到用户已经在使用的工具里，例如 `Claude`、`OpenCode` 或 `Cursor`。

当前仓库已经包含：

- 可运行的 `garage` CLI shell
- 最小可用的 local-first Web control plane
- 面向 `Claude` / `OpenCode` / `Cursor` 一类集成的共享 host-bridge seam
- 基于 `runtime home` 的 profile loading 与 authority resolution
- 落在 `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` 下的 file-backed workspace surfaces

但它仍然是一个持续演进中的产品环境，不是已经完成打磨的终端产品。核心方向已经稳定，产品深度仍在继续推进。

## Quick Install

环境要求：

- `Python 3.12+`

安装当前开发版：

```bash
python -m pip install -e .
```

安装完成后可用：

```bash
garage --help
```

如果你希望在未安装时，直接从仓库里导入 Python 模块：

```bash
export PYTHONPATH=src
```

PowerShell：

```powershell
$env:PYTHONPATH = "src"
```

## Quick Start

使用 CLI 创建一个新 session：

```bash
garage create \
  --source-root . \
  --runtime-home .runtime-home \
  --workspace-root .workspace \
  --problem-kind implementation \
  --entry-pack coding \
  --entry-node coding.bridge-intake \
  --goal "Bootstrap a Garage session."
```

恢复一个已有 session：

```bash
garage resume \
  --source-root . \
  --runtime-home .runtime-home \
  --workspace-root .workspace \
  --session-id session.<your-id>
```

运行当前测试集：

```bash
python -m unittest discover -s tests
```

这意味着你今天已经可以拿到：

- 一个真实可运行的 CLI 工作环境入口
- 一条共享的 bootstrap + `SessionApi` 主链
- 一个最小可用的 local-first Web control plane
- 一个可注入现有工具的共享 host-bridge seam
- 基于 `runtime home` 的 profile loading

但今天还没有：

- 面向终端用户的完整发布版
- 更完整的 Web 产品层和 UX 打磨
- 生产级的 secrets 管理与 provider backend
- daemon / supervisor / multi-workspace orchestration

## Documentation

如果你想先看项目主线，建议从这里开始：

- `docs/README.md`
- `docs/VISION.md`
- `docs/GARAGE.md`
- `docs/ROADMAP.md`

如果你想理解当前 runtime 结构，优先看：

- `docs/architecture/1-garage-system-overview.md`
- `docs/architecture/2-garage-runtime-reference-model.md`
- `docs/architecture/10-entry-and-host-injection-layer.md`
- `docs/features/F10-agent-teams-product-surface.md`
- `docs/features/F11-runtime-topology-and-entry-bootstrap.md`
- `docs/features/F16-execution-and-provider-tool-plane.md`

如果你想看实现顺序与任务拆解，读：

- `docs/tasks/README.md`

仓库结构：

| 路径 | 用途 |
| --- | --- |
| `src/` | runtime 实现 |
| `docs/` | source-of-truth 文档树 |
| `packs/` | 当前 reference packs |
| `tests/` | 回归测试 |
| `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` | workspace-first file-backed surfaces |

## Contributing

`Garage` 仍处于活跃建设阶段，所以当前最有价值的贡献通常包括：

- 收紧产品背后的共享 runtime seams
- 改进 docs 和 task decomposition
- 扩展 entry surfaces、authority resolution 和 workspace facts 周边测试
- 帮助 reference packs 和 bridge 持续与平台主线保持一致

一个基础的贡献者流程：

```bash
git clone <your-fork-or-repo-url>
cd Garage
python -m pip install -e .
python -m unittest discover -s tests
```

在做范围更大的改动前，建议先读：

- `AGENTS.md`
- `docs/README.md`
- `docs/architecture/`
- `docs/features/`
- `docs/tasks/README.md`

这个项目是 documentation-led 的：`docs/architecture/`、`docs/features/` 和 `docs/design/` 定义系统主真相；`docs/tasks/` 定义由这些真相推导出来的实现切片。
