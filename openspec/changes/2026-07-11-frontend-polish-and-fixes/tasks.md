## 1. 注册接入后端

- [ ] 1.1 `smartClassApi.js` 新增 `register` 函数，调用 `POST /auth/register`，请求体 `{ username, password, nickname }`，返回 `unwrapResponse(data)`
- [ ] 1.2 `App.vue` import 中添加 `register`
- [ ] 1.3 `registerForm` 字段改为 `{ username: "", password: "", nickname: "" }`
- [ ] 1.4 重写 `submitRegisterRequest` → `submitRegister`：前端校验用户名 ≥ 2 字符、密码 ≥ 6 字符 → 调用 `register` → 复用 `enterAuthenticatedApp` 自动登录 → 错误时展示后端 message
- [ ] 1.5 注册表单模板：移除 `phone`/`name`/`role`/`confirmPassword`/`remark` 字段，改为 `username`/`password`/`nickname`（可选）输入框
- [ ] 1.6 注册 tab 标题从"手机号注册预留"改为"用户注册"，描述文案更新
- [ ] 1.7 注册按钮 `@click` 从 `submitRegisterRequest` 改为 `submitRegister`

## 2. 移除"规则配置"按钮

- [ ] 2.1 删除 header 中 `<el-button :icon="Setting" @click="activePage = 'rules'">规则配置</el-button>`

## 3. AI 研判事件流去重

- [ ] 3.1 新增 `deduplicateCrossSourceEvents(events)` 函数：按 `event_type/alert_type` + `stream_id` + `occurred_at`（5 秒容差）匹配，优先保留 `risk_score > 0` 的版本，均有评分则保留 `confidence` 更高的
- [ ] 3.2 `activeRiskEvents` 计算逻辑：在 `uniqueEvents` 之后追加 `deduplicateCrossSourceEvents` 调用
- [ ] 3.3 `aiEventFeed` 过滤：只包含 `risk_score > 0` 的事件

## 4. 告警截图通路确认

- [ ] 4.1 确认 AI 服务 `snapshot_root` 配置正确（`app.py` 中 `snapshot_root=BASE_DIR / "static" / "snapshots"`）
- [ ] 4.2 简化 `evidenceSummary`：只区分"已保存告警截图"和"未生成证据文件"，移除"截图与录像片段已关联"和"已关联录像路径"分支

## 5. 区域坐标解析修复

- [ ] 5.1 `smartClassApi.js` 新增 `parseCoordinates(value)` 辅助函数：数组直接返回，字符串做 `JSON.parse`（try/catch 回退 `[]`），其他返回 `[]`
- [ ] 5.2 `normalizeZone` 中 `coordinates` 字段改用 `parseCoordinates(item.coordinates || item.points)`

## 6. 清理 PPT/Demo 式内容

- [ ] 6.1 删除数据定义：`activeModules`、`handlingGuides`、`ruleTemplates`、`dependencySteps`、`operationLogs`
- [ ] 6.2 删除计算属性：`registrationSteps`
- [ ] 6.3 删除实时监控页"前端呈现模块"面板模板
- [ ] 6.4 删除告警管理页"处置建议"面板模板
- [ ] 6.5 删除告警管理页"证据链概览"面板模板
- [ ] 6.6 删除告警管理页"处理节奏"面板模板
- [ ] 6.7 删除区域规则页"推荐模板"面板模板
- [ ] 6.8 删除区域规则页"规则联动"面板模板
- [ ] 6.9 删除区域规则页"实时禁用区坐标"面板模板
- [ ] 6.10 删除区域规则页"区域示意"面板模板
- [ ] 6.11 删除人脸库页"陌生人核验"面板模板
- [ ] 6.12 删除人脸库页"身份策略"面板模板
- [ ] 6.13 删除人脸库页"注册进度"面板模板
- [ ] 6.14 删除系统状态页"依赖调用链路"面板模板
- [ ] 6.15 删除系统状态页"运行提示"面板模板

## 7. 编译与验证

- [ ] 7.1 运行前端构建，确认无编译错误
- [ ] 7.2 验证注册流程：新用户注册 → 自动登录 → 进入主界面
- [ ] 7.3 验证注册失败：重复用户名 → 显示 409 错误；空用户名/短密码 → 前端拦截
- [ ] 7.4 验证 header 无"规则配置"按钮，左侧导航"区域规则"仍可用
- [ ] 7.5 验证 AI 研判事件流无重复条目，零评分事件不在 feed 中显示
- [ ] 7.6 验证告警截图按钮：有 `snapshot_url` 时可点击打开，无时 disabled
- [ ] 7.7 验证区域规则页：后端返回 JSON 字符串坐标时，表格正确显示坐标值而非"暂无坐标"
- [ ] 7.8 验证各页面 Demo 面板已移除，有实际功能的面板仍正常工作
