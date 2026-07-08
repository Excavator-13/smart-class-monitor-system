## Context

基础工程 `init-springboot-backend` 已完成，提供了 `ApiResponse`、`PageResult`、`BusinessException`、`GlobalExceptionHandler`、Jackson/CORS/Swagger 配置。现在需要在其上搭建登录鉴权。

`backend_system/` 中尚无任何数据库表、Entity、Mapper。本 change 将创建第一张业务表 `user` 并打通 MyBatis → Service → Controller 全链路。

## Goals / Non-Goals

**Goals:**
- `user` 表 DDL + User Entity + UserMapper（MyBatis 注解或 XML）
- `POST /auth/login`：BCrypt 验密 → 生成 JWT → 返回 token + 用户信息
- `GET /auth/info`：解析 Token → 查询用户 → 返回用户信息
- `POST /auth/logout`：初版直接返回成功（后续可扩展 Token 黑名单）
- JWT 拦截器：对除 `/auth/login`、`/system/health`、Swagger 路径外的请求校验 Token
- `/auth/login` 和 `/system/health` 在拦截器中显式放行
- 密码使用 BCrypt 哈希，数据库只存 `password_hash`

**Non-Goals:**
- 不实现 `/users` CRUD
- 不实现 AI 内部接口鉴权
- 不实现 Token 刷新机制
- 不实现密码修改/重置
- 不实现 `@PreAuthorize` 方法级权限（初版角色校验在拦截器层即可）

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 密码哈希 | BCrypt | Spring Security 内置 `BCryptPasswordEncoder`，行业标准 |
| JWT 库 | `io.jsonwebtoken:jjwt` (jjwt-api + jjwt-impl + jjwt-jackson) | 轻量、广泛使用、与 SpringBoot 3.x 兼容 |
| MyBatis 映射方式 | 注解（`@Select`/`@Insert`） | user 表操作简单（3-4 条 SQL），XML 过重 |
| 拦截器 vs 过滤器 | HandlerInterceptor | 可获取 Spring Bean（如 `JwtTokenProvider`），能拿到 Controller 方法信息 |
| Token 传递方式 | `Authorization: Bearer <token>` | RESTful 标准，前端 Axios 拦截器统一添加 |
| 放行路径配置 | 配置文件 `auth.exclude-paths` | 不硬编码，后续加接口无需改代码 |
| `/auth/logout` 实现 | 空实现返回成功 | 初版前端直接清 Token 即可，后续扩展黑名单 |
| 登录失败 HTTP 码 | 400（参数缺失） + 统一业务错误 | 详细设计 §8：认证失败用特定 message，不区分 401 是为了简化前端处理 |

## JWT 认证流程

```
POST /auth/login
      │
      ▼
  AuthService.login(username, password)
      │
      ├─ 查询 user WHERE username=? AND deleted_at IS NULL
      ├─ BCrypt 校验 password ↔ password_hash
      ├─ 校验 status=enabled
      ├─ 更新 last_login_at
      ├─ JwtTokenProvider.generate(user_id, username, role)
      └─ 返回 LoginResponse { token, user_id, username, role, ... }

GET /auth/info  (Header: Authorization: Bearer <token>)
      │
      ▼
  JwtAuthenticationInterceptor.preHandle()
      │
      ├─ 提取 Token
      ├─ JwtTokenProvider.validate(token)
      ├─ 解析 claims → user_id, username, role
      ├─ 注入 CurrentUser 到 Request attribute
      └─ 放行

  AuthController.info()
      │
      ├─ 从 CurrentUser 获取 user_id
      ├─ 查询 user
      └─ 返回 UserInfoVO
```

## Risks / Trade-offs

- **[JWT 无状态]** Token 签发后无法主动失效 → 初版可接受，后续加 Redis 黑名单
- **[密码暴力破解]** 登录接口无限流 → 初版可接受，后续加限流
- **[Token 过期]** 需与前端约定过期时间 → 建议 24h，在 `application.yml` 中可配置

## Open Questions

- JWT 过期时间：建议 24 小时，在 `application.yml` 中通过 `auth.jwt.expiration-hours` 配置
- 是否需要 `refresh_token`：初版不做
