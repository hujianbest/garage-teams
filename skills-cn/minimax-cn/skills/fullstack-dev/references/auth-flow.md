# 身份验证流程模式

跨前端和后端的完整身份验证流程。涵盖 JWT 承载流程、自动令牌刷新、Next.js 服务器端身份验证、RBAC 和后端中间件订单。

---

## JWT 承载流程（最常见）```
1. Login
   Client → POST /api/auth/login { email, password }
   Server → { accessToken (15min), refreshToken (7d, httpOnly cookie) }

2. Authenticated Requests
   Client → GET /api/orders  Authorization: Bearer <accessToken>
   Server → validates JWT → returns data

3. Token Refresh (transparent)
   Client → 401 received → POST /api/auth/refresh (cookie auto-sent)
   Server → new accessToken
   Client → retry original request with new token

4. Logout
   Client → POST /api/auth/logout
   Server → invalidate refresh token → clear cookie
```---

## 前端：自动令牌刷新```typescript
// lib/api-client.ts — add to existing fetch wrapper
async function apiWithRefresh<T>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    return await api<T>(path, options);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      // Try refresh
      const refreshed = await api<{ accessToken: string }>('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',  // send httpOnly cookie
      });
      setAuthToken(refreshed.accessToken);
      // Retry original request
      return api<T>(path, options);
    }
    throw err;
  }
}
```---

## Next.js：服务器端身份验证（应用程序路由器）```typescript
// middleware.ts — protect routes server-side
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('session')?.value;
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  return NextResponse.next();
}

// app/dashboard/page.tsx — server component with auth
import { cookies } from 'next/headers';

export default async function Dashboard() {
  const token = (await cookies()).get('session')?.value;
  const user = await fetch(`${process.env.API_URL}/api/me`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then(r => r.json());

  return <DashboardContent user={user} />;
}
```---

## 后端：标准中间件订单```
Request → 1.RequestID → 2.Logging → 3.CORS → 4.RateLimit → 5.BodyParse
       → 6.Auth → 7.Authz → 8.Validation → 9.Handler → 10.ErrorHandler → Response
```---

## 后端：JWT 规则```
✅ Short expiry access token (15min) + refresh token (server-stored)
✅ Minimal claims: userId, roles (not entire user object)
✅ Rotate signing keys periodically

❌ Never store tokens in localStorage (XSS risk)
❌ Never pass tokens in URL query params
```---

## 后端：RBAC 模式```typescript
function authorize(...roles: Role[]) {
  return (req, res, next) => {
    if (!req.user) throw new UnauthorizedError();
    if (!roles.some(r => req.user.roles.includes(r))) throw new ForbiddenError();
    next();
  };
}
router.delete('/users/:id', authenticate, authorize('admin'), deleteUser);
```---

## 授权决策表

|方法|当 |前端 |
|--------|------|----------|
|会议|同域、SSR、Django 模板 | Django 模板/htmx |
|智威汤逊 |不同域名、SPA、移动 | React、Vue、移动应用程序 |
| OAuth2 |第三方登录、API消费者|任何|

---

## 铁律```
✅ Access token: short-lived (15min), in memory
✅ Refresh token: httpOnly cookie (XSS-safe)
✅ Automatic transparent refresh on 401
✅ Redirect to login when refresh fails

❌ Never store tokens in localStorage (XSS risk)
❌ Never send tokens in URL query params (logged)
❌ Never trust client-side auth checks alone (server must validate)
```---

## 常见问题

### 问题 1：“身份验证在页面加载时有效，但在导航时中断”

**原因：** 令牌存储在组件状态中（卸载时丢失）。

**修复：** 将访问令牌存储在持久位置：
- React Context（在导航中幸存，在刷新时丢失）
- Cookie（刷新后仍然存在）
- 使用会话的“staleTime: Infinity”来响应查询缓存

### 问题 2：“身份验证请求出现 CORS 错误”

**原因：** 前端缺少 `credentials: 'include'` 或后端 CORS 配置上缺少 `credentials: true`。

**修复：**
1. 前端：`fetch(url, {凭证:'include'})`
2. 后端：`cors({ origin: 'https://your-frontend.com',凭证: true })`
3. 后端：使用凭据时显式来源（不是“*”）