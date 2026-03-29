# Django 最佳实践

Django 5.x 和 Django REST Framework 的生产级指南。 8 个类别的 40 多个规则。

## 核心原则（7 条规则）```
1. ✅ Custom User model BEFORE first migration (can't change later)
2. ✅ One Django app per domain concept (users, orders, payments)
3. ✅ Fat models, thin views — business logic in models/managers, not views
4. ✅ Always use select_related/prefetch_related (prevent N+1)
5. ✅ Settings split by environment (base + dev + prod)
6. ✅ Test with pytest-django + factory_boy (not fixtures)
7. ✅ Never use runserver in production (Gunicorn + Nginx)
```---

## 1. 项目结构（关键）

### 每个域的应用程序```
myproject/
├── config/                     # Project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── dev.py              # DEBUG=True, SQLite ok
│   │   └── prod.py             # DEBUG=False, Postgres, HTTPS
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/                  # Custom User model
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── services.py         # Business logic
│   │   ├── selectors.py        # Complex queries
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── factories.py
│   ├── orders/
│   └── payments/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── docker-compose.yml
```### 规则```
✅ One app = one bounded context (users, orders, payments)
✅ Business logic in services.py / selectors.py, not views
✅ Each app has its own urls.py, admin.py, tests/

❌ Never put everything in one app
❌ Never import across app boundaries at the model level (use IDs)
❌ Never put business logic in views or serializers
```---

## 2. 模型和迁移（关键）

### 自定义用户模型（第一天！）```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

# config/settings/base.py
AUTH_USER_MODEL = 'users.User'
```**这必须在“迁移”之前完成。之后无法更改。**

### 建模最佳实践```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Order(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def can_cancel(self) -> bool:
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def cancel(self):
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel order in {self.status} status")
        self.status = OrderStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
```### 迁移规则```
✅ Review migration SQL: python manage.py sqlmigrate app_name 0001
✅ Name migrations descriptively: --name add_status_index_to_orders
✅ Separate data migrations from schema migrations
✅ Non-destructive first: add column → backfill → remove old column

❌ Never edit or delete applied migrations
❌ Never use RunPython without reverse function
```---

## 3. 视图和序列化器 — DRF（高）

### 服务层模式```python
# apps/orders/services.py
from django.db import transaction

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, items_data: list[dict]) -> Order:
        total = sum(item['price'] * item['quantity'] for item in items_data)
        order = Order.objects.create(user=user, total=total)
        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item) for item in items_data
        ])
        return order

    @staticmethod
    def cancel_order(order_id: str, user) -> Order:
        order = Order.objects.select_for_update().get(id=order_id, user=user)
        order.cancel()
        return order
```### 序列化器```python
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'status', 'total', 'items', 'created_at']
        read_only_fields = ['id', 'total', 'created_at']

class CreateOrderSerializer(serializers.Serializer):
    """Input-only serializer — separate from output."""
    items = serializers.ListField(
        child=serializers.DictField(), min_length=1, max_length=50,
    )
    def validate_items(self, items):
        for item in items:
            if item.get('quantity', 0) < 1:
                raise serializers.ValidationError("Quantity must be at least 1")
        return items
```### 视图（薄！）```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    serializer = CreateOrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = OrderService.create_order(request.user, serializer.validated_data['items'])
    return Response({'data': OrderSerializer(order).data}, status=status.HTTP_201_CREATED)
```### 规则```
✅ Separate input serializers from output serializers
✅ Views only: validate → call service → serialize → respond
✅ Use @transaction.atomic for multi-model writes

❌ Never put business logic in views or serializers
❌ Never use ModelSerializer for write operations (too implicit)
```---

## 4. 身份验证（高）

|方法|当 |前端 |
|--------|------|----------|
|会议|同域、SSR、Django 模板 | Django 模板/htmx |
|智威汤逊 |不同域名、SPA、移动 | React、Vue、移动应用程序 |
| OAuth2 |第三方登录、API消费者|任何|

### JWT 配置 (djangorestframework-simplejwt)```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```---

## 5. 性能优化（高）

### N+1 查询预防```python
# ❌ N+1: 1 query for orders + N queries for users
orders = Order.objects.all()
for o in orders:
    print(o.user.email)     # hits DB each iteration

# ✅ select_related (FK/OneToOne — JOIN)
orders = Order.objects.select_related('user').all()

