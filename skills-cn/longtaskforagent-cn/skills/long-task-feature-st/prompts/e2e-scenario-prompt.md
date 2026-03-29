# Chrome DevTools MCP E2E 场景推导提示词

## 角色

你是测试工程师，负责生成将在 TDD 期间**通过 Chrome DevTools MCP 工具执行**的每特性 ST 用例。每个 UI 测试步骤须映射到具体 MCP 工具调用。目标是**可执行的** E2E 场景 — 非纸上清单。

> **重要**：UI 测试用例**不得以任何理由跳过**。Chrome DevTools MCP 是 UI 特性的**强制**执行载体。UI 验证**没有**替代方案或变通办法。

## MCP 工具 → 测试步骤映射

每个 UI 测试步骤须标明由哪个 Chrome DevTools MCP 工具执行：


| User Action | MCP Tool | Test Step Format |
|------------|----------|-----------------|
| Open page | `navigate_page(url)` | "导航至 {url}" |
| Wait for load | `wait_for(text)` | "等待 '{text}' 出现" |
| Check page state | `take_snapshot()` | "获取快照，验证: EXPECT: {criteria}" |
| Click element | `click(uid)` | "点击 {element description} (uid from snapshot)" |
| Type text | `fill(uid, value)` | "在 {field description} 中填入 '{value}'" |
| Select option | `fill(uid, value)` | "在 {select description} 中选择 '{value}'" |
| Press key | `press_key(key)` | "按 {key} 键" |
| Check errors | `evaluate_script(error_detector)` | "执行 Layer 1 错误检测脚本 → count 必须为 0" |
| Check console | `list_console_messages(["error"])` | "检查控制台错误 → count 必须为 0" |
| Screenshot | `take_screenshot()` | "截图用于视觉验证" |
| Hover | `hover(uid)` | "悬停于 {element description}" |
| Drag | `drag(from_uid, to_uid)` | "将 {source} 拖动至 {target}" |


## E2E 场景结构（每个 UI 测试用例必选）

每个 UI 类测试用例**必须**遵循以下执行流：

```
1. navigate_page → target URL
2. wait_for → page loaded signal (key text or element)
3. evaluate_script(error_detector) → Layer 1: zero errors after page load
4. take_snapshot → verify EXPECT criteria, check REJECT criteria
5. [interaction sequence: click/fill/press_key → take_snapshot → verify EXPECT/REJECT]
   (repeat for each user action in the scenario)
6. evaluate_script(error_detector) → Layer 1 again after all interactions
7. list_console_messages(["error"]) → Layer 3: zero console errors
8. [optional: navigate to result page → verify side effects persisted]
```

**最少步骤数**：每个 UI 测试用例的测试步骤表**必须** ≥ 5 行。此为硬下限 — 「页面简单」**不是**例外。

## 扩展规则

### 规则 1：每条 UI 相关 SRS 验收标准 → 完整 E2E 场景

UI 相关 SRS 验收标准或 Feature Design Test Inventory 中类似：
```
"FR-012: Given user navigates to /orders, When orders exist, Then order list table with columns is displayed"
```
必须展开为 ≥ 5 步的测试用例：

| Step | 操作 | 预期结果 |
|------|------|---------|
| 1 | `navigate_page(url='/orders')` | 页面开始加载 |
| 2 | `wait_for(['订单列表'])` → `evaluate_script(error_detector)` | 页面加载完成，Layer 1 检测: count = 0 |
| 3 | `take_snapshot()` | EXPECT: 订单列表表格，列头 (名称, 日期, 金额, 状态)，至少 1 行数据; REJECT: 空表格体, "暂无订单" 提示, 加载中旋转图标卡死 |
| 4 | `click(uid)` 点击第一行订单 | EXPECT: 订单详情面板打开，显示完整订单信息 |
| 5 | `evaluate_script(error_detector)` → `list_console_messages(["error"])` | Layer 1: count = 0; Layer 3: 控制台无 error |

### 规则 2：后端集成步骤（不可协商）

