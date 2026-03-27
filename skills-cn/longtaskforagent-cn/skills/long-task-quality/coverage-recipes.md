# 覆盖率与变异测试工具配置食谱

多语言覆盖率与变异测试工具的配置说明。为新项目配置工具时阅读本文。

## 多语言工具矩阵

| 语言 | 覆盖率工具 | 分支覆盖支持 | 变异测试工具 | 增量支持 |
|----------|--------------|----------------|---------------|---------------------|
| Python | pytest-cov (coverage.py) | 支持 | mutmut | 支持（`--paths-to-mutate`） |
| Java | JaCoCo | 支持 | PIT (pitest) | 支持（`-DtargetClasses`） |
| JavaScript | c8 / nyc (Istanbul) | 支持 | Stryker | 支持（`--mutate` glob） |
| TypeScript | c8 / nyc (Istanbul) | 支持 | Stryker | 支持（`--mutate` glob） |
| C | gcov + lcov | 支持（`--branch-probabilities`） | Mull | 部分支持（按文件过滤） |
| C++ | gcov + lcov / llvm-cov | 支持 | Mull | 部分支持（按文件过滤） |

---

## Python

**覆盖率** —— pytest-cov（封装 coverage.py）：

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-branch --cov-report=term-missing --cov-fail-under=90"

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
fail_under = 90
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```

**变异测试** —— mutmut：

```toml
# pyproject.toml (or setup.cfg)
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=short"
```

**命令**：
```bash
# Coverage
pytest --cov=src --cov-branch --cov-report=term-missing

# Mutation (incremental — changed files only)
mutmut run --paths-to-mutate=src/changed_module.py

# Mutation (full)
mutmut run

# View surviving mutants
mutmut results
mutmut show <mutant-id>
```

---

## Java

**覆盖率** —— JaCoCo：

Maven (`pom.xml`):
```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.12</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals><goal>report</goal></goals>
        </execution>
        <execution>
            <id>check</id>
            <phase>verify</phase>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.90</minimum>
                            </limit>
                            <limit>
                                <counter>BRANCH</counter>
                                <value>COVEREDRATIO</value>
                                <minimum>0.80</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

Gradle (`build.gradle`):
```groovy
plugins {
    id 'jacoco'
}

jacocoTestReport {
    reports {
        xml.required = true
        html.required = true
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit { counter = 'LINE';   value = 'COVEREDRATIO'; minimum = 0.90 }
            limit { counter = 'BRANCH'; value = 'COVEREDRATIO'; minimum = 0.80 }
        }
    }
}

test.finalizedBy jacocoTestReport
check.dependsOn jacocoTestCoverageVerification
```

**变异测试** —— PIT（pitest）：

Maven:
```xml
<plugin>
    <groupId>org.pitest</groupId>
    <artifactId>pitest-maven</artifactId>
    <version>1.17.1</version>
    <configuration>
        <targetClasses><param>com.example.*</param></targetClasses>
        <targetTests><param>com.example.*Test</param></targetTests>
        <mutationThreshold>80</mutationThreshold>
        <outputFormats>
            <outputFormat>HTML</outputFormat>
            <outputFormat>XML</outputFormat>
        </outputFormats>
    </configuration>
</plugin>
```

Gradle:
```groovy
plugins {
    id 'info.solidsoft.pitest' version '1.15.0'
}

pitest {
    targetClasses = ['com.example.*']
    targetTests = ['com.example.*Test']
    mutationThreshold = 80
    outputFormats = ['HTML', 'XML']
    timestampedReports = false
}
```

**命令**：
```bash
# Coverage
mvn test jacoco:report
# or
gradle test jacocoTestReport

# Mutation (incremental — specific classes)
mvn pitest:mutationCoverage -DtargetClasses=com.example.ChangedClass
# or
gradle pitest -PtargetClasses=com.example.ChangedClass

# Mutation (full)
mvn pitest:mutationCoverage
```

---

## JavaScript

