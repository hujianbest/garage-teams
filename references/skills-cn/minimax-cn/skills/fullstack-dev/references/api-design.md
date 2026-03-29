---
名称：fullstack-dev-api-design
描述：“API 设计模式和最佳实践。在创建端点、选择方法/状态代码、实现分页或编写 OpenAPI 规范时使用。防止常见的 REST/GraphQL/gRPC 错误。”
许可证：麻省理工学院
元数据：
  版本：“2.0.0”
  来源：
    - 微软 REST API 指南
    - 谷歌API设计指南
    - Zalando RESTful API 指南
    - JSON：API规范
    - RFC 9457（HTTP API 的问题详细信息）
    - RFC 9110（HTTP 语义）
---

# API 设计指南

面向后端和全栈工程师的与框架无关的 API 设计指南。 10 个类别的 50 多条规则，按影响优先级排列。涵盖 REST、GraphQL 和 gRPC。

## 范围

**在以下情况下使用此技能：**
- 设计新的API或添加端点
- 审查 API 拉取请求
- 在 REST / GraphQL / gRPC 之间进行选择
- 编写OpenAPI规范
- 迁移现有 API 或对其进行版本控制

**不适合：**
- 特定于框架的实现细节（使用您的框架自己的技能/文档）
- 前端数据获取模式（使用 React Query / SWR 文档）
- 身份验证实施细节（使用您的身份验证库的文档）
- 数据库模式设计（→`数据库模式设计`）

## 需要上下文

在应用此技能之前，请收集：

|必填 |可选|
|----------|----------|
|目标消费者（浏览器、移动设备、服务）|项目中现有的API约定|
|预期请求量（RPS 估算）|当前 OpenAPI / Swagger 规范 |
|身份验证方法（JWT、API 密钥、OAuth）|速率限制要求|
|数据模型/领域实体|缓存策略|

---

## 快速入门清单

新的 API 端点？在编写代码之前先运行一下：

- [ ] 资源命名为**复数名词**（`/orders`，而不是`/getOrders`）
- [ ] URL 采用 **kebab-case**，正文字段采用 **camelCase**
- [ ] 正确的 **HTTP 方法**（GET=读取、POST=创建、PUT=替换、PATCH=部分、DELETE=删除）
- [ ] 正确的**状态代码**（201 已创建、422 验证、404 未找到...）
- [ ] 错误响应遵循 **RFC 9457** 信封
- [ ] **所有列表端点上的分页**（默认 20，最大 100）
- [ ] **需要身份验证**（承载令牌，而不是查询参数）
- [ ] **请求 ID** 位于响应标头中（`X-Request-Id`）
- [ ] **包含速率限制**标头
- [ ] 端点记录在 **OpenAPI 规范**中

---

## 快速导航

