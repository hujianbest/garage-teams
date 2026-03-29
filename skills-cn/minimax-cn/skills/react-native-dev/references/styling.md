# 样式参考

StyleSheet、NativeWind/Tailwind、平台特定样式以及 Expo/React Native 主题。

## 样式表```tsx
import { StyleSheet } from "react-native";
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  text: { fontSize: 16, fontWeight: "600" },
});
```与内联样式对象相比，更喜欢“StyleSheet.create”——它会在创建时验证样式并实现未来潜在的优化。

## 特定于平台的样式```tsx
import { Platform, StyleSheet } from "react-native";

const styles = StyleSheet.create({
  shadow: Platform.select({
    ios: { shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
    android: { elevation: 4 },
  }),
});
```从 React Native 0.76+ 开始，支持“boxShadow”作为统一的跨平台影子 API。当针对新架构时，更喜欢它而不是特定于平台的影子属性。

## NativeWind / Tailwind CSS

对于现有项目，请检查“package.json”中的 NativeWind 版本并遵循相应的文档。对于新项目，请使用 NativeWind v4（稳定版）。

### 安装（NativeWind v4）```bash
npx expo install nativewind tailwindcss@3 \
  tailwind-merge clsx
```＃＃＃ 配置```js
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
    plugins: ["nativewind/babel"],
  };
};
```

```js
// tailwind.config.js
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: { extend: {} },
};
```

```css
/* global.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

```tsx
// app/_layout.tsx
import "../global.css";
```＃＃＃ 用法```tsx
<View className="flex-1 bg-white p-4">
  <Text className="text-lg font-semibold text-gray-900">Title</Text>
  <Pressable className="mt-4 rounded-lg bg-blue-500 px-4 py-2">
    <Text className="text-center text-white font-medium">Button</Text>
  </Pressable>
</View>
```### 条件类```tsx
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

<View className={cn("p-4", isActive && "bg-blue-500", isDisabled && "opacity-50")} />
```## 主题和深色模式

对于使用 NativeWind 的应用程序，请使用 Tailwind 的“dark:”变体：```tsx
<View className="bg-white dark:bg-gray-900">
  <Text className="text-gray-900 dark:text-white">Adaptive text</Text>
</View>
```对于基于 StyleSheet 的项目，读取系统配色方案并将其映射到主题对象：```tsx
import { useColorScheme } from "react-native";

const colorScheme = useColorScheme(); // "light" | "dark"
```将颜色标记保存在带有浅色和深色变体的中央“constants/colors.ts”文件中。通过 React Context 或 Zustand 存储传递活动调色板。