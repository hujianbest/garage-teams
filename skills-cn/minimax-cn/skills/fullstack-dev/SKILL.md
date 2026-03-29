---
名称：fullstack-dev
描述：|
  全栈后端架构和前后端集成指南。
  触发时机：构建全栈应用程序、使用前端创建 REST API、搭建后端服务、
  构建待办事项应用程序、构建 CRUD 应用程序、构建实时应用程序、构建聊天应用程序、
  Express + React、Next.js API、Node.js 后端、Python 后端、Go 后端、
  设计服务层，实现错误处理，管理配置/身份验证，
  设置 API 客户端、实施身份验证流程、处理文件上传、
  添加实时功能（SSE/WebSocket）、生产强化。
  不要在以下情况下触发：纯前端 UI 工作、纯 CSS/样式、仅数据库模式。
许可证：麻省理工学院
元数据：
  类别：全栈
  版本：“1.0.0”
  来源：
    - 十二因素应用程序 (12factor.net)
    - 干净的建筑（罗伯特·C·马丁）
    - 领域驱动设计（埃里克·埃文斯）
    - 企业应用程序架构模式（Martin Fowler）
    - Martin Fowler（测试金字塔、合同测试）
    - Google SRE 手册（发布工程）
    - ThoughtWorks技术雷达
---

# 全栈开发实践

## 强制工作流程 — 按顺序执行以下步骤

**当此技能被触发时，您必须遵循此工作流程才能编写任何代码。**

### 第 0 步：收集需求

在搭建任何东西之前，请用户澄清（或从上下文推断）：

1. **Stack**：后端和前端的语言/框架（例如 Express + React、Django + Vue、Go + HTMX）
2. **服务类型**：纯 API、全栈单体还是微服务？
3. **数据库**：SQL（PostgreSQL、SQLite、MySQL）还是NoSQL（MongoDB、Redis）？
4. **集成**：REST、GraphQL、tRPC 还是 gRPC？
5. **实时**：需要吗？如果是，SSE、WebSocket 还是轮询？
6. **授权**：需要吗？如果是，JWT、会话、OAuth 还是第三方（Clerk、Auth.js）？

如果用户已在请求中指定这些内容，请跳过询问并继续。

### 步骤 1：架构决策

根据需求，在编码之前做出并陈述这些决定：

