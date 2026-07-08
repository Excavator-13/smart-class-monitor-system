## ADDED Requirements

### Requirement: 前端监控首页
系统必须提供 Vue 前端首页，用于展示单路教室实时监控、AI 标注、实时告警、AI 研判助手、规则概览和系统状态。
系统必须在后端服务未启动时仍展示 mock 降级内容，不得呈现纯白屏。

#### Scenario: 正常展示监控首页
- GIVEN 用户已经启动前端开发服务
- WHEN 用户访问 `http://127.0.0.1:5173/`
- THEN 系统展示智慧教室实时行为分析与安全监测系统首页
- AND 页面包含当前视频源、平均延迟、今日识别人数、待处理告警等指标
- AND 页面包含实时画面、实时告警、AI 研判助手和规则概览

#### Scenario: 后端服务不可用
- GIVEN SpringBoot、Flask 或 Nginx 服务未启动
- WHEN 前端请求业务数据、AI 摘要或视频流失败
- THEN 系统使用 mock 数据或演示画面继续展示页面
- AND 系统不得因为接口失败显示纯白屏

### Requirement: 接口配置与封装
系统必须通过环境变量或 Vite 代理配置访问 SpringBoot、Flask 和 Nginx 服务。
组件不得硬编码服务器 IP 地址。

#### Scenario: 从环境变量读取服务地址
- GIVEN `.env` 或 `.env.example` 配置了 `VITE_API_BASE`、`VITE_AI_BASE`、`VITE_NGINX_BASE`
- WHEN 前端调用业务接口、AI 接口或静态资源
- THEN 请求地址从统一服务层读取
- AND 组件代码不直接拼接服务器 IP

### Requirement: 启动与构建
系统必须提供适合 Windows + VS Code 的启动命令，避免 PowerShell 执行策略阻断 `npm.ps1`。

#### Scenario: 开发模式自动打开页面
- GIVEN 用户位于 `frontend` 目录
- WHEN 用户执行 `npm.cmd run dev:open`
- THEN Vite 开发服务启动
- AND 浏览器自动打开本地页面

#### Scenario: 构建生产产物
- GIVEN 依赖已经安装
- WHEN 用户执行 `npm.cmd run build`
- THEN 系统成功生成 `frontend/dist`
