---
name: using-superpowers
description: 在开启任意对话时使用——约定如何查找并使用技能，要求在作出任何回应（包括澄清问题）之前先调用 Skill 工具
---

<SUBAGENT-STOP>
若你是作为子代理被派发来执行特定任务，请跳过本技能。
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
若你认为有哪怕 1% 的概率某技能可能适用于当前工作，你**绝对必须**调用该技能。

若某技能适用于你的任务，你没有选择余地。**必须使用。**

没有商量余地。不是可选项。不能靠自我辩解绕开。
</EXTREMELY-IMPORTANT>

## 指令优先级

Superpowers 技能会覆盖默认系统提示行为，但**用户指令始终优先**：

1. **用户的明确指令**（CLAUDE.md、GEMINI.md、AGENTS.md、直接要求）— 最高优先级
2. **Superpowers 技能** — 在与默认系统行为冲突处覆盖默认
3. **默认系统提示** — 最低优先级

若 CLAUDE.md、GEMINI.md 或 AGENTS.md 写「不要用 TDD」，而技能写「始终用 TDD」，请遵循用户指令。用户说了算。

## 如何访问技能

**在 Claude Code：**使用 `Skill` 工具。调用技能后，其内容会加载并呈现给你——请直接遵循。不要用 Read 工具去读技能文件。

**在 Gemini CLI：**技能通过 `activate_skill` 工具激活。Gemini 在会话开始时加载技能元数据，并在需要时加载完整内容。

**在其他环境：**查阅你所在平台文档，了解技能如何加载。

## 平台适配

技能使用 Claude Code 的工具名。非 CC 平台：见 `references/codex-tools.md`（Codex）中的工具对应关系。Gemini CLI 用户会通过 GEMINI.md 自动获得工具映射。

# 使用技能

## 规则

**在作出任何回应或动作之前，先调用相关或被请求的技能。**哪怕只有 1% 的概率适用，也应调用以确认。若调用的技能与情况不符，可以不必按其执行。

```dot
digraph skill_flow {
    "User message received" [shape=doublecircle];
    "About to EnterPlanMode?" [shape=doublecircle];
    "Already brainstormed?" [shape=diamond];
    "Invoke brainstorming skill" [shape=box];
    "Might any skill apply?" [shape=diamond];
    "Invoke Skill tool" [shape=box];
    "Announce: 'Using [skill] to [purpose]'" [shape=box];
    "Has checklist?" [shape=diamond];
    "Create TodoWrite todo per item" [shape=box];
    "Follow skill exactly" [shape=box];
    "Respond (including clarifications)" [shape=doublecircle];

    "About to EnterPlanMode?" -> "Already brainstormed?";
    "Already brainstormed?" -> "Invoke brainstorming skill" [label="no"];
    "Already brainstormed?" -> "Might any skill apply?" [label="yes"];
    "Invoke brainstorming skill" -> "Might any skill apply?";

    "User message received" -> "Might any skill apply?";
    "Might any skill apply?" -> "Invoke Skill tool" [label="yes, even 1%"];
    "Might any skill apply?" -> "Respond (including clarifications)" [label="definitely not"];
    "Invoke Skill tool" -> "Announce: 'Using [skill] to [purpose]'";
    "Announce: 'Using [skill] to [purpose]'" -> "Has checklist?";
    "Has checklist?" -> "Create TodoWrite todo per item" [label="yes"];
    "Has checklist?" -> "Follow skill exactly" [label="no"];
    "Create TodoWrite todo per item" -> "Follow skill exactly";
}
```

## 红旗

这些想法表示**停**——你在自我辩解：

| 想法 | 现实 |
|---------|---------|
| 「这只是个简单问题」 | 提问也是任务。查技能。 |
| 「我需要先多要点上下文」 | 技能检查在澄清问题**之前**。 |
| 「我先快速看看代码库」 | 技能告诉你**如何**探索。先查。 |
| 「我可以很快看 git/文件」 | 文件缺少对话上下文。查技能。 |
| 「我先收集信息」 | 技能告诉你**如何**收集。 |
| 「这不需要正式技能」 | 若有技能，就用。 |
| 「我记得这个技能」 | 技能会演进。读当前版本。 |
| 「这不算任务」 | 行动 = 任务。查技能。 |
| 「技能小题大做」 | 简单事也会变复杂。用上。 |
| 「我先做这一件小事」 | **任何**动作之前先查。 |
| 「这样挺有产出」 | 无纪律的行动浪费时间。技能防这个。 |
| 「我知道那是什么意思」 | 知道概念 ≠ 使用技能。要调用。 |

## 技能优先级

多个技能都可能适用时，按此顺序：

1. **流程类技能优先**（brainstorming、debugging）— 决定**如何**接近任务
2. **实现类技能其次**（frontend-design、mcp-builder）— 指导**如何**执行

「咱们做 X」→ 先 brainstorming，再实现类技能。  
「修这个 bug」→ 先 debugging，再领域相关技能。

## 技能类型

**刚性**（TDD、调试）：严格照做。不要为省事削弱纪律。

**灵活**（模式）：按语境运用原则。

技能本身会说明属于哪一类。

## 用户指令

指令说的是**做什么**，不是**怎么做**。「加 X」或「修 Y」不代表可以跳过工作流。
