# 导航模式

iOS 导航模式指南涵盖选项卡导航、导航控制器和模式呈现。

## 基于选项卡的导航

对于具有 3-5 个主要部分的应用程序：```swift
class AppTabBarController: UITabBarController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let homeNav = UINavigationController(rootViewController: HomeVC())
        homeNav.tabBarItem = UITabBarItem(
            title: "Home",
            image: UIImage(systemName: "house"),
            selectedImage: UIImage(systemName: "house.fill")
        )
        
        let searchNav = UINavigationController(rootViewController: SearchVC())
        searchNav.tabBarItem = UITabBarItem(
            title: "Search",
            image: UIImage(systemName: "magnifyingglass"),
            tag: 1
        )
        
        let profileNav = UINavigationController(rootViewController: ProfileVC())
        profileNav.tabBarItem = UITabBarItem(
            title: "Profile",
            image: UIImage(systemName: "person"),
            selectedImage: UIImage(systemName: "person.fill")
        )
        
        viewControllers = [homeNav, searchNav, profileNav]
    }
}
```### 标签栏最佳实践

|原理|描述 |
|------------|-------------|
|限制计数 |最多 5 个选项卡，使用“更多”进行附加 |
|始终可见 |标签栏在所有导航级别均保持可见 |
|国家保存|切换选项卡时保留导航状态 |
|图标选择|使用SF符号，提供选中/未选中状态 |

## 导航控制器

对根视图使用大标题：```swift
class ListViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Items"
        navigationController?.navigationBar.prefersLargeTitles = true
        navigationItem.largeTitleDisplayMode = .always
    }
    
    func pushDetail(_ item: Item) {
        let detail = DetailViewController(item: item)
        detail.navigationItem.largeTitleDisplayMode = .never
        navigationController?.pushViewController(detail, animated: true)
    }
}
```### 导航栏配置```swift
class CustomNavigationController: UINavigationController {
    override func viewDidLoad() {
        super.viewDidLoad()
        
        let appearance = UINavigationBarAppearance()
        appearance.configureWithDefaultBackground()
        
        navigationBar.standardAppearance = appearance
        navigationBar.scrollEdgeAppearance = appearance
        navigationBar.compactAppearance = appearance
    }
}
```### 导航栏按钮```swift
override func viewDidLoad() {
    super.viewDidLoad()
    
    navigationItem.rightBarButtonItem = UIBarButtonItem(
        image: UIImage(systemName: "plus"),
        style: .plain,
        target: self,
        action: #selector(addItem)
    )
    
    navigationItem.rightBarButtonItems = [
        UIBarButtonItem(systemItem: .add, primaryAction: UIAction { _ in }),
        UIBarButtonItem(systemItem: .edit, primaryAction: UIAction { _ in })
    ]
}
```## 模态表示

### 表格演示```swift
func presentEditor() {
    let editorVC = EditorViewController()
    let nav = UINavigationController(rootViewController: editorVC)
    
    editorVC.navigationItem.leftBarButtonItem = UIBarButtonItem(
        systemItem: .cancel, target: self, action: #selector(dismissEditor)
    )
    editorVC.navigationItem.rightBarButtonItem = UIBarButtonItem(
        systemItem: .done, target: self, action: #selector(saveAndDismiss)
    )
    
    if let sheet = nav.sheetPresentationController {
        sheet.detents = [.medium(), .large()]
        sheet.prefersGrabberVisible = true
        sheet.prefersScrollingExpandsWhenScrolledToEdge = false
    }
    
    present(nav, animated: true)
}
```### 自定义制动器（iOS 16+）```swift
if let sheet = nav.sheetPresentationController {
    let customDetent = UISheetPresentationController.Detent.custom { context in
        return context.maximumDetentValue * 0.4
    }
    sheet.detents = [customDetent, .large()]
}
```### 全屏演示```swift
func presentFullScreen() {
    let vc = FullScreenViewController()
    vc.modalPresentationStyle = .fullScreen
    vc.modalTransitionStyle = .coverVertical
    present(vc, animated: true)
}
```## 演示风格

|风格|用途 |
|--------|--------|
| `.自动` |系统默认（通常是sheet）|
| `.pageSheet` |卡片式，父视图可见 |
| `.全屏` |全面屏封面|
| `.overFullScreen` |全屏透明背景|
| `.popover` | iPad 弹出窗口 |

## 导航最佳实践

1. **后退手势** - 确保边缘向后滑动始终有效
2. **状态恢复** - 使用`UIStateRestoring`保存导航堆栈
3. **深度限制** - 避免超过 4-5 个导航级别
4. **取消按钮** - 模态视图必须提供取消选项
5. **保存确认** - 显示未保存更改的确认对话框

---

*UIKit、SF Symbols 和 Apple 是 Apple Inc. 的商标。*