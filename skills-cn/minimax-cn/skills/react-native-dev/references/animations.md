# 动画参考

为 Expo/React Native 重新激活了 3 个动画、手势和过渡。

## 核心规则

- **仅对“变换”和“不透明度”进行动画处理** — GPU 合成，无布局重新计算
- 使用“useDerivedValue”计算动画值，而不是内联 JS 表达式
- 在“GestureDetector”中使用“Gesture.Tap”而不是“Pressable”
- 所有 Reanimated 回调都作为 UI 线程上的工作集运行 — 无异步/等待

## 设置```bash
npx expo install react-native-reanimated react-native-gesture-handler
```

```js
// babel.config.js
module.exports = { presets: ["babel-preset-expo"], plugins: ["react-native-reanimated/plugin"] };
```

```tsx
// app/_layout.tsx — wrap root in GestureHandlerRootView
import { GestureHandlerRootView } from "react-native-gesture-handler";
export default function RootLayout() {
  return <GestureHandlerRootView style={{ flex: 1 }}><Stack /></GestureHandlerRootView>;
}
```## 进入/退出动画```tsx
import Animated, {
  FadeIn, FadeOut,
  SlideInRight, SlideOutLeft,
  ZoomIn, ZoomOut,
  BounceIn,
} from "react-native-reanimated";

// Basic
<Animated.View entering={FadeIn} exiting={FadeOut}>
  <Text>Content</Text>
</Animated.View>

// With options
<Animated.View
  entering={FadeIn.duration(300).delay(100)}
  exiting={SlideOutLeft.duration(200)}
/>

// Spring-based
<Animated.View entering={ZoomIn.springify().damping(15)} />
```### 内置预设

|类别 |进入|退出 |
|----------|----------|---------|
|淡出| `淡入`、`淡入上`、`淡入下`、`淡入左`、`淡入右` | `淡出*` |
|幻灯片| `SlideInUp`、`SlideInDown`、`SlideInLeft`、`SlideInRight` | `幻灯片*` |
|放大| “放大”、“向上放大”、“向下放大” | `缩小*` |
|弹跳 | `BounceIn`、`BounceInUp`、`BounceInDown` | `跳出*` |
|翻转| `FlipInXUp`、`FlipInYLeft` | `翻转*` |
|卷| `向左滚动`、`向右滚动` | `RollOut*` |
|拉伸| `StretchInX`、`StretchInY` | `伸展*` |
|风车| `风车在` | '风车出' |
|旋转| `向左旋转` | `旋转输出*` |
|光速| `光速向左` | `LightSpeedOut*` |

## 共享值和 useAnimatedStyle```tsx
import {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  withRepeat,
  withSequence,
  Easing,
} from "react-native-reanimated";

const offset = useSharedValue(0);
const opacity = useSharedValue(1);

const animStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: offset.value }],
  opacity: opacity.value,
}));

// Animate
offset.value = withSpring(100);
opacity.value = withTiming(0, { duration: 300, easing: Easing.out(Easing.quad) });

// Repeat
opacity.value = withRepeat(withTiming(0.3, { duration: 800 }), -1, true);

// Sequence
offset.value = withSequence(
  withTiming(-10, { duration: 100 }),
  withTiming(10, { duration: 100 }),
  withSpring(0),
);

<Animated.View style={animStyle} />
```## 使用派生值```tsx
import { useDerivedValue } from "react-native-reanimated";

const progress = useSharedValue(0); // 0–1
const rotation = useDerivedValue(() => `${progress.value * 360}deg`);
const scale = useDerivedValue(() => 0.5 + progress.value * 0.5);

const animStyle = useAnimatedStyle(() => ({
  transform: [{ rotate: rotation.value }, { scale: scale.value }],
}));
```## 布局动画```tsx
import { Layout, LinearTransition, CurvedTransition } from "react-native-reanimated";

// Item reorder/add/remove animation
<Animated.View layout={LinearTransition}>
  {/* Content that changes size/position */}
</Animated.View>

// Spring layout transition
<Animated.View layout={LinearTransition.springify()}>
```## 手势```tsx
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useSharedValue, useAnimatedStyle, withSpring } from "react-native-reanimated";

// Pan gesture
const offsetX = useSharedValue(0);
const offsetY = useSharedValue(0);

const panGesture = Gesture.Pan()
  .onUpdate((e) => {
    offsetX.value = e.translationX;
    offsetY.value = e.translationY;
  })
  .onEnd(() => {
    offsetX.value = withSpring(0);
    offsetY.value = withSpring(0);
  });

const animStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: offsetX.value }, { translateY: offsetY.value }],
}));

<GestureDetector gesture={panGesture}>
  <Animated.View style={animStyle} />
</GestureDetector>
```

```tsx
// Tap gesture (use instead of Pressable inside GestureDetector)
const tapGesture = Gesture.Tap()
  .numberOfTaps(1)
  .onEnd(() => {
    scale.value = withSequence(withTiming(0.95), withSpring(1));
  });

// Pinch gesture
const baseScale = useSharedValue(1);
const savedScale = useSharedValue(1);

const pinchGesture = Gesture.Pinch()
  .onUpdate((e) => { baseScale.value = savedScale.value * e.scale; })
  .onEnd(() => { savedScale.value = baseScale.value; });

// Composed gestures
const composed = Gesture.Simultaneous(panGesture, pinchGesture);
const exclusive = Gesture.Exclusive(tapGesture, panGesture);
```## 滚动驱动的动画```tsx
import Animated, {
  useAnimatedScrollHandler,
  useSharedValue,
  interpolate,
  Extrapolation,
} from "react-native-reanimated";

const scrollY = useSharedValue(0);
const scrollHandler = useAnimatedScrollHandler((e) => {
  scrollY.value = e.contentOffset.y;
});

// Parallax header
const headerStyle = useAnimatedStyle(() => ({
  transform: [{
    translateY: interpolate(scrollY.value, [0, 200], [0, -100], Extrapolation.CLAMP),
  }],
  opacity: interpolate(scrollY.value, [0, 200], [1, 0], Extrapolation.CLAMP),
}));

<Animated.ScrollView onScroll={scrollHandler} scrollEventThrottle={16}>
  <Animated.View style={headerStyle}>
    <Text>Parallax Header</Text>
  </Animated.View>
</Animated.ScrollView>
```## 缩放过渡（Expo Router，iOS 18+）```tsx
import { Link } from "expo-router";

<Link href="/detail" asChild>
  <Link.AppleZoom>
    <Pressable>
      <Image source={thumbnail} />
    </Pressable>
  </Link.AppleZoom>
</Link>
```## 为状态变化添加动画```tsx
// ✓ Always add entering/exiting for state-driven UI changes
{isVisible && (
  <Animated.View entering={FadeIn.duration(200)} exiting={FadeOut.duration(150)}>
    <Toast message={message} />
  </Animated.View>
)}

// ✓ AnimatedFlatList for list item changes
import Animated from "react-native-reanimated";
const AnimatedFlashList = Animated.createAnimatedComponent(FlashList);
```## 常见错误

|错误 |对|
|--------|--------|
|动画`宽度`/`高度` |动画`变换：scaleX/scaleY` |
| `useAnimatedStyle` 中的内联 JS 数学 |用于计算的“useDerivedValue” |
| `GestureDetector` 内的 `Pressable` | `Gesture.Tap()` |
|工作集中的“异步” |外部运行异步，在回调中更新共享值 |
|工作集中频繁使用“console.log” | `console.log` 可以工作，但会序列化到 JS 线程 — 在热路径中谨慎使用 |