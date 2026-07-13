## Context

### 已有基础设施

**鉴权层**：`JwtAuthenticationInterceptor` 已从 JWT 解析 `currentUserId`、`currentUsername`、`currentRole` 并存入 request attribute。`CurrentUserResolver` 解析 `@CurrentUser` 注解获取 userId。`WebMvcConfig` 注册拦截器链。

**用户模型**：`User` 实体有 `role`（admin/teacher）和 `status`（enabled/disabled）字段。`UserMapper` 有 `findByUsername`、`findById`、`insert`、`updateLastLoginAt`。`AuthService.register()` 硬编码 `role="teacher"`。

**告警截图**：`AnalysisService._save_snapshot()` 将帧写入 `static/snapshots/{day}/{event_id}.jpg`，返回 `/snapshots/{day}/{event_id}.jpg`。前端通过 `joinResourceUrl()` 拼接 `NGINX_BASE`（云服务器 Nginx 9092）访问截图，但文件在本地 AI 机器上，云服务器无此文件 → 404。Flask 未注册 `/snapshots` 路由。

**Flask 应用**：`create_app()` 在 `app.py` 中组装所有服务，`snapshot_root` 硬编码为 `BASE_DIR / "static" / "snapshots"`。配置通过 `config/app.yaml` + 环境变量覆盖。

## Goals / Non-Goals

**Goals:**

1. `@RequireRole` 注解 + `RequireRoleInterceptor` 实现方法级角色校验
2. 所有 Controller 按权限矩阵添加 `@RequireRole` 注解
3. 注册逻辑：首个用户自动 admin，后续 teacher
4. 用户管理 API（`GET/PUT/DELETE /users/**`），仅 admin 可访问
5. `UserMapper` 扩展：分页查询、角色更新、状态更新、软删除
6. AI 异步 SCP 推送截图到云服务器
7. Flask `/snapshots/<path:filename>` 本地 fallback 路由
8. `snapshot_remote` 配置节（app.yaml + 环境变量）

**Non-Goals:**

- 不引入 Spring Security 框架
- 不实现细粒度权限（按资源实例授权）
- 不修改前端代码
- 不自动化云服务器 Nginx 配置
- 不使用 OSS/S3 或数据库 BLOB 存储截图
- 不实现视频片段代理

## Decisions

| 决策                | 选择                                         | 理由                                                               |
| ------------------- | -------------------------------------------- | ------------------------------------------------------------------ |
| 权限实现方式        | 自定义 `@RequireRole` + `HandlerInterceptor` | 与现有 JWT 拦截器架构一致，轻量，不引入 Spring Security 复杂性     |
| 注解位置            | 方法级优先，类级作为默认                     | 大部分 Controller 读操作允许 teacher、写操作限 admin，方法级更灵活 |
| 拦截器顺序          | InternalToken → JWT → RequireRole            | 角色校验必须在身份认证之后                                         |
| 首个 admin 判断     | `UserMapper.countActive() == 0`              | 简单可靠，注册时一次查询即可                                       |
| 用户管理 API 路径   | `/users/**`                                  | RESTful 风格，与现有 `/students`、`/streams` 一致                  |
| 不能操作自己        | Service 层校验 currentUserId != targetId     | 防止管理员误删/禁用/改角色自己                                     |
| 截图推送方式        | SCP（subprocess 异步）                       | 零额外依赖，SCP 是标准文件传输方式，异步不阻塞告警管道             |
| SCP 认证            | 系统现有 SSH 配置（默认 key / ssh-agent）    | 用户已有公网 SSH 访问能力，无需额外配置密钥                        |
| 远程目录创建        | SSH `mkdir -p` 后 SCP                        | 确保日期子目录存在，避免 SCP 失败                                  |
| Flask fallback 路由 | `send_from_directory`                        | Flask 内置安全文件服务，自动防路径穿越                             |
| 配置方式            | app.yaml + 环境变量覆盖                      | 与现有 `spring.base_url` / `SPRING_BASE_URL` 模式一致              |

## RBAC 详细设计

