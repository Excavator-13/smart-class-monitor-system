## Context

前端 `App.vue`（单文件组件，~3200 行）和 `smartClassApi.js` 经过多轮迭代，积累了 6 类问题：注册占位逻辑未接入真实后端、冗余导航按钮、AI 事件流跨源重复、告警截图通路未完全打通、区域坐标 JSON 字符串未解析、以及大量纯展示性 PPT/Demo 模块。

后端 `POST /auth/register` 已在 `add-auth-register` change 中实现，接收 `{ username, password, nickname? }`，返回 `LoginResponse`（JWT + 用户信息），与 `POST /auth/login` 响应格式完全一致。前端 `smartClassApi.js` 已有 `login` 函数作为参考模式。

AI 服务 `analysis_service.py` 已实现截图保存（`_save_snapshot`），路径格式为 `/snapshots/{day}/{event_id}.jpg`，通过 `alert_client.py` 写入 `snapshot_path` 字段。SpringBoot `AlertService.mapToAlertVO` 已将 `snapshot_path` 映射为 `snapshot_url`。前端 `normalizeAlert` 和 `joinResourceUrl` 已正确处理。截图通路的前端侧无需修改，仅需确认 AI 服务 `snapshot_root` 配置正确。

区域坐标问题：后端 `ZoneVO.coordinates` 是 JSON 字符串（MyBatis 映射 `VARCHAR` → Java `String` → Jackson 序列化为 JSON 字符串），前端 `normalizeZone` 未做 `JSON.parse`，导致 `Array.isArray` 判断为 `false`。

## Goals / Non-Goals

**Goals:**

- 前端注册表单对接 `POST /auth/register`，注册成功后自动登录
- 移除 header "规则配置"按钮
- AI 研判事件流跨源去重，只显示有评分的事件
- 确认告警截图通路完整可用
- 修复 `normalizeZone` 对 `coordinates` JSON 字符串的解析
- 移除 12 个纯展示性 PPT/Demo 面板及对应数据定义

**Non-Goals:**

- 不实现视频片段（`record_url`）的自动录制和关联
- 不新增后端接口或数据库表
- 不修改后端代码
- 不修改 AI 服务截图保存逻辑
- 不重新设计页面布局或修改 CSS
- 不移除值守小狗动图

## Decisions

| 决策               | 选择                                                                                         | 理由                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 注册后自动登录     | 复用 `enterAuthenticatedApp`，与登录流程一致                                                 | 后端 `POST /auth/register` 返回 `LoginResponse`，与登录响应格式相同，无需额外登录请求        |
| 注册表单字段       | `username` + `password` + `nickname`（可选），移除 `phone`/`role`/`confirmPassword`/`remark` | 对齐后端 `RegisterRequest` DTO，降低注册门槛                                                 |
| 注册前端校验       | 用户名非空且 ≥ 2 字符、密码非空且 ≥ 6 字符                                                   | 与后端校验对齐，前端先拦截明显无效输入，减少无效请求                                         |
| 事件去重匹配键     | `event_type/alert_type` + `stream_id` + `occurred_at`（5 秒容差）                            | AI 和 SpringBoot 对同一事件使用不同 `event_id`，无法按 ID 去重；按类型+视频源+时间匹配最可靠 |
| 去重保留策略       | 优先保留 `risk_score > 0` 的版本；均有评分则保留 `confidence` 更高的                         | 无评分版本对用户无价值，有评分版本才有研判意义                                               |
| `aiEventFeed` 过滤 | 只显示 `risk_score > 0` 的事件                                                               | 零评分事件（如不在禁用区的手机违规）不应出现在事件流                                         |
| 坐标解析           | `normalizeZone` 中对字符串 `coordinates` 做 `JSON.parse`，失败回退 `[]`                      | 最小改动修复问题，兼容已解析的数组（mock 数据）和字符串（真实后端）                          |
| 截图通路           | 前端侧无需修改，确认 AI 服务 `snapshot_root` 配置正确即可                                    | 前端 `normalizeAlert` → `snapshot_url`、`joinResourceUrl` → Nginx 拼接、截图按钮逻辑均已正确 |
| 录像按钮           | 保持 disabled                                                                                | 视频片段功能实现复杂度高，不在本次范围                                                       |
| `evidenceSummary`  | 简化为只区分"已保存告警截图"和"未生成证据文件"                                               | 录像不可用，"截图与录像片段已关联"和"已关联录像路径"文案无实际意义                           |
| Demo 内容移除      | 删除模板和数据定义，不留空壳                                                                 | 空壳 div 仍占布局空间，完全移除更干净                                                        |
| 值守小狗           | 保留                                                                                         | 用户明确要求保留                                                                             |

