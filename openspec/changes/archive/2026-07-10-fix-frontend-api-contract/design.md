## Context

前端 `smartClassApi.js` 和 `mockData.js` 在开发初期基于推测编写了接口调用和 fallback 数据，与后端接口文档存在多处字段名、数据结构和语义不一致。经审查发现 11 处问题，其中 2 处（`fetchAlertStats` 字段名、`fetchStreams` status 语义）会导致真实后端数据无法正确展示。

## Goals / Non-Goals

**Goals:**

- 修正 `fetchAlertStats` 字段名为 `today_total` / `unhandled_count`
- 修正 `onlineStreamCount` 计算逻辑，区分配置状态与推流状态
- 修正分页 fallback 结构 `list` → `records`
- 修正 `fetchAnalysisEvents` fallback 使用 AI 事件格式
- 修正 `mockHealth` 字段名 `api` → `backend`
- 移除 `fetchAlertStats` 不支持的 `stream_id` 参数
- 修正 Vite 代理 AI 端口 `5000` → `5001`
- 补充 `mockAlerts` 缺失的 AlertVO 字段

**Non-Goals:**

- 不新增前端尚未调用的后端写操作接口（如 `PUT /alerts/{id}/status`、`POST /students/{id}/face` 等）
- 不改造 `getVideoFeedUrl` 为 `preview-url` 接口获取方式
- 不修改后端接口文档或后端代码
- 不新增数据库表或后端接口

## Decisions

| 决策                           | 选择                                                                                 | 理由                                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| `onlineStreamCount` 计算方式   | 改为统计 `status === "enabled"` 的视频源数量                                         | `GET /streams` 返回的是配置状态，逐个调用 `/streams/{stream_id}/status` 开销过大，系统页面已有独立状态展示 |
| `normalizeHealth` 字段映射     | 保留 `payload.backend` 兜底，mock 改用 `backend`                                     | 兼容已部署版本，同时 mock 对齐文档                                                                         |
| `fetchAnalysisEvents` fallback | 新建 `mockAnalysisEvents` 替代 `mockAlerts.slice(0, 2)`                              | AI 事件与 SpringBoot 告警是不同数据结构，不应复用                                                          |
| `fetchAlertStats` 调用方式     | 移除 `stream_id` 参数                                                                | 文档未定义此参数，后端会忽略                                                                               |
| Vite 代理端口                  | 改为 `5001`                                                                          | AI 文档 `config/app.yaml` 默认端口为 `5001`                                                                |
| `mockAlerts` 补充字段          | 添加 `stream_name`、`student_id`、`student_name`、`handled_at`、`remark`（nullable） | 对齐 AlertVO 定义，避免详情展示缺失                                                                        |

## Risks / Trade-offs

- **[onlineStreamCount 语义变化]** 改为统计 `enabled` 后，指标含义从"在线推流数"变为"已启用配置数"，系统页面已有独立的推流状态展示 → 可接受，指标卡片标签可同步调整
- **[normalizeHealth 双字段兼容]** 保留 `payload.api || payload.backend` 兼容逻辑 → 如果后端未来也改用 `api` 字段名，需再调整；当前以文档为准
- **[mockAnalysisEvents 新增]** 新增 mock 数据增加维护成本 → 数据量小（2-3 条），结构简单

## Open Questions

- `onlineStreamCount` 指标卡片标签是否需要从"在线视频源"改为"已启用视频源"？→ 建议改为"已启用视频源"，避免语义歧义
