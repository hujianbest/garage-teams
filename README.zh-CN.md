# Garage

[English](README.md) | **中文**

`Garage` 是一个面向 `独立创作者` 的开源 `Agent Skills` 工作台。

它遵循一个核心原则：**技能驱动、工作流编排的开发模式**。

- 基于技能的可组合架构
- AHE（Agent-Harness-Engineering）工作流实现系统化开发
- 两套完整技能家族：产品洞察 → 编码实现
- 基于 Packs 的可复用技能集合组织
- 机器辅助开发与清晰的治理边界

当前状态：V1开发基线，完整的AHE工作流技能集。

## 快速开始

这是一个技能仓库，组织为两个互补的工作流家族：

**产品洞察技能** - 当你有模糊想法或需要产品清晰度时：
- 从 `using-ahe-product-workflow` 开始确定你的入口点
- 通过洞察收集、机会映射、概念塑造逐步推进
- 准备好实现时通过桥接技能进入编码工作流

**编码技能** - 当你有清晰需求并需要实现时：
- 从 `ahe-specify` 开始编写详细需求
- 继续通过设计、任务、实现和审查流程
- 在整个开发过程中使用质量门禁

对于Claude Code用户，可以直接通过 `/skill-name` 命令模式调用技能。

## 项目结构

| 路径 | 用途 |
| --- | --- |
| `packs/coding/skills/` | AHE编码工作流技能（specify、design、tasks、review等） |
| `packs/product-insights/skills/` | AHE产品洞察技能（framing、research、concept、bridge） |
| `packs/coding/skills/docs/` | AHE编码工作流文档和指南 |
| `packs/product-insights/skills/docs/` | AHE产品洞察文档和约定 |
| `docs/wiki/` | 架构分析和设计文档 |
| `.agents/` | Agent特定配置和扩展 |
| `AGENTS.md` | AHE工作流文档约定 |

## 产品洞察技能

当你有模糊想法或需要产品清晰度时使用这些技能：

- **入口与路由**
  - `using-ahe-product-workflow` - 产品洞察家族的公开入口

- **核心工作流**
  - `ahe-outcome-framing` - 定义期望结果、目标用户和替代方案
  - `ahe-insight-mining` - 从网络、GitHub和社区提取证据
  - `ahe-opportunity-mapping` - 映射JTBD机会并优先级排序
  - `ahe-concept-shaping` - 生成和评估多个概念方向
  - `ahe-assumption-probes` - 设计低成本验证实验
  - `ahe-spec-bridge` - 将洞察压缩为编码工作流的规格输入

## 编码技能

当你有清晰需求并需要实现时使用这些技能：

- **上游链路**
  - `ahe-specify` - 支持延后的需求规格说明
  - `ahe-spec-review` - 带质量评审标准的规格评审
  - `ahe-design` - 架构和设计文档
  - `ahe-tasks` - 任务分解和规划

- **执行与评审**
  - `ahe-test-driven-dev` - TDD指导与实践
  - `ahe-code-review` - 代码审查和质量保证
  - `ahe-test-review` - 测试覆盖率和验证
  - `ahe-design-review` - 设计审查和验证
  - `ahe-tasks-review` - 任务分解评审

- **质量门禁**
  - `ahe-bug-patterns` - 常见bug模式检测
  - `ahe-completion-gate` - 完成标准验证
  - `ahe-regression-gate` - 回归预防
  - `ahe-traceability-review` - 需求可追溯性

- **支持技能**
  - `ahe-increment` - 增量开发指导
  - `ahe-hotfix` - 热修复工作流支持
  - `ahe-finalize` - 项目完成和关闭
  - `ahe-workflow-router` - 工作流编排和路由

## 文档

**产品洞察：**
- `packs/product-insights/skills/docs/` - 产品洞察工作流指南
- `packs/product-insights/skills/using-ahe-product-workflow/SKILL.md` - 入口点指南

**编码：**
- `packs/coding/skills/docs/` - AHE编码工作流指南
- `packs/coding/skills/README.md` - 编码技能概览

**架构：**
- `docs/wiki/W120-ahe-workflow-externalization-guide.md` - 外部工作流集成
- `docs/wiki/W140-ahe-platform-first-multi-agent-architecture.md` - 架构概览
- `docs/wiki/` - 工程分析和设计思路

**约定：**
- `AGENTS.md` - AHE文档约定

## 最新更新

最近的发展重点在于增强两个工作流家族：

**产品洞察：**
- 完整的产品洞察工作流，从想法到规格桥接
- 多agent辩论协议用于概念验证
- 研究和证据收集技能

**编码：**
- 增强的 `ahe-specify` 技能，包含需求编写契约
- 新增 `ahe-spec-review` 技能，带全面的评审标准
- 改进的粒度和延后指导
- 新增技能质量评估框架

## 贡献指南

`Garage` 专注于高质量的agent技能。有价值的贡献包括：

- 遵循AHE模式的新工作流技能
- 增强的评审标准和质量门禁
- 不同领域的额外packs
- 改进的文档和示例
- 跨平台兼容性改进

## 许可证

本项目专注于开源的agent辅助开发工具。
