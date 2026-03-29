# 后端测试策略

后端和全栈应用程序的综合测试指南。涵盖完整的测试金字塔，重点关注 API 集成测试、数据库测试、合约测试和性能测试。

## 快速入门清单

- [ ] **配置测试运行器**（Jest/Vitest、Pytest、Go 测试）
- [ ] **测试数据库**就绪（Docker 容器或内存中）
- [ ] **数据库隔离** 每次测试（事务回滚或截断）
- [ ] **通用实体（用户、订单、产品）的测试工厂**
- [ ] **Auth helper** 生成用于测试的令牌
- [ ] **CI pipeline** 使用真实数据库服务运行测试
- [ ] **强制覆盖阈值** (≥ 80%)

---

## 测试金字塔```
         ╱╲        E2E (few, slow) — full flows across services
        ╱  ╲
       ╱────╲       Integration (moderate) — API + DB + external
      ╱      ╲
     ╱────────╲      Unit (many, fast) — pure business logic
    ╱__________╲
```|水平|什么 |速度|计数|
|--------|------|--------|--------|
|单位|纯函数、业务逻辑、无I/O | < 10 毫秒 | 70% 以上的测试 |
|整合 | API 路由 + 真实数据库 + 模拟外部 | 50-500 毫秒 | 〜20% |
|端到端|跨已部署服务的完整用户流 | 1-30 秒 | 〜10% |
|合同|服务之间的API兼容性| < 100 毫秒 |每个 API 边界 |
|性能|负载、压力、浸泡 |分钟 |每个关键路径|

---

## 1. API 集成测试（关键）

### 每个端点要测试什么

|方面|编写测试|
|--------|----------------|
|幸福之路|正确的输入→预期的响应+正确的数据库状态|
|授权 |无令牌 → 401，坏令牌 → 401，已过期 → 401 |
|授权|错误的角色 → 403，不是所有者 → 403 |
|验证 |缺失字段 → 422，错误类型 → 422，边界值 |
|没有找到|无效 ID → 404，已删除资源 → 404 |
|冲突|重复创建 → 409，过时更新 → 409 |
|幂等性 |两次相同的请求 → 相同的结果 |
|副作用 |数据库状态更改、事件发出、缓存失效 |
|错误格式|所有错误均符合 RFC 9457 信封 |

### TypeScript（玩笑+超级测试）```typescript
describe('POST /api/orders', () => {
  let token: string;
  let product: Product;

  beforeAll(async () => {
    await resetDatabase();
    const user = await createTestUser({ role: 'customer' });
    token = await getAuthToken(user);
    product = await createTestProduct({ price: 29.99, stock: 10 });
  });

  it('creates order → 201 + correct DB state', async () => {
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [{ productId: product.id, quantity: 2 }] });

    expect(res.status).toBe(201);
    expect(res.body.data.total).toBe(59.98);

    const updated = await db.product.findUnique({ where: { id: product.id } });
    expect(updated!.stock).toBe(8);
  });

  it('rejects without auth → 401', async () => {
    const res = await request(app).post('/api/orders').send({ items: [] });
    expect(res.status).toBe(401);
  });

  it('rejects empty items → 422', async () => {
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [] });
    expect(res.status).toBe(422);
    expect(res.body.errors[0].field).toBe('items');
  });
});
```### Python（Pytest + FastAPI TestClient）```python
@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_create_order_success(client, auth_headers, test_product):
    response = client.post("/api/orders", json={
        "items": [{"product_id": test_product.id, "quantity": 2}]
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["total"] == 59.98

def test_create_order_no_auth(client):
    response = client.post("/api/orders", json={"items": []})
    assert response.status_code == 401

def test_create_order_empty_items(client, auth_headers):
    response = client.post("/api/orders", json={"items": []}, headers=auth_headers)
    assert response.status_code == 422
```---

## 2. 数据库测试（高）

### 测试隔离策略

|战略|速度|现实主义|当 |
|----------|--------|---------|-----|
| **事务回滚** | ⚡ 最快|中等|默认单位 + 积分 |
| **截断** |快|高|当无法回滚时 |
| **测试容器** |启动慢|最高| CI管道，全面集成|

**事务回滚（推荐默认）：**```typescript
let tx: Transaction;
beforeEach(async () => { tx = await db.beginTransaction(); });
afterEach(async () => { await tx.rollback(); });
```**Docker 测试容器 (CI)：**```yaml
# docker-compose.test.yml
services:
  test-db:
    image: postgres:16-alpine
    tmpfs: /var/lib/postgresql/data   # RAM disk for speed
    environment:
      POSTGRES_DB: myapp_test
```### 测试工厂（不是原始 SQL）```typescript
// factories/user.factory.ts
import { faker } from '@faker-js/faker';

export function buildUser(overrides: Partial<User> = {}): CreateUserDTO {
  return {
    email: faker.internet.email(),
    firstName: faker.person.firstName(),
    role: 'customer',
    ...overrides,
  };
}
export async function createUser(overrides = {}) {
  return db.user.create({ data: buildUser(overrides) });
}
```

```python
# factories/user_factory.py
import factory
from faker import Faker

class UserFactory(factory.Factory):
    class Meta:
        model = User
    email = factory.LazyAttribute(lambda _: Faker().email())
    first_name = factory.LazyAttribute(lambda _: Faker().first_name())
    role = "customer"
```---

## 3. 外部服务测试（高）

### HTTP 级模拟（不是函数模拟）

**TypeScript（诺克）：**```typescript
import nock from 'nock';

it('processes payment successfully', async () => {
  nock('https://api.stripe.com')
    .post('/v1/charges')
    .reply(200, { id: 'ch_123', status: 'succeeded', amount: 5000 });

  const result = await paymentService.charge({ amount: 50.00, currency: 'usd' });
  expect(result.status).toBe('succeeded');
});

it('handles payment timeout', async () => {
  nock('https://api.stripe.com').post('/v1/charges').delay(10000).reply(200);
  await expect(paymentService.charge({ amount: 50, currency: 'usd' }))
    .rejects.toThrow('timeout');
});
```**Python（响应）：**```python
import responses

@responses.activate
def test_payment_success():
    responses.post("https://api.stripe.com/v1/charges",
                   json={"id": "ch_123", "status": "succeeded"}, status=200)
    result = payment_service.charge(amount=50.00, currency="usd")
    assert result.status == "succeeded"
```### 测试基础设施容器```typescript
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer } from '@testcontainers/redis';

beforeAll(async () => {
  const pg = await new PostgreSqlContainer('postgres:16').start();
  process.env.DATABASE_URL = pg.getConnectionUri();
  await runMigrations();
}, 60000);
```---

## 4. 合同测试（中-高）

### 消费者驱动的合同（Pact）

**消费者（OrderService调用UserService）：**```typescript
it('can fetch user by ID', async () => {
  await pact.addInteraction()
    .given('user usr_123 exists')
    .uponReceiving('GET /users/usr_123')
    .withRequest('GET', '/api/users/usr_123')
    .willRespondWith(200, (b) => {
      b.jsonBody({ data: { id: MatchersV3.string(), email: MatchersV3.email() } });
    })
    .executeTest(async (mockserver) => {
      const user = await new UserClient(mockserver.url).getUser('usr_123');
      expect(user.id).toBeDefined();
    });
});
```**提供商在 CI 中验证：**```typescript
await new Verifier({
  providerBaseUrl: 'http://localhost:3001',
  pactBrokerUrl: process.env.PACT_BROKER_URL,
  provider: 'UserService',
}).verifyProvider();
```---

## 5. 性能测试（中）

### k6 负载测试```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },    // ramp up
    { duration: '1m',  target: 100 },   // sustain
    { duration: '30s', target: 0 },     // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/api/orders`);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```### 绩效预算

