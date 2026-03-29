# 布局系统

iOS 布局系统指南，涵盖触摸目标、安全区域、UICollectionView 和组合布局。

## 触摸目标

交互元素需要足够的点击区域。建议的最小值为 44x44 点。```swift
let actionButton = UIButton(type: .system)
actionButton.setTitle("Submit", for: .normal)
view.addSubview(actionButton)

actionButton.snp.makeConstraints { make in
    make.height.greaterThanOrEqualTo(44)
    make.leading.trailing.equalToSuperview().inset(16)
    make.bottom.equalTo(view.safeAreaLayoutGuide).offset(-16)
}
```使用 8 点增量进行间距（8、16、24、32、40、48）以保持视觉一致性。

## 安全区

始终将内容限制在安全区域，以避免出现缺口、动态岛和主页指示器。```swift
class MainViewController: UIViewController {
    private let contentStack = UIStackView()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        
        contentStack.axis = .vertical
        contentStack.spacing = 16
        view.addSubview(contentStack)
        
        contentStack.snp.makeConstraints { make in
            make.top.bottom.equalTo(view.safeAreaLayoutGuide)
            make.leading.trailing.equalTo(view.safeAreaLayoutGuide).inset(16)
        }
    }
}
```## 具有 Diffable 数据源的 UICollectionView```swift
class ItemsViewController: UIViewController {
    enum Section { case main }
    
    private var collectionView: UICollectionView!
    private var dataSource: UICollectionViewDiffableDataSource<Section, Item>!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupCollectionView()
        configureDataSource()
    }
    
    private func setupCollectionView() {
        var config = UICollectionLayoutListConfiguration(appearance: .insetGrouped)
        config.trailingSwipeActionsConfigurationProvider = { [weak self] indexPath in
            self?.makeSwipeActions(for: indexPath)
        }
        
        let layout = UICollectionViewCompositionalLayout.list(using: config)
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        
        view.addSubview(collectionView)
        collectionView.snp.makeConstraints { make in
            make.edges.equalToSuperview()
        }
    }
    
    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Item> { 
            cell, indexPath, item in
            var content = cell.defaultContentConfiguration()
            content.text = item.title
            content.secondaryText = item.subtitle
            cell.contentConfiguration = content
        }
        
        dataSource = UICollectionViewDiffableDataSource(collectionView: collectionView) { 
            collectionView, indexPath, item in
            collectionView.dequeueConfiguredReusableCell(
                using: cellRegistration, for: indexPath, item: item
            )
        }
    }
    
    func updateItems(_ items: [Item]) {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
        snapshot.appendSections([.main])
        snapshot.appendItems(items)
        dataSource.apply(snapshot)
    }
}
```## 网格布局```swift
private func createGridLayout() -> UICollectionViewLayout {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1/3),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)
    item.contentInsets = NSDirectionalEdgeInsets(top: 2, leading: 2, bottom: 2, trailing: 2)
    
    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalWidth(1/3)
    )
    let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])
    
    let section = NSCollectionLayoutSection(group: group)
    return UICollectionViewCompositionalLayout(section: section)
}
```## 带标题的分段列表```swift
class CategorizedListVC: UIViewController {
    enum Section: Hashable {
        case favorites, recent, all
    }
    
    private var dataSource: UICollectionViewDiffableDataSource<Section, Item>!
    
    private func setupCollectionView() {
        var config = UICollectionLayoutListConfiguration(appearance: .insetGrouped)
        config.headerMode = .supplementary
        
        let layout = UICollectionViewCompositionalLayout.list(using: config)
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
    }
    
    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Item> { 
            cell, indexPath, item in
            var content = cell.defaultContentConfiguration()
            content.text = item.title
            cell.contentConfiguration = content
        }
        
        let headerRegistration = UICollectionView.SupplementaryRegistration<UICollectionViewListCell>(
            elementKind: UICollectionView.elementKindSectionHeader
        ) { [weak self] header, elementKind, indexPath in
            guard let section = self?.dataSource.sectionIdentifier(for: indexPath.section) else { return }
            var content = header.defaultContentConfiguration()
            content.text = self?.title(for: section)
            header.contentConfiguration = content
        }
        
        dataSource = UICollectionViewDiffableDataSource(collectionView: collectionView) { 
            collectionView, indexPath, item in
            collectionView.dequeueConfiguredReusableCell(using: cellRegistration, for: indexPath, item: item)
        }
        
        dataSource.supplementaryViewProvider = { collectionView, kind, indexPath in
            collectionView.dequeueConfiguredReusableSupplementary(using: headerRegistration, for: indexPath)
        }
    }
    
    func applySnapshot(favorites: [Item], recent: [Item], all: [Item]) {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
        if !favorites.isEmpty {
            snapshot.appendSections([.favorites])
            snapshot.appendItems(favorites, toSection: .favorites)
        }
        if !recent.isEmpty {
            snapshot.appendSections([.recent])
            snapshot.appendItems(recent, toSection: .recent)
        }
        snapshot.appendSections([.all])
        snapshot.appendItems(all, toSection: .all)
        dataSource.apply(snapshot)
    }
}
```## 间距准则

|间距|用途 |
|--------|--------|
| 8分|紧凑的元件间距|
| 16点|标准填充|
| 24点|截面间距|
| 32点|大断面分离|
| 48点|屏幕边距（大屏幕）|

---

*UIKit 和 Apple 是 Apple Inc. 的商标。SnapKit 是其各自所有者的商标。*