### 1. @RequireRole 注解

```java
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface RequireRole {
    String[] value();
}
```

用法示例：

- `@RequireRole("admin")` — 仅 admin
- `@RequireRole({"admin", "teacher"})` — admin 和 teacher 均可
- 不标注 — 所有已认证用户均可（向后兼容）

### 2. RequireRoleInterceptor

```
请求进入
    │
    ▼
InternalTokenInterceptor.preHandle()
    │
    ▼
JwtAuthenticationInterceptor.preHandle()
    │  解析 JWT → currentUserId, currentUsername, currentRole
    │  存入 request attribute
    ▼
RequireRoleInterceptor.preHandle()
    │
    ├─ 获取 handler（HandlerMethod）
    ├─ 查找 @RequireRole 注解（方法级优先，其次类级）
    │     └─ 无注解 → 放行
    ├─ 读取 request.getAttribute("currentRole")
    ├─ role ∈ 注解.value[] → 放行
    └─ role ∉ 注解.value[] → 抛出 BusinessException(403, "权限不足")
```

关键实现细节：

- `handler` 参数类型为 `Object`，需 `instanceof HandlerMethod` 判断才能获取方法注解
- 方法级注解优先于类级注解（方法级可扩大权限范围，如类级 admin 但某方法允许 teacher）
- Internal token 请求（AI 内部调用）直接放行，不走角色校验

### 3. WebMvcConfig 拦截器注册

```java
registry.addInterceptor(internalTokenInterceptor).addPathPatterns("/**");
registry.addInterceptor(jwtInterceptor).addPathPatterns("/**");
registry.addInterceptor(requireRoleInterceptor).addPathPatterns("/**");
```

顺序：InternalToken → JWT → RequireRole，Spring 按注册顺序执行。

### 4. 各 Controller 注解方案

| Controller                | 类级注解                | 方法级覆盖（扩大权限）                               |
| ------------------------- | ----------------------- | ---------------------------------------------------- |
| `UserController`          | `@RequireRole("admin")` | 无（全部 admin）                                     |
| `AlertController`         | 无                      | 无（全部认证用户）                                   |
| `StudentController`       | 无                      | `POST`/`PUT`/`DELETE` 方法加 `@RequireRole("admin")` |
| `FaceController`          | 无                      | 无（人脸注册/查询允许 teacher）                      |
| `StreamController`        | 无                      | `POST`/`PUT`/`DELETE` 方法加 `@RequireRole("admin")` |
| `ZoneController`          | 无                      | `POST`/`PUT`/`DELETE` 方法加 `@RequireRole("admin")` |
| `RuleController`          | 无                      | `POST`/`PUT`/`DELETE` 方法加 `@RequireRole("admin")` |
| `RecordingController`     | 无                      | 无（只读）                                           |
| `OperationLogController`  | `@RequireRole("admin")` | 无                                                   |
| `ReportController`        | 无                      | `POST /report/generate` 加 `@RequireRole("admin")`   |
| `SystemController`        | 无                      | 无（health 已在 JWT 白名单）                         |
| `AuthController`          | 无                      | 无（login/register 已在 JWT 白名单）                 |
| `AiAlertController`       | 无                      | 无（Internal token 鉴权，不走角色校验）              |
| `AiFaceFeatureController` | 无                      | 无（Internal token 鉴权）                            |

### 5. 注册逻辑调整

```
AuthService.register(username, password, nickname)
      │
      ├─ 校验 username 唯一（现有逻辑）
      ├─ 判断 userMapper.countActive() == 0
      │     ├─ 是 → role = "admin"
      │     └─ 否 → role = "teacher"
      ├─ BCrypt 加密 → 插入 user
      └─ 生成 JWT（含 role）→ 返回 LoginResponse
```

`UserMapper` 新增：

```java
@Select("SELECT COUNT(*) FROM user WHERE deleted_at IS NULL")
long countActive();
```

### 6. 用户管理 API

#### UserController

