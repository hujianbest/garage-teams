---
名称：fullstack-dev-db-schema
描述：“数据库架构设计和迁移。在创建表、定义 ORM 模型、添加索引或设计关系时使用。涵盖零停机迁移和多租户。”
许可证：麻省理工学院
元数据：
  版本：“1.0.0”
  来源：
    - PostgreSQL 官方文档
    - 使用索引，卢克 (use-the-index-luke.com)
    - 设计数据密集型应用程序（Martin Kleppmann）
    - 数据库可靠性工程（莱恩坎贝尔和慈善专业）
---

# 数据库架构设计

与 ORM 无关的关系数据库模式设计指南。涵盖数据建模、规范化、索引、迁移、多租户和常见应用程序模式。主要关注 PostgreSQL，但原则适用于 MySQL/MariaDB。

## 范围

**在以下情况下使用此技能：**
- 为新项目或功能设计架构
- 在规范化和非规范化之间做出决定
- 选择要创建的索引
- 规划实时数据库的零停机迁移
- 实现多租户数据隔离
- 添加审计跟踪、软删除或版本控制
- 诊断由模式问题引起的慢查询

**不适合：**
- 选择要使用的数据库技术（→“技术选择”）
- PostgreSQL 特定的查询调优（使用 PostgreSQL 性能文档）
- ORM 特定的配置（→ `django-best-practices` 或您的 ORM 文档）
- 应用层缓存（→ `fullstack-dev-practices`）

## 需要上下文

|必填 |可选|
|----------|----------|
|数据库引擎（PostgreSQL/MySQL）|预期数据量（行数、增长率）|
|领域实体和关系 |读/写比率 |
|关键访问模式（查询）|多租户需求 |

---

## 快速入门清单

设计一个新的模式：

- [ ] **已识别的域实体** — 映射 1 个实体 = 1 个表（不是 1 个类 = 1 个表）
- [ ] **主键**：UUID 用于公共 ID，serial/bigserial 用于内部专用
- [ ] **外键**具有明确的“ON DELETE”行为
- [ ] **NOT NULL** 默认情况下 — 仅当业务逻辑需要时可为空
- [ ] **时间戳**：每个表上的 `created_at` + `updated_at`
- [ ] **为每个 WHERE、JOIN、ORDER BY 列创建索引**
- [ ] **无过早反规范化** — 开始规范化，测量时反规范化
- [ ] **命名约定**一致：`snake_case`，复数表名

---

## 快速导航