## 修改清单

### smartClassApi.js

1. 新增 `register` 函数：

```
export async function register(payload) {
  const data = await requestData(apiClient, {
    method: "post",
    url: "/auth/register",
    data: {
      username: payload.username,
      password: payload.password,
      nickname: payload.nickname || undefined
    }
  });
  return unwrapResponse(data);
}
```

2. `normalizeZone` 修改 `coordinates` 解析：

```
coordinates: parseCoordinates(item.coordinates || item.points),
```

新增 `parseCoordinates` 辅助函数：

```
function parseCoordinates(value) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string" && value.trim()) {
    try { return JSON.parse(value); } catch { return []; }
  }
  return [];
}
```

### App.vue — Script

3. `registerForm` 字段改为：

```
{ username: "", password: "", nickname: "" }
```

4. 重写 `submitRegisterRequest` → `submitRegister`：

```
async function submitRegister() {
  if (!registerForm.value.username || registerForm.value.username.length < 2) {
    setAuthNotice("用户名至少 2 个字符。", "warning");
    return;
  }
  if (!registerForm.value.password || registerForm.value.password.length < 6) {
    setAuthNotice("密码至少 6 个字符。", "warning");
    return;
  }
  authLoading.value = true;
  setAuthNotice("");
  try {
    const payload = await register(registerForm.value);
    const token = payload?.token || payload?.access_token || payload?.jwt || "";
    const user = normalizeUser(payload, registerForm.value.username);
    if (!token) throw new Error("注册响应缺少 token");
    await enterAuthenticatedApp(user, token, true);
  } catch (error) {
    setAuthNotice(error?.message || "注册请求失败，请确认后端服务可用。", "error");
  } finally {
    authLoading.value = false;
  }
}
```

5. 删除数据定义：`activeModules`、`handlingGuides`、`ruleTemplates`、`dependencySteps`、`operationLogs`、`registrationSteps`

6. 删除 `registerStudentFace` import（如不再直接使用，但 `savePerson` 和 `saveFaceRegistration` 仍需要，保留）

7. `evidenceSummary` 简化：

```
function evidenceSummary(row = {}) {
  if (row.snapshot_url) return "已保存告警截图";
  return "未生成证据文件";
}
```

8. `activeRiskEvents` 去重逻辑调整：在 `uniqueEvents` 之后追加跨源去重步骤，按 `event_type/alert_type` + `stream_id` + `occurred_at`（5 秒容差）匹配，优先保留 `risk_score > 0` 的版本

### App.vue — Template

9. 移除 header "规则配置"按钮

10. 注册表单模板：替换 `phone`/`name`/`role`/`confirmPassword`/`remark` 为 `username`/`password`/`nickname`

11. 移除 12 个 Demo 面板模板区块（详见 specs/remove-demo-content）

12. 注册 tab 标题和描述文案更新：从"手机号注册预留"改为"用户注册"

## Risks / Trade-offs

- **[事件去重误匹配]** 不同事件恰好同类型、同视频源、时间在 5 秒内 → 概率极低（同一视频源同一类型事件 5 秒内发生两次的情况罕见），可接受
- **[注册无确认密码]** 移除 `confirmPassword` 后用户可能输错密码 → 密码字段已有 `show-password` 切换，用户可自行核对；后端有密码重置机制可后续补充
- **[Demo 面板移除后布局空旷]** 移除 12 个面板后部分页面可能显得内容较少 → 后续迭代可补充真实功能模块，当前空旷优于误导性占位内容
- **[coordinates 解析兼容性]** `JSON.parse` 对非标准 JSON 字符串会失败 → 已有 try/catch 回退 `[]`，不会崩溃

## Open Questions

- 无
