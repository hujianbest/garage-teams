# 系统测试实践备忘（Recipes）

按 ST 测试类别给出的语言/框架实践。根据 `feature-list.json` 中的 `tech_stack` 选用。

## 1. 集成测试模式

### 真实测试 vs 契约测试分类

- **契约测试** — 用 mock/stub（`unittest.mock`、`requests-mock`、`msw`、`gmock`）校验调用签名与数据形态。可验证接口但**不**验证真实数据流。
- **集成测试** — 验证真实组件间实际数据流（真实 DB、HTTP、文件系统）。可发现 mock 掩盖的契约不一致、类型错误与协议缺陷。

**真实集成优先工具：**
- `testcontainers`（Python、Java、JS/TS）— Docker 中的真实 DB/服务
- `sqlite:///:memory:` — 真实 SQL 引擎，内存库（可作 SQL 集成）
- 对运行中服务器使用 `httpx` — 内部 API 优先于 `requests-mock`
- 对运行中 Express/Fastify 使用 `supertest` — 内部 API 优先于 `msw`

**外部第三方服务测试策略（优先级）：**
1. **优先真实测试** — 通过 `AskUserQuestion` 向用户索取测试凭证/沙箱（如 Stripe 测试密钥、GitHub personal token）
2. **用户确认无法提供** — 仅当用户明确确认无法提供凭证时，使用契约测试（mock）
3. **记录决策** — 在 ST 计划分类表中注明：`External (user confirmed no credentials)` 作为 mock 授权依据

**仅允许 mock 的情况：**
- 外部第三方服务（如 Stripe API、GitHub API）**且**用户经 `AskUserQuestion` 确认无法提供测试凭证
- 须在 ST 计划中记录用户确认，作为 mock 授权依据

### Python
```bash
# Directory structure
tests/integration/
  test_feature_a_b_integration.py
  conftest.py  # shared fixtures

# Run with pytest
pytest tests/integration/ -v --tb=short

# With coverage
pytest tests/integration/ --cov=src --cov-report=term-missing
```

**模式：**
- 共享状态用 `pytest` fixture 搭建/ teardown
- 数据库集成用 `sqlite:///:memory:` 或 `testcontainers` [Real]
- 内部 API 集成对运行中服务器用 `httpx` [Real]
- **仅**对外部服务边界使用 `unittest.mock.patch` 或 `requests-mock` [Contract] — 须用户确认无法提供真实凭证

### JavaScript / TypeScript
```bash
# Directory structure
tests/integration/
  featureA-featureB.test.ts
  setup.ts  # shared setup

# Run with vitest
npx vitest run tests/integration/ --reporter=verbose

# Run with jest
npx jest tests/integration/ --verbose
```

**模式：**
- 共享状态用 `beforeAll`/`afterAll`
- 数据库集成用 `testcontainers` [Real]
- 内部 API 对运行中 Express/Fastify 应用用 `supertest` [Real]
- **仅**对外部服务边界用 `msw`（Mock Service Worker）[Contract] — 须用户确认无法提供真实凭证

### Java
```bash
# Directory structure
src/test/java/integration/
  FeatureABIntegrationTest.java

# Run with Maven
mvn test -Dtest="integration.*" -pl module-name

# Run with Gradle
./gradlew test --tests "integration.*"
```

**模式：**
- Spring 集成用 `@SpringBootTest` [Real]
- DB/服务集成用 `Testcontainers` [Real]
- 内部 API 对运行中服务器用 `RestAssured` [Real]；对外部边界对 mock 服务器 [Contract]
- 测试间状态隔离可用 `@DirtiesContext`

### C / C++
```bash
# Integration tests in separate directory
tests/integration/
  test_module_integration.cpp

# Build and run with CMake + CTest
cmake --build build --target integration_tests
ctest --test-dir build -R integration -V
```

**模式：**
- 共享状态用 `gtest` fixture
- 模块间 IPC、共享内存、文件 I/O [Real]
- **仅**对外部边界用 mock 库（`gmock`、`fff`）[Contract] — 须用户确认无法提供真实凭证

