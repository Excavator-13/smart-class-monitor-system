## Why

视频源管理已就绪，需要实现区域配置模块。区域是 AI 检测（入侵、停留、接近预警）和告警关联的基础数据。

## What Changes

- 新增 `danger_zone` 表（含 `safe_distance` 接近预警参数）
- `GET /zones`：按 `stream_id`、`zone_type` 查询
- `POST /zones`：新增区域（归一化坐标）
- `GET /zones/{id}`：区域详情
- `PUT /zones/{id}`：修改区域 → 调 AI `/config/reload`
- `DELETE /zones/{id}`：软删除 → 调 AI `/config/reload`
- `GET /streams/{stream_id}/zones`：某视频源全部区域
- 坐标归一化 0-1，`zone_type`: danger/seat/phone_forbidden/roi
- **不加 /api/v1**，**不改已有接口**

## Capabilities

### New Capabilities
- `zone-crud`: 区域配置增删改查
- `zone-config-reload`: 区域变更后通知 AI 刷新配置

## Impact

- 新增表：`danger_zone`
- 新增文件：Entity、Mapper、DTO、VO、Service、Controller
- AiClient 追加：`reloadConfig(String streamId, List<String> items)`
