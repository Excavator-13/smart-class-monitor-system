# 前端打磨与缺陷修复

## 动机

前端经过多轮迭代，存在以下 6 个需修复/改进的问题：

1. **注册未接入后端**：后端 `POST /auth/register` 已实现（`add-auth-register` change），但前端注册表单仍走 `submitRegisterRequest` 占位逻辑，仅弹出"手机号注册接口尚未确认"提示后切回登录页，无法真正创建账户。
2. **"规则配置"按钮冗余**：顶部 header 中有独立的"规则配置"按钮，但左侧导航已有"区域规则"入口，功能完全重复，应移除。
3. **AI 研判助手事件流重复**：`activeRiskEvents` 合并了 `alerts` 和 `analysisEvents`，`uniqueEvents` 按 `eventIdentity` 去重，但 AI 服务和 SpringBoot 对同一事件可能使用不同 `event_id`（AI 用 `event_id`，SpringBoot 用自增 `id`），导致同一物理事件出现两条记录，其中一条无评分（`risk_score = 0`），事件流中显示重复。应只保留有评分的版本。
4. **告警管理页证据通路未打通**：`snapshot_url` 字段已从后端 `/alerts` 返回（AI 服务截图后写入 `snapshot_path`，SpringBoot 映射为 `snapshot_url`），但 AI 服务截图保存路径为 `/snapshots/{day}/{event_id}.jpg`，需要 Nginx 静态服务映射才能访问。截图本身已可工作，前端也已用 `joinResourceUrl` 拼接 Nginx 地址，但当前 AI 告警入库时 `snapshot_path` 可能为空（AI 服务未配置 `snapshot_root` 时跳过截图保存）。需要确保 AI 服务截图保存路径正确入库，前端截图链接可用。视频片段（`record_url`）较难实现，暂不处理。
5. **区域规则页"暂无坐标"**：后端 `ZoneVO.coordinates` 是 JSON 字符串（如 `"[{\"x\":0.1,\"y\":0.2}]"`），但前端 `normalizeZone` 直接取 `item.coordinates || item.points || []`，未对 JSON 字符串做 `JSON.parse`，导致 `Array.isArray(zone.coordinates)` 为 `false`，`zoneCoordinateText` 返回"暂无坐标"。
6. **PPT 式/Demo 式内容**：多个页面存在纯展示性、无实际功能的占位模块，对用户和开发者均无价值，应清理：
   - 实时监控页"前端呈现模块"面板（`activeModules`，4 条纯文字描述）
   - 告警管理页"处置建议"面板（`handlingGuides`，3 条静态文字）
   - 告警管理页"证据链概览"面板（3 条静态文字卡片）
   - 告警管理页"处理节奏"面板（3 步静态流程图）
   - 区域规则页"推荐模板"面板（`ruleTemplates`，3 条静态文字）
   - 区域规则页"规则联动"面板（3 步静态流程图）
   - 区域规则页"实时禁用区坐标"面板（JSON 导出展示）
   - 区域规则页"区域示意"面板（CSS 画出的教室示意图，非真实数据）
   - 人脸库页"陌生人核验"面板（占位人脸框 + 静态文字）
   - 人脸库页"身份策略"面板（2 条静态文字）
   - 系统状态页"依赖调用链路"面板（`dependencySteps`，4 步静态流程图）
   - 系统状态页"运行提示"面板（`operationLogs`，3 条静态文字）

## 范围

### 注册接入后端

- `smartClassApi.js` 新增 `register(username, password, nickname?)` 函数，调用 `POST /auth/register`
- `App.vue` 重写 `submitRegisterRequest` 为 `submitRegister`，调用 `register` API
- 注册表单字段对齐后端 DTO：`username`（替代 `phone`）、`password`、`nickname`（替代 `name`），移除 `role`、`confirmPassword`、`remark`
- 注册成功后自动登录（后端返回 JWT + 用户信息，与登录响应格式一致），无需再手动跳转登录
- 注册失败时展示后端错误信息（用户名已存在 → 409、参数校验失败 → 400）

### 移除"规则配置"按钮

- 删除 header 中 `<el-button :icon="Setting" @click="activePage = 'rules'">规则配置</el-button>`

### AI 研判事件流去重

- `activeRiskEvents` 计算逻辑调整：对合并后的事件列表，当存在 `event_id` 相同但来源不同（AI vs SpringBoot）的记录时，优先保留有 `risk_score > 0` 的版本；若均有评分，保留置信度更高的版本
- 事件流 `aiEventFeed` 只显示有评分的事件

### 告警截图通路

- 前端侧：确保 `normalizeAlert` 正确映射 `snapshot_url`，`evidenceSummary` 和截图按钮逻辑已正确，无需修改
- 后端侧：确认 AI 服务 `snapshot_root` 配置正确，截图保存后路径写入 `snapshot_path` 字段并随 `/alerts/ai` 入库
- 本次不实现视频片段功能，`record_url` 按钮保持 disabled 状态

### 区域坐标解析修复

- `normalizeZone` 中对 `coordinates` 字段做 `JSON.parse`：若为字符串则解析为数组
- 修复后 `zoneCoordinateText` 能正确显示坐标

### 清理 PPT/Demo 式内容

- 移除以下数据定义及其模板引用：
  - `activeModules`、`handlingGuides`、`ruleTemplates`、`dependencySteps`、`operationLogs`
  - `registrationSteps`（人脸库页"注册进度"面板）
- 移除以下模板区块：
  - 实时监控页"前端呈现模块"面板
  - 告警管理页"处置建议"、"证据链概览"、"处理节奏"面板
  - 区域规则页"推荐模板"、"规则联动"、"实时禁用区坐标"、"区域示意"面板
  - 人脸库页"陌生人核验"、"身份策略"、"注册进度"面板
  - 系统状态页"依赖调用链路"、"运行提示"面板
- 保留有实际功能的模块：告警评分配置、区域规则配置、区域表格、视频源列表、运行概览、值守小狗等

## 不做

- 不实现视频片段（`record_url`）的自动录制和关联
- 不新增后端接口或数据库表
- 不修改后端已有接口的行为
- 不修改 AI 服务的截图保存逻辑（仅确认配置正确）
- 不重新设计页面布局（仅移除冗余模块后自然收缩）
- 不修改 CSS 样式

## 影响模块

- frontend（`App.vue`、`smartClassApi.js`）
- 不涉及后端代码修改
