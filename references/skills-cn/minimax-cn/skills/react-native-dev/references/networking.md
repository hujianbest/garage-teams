# 网络参考

为 Expo 应用程序构建强大的数据层：API 客户端、服务器状态、身份验证和服务器端路由。

## API 客户端

### 设置

围绕“fetch”（或 SDK 53+ 上的“expo/fetch”）创建一个薄包装器，而不是安装 axios。构建一个通用的 `request<T>(path, init?)` 函数：

- 将 `process.env.EXPO_PUBLIC_API_URL` 添加到路径前面
- 默认 `Content-Type: application/json`，合并调用者标头
- 在 `!res.ok` 上，抛出附加了 `status` 和 `body` 的错误（使用 `Object.assign`），以便调用者可以根据 HTTP 状态进行分支
- 返回 `res.json() 作为 Promise<T>`

然后导出便捷方法：`api.get<T>(path)`、`api.post<T>(path, body)`等，每个方法都使用适当的方法和`JSON.stringify(body)`委托给`request()`。

### 输入错误

区分网络级故障（无连接、DNS）和 HTTP 级错误 (4xx/5xx)。上面的包装器将“status”和“body”附加到抛出的错误上，以便调用者可以分支：```tsx
try {
  await api.post("/tasks", newTask);
} catch (err: any) {
  if (err.status === 409) {
    Alert.alert("Duplicate", "A task with that title already exists.");
  } else if (err.status === undefined) {
    Alert.alert("Offline", "Check your connection and try again.");
  }
}
```## 服务器状态（反应查询）

### 提供者```tsx
// app/_layout.tsx
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000 } },
});

export default function RootLayout() {
  return (
    <QueryClientProvider client={qc}>
      <Stack />
    </QueryClientProvider>
  );
}
```### 读取数据```tsx
function TaskList({ projectId }: { projectId: string }) {
  const { data: tasks, isPending, error } = useQuery({
    queryKey: ["projects", projectId, "tasks"],
    queryFn: () => api.get<Task[]>(`/projects/${projectId}/tasks`),
  });

  if (isPending) return <ActivityIndicator />;
  if (error) return <ErrorBanner message={error.message} />;

  return (
    <FlashList
      data={tasks}
      renderItem={({ item }) => <TaskRow task={item} />}
      estimatedItemSize={56}
    />
  );
}
```### 写入数据```tsx
function useCompleteTask(projectId: string) {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => api.put(`/tasks/${taskId}`, { done: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects", projectId, "tasks"] }),
  });
}
```### 乐观更新

对于快速 UI，请在服务器确认之前更新缓存：```tsx
const toggle = useMutation({
  mutationFn: (task: Task) => api.put(`/tasks/${task.id}`, { done: !task.done }),
  onMutate: async (task) => {
    await qc.cancelQueries({ queryKey });
    const prev = qc.getQueryData<Task[]>(queryKey);
    qc.setQueryData<Task[]>(queryKey, (old) =>
      old?.map((t) => (t.id === task.id ? { ...t, done: !t.done } : t)),
    );
    return { prev };
  },
  onError: (_err, _task, ctx) => qc.setQueryData(queryKey, ctx?.prev),
  onSettled: () => qc.invalidateQueries({ queryKey }),
});
```## 身份验证

### 存储凭证

对任何令牌或秘密使用“expo-secure-store”。 AsyncStorage 未加密，可在 root/越狱设备上读取。```tsx
import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "session_token";

export async function saveToken(token: string) {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}
export async function getToken() {
  return SecureStore.getItemAsync(TOKEN_KEY);
}
export async function clearToken() {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}
```### 注入身份验证标头

扩展 API 客户端以自动附加令牌：```tsx
export async function authRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getToken();
  return request<T>(path, {
    ...init,
    headers: { ...init?.headers, ...(token && { Authorization: `Bearer ${token}` }) },
  });
}
```### 刷新过期令牌

当多个请求发现令牌同时过期时，避免踩踏刷新调用。持有一个飞行中刷新承诺并让所有服务员分享：```tsx
let pending: Promise<string> | null = null;

async function getFreshToken(): Promise<string> {
  if (pending) return pending;

  pending = (async () => {
    const refresh = await SecureStore.getItemAsync("refresh_token");
    const { accessToken } = await api.post<{ accessToken: string }>("/auth/refresh", { refresh });
    await saveToken(accessToken);
    return accessToken;
  })();

  try {
    return await pending;
  } finally {
    pending = null;
  }
}
```## 环境变量```bash
# .env.development
EXPO_PUBLIC_API_URL=http://localhost:3000

