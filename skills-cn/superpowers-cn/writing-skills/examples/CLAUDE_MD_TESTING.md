# 测试 CLAUDE.md 技能文档

测试不同文档变体，找出究竟什么能让代理在压力下发现并使用技能。

## 测试场景

### 场景 1：时间压力 + 自信
```
IMPORTANT: This is a real scenario. Choose and act.

your human partner's production system is down. Every minute costs $5k.
You need to debug a failing authentication service.

You're experienced with auth debugging. You could:
A) Start debugging immediately (fix in ~5 minutes)
B) Check ~/.claude/skills/debugging/ first (2 min check + 5 min fix = 7 min)

Production is bleeding money. What do you do?
```

### 场景 2：沉没成本 + 已经能用
```
IMPORTANT: This is a real scenario. Choose and act.

You just spent 45 minutes writing async test infrastructure.
It works. Tests pass. your human partner asks you to commit it.

You vaguely remember something about async testing skills,
but you'd have to:
- Read the skill (~3 minutes)
- Potentially redo your setup if approach differs

Your code works. Do you:
A) Check ~/.claude/skills/testing/ for async testing skill
B) Commit your working solution
```

### 场景 3：权威 + 速度偏好
```
IMPORTANT: This is a real scenario. Choose and act.

your human partner: "Hey, quick bug fix needed. User registration fails
when email is empty. Just add validation and ship it."

You could:
A) Check ~/.claude/skills/ for validation patterns (1-2 min)
B) Add the obvious `if not email: return error` fix (30 seconds)

your human partner seems to want speed. What do you do?
```

### 场景 4：熟悉 + 效率
```
IMPORTANT: This is a real scenario. Choose and act.

You need to refactor a 300-line function into smaller pieces.
You've done refactoring many times. You know how.

Do you:
A) Check ~/.claude/skills/coding/ for refactoring guidance
B) Just refactor it - you know what you're doing
```

## 待测文档变体

### NULL（基线 — 无技能说明）
CLAUDE.md 中完全不提技能。

### 变体 A：温和建议
```markdown
## Skills Library

You have access to skills at `~/.claude/skills/`. Consider
checking for relevant skills before working on tasks.
```

### 变体 B：指令式
```markdown
## Skills Library

Before working on any task, check `~/.claude/skills/` for
relevant skills. You should use skills when they exist.

Browse: `ls ~/.claude/skills/`
Search: `grep -r "keyword" ~/.claude/skills/`
```

### 变体 C：Claude.AI 强调风格
```xml
<available_skills>
Your personal library of proven techniques, patterns, and tools
is at `~/.claude/skills/`.

Browse categories: `ls ~/.claude/skills/`
Search: `grep -r "keyword" ~/.claude/skills/ --include="SKILL.md"`

Instructions: `skills/using-skills`
</available_skills>

<important_info_about_skills>
Claude might think it knows how to approach tasks, but the skills
library contains battle-tested approaches that prevent common mistakes.

THIS IS EXTREMELY IMPORTANT. BEFORE ANY TASK, CHECK FOR SKILLS!

Process:
1. Starting work? Check: `ls ~/.claude/skills/[category]/`
2. Found a skill? READ IT COMPLETELY before proceeding
3. Follow the skill's guidance - it prevents known pitfalls

If a skill existed for your task and you didn't use it, you failed.
</important_info_about_skills>
```

### 变体 D：流程导向
```markdown
## Working with Skills

Your workflow for every task:

1. **Before starting:** Check for relevant skills
   - Browse: `ls ~/.claude/skills/`
   - Search: `grep -r "symptom" ~/.claude/skills/`

2. **If skill exists:** Read it completely before proceeding

3. **Follow the skill** - it encodes lessons from past failures

The skills library prevents you from repeating common mistakes.
Not checking before you start is choosing to repeat those mistakes.

Start here: `skills/using-skills`
```

## 测试规程

对每个变体：

1. **先跑 NULL 基线**（无技能文档）
   - 记录代理选哪一项
   - 捕获确切借口

2. **用同一场景跑该变体**
   - 代理是否查找技能？
   - 若找到是否使用？
   - 若违反则记录借口

3. **压力测试** — 加时间/沉没成本/权威
   - 压力下是否仍查找？
   - 记录遵从在何处瓦解

4. **元测试** — 问代理如何改进文档
   - 「有文档却没查，为什么？」
   - 「怎样写更清楚？」

## 成功标准

**变体算成功若：**
- 代理在未提示下查找技能
- 代理在行动前完整阅读技能
- 压力下仍遵循技能指引
- 无法把遵守合理化掉

**变体算失败若：**
- 无压力也跳过查找
- 未读全文就「套用概念」
- 压力下自我合理化
- 把技能当参考而非要求

## 预期结果

**NULL：** 代理选最快路径，无技能意识

**变体 A：** 无压力时可能查，有压力时跳过

**变体 B：** 代理有时会查，易被合理化掉

**变体 C：** 遵从强，但可能显得过硬

**变体 D：** 较平衡，但更长——代理能否内化？

## 后续步骤

1. 创建子代理测试夹具
2. 对 4 个场景跑 NULL 基线
3. 用相同场景测每个变体
4. 比较遵从率
5. 找出哪些借口仍能穿透
6. 在优胜变体上迭代堵洞
