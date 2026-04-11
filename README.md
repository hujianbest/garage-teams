# Garage

`Garage` 是一个面向 `solo creator` 的开源 agent runtime。

它的目标不是再做一个聊天壳，而是把下面这些东西变成同一个长期系统：

- AI 团队协作
- `workspace-first` 的 file-backed facts
- packs / contracts 驱动的能力扩展
- evidence、governance 和长期成长

当前仓库是 `Garage` 的主开发仓，既承载源码与设计文档，也承载当前默认的 dogfooding workspace。

## 一句话状态

`Garage` 现在已经能跑通一条最小 runtime 主链，但还不是一个已经打包完成的终端产品。

今天仓库里已经有：

- `src/` 下的 runtime topology、bootstrap 和 execution layer 骨架
- `coding` 与 `product-insights` 两个 reference packs
- `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` 这套 workspace-first surfaces
- `unittest` 覆盖的最小回归验证

今天还没有：

- 稳定的 `garage` CLI
- GUI 或完整 IDE 产品入口
- installer / daemon / 多 workspace supervisor
- 生产级 provider 配置、secrets 管理和 execution backend

如果你是第一次打开这个仓库，可以直接把它理解成：

**一个 docs-first、runtime-first、正在演进中的开源 `Creator OS` scaffold。**

## 快速开始

### 环境要求

- `Python 3.12+`

### 先让 Python 能导入 `src/`

PowerShell:

```powershell
$env:PYTHONPATH = "src"
```

bash / zsh:

```bash
export PYTHONPATH=src
```

## 现在怎么运行

### 1. 跑测试

这是当前最稳妥的运行入口：

```bash
python -m unittest discover -s tests
```

这会验证当前已经落下来的主链，包括：

- runtime topology bindings
- unified bootstrap chain
- session create / resume / attach
- reference pack registry loading
- provider / tool execution skeleton

### 2. 跑一个最小 bootstrap demo

当前没有稳定 CLI，所以真正“启动一次 Garage”最直接的办法，是直接调用 `GarageLauncher`：

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from bootstrap import BootstrapConfig, GarageLauncher, LaunchMode

repo_root = Path.cwd()
launcher = GarageLauncher()

with TemporaryDirectory() as tmp:
    tmp_root = Path(tmp)
    result = launcher.launch(
        BootstrapConfig(
            launch_mode=LaunchMode.CREATE,
            source_root=repo_root,
            runtime_home=tmp_root / "runtime-home",
            workspace_root=tmp_root / "workspace",
            workspace_id="garage-demo",
            profile_id="default",
            entry_surface="cli",
            problem_kind="implementation",
            entry_pack="coding",
            entry_node="coding.bridge-intake",
            goal="Bootstrap a demo Garage session.",
        )
    )

    print(result.session_state.session_id)
    print(result.session_state.session_status)
    print(result.session_route.file_path)
```

这个 demo 当前能证明：

- source root / runtime home / workspace 三层绑定能被正确解析
- reference packs 能从 `packs/` 被加载
- runtime services 能被装配
- 新 session 能被创建并落盘到 workspace surfaces

当前它还不能证明：

- 你已经拿到了稳定 CLI
- execution layer 已经接好生产级 provider
- Garage 已经是 end-user ready app

## 当前仓库如何理解

这个仓库目前运行在 `source-coupled workspace mode`：

- 仓库根目录是 `Garage Source Root`
- 仓库根目录也可以作为默认 dogfooding workspace

这就是为什么你会在根目录看到：

- `artifacts/`
- `evidence/`
- `sessions/`
- `archives/`
- `.garage/`

对贡献者来说，更推荐先用临时外部 workspace 跑 demo，而不是直接把 repo root 当测试 workspace，这样不会把运行状态混进本地 clone。

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `README.md` | 仓库入口 |
| `AGENTS.md` | 仓库级 agent 约定 |
| `pyproject.toml` | Python package / `src` layout 入口 |
| `src/` | `Garage` runtime 的当前实现面 |
| `docs/` | 主文档树与 source-of-truth |
| `packs/` | 当前 reference packs |
| `tests/` | 当前最小验证面 |
| `.agents/skills/` | 仓库内使用的本地 skills 资产 |
| `artifacts/`、`evidence/`、`sessions/`、`archives/`、`.garage/` | workspace-first file-backed surfaces |

## 先读哪里

如果你想理解项目本体，推荐顺序是：

1. `docs/README.md`
2. `docs/VISION.md`
3. `docs/GARAGE.md`
4. `docs/ROADMAP.md`
5. `docs/architecture/`
6. `docs/features/`
7. `docs/design/`
8. `docs/tasks/README.md`

如果你只关心“现在为什么能这样运行”，优先看：

- `docs/features/F210-runtime-home-and-workspace-topology.md`
- `docs/features/F220-runtime-bootstrap-and-entrypoints.md`
- `docs/features/F230-runtime-provider-and-tool-execution.md`

## 当前实现边界

当前主线坚持这些约束：

- `Markdown-first`
- `file-backed`
- `Contract-first`
- `workspace-first`
- `one runtime, many entry surfaces`

也就是说：

- 设计真相主要在 `docs/`
- 运行时代码主要在 `src/`
- pack 能力面主要在 `packs/`
- workspace facts 主要留在根部 surfaces，而不是被 runtime home 吞掉

## 当前不是哪些东西

为了避免误解，这个仓库当前不是：

- 一个已经打磨完成的通用桌面应用
- 一个已经稳定发布的 CLI 工具
- 一个单纯的 workflow 资料库

它更准确的说法是：

**一个正在把 `Creator OS` 设计落成真实 runtime 的开源主仓。**
