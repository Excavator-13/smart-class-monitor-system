## 技术方案

### 前端

- 在 `frontend/src/App.vue` 中增加本地登录态：
  - 未登录展示认证界面。
  - 登录成功后展示现有监控应用。
  - 允许演示账号或接口失败时 mock 登录，避免阻塞演示。
- 认证界面采用左右分区：
  - 左侧展示系统名称、场景价值和安全能力。
  - 右侧为登录/注册表单。
- 登录表单字段：
  - `account`：手机号、用户名或工号。
  - `password`：密码。
  - `remember`：记住登录状态。
- 注册表单字段：
  - `phone`：手机号。
  - `password`：密码。
  - `confirmPassword`：确认密码。
  - `name`：用户姓名。
  - `role`：教师或管理员。
  - `remark`：申请说明。
- 手机号注册在当前后端文档中没有已确认接口，因此前端仅实现“注册申请/预留界面”，用于后续对接 `/users` 用户管理或团队确认后的注册接口。

### 接口调用

- 在 `frontend/src/services/smartClassApi.js` 中保留并扩展认证接口封装：
  - `login(payload)` → `POST /auth/login`
  - `getCurrentUser()` → `GET /auth/info`
  - `logout()` → `POST /auth/logout`，后端文档标记为待定，前端失败时可直接清除本地 Token
- 不将 `/auth/register/code`、`/auth/register` 写入正式接口封装；如后端后续确认，再通过新的 OpenSpec change 补充。
- 请求仍通过 `frontend/src/services/http.js` 的统一客户端。
- Token 存储在 `localStorage` 或 `sessionStorage`，并由 HTTP 拦截器自动携带。

### 状态管理

- 不引入额外状态库。
- 使用 Vue 组件内状态维护：
  - `isAuthenticated`
  - `currentUser`
  - `authMode`
  - `authForm`
  - `registerForm`

### 文档

- 扩充 `C:/Users/adwe2/Downloads/前端服务接口文档.md`：
  - 增加登录注册页面设计。
  - 增加认证接口明细。
  - 增加字段校验、状态流转、错误处理和 mock 兜底。

### 风险

- 后端认证接口实际字段可能与当前约定不同，前端需要通过服务层集中适配。
- 手机号注册接口尚未在后端文档中确认，当前实现只做前端预留和本地提示，不向后端提交注册请求。
- 当前项目没有路由，登录态切换采用组件条件渲染，后续多页面化时可迁移到路由守卫。
