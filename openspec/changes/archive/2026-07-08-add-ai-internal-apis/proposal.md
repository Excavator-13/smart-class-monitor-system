## Why

AI 服务需要两个专用接口：告警入库（`/alerts/ai`）和人脸特征同步（`/students/face-features`）。`/students/face-features` 已在 `add-student-face-register` 中创建，本 change 检查其完整性并实现 `/alerts/ai`。

## What Changes

- 新增 `alert_event` 数据库表 DDL
- 新增 `POST /alerts/ai`：AI 写入确认告警，**`event_id` 幂等**（相同 event_id 不重复插入）
- 检查并确认 `GET /students/face-features` 满足 AI 使用（已实现）
- 检查 `GET /streams`、`/zones`、`/rules` 返回字段满足 AI 配置拉取
- 新增 `InternalTokenInterceptor`：AI 内部接口使用 `X-Internal-Token` 鉴权，与前端 JWT 分离
- `snapshot_path`、`record_path` 校验：只允许相对路径（以 `/` 开头）
- **不改成 `/internal/ai/**`**，**不改成 `event_uid`**
- **不实现前端告警列表/详情/状态处理**

## Capabilities

### New Capabilities
- `ai-alert-ingest`: AI 告警入库（POST /alerts/ai，event_id 幂等）
- `ai-internal-auth`: AI 内部接口鉴权（X-Internal-Token，与前端 JWT 分离）

## Impact

- 新增表：`alert_event`
- 新增文件：Entity、Mapper、Service、Controller (controller.ai)、InternalTokenInterceptor
- 修改：JwtAuthenticationInterceptor 放行 `/alerts/ai`