# ✅ prefetch_related (ManyToMany/reverse FK — 2 queries)
orders = Order.objects.prefetch_related('items').all()

# ✅ Combined
orders = Order.objects.select_related('user').prefetch_related('items').all()
```### 查询优化工具包```python
# Only fetch needed columns
User.objects.values('id', 'email')
User.objects.values_list('email', flat=True)

# Annotate instead of Python loops
from django.db.models import Count, Sum
Order.objects.annotate(item_count=Count('items'), revenue=Sum('items__price'))

# Bulk operations
OrderItem.objects.bulk_create([...])
Order.objects.filter(status='pending').update(status='cancelled')

# Database indexes
class Meta:
    indexes = [
        models.Index(fields=['user', 'status']),
        models.Index(fields=['-created_at']),
        models.Index(fields=['email'], condition=Q(is_active=True)),
    ]

# Pagination
from rest_framework.pagination import CursorPagination
class OrderPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'
```### 缓存```python
from django.core.cache import cache

def get_product(product_id: str):
    cache_key = f'product:{product_id}'
    product = cache.get(cache_key)
    if product is None:
        product = Product.objects.get(id=product_id)
        cache.set(cache_key, product, timeout=300)
    return product
```---

## 6. 测试（中-高）

### pytest-django +factory_boy```python
# conftest.py
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client
```

```python
# factories.py
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'orders.Order'
    user = factory.SubFactory(UserFactory)
    total = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
```

```python
# test_views.py
@pytest.mark.django_db
class TestListOrders:
    def test_returns_user_orders(self, authenticated_client):
        OrderFactory.create_batch(3, user=authenticated_client.handler._force_user)
        response = authenticated_client.get('/api/orders/')
        assert response.status_code == 200
        assert len(response.data['data']) == 3

    def test_requires_authentication(self, api_client):
        response = api_client.get('/api/orders/')
        assert response.status_code == 401
```---

## 7. 管理自定义（中）```python
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
```---

## 8. 生产部署（中）

### 安全设置```python
# settings/prod.py
DEBUG = False
ALLOWED_HOSTS = ['example.com', 'www.example.com']
CSRF_TRUSTED_ORIGINS = ['https://example.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```### 部署堆栈```
Nginx → Gunicorn → Django
         ↕
      PostgreSQL + Redis (cache)
         ↕
      Celery (background tasks)
```

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile -
```### 静态文件的 WhiteNoise```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # right after Security
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```### 规则```
✅ Gunicorn + Nginx (or Cloud Run / Railway)
✅ PostgreSQL (not SQLite)
✅ python manage.py check --deploy
✅ Sentry for error tracking

❌ Never use runserver in production
❌ Never use DEBUG=True in production
❌ Never use SQLite in production
```---

## 反模式

| ＃| ❌不要 | ✅ 改为 |
|---|---------|--------------|
| 1 |视图中的业务逻辑|服务层（`services.py`）|
| 2 |一个巨大的应用程序 |每个域的应用程序 |
| 3 |默认用户模型 |首次迁移前的自定义用户 |
| 4 |没有“选择相关” |始终急切加载相关对象 |
| 5 |用于测试的 Django 装置 | “factory_boy”工厂 |
| 6 | `settings.py` 单个文件 |拆分：基础 + 开发 + 产品 |
| 7 |生产环境中的“runserver” | Gunicorn + Nginx |
| 8 | SQLite 投入生产 | PostgreSQL |
| 9 |用于写入的`ModelSerializer`显式输入序列化器 |
| 10 | 10视图中的原始 SQL | ORM 查询集 + `selectors.py` |

---

## 常见问题

### 问题 1：“首次迁移后无法更改用户模型”

**修复：** 如果重新开始：删除所有迁移+数据库，设置自定义用户，重新迁移。如果数据存在：复杂迁移（使用`django-allauth`或增量字段迁移）。

### 问题 2：“序列化器在大型查询集上太慢”

**修复：** 缺少 `select_lated` / `prefetch_lated` → N+1 查询。```python
queryset = Order.objects.select_related('user').prefetch_related('items')
```### 问题 3：“应用程序之间的循环导入”

**修复：** 使用字符串引用：`models.ForeignKey('orders.Order', ...)` 而不是导入模型类。对于服务，请在函数内部导入。