# 测试参考

Jest、React Native 测试库以及 Expo/React Native 应用程序的 E2E 测试。

＃＃ 设置```bash
npx expo install jest-expo @testing-library/react-native
```

```json
// package.json
{
  "jest": {
    "preset": "jest-expo",
    "setupFilesAfterSetup": ["@testing-library/react-native/extend-expect"]
  }
}
```

```bash
npx jest                    # Run all tests
npx jest --watch            # Watch mode
npx jest --coverage         # Coverage report
npx jest path/to/test.tsx   # Single file
```## React Native 测试库

### 基本组件测试```tsx
// components/__tests__/Button.test.tsx
import { render, fireEvent, screen } from "@testing-library/react-native";
import { Button } from "../Button";

describe("Button", () => {
  it("renders label", () => {
    render(<Button label="Submit" onPress={() => {}} />);
    expect(screen.getByText("Submit")).toBeTruthy();
  });

  it("calls onPress when tapped", () => {
    const onPress = jest.fn();
    render(<Button label="Submit" onPress={onPress} />);
    fireEvent.press(screen.getByText("Submit"));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("is disabled when loading", () => {
    render(<Button label="Submit" onPress={() => {}} loading />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
```### 查询```tsx
// Prefer accessible queries
screen.getByRole("button", { name: "Submit" });
screen.getByLabelText("Email");
screen.getByPlaceholderText("Enter email");

// Text content
screen.getByText("Welcome back");
screen.getByText(/welcome/i);   // Regex — case insensitive

// Test IDs (last resort)
screen.getByTestId("user-avatar");

// Async queries
await screen.findByText("Loaded content");       // Waits for element to appear
await screen.findAllByRole("listitem");

// Non-existence
expect(screen.queryByText("Error")).toBeNull();
```### 用户事件```tsx
import { userEvent } from "@testing-library/react-native";

it("submits form on valid input", async () => {
  const user = userEvent.setup();
  render(<LoginForm onSubmit={mockSubmit} />);

  await user.type(screen.getByPlaceholderText("Email"), "user@example.com");
  await user.type(screen.getByPlaceholderText("Password"), "password123");
  await user.press(screen.getByRole("button", { name: "Login" }));

  expect(mockSubmit).toHaveBeenCalledWith({
    email: "user@example.com",
    password: "password123",
  });
});
```### 测试异步状态```tsx
import { waitFor, act } from "@testing-library/react-native";

it("shows user data after loading", async () => {
  render(<UserProfile userId="123" />);

  // Loading state
  expect(screen.getByTestId("loading-indicator")).toBeTruthy();

  // Wait for data
  await waitFor(() => {
    expect(screen.getByText("John Doe")).toBeTruthy();
  });

  expect(screen.queryByTestId("loading-indicator")).toBeNull();
});
```### 使用 React 查询进行测试```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
}

function renderWithQuery(ui: ReactElement) {
  const client = createTestQueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

it("fetches and displays posts", async () => {
  // Mock fetch
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve([{ id: "1", title: "Post 1" }]),
  });

  renderWithQuery(<PostsList />);

  await waitFor(() => {
    expect(screen.getByText("Post 1")).toBeTruthy();
  });
});
```### 有条件测试```tsx
import { useAuthStore } from "../../stores/auth-store";

beforeEach(() => {
  // Reset store state before each test
  useAuthStore.setState({ user: null, token: null });
});

it("shows user name when logged in", () => {
  useAuthStore.setState({ user: { id: "1", name: "Alice" }, token: "tok" });
  render(<Header />);
  expect(screen.getByText("Alice")).toBeTruthy();
});
```### 测试导航（Expo 路由器）```tsx
import { renderRouter, screen } from "expo-router/testing-library";

it("navigates to detail screen", async () => {
  renderRouter({
    index: () => <HomeScreen />,
    "user/[id]": () => <UserScreen />,
  });

  fireEvent.press(screen.getByText("View Profile"));

  await waitFor(() => {
    expect(screen.getByTestId("user-screen")).toBeTruthy();
  });
});
```## 嘲笑

### 模拟展览模块```tsx
// __mocks__/expo-secure-store.ts
export const getItemAsync = jest.fn().mockResolvedValue(null);
export const setItemAsync = jest.fn().mockResolvedValue(undefined);
export const deleteItemAsync = jest.fn().mockResolvedValue(undefined);
```

```tsx
// In test
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue("mock-token"),
  setItemAsync: jest.fn(),
}));
```### 模拟获取/API 调用```tsx
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

it("handles API error", async () => {
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: false,
    status: 500,
    json: () => Promise.resolve({ message: "Server error" }),
  });

  render(<UserProfile userId="123" />);

  await waitFor(() => {
    expect(screen.getByText("Server error")).toBeTruthy();
  });
});
```### 模拟反应本机模块```tsx
// jest.setup.ts
jest.mock("react-native/Libraries/Animated/NativeAnimatedHelper");

