# Spec: Frontend

## Requirements

### Requirement: Frontend Monitor UI

前端 MUST 提供智慧教室实时监控主界面。

#### Scenario: View monitor page

- GIVEN 用户打开前端页面
- THEN 页面 SHOULD 展示实时监控入口
- AND 页面 SHOULD 展示视频画面、AI 研判、实时告警、规则概览等核心模块

### Requirement: API Access Layer

前端 MUST 通过统一服务层访问接口。

#### Scenario: Call backend APIs

- GIVEN 页面需要获取视频源、告警、规则、学生或系统状态
- THEN 组件 SHOULD 调用 `frontend/src/services/smartClassApi.js`
- AND API 基础地址 SHOULD 来自运行时配置、环境变量或默认相对路径

### Requirement: Runtime Fallback

后端不可用时，前端 SHOULD 仍能展示演示页面。

#### Scenario: API unavailable

- GIVEN 后端接口暂不可用
- WHEN 前端请求失败
- THEN 页面 SHOULD 使用 mock 数据兜底
- AND 页面 SHOULD 避免白屏

### Requirement: Dashboard Density

前端非实时监控页面 SHOULD 保持信息密度和布局均衡。

#### Scenario: View non-monitor pages

- GIVEN 用户进入告警管理、区域规则、人脸库或系统状态页面
- THEN 页面 SHOULD 展示 KPI 区域
- AND 主体内容 SHOULD 使用统一栅格布局
- AND 留白 SHOULD 尽量均衡、不突兀

### Requirement: Theme Toggle

白天/夜晚模式 MUST 由用户手动切换。

#### Scenario: Toggle eye-care mode

- GIVEN 用户点击顶部太阳/月亮组件
- THEN 页面 SHOULD 在白天模式和黑色护眼模式之间切换

### Requirement: Interactive Planter

实时监控页 SHOULD 提供盆栽交互。

#### Scenario: Water planter

- GIVEN 用户将鼠标移动到盆栽附近
- THEN 光标 SHOULD 显示为水壶样式
- WHEN 用户点击盆栽
- THEN 页面 SHOULD 显示水滴反馈
- AND 植物 SHOULD 随浇水次数逐步成长

### Requirement: Deployment Split

前端 MUST 支持云端静态部署和本地非静态接口网关拆分。

#### Scenario: Deploy static frontend

- GIVEN 用户执行 `npm.cmd run build`
- THEN `frontend/dist` SHOULD 生成可部署到云服务器的静态资源
- AND `runtime-config.js` SHOULD 可独立修改接口地址

#### Scenario: Run local gateway

- GIVEN 用户启动 `local-runtime/local-gateway.mjs`
- THEN `/api`、`/ai`、`/media` SHOULD 被转发到本地对应服务
