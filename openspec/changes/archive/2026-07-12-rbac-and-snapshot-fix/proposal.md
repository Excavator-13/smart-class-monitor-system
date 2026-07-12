# RBAC 权限控制 + 告警截图通路修复

## 动机

### 问题一：权限控制缺失

当前系统已具备角色基础设施（`User.role` 字段、JWT claims 含 role、拦截器解析 role 存入 request attribute），但**没有任何接口做角色校验**。所有已登录用户（无论 admin 还是 teacher）均可访问全部 API，包括用户管理、视频源增删改、规则增删改等管理操作。这不符合实际使用场景：教师只需查看告警和人员信息，管理操作应由管理员执行。

此外，注册接口硬编码 `role="teacher"`，缺少管理员创建机制。需要：

1. 第一个注册用户自动成为 admin（系统初始化场景）
2. 后续注册用户仍为 teacher
3. 管理员可在用户管理页分配/变更角色

### 问题二：告警截图 404

告警的"证据"功能当前不可用，点击截图链接返回 404。经排查，问题链路如下：

1. **AI 服务截图保存正常**：`AnalysisService._save_snapshot()` 将截图写入 `backend_ai/static/snapshots/{day}/{event_id}.jpg`，返回相对路径 `/snapshots/{day}/{event_id}.jpg`，并随 `push_alert()` 入库到 `alert_event.snapshot_path`
2. **SpringBoot 返回路径正常**：`AlertService.mapToAlertVO()` 将 `snapshot_path` 映射为 `snapshot_url` 返回给前端
3. **前端拼接 Nginx 地址**：`joinResourceUrl()` 将 `snapshot_url` 与 `NGINX_BASE`（云服务器 `http://39.106.209.208:9092`）拼接，最终请求 `http://39.106.209.208:9092/snapshots/...`
4. **截图文件不在云服务器上**：AI 在本地机器保存截图，云服务器 Nginx 的磁盘上没有这些文件，返回 404
5. **Flask 本地也未正确提供静态服务**：`Flask(__name__)` 默认 static URL 前缀为 `/static`，访问 `/snapshots/...` 无法命中

修复方案（Nginx 静态目录 + AI SCP 推送）：

- AI 保存截图后，异步 SCP 推送到云服务器 `/data/snapshots/` 目录
- 云服务器 Nginx 新增 `location /snapshots/` 配置，alias 到 `/data/snapshots/`
- Flask 本地也注册 `/snapshots` 路由作为开发环境 fallback
- 前端 `joinResourceUrl()` 逻辑不变，继续走 `NGINX_BASE/snapshots/...`

## 范围

### 一、RBAC 权限控制

#### 角色与权限矩阵

| 接口分组     | 操作                               | admin | teacher |
| ------------ | ---------------------------------- | ----- | ------- |
| **认证**     | `POST /auth/login`                 | ✅    | ✅      |
|              | `POST /auth/register`              | ✅    | ✅      |
|              | `GET /auth/info`                   | ✅    | ✅      |
|              | `POST /auth/logout`                | ✅    | ✅      |
| **用户管理** | `GET /users`                       | ✅    | ❌      |
|              | `GET /users/{id}`                  | ✅    | ❌      |
|              | `PUT /users/{id}`                  | ✅    | ❌      |
|              | `PUT /users/{id}/role`             | ✅    | ❌      |
|              | `PUT /users/{id}/status`           | ✅    | ❌      |
|              | `DELETE /users/{id}`               | ✅    | ❌      |
| **告警**     | `GET /alerts`                      | ✅    | ✅      |
|              | `GET /alerts/{id}`                 | ✅    | ✅      |
|              | `PUT /alerts/{id}/status`          | ✅    | ✅      |
|              | `GET /alert-stats`                 | ✅    | ✅      |
| **人员**     | `GET /students`                    | ✅    | ✅      |
|              | `GET /students/{id}`               | ✅    | ✅      |
|              | `POST /students`                   | ✅    | ❌      |
|              | `PUT /students/{id}`               | ✅    | ❌      |
|              | `DELETE /students/{id}`            | ✅    | ❌      |
| **人脸**     | `POST /students/{id}/face`         | ✅    | ✅      |
|              | `GET /students/{id}/face-features` | ✅    | ✅      |
| **视频源**   | `GET /streams`                     | ✅    | ✅      |
|              | `GET /streams/enabled`             | ✅    | ✅      |
|              | `GET /streams/{id}`                | ✅    | ✅      |
|              | `GET /streams/{id}/status`         | ✅    | ✅      |
|              | `GET /streams/{id}/preview-url`    | ✅    | ✅      |
|              | `POST /streams`                    | ✅    | ❌      |
|              | `PUT /streams/{id}`                | ✅    | ❌      |
|              | `DELETE /streams/{id}`             | ✅    | ❌      |
| **区域**     | `GET /zones`                       | ✅    | ✅      |
|              | `GET /zones/{id}`                  | ✅    | ✅      |
|              | `GET /streams/{id}/zones`          | ✅    | ✅      |
|              | `POST /zones`                      | ✅    | ❌      |
|              | `PUT /zones/{id}`                  | ✅    | ❌      |
|              | `DELETE /zones/{id}`               | ✅    | ❌      |
| **规则**     | `GET /rules`                       | ✅    | ✅      |
|              | `GET /rules/{id}`                  | ✅    | ✅      |
|              | `POST /rules`                      | ✅    | ❌      |
|              | `PUT /rules/{id}`                  | ✅    | ❌      |
|              | `DELETE /rules/{id}`               | ✅    | ❌      |
| **录像**     | `GET /recordings`                  | ✅    | ✅      |
| **操作日志** | `GET /operation-logs`              | ✅    | ❌      |
| **系统**     | `GET /system/health`               | ✅    | ✅      |
| **日报**     | `GET /report/latest`               | ✅    | ✅      |
|              | `POST /report/generate`            | ✅    | ❌      |