|需要…… |跳转至 |
|----------|---------|
|模型实体和关系| [1.数据建模](#1-数据建模-关键) |
|决定标准化与非标准化 | [2.标准化](#2-标准化与非标准化-关键) |
|选择正确的索引 | [3.索引](#3-索引策略-关键) |
|在实时数据库上安全地运行迁移 | [4.迁移](#4-零停机-迁移-高) |
|设计多租户架构 | [5.多租户](#5-多租户设计-高) |
|添加软删除/审计跟踪 | [6.常见模式](#6-common-schema-patterns-medium) |
|大表分区| [7.分区](#7-表分区-中) |
|查看反模式 | [反模式](#反模式) |

---

## 核心原则（7 条规则）```
1. ✅ Start normalized (3NF) — denormalize only when you have measured evidence
2. ✅ Every table has a primary key, created_at, updated_at
3. ✅ UUID for public-facing IDs, serial for internal join keys
4. ✅ NOT NULL by default — null is a business decision, not a lazy default
5. ✅ Index every column used in WHERE, JOIN, ORDER BY
6. ✅ Foreign keys enforced in database (not just application code)
7. ✅ Migrations are additive — never drop/rename in production without a multi-step plan
```---

## 1. 数据建模（关键）

### 表命名```sql
-- ✅ Plural, snake_case
CREATE TABLE orders (...);
CREATE TABLE order_items (...);
CREATE TABLE user_profiles (...);

-- ❌ Singular, mixed case
CREATE TABLE Order (...);
CREATE TABLE OrderItem (...);
CREATE TABLE tbl_usr_prof (...);    -- cryptic abbreviation
```### 主键

|战略|当 |优点 |缺点 |
|----------|------|------|------|
| `bigserial`（自动增量）|内表、FK 连接 |紧凑、快速连接 |可枚举，对于公共 ID 来说不安全 |
| `uuid`（v4 随机）|面向公众的资源 |不可猜测，全球独一无二 | B 树上的更大（16 字节）随机 I/O |
| `uuid` v7（按时间排序）|公众号+需求订购|不可猜测+插入友好|较新、较少的生态系统支持 |
| `文本` slug | URL 友好的资源 |人类可读 |必须强制唯一性，更新成本昂贵 |

**推荐默认值：**```sql
CREATE TABLE orders (
    id          bigserial PRIMARY KEY,             -- internal FK target
    public_id   uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,  -- API-facing
    -- ...
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
```### 关系```sql
-- One-to-Many: user → orders
CREATE TABLE orders (
    id         bigserial PRIMARY KEY,
    user_id    bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- ...
);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Many-to-Many: orders ↔ products (via junction table)
CREATE TABLE order_items (
    id         bigserial PRIMARY KEY,
    order_id   bigint NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id bigint NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity   int NOT NULL CHECK (quantity > 0),
    unit_price numeric(10,2) NOT NULL,
    UNIQUE (order_id, product_id)  -- prevent duplicate line items
);

-- One-to-One: user → profile
CREATE TABLE user_profiles (
    user_id    bigint PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio        text,
    avatar_url text,
    -- ...
);
```### 删除行为

|行为 |当 |示例|
|----------|------|---------|
| `级联` |没有父母的孩子毫无意义|订单删除时的 order_items |
| `限制` |防止意外删除 | order_items | 引用的产品
| `设置为空` |保护孩子，明确参考|员工离职时的orders.assigned_to |
| `设置默认值` |回退到默认值 |罕见，用于状态栏 |

---

## 2. 规范化与非规范化（关键）

### 开始标准化 (3NF)

**实践中的范式：**

|表格 |规则|违规示例 |
|------|------|--------------------|
| 1NF |无重复组、原子值 |一列中的 `tags = "go,python,rust"` |
| 2NF |没有部分依赖关系（复合键）| `order_items.product_name` 仅取决于 `product_id` |
| 3NF |没有传递依赖 | `orders.customer_city` 取决于 `customer_id`，而不是 `order_id` |

**1NF 违规修复：**```sql
-- ❌ Tags as comma-separated string
CREATE TABLE posts (id serial, tags text);  -- tags = "go,python"

-- ✅ Separate table (or array/JSONB if simple)
CREATE TABLE post_tags (
    post_id bigint REFERENCES posts(id) ON DELETE CASCADE,
    tag_id  bigint REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- ✅ Alternative: PostgreSQL array (if tags are just strings, no metadata)
CREATE TABLE posts (id serial, tags text[] NOT NULL DEFAULT '{}');
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);
```### 何时非规范化

**仅在以下情况下才进行反规范化：**
1.您**测量**性能问题（解释分析，而不是“我认为它很慢”）
2.非规范化数据**读重**（读：写比> 100：1）
3. 您接受**一致性维护成本**（触发器、应用程序逻辑或物化视图）

**安全的反规范化模式：**```sql
-- Pattern 1: Materialized view (computed, refreshable)
CREATE MATERIALIZED VIEW order_summary AS
SELECT o.id, o.user_id, o.total,
       COUNT(oi.id) AS item_count,
       u.email AS user_email
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN users u ON u.id = o.user_id
GROUP BY o.id, u.email;

REFRESH MATERIALIZED VIEW CONCURRENTLY order_summary;  -- non-blocking

-- Pattern 2: Cached aggregate column (application-maintained)
ALTER TABLE orders ADD COLUMN item_count int NOT NULL DEFAULT 0;
-- Update via trigger or application code on order_item insert/delete

-- Pattern 3: JSONB snapshot (freeze-at-write-time)
-- Store a copy of the product details at the time of purchase
CREATE TABLE order_items (
    id          bigserial PRIMARY KEY,
    order_id    bigint NOT NULL REFERENCES orders(id),
    product_id  bigint REFERENCES products(id),
    quantity    int NOT NULL,
    unit_price  numeric(10,2) NOT NULL,      -- frozen price
    product_snapshot jsonb NOT NULL           -- frozen name, description, image
);
```---

## 3. 索引策略（关键）

### 索引类型 (PostgreSQL)

|类型 |当 |示例|
|------|------|---------|
| **B 树**（默认）|平等、范围、ORDER BY | `WHERE status = 'active'`, `WHERE created_at > '2025-01-01'` |
| **哈希** |仅相等（很少见，B 树通常更好）| `WHERE id = 123`（大型表，Postgres 10+）|
| **杜松子酒** |数组、JSONB、全文搜索 | `WHERE 标签 @> '{go}'`, `WHERE data->>'key' = 'val'` |
| **吉斯特** |几何、范围、最近邻| PostGIS、tsrange、ltree |
| **布林** |非常大的桌子，自然排序|按时间戳排序的时间序列数据 |

### 指数决策规则```
Rule 1: Index every column in WHERE clauses
Rule 2: Index every column used in JOIN ON conditions
Rule 3: Index every column in ORDER BY (if queried with LIMIT)
Rule 4: Composite index for multi-column WHERE (leftmost prefix rule)
Rule 5: Partial index when filtering a subset (e.g., only active records)
Rule 6: Covering index (INCLUDE) to avoid table lookup
Rule 7: DON'T index low-cardinality columns alone (e.g., boolean)
```### 综合索引：列顺序很重要```sql
-- Query: WHERE user_id = ? AND status = ? ORDER BY created_at DESC
-- ✅ Optimal: matches query pattern left-to-right
CREATE INDEX idx_orders_user_status_created
ON orders(user_id, status, created_at DESC);

-- ❌ Wrong order: can't use for this query efficiently
CREATE INDEX idx_orders_created_user_status
ON orders(created_at DESC, user_id, status);
```**最左前缀规则：** `(A, B, C)` 上的索引支持对 `(A)`、`(A, B)`、`(A, B, C)` 的查询，但不支持对 `(B)`、`(C)` 或 `(B, C)` 的查询。

### 部分索引（仅索引重要的内容）```sql
-- Only 5% of orders are 'pending', but queried frequently
CREATE INDEX idx_orders_pending
ON orders(created_at DESC)
WHERE status = 'pending';

-- Only active users matter for login
CREATE INDEX idx_users_active_email
ON users(email)
WHERE is_active = true;
```### 覆盖索引（避免查表）```sql
-- Query only needs id and status, no need to read the table row
CREATE INDEX idx_orders_user_covering
ON orders(user_id) INCLUDE (status, total);

-- Now this query is index-only:
SELECT status, total FROM orders WHERE user_id = 123;
```### 何时不建立索引```
❌ Columns rarely used in WHERE/JOIN/ORDER BY
❌ Tables with < 1,000 rows (sequential scan is faster)
❌ Columns with very low cardinality alone (e.g., boolean is_active)
❌ Write-heavy tables where index maintenance cost > read benefit
❌ Duplicate indexes (check pg_stat_user_indexes for unused indexes)
```---

## 4. 零停机迁移（高）

### 黄金法则```
NEVER make destructive changes in one step.
Always: ADD → MIGRATE DATA → REMOVE OLD (in separate deploys).
```### 安全迁移模式

**重命名列（3 次部署）：**```
Deploy 1: Add new column
  ALTER TABLE users ADD COLUMN full_name text;
  UPDATE users SET full_name = name;           -- backfill
  -- App writes to BOTH name and full_name

Deploy 2: Switch reads to new column
  -- App reads from full_name, still writes to both

Deploy 3: Drop old column
  ALTER TABLE users DROP COLUMN name;
  -- App only uses full_name
```**添加 NOT NULL 列（2 次部署）：**```sql
-- Deploy 1: Add nullable column, backfill
ALTER TABLE orders ADD COLUMN currency text;              -- nullable first
UPDATE orders SET currency = 'USD' WHERE currency IS NULL; -- backfill

-- Deploy 2: Add constraint (after all rows backfilled)
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;
ALTER TABLE orders ALTER COLUMN currency SET DEFAULT 'USD';
```**添加不加锁的索引：**```sql
-- ✅ CONCURRENTLY: no table lock, can run on live DB
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);

-- ❌ Without CONCURRENTLY: locks table for writes during build
CREATE INDEX idx_orders_status ON orders(status);
```### 迁移安全检查表```
✅ Migration runs in < 30 seconds on production data size
✅ No exclusive table locks (use CONCURRENTLY for indexes)
✅ Rollback plan documented and tested
✅ Backfill runs in batches (not one giant UPDATE)
✅ New column added as nullable first, constraint added later
✅ Old column kept until all code references removed

❌ Never rename/drop columns in one deploy
❌ Never ALTER TYPE on large tables without testing timing
❌ Never run data backfill in a transaction (OOM on large tables)
```### 批量回填模板```sql
-- Backfill in batches of 10,000 (avoids long-running transactions)
DO $$
DECLARE
  batch_size int := 10000;
  affected int;
BEGIN
  LOOP
    UPDATE orders
    SET currency = 'USD'
    WHERE id IN (
      SELECT id FROM orders WHERE currency IS NULL LIMIT batch_size
    );
    GET DIAGNOSTICS affected = ROW_COUNT;
    RAISE NOTICE 'Updated % rows', affected;
    EXIT WHEN affected = 0;
    PERFORM pg_sleep(0.1);  -- brief pause to reduce load
  END LOOP;
END $$;
```---

## 5. 多租户设计（高）

### 三种方法

|方法|隔离|复杂性 |当 |
|----------|------------|------------|-----|
| **行级**（共享表+`tenant_id`）|低|低| SaaS MVP，< 1,000 名租户 |
| **每个租户架构** |中等|中等|行业受监管，规模适中|
| **每个租户数据库** |高|高|企业，严格数据隔离 |

### 行级租赁（最常见）```sql
-- Every table has tenant_id
CREATE TABLE orders (
    id         bigserial PRIMARY KEY,
    tenant_id  bigint NOT NULL REFERENCES tenants(id),
    user_id    bigint NOT NULL REFERENCES users(id),
    total      numeric(10,2) NOT NULL,
    -- ...
);

-- Composite index: tenant first (most queries filter by tenant)
CREATE INDEX idx_orders_tenant_user ON orders(tenant_id, user_id);
CREATE INDEX idx_orders_tenant_status ON orders(tenant_id, status);

-- Row-Level Security (PostgreSQL)
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::bigint);
```**应用程序级执行：**```typescript
// Middleware: set tenant context on every request
app.use((req, res, next) => {
  const tenantId = req.headers['x-tenant-id'];
  if (!tenantId) return res.status(400).json({ error: 'Missing tenant' });
  req.tenantId = tenantId;
  next();
});

// Repository: ALWAYS filter by tenant
async findOrders(tenantId: string, userId: string) {
  return db.order.findMany({
    where: { tenantId, userId },  // ← tenant_id in EVERY query
  });
}
```### 规则```
✅ tenant_id in EVERY table that holds tenant data
✅ tenant_id as FIRST column in every composite index
✅ Application middleware enforces tenant context
✅ Use RLS (PostgreSQL) as defense-in-depth, not sole protection
✅ Test with 2+ tenants to verify isolation

❌ Never allow cross-tenant queries in application code
❌ Never skip tenant_id in WHERE clauses (even in admin tools)
```---

## 6. 常见架构模式（中）

### 软删除```sql
ALTER TABLE orders ADD COLUMN deleted_at timestamptz;

-- All queries filter deleted records
CREATE VIEW active_orders AS
SELECT * FROM orders WHERE deleted_at IS NULL;

-- Partial index: only index non-deleted rows
CREATE INDEX idx_orders_active_status
ON orders(status, created_at DESC)
WHERE deleted_at IS NULL;
```**ORM 集成：**```typescript
// Prisma middleware: auto-filter soft-deleted records
prisma.$use(async (params, next) => {
  if (params.action === 'findMany' || params.action === 'findFirst') {
    params.args.where = { ...params.args.where, deletedAt: null };
  }
  return next(params);
});
```### 审计追踪```sql
-- Option A: Audit columns on every table
ALTER TABLE orders ADD COLUMN created_by bigint REFERENCES users(id);
ALTER TABLE orders ADD COLUMN updated_by bigint REFERENCES users(id);

-- Option B: Separate audit log table (more detail)
CREATE TABLE audit_log (
    id          bigserial PRIMARY KEY,
    table_name  text NOT NULL,
    record_id   bigint NOT NULL,
    action      text NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data    jsonb,
    new_data    jsonb,
    changed_by  bigint REFERENCES users(id),
    changed_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at DESC);
```### 枚举列```sql
-- Option A: PostgreSQL enum type (strict, but ALTER TYPE is painful)
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');
ALTER TABLE orders ADD COLUMN status order_status NOT NULL DEFAULT 'pending';

-- Option B: Text + CHECK constraint (easier to migrate)
ALTER TABLE orders ADD COLUMN status text NOT NULL DEFAULT 'pending'
  CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled'));

-- Option C: Lookup table (most flexible, best for UI-driven lists)
CREATE TABLE order_statuses (
    id    serial PRIMARY KEY,
    name  text UNIQUE NOT NULL,
    label text NOT NULL      -- display name
);
```**建议：** 对于大多数情况，选项 B（文本 + 检查）。如果状态由非开发人员管理，则选项 C。

### 多态关联```sql
-- ❌ Anti-pattern: polymorphic FK (no referential integrity)
CREATE TABLE comments (
    id             bigserial PRIMARY KEY,
    commentable_type text,    -- 'Post' or 'Photo'
    commentable_id   bigint,  -- no FK constraint possible!
    body           text
);

-- ✅ Pattern A: Separate FK columns (nullable)
CREATE TABLE comments (
    id       bigserial PRIMARY KEY,
    post_id  bigint REFERENCES posts(id) ON DELETE CASCADE,
    photo_id bigint REFERENCES photos(id) ON DELETE CASCADE,
    body     text NOT NULL,
    CHECK (
      (post_id IS NOT NULL AND photo_id IS NULL) OR
      (post_id IS NULL AND photo_id IS NOT NULL)
    )
);

-- ✅ Pattern B: Separate tables (cleanest, best for different schemas)
CREATE TABLE post_comments (..., post_id bigint REFERENCES posts(id));
CREATE TABLE photo_comments (..., photo_id bigint REFERENCES photos(id));
```### JSONB 列（半结构化数据）```sql
-- Good uses: metadata, settings, flexible attributes
CREATE TABLE products (
    id         bigserial PRIMARY KEY,
    name       text NOT NULL,
    price      numeric(10,2) NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'  -- color, size, weight...
);

-- Index for JSONB queries
CREATE INDEX idx_products_attrs ON products USING GIN(attributes);

-- Query
SELECT * FROM products WHERE attributes->>'color' = 'red';
SELECT * FROM products WHERE attributes @> '{"size": "XL"}';
```

```
✅ Use JSONB for truly flexible/optional data (metadata, settings, preferences)
✅ Index JSONB columns with GIN when queried

❌ Never use JSONB for data that should be columns (email, status, price)
❌ Never use JSONB to avoid schema design (it's not MongoDB-in-Postgres)
```---

## 7. 表分区（中）

### 何时分区```
✅ Table > 100M rows AND growing
✅ Most queries filter on the partition key (date range, tenant)
✅ Old data can be dropped/archived by partition (efficient DELETE)

❌ Table < 10M rows (overhead not worth it)
❌ Queries don't filter on partition key (scans all partitions)
```### 范围分区（时间序列）```sql
CREATE TABLE events (
    id         bigserial,
    tenant_id  bigint NOT NULL,
    event_type text NOT NULL,
    payload    jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE events_2025_01 PARTITION OF events
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE events_2025_02 PARTITION OF events
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Automate partition creation with pg_partman or cron
```### 列表分区（多租户）```sql
CREATE TABLE orders (
    id        bigserial,
    tenant_id bigint NOT NULL,
    total     numeric(10,2)
) PARTITION BY LIST (tenant_id);

CREATE TABLE orders_tenant_1 PARTITION OF orders FOR VALUES IN (1);
CREATE TABLE orders_tenant_2 PARTITION OF orders FOR VALUES IN (2);
```---

## 反模式

| ＃| ❌不要 | ✅ 改为 |
|---|---------|--------------|
| 1 |过早的反规范化 |启动 3NF，测量时反规范化 |
| 2 |自动递增ID作为公共API标识符| UUID 为公共，序列号为内部 |
| 3 |无外键约束| FK 在数据库中强制执行，始终 |
| 4 |默认为空 |默认为 NOT NULL，需要时可为空 |
| 5 | FK 列上没有索引 |索引每个 FK 列 |
| 6 |单步破坏性迁移 |在单独的部署中添加→迁移→删除|
| 7 |不带“CONCURRENTLY”的“CREATE INDEX” |实时餐桌上始终“同时” |
| 8 |多态 FK (`commentable_type + commentable_id`) |单独的 FK 列或单独的表 |
| 9 | JSONB 适用于一切 | JSONB 仅用于灵活数据，列用于结构化 |
| 10 | 10没有 `created_at` / `updated_at` |每个表上的时间戳对 |
| 11 | 11一列中的逗号分隔值 |单独的表或 PostgreSQL 数组 |
| 12 | 12没有长度验证的`text` CHECK 约束或应用程序验证 |

---

## 常见问题

### 问题 1：“查询很慢，但我已经有索引了”

**症状：** `EXPLAIN ANALYZE` 显示顺序扫描，尽管存在索引。

**原因：**
1. **错误的索引列顺序** — 复合索引 `(A, B)` 不会帮助 `WHERE B = ?`
2. **低选择性** — 布尔列上的索引（50% 的行匹配），规划器更喜欢 seq 扫描
3. **过时的统计信息** — 运行 `ANALYZE table_name;`
4. **类型不匹配** — 将 `varchar` 列与 `integer` 参数进行比较 → 不使用索引

**修复：** 检查“EXPLAIN (ANALYZE, BUFFERS)”，验证索引与查询模式匹配，运行“ANALYZE”。

### 问题 2：“迁移将表锁定几分钟”

**症状：** `ALTER TABLE` 在执行期间阻止所有写入。

**原因：** 添加 NOT NULL 约束、更改列类型或在没有“CONCURRENTLY”的情况下创建索引。

**使固定：**```sql
-- Add index without lock
CREATE INDEX CONCURRENTLY idx_name ON table(col);

-- Add NOT NULL constraint without lock (Postgres 12+)
ALTER TABLE t ADD CONSTRAINT t_col_nn CHECK (col IS NOT NULL) NOT VALID;
ALTER TABLE t VALIDATE CONSTRAINT t_col_nn;  -- non-blocking validation
```### 问题 3：“多少个索引太多？”

**经验法则：**
- 读取量大的表（报告、产品目录）：5-10个索引即可
- 写入量大的表（事件、日志）：最多 2-3 个索引
- 使用“pg_stat_user_indexes”进行监控 — 使用“idx_scan = 0”删除索引```sql
-- Find unused indexes
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelname NOT LIKE '%pkey%'
ORDER BY pg_relation_size(indexrelid) DESC;
```
