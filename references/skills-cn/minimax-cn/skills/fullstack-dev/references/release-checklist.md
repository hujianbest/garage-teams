# 发布和验收清单

后端和全栈应用程序的 6 门发布清单。防止“它在我的机器上运行”和“我们忘记检查 X”故障。

**铁律：不通过所有关卡就不能释放。**

---

## 释放门概述```
Feature Complete
    ↓
Gate 1: Functional Acceptance        → Does it do what it should?
    ↓
Gate 2: Non-Functional Acceptance    → Is it fast, reliable, observable?
    ↓
Gate 3: Security Review              → Is it safe?
    ↓
Gate 4: Deployment Readiness         → Can we deploy and rollback safely?
    ↓
Gate 5: Release Execution            → Deploy with canary + monitoring
    ↓
Gate 6: Post-Release Validation      → Did it actually work in production?
```---

## 第一关：功能接受

**问题：它是否符合要求？**

- [ ] Ticket/PRD 的所有验收标准均已通过测试
- [ ] 快乐路径端到端工作
- [ ] 测试边缘情况（空输入、最大长度、Unicode）
- [ ] 测试错误情况（无效输入、未找到、超时）
- [ ] 数据完整性验证（CRUD 循环产生正确的状态）
- [ ] 已确认向后兼容性（现有客户端未损坏）
- [ ] API 合约符合 OpenAPI 规范
- [ ] 幂等性验证（重试不会创建重复项）

### 证据模板

|要求 |测试|状态 |笔记|
|------------|-----|--------|--------|
|用户可以创建订单 | `orders.api.test:创建订单` | ✅ 通过 | |
|空购物车 → 错误 | `orders.api.test:拒绝空` | ✅ 通过 | |
|付款失败处理 | ` payment.test：处理拒绝` | ✅ 通过 | |

---

## Gate 2：非功能性验收

**问题：它是否快速、可靠且可观察？**

### 性能

- [ ] 预算内的响应时间 (p95 < ___ms) — 测量值，未假设
- [ ] 无 N+1 查询（通过查询日志记录检查）
- [ ] 新查询使用索引（`EXPLAIN ANALYZE`）
- [ ] 分页适用于大型数据集
- [ ] 缓存有效（命中率 > 80%）
- [ ] 连接池在负载下健康

### 可靠性

- [ ] 依赖失败时优雅降级（断路器）
- [ ] 重试逻辑适用于暂时性故障
- [ ] 所有外部调用都有超时
- [ ] 速率限制正确返回 429
- [ ] 健康检查端点已验证（`/health`、`/ready`）

### 可观察性

- [ ] 带有请求 ID 的结构化日志记录（不是 `console.log`）
- [ ] 公开的指标（请求计数、延迟、错误率）
- [ ] 配置警报（错误峰值、延迟峰值）
- [ ] 请求跟踪是端到端的
- [ ] 仪表板更新了新功能

### 证据

|公制|目标|实际 |状态 |
|--------|--------|--------|--------|
| p95 回应 | < 500 毫秒 | ___毫秒 | ✅/❌ |
| p99 回应 | < 1000 毫秒 | ___毫秒 | ✅/❌ |
|错误率（负载）| < 0.1% | ___% | ✅/❌ |
|吞吐量| > ___ RPS | ___ RPS | ✅/❌ |

---

## 第三关：安全审查

**问题：这会引入漏洞吗？**

### 输入和输出

- [ ] 所有输入均经过服务器端验证（从不信任客户端）
- [ ] 阻止 SQL 注入（仅限参数化查询）
- [ ] XSS 阻止（输出编码）
- [ ] 文件上传已验证（类型、大小、名称已清理）
- [ ] 敏感端点的速率限制（登录、重置、API）

### 身份验证和数据

- [ ] 受保护的端点需要有效的凭据
- [ ] 用户只能访问自己的资源
- [ ] 管理路由需要管理员角色
- [ ] 令牌过期（短期访问+刷新）
- [ ] 密码经过哈希处理（bcrypt/argon2，而不是 MD5/SHA）
- [ ] 未记录敏感数据（密码、令牌、PII）
- [ ] 环境变量中的秘密（未硬编码）
- [ ] 错误消息不会泄露内部信息

### 依赖关系

- [ ] 没有已知漏洞（`npmaudit`/`pipaudit`/`govulncheck`）
- [ ] 依赖关系固定在锁定文件中
- [ ] 删除未使用的依赖项

---

## Gate 4：部署准备

**问题：我们可以安全部署并在需要时回滚吗？**

### 代码

- [ ] 所有测试都在 CI 中通过（不是“在本地通过”）
- [ ] Linter 干净，构建成功
- [ ] 代码已审核并批准
- [ ] 没有未解决的 TODO/FIXME/HACK

### 数据库

- [ ] 使用类似生产的数据进行迁移测试
- [ ] 向下迁移工作（已测试！）
- [ ] 迁移是非破坏性的（仅添加）
- [ ] 根据生产数据大小估计迁移时间
- [ ] 记录回填计划（如果需要）

### 配置

- [ ] 新环境变量记录在 `.env.example` 中
- [ ] 环境变量在暂存中设置并经过验证
- [ ] 环境变量在生产环境中设置
- [ ] 配置功能标志（如果适用）

### 回滚计划模板```markdown
## Rollback Plan: [Feature]