---

## 2. E2E 测试工具

### 基于 API 的 E2E

| 语言 | 工具 | 安装方式 |
|----------|------|---------|
| Python | `httpx` + `pytest` | `pip install httpx` |
| Python | `requests` + `pytest` | `pip install requests` |
| JS/TS | `supertest` | `npm install supertest` |
| JS/TS | `axios` + `vitest` | `npm install axios` |
| Java | `RestAssured` | Maven: `io.rest-assured:rest-assured` |

### UI E2E（Chrome DevTools MCP）

对 `"ui": true` 的特性，直接使用 Chrome DevTools MCP 工具：

```
1. navigate_page → url: <ui_entry from feature>
2. take_snapshot → capture initial state
3. click/fill/press_key → simulate user interaction
4. take_snapshot → verify state change
5. list_console_messages → check for errors
6. list_network_requests → verify API calls
7. take_screenshot → visual evidence
```

**多步工作流模式：**
```
场景：用户完成结账流程
  navigate_page → /products
  click → "Add to Cart" button
  navigate_page → /cart
  take_snapshot → verify cart has item
  click → "Checkout" button
  fill_form → payment details
  click → "Pay" button
  wait_for → "Order confirmed"
  take_snapshot → verify confirmation page
  list_console_messages → zero errors
```

### CLI E2E

| 语言 | 方式 |
|----------|----------|
| Python | `subprocess.run()` in pytest |
| Node.js | `execa` or `child_process` in vitest |
| Java | `ProcessBuilder` in JUnit |
| C/C++ | `system()` or `popen()` in gtest |

---

## 3. 性能基准

### Python
```bash
# pytest-benchmark (micro-benchmarks)
pip install pytest-benchmark
pytest tests/perf/ --benchmark-only --benchmark-json=benchmark.json

# locust (load testing)
pip install locust
locust -f tests/perf/locustfile.py --headless -u 100 -r 10 --run-time 60s --csv=perf_results

# time module (simple timing)
import time
start = time.perf_counter()
# ... operation ...
elapsed = time.perf_counter() - start
assert elapsed < 0.2, f"Response time {elapsed:.3f}s exceeds 200ms threshold"
```

### JavaScript / TypeScript
```bash
# Vitest bench
npx vitest bench

# k6 (load testing)
k6 run tests/perf/load-test.js --out csv=perf_results.csv

# autocannon (HTTP benchmarking)
npx autocannon -c 100 -d 30 http://localhost:3000/api/endpoint
```

### Java
```bash
# JMH (micro-benchmarks)
mvn exec:exec -Pbenchmark

# Gatling (load testing)
mvn gatling:test
```

### C / C++
```bash
# Google Benchmark
cmake --build build --target benchmarks
./build/benchmarks --benchmark_format=json --benchmark_out=benchmark.json

# Custom timing
#include <chrono>
auto start = std::chrono::high_resolution_clock::now();
// ... operation ...
auto elapsed = std::chrono::duration<double>(std::chrono::high_resolution_clock::now() - start).count();
```

---

## 4. 安全扫描

### 依赖漏洞扫描器

| 语言 | 工具 | 命令 |
|----------|------|---------|
| Python | `pip-audit` | `pip-audit --strict` |
| Python | `safety` | `safety check` |
| JS/TS | `npm audit` | `npm audit --audit-level=high` |
| JS/TS | `snyk` | `npx snyk test` |
| Java | `OWASP Dependency-Check` | `mvn org.owasp:dependency-check-maven:check` |
| C/C++ | `cve-bin-tool` | `cve-bin-tool ./build/` |
| General | `trivy` | `trivy fs --severity HIGH,CRITICAL .` |

### 静态分析（安全向）

| Language | Tool | Command |
|----------|------|---------|
| Python | `bandit` | `bandit -r src/ -f json -o bandit-report.json` |
| JS/TS | `eslint-plugin-security` | `npx eslint --rule 'security/*' src/` |
| Java | `SpotBugs + FindSecBugs` | `mvn spotbugs:check` |
| C/C++ | `cppcheck` | `cppcheck --enable=all --force src/` |

