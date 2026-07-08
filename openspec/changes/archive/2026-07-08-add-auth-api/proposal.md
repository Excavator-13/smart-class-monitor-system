## Why

基础工程已搭建完成（`init-springboot-backend`），需要实现登录鉴权模块，让前端能够通过 `/auth/login` 获取 JWT Token，并在后续请求中携带 Token 访问受保护的接口。鉴权是后续所有业务模块的前置依赖。

## What Changes

- 新增 `user` 数据库表（DDL）：`id`、`username`、`password_hash`、`role`、`nickname`、`avatar_url`、`status`、`last_login_at`、`created_at`、`updated_at`、`deleted_at`
- 新增 `User` Entity、`UserMapper`（MyBatis）
- 新增 `POST /auth/login`：校验用户名密码，返回 JWT token + 用户信息（`user_id`、`username`、`role`、`nickname`、`avatar_url`）
- 新增 `GET /auth/info`：根据请求头 Token 返回当前用户信息
- 新增 `POST /auth/logout`：初版空实现，返回成功
- 新增 JWT Token 生成与校验（`JwtTokenProvider`），Token 包含 `user_id`、`username`、`role`、过期时间
- 新增 `JwtAuthenticationInterceptor`：拦截除 `/auth/login` 和 `/system/health` 外的请求，校验 Token 并注入当前用户上下文
- 新增 `CurrentUser` 注解和 `CurrentUserResolver`，Controller 可注入当前登录用户
- 新增 DTO（`LoginRequest`）和 VO（`LoginResponse`、`UserInfoVO`），Swagger 示例真实可用
- **不实现** `/users` CRUD（用户管理后续独立 change）
- **不实现** AI 内部接口鉴权（后续独立 change）

## Capabilities

### New Capabilities
- `auth-login`: 用户登录，返回 JWT Token
- `auth-token-verify`: JWT Token 校验与用户信息获取
- `auth-logout`: 退出登录（初版空实现）

### Modified Capabilities
<!-- 无现有 capability 需要修改 -->

## Impact

- 新增数据库表：`user`
- 新增文件：Entity、Mapper、DTO、VO、Service、Controller、JWT 相关类
- 修改文件：`application.yml`（可选，增加 JWT 配置项）
- 影响接口：`/auth/login`（放行）、`/auth/info`（需 Token）、`/auth/logout`（需 Token）
- 鉴权拦截器影响所有现有接口（`/system/health` 需显式放行）
