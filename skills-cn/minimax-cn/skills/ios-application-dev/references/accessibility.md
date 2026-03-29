# 辅助功能

iOS 辅助功能指南涵盖动态类型、语义颜色、VoiceOver 和动作适应。

## 动态类型

### 使用系统字体```swift
private func setupLabels() {
    let titleLabel = UILabel()
    titleLabel.font = .preferredFont(forTextStyle: .headline)
    titleLabel.adjustsFontForContentSizeCategory = true
    
    let bodyLabel = UILabel()
    bodyLabel.font = .preferredFont(forTextStyle: .body)
    bodyLabel.adjustsFontForContentSizeCategory = true
    bodyLabel.numberOfLines = 0
}
```### 自定义字体缩放```swift
extension UIFont {
    static func scaled(_ name: String, size: CGFloat, for style: TextStyle) -> UIFont {
        guard let font = UIFont(name: name, size: size) else {
            return .preferredFont(forTextStyle: style)
        }
        return UIFontMetrics(forTextStyle: style).scaledFont(for: font)
    }
}

let customFont = UIFont.scaled("Avenir-Medium", size: 16, for: .body)
```### 文本样式参考

|风格|默认尺寸 |用途 |
|--------|--------------|--------|
| `.largeTitle` | 34点|屏幕标题 |
| `.title1` | 28点|主标题 |
| `.title2` | 22点|二级标题 |
| `.title3` | 20点|第三级标题 |
| `.headline` | 17pt（半粗体​​）|重要信息 |
| `.body` | 17点|正文 |
| `.callout` | 16点|说明文字|
| `.副标题` | 15分|字幕|
| `.脚注` | 13点|脚注|
| `.caption1` | 12点|标签|
| `.caption2` | 11点|小标签|

### 调整大文本布局```swift
override func traitCollectionDidChange(_ previous: UITraitCollection?) {
    super.traitCollectionDidChange(previous)
    
    let isLargeText = traitCollection.preferredContentSizeCategory.isAccessibilityCategory
    contentStack.axis = isLargeText ? .vertical : .horizontal
    
    if isLargeText {
        iconImageView.snp.remakeConstraints { make in
            make.size.equalTo(64)
        }
    } else {
        iconImageView.snp.remakeConstraints { make in
            make.size.equalTo(44)
        }
    }
}
```## 语义颜色

使用系统语义颜色进行自动暗模式适应：```swift
view.backgroundColor = .systemBackground
containerView.backgroundColor = .secondarySystemBackground
cardView.backgroundColor = .tertiarySystemBackground

titleLabel.textColor = .label
subtitleLabel.textColor = .secondaryLabel
hintLabel.textColor = .tertiaryLabel
placeholderLabel.textColor = .placeholderText

separatorView.backgroundColor = .separator
borderView.layer.borderColor = UIColor.separator.cgColor
```### 系统颜色参考

|颜色 |灯光模式 |深色模式 |用途 |
|--------|------------|------------|--------|
| `.systemBackground` |白色|黑色|主要背景|
| `.secondarySystemBackground` |浅灰色|深灰色|卡片/分组背景|
| `.tertiarySystemBackground` |浅灰色|中灰色|嵌套内容背景|
| `.label` |黑色|白色|主要文本|
| `.secondaryLabel` |灰色|浅灰色|辅助文本 |
| `.tertiaryLabel` |浅灰色|深灰色|辅助文字|

### 自定义颜色适应```swift
extension UIColor {
    static let customAccent = UIColor { traitCollection in
        switch traitCollection.userInterfaceStyle {
        case .dark:
            return UIColor(red: 0.4, green: 0.8, blue: 1.0, alpha: 1.0)
        default:
            return UIColor(red: 0.0, green: 0.5, blue: 0.8, alpha: 1.0)
        }
    }
}
```## 旁白

### 基本标签```swift
let cartButton = UIButton(type: .system)
cartButton.setImage(UIImage(systemName: "cart.badge.plus"), for: .normal)
cartButton.accessibilityLabel = "Add to cart"

let ratingView = UIView()
ratingView.accessibilityLabel = "Rating: 4 out of 5 stars"

let closeButton = UIButton()
closeButton.accessibilityLabel = "Close"
closeButton.accessibilityHint = "Dismisses this dialog"
```### 自定义辅助功能```swift
class ProductCell: UICollectionViewCell {
    override var accessibilityLabel: String? {
        get {
            return "\(product.name), \(product.price), \(product.isAvailable ? "In stock" : "Out of stock")"
        }
        set {}
    }
    
    override var accessibilityTraits: UIAccessibilityTraits {
        get {
            var traits: UIAccessibilityTraits = .button
            if product.isSelected {
                traits.insert(.selected)
            }
            return traits
        }
        set {}
    }
}
```### 辅助功能容器```swift
class CustomContainerView: UIView {
    override var isAccessibilityElement: Bool {
        get { false }
        set {}
    }
    
    override var accessibilityElements: [Any]? {
        get {
            return [titleLabel, actionButton, detailLabel]
        }
        set {}
    }
}
```### 旁白通知```swift
func didLoadContent() {
    UIAccessibility.post(notification: .screenChanged, argument: headerLabel)
}

func didUpdateStatus() {
    UIAccessibility.post(notification: .announcement, argument: "Download complete")
}
```## 减少运动```swift
func animateTransition() {
    let duration: TimeInterval = UIAccessibility.isReduceMotionEnabled ? 0 : 0.3
    UIView.animate(withDuration: duration) {
        self.cardView.alpha = 1
    }
}

func showPopup() {
    if UIAccessibility.isReduceMotionEnabled {
        popupView.alpha = 1
    } else {
        popupView.transform = CGAffineTransform(scaleX: 0.8, y: 0.8)
        popupView.alpha = 0
        UIView.animate(withDuration: 0.3, delay: 0, usingSpringWithDamping: 0.7, initialSpringVelocity: 0) {
            self.popupView.transform = .identity
            self.popupView.alpha = 1
        }
    }
}
```### 观察设置变化```swift
NotificationCenter.default.addObserver(
    self,
    selector: #selector(reduceMotionChanged),
    name: UIAccessibility.reduceMotionStatusDidChangeNotification,
    object: nil
)

@objc func reduceMotionChanged() {
    updateAnimationSettings()
}
```## 辅助功能检查表

### 基本要求
- [ ] 所有图标按钮都有 `accessibilityLabel`
- [ ] 自定义控件具有正确的 `accessibilityTraits`
- [ ] 图像具有“accessibilityLabel”或标记为装饰性
- [ ] 表单有明确的错误消息

### 动态类型
- [ ] 使用 `preferredFont(forTextStyle:)`
- [ ] 设置 `adjustsFontForContentSizeCategory = true`
- [ ] 布局适应可访问性大小
- [ ] 文本不被截断

### 颜色对比
- [ ] 正文对比度 >= 4.5:1
- [ ] 大文本对比度 >= 3:1
- [ ] 信息不能仅通过颜色传达

### 运动
- [ ] 尊重减少运动设置
- [ ] 无闪烁或快速动画
- [ ] 自动播放动画可以暂停

### 互动
- [ ] 触摸目标 >= 44x44pt
- [ ] 手势有替代动作
- [ ] 超时可以延长

---

*UIKit、VoiceOver、Dynamic Type 和 Apple 是 Apple Inc. 的商标。*