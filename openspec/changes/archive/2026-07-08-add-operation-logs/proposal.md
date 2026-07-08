## Why

需要操作审计能力，记录关键操作（登录、CRUD 视频源/人员/区域/规则、人脸注册、告警处理等），支持管理员追溯。

## What Changes

- 新增 `operation_log` 表
- `GET /operation-logs`：分页查询，支持 `user_id`/`action`/`target_type`/`target_id`/`time_range` 筛选
- 初版手动记录关键操作（Service 层调用 `OperationLogService`），后续 AOP 扩展
- 敏感数据脱敏：不记录 password、token、feature_vector
- 分页：`records/page/page_size/total`

## Capabilities

### New Capabilities
- `operation-log-query`: 操作日志分页查询 + 手动记录

## Impact

- 新增表：`operation_log`
- 新增文件：Entity、Mapper、VO、Service、Controller
