## Why

AI 内部告警入库（`/alerts/ai`）已完成，需要前端告警列表、详情、状态处理和首页统计接口。

## What Changes

- `GET /alerts`：告警分页，支持 `time_range`、`alert_type`、`status`、`level`、`stream_id` 筛选
- `GET /alerts/{id}`：告警详情，返回 `snapshot_url` + `record_url` 相对路径
- `PUT /alerts/{id}/status`：状态流转（unhandled→processing→handled/false_alarm/ignored）
- `GET /alert-stats`：首页统计（今日告警数、未处理数、分类统计）
- 分页 `records/page/page_size/total`
- **不改 /alerts/ai**，**不暴露 /students/face-features**，**不硬编码 IP**

## Capabilities

### New Capabilities
- `alert-frontend`: 前端告警查询、详情、状态处理和统计

## Impact

- 修改文件：AlertEventMapper（追加查询方法）、新增 Service、Controller、VO
- 无新表