#### 实现要点

1. **`@RequireRole` 自定义注解**：标注在 Controller 方法或类上，声明所需角色（如 `@RequireRole("admin")`），支持多角色（如 `@RequireRole({"admin", "teacher"})`）
2. **`RequireRoleInterceptor`**：在 JWT 拦截器之后执行，读取 `request.getAttribute("currentRole")`，校验是否满足注解要求，不满足抛 403
3. **注册逻辑调整**：`AuthService.register()` 中判断当前 user 表是否为空（无任何记录），若为空则第一个用户角色为 `admin`，否则为 `teacher`
4. **用户管理 API**（新增）：
   - `GET /users`：分页查询用户列表（支持 role/status 筛选）
   - `GET /users/{id}`：用户详情
   - `PUT /users/{id}`：更新用户基本信息（nickname、avatarUrl）
   - `PUT /users/{id}/role`：变更用户角色（仅 admin 可调用）
   - `PUT /users/{id}/status`：启用/禁用用户（仅 admin 可调用）
   - `DELETE /users/{id}`：软删除用户（仅 admin 可调用）
5. **UserMapper 扩展**：新增 `countAll()`、`findAll()`、`updateRole()`、`updateStatus()`、`softDelete()` 等方法
6. **新增 DTO/VO**：`UserUpdateRequest`、`UserRoleUpdateRequest`、`UserStatusUpdateRequest`、`UserVO`
7. **新增 `UserController`**：用户管理接口，类级 `@RequireRole("admin")`
8. **现有 Controller 添加注解**：按权限矩阵在写操作方法上添加 `@RequireRole("admin")`

### 二、告警截图通路修复

#### 实现要点

1. **AI 异步 SCP 推送**：`_save_snapshot()` 保存本地后，异步调用 `scp -i {key_path}` 将文件推送到云服务器 `{user}@{host}:{path}/{day}/{event_id}.jpg`，推送前通过 SSH `mkdir -p` 确保远程目录存在
2. **推送失败容错**：SCP 推送失败不影响告警流程，仅 log warning，本地文件仍保留
3. **配置化**：通过 `config/app.yaml` 的 `snapshot_remote` 节或环境变量 `SNAPSHOT_REMOTE_HOST` 等配置远程推送参数，`host` 为空则不推送
4. **Flask 本地 fallback**：注册 `/snapshots/<path:filename>` 路由，`send_from_directory` 提供本地文件服务，供开发环境使用
5. **云服务器 Nginx 配置**（手动操作，不自动化）：新增 `location /snapshots/ { alias /data/snapshots/; }`

## 不做

- 不引入 Spring Security 框架（保持轻量拦截器方案）
- 不实现细粒度权限（如按视频源/区域授权）
- 不实现角色继承或权限组
- 不修改前端代码（前端后续独立 change 对接）
- 不实现视频片段（`record_url`）的代理或播放
- 不修改 AI 服务的截图保存逻辑（本地保存路径和返回值不变）
- 不修改 SpringBoot 侧的 `snapshot_path` → `snapshot_url` 映射逻辑
- 不自动化云服务器 Nginx 配置（需手动操作，spec 中给出步骤）
- 不使用对象存储（OSS/S3）或数据库 BLOB 存储截图

## 影响模块

### backend_system（Java / SpringBoot）

- `security/`：新增 `RequireRole` 注解、`RequireRoleInterceptor` 拦截器
- `config/WebMvcConfig`：注册新拦截器
- `controller/`：所有 Controller 添加 `@RequireRole` 注解
- `controller/UserController`：新增用户管理 API
- `service/AuthService`：注册逻辑调整（首个用户自动 admin）
- `service/UserService`：新增用户管理 Service
- `mapper/UserMapper`：扩展查询和更新方法
- `dto/`：新增 `UserUpdateRequest`、`UserRoleUpdateRequest`、`UserStatusUpdateRequest`
- `vo/`：新增 `UserVO`

### backend_ai（Python / Flask）

- `app.py`：新增 `/snapshots/<path:filename>` 路由，映射到 `static/snapshots` 目录
- `services/analysis_service.py`：`_save_snapshot()` 后异步 SCP 推送到云服务器
- `services/snapshot_push.py`（新增）：SCP 推送逻辑，含远程目录创建、失败重试、日志
- `config/app.yaml`：新增 `snapshot_remote` 配置节
- `.env.example`：新增 `SNAPSHOT_REMOTE_*` 环境变量示例
