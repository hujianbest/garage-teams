# `packs/writing/` — 内容创作 Pack

`packs/writing/` 是 Garage 自带的 **内容创作 family pack**，把 5 个写作 skill 打包成可分发载体。下游用户在自己项目里 `garage init --hosts <list>` 之后，就能在挂载的宿主里加载 blog-writing / humanizer-zh / hv-analysis / khazix-writer / magazine-web-ppt 等 skill，按个人风格驱动 AI Agent 写博客 / 去 AI 痕迹 / 做深度研究 / 写公众号长文 / 生成杂志风网页 PPT。

## Pack 概况

| 字段 | 值 |
|---|---|
| `pack_id` | `writing` |
| `version` | `0.2.0` |
| `schema_version` | `1` |
| `skills` | 5 |
| `agents` | 0 |
| family-level 资产 | 1（`prompts/横纵分析法.md`） |

## 5 个 Skill 清单

| Skill | 用途 |
|---|---|
| `blog-writing` | 写技术博客或思考随笔（个人风格沉淀，含发布前定稿 12 条规律） |
| `humanizer-zh` | 去除中文文本中的 AI 生成痕迹（基于维基百科 AI 写作特征综合指南） |
| `hv-analysis` | 横纵分析法深度研究（融合索绪尔历时-共时分析 + 商学院案例研究法 + 竞争战略分析） |
| `khazix-writer` | 数字生命卡兹克公众号长文风格写作 |
| `magazine-web-ppt` | 单文件横向翻页网页 PPT（电子杂志 × 电子墨水风格，WebGL 背景、版式与主题参考见 `references/`） |

## Family-Level 共享资产

### `packs/writing/prompts/横纵分析法.md`

横纵分析法的子 Agent prompt 模板，由 `hv-analysis` skill 引用（多个并发子 Agent 共享同一 prompt 蓝本）。

## 上游归属与许可

本 pack 的内容物搬迁自 `.agents/skills/write-blog/`（数字生命卡兹克 / Khazix 等多位作者贡献），上游 LICENSE 已保留为 `packs/writing/LICENSE`。

具体子 skill 的上游来源：

- `blog-writing` — 个人风格博客写作 SOP，含「发布前定稿」12 条用户改稿规律
- `humanizer-zh` — Humanizer-zh 项目（https://github.com/op7418/Humanizer-zh）的 Garage skill 适配
- `hv-analysis` — 横纵分析法（数字生命卡兹克提出）
- `khazix-writer` — 数字生命卡兹克公众号风格
- `magazine-web-ppt` — [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)（MIT；`skills/magazine-web-ppt/LICENSE`）

## 安装样板

下游用户在自己项目执行：

```bash
cd ~/projects/my-app
garage init --hosts claude
# stdout: Installed N skills, M agents into hosts: claude   (N == sum(三 pack.json.skills[]))
ls .claude/skills/ | grep -E 'blog-writing|humanizer-zh|hv-analysis|khazix-writer|magazine-web-ppt'
# 5 个 skill 子目录全部存在
cat .claude/skills/blog-writing/SKILL.md | head -5
# → 含 installed_by: garage, installed_pack: writing
```

## 与 humanizer-zh 协作的范例工作流

```
用户素材 → khazix-writer 出长文初稿 → humanizer-zh 去 AI 痕迹 → 用户编辑发布
                ↓
        （研究类话题前置 hv-analysis 做横纵分析）
                ↓
        blog-writing 提炼为个人博客版（应用 12 条发布前定稿规律）
```

## NFR-801 文件级豁免（spec NFR-801 + design ADR-D8-9）

本 pack 内 `humanizer-zh/README.md` 含 3 处 `~/.claude/skills/humanizer-zh` 安装命令样板（git clone 路径），按 design ADR-D8-9 豁免清单整文件保留 — 删除/重写会让用户无从安装该 skill，与 manifesto "数据归你" 信念冲突。SKILL.md 主体仍受 NFR-801 强约束（grep = 0）。
