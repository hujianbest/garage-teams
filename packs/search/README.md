# `packs/search/` — Garage Search & Curation Pack

> 信息聚合 / curation family pack。从外部信息源收集和编排实用周报 / 日报。

## 当前内容

| 类型 | 名称 | 用途 |
|---|---|---|
| skill | `ai-weekly` | 从最近 7 天 X/Twitter 帖子（fixed source roster）生成一份可立刻使用的中文 AI 周报，按 Priority 1/2/3 给 creator 排版 |

## 安装

随 `garage init --hosts <list>` 自动装到三家宿主原生目录。详见 `packs/README.md` 顶层契约 + `docs/guides/garage-os-user-guide.md` "Pack & Host Installer" 段。

## 设计来源

ai-weekly skill 沉淀自 Garage 维护者本人在 X/Twitter 上的 AI 周报实践，作为 search & curation 类 skill 的首个内容物落入此 pack。后续可能再加 ai-daily / paper-roundup / trends-monitor 等同 family skill；新增时务必：

1. 在 `packs/search/skills/<id>/SKILL.md` 落 skill 文件 + 至少 1 个 references/ + 1 个 evals/
2. 在 `packs/search/pack.json` `skills[]` 数组追加 `<id>`
3. 同步 `tests/adapter/installer/test_full_packs_install.py` INV-1 hard gate（总 skill 数 30 → N+1）+ 各 host install count
4. 同步 `AGENTS.md` 顶部 packs 表格

## 不变量

- 不得包含宿主特定术语（参见 NFR-701 黑名单 — 由 `tests/adapter/installer/test_neutrality.py` 自动守门）
- `pack.json` schema 与其它 pack 一致（schema_version=1，pack_id=search）
- 任一 SKILL.md 增改后必须能通过 `pytest tests/adapter/installer/ -q` 全套绿
