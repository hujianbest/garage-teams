# 环境和 CORS 管理

用于跨前端和后端堆栈管理环境变量、API URL 和 CORS 配置的模式。

---

## 标准环境模式```
# .env.local (gitignored, for local dev)
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_WS_URL=ws://localhost:3001

# Staging (set in Vercel/CI)
NEXT_PUBLIC_API_URL=https://api-staging.example.com

# Production (set in Vercel/CI)
NEXT_PUBLIC_API_URL=https://api.example.com
```---

## 环境变量规则```
✅ API base URL from environment variable — NEVER hardcoded
✅ Prefix client-side vars with NEXT_PUBLIC_ (Next.js) or VITE_ (Vite)
✅ Backend URL = server-only env var (for SSR calls, not exposed to browser)
✅ CORS on backend: explicit list of allowed origins per environment

❌ Never use localhost URLs in production builds
❌ Never expose backend-only secrets with NEXT_PUBLIC_ prefix
❌ Never commit .env.local (commit .env.example with placeholders)
```---

## CORS 配置```typescript
// Backend: environment-aware CORS
const ALLOWED_ORIGINS = {
  development: ['http://localhost:3000', 'http://localhost:5173'],
  staging: ['https://staging.example.com'],
  production: ['https://example.com', 'https://www.example.com'],
};

app.use(cors({
  origin: ALLOWED_ORIGINS[process.env.NODE_ENV || 'development'],
  credentials: true,  // needed for cookies (auth)
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
}));
```---

## 常见问题

### 问题 1：“浏览器中出现 CORS 错误，但在 Postman 中有效”

**原因：** CORS 是一项浏览器安全功能。邮差/卷曲跳过它。

**修复：**
1. 后端必须返回 `Access-Control-Allow-Origin: https://your-frontend.com`
2. 对于cookie/auth：两边都是`credentials: true`
3. 检查预检“OPTIONS”请求是否返回正确的标头

### 问题 2：“浏览器中未定义环境变量”

**原因：** 客户端访问缺少“NEXT_PUBLIC_”或“VITE_”前缀。

**修复：** 客户端变量必须具有框架前缀。添加新的环境变量后重新构建（它们在构建时嵌入）。

### 问题 3：“本地工作，暂存失败”

**原因：** 来源不同，缺少暂存域的 CORS 配置。

**修复：** 将暂存源添加到“ALLOWED_ORIGINS”，验证部署平台中是否设置了环境变量。