jest.mock("@react-native-community/netinfo", () => ({
  addEventListener: jest.fn(() => jest.fn()),
  fetch: jest.fn(() => Promise.resolve({ isConnected: true })),
}));
```## 单元测试（非 UI 逻辑）```tsx
// utils/__tests__/format.test.ts
import { formatCurrency, formatDate } from "../format";

describe("formatCurrency", () => {
  it("formats USD", () => expect(formatCurrency(1234.5, "USD")).toBe("$1,234.50"));
  it("handles zero", () => expect(formatCurrency(0, "USD")).toBe("$0.00"));
  it("handles negative", () => expect(formatCurrency(-50, "USD")).toBe("-$50.00"));
});
```

```tsx
// stores/__tests__/cart-store.test.ts
import { useCartStore } from "../cart-store";

beforeEach(() => useCartStore.setState({ items: [] }));

describe("CartStore", () => {
  it("adds item", () => {
    useCartStore.getState().add(mockProduct);
    expect(useCartStore.getState().items).toHaveLength(1);
  });

  it("calculates total", () => {
    useCartStore.getState().add({ ...mockProduct, price: 10 });
    expect(useCartStore.getState().total()).toBe(10);
  });
});
```## E2E 测试（Maestro）

Maestro 是 Expo 推荐的 E2E 工具 — 无需构建配置。```bash
# Install
curl -Ls "https://get.maestro.mobile.dev" | bash

# Run flow
maestro test flows/login.yaml
```

```yaml
# flows/login.yaml
appId: com.example.myapp
---
- launchApp
- tapOn:
    text: "Sign In"
- inputText:
    id: "email-input"
    text: "user@example.com"
- inputText:
    id: "password-input"
    text: "password123"
- tapOn:
    text: "Login"
- assertVisible:
    text: "Welcome back"
- takeScreenshot: login-success
```

```yaml
# flows/create-post.yaml
appId: com.example.myapp
---
- launchApp
- runFlow: ./login.yaml
- tapOn:
    id: "new-post-button"
- inputText:
    id: "post-title"
    text: "My Test Post"
- tapOn:
    text: "Publish"
- assertVisible:
    text: "My Test Post"
```## 测试清单

|层|测试什么 |
|--------|-------------|
|单位|业务逻辑、存储、实用函数、挂钩 |
|组件|正确渲染、用户交互、加载/错误状态 |
|整合 |组件+存储/查询协同工作|
|端到端|关键用户流程（登录、结帐、核心功能）|

## 常见错误

|错误 |对|
|--------|--------|
| `getByTestId` 无处不在 |使用可访问的查询（`getByRole`、`getByLabelText`）|
|测试实施细节|测试用户看到的行为 |
|异步操作上没有“waitFor” |用于异步的 `waitFor` 或 `findBy*`
|测试中的真实网络调用|模拟“fetch”或使用 MSW |
|测试每一行 |关注行为，而不是覆盖率