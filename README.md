# Garage

**English** | [中文](README.zh-CN.md)

`Garage` is an open-source `Agent Skills` workspace designed for `solo creators`.

It follows one core principle: **skills-driven, workflow-orchestrated development**.

- Skill-based architecture with composable capabilities
- AHE (Agent-Harness-Engineering) workflow for systematic development
- Two complete skill families: Product Insights → Coding implementation
- Packs-based organization for reusable skill collections
- Machine-assisted development with clear governance boundaries

Current status: V1 development baseline with complete AHE workflow skill sets.

## Quick Start

This is a skills repository organized into two complementary workflow families:

**Product Insights Skills** - When you have a fuzzy idea or need product clarity:
- Start with `using-ahe-product-workflow` to determine your entry point
- Move through insight gathering, opportunity mapping, concept shaping
- Bridge to coding skills when ready for implementation

**Coding Skills** - When you have clear requirements and need implementation:
- Start with `ahe-specify` for detailed requirements
- Continue through design, tasks, implementation, and review
- Use quality gates throughout the development process

For Claude Code users, skills can be invoked directly through the `/skill-name` command pattern.

## Project Structure

| Path | Purpose |
| --- | --- |
| `packs/coding/skills/` | AHE coding workflow skills (specify, design, tasks, review, etc.) |
| `packs/product-insights/skills/` | AHE product insight skills (framing, research, concept, bridge) |
| `packs/coding/skills/docs/` | AHE coding workflow documentation and guides |
| `packs/product-insights/skills/docs/` | AHE product insight documentation and conventions |
| `docs/wiki/` | Architecture analysis and design documentation |
| `.agents/` | Agent-specific configuration and extensions |
| `AGENTS.md` | AHE workflow documentation conventions |

## Product Insights Skills

Use these when you have a vague idea or need product clarity:

- **Entry & Routing**
  - `using-ahe-product-workflow` - Public entry point for product insight family

- **Core Workflow**
  - `ahe-outcome-framing` - Define desired outcomes, target users, and alternatives
  - `ahe-insight-mining` - Extract evidence from web, GitHub, and communities
  - `ahe-opportunity-mapping` - Map JTBD opportunities and prioritize wedges
  - `ahe-concept-shaping` - Generate and evaluate multiple concept directions
  - `ahe-assumption-probes` - Design low-cost validation experiments
  - `ahe-spec-bridge` - Compress insights into spec input for coding workflow

## Coding Skills

Use these when you have clear requirements and need implementation:

- **Upstream Chain**
  - `ahe-specify` - Requirements specification with deferment support
  - `ahe-spec-review` - Specification review with quality rubrics
  - `ahe-design` - Architecture and design documentation
  - `ahe-tasks` - Task breakdown and planning

- **Execution & Review**
  - `ahe-test-driven-dev` - TDD guidance and practices
  - `ahe-code-review` - Code review and quality assurance
  - `ahe-test-review` - Test coverage and validation
  - `ahe-design-review` - Design review and validation
  - `ahe-tasks-review` - Task breakdown review

- **Quality Gates**
  - `ahe-bug-patterns` - Common bug pattern detection
  - `ahe-completion-gate` - Completion criteria validation
  - `ahe-regression-gate` - Regression prevention
  - `ahe-traceability-review` - Requirements traceability

- **Supporting Skills**
  - `ahe-increment` - Incremental development guidance
  - `ahe-hotfix` - Hotfix workflow support
  - `ahe-finalize` - Project finalization and closeout
  - `ahe-workflow-router` - Workflow orchestration and routing

## Documentation

**Product Insights:**
- `packs/product-insights/skills/docs/` - Product insight workflow guides
- `packs/product-insights/skills/using-ahe-product-workflow/SKILL.md` - Entry point guide

**Coding:**
- `packs/coding/skills/docs/` - AHE coding workflow guides
- `packs/coding/skills/README.md` - Coding skills overview

**Architecture:**
- `docs/wiki/W120-ahe-workflow-externalization-guide.md` - External workflow integration
- `docs/wiki/W140-ahe-platform-first-multi-agent-architecture.md` - Architecture overview
- `docs/wiki/` - Engineering analysis and design ideas

**Conventions:**
- `AGENTS.md` - AHE documentation conventions

## Recent Updates

Latest developments focus on enhancing both workflow families:

**Product Insights:**
- Complete product insight workflow from idea to spec bridge
- Multi-agent debate protocols for concept validation
- Research and evidence gathering skills

**Coding:**
- Enhanced `ahe-specify` with requirement authoring contracts
- Added `ahe-spec-review` with comprehensive review rubrics
- Improved granularity and deferment guidance
- Added evaluation frameworks for skill quality assessment

## Contributing

`Garage` is focused on high-quality agent skills. Valuable contributions include:

- New workflow skills following AHE patterns
- Enhanced evaluation rubrics and quality gates
- Additional packs for different domains
- Improved documentation and examples
- Cross-platform compatibility improvements

## License

This project maintains an open-source focus on agent-assisted development tools.
