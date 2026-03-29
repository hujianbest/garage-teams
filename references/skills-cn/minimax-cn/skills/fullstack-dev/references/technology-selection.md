# 技术选型框架

用于后端和全栈技术选择的结构化决策框架。防止分析瘫痪，同时确保严格评估。

**铁律：没有明确的权衡分析就没有技术选择。**

“我喜欢它”和“它很流行”不是工程论据。

---

## 第一阶段：需求先于技术

### 非功能性需求（量化！）

|尺寸|问题 |错误答案 |好答案|
|------------|----------|------------|----------|
|规模|有多少并发用户？ | “很多”| “1K并发，500RPS峰值”|
|延迟| p99 响应时间可接受吗？ | “快”| “< 200ms API，< 2s 报告”|
|可用性 |所需的正常运行时间？ | “永远向上” | “99.9%（8.7 小时停机时间/年）”|
|数据量|预期存储增长？ | “很多” | “100GB/年，10M 行”|
|一致性|强还是最终？ | “一致”| “强大的支付能力，最终的饲料”|
|合规|监管？ | “一些”| “GDPR 数据驻留欧盟，SOC 2 Type II” |

### 团队约束

- 团队规模和资历级别
- 团队已经熟知的内容
- 你能雇用这个堆栈吗？ （查看就业市场）
- 时间压力（生产所需的天数与月数）
- 许可证、基础设施、培训预算

---

## 第 2 阶段：评估矩阵

根据加权标准对每个选项进行 1-5 分评分：

|标准|重量 |选项A |选项 B |选项C |
|------------|--------|----------|---------|----------|
|满足功能需求 | 5× | _ | _ | _ |
|满足非功能性需求 | 5× | _ | _ | _ |
|团队专业知识/学习曲线| 4× | _ | _ | _ |
|生态系统成熟度（库、工具）| 3×| _ | _ | _ |
|社区和长期生存能力| 3×| _ | _ | _ |
|运营复杂性 | 3×| _ | _ | _ |
|招聘池可用性 | 2×| _ | _ | _ |
|成本（许可证+基础设施+培训）| 2×| _ | _ | _ |
| **加权总计** | | _ | _ | _ |

**规则：**
- 任何选项在 5× 标准上得分 **1** → 自动取消资格
- 选项彼此相差**10%** → 选择团队最了解的
- **15%** 以内的选项 → 运行 **限时 PoC**（最多 2-5 天）

---

## 第 3 阶段：决策树

### 后端语言/框架```
What type of project?
│
├─ REST/GraphQL API, rapid development
│   ├─ Team knows TypeScript → Node.js
│   │   ├─ Full-featured, enterprise patterns → NestJS
│   │   ├─ Lightweight, flexible → Fastify / Hono / Express
│   │   └─ Full-stack with React → Next.js API routes
│   ├─ Team knows Python
│   │   ├─ High-perf async API → FastAPI
│   │   ├─ Full-stack, admin-heavy → Django
│   │   └─ Lightweight → Flask / Litestar
│   └─ Team knows Java/Kotlin
│       ├─ Enterprise, large team → Spring Boot
│       └─ Lightweight, fast startup → Quarkus / Ktor
│
├─ High concurrency, systems-level
│   ├─ Microservices, network → Go
│   ├─ Extreme perf, safety → Rust (Axum / Actix)
│   └─ Fault tolerance → Elixir (Phoenix)
│
├─ Real-time (WebSocket, streaming)
│   ├─ Node.js ecosystem → Socket.io / ws
│   ├─ Scalable pub/sub → Elixir Phoenix
│   └─ Low-latency → Go / Rust
│
└─ ML / data-intensive
    └─ Python (FastAPI + ML libs)
```＃＃＃ 数据库```
What data model?
│
├─ Structured, relational, ACID
│   ├─ General purpose → PostgreSQL ← DEFAULT CHOICE
│   ├─ Read-heavy, MySQL ecosystem → MySQL / MariaDB
│   └─ Embedded / serverless edge → SQLite / Turso / D1
│
├─ Semi-structured, flexible schema
│   ├─ Document-oriented → MongoDB
│   ├─ Serverless document → DynamoDB / Firestore
│   └─ Search-heavy → Elasticsearch / OpenSearch
│
├─ Key-value / cache
│   ├─ In-memory + data structures → Redis / Valkey
│   └─ Planet-scale KV → DynamoDB / Cassandra
│
├─ Time-series → TimescaleDB / ClickHouse / InfluxDB
├─ Graph → Neo4j / Apache AGE (Postgres extension)
└─ Vector (AI embeddings) → pgvector / Pinecone / Qdrant
```**默认：** 从 PostgreSQL 开始。它可以处理 80% 的用例。

### 缓存策略

|图案|技术 |当 |
|--------|------------|------|
|应用程序缓存 | Redis/Valkey |会话、频繁阅读、速率限制 |
| HTTP 缓存 | CDN（Cloudflare/Vercel）|静态资产、公共 API 响应 |
|查询缓存 |物化视图 |复杂的聚合、仪表板 |
|进程内缓存 | LRU（内存中）|配置，小型查找表 |
|边缘缓存 | Cloudflare KV / Vercel KV |全局低延迟读取|

### 消息队列/事件流

|图案|技术 |当 |
|--------|------------|------|
|任务队列（后台作业）| BullMQ/Celery/SQS |电子邮件、出口、付款 |
|事件流（重放、审核）|卡夫卡/Redpanda |事件溯源、实时管道 |
|轻量级发布/订阅 | Redis 流/NATS |简单的通知、广播 |
|请求-回复（同步而非异步）| NATS / RabbitMQ RPC |内部服务电话 |

### 托管/部署

|型号|技术 |当 |
|--------|------------|------|
|无服务器（自动扩展）| Vercel / Cloudflare Workers / Lambda |可变流量，按使用付费 |
|容器（可预测）|云跑/渲染/铁路/Fly.io |流量稳定，操作简单 |
| Kubernetes（大规模）| EKS / GKE / AKS | 10+服务，团队具备K8s专业知识 |
| VPS（完全控制）| DigitalOcean / Hetzner / EC2 |可预测的工作量，对成本敏感 |

---

## 第 4 阶段：决策文档

### ADR（架构决策记录）模板```markdown
# ADR-{NNN}: {Title}

