# 系统集成

iOS 系统集成指南，涵盖权限、位置、共享、应用程序生命周期和触觉反馈。

## 权限请求

根据上下文请求权限，而不是在启动时请求权限：```swift
import AVFoundation

@objc func openCamera() {
    AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
        DispatchQueue.main.async {
            if granted {
                self?.showCameraInterface()
            } else {
                self?.showPermissionDeniedAlert()
            }
        }
    }
}
```### 照片库```swift
import Photos

func requestPhotoAccess() {
    PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
        DispatchQueue.main.async {
            switch status {
            case .authorized, .limited:
                self.showPhotoPicker()
            case .denied, .restricted:
                self.showSettingsAlert()
            default:
                break
            }
        }
    }
}
```＃＃＃ 麦克风```swift
func requestMicrophoneAccess() {
    AVAudioSession.sharedInstance().requestRecordPermission { granted in
        DispatchQueue.main.async {
            if granted {
                self.startRecording()
            }
        }
    }
}
```### 通知```swift
import UserNotifications

func requestNotificationPermission() {
    UNUserNotificationCenter.current().requestAuthorization(
        options: [.alert, .badge, .sound]
    ) { granted, error in
        DispatchQueue.main.async {
            if granted {
                self.registerForRemoteNotifications()
            }
        }
    }
}
```## 位置按钮

对于没有永久权限的一次性位置访问：```swift
import CoreLocationUI

class StoreFinderVC: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let locationBtn = CLLocationButton()
        locationBtn.icon = .arrowFilled
        locationBtn.label = .currentLocation
        locationBtn.cornerRadius = 20
        locationBtn.addTarget(self, action: #selector(findNearby), for: .touchUpInside)
        
        view.addSubview(locationBtn)
        locationBtn.snp.makeConstraints { make in
            make.centerX.equalToSuperview()
            make.bottom.equalTo(view.safeAreaLayoutGuide).offset(-24)
        }
    }
}
```### 核心位置```swift
import CoreLocation

class LocationManager: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    
    func requestLocation() {
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.requestWhenInUseAuthorization()
    }
    
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            manager.requestLocation()
        case .denied:
            showLocationDeniedAlert()
        default:
            break
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        handleLocation(location)
    }
}
```## 分享表```swift
@objc func shareContent() {
    let items: [Any] = [contentURL, contentImage].compactMap { $0 }
    let activityVC = UIActivityViewController(activityItems: items, applicationActivities: nil)
    
    if let popover = activityVC.popoverPresentationController {
        popover.sourceView = shareButton
        popover.sourceRect = shareButton.bounds
    }
    
    present(activityVC, animated: true)
}
```### 自定义共享项目```swift
class ShareItem: NSObject, UIActivityItemSource {
    let title: String
    let url: URL
    
    init(title: String, url: URL) {
        self.title = title
        self.url = url
    }
    
    func activityViewControllerPlaceholderItem(_ activityViewController: UIActivityViewController) -> Any {
        return url
    }
    
    func activityViewController(_ activityViewController: UIActivityViewController, itemForActivityType activityType: UIActivity.ActivityType?) -> Any? {
        return url
    }
    
