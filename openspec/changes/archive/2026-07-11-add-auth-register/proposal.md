# 用户注册 API

## 动机

前端需要用户自主注册功能，当前后端仅提供登录（`POST /auth/login`），无法创建新账户。新增注册接口使前端能够完成完整的用户准入流程，不再依赖数据库手动插入初始用户。

## 范围

- `POST /auth/register` 接收用户名、密码、昵称（可选），创建新用户并返回 JWT Token + 用户信息
- 校验：用户名不能为空、长度 2-64、不能重复；密码不能为空、长度 6-128；昵称长度上限 64
- 新增 `RegisterRequest` DTO，复用 `LoginResponse` VO
- `AuthService` 新增 `register` 方法，使用已有 `PasswordEncoder` 加密密码
- `JwtAuthenticationInterceptor` 放行 `/auth/register`
- 注册用户默认角色 `teacher`、状态 `enabled`
- 不涉及管理员创建、角色指定、邮箱/手机验证等高级功能
