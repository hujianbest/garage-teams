# 图形和动画

iOS 图形和动画指南，涵盖 CAShapeLayer、CAGradientLayer、UIBezierPath 和 Core Animation。

## CAShapeLayer

对于自定义形状、路径和动画：```swift
class CircularProgressView: UIView {
    private let trackLayer = CAShapeLayer()
    private let progressLayer = CAShapeLayer()
    
    var progress: CGFloat = 0 {
        didSet { updateProgress() }
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupLayers()
    }
    
    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupLayers()
    }
    
    private func setupLayers() {
        let center = CGPoint(x: bounds.midX, y: bounds.midY)
        let radius = min(bounds.width, bounds.height) / 2 - 10
        let startAngle = -CGFloat.pi / 2
        let endAngle = startAngle + 2 * CGFloat.pi
        
        let circularPath = UIBezierPath(
            arcCenter: center,
            radius: radius,
            startAngle: startAngle,
            endAngle: endAngle,
            clockwise: true
        )
        
        trackLayer.path = circularPath.cgPath
        trackLayer.strokeColor = UIColor.systemGray5.cgColor
        trackLayer.fillColor = UIColor.clear.cgColor
        trackLayer.lineWidth = 10
        trackLayer.lineCap = .round
        layer.addSublayer(trackLayer)
        
        progressLayer.path = circularPath.cgPath
        progressLayer.strokeColor = UIColor.systemBlue.cgColor
        progressLayer.fillColor = UIColor.clear.cgColor
        progressLayer.lineWidth = 10
        progressLayer.lineCap = .round
        progressLayer.strokeEnd = 0
        layer.addSublayer(progressLayer)
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        setupLayers()
    }
    
    private func updateProgress() {
        progressLayer.strokeEnd = progress
    }
    
    func animateProgress(to value: CGFloat, duration: TimeInterval = 0.5) {
        let animation = CABasicAnimation(keyPath: "strokeEnd")
        animation.fromValue = progressLayer.strokeEnd
        animation.toValue = value
        animation.duration = duration
        animation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
        progressLayer.strokeEnd = value
        progressLayer.add(animation, forKey: "progressAnimation")
    }
}
```## UIBezier路径

### 常见形状```swift
let roundedRect = UIBezierPath(
    roundedRect: bounds,
    cornerRadius: 12
)

let customCorners = UIBezierPath(
    roundedRect: bounds,
    byRoundingCorners: [.topLeft, .topRight],
    cornerRadii: CGSize(width: 16, height: 16)
)

let triangle = UIBezierPath()
triangle.move(to: CGPoint(x: bounds.midX, y: 0))
triangle.addLine(to: CGPoint(x: bounds.maxX, y: bounds.maxY))
triangle.addLine(to: CGPoint(x: 0, y: bounds.maxY))
triangle.close()

let circle = UIBezierPath(
    arcCenter: CGPoint(x: bounds.midX, y: bounds.midY),
    radius: bounds.width / 2,
    startAngle: 0,
    endAngle: .pi * 2,
    clockwise: true
)
```### 自定义路径```swift
let customPath = UIBezierPath()
customPath.move(to: CGPoint(x: 0, y: bounds.height))
customPath.addCurve(
    to: CGPoint(x: bounds.width, y: 0),
    controlPoint1: CGPoint(x: bounds.width * 0.3, y: bounds.height),
    controlPoint2: CGPoint(x: bounds.width * 0.7, y: 0)
)
```## CA渐变层

### 线性渐变按钮```swift
class GradientButton: UIButton {
    private let gradientLayer = CAGradientLayer()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupGradient()
    }
    
    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupGradient()
    }
    
    private func setupGradient() {
        gradientLayer.colors = [
            UIColor.systemBlue.cgColor,
            UIColor.systemPurple.cgColor
        ]
        gradientLayer.startPoint = CGPoint(x: 0, y: 0.5)
        gradientLayer.endPoint = CGPoint(x: 1, y: 0.5)
        gradientLayer.cornerRadius = 12
        layer.insertSublayer(gradientLayer, at: 0)
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        gradientLayer.frame = bounds
    }
}
```### 渐变背景视图```swift
class GradientBackgroundView: UIView {
    private let gradientLayer = CAGradientLayer()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        setupGradient()
    }
    
    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupGradient()
    }
    
    private func setupGradient() {
        gradientLayer.colors = [
            UIColor.systemBackground.cgColor,
            UIColor.secondarySystemBackground.cgColor
        ]
        gradientLayer.locations = [0.0, 1.0]
        gradientLayer.startPoint = CGPoint(x: 0.5, y: 0)
        gradientLayer.endPoint = CGPoint(x: 0.5, y: 1)
        layer.insertSublayer(gradientLayer, at: 0)
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        gradientLayer.frame = bounds
    }
    
    override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
        super.traitCollectionDidChange(previousTraitCollection)
        gradientLayer.colors = [
            UIColor.systemBackground.cgColor,
            UIColor.secondarySystemBackground.cgColor
        ]
    }
}
```### 渐变类型

|类型 |配置|
|------|----------------|
|线性（水平）| `起点: (0, 0.5)`, `终点: (1, 0.5)` |
|线性（垂直）| `起点：(0.5，0)`，`终点：(0.5，1)` |
|对角线| `起点：(0, 0)`，`终点：(1, 1)` |
|径向|使用 `CAGradientLayer.type = .radial` |

## 核心动画

### 基本动画```swift
func animateScale() {
    let animation = CABasicAnimation(keyPath: "transform.scale")
    animation.fromValue = 1.0
    animation.toValue = 1.2
    animation.duration = 0.3
    animation.autoreverses = true
    animation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
    layer.add(animation, forKey: "scaleAnimation")
}

