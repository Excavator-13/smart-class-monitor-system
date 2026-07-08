## 技术方案

### 前端
- 使用 Vue 3 + Vite + Element Plus + Axios。
- 主界面位于 `frontend/src/App.vue`，覆盖实时监控、告警管理、区域规则、人脸库、系统状态等演示页面。
- 样式位于 `frontend/src/styles.css`，保留原型中的目标框、风险热力点、实时研判条和响应式布局。
- 启动入口位于 `frontend/index.html`，提供加载和错误兜底，避免脚本异常时纯白屏。

### 接口调用
- `frontend/src/services/http.js` 统一创建 `apiClient`、`aiClient`，并拼接 Nginx 静态资源地址。
- `frontend/src/services/smartClassApi.js` 封装业务接口，组件不直接写 API 路径细节。
- 后端未启动时通过 `safeGet` 返回 mock 数据，保证演示页面仍可展示。

### 配置
- `.env.example` 提供：
  - `VITE_API_BASE`
  - `VITE_AI_BASE`
  - `VITE_NGINX_BASE`
- `vite.config.js` 在开发模式配置 `/api`、`/ai`、`/media` 代理。
- `package.json` 提供 `dev:open`、`build`、`preview:open`。
- `start-dev.bat` 用于 Windows 用户一键启动。

### 风险
- 如果浏览器缓存了旧的 Vite 依赖预构建结果，可能需要删除 `node_modules/.vite` 后重启。
- 真实后端未启动时，视频流会进入演示 fallback 状态，这是预期行为。
- 当前页面仍是单文件主界面，后续功能扩张时应按模块拆分组件。
