# CMake + GoogleTest 项目配置参考

**何时加载此参考：** 从零搭建 C++ 项目、配置 GoogleTest、或遇到 CMake 构建问题时。

## 目录

1. [最小项目结构](#最小项目结构)
2. [根 CMakeLists.txt](#根-cmakeliststxt)
3. [引入 GoogleTest（FetchContent）](#引入-googletestfetchcontent)
4. [src 目录](#src-目录)
5. [tests 目录](#tests-目录)
6. [构建与运行](#构建与运行)
7. [常见问题](#常见问题)
8. [IDE 集成](#ide-集成)

## 最小项目结构

```
my_project/
├── CMakeLists.txt           # 项目根 CMake
├── src/
│   ├── CMakeLists.txt       # 产品代码库
│   ├── calculator.h
│   └── calculator.cpp
└── tests/
    ├── CMakeLists.txt       # 测试目标
    └── calculator_test.cpp
```

## 根 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.14)
project(my_project LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_subdirectory(src)

enable_testing()
add_subdirectory(tests)
```

`CMAKE_EXPORT_COMPILE_COMMANDS` 生成 `compile_commands.json`，方便编辑器和静态分析工具使用。

## 引入 GoogleTest（FetchContent）

在 `tests/CMakeLists.txt` 中通过 FetchContent 拉取 GoogleTest，不需要提前安装：

```cmake
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.15.2
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)
```

`gtest_force_shared_crt` 在 Windows/MSVC 上避免运行时库冲突，Linux/macOS 上无害。

### 替代方案

如果网络受限或需要离线构建：

```cmake
# 方案 A：系统已安装 GoogleTest
find_package(GTest REQUIRED)

# 方案 B：作为 git submodule
add_subdirectory(third_party/googletest)
```

## src 目录

```cmake
# src/CMakeLists.txt
add_library(my_project_lib
  calculator.cpp
)
target_include_directories(my_project_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
```

将产品代码编译为库（`my_project_lib`），测试目标链接它即可。
如果项目只有一个可执行文件，也可以把源文件同时编入测试目标——但拆成库更清晰。

## tests 目录

```cmake
# tests/CMakeLists.txt
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.15.2
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

include(GoogleTest)

add_executable(my_project_tests
  calculator_test.cpp
)
target_link_libraries(my_project_tests
  PRIVATE
    my_project_lib
    GTest::gtest_main
    GTest::gmock
)
gtest_discover_tests(my_project_tests)
```

**关键点：**
- 链接 `GTest::gtest_main` 提供 `main()` 函数，测试文件不需要自己写
- 链接 `GTest::gmock` 如果需要使用 GoogleMock（MOCK_METHOD、匹配器等）
- `gtest_discover_tests()` 让 CTest 自动发现所有 `TEST()` / `TEST_F()` / `TEST_P()`

### 多个测试文件

```cmake
add_executable(my_project_tests
  calculator_test.cpp
  validator_test.cpp
  parser_test.cpp
)
```

或者用 `file(GLOB ...)` 自动收集（适合测试文件，不推荐产品代码）：

```cmake
file(GLOB TEST_SOURCES "*_test.cpp")
add_executable(my_project_tests ${TEST_SOURCES})
```

## 构建与运行

### 首次构建

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

首次会下载 GoogleTest 源码，后续增量构建不再下载。

### 运行所有测试

```bash
cd build && ctest --output-on-failure
```

`--output-on-failure` 只在测试失败时打印详细输出，保持成功时的输出简洁。

### 运行特定测试

```bash
# 按测试名过滤（支持通配符）
cd build && ctest --output-on-failure -R "CalculatorTest"

# 或直接运行测试可执行文件 + GoogleTest 过滤
./build/tests/my_project_tests --gtest_filter="CalculatorTest.AddsPositiveNumbers"
```

### 常用 CTest 参数

| 参数 | 用途 |
|------|------|
| `--output-on-failure` | 失败时显示完整输出 |
| `-R <regex>` | 只运行匹配的测试 |
| `-E <regex>` | 排除匹配的测试 |
| `-j <N>` | 并行运行 N 个测试 |
| `--verbose` | 显示所有测试输出 |
| `--repeat until-fail:3` | 重复运行直到失败（发现 flaky test） |

### 常用 GoogleTest 命令行参数

| 参数 | 用途 |
|------|------|
| `--gtest_filter=<pattern>` | 过滤测试（支持 `*` 和 `-` 排除） |
| `--gtest_repeat=N` | 重复运行 N 次 |
| `--gtest_shuffle` | 随机顺序运行（发现隐式依赖） |
| `--gtest_list_tests` | 列出所有测试，不运行 |
| `--gtest_break_on_failure` | 失败时中断（配合调试器） |

## 常见问题

### 1. Windows 上链接错误（LNK2038 / runtime library mismatch）

确保 `gtest_force_shared_crt` 在 `FetchContent_MakeAvailable` 之前设置：
```cmake
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)
```

### 2. 找不到 `gtest/gtest.h`

确认 `FetchContent_MakeAvailable(googletest)` 已执行，并且测试目标链接了 `GTest::gtest_main`。

### 3. `gtest_discover_tests` 报错

需要 `include(GoogleTest)` 模块（CMake 3.10+）。

### 4. 测试发现慢

`gtest_discover_tests` 在构建后运行测试可执行文件来发现测试，大型项目可能比较慢。替代方案：

```cmake
# 改用编译时发现（更快但可能漏掉参数化测试名）
gtest_discover_tests(my_project_tests DISCOVERY_MODE PRE_TEST)
```

## IDE 集成

### VS Code（CMake Tools 扩展）

`settings.json` 中添加：
```json
{
  "cmake.buildDirectory": "${workspaceFolder}/build",
  "cmake.configureOnOpen": true
}
```

按 `Ctrl+Shift+P` → "CMake: Build" 构建，"CMake: Run Tests" 运行测试。

### CLion

打开项目根目录即可，CLion 自动识别 CMake。测试用例可以单独运行或调试。

### Visual Studio

```bash
cmake -B build -G "Visual Studio 17 2022"
```

打开 `build/my_project.sln`，Test Explorer 自动发现 GoogleTest 用例。
