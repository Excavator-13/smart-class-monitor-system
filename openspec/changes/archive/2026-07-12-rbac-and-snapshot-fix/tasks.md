## 1. RBAC 注解与拦截器

- [x] 1.1 创建 `@RequireRole` 注解（`@Target({METHOD, TYPE})`，`String[] value()`）
- [x] 1.2 创建 `RequireRoleInterceptor`：读取 handler 方法/类上的 `@RequireRole`，从 `request.getAttribute("currentRole")` 校验，不满足抛 `BusinessException(403, "权限不足")`；Internal token 请求放行；无注解放行
- [x] 1.3 `WebMvcConfig` 注册 `RequireRoleInterceptor`（在 JWT 拦截器之后）

## 2. 现有 Controller 添加权限注解

- [x] 2.1 `StudentController`：`POST`/`PUT`/`DELETE` 方法添加 `@RequireRole("admin")`
- [x] 2.2 `StreamController`：`POST`/`PUT`/`DELETE` 方法添加 `@RequireRole("admin")`
- [x] 2.3 `ZoneController`：`POST`/`PUT`/`DELETE` 方法添加 `@RequireRole("admin")`
- [x] 2.4 `RuleController`：`POST`/`PUT`/`DELETE` 方法添加 `@RequireRole("admin")`
- [x] 2.5 `OperationLogController`：类级 `@RequireRole("admin")`
- [x] 2.6 `ReportController`：`POST /report/generate` 添加 `@RequireRole("admin")`

## 3. 注册逻辑调整（首个用户自动 admin）

- [x] 3.1 `UserMapper` 新增 `countActive()` 方法
- [x] 3.2 `AuthService.register()` 中判断 `countActive() == 0` 则 `role = "admin"`，否则 `role = "teacher"`

## 4. 用户管理 API

- [x] 4.1 `UserMapper` 新增：`findAll`、`findByRole`、`findByStatus`、`countAll`、`countByRole`、`countByStatus`、`updateRole`、`updateStatus`、`softDelete`
- [x] 4.2 创建 `UserUpdateRequest` DTO（nickname、avatarUrl）
- [x] 4.3 创建 `UserRoleUpdateRequest` DTO（role，校验 admin/teacher）
- [x] 4.4 创建 `UserStatusUpdateRequest` DTO（status，校验 enabled/disabled）
- [x] 4.5 创建 `UserVO`（id、username、role、nickname、avatarUrl、status、lastLoginAt、createdAt）
- [x] 4.6 创建 `UserService`：listUsers、getUser、updateUser、updateRole、updateStatus、deleteUser（含"不能操作自己"校验）
- [x] 4.7 创建 `UserController`（类级 `@RequireRole("admin")`）：`GET /users`、`GET /users/{id}`、`PUT /users/{id}`、`PUT /users/{id}/role`、`PUT /users/{id}/status`、`DELETE /users/{id}`

## 5. 截图 SCP 推送

- [x] 5.1 `config/app.yaml` 新增 `snapshot_remote` 配置节（host、user、path）
- [x] 5.2 `.env.example` 新增 `SNAPSHOT_REMOTE_HOST`、`SNAPSHOT_REMOTE_USER`、`SNAPSHOT_REMOTE_PATH`
- [x] 5.3 创建 `services/snapshot_push.py`：`SnapshotPusher` 类，`push()` 方法执行 SSH `mkdir -p` + SCP，`push_async()` 用 `threading.Thread(daemon=True)` 异步执行，失败 log warning 不抛异常
- [x] 5.4 `app.py` 中读取 `snapshot_remote` 配置，构造 `SnapshotPusher` 实例，注入 `AnalysisService`

## 6. Flask /snapshots 路由

- [x] 6.1 `app.py` 中注册 `GET /snapshots/<path:filename>` 路由，`send_from_directory(snapshot_dir, filename)`

## 7. AnalysisService 集成推送

- [x] 7.1 `AnalysisService.__init__` 新增 `snapshot_pusher` 参数
- [x] 7.2 `_save_snapshot()` 保存本地后调用 `snapshot_pusher.push_async()`

## 8. 编译与验证

- [x] 8.1 `mvn -DskipTests compile` 编译通过
- [ ] 8.2 验证 teacher 调用 `POST /streams` 返回 403
- [ ] 8.3 验证 teacher 调用 `GET /streams` 返回 200
- [ ] 8.4 验证 admin 调用 `GET /users` 返回 200
- [ ] 8.5 验证 teacher 调用 `GET /users` 返回 403
- [ ] 8.6 验证首个注册用户 role 为 admin
- [ ] 8.7 验证后续注册用户 role 为 teacher
- [ ] 8.8 验证 `PUT /users/{id}/role` 不能改自己角色
- [ ] 8.9 验证 Flask `/snapshots/` 路由可返回本地截图文件
- [ ] 8.10 验证 `SNAPSHOT_REMOTE_HOST` 为空时不执行 SCP 推送