```
@RestController
@RequestMapping("/users")
@RequireRole("admin")
public class UserController {

    GET  /users              → 分页列表（page, size, role, status 筛选）
    GET  /users/{id}         → 用户详情
    PUT  /users/{id}         → 更新 nickname、avatarUrl
    PUT  /users/{id}/role    → 变更角色（admin/teacher）
    PUT  /users/{id}/status  → 启用/禁用（enabled/disabled）
    DELETE /users/{id}       → 软删除（设 deleted_at）
}
```

#### UserService

```
UserService
    ├─ listUsers(page, size, role, status) → PageResult<UserVO>
    ├─ getUser(id) → UserVO
    ├─ updateUser(id, request) → UserVO
    ├─ updateRole(id, role, currentUserId) → void
    │     └─ 校验 id != currentUserId（不能改自己角色）
    │     └─ 校验 role ∈ {"admin", "teacher"}
    ├─ updateStatus(id, status, currentUserId) → void
    │     └─ 校验 id != currentUserId（不能禁用自己）
    │     └─ 校验 status ∈ {"enabled", "disabled"}
    └─ deleteUser(id, currentUserId) → void
          └─ 校验 id != currentUserId（不能删自己）
          └─ 设 deleted_at = now
```

#### UserMapper 扩展

```java
@Select("SELECT COUNT(*) FROM user WHERE deleted_at IS NULL")
long countActive();

@Select("SELECT * FROM user WHERE deleted_at IS NULL ORDER BY id DESC LIMIT #{offset}, #{size}")
List<User> findAll(@Param("offset") long offset, @Param("size") int size);

@Select("SELECT * FROM user WHERE role = #{role} AND deleted_at IS NULL ORDER BY id DESC LIMIT #{offset}, #{size}")
List<User> findByRole(@Param("role") String role, @Param("offset") long offset, @Param("size") int size);

@Select("SELECT * FROM user WHERE status = #{status} AND deleted_at IS NULL ORDER BY id DESC LIMIT #{offset}, #{size}")
List<User> findByStatus(@Param("status") String status, @Param("offset") long offset, @Param("size") int size);

@Select("SELECT COUNT(*) FROM user WHERE deleted_at IS NULL")
long countAll();

@Select("SELECT COUNT(*) FROM user WHERE role = #{role} AND deleted_at IS NULL")
long countByRole(@Param("role") String role);

@Select("SELECT COUNT(*) FROM user WHERE status = #{status} AND deleted_at IS NULL")
long countByStatus(@Param("status") String status);

@Update("UPDATE user SET role = #{role}, updated_at = NOW() WHERE id = #{id} AND deleted_at IS NULL")
int updateRole(@Param("id") Long id, @Param("role") String role);

@Update("UPDATE user SET status = #{status}, updated_at = NOW() WHERE id = #{id} AND deleted_at IS NULL")
int updateStatus(@Param("id") Long id, @Param("status") String status);

@Update("UPDATE user SET deleted_at = NOW() WHERE id = #{id} AND deleted_at IS NULL")
int softDelete(@Param("id") Long id);
```

#### 新增 DTO

- `UserUpdateRequest`：`nickname`（String, 可选）、`avatarUrl`（String, 可选）
- `UserRoleUpdateRequest`：`role`（String, 必填，校验 admin/teacher）
- `UserStatusUpdateRequest`：`status`（String, 必填，校验 enabled/disabled）

#### 新增 VO

- `UserVO`：`id`、`username`、`role`、`nickname`、`avatarUrl`、`status`、`lastLoginAt`、`createdAt`

## Snapshot 推送详细设计

### 1. 配置

`config/app.yaml` 新增：

```yaml
snapshot_remote:
  host: "" # 空 = 不推送
  user: "root"
  path: "/data/snapshots"
```

环境变量覆盖：`SNAPSHOT_REMOTE_HOST`、`SNAPSHOT_REMOTE_USER`、`SNAPSHOT_REMOTE_PATH`

`create_app()` 中读取：

