# 状态管理参考

React Native / Expo 应用程序中本地、共享和服务器状态的模式。

## 决策指南

|状态类型 |解决方案 |
|------------|----------|
|本地 UI 状态（切换、输入）| `useState` / `useReducer` |
|共享应用程序范围的状态 | Zustand 或 Jotai |
|服务器/异步数据 | React 查询（TanStack 查询）|
|表格状态 | React Hook Form（参见 forms.md）|
|身份验证/会话 | Zustand + `expo-secure-store` |

**避免**：新项目的 Redux（样板）、高频更新的上下文（重新渲染开销）。

## useState / useReducer```tsx
// Simple toggle
const [isOpen, setIsOpen] = useState(false);

// Complex local state — useReducer
type State = { count: number; status: "idle" | "loading" | "error" };
type Action = { type: "increment" } | { type: "setStatus"; payload: State["status"] };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "increment": return { ...state, count: state.count + 1 };
    case "setStatus": return { ...state, status: action.payload };
  }
}

const [state, dispatch] = useReducer(reducer, { count: 0, status: "idle" });
dispatch({ type: "increment" });
```## Zustand（共享状态）```bash
npx expo install zustand
```

```tsx
// stores/settings-store.ts
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import AsyncStorage from "@react-native-async-storage/async-storage";

interface SettingsStore {
  theme: "light" | "dark";
  locale: string;
  setTheme: (theme: "light" | "dark") => void;
  setLocale: (locale: string) => void;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      theme: "light",
      locale: "en",
      setTheme: (theme) => set({ theme }),
      setLocale: (locale) => set({ locale }),
    }),
    {
      name: "settings-storage",
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Usage
const { theme, setTheme } = useSettingsStore();
const locale = useSettingsStore((s) => s.locale); // Selector — minimizes re-renders
```

```tsx
// stores/cart-store.ts
interface CartStore {
  items: CartItem[];
  add: (product: Product) => void;
  remove: (id: string) => void;
  clear: () => void;
  total: () => number;
}

export const useCartStore = create<CartStore>()((set, get) => ({
  items: [],
  add: (product) => set((s) => ({
    items: [...s.items, { product, quantity: 1 }],
  })),
  remove: (id) => set((s) => ({
    items: s.items.filter((i) => i.product.id !== id),
  })),
  clear: () => set({ items: [] }),
  total: () => get().items.reduce((sum, i) => sum + i.product.price * i.quantity, 0),
}));
```## Jotai（原子态）```bash
npx expo install jotai
```

```tsx
// atoms/user-atoms.ts
import { atom } from "jotai";
import { atomWithStorage, createJSONStorage } from "jotai/utils";
import AsyncStorage from "@react-native-async-storage/async-storage";

const storage = createJSONStorage(() => AsyncStorage);

export const userAtom = atom<User | null>(null);
export const themeAtom = atomWithStorage<"light" | "dark">("theme", "light", storage);

// Derived atom — computed from others
export const isAdminAtom = atom((get) => get(userAtom)?.role === "admin");
```

```tsx
// Usage — component only re-renders when its atoms change
import { useAtom, useAtomValue, useSetAtom } from "jotai";

function Header() {
  const user = useAtomValue(userAtom);         // read-only
  const setTheme = useSetAtom(themeAtom);      // write-only
  const [theme, setThemeRW] = useAtom(themeAtom); // read + write
  return <Text>{user?.name}</Text>;
}
```**祖斯坦 vs 乔泰**：
- **Zustand** — 基于商店，更适合与操作相关的状态（身份验证、购物车）
- **Jotai** — 基于原子，更适合独立值，细粒度订阅，避免重新渲染

## 反应查询（服务器状态）

请参阅 [networking.md](networking.md) 以获取完整参考。关键模式：```tsx
// Queries — read
const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });

// Mutations — write
const mutation = useMutation({
  mutationFn: createUser,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
});

// Optimistic update
const mutation = useMutation({
  mutationFn: updateUser,
  onMutate: async (newUser) => {
    await queryClient.cancelQueries({ queryKey: ["user", newUser.id] });
    const prev = queryClient.getQueryData(["user", newUser.id]);
    queryClient.setQueryData(["user", newUser.id], newUser);
    return { prev };
  },
  onError: (_err, variables, context) => {
    queryClient.setQueryData(["user", variables.id], context?.prev);
  },
});
```## 最小化重新渲染

### Zustand 选择器```tsx
// ✗ Wrong — re-renders on any store change
const store = useAuthStore();

// ✓ Correct — re-renders only when user changes
const user = useAuthStore((s) => s.user);
const logout = useAuthStore((s) => s.logout); // Actions are stable references
```### 调度程序模式```tsx
// ✗ Wrong — passes callbacks that recreate on every render
function Parent() {
  const [count, setCount] = useState(0);
  return <Child onIncrement={() => setCount(c => c + 1)} />;
}

// ✓ Correct — dispatcher reference is stable
function Parent() {
  const [count, dispatch] = useReducer(reducer, 0);
  return <Child dispatch={dispatch} />;
}
```### React 编译器（SDK 54+）

启用 React Compiler 后，`memo`、`useCallback` 和 `useMemo` 通常是不必要的：```json
// app.json
{ "expo": { "experiments": { "reactCompiler": true } } }
```## 上下文（谨慎使用）

上下文适用于不经常更改的值（主题、区域设置、身份验证状态）。 **避免**高频更新，例如滚动位置或表单输入。```tsx
const ThemeContext = createContext<"light" | "dark">("light");

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  return <ThemeContext value={theme}>{children}</ThemeContext>; // React 19+
}

// Consume
const theme = use(ThemeContext); // React 19+
```## 第一次渲染时的回退```tsx
// ✓ Always show fallback while async state loads
function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading } = useQuery({ queryKey: ["user", userId], queryFn: () => fetchUser(userId) });
  if (isLoading) return <UserProfileSkeleton />;
  if (!data) return null;
  return <Profile user={data} />;
}
```
