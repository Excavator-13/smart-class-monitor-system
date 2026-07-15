# Spec: Frontend Evolution

## Requirements

### Requirement: Static Cloud Frontend

前端静态构建产物 SHOULD 能部署到云服务器。

#### Scenario: Build frontend

- GIVEN 用户在 `frontend` 目录执行 `npm.cmd run build`
- THEN `frontend/dist` SHOULD 生成可部署静态资源
- AND `runtime-config.js` SHOULD 随静态包输出

### Requirement: Local Runtime Gateway

接口转发 SHOULD 由本地网关承担。

#### Scenario: Local gateway

- GIVEN 用户启动 `local-runtime/local-gateway.mjs`
- THEN `/api` SHOULD 转发到业务后端
- AND `/ai` SHOULD 转发到 AI 服务
- AND `/media` SHOULD 转发到媒体服务

### Requirement: Manual Eye-care Theme

白天/黑夜模式 MUST 由用户点击切换。

#### Scenario: Toggle night mode

- GIVEN 用户点击顶部太阳/月亮组件
- THEN 页面 SHOULD 在白天模式和黑色护眼模式之间切换

### Requirement: Interactive Monitor Planter

实时监控页 SHOULD 展示可交互盆栽。

#### Scenario: Water planter

- GIVEN 用户将鼠标移动到盆栽附近
- THEN 鼠标 SHOULD 显示为水壶光标
- WHEN 用户点击盆栽
- THEN 页面 SHOULD 显示水滴反馈
- AND 植物 SHOULD 随浇水次数逐步成长

### Requirement: Balanced Dashboard Pages

非实时监控模块 SHOULD 使用整洁、均衡的栅格布局。

#### Scenario: View module page

- GIVEN 用户进入告警管理、区域规则、人脸库或系统状态页面
- THEN 页面 SHOULD 展示 KPI 卡片
- AND 主体内容 SHOULD 使用统一栅格排版