```python
snapshot_remote = app_config.get("snapshot_remote", {})
remote_host = os.environ.get("SNAPSHOT_REMOTE_HOST") or snapshot_remote.get("host", "")
remote_user = os.environ.get("SNAPSHOT_REMOTE_USER") or snapshot_remote.get("user", "root")
remote_path = os.environ.get("SNAPSHOT_REMOTE_PATH") or snapshot_remote.get("path", "/data/snapshots")
```

### 2. snapshot_push.py

```python
class SnapshotPusher:
    def __init__(self, host: str, user: str, remote_path: str):
        self.host = host
        self.user = user
        self.remote_path = remote_path

    @property
    def enabled(self) -> bool:
        return bool(self.host)

    def push(self, local_path: Path, relative_path: str) -> None:
        """异步推送截图到云服务器"""
        if not self.enabled:
            return
        # 1. SSH mkdir -p 确保远程目录存在
        # 2. SCP 推送文件
        # 失败只 log warning，不抛异常
```

推送流程：

```
_save_snapshot(frame, event_id)
      │
      ├─ cv2.imwrite → 本地文件
      ├─ 返回 /snapshots/{day}/{event_id}.jpg
      │
      ▼ (异步，不阻塞)
SnapshotPusher.push(local_path, relative_path)
      │
      ├─ ssh {user}@{host} "mkdir -p {remote_path}/{day}"
      ├─ scp -o StrictHostKeyChecking=no {local_path} {user}@{host}:{remote_path}/{day}/{event_id}.jpg
      │
      ├─ 成功 → log.debug
      └─ 失败 → log.warning（不影响告警流程）
```

异步实现：使用 `threading.Thread(daemon=True)` 启动推送，不阻塞告警管道。

### 3. AnalysisService 集成

```python
class AnalysisService:
    def __init__(self, ..., snapshot_pusher: SnapshotPusher | None = None):
        self.snapshot_pusher = snapshot_pusher

    def _save_snapshot(self, frame, event_id):
        # 现有逻辑不变：保存本地，返回相对路径
        ...
        # 新增：异步推送
        if self.snapshot_pusher:
            self.snapshot_pusher.push_async(path, relative_path)
        return relative_path
```

### 4. Flask /snapshots 路由

```python
from flask import send_from_directory

@app.get("/snapshots/<path:filename>")
def serve_snapshot(filename):
    snapshot_dir = BASE_DIR / "static" / "snapshots"
    return send_from_directory(snapshot_dir, filename)
```

`send_from_directory` 自动处理路径穿越防护（`../` 会被拒绝）。

### 5. .env.example 更新

新增：

```env
# 截图远程推送配置（留空则不推送）
SNAPSHOT_REMOTE_HOST=
SNAPSHOT_REMOTE_USER=root
SNAPSHOT_REMOTE_PATH=/data/snapshots
```

## Risks / Trade-offs

- **[SCP 推送延迟]** 截图保存后到云服务器可访问有网络延迟 → 异步推送，前端加载截图时可能有短暂延迟（通常 < 1s），可接受
- **[SCP 推送失败]** 网络中断时截图只存本地 → 容错处理，log warning，后续可加定时重扫补推机制
- **[并发 SCP]** 高频告警场景下多个 SCP 进程 → 每次推送是独立 subprocess，OS 可并行处理，短期不会成为瓶颈
- **[首个 admin 竞争]** 两人同时注册，都判断 count=0 → DB 唯一键保证只有一个成功，第二个抛 409 用户名已存在（或如果用户名不同，两人都成 admin）→ 初版可接受，实际部署中首个注册是运维操作
- **[角色变更不即时生效]** 管理员变更用户角色后，该用户已持有的 JWT 仍含旧 role → 需用户重新登录获取新 JWT → 初版可接受，后续可加 JWT 黑名单

## Open Questions

- SCP 推送是否需要限流/队列：初版不做，每个推送独立 subprocess。如果告警频率极高（>10/s），可能需要改为队列 + 批量推送
- 是否需要定时补推机制（扫描本地有但远程缺失的截图）：初版不做，后续可加
- 用户管理是否需要操作日志记录：当前 `OperationLogService` 已有基础设施，用户管理操作应记录操作日志
