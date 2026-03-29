# 原生功能参考

Expo/React Native 的摄像头、位置、权限、触觉、通知和生物识别。

## 权限

所有需要权限的 Expo 模块都会公开一个 `use*Permissions()` 钩子。遵循以下模式：

1. 调用权限钩子获取当前状态和请求函数
2. 检查“status”——如果不是“granted”，请说明理由并调用“requestPermission()”
3. 如果用户拒绝两次，“canAskAgain”将变为“false”——将他们引导至“设置”```tsx
import { useCameraPermissions } from "expo-camera";

const [permission, requestPermission] = useCameraPermissions();

if (!permission?.granted) {
  // Show rationale, then call requestPermission()
}
```|模块|权限挂钩|
|--------|----------------|
| `世博相机` | `useCameraPermissions()` |
| `世博会地点` | `useForegroundPermissions()` / `useBackgroundPermissions()` |
| `世博媒体库` | `usePermissions()` |
| `博览会通知` | `getPermissionsAsync()` / `requestPermissionsAsync()` |
| `世博会联系方式` | `usePermissions()` |

对于没有挂钩的模块，请直接使用 `requestPermissionsAsync()` / `getPermissionsAsync()`。

＃＃ 相机```tsx
import { CameraView, useCameraPermissions } from "expo-camera";

const [permission, requestPermission] = useCameraPermissions();
const cameraRef = useRef<CameraView>(null);

// Capture a photo
const photo = await cameraRef.current?.takePictureAsync();

// Toggle front/back
const [facing, setFacing] = useState<"front" | "back">("back");
```对于没有相机 UI 的简单照片/视频选择，请使用“expo-image-picker”：```tsx
import * as ImagePicker from "expo-image-picker";

const result = await ImagePicker.launchImageLibraryAsync({
  mediaTypes: ["images"],
  allowsEditing: true,
  quality: 0.8,
});
```＃＃ 地点```tsx
import * as Location from "expo-location";

// One-time location
const { status } = await Location.requestForegroundPermissionsAsync();
if (status === "granted") {
  const location = await Location.getCurrentPositionAsync({});
  // location.coords.latitude, location.coords.longitude
}
```对于后台位置跟踪，请请求“requestBackgroundPermissionsAsync()”并注册后台任务。后台位置需要`app.json`中的`location`后台模式：```json
{
  "expo": {
    "ios": { "infoPlist": { "UIBackgroundModes": ["location"] } }
  }
}
```## 触觉```tsx
import * as Haptics from "expo-haptics";

// Light tap feedback (button press)
Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

// Success / error / warning
Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

// Selection change (picker scroll)
Haptics.selectionAsync();
```|风格|何时使用 |
|--------|-------------|
| `ImpactFeedbackStyle.Light` |按钮点击、切换 |
| `ImpactFeedbackStyle.Medium` |拖动快照，重大动作 |
| `ImpactFeedbackStyle.Heavy` |破坏性行为、影响 |
| `NotificationFeedbackType.Success` |任务完成 |
| `NotificationFeedbackType.Warning` |需要注意|
| `NotificationFeedbackType.Error` |行动失败 |
| `selectionAsync()` |选择器/滑块值更改 |

## 通知

### 推送通知（博览会）```tsx
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";

async function registerForPushNotifications() {
  if (!Device.isDevice) return; // Push doesn't work on simulators

  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") return;

  const token = await Notifications.getExpoPushTokenAsync({
    projectId: "your-project-id", // From app.json > extra > eas > projectId
  });
  // Send token.data to your server
}
```### 通知处理程序```tsx
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Listen for received/tapped notifications
const subscription = Notifications.addNotificationReceivedListener(notification => {
  // Notification received while app is foregrounded
});
```## 生物识别```tsx
import * as LocalAuthentication from "expo-local-authentication";

const hasHardware = await LocalAuthentication.hasHardwareAsync();
const isEnrolled = await LocalAuthentication.isEnrolledAsync();

if (hasHardware && isEnrolled) {
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: "Authenticate to continue",
    fallbackLabel: "Use passcode",
  });
  if (result.success) {
    // Authenticated
  }
}
```