func animatePosition() {
    let animation = CABasicAnimation(keyPath: "position")
    animation.fromValue = layer.position
    animation.toValue = CGPoint(x: 200, y: 200)
    animation.duration = 0.5
    layer.add(animation, forKey: "positionAnimation")
}
```### 关键帧动画```swift
func animateAlongPath() {
    let path = UIBezierPath()
    path.move(to: CGPoint(x: 50, y: 50))
    path.addCurve(
        to: CGPoint(x: 250, y: 250),
        controlPoint1: CGPoint(x: 150, y: 50),
        controlPoint2: CGPoint(x: 50, y: 250)
    )
    
    let animation = CAKeyframeAnimation(keyPath: "position")
    animation.path = path.cgPath
    animation.duration = 2.0
    animation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)
    layer.add(animation, forKey: "pathAnimation")
}
```### 动画组```swift
func animateMultiple() {
    let scaleAnimation = CABasicAnimation(keyPath: "transform.scale")
    scaleAnimation.fromValue = 1.0
    scaleAnimation.toValue = 1.5
    
    let opacityAnimation = CABasicAnimation(keyPath: "opacity")
    opacityAnimation.fromValue = 1.0
    opacityAnimation.toValue = 0.0
    
    let group = CAAnimationGroup()
    group.animations = [scaleAnimation, opacityAnimation]
    group.duration = 0.5
    group.fillMode = .forwards
    group.isRemovedOnCompletion = false
    
    layer.add(group, forKey: "multipleAnimations")
}
```### 春天动画```swift
func springAnimation() {
    let spring = CASpringAnimation(keyPath: "transform.scale")
    spring.fromValue = 0.8
    spring.toValue = 1.0
    spring.damping = 10
    spring.stiffness = 100
    spring.mass = 1
    spring.initialVelocity = 5
    spring.duration = spring.settlingDuration
    layer.add(spring, forKey: "springAnimation")
}
```## UIView 动画

### 基本 UIView 动画```swift
UIView.animate(withDuration: 0.3) {
    self.view.alpha = 1.0
    self.view.transform = .identity
}

UIView.animate(withDuration: 0.3, delay: 0, options: [.curveEaseInOut]) {
    self.cardView.frame.origin.y = 100
} completion: { _ in
    self.didFinishAnimation()
}
```### 春天动画```swift
UIView.animate(
    withDuration: 0.6,
    delay: 0,
    usingSpringWithDamping: 0.7,
    initialSpringVelocity: 0.5,
    options: []
) {
    self.popupView.transform = .identity
}
```### 关键帧动画```swift
UIView.animateKeyframes(withDuration: 1.0, delay: 0) {
    UIView.addKeyframe(withRelativeStartTime: 0, relativeDuration: 0.25) {
        self.view.transform = CGAffineTransform(scaleX: 1.2, y: 1.2)
    }
    UIView.addKeyframe(withRelativeStartTime: 0.25, relativeDuration: 0.25) {
        self.view.transform = CGAffineTransform(rotationAngle: .pi / 4)
    }
    UIView.addKeyframe(withRelativeStartTime: 0.5, relativeDuration: 0.5) {
        self.view.transform = .identity
    }
}
```## 计时函数

|名称 |描述 |
|------|-------------|
| `.线性` |恒速|
| `.easeIn` |慢启动|
| `.easeOut` |慢结束|
| `.easeInEaseOut` |缓慢的开始和结束|
| `.default` |系统默认 |

---

*UIKit、Core Animation 和 Apple 是 Apple Inc. 的商标。*