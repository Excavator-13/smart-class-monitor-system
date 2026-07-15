## Context

视频源 CRUD 已完成。区域配置是 AI 检测的基础数据。`danger_zone` 表已在详细设计 §5.7 定义完毕。`AiClient` 已有 `reloadFeatures()`，需追加 `reloadConfig()`。

## Goals / Non-Goals

**Goals:**
- danger_zone 表 + CRUD + 软删除
- coordinates 归一化 JSON（0-1 比例）
- 修改/删除后通知 AI reload config（不阻断）
- `GET /streams/{stream_id}/zones` 供 AI 同步

**Non-Goals:**
- 不实现规则和告警模块
- reload 失败不阻断 CRUD

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| coordinates 类型 | MySQL JSON + Java String | 易于序列化 |
| AI reload | 记日志，不阻断 | 详细设计 §7.4 |
| stream_id vs id | zones 用 `id` 管理 CRUD；`/streams/{stream_id}/zones` 用 stream_id | 与 streams 一致 |

## Risks

- **[坐标格式]** 前端传非归一化坐标 → 后端不校验数值范围，由前端保证
