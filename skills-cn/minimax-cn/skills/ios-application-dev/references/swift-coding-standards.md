# Swift 编码标准

遵循 Apple 指南和现代 Swift 约定编写干净、安全且惯用的 Swift 代码的最佳实践。

---

## 1. 选项和安全

**影响：** 严重

Swift 的可选系统通过编译时安全性消除了空指针异常。

### 1.1 使用 if let 安全展开```swift
if let name = optionalName {
    print("Hello, \(name)")
}

// Multiple bindings
if let name = userName, let age = userAge, age >= 18 {
    print("\(name) is an adult")
}
```### 1.2 提早退出的防护

当不满足先决条件时，使用“guard”提前退出：```swift
func processUser(_ user: User?) {
    guard let user = user else { return }
    guard !user.name.isEmpty else { return }
    print(user.name)
}
```### 1.3 默认值的零合并```swift
let displayName = name ?? "Anonymous"
let count = items?.count ?? 0
```### 1.4 可选链```swift
let count = user?.profile?.posts?.count
let uppercased = optionalString?.uppercased()
```### 1.5 可选地图/flatMap```swift
let uppercasedName = userName.map { $0.uppercased() }
let userID = userIDString.flatMap { Int($0) }
```### 1.6 切勿强行打开包装

避免“！”强制展开。使用安全的替代方案：

|而不是 |使用|
|------------|-----|
| `价值！` | `如果让值=值{}` |
| `数组[0]`（不安全）| `数组.first` |
| `字典[“键”]！` | `字典["key"，默认值：defaultValue]` |

---

## 2. 命名约定

**影响：** 高

### 2.1 类型：PascalCase```swift
class UserProfileViewController { }
struct NetworkRequest { }
protocol DataSource { }
enum LoadingState { }
```### 2.2 变量和函数：驼峰命名法```swift
var userName: String
let maximumRetryCount = 3
func fetchUserProfile() { }
```### 2.3 布尔命名

使用“is”、“has”、“should”、“can”前缀：```swift
var isLoading: Bool
var hasCompletedOnboarding: Bool
var shouldShowAlert: Bool
var canEditProfile: Bool
```### 2.4 函数命名

使用动词短语，像自然英语一样阅读：```swift
// Good - clear actions
func fetchUsers() async throws -> [User]
func remove(_ item: Item, at index: Int)
func makeIterator() -> Iterator

// Avoid - unclear or redundant
func getUsersData() // "get" is redundant
func doRemove() // vague
```### 2.5 参数标签

当明显时可以省略第一个参数标签：```swift
func insert(_ element: Element, at index: Int)
func move(from source: Int, to destination: Int)
```---

## 3. 面向协议的设计

**影响：** 高

Swift 更喜欢通过协议进行组合而不是继承。

### 3.1 通过协议定义能力```swift
protocol DataStore {
    func save<T: Codable>(_ item: T, key: String) throws
    func load<T: Codable>(key: String) throws -> T?
}

protocol Drawable {
    var color: Color { get set }
    func draw()
}
```### 3.2 默认行为的协议扩展```swift
extension Drawable {
    func draw() {
        print("Drawing with \(color)")
    }
}

extension Collection {
    func chunked(into size: Int) -> [[Element]] {
        guard size > 0 else { return [] }

        var result: [[Element]] = []
        var i = startIndex

        while i != endIndex {
            let j = index(i, offsetBy: size, limitedBy: endIndex) ?? endIndex
            result.append(Array(self[i..<j]))
            i = j
        }

        return result
    }
}
```### 3.3 关联类型以实现灵活性```swift
protocol Repository {
    associatedtype Item
    func fetchAll() async throws -> [Item]
    func save(_ item: Item) async throws
}

class UserRepository: Repository {
    typealias Item = User
    
    func fetchAll() async throws -> [User] { /* ... */ }
    func save(_ item: User) async throws { /* ... */ }
}
```### 3.4 协议组成```swift
protocol Named { var name: String { get } }
protocol Aged { var age: Int { get } }

func greet(_ person: Named & Aged) {
    print("Hello, \(person.name), age \(person.age)")
}
```---

## 4. 值类型与引用类型

**影响：** 高

### 4.1 首选结构（值类型）

使用结构体进行简单数据模型、独立副本：```swift
struct User {
    var name: String
    var email: String
}

struct Point {
    var x: Double
    var y: Double
}
```### 4.2 需要时使用类

当身份、共享所有权或引用语义很重要时，请使用类。
更喜欢在并发任务之间共享可变状态的参与者：```swift
class NetworkManager {
    static let shared = NetworkManager()
    private init() { }
}

class FileHandle {
    // Wrapping system resource
}
```### 4.3 有限状态的枚举```swift
enum LoadingState {
    case idle
    case loading
    case success(Data)
    case failure(Error)
}