|公制|目标|超过时采取的行动 |
|--------|--------|--------------------|
| p95 响应时间 | < 500 毫秒 |优化查询/缓存 |
| p99 响应时间 | < 1000 毫秒 |检查异常查询 |
|错误率| < 0.1% |调查尖峰 |
|数据库查询时间|每个 < 100 毫秒 |添加索引 |

### 何时运行

|触发|测试类型|
|--------|------------|
|在主要版本发布之前 |满载测试|
|新的数据库查询/索引 |查询基准|
|基础设施变革 |基线比较|
|每周 (CI) |烟负荷测试|

---

## 测试文件组织```
tests/
  unit/                      # Pure logic, mocked dependencies
    order.service.test.ts
  integration/               # API + real DB
    orders.api.test.ts
    auth.api.test.ts
  contracts/                 # Consumer-driven contracts
    user-service.consumer.pact.ts
  performance/               # Load tests
    load-test.js
  fixtures/
    factories/               # Test data factories
      user.factory.ts
    seeds/
      test-data.ts
  helpers/
    setup.ts                 # Global test config
    auth.helper.ts           # Token generation
    db.helper.ts             # DB cleanup
```---

## 反模式

| ＃| ❌不要 | ✅ 改为 |
|---|---------|--------------|
| 1 |仅测试快乐路径 |测试错误、身份验证、验证、边缘情况 |
| 2 |模拟一切（没有真正的数据库）|使用测试容器或测试数据库 |
| 3 |测试取决于执行顺序 |每个测试都会设置/拆除自己的状态|
| 4 |硬编码测试数据|使用工厂（faker + 覆盖）|
| 5 |测试实施细节|测试行为：输入→输出|
| 6 |共享可变状态 |每次测试隔离（事务回滚）|
| 7 |跳过 CI 中的迁移测试 |在 CI 中从头开始运行迁移 |
| 8 |发布前无性能测试|每个主要版本的负载测试 |
| 9 |针对生产数据进行测试 |仅生成测试数据 |
| 10 | 10测试套件 > 10 分钟 |并行化、RAM 磁盘、优化设置 |

---

## 常见问题

### 问题 1：“测试单独通过但一起失败”

**原因：** 测试之间共享数据库状态。缺少清理。

**使固定：**```typescript
beforeEach(async () => { await db.raw('TRUNCATE orders, users CASCADE'); });
// OR use transaction rollback per test
```### 问题 2：“Jest 在测试运行后一秒没有退出”

**原因：** 未关闭的数据库连接或 HTTP 服务器。

**使固定：**```typescript
afterAll(async () => {
  await db.destroy();
  await server.close();
});
```### 问题 3：“超时内未调用异步回调”

**原因：** 缺少 `async/await` 或未处理的承诺。

**使固定：**```typescript
// ❌ Promise not awaited
it('should work', () => { request(app).get('/users'); });

// ✅ Properly awaited
it('should work', async () => { await request(app).get('/users'); });
```### 问题 4：“CI 中的集成测试太慢”

**修复：**
1. 使用 `tmpfs` 作为 PostgreSQL 数据目录（RAM 磁盘）
2. 在`beforeAll`中运行一次迁移，在`beforeEach`中截断
3. 使用 `--maxWorkers` 并行化测试套件
4. 跳过功能分支上的性能测试（仅限主分支）