|决定|选项|参考|
|----------|---------|------------|
|项目结构|功能优先（推荐）与层优先 | [第 1 节](#1-项目结构--分层-关键) |
| API客户端方法|类型化获取 / React 查询 / tRPC / OpenAPI 代码生成 | [第 5 节](#5-api-client-patterns-medium) |
|授权策略| JWT + 刷新/会话/第三方| [第 6 节](#6-身份验证--中间件-高) |
|实时法 |轮询/SSE/WebSocket | [第 11 节](#11-实时模式-中) |
|错误处理 |类型化错误层次结构 + 全局处理程序 | [第 3 节](#3-错误处理--弹性-高) |

简要解释每个选择（每个决定 1 句话）。

### 第 2 步：带有清单的支架

使用下面适当的清单。确保所有检查项目均已实施 - 不要跳过任何项目。

### 步骤 3：实施以下模式

按照本文档中的模式编写代码。实现每个部分时请参考特定部分。

### 第 4 步：测试和验证

实施后，在声明完成之前运行这些检查：

1. **构建检查**：确保后端和前端编译没有错误```bash
   # Backend
   cd server && npm run build
   # Frontend
   cd client && npm run build
   ```2. **启动&冒烟测试**：启动服务器，验证关键端点返回预期响应```bash
   # Start server, then test
   curl http://localhost:3000/health
   curl http://localhost:3000/api/<resource>
   ```3. **集成检查**：验证前端是否可以连接到后端（CORS、API 基本 URL、身份验证流程）
4. **实时检查**（如果适用）：打开两个浏览器选项卡，验证更改同步

如果任何检查失败，请先解决问题，然后再继续。

### 步骤 5：移交总结

向用户提供简要摘要：

- **构建了什么**：已实现的功能和端点列表
- **如何运行**：启动后端和前端的确切命令
- **缺少什么/后续步骤**：任何推迟的项目、已知的限制或建议的改进
- **关键文件**：列出用户应该了解的最重要的文件

---

## 范围

**在以下情况下使用此技能：**
- 构建全栈应用程序（后端+前端）
- 搭建新的后端服务或 API
- 设计服务层和模块边界
- 实施数据库访问、缓存或后台作业
- 编写错误处理、日志记录或配置管理
- 检查后端代码的架构问题
- 生产硬化
- 设置 API 客户端、身份验证流程、文件上传或实时功能

**不适合：**
- 纯粹的前端/UI 问题（使用您的前端框架的文档）
- 纯数据库架构设计，无后端上下文

---

## 快速入门 — 新后端服务清单

- [ ] 项目采用 **功能优先** 结构搭建
- [ ] 配置 **集中式**，环境变量 **在启动时验证**（快速失败）
- [ ] **定义了类型化错误层次结构**（不是通用的“错误”）
- [ ] **全局错误处理程序**中间件
- [ ] **带有请求 ID 传播的结构化 JSON 日志记录**
- [ ] 数据库：**迁移**设置，**连接池**配置
- [ ] **所有端点上的输入验证**（Zod / Pydantic / Go 验证器）
- [ ] **身份验证中间件**到位
- [ ] **运行状况检查**端点（`/health`、`/ready`）
- [ ] **正常关闭**处理 (SIGTERM)
- [ ] **CORS** 配置（显式来源，而不是“*”）
- [ ] **安全标头**（头盔或等效物）
- [ ] `.env.example` 已提交（没有真正的秘密）

## 快速入门 — 前后端集成清单

- [ ] **API 客户端** 配置（生成类型化获取包装器、React Query、tRPC 或 OpenAPI）
- [ ] **来自环境变量的基本 URL**（未硬编码）
- [ ] **身份验证令牌**自动附加到请求（拦截器/中间件）
- [ ] **错误处理** — API 错误映射到面向用户的消息
- [ ] **加载状态**已处理（骨架/旋转器，不是空白屏幕）
- [ ] **跨界类型安全**（共享类型、OpenAPI 或 tRPC）
- [ ] **CORS** 配置有显式来源（生产中不是“*”）
- [ ] **刷新令牌**流程已实施（httpOnly cookie + 401 上的透明重试）

---

## 快速导航

|需要…… |跳转至 |
|----------|---------|
|组织项目文件夹 | [1.项目结构](#1-项目结构--分层关键) |
|管理配置+机密 | [2.配置](#2-配置--环境关键)|
|正确处理错误 | [3.错误处理](#3-错误处理--弹性-高) |
|编写数据库代码 | [4.数据库访问模式](#4-database-access-patterns-high) |
|从前端设置 API 客户端 | [5. API 客户端模式](#5-api-client-patterns-medium) |
|添加身份验证中间件 | [6.身份验证和中间件](#6-身份验证--中间件-高) |
|设置日志记录 | [7.日志记录和可观测性](#7-日志记录--可观测性-中-高)|
|添加后台作业 | [8.后台作业](#8-background-jobs--async-medium) |
|实施缓存 | [9.缓存](#9-缓存模式-中) |
|上传文件（预先指定的 URL，多部分）| [10.文件上传模式](#10-file-upload-patterns-medium) |
|添加实时功能（SSE、WebSocket）| [11.实时模式](#11-实时模式-中) |
|处理前端 UI 中的 API 错误 | [12.跨界错误处理](#12-跨界错误处理-中) |
|生产硬化 | [13.生产硬化](#13-生产-硬化-中) |
|设计 API 端点 | [API设计](references/api-design.md) |
|设计数据库架构| [数据库架构](references/db-schema.md) |
|身份验证流程（JWT、刷新、Next.js SSR、RBAC）| [参考文献/auth-flow.md](参考文献/auth-flow.md) |
| CORS、环境变量、环境管理 | [参考文献/环境管理.md](参考文献/环境管理.md) |

---

## 核心原则（七大铁律）```
1. ✅ Organize by FEATURE, not by technical layer
2. ✅ Controllers never contain business logic
3. ✅ Services never import HTTP request/response types
4. ✅ All config from env vars, validated at startup, fail fast
5. ✅ Every error is typed, logged, and returns consistent format
6. ✅ All input validated at the boundary — trust nothing from client
7. ✅ Structured JSON logging with request ID — not console.log
```---

## 1. 项目结构和分层（关键）

### 功能优先的组织```
✅ Feature-first                    ❌ Layer-first
src/                                src/
  orders/                             controllers/
    order.controller.ts                 order.controller.ts
    order.service.ts                    user.controller.ts
    order.repository.ts               services/
    order.dto.ts                        order.service.ts
    order.test.ts                       user.service.ts
  users/                              repositories/
    user.controller.ts                  ...
    user.service.ts
  shared/
    database/
    middleware/
```### 三层架构```
Controller (HTTP) → Service (Business Logic) → Repository (Data Access)
```|层|责任| ❌从不|
|--------|----------------|---------|
|控制器|解析请求、验证、调用服务、格式化响应 |业务逻辑、数据库查询 |
|服务 |业务规则、编排、事务管理 | HTTP 类型（req/res），直接 DB |
|存储库 |数据库查询、外部API调用|业务逻辑、HTTP 类型 |

### 依赖注入（所有语言）

**打字稿：**```typescript
class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,    // ✅ injected interface
    private readonly emailService: EmailService,
  ) {}
}
```**Python：**```python
class OrderService:
    def __init__(self, order_repo: OrderRepository, email_service: EmailService):
        self.order_repo = order_repo                 # ✅ injected
        self.email_service = email_service
```**去：**```go
type OrderService struct {
    orderRepo    OrderRepository                      // ✅ interface
    emailService EmailService
}

func NewOrderService(repo OrderRepository, email EmailService) *OrderService {
    return &OrderService{orderRepo: repo, emailService: email}
}
```---

## 2. 配置和环境（关键）

### 集中式、类型化、快速失败

**打字稿：**```typescript
const config = {
  port: parseInt(process.env.PORT || '3000', 10),
  database: { url: requiredEnv('DATABASE_URL'), poolSize: intEnv('DB_POOL_SIZE', 10) },
  auth: { jwtSecret: requiredEnv('JWT_SECRET'), expiresIn: process.env.JWT_EXPIRES_IN || '1h' },
} as const;

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var: ${name}`);  // fail fast
  return value;
}
```**Python：**```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str                        # required — app won't start without it
    jwt_secret: str                          # required
    port: int = 3000                         # optional with default
    db_pool_size: int = 10
    class Config:
        env_file = ".env"

settings = Settings()                        # fails fast if DATABASE_URL missing
```### 规则```
✅ All config via environment variables (Twelve-Factor)
✅ Validate required vars at startup — fail fast
✅ Type-cast at config layer, not at usage sites
✅ Commit .env.example with dummy values

❌ Never hardcode secrets, URLs, or credentials
❌ Never commit .env files
❌ Never scatter process.env / os.environ throughout code
```---

## 3. 错误处理和弹性（高）

### 类型错误层次结构```typescript
// Base (TypeScript)
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly isOperational: boolean = true,
  ) { super(message); }
}
class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404);
  }
}
class ValidationError extends AppError {
  constructor(public readonly errors: FieldError[]) {
    super('Validation failed', 'VALIDATION_ERROR', 422);
  }
}
```

```python
# Base (Python)
class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int):
        self.message, self.code, self.status_code = message, code, status_code

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} not found: {id}", "NOT_FOUND", 404)
```### 全局错误处理程序```typescript
// TypeScript (Express)
app.use((err, req, res, next) => {
  if (err instanceof AppError && err.isOperational) {
    return res.status(err.statusCode).json({
      title: err.code, status: err.statusCode,
      detail: err.message, request_id: req.id,
    });
  }
  logger.error('Unexpected error', { error: err.message, stack: err.stack, request_id: req.id });
  res.status(500).json({ title: 'Internal Error', status: 500, request_id: req.id });
});
```### 规则```
✅ Typed, domain-specific error classes
✅ Global error handler catches everything
✅ Operational errors → structured response
✅ Programming errors → log + generic 500
✅ Retry transient failures with exponential backoff

❌ Never catch and ignore errors silently
❌ Never return stack traces to client
❌ Never throw generic Error('something')
```---

## 4. 数据库访问模式（高）

### 总是迁移```bash
# TypeScript (Prisma)           # Python (Alembic)              # Go (golang-migrate)
npx prisma migrate dev          alembic revision --autogenerate  migrate -source file://migrations
npx prisma migrate deploy       alembic upgrade head             migrate -database $DB up
```

```
✅ Schema changes via migrations, never manual SQL
✅ Migrations must be reversible
✅ Review migration SQL before production
❌ Never modify production schema manually
```### N+1预防```typescript
// ❌ N+1: 1 query + N queries
const orders = await db.order.findMany();
for (const o of orders) { o.items = await db.item.findMany({ where: { orderId: o.id } }); }

// ✅ Single JOIN query
const orders = await db.order.findMany({ include: { items: true } });
```### 多步写入事务```typescript
await db.$transaction(async (tx) => {
  const order = await tx.order.create({ data: orderData });
  await tx.inventory.decrement({ productId, quantity });
  await tx.payment.create({ orderId: order.id, amount });
});
```### 连接池

池大小 = `(CPU 核心 × 2) + 主轴计数`（从 10-20 开始）。始终设置连接超时。使用 PgBouncer 进行无服务器。

---

## 5. API 客户端模式（中）

前端和后端之间的“粘合层”。选择适合您的团队和堆栈的方法。

### 选项 A：类型化获取包装器（简单，无依赖性）```typescript
// lib/api-client.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

class ApiError extends Error {
  constructor(public status: number, public body: any) {
    super(body?.detail || body?.message || `API error ${status}`);
  }
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();  // from cookie / memory / context

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const apiClient = {
  get: <T>(path: string) => api<T>(path),
  post: <T>(path: string, data: unknown) => api<T>(path, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(path: string, data: unknown) => api<T>(path, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(path: string, data: unknown) => api<T>(path, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(path: string) => api<T>(path, { method: 'DELETE' }),
};
```### 选项 B：React 查询 + 类型化客户端（推荐用于 React）```typescript
// hooks/use-orders.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface Order { id: string; total: number; status: string; }
interface CreateOrderInput { items: { productId: string; quantity: number }[] }

export function useOrders() {
  return useQuery({
    queryKey: ['orders'],
    queryFn: () => apiClient.get<{ data: Order[] }>('/api/orders'),
    staleTime: 1000 * 60,  // 1 min
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateOrderInput) =>
      apiClient.post<{ data: Order }>('/api/orders', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}

// Usage in component:
function OrdersPage() {
  const { data, isLoading, error } = useOrders();
  const createOrder = useCreateOrder();
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorBanner error={error} />;
  // ...
}
```### 选项 C：tRPC（同一团队拥有双方）```typescript
// server: trpc/router.ts
export const appRouter = router({
  orders: router({
    list: publicProcedure.query(async () => {
      return db.order.findMany({ include: { items: true } });
    }),
    create: protectedProcedure
      .input(z.object({ items: z.array(orderItemSchema) }))
      .mutation(async ({ input, ctx }) => {
        return orderService.create(ctx.user.id, input);
      }),
  }),
});
export type AppRouter = typeof appRouter;

// client: automatic type safety, no code generation
const { data } = trpc.orders.list.useQuery();
const createOrder = trpc.orders.create.useMutation();
```### 选项 D：OpenAPI 生成的客户端（公共/多消费者 API）```bash
npx openapi-typescript-codegen \
  --input http://localhost:3001/api/openapi.json \
  --output src/generated/api \
  --client axios
```### 决定：哪个 API 客户端？

|方法|当 |类型安全 |努力|
|----------|------|-------------|--------|
|类型化获取包装器 |简单的应用程序，小团队 |手动类型|低|
| React 查询 + 获取 | React 应用程序、服务器状态 |手动类型|中等|
| tRPC |双方都是 TypeScript | 同一团队自动|低|
| OpenAPI 生成 |公共API，多消费者 |自动|中等|
| GraphQL 代码生成 | GraphQL API |自动|中等|

---

## 6. 身份验证和中间件（高）

> **完整参考：** [references/auth-flow.md](references/auth-flow.md) — JWT 承载流程、自动令牌刷新、Next.js 服务器端身份验证、RBAC 模式、后端中间件顺序。

### 标准中间件顺序```
Request → 1.RequestID → 2.Logging → 3.CORS → 4.RateLimit → 5.BodyParse
       → 6.Auth → 7.Authz → 8.Validation → 9.Handler → 10.ErrorHandler → Response
```### JWT 规则```
✅ Short expiry access token (15min) + refresh token (server-stored)
✅ Minimal claims: userId, roles (not entire user object)
✅ Rotate signing keys periodically

❌ Never store tokens in localStorage (XSS risk)
❌ Never pass tokens in URL query params
```### RBAC 模式```typescript
function authorize(...roles: Role[]) {
  return (req, res, next) => {
    if (!req.user) throw new UnauthorizedError();
    if (!roles.some(r => req.user.roles.includes(r))) throw new ForbiddenError();
    next();
  };
}
router.delete('/users/:id', authenticate, authorize('admin'), deleteUser);
```### 身份验证令牌自动刷新```typescript
// lib/api-client.ts — transparent refresh on 401
async function apiWithRefresh<T>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    return await api<T>(path, options);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      const refreshed = await api<{ accessToken: string }>('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',  // send httpOnly cookie
      });
      setAuthToken(refreshed.accessToken);
      return api<T>(path, options);  // retry
    }
    throw err;
  }
}
```---

## 7. 日志记录和可观测性（中-高）

### 结构化 JSON 日志记录```typescript
// ✅ Structured — parseable, filterable, alertable
logger.info('Order created', {
  orderId: order.id, userId: user.id, total: order.total,
  items: order.items.length, duration_ms: Date.now() - startTime,
});
// Output: {"level":"info","msg":"Order created","orderId":"ord_123",...}

// ❌ Unstructured — useless at scale
console.log(`Order created for user ${user.id} with total ${order.total}`);
```### 日志级别

|水平|当 |生产？ |
|--------|------|------------|
|错误 |需要立即关注 | ✅ 永远 |
|警告|意外但已处理 | ✅ 永远 |
|信息 |正常运营，审计追踪| ✅ 永远 |
|调试|开发故障排除 | ❌ 仅限开发 |

### 规则```
✅ Request ID in every log entry (propagated via middleware)
✅ Log at layer boundaries (request in, response out, external call)
❌ Never log passwords, tokens, PII, or secrets
❌ Never use console.log in production code
```---

## 8. 后台作业和异步（中）

### 规则```
✅ All jobs must be IDEMPOTENT (same job running twice = same result)
✅ Failed jobs → retry (max 3) → dead letter queue → alert
✅ Workers run as SEPARATE processes (not threads in API server)

❌ Never put long-running tasks in request handlers
❌ Never assume job runs exactly once
```### 幂等作业模式```typescript
async function processPayment(data: { orderId: string }) {
  const order = await orderRepo.findById(data.orderId);
  if (order.paymentStatus === 'completed') return;  // already processed
  await paymentGateway.charge(order);
  await orderRepo.updatePaymentStatus(order.id, 'completed');
}
```---

## 9. 缓存模式（中）

### 缓存旁路（延迟加载）```typescript
async function getUser(id: string): Promise<User> {
  const cached = await redis.get(`user:${id}`);
  if (cached) return JSON.parse(cached);

  const user = await userRepo.findById(id);
  if (!user) throw new NotFoundError('User', id);

  await redis.set(`user:${id}`, JSON.stringify(user), 'EX', 900);  // 15min TTL
  return user;
}
```### 规则```
✅ ALWAYS set TTL — never cache without expiry
✅ Invalidate on write (delete cache key after update)
✅ Use cache for reads, never for authoritative state

❌ Never cache without TTL (stale data is worse than slow data)
```|数据类型 |建议的 TTL |
|------------|--------------|
|用户简介 | 5-15 分钟 |
|产品目录| 1-5 分钟 |
|配置/功能标志| 30-60 秒 |
|会议|比赛时长|

---

## 10. 文件上传模式（中）

### 选项 A：预签名 URL（推荐用于大文件）```
Client → GET /api/uploads/presign?filename=photo.jpg&type=image/jpeg
Server → { uploadUrl: "https://s3.../presigned", fileKey: "uploads/abc123.jpg" }
Client → PUT uploadUrl (direct to S3, bypasses your server)
Client → POST /api/photos { fileKey: "uploads/abc123.jpg" }  (save reference)
```**后端：**```typescript
app.get('/api/uploads/presign', authenticate, async (req, res) => {
  const { filename, type } = req.query;
  const key = `uploads/${crypto.randomUUID()}-${filename}`;
  const url = await s3.getSignedUrl('putObject', {
    Bucket: process.env.S3_BUCKET, Key: key,
    ContentType: type, Expires: 300,  // 5 min
  });
  res.json({ uploadUrl: url, fileKey: key });
});
```**前端：**```typescript
async function uploadFile(file: File) {
  const { uploadUrl, fileKey } = await apiClient.get<PresignResponse>(
    `/api/uploads/presign?filename=${file.name}&type=${file.type}`
  );
  await fetch(uploadUrl, { method: 'PUT', body: file, headers: { 'Content-Type': file.type } });
  return apiClient.post('/api/photos', { fileKey });
}
```### 选项 B：多部分（小文件 < 10MB）```typescript
// Frontend
const formData = new FormData();
formData.append('file', file);
formData.append('description', 'Profile photo');
const res = await fetch('/api/upload', { method: 'POST', body: formData });
// Note: do NOT set Content-Type header — browser sets boundary automatically
```### 决定

|方法|文件大小 |服务器负载 |复杂性 |
|--------|------------|-------------|------------|
|预签名 URL |任意（建议 > 5MB）|无（直接存储）|中等|
|多部分| < 10MB |高（通过服务器传输）|低|
|分块/可恢复 | > 100MB |中等|高|

---

## 11. 实时模式（中）

### 选项 A：服务器发送事件 (SSE) — 单向服务器 → 客户端

最适合：通知、实时反馈、流式人工智能响应。

**后端（快速）：**```typescript
app.get('/api/events', authenticate, (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
  });
  const send = (event: string, data: unknown) => {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  };
  const unsubscribe = eventBus.subscribe(req.user.id, (event) => {
    send(event.type, event.payload);
  });
  req.on('close', () => unsubscribe());
});
```**前端：**```typescript
function useServerEvents(userId: string) {
  useEffect(() => {
    const source = new EventSource(`/api/events?userId=${userId}`);
    source.addEventListener('notification', (e) => {
      showToast(JSON.parse(e.data).message);
    });
    source.onerror = () => { source.close(); setTimeout(() => /* reconnect */, 3000); };
    return () => source.close();
  }, [userId]);
}
```### 选项 B：WebSocket — 双向

最适合：聊天、协作编辑、游戏。

**后端（ws库）：**```typescript
import { WebSocketServer } from 'ws';
const wss = new WebSocketServer({ server: httpServer, path: '/ws' });
wss.on('connection', (ws, req) => {
  const userId = authenticateWs(req);
  if (!userId) { ws.close(4001, 'Unauthorized'); return; }
  ws.on('message', (raw) => handleMessage(userId, JSON.parse(raw.toString())));
  ws.on('close', () => cleanupUser(userId));
  const interval = setInterval(() => ws.ping(), 30000);
  ws.on('pong', () => { /* alive */ });
  ws.on('close', () => clearInterval(interval));
});
```**前端：**```typescript
function useWebSocket(url: string) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  useEffect(() => {
    const socket = new WebSocket(url);
    socket.onopen = () => setWs(socket);
    socket.onclose = () => setTimeout(() => /* reconnect */, 3000);
    return () => socket.close();
  }, [url]);
  const send = useCallback((data: unknown) => ws?.send(JSON.stringify(data)), [ws]);
  return { ws, send };
}
```### 选项 C：轮询（最简单，无基础设施）```typescript
function useOrderStatus(orderId: string) {
  return useQuery({
    queryKey: ['order-status', orderId],
    queryFn: () => apiClient.get<Order>(`/api/orders/${orderId}`),
    refetchInterval: (query) => {
      if (query.state.data?.status === 'completed') return false;
      return 5000;
    },
  });
}
```### 决定

|方法|方向 |复杂性 |当 |
|--------|---------|------------|-----|
|投票 |客户端→服务器|低|简单的状态检查，< 10 个客户端 |
|上交所 |服务器→客户端|中等|通知、提要、人工智能流 |
| WebSocket |双向|高|聊天、协作、游戏 |

---

## 12. 跨界错误处理（中）

### API 错误 → 面向用户的消息```typescript
// lib/error-handler.ts
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401: return 'Please log in to continue.';
      case 403: return 'You don\'t have permission to do this.';
      case 404: return 'The item you\'re looking for doesn\'t exist.';
      case 409: return 'This conflicts with an existing item.';
      case 422:
        const fields = error.body?.errors;
        if (fields?.length) return fields.map((f: any) => f.message).join('. ');
        return 'Please check your input.';
      case 429: return 'Too many requests. Please wait a moment.';
      default: return 'Something went wrong. Please try again.';
    }
  }
  if (error instanceof TypeError && error.message === 'Failed to fetch') {
    return 'Cannot connect to server. Check your internet connection.';
  }
  return 'An unexpected error occurred.';
}
```### React 查询全局错误处理程序```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    mutations: { onError: (error) => toast.error(getErrorMessage(error)) },
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof ApiError && error.status < 500) return false;
        return failureCount < 3;
      },
    },
  },
});
```### 规则```
✅ Map every API error code to a human-readable message
✅ Show field-level validation errors next to form inputs
✅ Auto-retry on 5xx (max 3, with backoff), never on 4xx
✅ Redirect to login on 401 (after refresh attempt fails)
✅ Show "offline" banner when fetch fails with TypeError