### OWASP Top 10 检查清单（人工评审）

| # | 类别 | 检查点 |
|---|----------|---------------|
| A01 | Broken Access Control | 认证绕过、权限提升、IDOR |
| A02 | Cryptographic Failures | 硬编码密钥、弱算法、明文敏感数据 |
| A03 | Injection | SQL、XSS、命令、LDAP、模板注入 |
| A04 | Insecure Design | 缺少限流、缺少输入校验 |
| A05 | Security Misconfiguration | 调试模式、默认凭证、过度详细错误 |
| A06 | Vulnerable Components | 过期依赖（运行上方扫描器） |
| A07 | Authentication Failures | 弱密码、缺失 MFA、会话固定 |
| A08 | Data Integrity Failures | 未签名更新、不可信反序列化 |
| A09 | Logging Failures | 缺少审计日志、日志含敏感数据 |
| A10 | SSRF | 未校验 URL、可访问内网 |

---

## 5. 兼容性测试

### 跨浏览器（UI 项目）

使用 Chrome DevTools MCP 配合不同 User-Agent：

```
# Emulate different browsers
emulate → userAgent: "Mozilla/5.0 ... Firefox/120.0"
emulate → viewport: { width: 1920, height: 1080 }
navigate_page → target URL
take_screenshot → evidence

# Mobile emulation
emulate → viewport: { width: 375, height: 812, isMobile: true, hasTouch: true }
```

### 跨平台（CLI/库）

在可用环境中于目标平台验证：
```bash
# Check platform-specific behavior
python -c "import platform; print(platform.system())"

# Verify file path handling
# Verify line ending handling
# Verify permission handling
```

---

## 6. 测试报告指标收集

### 覆盖率指标

| 语言 | 获取汇总的命令 |
|----------|----------------------|
| Python | `pytest --cov=src --cov-report=term-missing` |
| JS/TS | `npx vitest run --coverage` |
| Java | `mvn jacoco:report` (then read `target/site/jacoco/index.html`) |
| C/C++ | `gcovr --print-summary` |

### 测试数量

| 语言 | 命令 |
|----------|---------|
| Python | `pytest --tb=no -q` (last line shows counts) |
| JS/TS | `npx vitest run --reporter=verbose` |
| Java | `mvn test` (Surefire report) |
| C/C++ | `ctest --test-dir build -V` |

---

## 7. 全量变异回归（Full Mutation Regression）

ST 阶段对**全代码库**做变异测试。与 Worker 周期中的按特性变异互补 — 用**完整**测试套件验证变异分在全项目范围仍达标。

### 各工具命令

| 工具 | 全量变异命令 | 结果查看命令 | 分数提取方式 |
|------|----------------------|-----------------|------------------|
| mutmut | `mutmut run` | `mutmut results` | "Killed N out of M mutants" line |
| pitest | `mvn pitest:mutationCoverage` | `cat target/pit-reports/*/mutations.xml` | `mutationScore` attribute in XML |
| stryker | `npx stryker run` | `cat reports/mutation/mutation.json` | `.thresholds.high` in JSON |
| mull | `mull-runner ./test-binary` | `cat mull-report.json` | killed/survived counts in JSON |

### 结果解读

- **分数 >= 阈值** → PASS
- **分数 < 阈值** 且已文档化等价变异体 → 若剔除等价后调整分 >= 阈值，可判 PASS
- **分数 < 阈值** 且为真实缺口 → FAIL（Major 级缺陷 — 补测试杀死幸存变异体后重跑）

### 与按特性变异的关系

- Worker 周期中，活跃特性数 ≤ `mutation_full_threshold` 时已按特性跑全量变异 — 本步在全项目范围再次确认
- 活跃特性数 > `mutation_full_threshold` 时 Worker 仅跑**特性范围**变异 — 本步是首次全套件变异，可能暴露跨特性变异缺口