**覆盖率** —— c8（原生 V8 覆盖率，推荐）或 nyc（Istanbul）：

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:cov": "c8 --branches 80 --lines 90 --reporter=text npx jest",
    "test:cov:nyc": "nyc --branches 80 --lines 90 --reporter=text npx jest"
  }
}
```

```json
// jest.config.json (if using Jest built-in coverage instead of c8)
{
  "collectCoverage": true,
  "coverageDirectory": "coverage",
  "coverageReporters": ["text", "html", "lcov"],
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "lines": 90,
      "functions": 80,
      "statements": 90
    }
  },
  "collectCoverageFrom": ["src/**/*.js", "!src/**/*.test.js"]
}
```

**变异测试** —— Stryker：

```json
// stryker.conf.json
{
  "$schema": "https://raw.githubusercontent.com/stryker-mutator/stryker/master/packages/core/schema/stryker-core.schema.json",
  "mutate": ["src/**/*.js", "!src/**/*.test.js", "!src/**/*.spec.js"],
  "testRunner": "jest",
  "reporters": ["clear-text", "html"],
  "thresholds": {
    "high": 90,
    "low": 80,
    "break": 80
  },
  "coverageAnalysis": "perTest"
}
```

**命令**：
```bash
# Coverage (c8)
npx c8 --branches 80 --lines 90 --reporter=text npx jest

# Coverage (Jest built-in)
npx jest --coverage

# Mutation (incremental — changed files only)
npx stryker run --mutate='src/changed-module.js'

# Mutation (full)
npx stryker run
```

---

## TypeScript

**覆盖率** —— c8（原生 V8 覆盖率，推荐）或 nyc（Istanbul）：

```json
// package.json
{
  "scripts": {
    "test": "vitest run",
    "test:cov": "vitest run --coverage",
    "test:cov:c8": "c8 --branches 80 --lines 90 --reporter=text npm test"
  }
}
```

```json
// vitest.config.ts or vitest section
{
  "test": {
    "coverage": {
      "provider": "v8",
      "reporter": ["text", "html", "lcov"],
      "branches": 80,
      "lines": 90,
      "functions": 80,
      "statements": 90,
      "exclude": ["node_modules/", "test/", "**/*.d.ts"]
    }
  }
}
```

**变异测试** —— Stryker：

```json
// stryker.conf.json
{
  "$schema": "https://raw.githubusercontent.com/stryker-mutator/stryker/master/packages/core/schema/stryker-core.schema.json",
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts", "!src/**/*.spec.ts"],
  "testRunner": "vitest",
  "reporters": ["clear-text", "html"],
  "thresholds": {
    "high": 90,
    "low": 80,
    "break": 80
  },
  "coverageAnalysis": "perTest"
}
```

**命令**：
```bash
# Coverage
npx c8 --branches --reporter=text npm test
# or
npx vitest run --coverage

# Mutation (incremental — changed files only)
npx stryker run --mutate='src/changed-module.ts'

# Mutation (full)
npx stryker run
```

---

## C

**覆盖率** —— gcov + lcov：

```makefile
# Makefile additions
CFLAGS += --coverage -fprofile-arcs -ftest-coverage
LDFLAGS += --coverage