# .env.production
EXPO_PUBLIC_API_URL=https://api.production.example.com
```- “EXPO_PUBLIC_”前缀使变量在客户端 JS 中可用（在构建时内联）
- **不带**前缀的变量只能在服务器端 API 路由中访问
- 切勿通过“EXPO_PUBLIC_”公开数据库凭据或可写的 API 密钥
- 编辑`.env`文件后重新启动开发服务器

输入自动完成的变量：```tsx
// env.d.ts
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      EXPO_PUBLIC_API_URL: string;
    }
  }
}
export {};
```## 离线和连接

使用“@react-native-community/netinfo”跟踪设备连接并将其连接到 React Query，以便查询自动离线暂停并在重新连接时恢复：```tsx
// app/_layout.tsx (once, at startup)
import { onlineManager } from "@tanstack/react-query";
import NetInfo from "@react-native-community/netinfo";

onlineManager.setEventListener((setOnline) =>
  NetInfo.addEventListener((state) => setOnline(!!state.isConnected)),
);
```要显示应用内横幅，请单独订阅：```tsx
function useOnline() {
  const [online, setOnline] = useState(true);
  useEffect(() => NetInfo.addEventListener((s) => setOnline(!!s.isConnected)), []);
  return online;
}
```## 请求生命周期

### 取消

当组件在请求中卸载时，中止正在进行的获取以避免在已卸载的组件上设置状态：```tsx
useEffect(() => {
  const ac = new AbortController();
  api.get(`/projects/${id}`, { signal: ac.signal }).then(setProject);
  return () => ac.abort();
}, [id]);
```React Query 自动处理查询的取消——无需额外的工作。

### 重试

React Query 默认重试失败的查询（指数退避 3 次尝试）。对于突变或非 React-Query 代码，手动实现：```tsx
async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === attempts - 1) throw err;
      await new Promise((r) => setTimeout(r, 1000 * 2 ** i));
    }
  }
  throw new Error("unreachable");
}
```## 服务器端 API 路由

Expo Router 支持在服务器上运行的 `+api.ts` 文件（部署到 EAS Hosting / Cloudflare Workers）。当您需要在服务器端保守秘密、代理第三方 API 或运行数据库查询时，请使用它们。

### 惯例```
app/
  api/
    health+api.ts              → GET /api/health
    projects+api.ts            → GET|POST /api/projects
    projects/[id]+api.ts       → GET|PUT|DELETE /api/projects/:id
    webhooks/payments+api.ts   → POST /api/webhooks/payments
```每个 HTTP 方法导出一个命名函数：```ts
// app/api/projects+api.ts
export async function GET(req: Request) {
  const url = new URL(req.url);
  const cursor = url.searchParams.get("cursor");
  const rows = await db.query("SELECT * FROM projects WHERE id > ? LIMIT 20", [cursor ?? 0]);
  return Response.json(rows);
}

export async function POST(req: Request) {
  const { name, description } = await req.json();
  const [row] = await db.insert(projectsTable).values({ name, description }).returning();
  return Response.json(row, { status: 201 });
}
```### 秘密

**不带** `EXPO_PUBLIC_` 前缀的变量仅适用于服务器：```ts
// app/api/ai/summarize+api.ts
const LLM_KEY = process.env.LLM_API_KEY; // never reaches the client bundle

export async function POST(req: Request) {
  const { text } = await req.json();
  const res = await fetch("https://api.llm.example.com/v1/chat", {
    method: "POST",
    headers: { Authorization: `Bearer ${LLM_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ messages: [{ role: "user", content: `Summarize: ${text}` }] }),
  });
  return Response.json(await res.json());
}
```### 网络钩子```ts
// app/api/webhooks/payments+api.ts — verify signature, then handle event
const event = stripe.webhooks.constructEvent(rawBody, sig, process.env.STRIPE_WH_SECRET!);
if (event.type === "checkout.session.completed") {
  await activateSubscription(event.data.object.customer as string);
}
```### 保护路由```ts
// lib/require-auth.ts — extract and verify JWT from Authorization header, throw Response on failure
export async function requireAuth(req: Request): Promise<string> {
  const header = req.headers.get("Authorization");
  if (!header?.startsWith("Bearer "))
    throw Response.json({ error: "unauthorized" }, { status: 401 });
  const uid = await verifyJwt(header.slice(7));
  if (!uid) throw Response.json({ error: "invalid token" }, { status: 401 });
  return uid;
}
// Usage in route: const uid = await requireAuth(req);
```### 部署```bash
npx expo export
eas deploy            # preview
eas deploy --prod     # production

# Set server-only secrets
eas env:create --name LLM_API_KEY --value "sk-..." --environment production
```API 路由在 Cloudflare Workers 上运行 — 无“fs”模块，30 秒 CPU 限制，使用 Web API（“fetch”、“crypto.subtle”）而不是 Node 内置组件。