enum Result<Success, Failure: Error> {
    case success(Success)
    case failure(Failure)
}
```|类型 |使用时间 |
|------|----------|
| `结构` |数据模型、坐标、独立值|
| `类` |共享状态、身份很重要、需要继承 |
| `枚举` |有限选项集、状态机 |

---

## 5. 使用 ARC 进行内存管理

**影响：** 严重

### 5.1 用弱打破保留周期```swift
class Apartment {
    weak var tenant: Person?
}

class Person {
    var apartment: Apartment?
}
```### 5.2 关闭捕获列表

有意使用捕获列表以避免循环引用。
根据生命周期保证选择“弱”或“无主”：```swift
// Weak capture for optional self
onComplete = { [weak self] in
    self?.processResult()
}

// Capture specific values
let id = user.id
fetchData { [id] result in
    print("Fetched for \(id)")
}
```### 5.3 保证终身无主

当引用在对象生命周期内永远不应该为 nil 时使用：```swift
class CreditCard {
    unowned let customer: Customer
    
    init(customer: Customer) {
        self.customer = customer
    }
}
```|关键词 |使用时间 |
|---------|----------|
| `弱` |引用可能会变成nil |
| `无主` |保证参考文献能够长久保存 |
|无 |需要强大的所有权|

---

## 6. 错误处理

**影响：** 高

### 6.1 定义类型错误```swift
enum NetworkError: Error {
    case invalidURL
    case noConnection
    case serverError(statusCode: Int)
    case decodingFailed(underlying: Error)
}

enum ValidationError: LocalizedError {
    case emptyField(name: String)
    case invalidFormat(field: String, expected: String)
    
    var errorDescription: String? {
        switch self {
        case .emptyField(let name):
            return "\(name) cannot be empty"
        case .invalidFormat(let field, let expected):
            return "\(field) must be \(expected)"
        }
    }
}
```### 6.2 投掷函数```swift
func fetchUser(id: Int) throws -> User {
    guard let url = URL(string: "https://api.example.com/users/\(id)") else {
        throw NetworkError.invalidURL
    }
    // ... implementation
}
```### 6.3 Do-Catch 处理```swift
do {
    let user = try fetchUser(id: 123)
    print(user.name)
} catch NetworkError.serverError(let code) {
    print("Server error: \(code)")
} catch NetworkError.noConnection {
    print("Check your internet connection")
} catch {
    print("Unknown error: \(error)")
}
```### 6.4 试试？并尝试！```swift
// try? returns optional (nil on error)
let user = try? fetchUser(id: 123)

// try! crashes on error - use only when failure is programmer error
let config = try! loadBundledConfig()
```### 6.5 重掷```swift
func perform<T>(_ operation: () throws -> T) rethrows -> T {
    return try operation()
}
```---

## 7. 现代并发（异步/等待）

**影响：** 严重

使用参与者隔离和“可发送”来防止跨并发域的数据竞争。

### 7.1 异步函数```swift
func fetchUser(id: Int) async throws -> User {
    guard let url = URL(string: "https://api.example.com/users/\(id)") else {
        throw NetworkError.invalidURL
    }
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Calling async functions
Task {
    do {
        let user = try await fetchUser(id: 123)
        print(user.name)
    } catch {
        print("Failed: \(error)")
    }
}
```### 7.2 使用任务组并行执行```swift
func fetchAllUsers(ids: [Int]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask {
                try await fetchUser(id: id)
            }
        }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}
```### 7.3 用于并发绑定的 async let```swift
async let user = fetchUser(id: 1)
async let posts = fetchPosts(userId: 1)
async let followers = fetchFollowers(userId: 1)

let profile = try await ProfileData(
    user: user,
    posts: posts,
    followers: followers
)
```### 7.4 线程安全状态的 Actor```swift
actor BankAccount {
    private var balance: Double = 0
    
    func deposit(_ amount: Double) {
        balance += amount
    }
    
    func withdraw(_ amount: Double) throws {
        guard balance >= amount else {
            throw BankError.insufficientFunds
        }
        balance -= amount
    }
    
    func getBalance() -> Double {
        balance
    }
}

