## Why

区域配置已完成，需要实现行为规则模块。规则是 AI 检测的判定依据（阈值、置信度、冷却时间），也是前端规则配置页的核心数据。

## What Changes

- 新增 `behavior_rule` 表
- `GET /rules`：按 `rule_type` 过滤
- `POST /rules`：新增规则
- `GET /rules/{id}`：规则详情
- `PUT /rules/{id}`：更新规则（**必须支持 `confidence_threshold` 和 `cooldown_seconds`**）
- `DELETE /rules/{id}`：软删除
- 修改后调 AI `/config/reload`（不阻断）
- 预置 9 种规则类型：phone_usage/flame_detected/danger_zone_intrusion/danger_zone_stay/danger_zone_approach/head_down/leave_seat/fall_detected/stream_offline
- **不加 /api/v1**

## Capabilities

### New Capabilities
- `rule-crud`: 行为规则增删改查 + AI 配置刷新联动

## Impact

- 新增表：`behavior_rule`
- 新增文件：Entity、Mapper、DTO、VO、Service、Controller
