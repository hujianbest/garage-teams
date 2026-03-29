# 工程参考

Expo / React Native 的项目结构、工具、构建、发布和平台集成。

## 项目结构

### 标准布局```
my-app/
  app/                        File-based routing (Expo Router)
    _layout.tsx               Root layout: providers, fonts, NativeTabs
    index.tsx                 → /
    (tabs)/
      _layout.tsx             Tab navigator
      home.tsx                → /home
      profile.tsx             → /profile
    (auth)/
      login.tsx               → /login (group, not in URL)
      register.tsx            → /register
    user/
      [id].tsx                → /user/:id
      [id]/
        posts.tsx             → /user/:id/posts
    api/
      users+api.ts            → /api/users (server route)
      users/[id]+api.ts       → /api/users/:id
  components/                 Reusable UI components
    ui/                       Primitive components (Button, Input, Card)
    shared/                   Composed components (UserAvatar, PostCard)
  hooks/                      Custom React hooks
  stores/                     Zustand / Jotai stores
  services/                   API client, external service wrappers
  utils/                      Pure utility functions
  constants/                  App-wide constants (colors, spacing, config)
  types/                      Shared TypeScript types/interfaces
  assets/                     Static assets (images, fonts, icons)
  scripts/                    Build/dev helper scripts
  app.json                    Expo config
  eas.json                    EAS Build config
  tsconfig.json               TypeScript config with path aliases
  .env                        Environment variables
  .env.development
  .env.production
