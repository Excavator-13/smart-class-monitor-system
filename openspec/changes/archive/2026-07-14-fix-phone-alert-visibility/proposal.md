## Why

手机使用事件能够确认并入库，但实时黄色框只显示单个检测帧，SpringBoot `/alerts` 又未返回已保存的 `target_info`，导致前端区域二次校验把数据库中的手机告警过滤掉；同时旧调用仍请求不存在的 `/events`。

## What Changes

- 已确认的手机目标框在视频中短时保持显示。
- `/alerts` 列表和详情返回 `target_info`、`zone_id`，前端可恢复目标框。
- 前端信任已由 AI 命中禁用区并入库的 `phone_usage`，无目标框的历史记录也不再消失。
- AI 提供 `/events` 到 `/analysis/events` 的兼容查询别名。

## Capabilities

### Modified Capabilities
- `ai-detection-stability`: 手机确认框保持及事件查询兼容。
- `frontend-api-contract`: 入库手机告警必须在告警管理中可见。

## Impact

涉及 Flask AI、SpringBoot AlertVO/服务映射、Vue 告警过滤与接口文档；不修改数据库结构。