### When to rollback
- Error rate > 1% sustained 5 minutes
- p99 latency > 3000ms sustained 10 minutes
- Critical business function broken

### Steps
1. Revert deploy: [command]
2. Rollback migration (if applied): [command]
3. Invalidate cache: [command]
4. Notify team: #incidents channel
5. Verify rollback: [verification steps]

### Estimated time: [X minutes]
### Data recovery: [procedure if data was modified]
```---

## Gate 5：释放执行

### 部署顺序```
1. 📢 ANNOUNCE in release channel

2. 🗄️ DATABASE — Apply migration
   - Run migration
   - Verify completion
   - Check data integrity

3. 🚀 DEPLOY — Roll out code
   - Canary first (10% traffic)
   - Monitor 5 minutes
   - If OK → 50% → monitor → 100%
   - If NOT OK → STOP immediately

4. 🔍 SMOKE TEST
   - Health check → 200
   - Login works
   - Core operation works
   - No error spikes

5. ✅ ANNOUNCE "Release complete. Monitoring 30 min."
```### 金丝雀决策表

|公制|基线|金丝雀 好的 |停止|回滚 |
|--------|----------|------------|-----|----------|
|错误率| 0.05% | < 0.1% | 0.5% | > 1% |
| p95 延迟 | 300 毫秒 | < 500 毫秒 | 700 毫秒 | > 1000 毫秒 |

---

## Gate 6：发布后验证

### 立即（0-30 分钟）

- [ ] 所有实例的运行状况检查均呈绿色
- [ ] 错误率在正常范围内
- [ ] 延迟正常（p95、p99）
- [ ] 核心用户旅程手动测试
- [ ] 日志干净 — 没有意外错误
- [ ] 警报静音

### 短期（1-24 小时）

- [ ] 无客户投诉
- [ ] 业务指标稳定（转化、收入、注册）
- [ ] 内存/CPU 稳定（无缓慢使用）
- [ ] 队列积压清除
- [ ] 数据库性能稳定

### 发布后报告模板```markdown
## Release Report: [Feature]
- Deployed: [timestamp] by @[engineer]
- Duration: [minutes]

| Check | Status | Notes |
|-------|--------|-------|
| Health checks | ✅ | All healthy |
| Error rate | ✅ | 0.03% (baseline: 0.05%) |
| p95 latency | ✅ | 310ms (baseline: 300ms) |
| Core flow | ✅ | Order creation verified |

Issues found: None / [details]
Rollback used: No / Yes: [reason]
```---

## 发布准备分数

对每个门进行评分 **0-2**：（0 = 未检查，1 = 部分检查，2 = 有证据充分验证）

|门 |分数 |
|------|--------|
| 1. 功能验收| /2 |
| 2. 非功能性验收 | /2 |
| 3.安全审查| /2 |
| 4.部署准备| /2 |
| 5.发布执行计划| /2 |
| 6. 发布后验证计划 | /2 |
| **总计** | **/12** |

**决定：**
- **12/12** → 发货 ✅
- **10-11** → 发货时记录异常情况 + 指定所有者
- **< 10** → 不要释放。首先修复间隙。

---

## 常见的合理化

| ❌ 对不起 | ✅ 现实 |
|----------|------------|
| “这是一个小小的改变”|每天的小变化都会导致停电 |
| “我们在本地进行了测试” |本地≠生产|
| “如果它坏了我们会修复它” |你将在凌晨 3 点修复它。立即预防。 |
| “最后期限是今天”|损坏的代码比延迟的代码成本更高 |
| “CI 通过”| CI 不会检查所有内容。运行检查表。 |
| “我们随时可以回滚” |仅当您计划并测试回滚时|
| “我们上次做得很好”|幸存者偏差。每次都检查清单。 |