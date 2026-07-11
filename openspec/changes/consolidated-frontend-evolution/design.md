# 前端演进设计合并说明

本文件合并此前多个 `design.md` 的内容，只保留当前仍然有效的设计决策。

## 前端结构

- 主界面位于 `frontend/src/App.vue`。
- 样式位于 `frontend/src/styles.css`。
- API 封装位于 `frontend/src/services/http.js` 和 `frontend/src/services/smartClassApi.js`。
- Mock 数据位于 `frontend/src/data/mockData.js`。
- 构建入口位于 `frontend/index.html`。

## 接口与部署

- 云端只部署 `frontend/dist` 静态资源。
- `frontend/public/runtime-config.js` 会复制到 `dist/runtime-config.js`，用于运行时指定接口地址。
- 本地非静态逻辑放在 `local-runtime/local-gateway.mjs`。
- 本地网关默认监听 `127.0.0.1:18080`，分别转发业务后端、AI 服务和媒体资源。

## 页面布局

- 实时监控页保持视频为主视图，右侧展示 AI 研判、告警、规则和盆栽。
- AI 研判助手作为重点模块放大展示。
- 非实时监控页面统一采用：
  - `page-kpis`：顶部四个 KPI 卡片。
  - `module-board`：12 栅格内容区。
  - `span-*`：控制卡片横向占比。

## 白天 / 夜晚模式

- 模式不再跟随系统时间。
- 顶部太阳/月亮组件是用户可点击按钮。
- 白天模式使用明亮背景和太阳形态。
- 夜晚模式给最外层添加 `eye-care-theme`，切换整页深色护眼风格。
- 太阳和月亮保留默认眨眼、悬停表情和视觉反馈。

## 实时监控工具栏

- 视频面板右上角采用紧凑图标工具栏。
- 工具栏按钮比普通图标按钮略宽，但不拉成长条。
- 操作通过 `title` 提示含义，避免长文字按钮破坏布局。

## 盆栽交互

- 盆栽位于实时监控右下角空白区域中间，并整体略向下放置。
- 盆栽区域是可点击按钮，但不影响其他业务操作。
- 鼠标悬停显示水壶光标。
- 点击后触发水滴动画。
- 盆栽有 `growth-0` 到 `growth-4` 五档成长状态，多次浇水后叶片逐渐变多、变大。

## 已废弃设计

- 全局鱼、蝴蝶、波浪、多处植物氛围层已移除。
- 按系统时间自动切换白天/黑夜已移除。
- 实时监控长文字按钮已替换为短图标工具栏。
