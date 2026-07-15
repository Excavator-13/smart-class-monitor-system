## Context

`alert_event` 表已在 `add-ai-internal-apis` 创建。本 change 只追加 Mapper 查询方法和前端 Controller，不新增表。

## Goals / Non-Goals

**Goals:**
- 前端告警分页列表（多条件筛选）
- 告警详情（含关联视频源名称、学生姓名）
- 状态流转（校验 + 记录处理信息）
- 首页统计卡片数据

**Non-Goals:**
- 不改 `/alerts/ai`
- 不实现告警导出、误报反馈
- 不实现 WebSocket 实时推送

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 分页方式 | SQL LIMIT/OFFSET | 告警数据可能多，用数据库分页 |
| 统计 | SQL COUNT + GROUP BY | 一次查询完成 |
| 状态校验 | Service 层白名单校验 | 简单可靠 |
| 字段名 | 返回 `snapshot_url`(←snapshot_path) + `record_url`(←record_path) | 与接口文档 §5.6 一致 |
