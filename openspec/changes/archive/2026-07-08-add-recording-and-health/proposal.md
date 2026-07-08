## Why

录像查询和系统健康是后端闭环的最后两块拼图。前者供前端查看 Nginx 自动录像文件列表，后者统一返回各组件状态。

## What Changes

- 新增 `recording_file` 表
- `GET /recordings`：分页查询录像文件（按 stream_id/time_range/event_id 筛选）
- 增强 `GET /system/health`：除 backend+DB 外，增加 AI（`/model/status`）和 Nginx（`/stat`）探活
- AI/Nginx 不可用时标记 degraded/down，不抛 500
- 路径全部相对路径
- **只改 SpringBoot，不动前端/AI/Nginx**

## Capabilities

### New Capabilities
- `recording-query`: 录像文件分页查询
- `system-health-enhanced`: 增强健康检查（AI + Nginx 探活）

## Impact

- 新增表：`recording_file`（初版无自动写入机制）
- 修改：`SystemController`（增强 health）
- 新增：Entity、Mapper、VO、Service、Controller
