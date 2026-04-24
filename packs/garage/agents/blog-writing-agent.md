---
name: blog-writing-agent
description: 适用于公众号长文 / 个人博客写作场景。组合 packs/writing/ 的 blog-writing + humanizer-zh + (可选) hv-analysis skill, 与用户的 KnowledgeType.STYLE 偏好对齐, 产出符合用户风格的中文长文. 不适用于 AI 周报 (→ packs/search/ai-weekly) 或 AI 痕迹检测 (→ humanizer-zh single skill).
---

# Blog Writing Agent

Production agent for end-to-end Chinese long-form content creation, combining 3 writing skills + user style preferences.

## When to Use

- 用户给一个主题 / 一篇素材 / 一条经验, 想产出一篇公众号长文 / 个人博客文章
- 用户的 `.garage/knowledge/style/` 已积累写作风格偏好 (e.g. "卡兹克风格 - 短句长句节奏", "段首多用名词起头", "避免否定式排比")
- F010 `garage sync` 已把 style entries 装到 host context surface (AI 开新对话时已 see 用户风格)

## How It Composes

1. **主创作**: 调用 `blog-writing` skill (packs/writing/) 做长文骨架 + 段落
2. **风格 humanize**: 调用 `humanizer-zh` skill 去掉 AI 痕迹, 应用 user style entries 的具体偏好 (e.g. 卡兹克风格 prompt template)
3. **可选研究层**: 如果题材需要深度调研, 先调 `hv-analysis` skill (横纵分析法) 产出研究 brief, 再喂给 blog-writing
4. **追溯锚点**: 写完后在文末 hidden comment 区留 "本文使用 style entries: <id-list>" 让用户验证

## Workflow

1. Read user 的写作意图 + 素材
2. Read user `.garage/knowledge/style/*.md` (F011 STYLE entries)
3. (Optional) 调 `hv-analysis` 做调研 brief
4. 调 `blog-writing` 起草初稿
5. 调 `humanizer-zh` 去 AI 痕迹 + 注入 user style
6. 输出 final draft + style anchor footer

## Hard Gates

- 不替用户决定主题 / 选材 / 价值判断 (B5 user-pact "你做主")
- Style entries 是 human-curated; agent 不修改 entry, 只 read

## Notes

本 agent 是 F011 ADR-D11-3 落地: 由宿主在执行时 read body + 调对应 skill (`blog-writing` / `humanizer-zh` / `hv-analysis`), agent.md 本身是 composition hint 不带 runtime.

详见 `packs/writing/README.md` (3 个组合 skill) + `packs/garage/README.md` (F011 段更新).
