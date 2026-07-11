## ADDED Requirements

### Requirement: Frontend Authentication Entry

前端 MUST 提供登录入口和手机号注册预留入口，并在用户未登录时阻止直接展示监控主界面。

#### Scenario: View login entry

- GIVEN 用户打开前端页面
- WHEN 本地没有有效登录状态
- THEN 页面 SHOULD 展示登录/注册入口
- AND 页面 SHOULD 提供用户登录表单
- AND 页面 SHOULD 提供手机号注册/申请注册切换入口

#### Scenario: User login

- GIVEN 用户停留在登录表单
- WHEN 用户输入账号和密码并提交
- THEN 前端 SHOULD 调用 `POST /auth/login`
- AND 登录成功后 SHOULD 保存 Token 和用户信息
- AND 页面 SHOULD 进入智慧教室监控主界面

#### Scenario: Phone registration reserved flow

- GIVEN 用户切换到手机号注册表单
- WHEN 用户填写手机号、姓名、角色和密码信息并提交
- THEN 页面 SHOULD 提示手机号注册接口尚待后端确认
- AND 页面 SHOULD 引导用户联系管理员或返回登录
- AND 前端 MUST NOT 调用未在后端文档中确认的 `/auth/register` 或 `/auth/register/code`

#### Scenario: Auth API unavailable

- GIVEN 后端认证接口暂不可用
- WHEN 用户在演示环境提交登录
- THEN 页面 SHOULD 使用 mock 登录兜底
- AND 页面 SHOULD 避免白屏
- AND 页面 SHOULD 提示当前处于演示登录状态