❌ Never show raw API error messages to users ("NullPointerException")
❌ Never silently swallow errors (show toast or log)
❌ Never retry 4xx errors (client is wrong, retrying won't help)
```### 集成决策树```
Same team owns frontend + backend?
│
├─ YES, both TypeScript
│   └─ tRPC (end-to-end type safety, zero codegen)
│
├─ YES, different languages
│   └─ OpenAPI spec → generated client (type safety via codegen)
│
├─ NO, public API
│   └─ REST + OpenAPI → generated SDKs for consumers
│
└─ Complex data needs, multiple frontends
    └─ GraphQL + codegen (flexible queries per client)

Real-time needed?
│
├─ Server → Client only (notifications, feeds, AI streaming)
│   └─ SSE (simplest, auto-reconnect, works through proxies)
│
├─ Bidirectional (chat, collaboration)
│   └─ WebSocket (need heartbeat + reconnection logic)
│
└─ Simple status polling (< 10 clients)
    └─ React Query refetchInterval (no infrastructure needed)
```---

## 13. 生产强化（中）

### 健康检查```typescript
app.get('/health', (req, res) => res.json({ status: 'ok' }));           // liveness
app.get('/ready', async (req, res) => {                                   // readiness
  const checks = {
    database: await checkDb(), redis: await checkRedis(), 
  };
  const ok = Object.values(checks).every(c => c.status === 'ok');
  res.status(ok ? 200 : 503).json({ status: ok ? 'ok' : 'degraded', checks });
});
```### 优雅关闭```typescript
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received');
  server.close();              // stop new connections
  await drainConnections();    // finish in-flight
  await closeDatabase();
  process.exit(0);
});
```### 安全检查表```
✅ CORS: explicit origins (never '*' in production)
✅ Security headers (helmet / equivalent)
✅ Rate limiting on public endpoints
✅ Input validation on ALL endpoints (trust nothing)
✅ HTTPS enforced
❌ Never expose internal errors to clients
```---

## 反模式

| ＃| ❌不要 | ✅ 改为 |
|---|---------|--------------|
| 1 |路由/控制器中的业务逻辑 |移至服务层|
| 2 | `process.env` 散布各处 |集中类型化配置 |
| 3 |用于日志记录的`console.log`结构化 JSON 记录器 |
| 4 |通用 `Error('oops')` |类型错误层次结构 |
| 5 |控制器中的直接数据库调用 |存储库模式|
| 6 |没有输入验证 |在边界处验证（Zod/Pydantic）|
| 7 |静默捕获错误 |记录+重新抛出或返回错误|
| 8 |没有健康检查端点 | `/health` + `/ready` |
| 9 |硬编码的配置/秘密 |环境变量|
| 10 | 10没有正常关机|正确处理SIGTERM |
| 11 | 11在前端硬编码 API URL |环境变量（`NEXT_PUBLIC_API_URL`）|
| 12 | 12将 JWT 存储在 localStorage |内存 + httpOnly 刷新 cookie |
| 13 |向用户显示原始 API 错误 |映射到人类可读的消息 |
| 14 | 14重试 4xx 错误 |仅重试 5xx（服务器故障）|
| 15 | 15跳过加载状态 |获取时的骷髅/旋转器 |
| 16 | 16通过API服务器上传大文件 |预签名 URL → 直接到 S3 |
| 17 | 17实时数据民意调查| SSE 或 WebSocket |
| 18 | 18重复类型前端 + 后端 |共享类型、tRPC 或 OpenAPI codegen |

---

## 常见问题

### 问题 1：“这个业务规则去哪里了？”

**规则：** 如果涉及HTTP（请求解析、状态码、标头）→控制器。如果涉及业务决策（定价、权限、规则）→服务。如果它触及数据库→存储库。

### 问题 2：“服务变得太大了”

**症状：** 一个服务文件 > 500 行，包含 20 多个方法。

**修复：** 按子域分割。 `OrderService` → `OrderCreationService` + `OrderFulfillmentService` + `OrderQueryService`。每个人都专注于一个工作流程。

### 问题 3：“测试很慢，因为它们访问了数据库”

**修复：** 单元测试模拟存储库层（快速）。集成测试使用测试容器或事务回滚（真正的数据库，仍然很快）。切勿在集成测试中模拟服务层。

---

## 参考文档

该技能包括针对专业主题的深入参考。当您需要详细指导时，请阅读相关参考资料。

|需要…… |参考|
|----------|------------|
|编写后端测试（单元、集成、e2e、合同、性能）| [参考文献/测试策略.md](参考文献/测试策略.md) |
|部署前验证版本（6 门清单）| [参考文献/release-checklist.md](参考文献/release-checklist.md) |
|选择技术堆栈（语言、框架、数据库、基础设施）| [参考文献/技术选择.md](参考文献/技术选择.md) |
|使用 Django / DRF 构建（模型、视图、序列化器、管理）| [参考文献/django-best-practices.md](参考文献/django-best-practices.md) |
|设计 REST/GraphQL/gRPC 端点（URL、状态代码、分页）| [参考资料/api-design.md](参考资料/api-design.md) |
|设计数据库架构、索引、迁移、多租户 | [参考文献/db-schema.md](参考文献/db-schema.md) |
|身份验证流程（JWT 承载、令牌刷新、Next.js SSR、RBAC、中间件顺序）| [参考文献/auth-flow.md](参考文献/auth-flow.md) |
| CORS 配置、每个环境的环境变量、常见 CORS 问题 | [参考文献/环境管理.md](参考文献/环境管理.md) |