    func activityViewController(_ activityViewController: UIActivityViewController, subjectForActivityType activityType: UIActivity.ActivityType?) -> String {
        return title
    }
}
```### 不包括活动```swift
let activityVC = UIActivityViewController(activityItems: items, applicationActivities: nil)
activityVC.excludedActivityTypes = [
    .addToReadingList,
    .assignToContact,
    .print
]
```## 应用程序生命周期```swift
class PlayerViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        NotificationCenter.default.addObserver(
            self, selector: #selector(onBackground),
            name: UIApplication.didEnterBackgroundNotification, object: nil
        )
        NotificationCenter.default.addObserver(
            self, selector: #selector(onForeground),
            name: UIApplication.willEnterForegroundNotification, object: nil
        )
        NotificationCenter.default.addObserver(
            self, selector: #selector(onTerminate),
            name: UIApplication.willTerminateNotification, object: nil
        )
    }
    
    @objc private func onBackground() { 
        saveState()
        pausePlayback()
    }
    
    @objc private func onForeground() { 
        restoreState()
        resumePlayback()
    }
    
    @objc private func onTerminate() {
        saveState()
    }
}
```### 场景生命周期（iOS 13+）```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    func sceneDidBecomeActive(_ scene: UIScene) {
        // Resume tasks
    }
    
    func sceneWillResignActive(_ scene: UIScene) {
        // Pause tasks
    }
    
    func sceneDidEnterBackground(_ scene: UIScene) {
        // Save state
    }
    
    func sceneWillEnterForeground(_ scene: UIScene) {
        // Prepare UI
    }
}
```### 国家保护```swift
class ViewController: UIViewController {
    override func encodeRestorableState(with coder: NSCoder) {
        super.encodeRestorableState(with: coder)
        coder.encode(currentItemID, forKey: "currentItemID")
    }
    
    override func decodeRestorableState(with coder: NSCoder) {
        super.decodeRestorableState(with: coder)
        if let itemID = coder.decodeObject(forKey: "currentItemID") as? String {
            loadItem(itemID)
        }
    }
}
```## 触觉反馈```swift
func onTaskComplete() {
    UINotificationFeedbackGenerator().notificationOccurred(.success)
}

func onError() {
    UINotificationFeedbackGenerator().notificationOccurred(.error)
}

func onWarning() {
    UINotificationFeedbackGenerator().notificationOccurred(.warning)
}

func onSelection() {
    UISelectionFeedbackGenerator().selectionChanged()
}

func onImpact() {
    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
}
```### 冲击风格

|风格|用途 |
|--------|--------|
| `.light` |微妙的反馈，微小的 UI 变化 |
| `.medium` |标准反馈，按钮按下|
| `.heavy` |强烈反馈，重大行动|
| `.软` |温和反馈，背景变化|
| `.刚性` |尖锐的反馈，碰撞|

### 准备好的反馈

对于时间关键的触觉，提前准备发电机：```swift
class DraggableView: UIView {
    private let impactGenerator = UIImpactFeedbackGenerator(style: .medium)
    
    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        super.touchesBegan(touches, with: event)
        impactGenerator.prepare()
    }
    
    func didSnapToPosition() {
        impactGenerator.impactOccurred()
    }
}
```## 深层链接

### URL方案```swift
// In AppDelegate or SceneDelegate
func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
    guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else {
        return false
    }
    
    switch components.host {
    case "item":
        if let itemID = components.queryItems?.first(where: { $0.name == "id" })?.value {
            navigateToItem(itemID)
            return true
        }
    default:
        break
    }
    
    return false
}
```### 通用链接```swift
func application(_ application: UIApplication, continue userActivity: NSUserActivity, restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void) -> Bool {
    guard userActivity.activityType == NSUserActivityTypeBrowsingWeb,
          let url = userActivity.webpageURL else {
        return false
    }
    
    return handleUniversalLink(url)
}
```## 后台任务```swift
import BackgroundTasks

func registerBackgroundTasks() {
    BGTaskScheduler.shared.register(
        forTaskWithIdentifier: "com.app.refresh",
        using: nil
    ) { task in
        self.handleAppRefresh(task: task as! BGAppRefreshTask)
    }
}

func scheduleAppRefresh() {
    let request = BGAppRefreshTaskRequest(identifier: "com.app.refresh")
    request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
    
    do {
        try BGTaskScheduler.shared.submit(request)
    } catch {
        print("Could not schedule app refresh: \(error)")
    }
}

func handleAppRefresh(task: BGAppRefreshTask) {
    scheduleAppRefresh()
    
    let operation = RefreshOperation()
    
    task.expirationHandler = {
        operation.cancel()
    }
    
    operation.completionBlock = {
        task.setTaskCompleted(success: !operation.isCancelled)
    }
    
    OperationQueue.main.addOperation(operation)
}
```---

*UIKit、Core Location 和 Apple 是 Apple Inc. 的商标。*