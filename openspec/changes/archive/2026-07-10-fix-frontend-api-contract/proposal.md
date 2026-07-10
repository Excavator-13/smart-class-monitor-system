# 前端接口契约对齐

## 动机

前端 `smartClassApi.js` 和 `mockData.js` 中存在多处接口字段名、数据结构与后端接口文档不一致的问题，导致联调时真实后端数据无法被正确读取或展示。经审查发现 11 处问题，其中 2 处为高严重度（数据丢失），需统一对齐。

## 范围

- 修正 `fetchAlertStats` 的字段名：`today_alerts` → `today_total`，`pending_alerts` → `unhandled_count`，对齐 SpringBoot 文档 §2.4。
- 修正 `fetchStreams` 返回的 `status` 字段语义混淆：文档定义为配置状态 `enabled`/`disabled`，前端误当推流状态 `online`/`offline` 使用；需改用 `GET /streams/{stream_id}/status` 获取在线状态，或调整 `onlineStreamCount` 计算逻辑。
- 修正 `fetchAlerts` / `fetchStudents` 的 fallback 结构：`list` → `records`，对齐 SpringBoot 分页格式 `PageResult`。
- 修正 `fetchAnalysisEvents` 的 fallback 数据：使用 AI 事件格式（`event_type`、`event_status`）而非 SpringBoot 告警格式（`alert_type`、`alert_status`）。
- 修正 `fetchSystemHealth` 的 mock 字段名：`api` → `backend`，对齐 SpringBoot 文档 §10.1。
- 移除 `fetchAlertStats` 中不支持的 `stream_id` 查询参数。
- 修正 Vite 代理 AI 服务 fallback 端口：`5000` → `5001`，对齐 AI 文档默认端口。
- 同步修正 `mockData.js` 中 mockStreams 的 `status` 值和 mockHealth 的字段名。

## 不做

- 不新增前端尚未调用的后端写操作接口（如 `PUT /alerts/{id}/status`、`POST /students/{id}/face`、`POST /streams` 等），这些属于功能补全，不在本次契约对齐范围内。
- 不改变 `getVideoFeedUrl` 的硬拼接方式为 `preview-url` 接口获取方式，仅记录为后续优化项。
- 不修改后端接口文档或后端代码。
- 不新增数据库表或后端接口。

## 影响模块

- frontend
