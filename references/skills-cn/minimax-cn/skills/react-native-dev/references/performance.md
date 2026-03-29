# 性能参考

诊断和修复 React Native / Expo 应用程序中的性能问题。

## 分析工作流程

在优化之前，先确定实际的瓶颈：

1. **JS 线程** — 打开 React Native DevTools（在 Metro 终端中按 `j`）→ Profiler 选项卡→ 记录交互→ 查找渲染时间较长的组件
2. **本机线程** — iOS：Xcode Instruments（时间分析器）； Android：Android Studio CPU 分析器
3. **测量，不要猜测** - 始终在类似发布的构建中重现问题（`npx expo run:ios --configuration Release`）

## 渲染

### 虚拟列表

切勿在“ScrollView”内渲染大型数据集。使用回收屏幕外视图的虚拟化列表：```tsx
import { FlashList } from "@shopify/flash-list";

function ProductCatalog({ products }: { products: Product[] }) {
  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductRow product={item} />}
      estimatedItemSize={72}
      keyExtractor={(p) => p.sku}
    />
  );
}

const ProductRow = memo(function ProductRow({ product }: { product: Product }) {
  return (
    <View style={rowStyles.container}>
      <Image source={product.thumbnail} style={rowStyles.image} />
      <Text style={rowStyles.title}>{product.name}</Text>
    </View>
  );
});
```要点：
- 使用“memo”包裹列表项，以在道具未更改时跳过重新渲染
- 始终提供 `estimatedItemSize` — FlashList 使用它进行布局估计
- 提取“renderItem”或使用命名组件来保持稳定的引用

### 最小化重新渲染

**按关注点分割状态。** 单个大型状态对象会强制每个订阅者在发生任何更改时重新渲染：```tsx
// Zustand — select only the slice you need
const count = useStore((s) => s.cart.itemCount);

// Jotai — one atom per concern
const cartTotalAtom = atom((get) => {
  const items = get(cartItemsAtom);
  return items.reduce((sum, i) => sum + i.price * i.qty, 0);
});
```**React Compiler** (Expo SDK 54+) 自动记忆组件和挂钩。使其能够消除大多数手动`useMemo`/`useCallback`：```json
// app.json
{ "expo": { "experiments": { "reactCompiler": true } } }
```### 延迟更新

当状态更改触发昂贵的计算（过滤长列表、渲染复杂树）时，请推迟更新，以便键入或滚动保持响应：```tsx
const [search, setSearch] = useState("");
const deferred = useDeferredValue(search);

const results = useMemo(
  () => catalog.filter((p) => p.name.toLowerCase().includes(deferred.toLowerCase())),
  [catalog, deferred],
);
```### Android 上的文本输入

受控的“TextInput”（使用“value”+“onChangeText”）在 Android 上可能会滞后，因为每次击键都会通过 JS 线程往返。对于搜索栏或其他高频输入，更喜欢不受控制的模式：```tsx
const ref = useRef<TextInput>(null);

<TextInput
  ref={ref}
  defaultValue=""
  onEndEditing={(e) => handleSearch(e.nativeEvent.text)}
/>
```## 启动时间（TTI）

### 测量```tsx
import { PerformanceObserver, performance } from "react-native-performance";

performance.mark("nativeLaunch");

export default function App() {
  useEffect(() => {
    performance.measure("TTI", "nativeLaunch");
  }, []);
  // ...
}
```始终测量**冷启动** - 在每次测量之前完全终止应用程序。

### 减少 TTI

- **Android Bundle mmap** - 在`android/gradle.properties`中设置`expo.useLegacyPackaging=false`，以便Hermes内存映射该bundle而不是解压缩它
- **预加载大量路由** — 当用户仍在启动/登录屏幕上时调用 `preloadRouteAsync("/dashboard")` （来自 `expo-router`）
- **延迟加载非关键屏幕** - 深度导航背后的屏幕不需要位于初始包中

## 捆绑包和应用程序大小

### 检查包```bash
npx expo export --platform ios --source-maps --output-dir dist
npx source-map-explorer dist/bundles/ios/*.js
```共同胜利：
- **直接导入** — `import groupBy from "lodash/groupBy"` 而不是 `import { groupBy } from "lodash"`
- **删除无效的 Intl 填充** - Hermes 自 SDK 50 起附带内置的“Intl”支持
- **Tree Shaking** — 通过应用程序配置中的 `"experiments": { "treeShaking": true }` 启用 (SDK 52+)

### 缩小本机二进制文件```properties
# android/gradle.properties
android.enableProguardInReleaseBuilds=true
```检查最终的工件：
- iOS：从 EAS 下载 `.ipa`，解压，检查 `Payload/*.app` 大小
- Android：在 Android Studio 中打开 `.aab`/`.apk` → 构建 → 分析 APK

## 内存

### 防止泄漏

必须清理在 `useEffect` 中获取的每个订阅、侦听器或长期资源：```tsx
useEffect(() => {
  const sub = AppState.addEventListener("change", onAppStateChange);
  return () => sub.remove();
}, []);
```对于 fetch 调用，传递 `AbortSignal` 并在卸载时中止：```tsx
useEffect(() => {
  const ac = new AbortController();
  loadProducts(ac.signal);
  return () => ac.abort();
}, [categoryId]);
```### 本机内存

- 使用 Xcode Memory Graph Debugger (iOS) 或 Android Studio Memory Profiler 进行监控
- 在清理中释放大量本机资源（相机会话、音频播放器）
- 在 Swift/Kotlin 模块中，注意保留周期 - 使用 `[weak self]` / `WeakReference`

## 动画

仅设置 **`变换`** 和 **`不透明度`** 动画。这些属性在 GPU 上合成，不会触发布局重新计算：```tsx
const style = useAnimatedStyle(() => ({
  opacity: withTiming(visible.value ? 1 : 0),
  transform: [{ translateY: withSpring(offset.value) }],
}));
```对“宽度”、“高度”、“边距”、“填充”或“顶部”/“左侧”进行动画处理会强制布局引擎重新测量每一帧——这是丢帧的常见原因。

在 UI 线程上保留手势回调：```tsx
const drag = Gesture.Pan().onUpdate((e) => {
  "worklet";
  translateX.value = e.translationX;
});
```## 本机模块性能

- 更喜欢**异步** Turbo Module 方法 - 同步调用会阻塞 JS 线程
- 在 JS polyfill 上使用本机 SDK 实现（在“crypto-js”上使用“expo-crypto”，在 AsyncStorage 上使用“react-native-mmkv”作为热路径）
- **Google Play (2025+) 需要 Android 16KB 页面对齐**。验证第三方“.so”文件是否以 16KB 对齐方式编译

## 故障排除指南

|症状|去哪里看|可能修复|
|---------|--------------|------------|
|在长列表中滚动卡顿 | JS 线程 — 重新渲染 |虚拟化列表+记忆项目|
|搜索栏中输入滞后 | JS 线程——受控输入 |不受控制的“TextInput”和“defaultValue” |
|冷启动慢|捆绑包大小，同步初始化 | Mmap 捆绑包、预加载路线、惰性屏幕 |
|应用程序二进制文件太大 |原生资源、未使用的库 | R8（Android），分析捆绑，直接导入|
|随着时间的推移记忆力不断增长|效果清理 |从每个 `useEffect` 返回拆卸 |
|断断续续的进入/退出动画 |动画属性 |仅“transform”+“opacity”，使用worklet |
|跨应用程序重新渲染级联 |全球国家形态|原子选择器（Zustand/Jotai），React 编译器 |