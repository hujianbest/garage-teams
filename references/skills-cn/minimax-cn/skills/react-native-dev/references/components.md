# 组件参考

Expo/React Native 的本机 UI 组件、媒体、视觉效果和存储模式。

## 图片```tsx
import { Image } from "expo-image";

// Always use expo-image — not React Native's built-in Image
<Image
  source={{ uri: "https://example.com/photo.jpg" }}
  style={{ width: 200, height: 200 }}
  contentFit="cover"
  transition={300}
  placeholder={blurhash}
/>
```## 列表```tsx
import { FlashList } from "@shopify/flash-list";
import { memo } from "react";

const Item = memo(({ title }: { title: string }) => (
  <View style={styles.item}><Text>{title}</Text></View>
));

<FlashList
  data={items}
  renderItem={({ item }) => <Item title={item.title} />}
  keyExtractor={(item) => item.id}
  estimatedItemSize={80}
/>
```## 安全区域```tsx
import { useSafeAreaInsets } from "react-native-safe-area-context";

// With ScrollView
<ScrollView contentInsetAdjustmentBehavior="automatic">
  {/* content */}
</ScrollView>

// Manual insets
const insets = useSafeAreaInsets();
<View style={{ paddingBottom: insets.bottom }} />
```## 本机控件 (iOS)```tsx
import { Switch } from "react-native";
import SegmentedControl from "@react-native-segmented-control/segmented-control";

// Switch
<Switch value={enabled} onValueChange={setEnabled} />

// Segmented Control
<SegmentedControl
  values={["Day", "Week", "Month"]}
  selectedIndex={selectedIndex}
  onChange={(e) => setSelectedIndex(e.nativeEvent.selectedSegmentIndex)}
/>
```## 表格（底页）```tsx
// app/modal.tsx
import { Stack } from "expo-router";
<Stack.Screen options={{
  presentation: "formSheet",
  sheetAllowedDetents: [0.5, 1.0],
  sheetGrabberVisible: true,
}} />
```## 视觉效果```tsx
import { BlurView } from "expo-blur";
<BlurView intensity={80} tint="light" style={StyleSheet.absoluteFill} />

// Liquid glass (iOS 26+, New Architecture only)
import { GlassEffect } from "expo-glass-effect";
<GlassEffect style={{ borderRadius: 16, padding: 20 }} />
```＃＃ 搜索```tsx
// Using expo-router search bar (iOS only)
import { useNavigation } from "expo-router";

useEffect(() => {
  navigation.setOptions({
    headerSearchBarOptions: {
      placeholder: "Search...",
      onChangeText: (e) => setQuery(e.nativeEvent.text),
    },
  });
}, [navigation]);
```## 存储

|需要|解决方案 |
|------|----------|
|结构化数据| `expo-sqlite` |
|简单的键值 | `@react-native-async-storage/async-storage` |
|敏感数据 | `expo-secure-store` |

＃＃ 媒体```tsx
import { CameraView, useCameraPermissions } from "expo-camera";
import { useAudioPlayer } from "expo-audio";
import { useVideoPlayer, VideoView } from "expo-video";
import * as ImagePicker from "expo-image-picker";
```