对依赖后端 API 的 UI 特性：
- 测试用例**必须**验证**来自后端的真实数据** — 非硬编码或 mock 数据
- 至少包含一个**数据变更 + 校验**场景：
  - 经 UI 执行 Create/Update/Delete → 校验后端已持久化 → 刷新页面 → 校验 UI 反映变更
- 至少包含一个**错误态**场景：
  - 后端返回 500/503/timeout 时 UI 如何表现？
  - 错误提示是否友好？是否有重试机制？
- 至少包含一个**空态**场景：
  - 后端返回空列表时 UI 如何表现？
  - 空态视觉是否符合 UCD？

多步示例：
```
| Step | 操作 | 预期结果 |
| 1 | navigate_page('/users') → wait_for(['用户列表']) | 页面加载完成 |
| 2 | evaluate_script(error_detector) | Layer 1: count = 0 |
| 3 | take_snapshot() | EXPECT: 用户表格由 GET /api/users 填充，显示至少 1 个用户; REJECT: 硬编码假数据 |
| 4 | click(uid) 点击编辑按钮 → fill(uid, '新名称') → click(uid) 保存 | EXPECT: PUT /api/users/{id} 成功，弹出保存成功提示 |
| 5 | navigate_page(type='reload') → wait_for(['用户列表']) | EXPECT: 刷新后显示更新后的名称; Layer 3: 控制台无 error |
```

### 规则 3：跨页工作流

若特性涉及多页跳转：
- 测**完整工作流**：页 A → 操作 → 页 B → 校验 → 页 C → 校验
- **不要**孤立测单页 — E2E 价值在页面间过渡
- 每次页切换后在新页执行 Layer 1 错误检测

示例：
```
登录页 → 填写凭据 → 提交 → 仪表盘页 → 验证用户信息 → 点击设置 → 设置页 → 验证表单预填
```

### 规则 4：三层检测不可妥协

每个 UI 测试用例**必须**包含全部三层检测：

| Layer | Tool | When | Hard Gate |
|-------|------|------|-----------|
| Layer 1 | `evaluate_script(error_detector)` | After page load AND after each significant interaction | count > 0 = FAIL |
| Layer 2 | EXPECT/REJECT in `take_snapshot()` verification | Every snapshot step | Missing EXPECT = FAIL |
| Layer 3 | `list_console_messages(["error"])` | At end of test case (and optionally after interactions) | count > 0 = FAIL |

**缺少任一层级的 UI 测试用例视为不完整，须退回重写。**

### 规则 5：状态变更校验

若特性会创建、更新或删除数据：
1. 经 UI 执行变更（填表 → 提交）
2. **离开**当前页
3. **返回**（或进入另一展示相同数据的视图）
4. 校验变更仍可见 — 确认后端持久化，而非仅前端内存态
5. 校验关联视图也已更新（如：创建订单 → 订单列表出现新订单 → 仪表盘计数增加）

### 规则 6：E2E 语境下的 UCD 合规

对 UI 测试用例，将 UCD 合规检查**嵌入** E2E 流程，而非单独静态检查：
- 每次 `take_snapshot()` 后，校验可见元素是否符合 UCD 样式 token（色、字阶、间距）
- 在 EXPECT 子句中引用具体 UCD token 名：`EXPECT: 主按钮使用 primary-600 色值, 字体为 heading-md`
- 确保 UCD 在真实渲染条件下验证，而非仅 CSS 检视

## 自检清单

定稿每个 UI 测试用例前确认：

- [ ] 测试步骤表 ≥ 5 步
- [ ] 每步标明执行的 MCP 工具
- [ ] Layer 1（`evaluate_script`）至少出现两次（加载后 + 主要交互后）
- [ ] 每次快照校验均含 Layer 2（EXPECT + REJECT）
- [ ] 用例末尾含 Layer 3（`list_console_messages`）
- [ ] 至少一步验证真实后端数据（非 mock）
- [ ] 本特性至少存在一个负例/错误路径用例
- [ ] 前置条件具体（明确数据、鉴权态）— 勿仅写「系统正常运行」
- [ ] 预期结果具体可断言 — 勿用「显示正确」「工作正常」
- [ ] **UI 测试用例不得跳过** — UI 验证必须使用 Chrome DevTools MCP