## Status: Proposed | Accepted | Deprecated | Superseded by ADR-{NNN}

## Context
What problem are we solving? What forces are at play?

## Decision
What did we choose and why?

## Evaluation
| Criterion | Weight | Chosen | Runner-up |
|-----------|--------|--------|-----------|

## Consequences
- Positive: ...
- Negative: ...
- Risks: ...

## Alternatives Rejected
- Option B: rejected because...
- Option C: rejected because...
```---

## 常用堆栈模板

### A：启动/MVP（速度）

|层|选择|为什么 |
|--------|--------|-----|
|语言 |打字稿 |正面+背面一种语言|
|框架| Next.js（全栈）或 NestJS (API) |快速迭代|
|数据库| PostgreSQL（Supabase / Neon）|托管、慷慨的免费套餐 |
|授权 |更好的授权/文员 |无需维护授权码 |
|缓存| Redis（Upstash）|无服务器友好 |
|托管| Vercel / 铁路 |零配置部署 |

### B：SaaS/商业应用程序（平衡）

|层|选择|为什么 |
|--------|--------|-----|
|语言 | TypeScript 或 Python |团队偏好|
|框架| NestJS 或 FastAPI |结构化、可测试 |
|数据库| PostgreSQL |可靠、功能丰富|
|队列| BullMQ（Redis）|简单的后台作业 |
|授权 | OAuth 2.0 + JWT |标准、灵活|
|托管| AWS ECS / 云运行 |可扩展容器 |
|监控| Datadog / Grafana + Prometheus | 数据狗全面的可观测性 |

### C：高性能（规模）

|层|选择|为什么 |
|--------|--------|-----|
|语言 |继续还是 Rust |最大吞吐量、低延迟 |
|数据库| PostgreSQL + Redis + ClickHouse | OLTP + 缓存 + 分析 |
|队列|卡夫卡/Redpanda |高通量流 |
|托管| Kubernetes（EKS/GKE）|细粒度缩放 |
|监控|普罗米修斯 + Grafana + Jaeger |指标+追踪|

### D：人工智能/机器学习应用

|层|选择|为什么 |
|--------|--------|-----|
|语言 | Python（API）+ TypeScript（前端）| ML 库 + 现代 UI |
|框架| FastAPI + Next.js |异步+SSR |
|数据库| PostgreSQL + pgvector |关系+嵌入|
|队列|芹菜+Redis |机器学习作业处理 |
|托管|模态/AWS GPU/复制 | GPU 访问 |

---

## 反模式

| ＃| ❌不要 | ✅ 改为 |
|---|---------|--------------|
| 1 | “X 正在 HN 上流行”|根据您的要求进行评估 |
| 2 |简历驱动的发展 |选择可以维护的团队 |
| 3 | “必须扩展到 100 万用户”（第 1 天）|为 10× 当前需求构建，而不是 1000× |
| 4 |评估几周 |时间框为3-5天，然后决定|
| 5 |没有决定文件 |为每一个主要选择写ADR |
| 6 |忽略运营成本|包括部署、监控、调试成本 |
| 7 | “我们稍后会重写”|假设你不会。仔细选择。 |
| 8 |默认微服务|启动整体，需要时提取 |
| 9 |每个服务不同的数据库（第 1 天）|一个数据库，合理时拆分 |
| 10 | 10 “这在谷歌行得通”|你不是谷歌。根据您的情况进行扩展。 |

---

## 常见问题

### 问题 1：“团队无法就框架达成一致”

**修复：** 时间范围为 3 天。填写评价矩阵。如果得分在 10% 以内，请选择大多数人都知道的内容。 ADR 中的文档。继续前行。

### 问题 2：“我们选择了 X，但它不合适”

**修正：**沉没成本谬误检查。如果投资时间少于 2 周，请立即切换。如果超过 2 周，记录痛点并计划分阶段迁移。

### 问题 3：“我们需要微服务吗？”

**修复：** 几乎可以肯定没有。从结构良好的整体开始。仅在以下情况下提取到服务：(a) 不同的扩展需求，(b) 不同的团队所有权，(c) 不同的部署节奏。