// Usage
let account = BankAccount()
await account.deposit(100)
let balance = await account.getBalance()
```### 7.5 MainActor UI 更新```swift
@MainActor
class ViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var users: [User] = []
    
    func loadUsers() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            users = try await fetchUsers()
        } catch {
            // Handle error
        }
    }
}
```### 7.6 任务取消```swift
func fetchWithTimeout() async throws -> Data {
    try await withThrowingTaskGroup(of: Data.self) { group in
        group.addTask {
            try await fetchData()
        }
        group.addTask {
            try await Task.sleep(for: .seconds(10))
            throw TimeoutError()
        }
        
        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}

// Check for cancellation
func longOperation() async throws {
    for item in items {
        try Task.checkCancellation()
        await process(item)
    }
}
```---

## 8. 访问控制

**影响：** 中

### 8.1 访问级别

|水平|范围 |
|--------|--------|
| `私人` |仅附上声明 |
| `文件私有` |整个源文件|
| `内部` |模块（默认）|
| `公共` |其他模块可以访问|
| `打开` |其他模块可以子类化/覆盖 |

### 8.2 最佳实践```swift
public class UserService {
    // Public API
    public func fetchUser(id: Int) async throws -> User { }
    
    // Internal helper
    func buildRequest(for id: Int) -> URLRequest { }
    
    // Private implementation detail
    private let session: URLSession
    private var cache: [Int: User] = [:]
}
```### 8.3 私人二传手```swift
public struct Counter {
    public private(set) var count = 0
    
    public mutating func increment() {
        count += 1
    }
}
```---

## 9. 泛型和类型约束

**影响：** 中

### 9.1 泛型函数```swift
func swapValues<T>(_ a: inout T, _ b: inout T) {
    let temp = a
    a = b
    b = temp
}
```### 9.2 类型约束```swift
func findIndex<T: Equatable>(of value: T, in array: [T]) -> Int? {
    array.firstIndex(of: value)
}

func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
    try JSONDecoder().decode(type, from: data)
}
```### 9.3 Where 子句```swift
func allMatch<C: Collection>(_ collection: C, predicate: (C.Element) -> Bool) -> Bool
    where C.Element: Equatable {
    collection.allSatisfy(predicate)
}

extension Array where Element: Numeric {
    func sum() -> Element {
        reduce(0, +)
    }
}
```### 9.4 不透明类型（一些）```swift
func makeCollection() -> some Collection {
    [1, 2, 3]
}

var body: some View {
    Text("Hello")
}
```---

## 10. 属性包装器

**影响：** 中

### 10.1 通用 SwiftUI 属性包装器

|包装|使用案例|
|---------|----------|
| `@State` |查看本地可变状态 |
| `@Binding` |与父状态的双向连接 |
| `@StateObject` |视图拥有的可观察对象 |
| `@ObservedObject` |传入的可观察对象 |
| `@EnvironmentObject` |来自祖先的共享对象 |
| `@Environment` |系统环境值|
| `@已发布` |类中的可观察属性 |

### 10.2 自定义属性包装器```swift
@propertyWrapper
struct Clamped<Value: Comparable> {
    private var value: Value
    let range: ClosedRange<Value>
    
    var wrappedValue: Value {
        get { value }
        set { value = min(max(newValue, range.lowerBound), range.upperBound) }
    }
    
    init(wrappedValue: Value, _ range: ClosedRange<Value>) {
        self.range = range
        self.value = min(max(wrappedValue, range.lowerBound), range.upperBound)
    }
}

struct Settings {
    @Clamped(0...100) var volume: Int = 50
}
```---

## 快速参考

### 选项```swift
if let x = optional { }      // Safe unwrap
guard let x = optional else { return }  // Early exit
let x = optional ?? default  // Default value
optional?.method()           // Optional chaining
optional.map { transform($0) }  // Transform if present
```### 常见模式```swift
// Defer for cleanup
func process() {
    let file = openFile()
    defer { closeFile(file) }
    // ... work with file
}

// Lazy initialization
lazy var expensive: ExpensiveObject = {
    ExpensiveObject()
}()

// Type inference
let numbers = [1, 2, 3]  // [Int]
let doubled = numbers.map { $0 * 2 }  // [Int]
```### 闭包语法```swift
// Full syntax
let sorted = names.sorted(by: { (s1: String, s2: String) -> Bool in
    return s1 < s2
})

// Shortened
let sorted = names.sorted { $0 < $1 }

// Trailing closure
UIView.animate(withDuration: 0.3) {
    view.alpha = 0
}
```---

## 清单

### 安全
- [ ] 除 IB 插座和已知安全的情况外，不得强行打开包装 (`!`)
- [ ] 所有选项均使用 `if let`、`guard let` 或 `??` 处理
- [ ] 数据模型中没有隐式展开的选项 (`!`)

### 内存
- [ ] 转义闭包有意捕获 `self`；在需要时使用“[weak self]”或“[unowned self]”来避免循环引用
- [ ] 委托属性是“弱”
- [ ] 对象之间没有循环保留

### 并发
- [ ] 使用异步函数代替完成处理程序
- [ ] 跨并发域共享的可变状态是隔离的，通常与参与者隔离
- [ ] 跨并发域的类型在适当的时候使用 `Sendable`
- [ ] `@MainActor` 上的 UI 更新
- [ ] 在长时间操作中检查任务取消

### 访问控制
- [ ] `private` 用于实现细节
- [ ] `public` API 是最小化且有意为之的
- [ ] 没有不必要的“内部”暴露

### 命名
- [ ] 类型使用 PascalCase
- [ ] 函数和变量使用驼峰命名法
- [ ] 布尔值有 `is`/`has`/`should` 前缀
- [ ] 函数读起来像自然英语

---

*Swift 和 Apple 是 Apple Inc. 的商标*