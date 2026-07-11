## Context

鉴权模块 `add-auth-api` 已完成，提供了 `POST /auth/login`、`GET /auth/info`、`POST /auth/logout`，以及 `User` Entity、`UserMapper`、`AuthService`、`JwtTokenProvider`、`JwtAuthenticationInterceptor` 等基础设施。现在需要新增用户自主注册功能，使前端能够完成完整的用户准入流程。

当前 `user` 表已有 `uk_user_username` 唯一键，`UserMapper` 已有 `insert` 方法，`PasswordEncoder`（BCrypt）已在 `SecurityConfig` 中注册为 Bean。注册接口可复用现有基础设施，改动量较小。

## Goals / Non-Goals

**Goals:**

- `POST /auth/register`：接收 `username`、`password`、可选 `nickname`，创建用户并返回 JWT + 用户信息
- 新增 `RegisterRequest` DTO，复用 `LoginResponse` VO
- `AuthService` 新增 `register` 方法：校验用户名唯一 → BCrypt 加密 → 插入 user 表 → 生成 JWT
- `JwtAuthenticationInterceptor` 放行 `/auth/register`
- 注册用户默认 `role = teacher`、`status = enabled`

**Non-Goals:**

- 不实现管理员创建或角色指定
- 不实现邮箱/手机验证
- 不实现密码强度评分
- 不实现注册限流/防刷
- 不实现邀请码机制

## Decisions

| 决策           | 选择                                       | 理由                                                    |
| -------------- | ------------------------------------------ | ------------------------------------------------------- |
| 注册后返回 JWT | 直接返回，与登录一致                       | 前端无需注册后再调一次登录，体验流畅                    |
| 响应 VO        | 复用 `LoginResponse`                       | 注册成功返回结构与登录完全相同，无需新增 VO             |
| 用户名唯一校验 | Service 层先查 + DB 唯一键兜底             | 双重保障：Service 层给出友好提示，DB 唯一键防止并发冲突 |
| 默认角色       | `teacher`                                  | 安全原则，新注册用户不应获得 admin 权限                 |
| 昵称字段       | 可选，为空时存 null                        | 降低注册门槛，用户可后续补充                            |
| 放行路径       | 在 `EXCLUDE_PATHS` 中添加 `/auth/register` | 与 `/auth/login` 保持一致的放行策略                     |
| 密码长度下限   | 6 字符                                     | 平衡安全性与易用性                                      |

## 注册流程

```
POST /auth/register  (无需 Token)
      │
      ▼
  AuthService.register(username, password, nickname)
      │
      ├─ 校验 username 非空、长度 2-64
      ├─ 校验 password 非空、长度 6-128
      ├─ 校验 nickname 长度 ≤ 64（如提供）
      ├─ 查询 user WHERE username=? AND deleted_at IS NULL
      │     └─ 若已存在 → 抛出 BusinessException(409, "用户名已存在")
      ├─ BCrypt 加密 password → passwordHash
      ├─ 构建 User：role=teacher, status=enabled, nickname=null(如未提供)
      ├─ UserMapper.insert(user)
      ├─ JwtTokenProvider.generate(user_id, username, role)
      └─ 返回 LoginResponse { token, user_id, username, role, nickname, avatar_url }
```

## Risks / Trade-offs

- **[并发注册]** 两个请求同时用相同用户名注册 → DB 唯一键兜底，抛出 500 → 需在 GlobalExceptionHandler 中捕获 `DuplicateKeyException` 转为 409
- **[注册防刷]** 无限流机制 → 初版可接受，后续可加验证码或 IP 限流
- **[弱密码]** 仅校验长度，不校验复杂度 → 初版可接受，后续可加密码强度校验

## Open Questions

- 是否需要注册后发送欢迎通知：初版不做
- 是否需要注册邮箱验证：初版不做
