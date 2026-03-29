# 平台整合

适用于 iOS、Android、Web 和桌面的 Flutter 平台特定实现。

## 平台检测```dart
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

bool get isIOS => !kIsWeb && Platform.isIOS;
bool get isAndroid => !kIsWeb && Platform.isAndroid;
bool get isWeb => kIsWeb;
bool get isDesktop => !kIsWeb && (Platform.isMacOS || Platform.isWindows || Platform.isLinux);
bool get isMobile => !kIsWeb && (Platform.isIOS || Platform.isAndroid);
```## 自适应小部件

### 平台感知组件```dart
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

class AdaptiveButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const AdaptiveButton({
    super.key,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    if (Platform.isIOS) {
      return CupertinoButton.filled(
        onPressed: onPressed,
        child: Text(label),
      );
    }
    return ElevatedButton(
      onPressed: onPressed,
      child: Text(label),
    );
  }
}
```### 自适应对话框```dart
Future<bool?> showAdaptiveConfirmDialog(
  BuildContext context, {
  required String title,
  required String content,
}) async {
  if (Platform.isIOS) {
    return showCupertinoDialog<bool>(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          CupertinoDialogAction(
            isDestructiveAction: true,
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
          CupertinoDialogAction(
            isDefaultAction: true,
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }

  return showDialog<bool>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(title),
      content: Text(content),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, true),
          child: const Text('Delete'),
        ),
      ],
    ),
  );
}
```### 自适应脚手架```dart
class AdaptiveScaffold extends StatelessWidget {
  final String title;
  final Widget body;
  final List<Widget>? actions;

  const AdaptiveScaffold({
    super.key,
    required this.title,
    required this.body,
    this.actions,
  });

  @override
  Widget build(BuildContext context) {
    if (Platform.isIOS) {
      return CupertinoPageScaffold(
        navigationBar: CupertinoNavigationBar(
          middle: Text(title),
          trailing: actions != null
              ? Row(mainAxisSize: MainAxisSize.min, children: actions!)
              : null,
        ),
        child: SafeArea(child: body),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(title), actions: actions),
      body: body,
    );
  }
}
```## 平台渠道

### 方法通道（Dart 侧）```dart
import 'package:flutter/services.dart';

class NativeBridge {
  static const _channel = MethodChannel('com.example.app/native');

  static Future<String> getPlatformVersion() async {
    final version = await _channel.invokeMethod<String>('getPlatformVersion');
    return version ?? 'Unknown';
  }

  static Future<void> triggerHaptic() async {
    await _channel.invokeMethod('triggerHaptic');
  }

  static Future<Map<String, dynamic>> getDeviceInfo() async {
    final result = await _channel.invokeMethod<Map>('getDeviceInfo');
    return Map<String, dynamic>.from(result ?? {});
  }
}
```### iOS 实现（Swift）```swift
// ios/Runner/AppDelegate.swift
import Flutter
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate {
    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        let controller = window?.rootViewController as! FlutterViewController
        let channel = FlutterMethodChannel(
            name: "com.example.app/native",
            binaryMessenger: controller.binaryMessenger
        )
        
        channel.setMethodCallHandler { (call, result) in
            switch call.method {
            case "getPlatformVersion":
                result("iOS " + UIDevice.current.systemVersion)
            case "triggerHaptic":
                let generator = UIImpactFeedbackGenerator(style: .medium)
                generator.impactOccurred()
                result(nil)
            case "getDeviceInfo":
                result([
                    "model": UIDevice.current.model,
                    "name": UIDevice.current.name,
                    "systemVersion": UIDevice.current.systemVersion
                ])
            default:
                result(FlutterMethodNotImplemented)
            }
        }
        
        GeneratedPluginRegistrant.register(with: self)
        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }
}
```### Android 实现（Kotlin）```kotlin
// android/app/src/main/kotlin/.../MainActivity.kt
package com.example.app

import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.content.Context
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.example.app/native"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "getPlatformVersion" -> {
                        result.success("Android ${Build.VERSION.RELEASE}")
                    }
                    "triggerHaptic" -> {
                        val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            vibrator.vibrate(
                                VibrationEffect.createOneShot(50, VibrationEffect.DEFAULT_AMPLITUDE)
                            )
                        } else {
                            @Suppress("DEPRECATION")
                            vibrator.vibrate(50)
                        }
                        result.success(null)
                    }
                    "getDeviceInfo" -> {
                        result.success(mapOf(
                            "model" to Build.MODEL,
                            "manufacturer" to Build.MANUFACTURER,
                            "version" to Build.VERSION.RELEASE
                        ))
                    }
                    else -> result.notImplemented()
                }
            }
    }
}
```## iOS 特定配置

### Info.plist 权限```xml
<!-- ios/Runner/Info.plist -->
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to take photos</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs photo library access to save images</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>This app needs location access to show nearby places</string>

<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for voice recording</string>
```### iOS 应用程序图标和启动屏幕```
ios/Runner/Assets.xcassets/
├── AppIcon.appiconset/
│   ├── Contents.json
│   └── Icon-App-*.png
└── LaunchImage.imageset/
    ├── Contents.json
    └── LaunchImage*.png
```## Android 特定配置

### AndroidManifest.xml 权限```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.CAMERA"/>
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
    
    <application
        android:label="My App"
        android:icon="@mipmap/ic_launcher">
        <!-- ... -->
    </application>
</manifest>
```### 构建 Gradle 配置```groovy
// android/app/build.gradle
android {
    compileSdkVersion 34
    
    defaultConfig {
        minSdkVersion 21
        targetSdkVersion 34
        multiDexEnabled true
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```## Web 特定的

### 有条件导入```dart
// lib/services/storage_service.dart
export 'storage_service_stub.dart'
    if (dart.library.io) 'storage_service_native.dart'
    if (dart.library.html) 'storage_service_web.dart';
```

```dart
// lib/services/storage_service_web.dart
import 'dart:html' as html;

class StorageService {
  void save(String key, String value) {
    html.window.localStorage[key] = value;
  }
  
  String? load(String key) {
    return html.window.localStorage[key];
  }
}
```### 网页索引配置```html
<!-- web/index.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My App</title>
  <link rel="manifest" href="manifest.json">
  <link rel="icon" type="image/png" href="favicon.png"/>
</head>
<body>
  <script src="flutter_bootstrap.js" async></script>
</body>
</html>
```## 特定于平台的样式```dart
ThemeData get theme {
  final baseTheme = ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
    useMaterial3: true,
  );

  if (Platform.isIOS) {
    return baseTheme.copyWith(
      // iOS-style page transitions
      pageTransitionsTheme: const PageTransitionsTheme(
        builders: {
          TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
        },
      ),
    );
  }

  return baseTheme;
}
```## 平台参考

|特色| iOS |安卓 |网页 |
|--------|-----|---------|-----|
|导航 |库比蒂诺风格|材质风格|基于 URL |
|触觉 | UI反馈生成器 |振动器|不可用 |
|存储| NSUserDefaults | NS用户默认值共享首选项 |本地存储|
|深层链接 |通用链接|应用程序链接 | URL路由|
|通知 | APN |流式细胞术|网页推送 |

---

*Flutter、iOS、Android 及其各自的徽标是 Google LLC 和 Apple Inc. 的商标。*