|需要…… |跳转至 |
|----------|---------|
|命名资源 URL | [1.资源建模](#1-资源建模-关键) |
|选择HTTP方法+状态码 | [3. HTTP 方法和状态代码](#3-http-methods--status-codes-ritic) |
|格式错误响应 | [4.错误处理](#4-错误处理-高) |
|添加分页或过滤 | [6.分页与过滤](#6-分页--过滤-高) |
|选择 API 风格（REST、GraphQL、gRPC）| [10. API 风格决策](#10-api-style-decision-tree) |
|对现有 API 进行版本控制 | [7.版本控制](#7-版本控制-中-高) |
|避免常见错误 | [反模式](#anti-patterns-checklist) |

---

## 1. 资源建模（关键）

### 核心规则```
✅ /users                         — plural noun
✅ /users/{id}/orders              — 1 level nesting
✅ /reviews?orderId={oid}          — flatten deep nesting with query params

❌ /getUsers                       — verb in URL
❌ /user                           — singular
❌ /users/{uid}/orders/{oid}/items/{iid}/reviews  — 3+ levels deep
```**最大嵌套：2 层。** 除此之外，通过过滤器提升到顶级资源。

### 域对齐

资源映射到**领域概念**，而不是数据库表：```
✅ /checkout-sessions       (domain aggregate)
✅ /shipping-labels          (domain concept)

❌ /tbl_order_header          (database table leak)
❌ /join_user_role            (internal schema leak)
```---

## 2. URL 和命名（关键）

|背景 |大会 |示例|
|--------|------------|---------|
|网址路径|烤肉串盒 | `/订单项目` |
| JSON 正文字段 |驼峰式 | `{ "firstName": "简" }` |
|查询参数 |驼峰命名法或蛇形命名法（保持一致） | `?sortBy=createdAt` |
|标题 |火车箱 | `X-请求-Id` |

**Python 例外：** 如果您的整个堆栈是 Python/snake_case，您可以在 JSON 中使用 `snake_case` — 但要 **在所有端点上保持一致**。```
✅ GET /users          ❌ GET /users/
✅ GET /reports/annual  ❌ GET /reports/annual.json
✅ POST /users          ❌ POST /users/create
```---

## 3. HTTP 方法和状态代码（关键）

### 方法语义

|方法|语义|幂等|安全|请求正文 |
|--------|---------|------------|-----|------------|
|获取 |阅读 | ✅ | ✅ | ❌从不|
|发布 |创建/操作| ❌ | ❌ | ✅ 永远 |
|放置|全面替换| ✅ | ❌ | ✅ 永远 |
|补丁|部分更新 | ❌* | ❌ | ✅ 永远 |
|删除|删除 | ✅ | ❌ | ❌很少|

### 状态代码快速参考

**成功：**

|代码|当 |响应正文 |
|------|------|--------------|
| 200 好 |获取、放置、修补成功 |资源/结果 |
| 201 已创建 | POST 创建的资源 |创建资源 + `Location` 标头 |
| 202 已接受 |异步操作开始 |作业 ID/状态 URL |
| 204 没有内容 | DELETE 成功，PUT 无正文 |无 |

**客户端错误：**

|代码|当 |关键区别|
|------|------|-----------------|
| 400 错误请求 |格式错误的语法 |甚至无法解析 |
| 401 未经授权 |缺少/无效的身份验证 | “你是谁？” |
| 403 禁止已认证，无权限 | “我认识你，但不” |
| 404 未找到 |资源不存在 |也可用于隐藏 403 |
| 409 冲突 |重复、版本不匹配 |国家冲突|
| 422 无法处理 |语法有效，验证失败 |语义错误 |
| 429 太多请求 |达到速率限制 |包括“之后重试”|

**服务器错误：** 500（意外）、502（上游失败）、503（过载）、504（上游超时）

---

## 4. 错误处理（高）

### 标准误差包络 (RFC 9457)

每个错误响应都使用以下格式：```json
{
  "type": "https://api.example.com/errors/insufficient-funds",
  "title": "Insufficient Funds",
  "status": 422,
  "detail": "Account balance $10.00 is less than withdrawal $50.00.",
  "instance": "/transactions/txn_abc123",
  "request_id": "req_7f3a8b2c",
  "errors": [
    { "field": "amount", "message": "Exceeds balance", "code": "INSUFFICIENT_BALANCE" }
  ]
}
```### 多语言实现

**打字稿（Express）：**```typescript
class AppError extends Error {
  constructor(
    public readonly title: string,
    public readonly status: number,
    public readonly detail: string,
    public readonly code: string,
  ) { super(detail); }
}

// Middleware
app.use((err, req, res, next) => {
  if (err instanceof AppError) {
    return res.status(err.status).json({
      type: `https://api.example.com/errors/${err.code}`,
      title: err.title, status: err.status,
      detail: err.detail, request_id: req.id,
    });
  }
  res.status(500).json({ title: 'Internal Error', status: 500, request_id: req.id });
});
```**Python（FastAPI）：**```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    def __init__(self, title: str, status: int, detail: str, code: str):
        self.title, self.status, self.detail, self.code = title, status, detail, code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={
        "type": f"https://api.example.com/errors/{exc.code}",
        "title": exc.title, "status": exc.status,
        "detail": exc.detail, "request_id": request.state.request_id,
    })
```### 铁律```
✅ Return RFC 9457 error envelope for ALL errors
✅ Include request_id in every error response
✅ Return per-field validation errors in `errors` array

❌ Never expose stack traces in production
❌ Never return 200 for errors
❌ Never swallow errors silently
```---

## 5. 身份验证和授权（高）```
✅ Authorization: Bearer eyJhbGci...      (header)
❌ GET /users?token=eyJhbGci...            (URL — appears in logs)

✅ 401 → "Who are you?"  (missing/invalid credentials)
✅ 403 → "You can't do this"  (authenticated, no permission)
✅ 404 → Hide resource existence  (use instead of 403 when needed)
```**速率限制标头（始终包含）：**```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1625097600
Retry-After: 30
```---

## 6. 分页和过滤（高）

### 光标与偏移量

|战略|当 |优点 |缺点 |
|----------|------|------|------|
| **光标**（首选）|大型/动态数据集 |一致，无跳跃|无法跳转至第 N 页 |
| **偏移** |小型/稳定的数据集，管理 UI |简单，页面跳转|插入/删除时漂移 |

**光标分页响应：**```json
{
  "data": [...],
  "pagination": { "next_cursor": "eyJpZCI6MTIwfQ", "has_more": true }
}
```**偏移分页响应：**```json
{
  "data": [...],
  "pagination": { "page": 3, "per_page": 20, "total": 256, "total_pages": 13 }
}
```**始终强制：** 默认 20 项，最多 100 项。

### 标准过滤器模式```
GET /orders?status=shipped&created_after=2025-01-01&sort=-created_at&fields=id,status
```|图案|大会 |
|--------|------------|
|精确匹配 | `？状态=已发货` |
|范围 | `?price_gte=10&price_lte=100` |
|日期范围 | `?created_after=2025-01-01&created_before=2025-12-31` |
|排序 | `?sort=field` (asc)、`?sort=-field` (desc) |
|稀疏领域 | `?fields=id,姓名,电子邮件` |
|搜索 | `?q=搜索+术语` |

---

## 7. 版本控制（中-高）

|战略|格式|最适合 |
|----------|--------|----------|
| **URL 路径**（推荐）| `/v1/用户` |公共 API |
| **标题** | `Api 版本：2` |内部 API |
| **查询参数** | `？版本=2` |遗留（避免）|

**非重大更改（无版本冲突）：**新的可选响应字段、新的端点、新的可选参数。

**重大更改（需要新版本）：** 删除/重命名字段、更改类型、更严格的验证、删除端点。

**弃用标头：**```
Sunset: Sat, 01 Mar 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.example.com/v2/users>; rel="successor-version"
```---

## 8.请求/响应设计（中）

### 一致的信封```json
{
  "data": { "id": "ord_123", "status": "pending", "total": 99.50 },
  "meta": { "request_id": "req_abc123", "timestamp": "2025-06-15T10:30:00Z" }
}
```### 关键规则

|规则|正确 |错误 |
|------|---------|--------|
|时间戳 | `“2025-06-15T10:30:00Z”`（ISO 8601）| `"06/15/2025"` 或 `1718447400` |
|公共 ID | UUID `"550e8400-..."` |自动递增 `42` |
|空与不存在（补丁）| `{ "nickname": null }` = 清除字段 |缺失字段 = 不更改 |
| HATEOAS（公共 API）| `"links": { "cancel": "/orders/123/cancel" }` |没有可发现性 |

---

## 9. 文档 — OpenAPI（中）

**设计优先的工作流程：**```
1. Write OpenAPI 3.1 spec
2. Review spec with stakeholders
3. Generate server stubs + client SDKs
4. Implement handlers
5. Validate responses against spec in CI
```每个端点文档：摘要、所有参数、请求正文+示例、所有响应代码+模式、身份验证要求。

---

## 10. API 风格决策树```
What kind of API?
│
├─ Browser + mobile clients, flexible queries
│   └─ GraphQL
│       Rules: DataLoader (no N+1), depth limit ≤7, Relay pagination
│
├─ Standard CRUD, public consumers, caching important
│   └─ REST (this guide)
│       Rules: Resources, HTTP methods, status codes, OpenAPI
│
├─ Service-to-service, high throughput, strong typing
│   └─ gRPC
│       Rules: Protobuf schemas, streaming for large data, deadlines
│
├─ Full-stack TypeScript, same team owns client + server
│   └─ tRPC
│       Rules: Shared types, no code generation needed
│
└─ Real-time bidirectional
    └─ WebSocket / SSE
        Rules: Heartbeat, reconnection, message ordering
```---

## 反模式清单

| ＃| ❌不要 | ✅ 改为 |
|---|---------|--------------|
| 1 | URL 中的动词 (`/getUser`) | HTTP 方法 + 名词资源 |
| 2 |错误返回 200 |正确的 4xx/5xx 状态代码 |
| 3 |混合命名风格 |每个上下文一个约定 |
| 4 |公开数据库 ID |公共标识符的 UUID |
| 5 |列表上没有分页 |始终分页（默认 20） |
| 6 |默默地吞下错误|结构化 RFC 9457 错误 |
| 7 | URL 查询中的令牌 |授权标头 |
| 8 |深度嵌套（3+层）|使用查询参数进行扁平化 |
| 9 |没有版本的中断更改 |维护兼容性或版本 |
| 10 | 10无速率限制 |通过标头实施+通信 |
| 11 | 11没有请求 ID |每个响应上的“X-Request-Id” |
| 12 | 12生产中的堆栈跟踪 |安全错误信息+内部日志|

---

## 常见问题

### 问题 1：“这应该是新资源还是子资源？”

**症状：** URL路径不断增长（`/users/{id}/orders/{id}/items/{id}/reviews`）

**规则：** 如果子实体本身有意义，则升级它。如果它仅存在于父上下文中，则保持其嵌套（最多 2 层）。```
/reviews?orderId=123      ✅  (reviews exist independently)
/orders/{id}/items         ✅  (items belong to orders, 1 level)
```### 问题 2：“PUT 还是 PATCH？”

**症状：** 团队无法就更新语义达成一致。

**规则：**
- PUT = 客户端发送**完整**资源（缺少字段→设置为默认/空）
- PATCH =客户端发送**仅更改的字段**（缺少字段→未更改）
- 当不确定时 → **PATCH** （更安全，不那么令人惊讶）

### 第 3 期：“400 还是 422？”

**症状：** 验证错误代码不一致。

**规则：**
- 400 = 根本无法解析请求（格式错误的 JSON、错误的内容类型）
- 422 = 解析正常，但值验证失败（电子邮件无效、数量为负）