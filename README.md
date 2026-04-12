# Garage

**English** | [中文](README.zh-CN.md)

`Garage` is an open-source `Agent Teams` workspace for a `solo creator`.

At the product layer, `Garage` is meant to be a working environment where a creator can build, guide, and grow a long-lived `Garage Team`. At the system layer, it is still a shared runtime, but that runtime exists to support a directly usable product environment rather than a developer-only integration framework.

It is designed around one idea: **one runtime, many entry surfaces**. `Garage` should first stand on its own as a CLI/Web workspace, and then inject its agents, skills, and long-term capabilities into tools people already use, such as `Claude`, `OpenCode`, or `Cursor`.

Today, the repository already includes:

- a working `garage` CLI shell
- a minimal local-first web control plane
- a shared host-bridge seam for `Claude` / `OpenCode` / `Cursor`-style integrations
- runtime-home profile loading and authority resolution
- file-backed workspace surfaces under `artifacts/`, `evidence/`, `sessions/`, `archives/`, and `.garage/`

This is still an actively evolving product environment, not a finished end-user app. The core direction is stable; product depth is still being built.

## Quick Install

Requirements:

- `Python 3.12+`

Install the current development build:

```bash
python -m pip install -e .
```

After installation:

```bash
garage --help
```

If you want Python imports to work directly from the repository without installation:

```bash
export PYTHONPATH=src
```

PowerShell:

```powershell
$env:PYTHONPATH = "src"
```

## Quick Start

Create a new session from the CLI:

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

Resume a session:

```bash
garage resume \
  --source-root . \
  --runtime-home .runtime-home \
  --workspace-root .workspace \
  --session-id session.<your-id>
```

Run the current test suite:

```bash
python -m unittest discover -s tests
```

What this gives you today:

- a real CLI workspace entry
- a shared bootstrap and `SessionApi` chain
- a minimal local-first web control plane
- a shared host-bridge seam for existing tools
- runtime-home based profile loading

What it does not give you yet:

- a production-ready packaged release
- full web product depth and UX polish
- production-grade secrets and provider backends
- daemon / supervisor / multi-workspace orchestration

## Documentation

Start here if you want the system overview:

- `docs/README.md`
- `docs/VISION.md`
- `docs/GARAGE.md`
- `docs/ROADMAP.md`

Read these if you want the current runtime model:

- `docs/architecture/1-garage-system-overview.md`
- `docs/architecture/2-garage-runtime-reference-model.md`
- `docs/architecture/10-entry-and-host-injection-layer.md`
- `docs/features/F10-agent-teams-product-surface.md`
- `docs/features/F11-runtime-topology-and-entry-bootstrap.md`
- `docs/features/F16-execution-and-provider-tool-plane.md`

Read this if you want the implementation sequence:

- `docs/tasks/README.md`

Repository structure:

| Path | Purpose |
| --- | --- |
| `src/` | runtime implementation |
| `docs/` | source-of-truth documentation |
| `packs/` | current reference packs |
| `tests/` | regression coverage |
| `artifacts/`, `evidence/`, `sessions/`, `archives/`, `.garage/` | workspace-first file-backed surfaces |

## Contributing

`Garage` is still in active construction, so the most useful contributions are usually:

- tightening the shared runtime seams behind the product
- improving docs and task decomposition
- expanding test coverage around entry surfaces, authority resolution, and workspace facts
- helping reference packs and bridges stay aligned with the platform model

Basic contributor flow:

```bash
git clone <your-fork-or-repo-url>
cd Garage
python -m pip install -e .
python -m unittest discover -s tests
```

Before making broader changes, read:

- `AGENTS.md`
- `docs/README.md`
- `docs/architecture/`
- `docs/features/`
- `docs/tasks/README.md`

The project is documentation-led: `docs/architecture/`, `docs/features/`, and `docs/design/` define the main truth; `docs/tasks/` defines the implementation slices that follow from it.
