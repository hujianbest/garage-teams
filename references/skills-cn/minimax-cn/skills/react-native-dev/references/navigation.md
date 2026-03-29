# 导航参考

Expo Router 基于文件的导航：堆栈、选项卡、模式、链接和上下文菜单。

## 文件约定```
app/
  _layout.tsx              Root layout (providers, NativeTabs)
  index.tsx                → /
  about.tsx                → /about
  user/
    [id].tsx               → /user/:id
    [id]/
      posts.tsx            → /user/:id/posts
  (tabs)/
    _layout.tsx            Tab navigator (group, not in URL)
    home.tsx               → /home
    profile.tsx            → /profile
  (index,search)/
    _layout.tsx            Shared Stack for both tabs
    index.tsx              → /
    search.tsx             → /search
    i/[id].tsx             → /i/:id (shared detail screen)
  api/
    users+api.ts           → /api/users (server route)
```**规则**：
- 路由仅存在于 `app/` 中 — 切勿将组件、类型或实用程序放置在其中
- 始终有一条与“/”匹配的路线（可能在组内）
- 重组导航时删除旧的路线文件
- 使用短横线大小写的文件名

## 根布局（堆栈）```tsx
// app/_layout.tsx — root is always a Stack
import { Stack } from "expo-router";

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerTransparent: true,
        headerLargeTitle: true,
        headerBackButtonDisplayMode: "minimal",
      }}
    >
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="user/[id]" options={{ headerLargeTitle: false }} />
    </Stack>
  );
}
```**始终通过“Stack.Screen options.title”设置页面标题**，切勿使用自定义文本元素作为标题。

## 选项卡 — 使用哪个

|场景|使用|
|----------|-----|
|定制设计系统，跨平台| **JS 选项卡**（稳定，完全可定制）|
| iOS 原生外观，液态玻璃 (iOS 26+) | **NativeTabs**（alpha，有限定制）|

## JS 标签```tsx
// app/(tabs)/_layout.tsx
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: "blue" }}>
      <Tabs.Screen
        name="home"
        options={{
          tabBarLabel: "Home",
          tabBarIcon: ({ color, size }) => <Ionicons name="home" color={color} size={size} />,
        }}
      />
    </Tabs>
  );
}
```## NativeTabs（alpha，iOS 18+）

> Alpha API — 所有选项卡同时呈现，有限的自定义，Android 上最多 5 个选项卡。当您想要原生 iOS 外观（液体玻璃、原生模糊/过渡）而无需自行重建时使用。```tsx
import { NativeTabs } from "expo-router/unstable-native-tabs";

export default function Layout() {
  return (
    <NativeTabs>
      <NativeTabs.Trigger name="(index)">
        <NativeTabs.Trigger.Icon sf="house" />
        <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="(profile)">
        <NativeTabs.Trigger.Icon sf="person" />
        <NativeTabs.Trigger.Label>Profile</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
```## 多个选项卡的共享堆栈```tsx
// app/(index,search)/_layout.tsx — shared Stack for both index and search tabs
import { Stack } from "expo-router/stack";

const tabLabels: Record<string, string> = { index: "Home", search: "Explore" };

export default function Layout({ segment }: { segment: string }) {
  const activeTab = segment.replace(/[()]/g, "");

  return (
    <Stack screenOptions={{ headerLargeTitle: true, headerBackButtonDisplayMode: "minimal" }}>
      <Stack.Screen name={activeTab} options={{ title: tabLabels[activeTab] }} />
      <Stack.Screen name="i/[id]" options={{ headerLargeTitle: false }} />
    </Stack>
  );
}
```## 链接组件```tsx
import { Link } from "expo-router";

// Basic navigation
<Link href="/about">About</Link>

// Dynamic routes
<Link href={`/user/${userId}`}>Profile</Link>

// Wrapping custom component
<Link href="/settings" asChild>
  <Pressable><Text>Settings</Text></Pressable>
</Link>
```## 程序化导航```tsx
import { useRouter, useLocalSearchParams } from "expo-router";

const router = useRouter();
router.push("/settings");
router.replace("/login");   // No back button
router.back();

// Access route params
const { id } = useLocalSearchParams<{ id: string }>();
```## 模态和板材```tsx
// Modal presentation
<Stack.Screen options={{ presentation: "modal" }} />

// Form sheet with detents
<Stack.Screen
  options={{
    presentation: "formSheet",
    sheetGrabberVisible: true,
    sheetAllowedDetents: [0.5, 1.0],
    contentStyle: { backgroundColor: "transparent" }, // Liquid glass on iOS 26+
  }}
/>
```## 链接上的上下文菜单```tsx
<Link href="/settings" asChild>
  <Link.Trigger>
    <Pressable><Card /></Pressable>
  </Link.Trigger>
  <Link.Menu>
    <Link.MenuAction
      title="Share"
      icon="square.and.arrow.up"
      onPress={handleShare}
    />
    <Link.MenuAction
      title="Delete"
      icon="trash"
      destructive
      onPress={handleDelete}
    />
    <Link.Menu title="More" icon="ellipsis">
      <Link.MenuAction title="Copy" icon="doc.on.doc" onPress={() => {}} />
    </Link.Menu>
  </Link.Menu>
</Link>
```## 链接预览（仅限 iOS，需要 Expo SDK 54+）```tsx
<Link href="/detail">
  <Link.Trigger>
    <Pressable><Card /></Pressable>
  </Link.Trigger>
  <Link.Preview />  {/* Shows peek preview on 3D touch / long press */}
</Link>
```## 标题搜索栏```tsx
// In Stack.Screen — preferred over building custom search UI
<Stack.Screen
  options={{
    headerSearchBarOptions: {
      placeholder: "Search...",
      onChangeText: (e) => setQuery(e.nativeEvent.text),
      onCancelButtonPress: () => setQuery(""),
    },
  }}
/>
```## 深层链接```json
// app.json
{
  "expo": {
    "scheme": "myapp",
    "ios": {
      "associatedDomains": ["applinks:myapp.example.com"]
    },
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [{ "scheme": "https", "host": "myapp.example.com" }],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```Expo Router 自动处理深层链接 - `/user/123` 映射到 `app/user/[id].tsx`。

## 路由中的滚动视图

当路由属于 Stack 时，它的第一个子级几乎总是 ScrollView：```tsx
export default function HomeScreen() {
  return (
    <ScrollView contentInsetAdjustmentBehavior="automatic">
      {/* Content */}
    </ScrollView>
  );
}
```在 `ScrollView`、`FlatList` 和 `SectionList` 上使用 `contentInsetAdjustmentBehavior="automatic"` — 这会自动处理安全区域和标题插入。更喜欢它而不是“<SafeAreaView>”。