coverage: test
	gcov -b src/*.c
	lcov --capture --directory . --output-file coverage.info
	lcov --remove coverage.info '/usr/*' 'tests/*' --output-file coverage.info
	lcov --summary coverage.info
	genhtml coverage.info --output-directory coverage-report

clean-coverage:
	find . -name '*.gcda' -o -name '*.gcno' -o -name '*.gcov' | xargs rm -f
	rm -rf coverage.info coverage-report
```

CMake:
```cmake
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()
```

**变异测试** —— Mull：

```yaml
# mull.yml
mutators:
  - cxx_add_to_sub
  - cxx_sub_to_add
  - cxx_mul_to_div
  - cxx_div_to_mul
  - cxx_remove_void_call
  - cxx_negate_condition
  - cxx_boundary

timeout: 10000
reporters:
  - Elements
  - SQLite
```

**命令**：
```bash
# Coverage
make clean-coverage
make CFLAGS="--coverage" test
gcov -b src/*.c
lcov --capture -d . -o coverage.info
lcov --summary coverage.info

# Mutation
clang -fexperimental-new-pass-manager -fpass-plugin=/path/to/mull-ir-frontend.so \
      -g -O0 src/*.c tests/*.c -o test-binary
mull-runner ./test-binary
```

---

## C++

**覆盖率** —— gcov + lcov 或 llvm-cov：

```cmake
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-instr-generate -fcoverage-mapping")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fprofile-instr-generate")
    endif()
endif()
```

**命令**：
```bash
# GCC + gcov + lcov
cmake -DENABLE_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug ..
make && ctest
gcov -b src/*.cpp
lcov --capture -d . -o coverage.info
lcov --remove coverage.info '/usr/*' '*/test/*' -o coverage.info
lcov --summary coverage.info

# Clang + llvm-cov
cmake -DENABLE_COVERAGE=ON -DCMAKE_CXX_COMPILER=clang++ ..
make && ctest
llvm-profdata merge -sparse default.profraw -o coverage.profdata
llvm-cov report ./test-binary -instr-profile=coverage.profdata
llvm-cov show ./test-binary -instr-profile=coverage.profdata --format=html > cov-report.html

# Mutation (Mull — same approach as C)
clang++ -fexperimental-new-pass-manager -fpass-plugin=/path/to/mull-ir-frontend.so \
        -g -O0 src/*.cpp tests/*.cpp -o test-binary
mull-runner ./test-binary
```

---

## 语言预设

使用 `init_project.py --lang <language>` 时：

| 语言 | 测试框架 | 覆盖率工具 | 变异测试工具 |
|----------|---------------|---------------|---------------|
| `python` | pytest | pytest-cov | mutmut |
| `java` | junit | jacoco | pitest |
| `javascript` | jest | c8-jest | stryker |
| `typescript` | vitest | c8 | stryker |
| `c` | ctest | gcov | mull |
| `cpp` / `c++` | gtest | gcov | mull |

## 默认阈值

| 指标 | 默认值 | 依据 |
|--------|---------|-----------|
| 行覆盖率 | >= 90% | 大部分生产代码路径须有测试 |
| 分支覆盖率 | >= 80% | 条件逻辑须双向执行 |
| 变异分数 | >= 80% | 测试应能发现约 4/5 的注入缺陷 |
| 全量变异阈值 | 100 features | 活跃特性数 ≤ 该值时，每特性可跑全量变异 |

---

## 按特性的变异测试范围

当项目活跃特性数超过 `mutation_full_threshold` 时，质量门禁将变异范围限定为**当前特性的变更源文件及其测试**，避免每个变异体都跑完整测试套件（大项目中过慢）。

**原则**：仅对变更源文件做变异，每个变异体只跑该特性相关测试。全量变异在 ST 阶段（Step 3b）执行，以捕获项目级回归。

### 如何识别特性测试文件

- TDD 周期内为本特性创建/修改的测试文件
- 约定：源文件为 `src/foo.ext` 时，测试常为 `tests/test_foo.ext`
- 标记：若项目使用 marker/tag，按特性标记过滤
- Worker 将特性测试文件路径传给 Quality SubAgent

### 各工具的范围参考

| 工具 | 变异目标限定方式 | 测试范围限定机制 |
|------|------------------------|------------------------|
| mutmut | `--paths-to-mutate={files}` | `--runner='{test_runner} {test_files}'` |
| pitest | `-DtargetClasses={classes}` | `-DtargetTests={test_classes}` |
| stryker | `--mutate='{files}'` | `--coverageAnalysis perTest` (auto-selects relevant tests) |
| mull | `--filters={files}` | Build feature-specific test binary |

### 各工具说明

- **mutmut** `--runner`：提供完整测试执行命令（含框架可执行文件与文件路径）。`{test_runner}` 占位解析为项目测试命令（如 `python -m pytest -x --tb=short`、`npx vitest run`）。
- **pitest** `-DtargetTests`：接受逗号分隔的 Java 类模式（如 `com.example.UserAuthTest,com.example.UserLoginTest`）。
- **Stryker** `--coverageAnalysis perTest`：Stryker 自动判断覆盖每个变异体的测试并仅运行这些测试。无需显式测试文件列表。需要 Stryker 6+。
- **mull**：编译测试二进制时仅链接与本特性相关的测试目标文件；按特性范围通常需单独构建二进制。
