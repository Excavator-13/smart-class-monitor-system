## 1. 数据库与数据层

- [x] 1.1 创建 `user` 表 DDL
- [x] 1.2 创建 `User` Entity
- [x] 1.3 创建 `UserMapper`

## 2. JWT 工具类

- [x] 2.1 在 `application.yml` 中增加 JWT 配置
- [x] 2.2 创建 `JwtTokenProvider`
- [x] 2.3 创建 `CurrentUser` 注解
- [x] 2.4 创建 `CurrentUserResolver`

## 3. DTO、VO

- [x] 3.1 创建 `LoginRequest` DTO
- [x] 3.2 创建 `LoginResponse` VO
- [x] 3.3 创建 `UserInfoVO`

## 4. 鉴权拦截器

- [x] 4.1 创建 `JwtAuthenticationInterceptor`
- [x] 4.2 创建 `WebMvcConfig`

## 5. Service 层

- [x] 5.1 创建 `AuthService`

## 6. Controller 层

- [x] 6.1 创建 `AuthController`（POST /auth/login, GET /auth/info, POST /auth/logout）

## 7. 密码加密

- [x] 7.1 创建 `SecurityConfig`（BCryptPasswordEncoder Bean）

## 8. 初始化数据

- [x] 8.1 创建 `data.sql`（admin/teacher 初始化 SQL，需手动生成 BCrypt 哈希）

## 9. Swagger 示例验证

- [x] 9.1 LoginRequest、LoginResponse、UserInfoVO 均含 `@Schema` 描述和示例值

## 10. 编译与测试

- [x] 10.1 运行 `mvn -DskipTests compile`，确保编译通过
- [x] 10.2 确认 `/auth/login` 不需要 Token 即可访问（在拦截器白名单中）
- [x] 10.3 确认 `/auth/info` 和 `/auth/logout` 需要 Token（返回 401 如果缺失）
