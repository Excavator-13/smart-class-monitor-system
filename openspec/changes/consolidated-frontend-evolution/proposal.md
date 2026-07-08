# 前端演进变更合并说明

本文件合并了此前分散在多个 OpenSpec change 目录里的同名 `proposal.md` 内容，避免仓库中出现大量同名 Markdown 文件。

## 合并范围

本次合并覆盖以下已完成变更：

- `standardize-frontend-monitor-ui`：Vue 前端原型规范化实现。
- `refine-dashboard-density`：提升 AI 研判助手权重，并填充非实时监控页面空白。
- `refine-sky-interaction-and-module-layout`：恢复太阳/月亮交互，并重排非实时监控模块。
- `refine-idle-ambient-motion`：曾加入默认眨眼和氛围动效，后续已按用户要求收敛为单个盆栽。
- `refine-monitor-planter-only`：移除全局装饰，仅保留实时监控页单个盆栽。
- `refine-monitor-toolbar-and-planter-position`：调整盆栽位置和实时监控工具栏样式。
- `split-cloud-static-and-local-runtime`：拆分云端静态部署与本地接口网关。
- `add-manual-eye-care-theme-toggle`：将白天/黑夜模式改为用户点击切换，并增加整页护眼黑夜主题。
- `add-interactive-planter-watering`：新增盆栽浇水、成长和水壶光标交互。

## 总体动机

前端原型已经逐步从单页展示发展为可运行、可部署、可交互的 Vue 应用。为了让后续维护更清晰，需要将重复分散的变更文档合并为一组总文档，同时保留关键设计决策和完成记录。

## 当前实现范围

- 前端使用 Vue 3、Vite、Element Plus 和 Axios。
- 云服务器部署 `frontend/dist` 静态构建产物。
- 本地运行 `local-runtime` 接口网关，转发 `/api`、`/ai`、`/media`。
- 前端接口地址通过 `runtime-config.js` 运行时配置，不需要重新构建即可调整。
- 实时监控页包含视频区域、AI 研判助手、实时告警、规则概览和可交互盆栽。
- 白天/夜晚模式由用户点击切换，夜晚模式启用整页黑色护眼主题。
- 盆栽支持水壶光标、点击浇水、水滴反馈和多次浇水后的成长状态。
- 告警管理、区域规则、人脸库、系统状态页使用统一 KPI + 栅格卡片布局。

## 不做范围

- 不在前端内实现真实 Spring Boot、Flask、Nginx 服务。
- 不新增数据库结构。
- 不接入真实摄像头或 RTMP 推流。
- 不改变既有导航和主要页面结构。
- 不把本地接口地址硬编码进云端静态包。

## 影响模块

- `frontend`
- `local-runtime`
- `docs`
- `openspec`