```### 路由约定

|文件 |路线 |笔记|
|------|--------|--------|
| `app/index.tsx` | `/` |主页/根 |
| `app/about.tsx` | `/关于` |静态路由|
| `app/user/[id].tsx` | `/用户/:id` |动态段|
| `app/user/[...rest].tsx` | `/用户/*` |包罗万象 |
| `app/(tabs)/home.tsx` | `/home` |组（不在 URL 中）|
| `app/(a,b)/shared.tsx` |在选项卡“a”和“b”之间共享 |多组|
| `app/_layout.tsx` |布局包装|没有路线 |
| `app/+not-found.tsx` | 404 页面 | |
| `app/api/users+api.ts` | `/api/用户` |服务器路由|

**规则**：
- 仅在“app/”中的路由 - 无组件、类型或实用程序
- 总是有一个匹配`/`的路由
- 使用短横线大小写的文件名（“user-profile.tsx”，而不是“UserProfile.tsx”）
- 重组时删除旧的路线文件

### 路径别名```json
// tsconfig.json
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "paths": {
      "@/*": ["./*"],
      "@components/*": ["./components/*"],
      "@hooks/*": ["./hooks/*"],
      "@stores/*": ["./stores/*"],
      "@services/*": ["./services/*"],
      "@utils/*": ["./utils/*"],
      "@constants/*": ["./constants/*"],
      "@types/*": ["./types/*"]
    }
  }
}
```

```tsx
// ✗ Relative imports — fragile, change with file moves
import { Button } from "../../../components/ui/Button";

// ✓ Alias imports — stable
import { Button } from "@components/ui/Button";
```Metro 原生从“tsconfig.json”解析“paths”和“baseUrl”——无需额外配置。如果使用非 Metro 捆绑程序，请安装“babel-plugin-module-resolver”：```js
// babel.config.js — only needed for non-Metro bundlers
module.exports = {
  presets: ["babel-preset-expo"],
  plugins: [
    ["module-resolver", {
      root: ["./"],
      alias: {
        "@": "./",
        "@components": "./components",
        "@hooks": "./hooks",
        "@stores": "./stores",
        "@services": "./services",
      },
    }],
  ],
};
```### 组件组织```
components/
  ui/                         Atomic components
    Button.tsx
    Input.tsx
    Card.tsx
    Badge.tsx
    index.ts                  Barrel export
  shared/                     Composed components
    UserAvatar.tsx
    PostCard.tsx
    EmptyState.tsx
  layout/                     Layout components
    Screen.tsx                SafeArea wrapper
    Header.tsx
```

```tsx
// components/ui/index.ts — barrel export
export { Button } from "./Button";
export { Input } from "./Input";
export { Card } from "./Card";

// Usage
import { Button, Input, Card } from "@components/ui";
```### 设计系统```
constants/
  colors.ts                   Color palette + semantic colors
  spacing.ts                  8pt grid spacing values
  typography.ts               Font families, sizes, weights
  theme.ts                    Combined theme object
```

```tsx
// constants/colors.ts
export const colors = {
  primary: "#6200EE",
  secondary: "#03DAC6",
  background: "#FFFFFF",
  surface: "#F5F5F5",
  error: "#B00020",
  text: { primary: "#000000DE", secondary: "#0000008A" },
} as const;

// constants/spacing.ts — 8pt grid
export const spacing = {
  xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
} as const;

// constants/typography.ts
export const typography = {
  sizes: { xs: 12, sm: 14, md: 16, lg: 20, xl: 24, xxl: 32 },
  weights: { regular: "400", medium: "500", semibold: "600", bold: "700" },
} as const;
```### 服务层```
services/
  api/
    client.ts               Base fetch client with auth headers
    users.ts                User-related API calls
    posts.ts                Post-related API calls
  storage/
    secure-store.ts         Wrapper for expo-secure-store
    async-storage.ts        Wrapper for AsyncStorage
  notifications/
    push.ts                 Expo push notification helpers
```

```tsx
// services/api/client.ts
const BASE_URL = process.env.EXPO_PUBLIC_API_URL!;

export const api = {
  get: <T,>(path: string, token?: string) =>
    fetch(`${BASE_URL}${path}`, {
      headers: { Authorization: token ? `Bearer ${token}` : "" },
    }).then(async (r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json() as Promise<T>;
    }),
  // post/put/delete follow same pattern — add method, Content-Type, JSON.stringify(body)
};
```### 莫诺雷波```
my-monorepo/
  apps/
    mobile/                 Expo app (all native deps here)
      package.json
      app.json
    web/                    Next.js app
      package.json
  packages/
    ui/                     Shared UI components (no native deps)
      package.json
    utils/                  Shared utilities (no native deps)
      package.json
    types/                  Shared TypeScript types
      package.json
  package.json              Root workspace config
```

```json
// Root package.json
{
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "scripts": {
    "mobile": "yarn workspace @my/mobile start",
    "web": "yarn workspace @my/web dev"
  }
}
```**Monorepo 规则**：
- **将本机依赖项保留在应用程序包中** (`apps/mobile`) - 绝不在共享包中
- 在所有包中使用每个依赖项的单一版本
- 共享包只能是纯 JS/TS

### 环境变量```bash
# .env (committed, non-sensitive defaults)
EXPO_PUBLIC_APP_NAME=MyApp
EXPO_PUBLIC_API_VERSION=v1

# .env.development (local only, gitignored)
EXPO_PUBLIC_API_URL=http://localhost:3000

# .env.production (CI/CD only, gitignored)
EXPO_PUBLIC_API_URL=https://api.production.example.com
```

```tsx
// types/env.d.ts
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      EXPO_PUBLIC_API_URL: string;
      EXPO_PUBLIC_APP_NAME: string;
    }
  }
}
export {};
```### 自定义字体```bash
npx expo install expo-font
```

```json
// app.json — config plugin (preferred over manual linking)
{
  "expo": {
    "plugins": [
      ["expo-font", { "fonts": ["./assets/fonts/Inter-Regular.ttf"] }]
    ]
  }
}
```

```tsx
// app/_layout.tsx
import { useFonts } from "expo-font";
import { SplashScreen } from "expo-router";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({ "Inter-Regular": require("../assets/fonts/Inter-Regular.ttf") });
  useEffect(() => { if (loaded) SplashScreen.hideAsync(); }, [loaded]);
  if (!loaded) return null;
  return <Stack />;
}
```## 开发构建

Expo Go（`npx expo start`）涵盖了大多数开箱即用的用例。当您的项目使用 Expo Go 未捆绑的本机代码时，请切换到自定义开发客户端 - 例如，“modules/”中的本地 Expo 模块、Apple 目标（小部件、应用程序剪辑）或未在 Expo Go 中预安装的社区本机库。

### 创建开发客户端```bash
# Option A — cloud build, push to TestFlight / internal distribution
eas build -p ios --profile development --submit

# Option B — build locally (requires Xcode / Android Studio)
eas build -p ios --profile development --local
```在设备或模拟器上安装后，连接：```bash
npx expo start --dev-client
```### eas.json 配置文件```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "autoIncrement": true
    }
  }
}
```## 升级SDK

### 例行升级```bash
npx expo install expo@latest --fix   # bumps Expo + aligns peer deps
npx expo-doctor                       # surfaces remaining mismatches
```然后在两个平台上进行测试，如果您使用一个平台，则重建开发客户端。

### 尝试预发布

预发布版本在 npm 上标记为“@next”：```bash
npx expo install expo@next --fix
```### 跨 SDK 版本的显着变化

|版本 |发生了什么变化|
|---------|-------------|
| SDK 53 |默认启用新架构； Expo Go 需要它；不再需要`autoprefixer`
| SDK 54 | React 19（`use()` 替换了 `useContext`，`<Context>` 替换了 `<Context.Provider>`，`forwardRef` 被删除）； React 编译器可用；已删除“EXPO_USE_FAST_RESOLVER”|
| SDK 55 | NativeTabs API 更新 - 通过 `NativeTabs.Trigger.*` 访问图标/标签/徽章 |
|正在进行 |已弃用“expo-av”，取而代之的是“expo-audio”+“expo-video” |

### React 19 模式（SDK 54+）```tsx
// Context
import { use, createContext } from "react";
const ThemeCtx = createContext("light");
// consume: const theme = use(ThemeCtx);
// provide: <ThemeCtx value="dark">...</ThemeCtx>

// Refs — no more forwardRef
function Field({ ref, ...props }: Props & { ref?: React.Ref<TextInput> }) {
  return <TextInput ref={ref} {...props} />;
}
```### 选择退出新架构

如果第三方库在新架构下崩溃：```json
{ "expo": { "newArchEnabled": false } }
```在 [reactnative.directory](https://reactnative.directory) 检查兼容性。

## 释放

### 构建配置文件

典型的“eas.json”具有三层：```json
{
  "cli": { "version": ">= 16.0.1", "appVersionSource": "remote" },
  "build": {
    "development": { "developmentClient": true, "distribution": "internal", "autoIncrement": true },
    "preview":     { "distribution": "internal", "autoIncrement": true },
    "production":  { "autoIncrement": true, "ios": { "resourceClass": "m-medium" } }
  }
}
```### 构建和提交```bash
# Build for both platforms
eas build -p ios --profile production
eas build -p android --profile production

# Build + submit in one step
eas build -p ios --profile production --submit

# Or submit a finished build separately
eas submit -p ios
eas submit -p android
```### 商店提交备注

**iOS** — 运行“eascredentials”来设置签名。在 App Store Connect 中创建应用程序记录，填充元数据，然后“--submit”自动将构建推送到 TestFlight。

**Android** — 创建一个 Google Play 服务帐户，下载其 JSON 密钥，并在 `submit.production.android.serviceAccountKeyPath` 下的 `eas.json` 中引用它。第一个版本必须通过 Play Console 手动上传；后续构建使用“eas Submit”。

### 无线更新

对于仅 JS 的更改（没有新的本机代码），请跳过完整的构建/审查周期：```bash
npx expo install expo-updates
eas update --branch production --message "Fix checkout rounding error"
```### 虚拟主机```bash
npx expo export -p web
eas deploy              # preview URL
eas deploy --prod       # production
```## CI/CD 与 EAS 工作流程

工作流程文件位于 `.eas/workflows/` 中并遵循 YAML 架构：```yaml
# .eas/workflows/release.yml
name: Release to stores

on:
  push:
    branches: [main]

jobs:
  build:
    type: build
    params:
      platform: all
      profile: production

  submit:
    type: submit
    needs: [build]
    params:
      platform: all
      profile: production
```

```yaml
# .eas/workflows/pr-check.yml
name: PR check

on:
  pull_request:
    branches: [main]

jobs:
  preview-build:
    type: build
    params:
      platform: all
      profile: preview
```## DOM 组件

“use dom”指令允许您在本机上的 WebView 中渲染仅 Web 的代码，同时在 Web 上将其作为标准 DOM 运行。对于依赖于浏览器 API 的库（图表库、富文本编辑器、语法荧光笔）很有用。```tsx
// components/RichPreview.tsx
"use dom";

import ReactMarkdown from "react-markdown";

export default function RichPreview({ markdown }: { markdown: string }) {
  return <ReactMarkdown>{markdown}</ReactMarkdown>;
}
```

```tsx
// app/note/[id].tsx — native screen
import RichPreview from "@/components/RichPreview";

export default function NoteScreen() {
  const { content } = useNote();
  return (
    <ScrollView>
      <RichPreview markdown={content} />
    </ScrollView>
  );
}
```规则：
- `"use dom"` 必须是文件中的第一个语句
- 每个文件一个默认导出；不能与原生组件混合
- 道具必须是可序列化的（字符串、数字、布尔值、普通对象/数组）
- 异步函数 props 将本机操作桥接到 Web 视图中（例如，`onSave: (data) => Promise<void>`）
- 不能在 `_layout.tsx` 文件中使用
- 读取本机导航状态的路由器钩子（`useLocalSearchParams`、`usePathname`等）必须在本机父级中调用并作为 props 传递