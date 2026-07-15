## 1. DataInitializer seedRules rule_type 修正

- [ ] 1.1 `backend_system/src/main/java/com/smartclass/monitor/config/DataInitializer.java` 修改 `seedRules()`：`fire_detected` → `flame_detected`
- [ ] 1.2 `DataInitializer.java` 修改 `seedRules()`：`zone_intrusion` → `danger_zone`
- [ ] 1.3 `DataInitializer.java` 修改 `seedRules()`：删除 `stranger_detected` 规则
- [ ] 1.4 `DataInitializer.java` 修改 `seedRules()`：新增 `crowd_gathering` 规则（`createRule("crowd_gathering", "异常人流聚集", true, 3, 0.70, 30, "high")`）
- [ ] 1.5 `DataInitializer.java` 修改 `seedRules()` 等级调整：`phone_usage` → `info`，`head_down` → `info`
- [ ] 1.6 验证：SpringBoot 编译通过（`mvn -DskipTests compile`）

## 2. AI 检测服务：规则不存在时跳过检测

- [ ] 2.1 `backend_ai/services/fire_service.py` 修改 `detect()`：`rule = (rules or {}).get("flame_detected", {})` 之后加 `if not rule: return []`
- [ ] 2.2 `backend_ai/services/behavior_service.py` 修改 `detect_from_objects()`：手机检测条件从 `if phones and phone_forbidden_zones:` 改为 `if phone_rule and phones and phone_forbidden_zones:`
- [ ] 2.3 `backend_ai/services/zone_service.py` 修改 `detect()`：方法开头加 `if not rule: return []`
- [ ] 2.4 验证：`fire_service.detect()` 在 `flame_detected` 规则不存在时返回空列表
- [ ] 2.5 验证：`behavior_service.detect_from_objects()` 在 `phone_usage` 规则不存在时跳过手机检测
- [ ] 2.6 验证：`zone_service.detect()` 在 `danger_zone` 规则不存在时返回空列表

## 3. AI 检测服务：从规则读取 level

- [ ] 3.1 `backend_ai/services/fire_service.py` 修改 `detect()`：`level = rule.get("level", "high")`，检测结果中 `"level": level` 替代 `self._classify_level(conf)`
- [ ] 3.2 `backend_ai/services/behavior_service.py` 修改手机检测：`phone_level = phone_rule.get("level", "info")`，`"level": phone_level` 替代硬编码 `"warning"`
- [ ] 3.3 `backend_ai/services/behavior_service.py` 修改 head_down 检测：`head_level = head_rule.get("level", "info")`，`"level": head_level` 替代硬编码 `"warning"`
- [ ] 3.4 `backend_ai/services/behavior_service.py` 修改 crowd_gathering 检测：`crowd_level = crowd_rule.get("level", "warning")`，`"level": crowd_level` 替代硬编码 `"warning"`
- [ ] 3.5 `backend_ai/services/behavior_service.py` 修改 fall_detected 检测：`fall_level = fall_rule.get("level", "high")`，`"level": fall_level` 替代硬编码 `"high"`
- [ ] 3.6 `backend_ai/services/zone_service.py` 修改 `detect()`：`intrusion_level = rule.get("level", "high")`，`stay_level = config.get("stay_level", "high")`，`approach_level = config.get("approach_level", "warning")`，检测结果中使用这些变量替代硬编码
- [ ] 3.7 验证：各检测服务在规则含 `level` 字段时使用规则值，不含时使用默认值

## 4. 钉钉开关链路打通

- [ ] 4.1 `frontend/src/App.vue` 修改 `syncContactsToBackend()`：请求 body 增加 `dingtalkEnabled: alertSettings.value.dingtalkEnabled`
- [ ] 4.2 `frontend/src/App.vue` 新增 watch：`watch(() => alertSettings.value.dingtalkEnabled, syncContactsToBackend)`
- [ ] 4.3 `backend_ai/services/alert_client.py` 修改 `__init__()`：新增 `dingtalk_enabled: bool = True` 参数，存储为 `self.dingtalk_enabled`
- [ ] 4.4 `backend_ai/services/alert_client.py` 修改 `push_alert()`：钉钉调用条件从 `if self.dingtalk:` 改为 `if self.dingtalk and self.dingtalk_enabled:`
- [ ] 4.5 `backend_ai/app.py` 修改 `contacts_sync()`：新增 `dingtalkEnabled` 字段消费，从 `app.extensions["ai_services"]["alert_client"]` 获取 `alert_client`，设置 `alert_client.dingtalk_enabled = bool(dingtalk_enabled)`
- [ ] 4.6 `backend_ai/app.py` 修改 `_restore_dingtalk_settings()`：从 settings 响应中读取 `dingtalkEnabled`，返回该值
- [ ] 4.7 `backend_ai/app.py` 修改 `create_app()`：`_restore_dingtalk_settings()` 返回 `dingtalk_enabled`，传入 `AlertClient(dingtalk_enabled=dingtalk_enabled)`
- [ ] 4.8 验证：前端关闭钉钉开关后 `PUT /api/settings` 请求 body 含 `dingtalkEnabled: false`
- [ ] 4.9 验证：AI 服务收到 `dingtalkEnabled: false` 后 `alert_client.dingtalk_enabled` 为 `False`
- [ ] 4.10 验证：`dingtalk_enabled=False` 时 `push_alert()` 不调用钉钉通知

## 5. AI日报开关链路打通

- [ ] 5.1 `frontend/src/App.vue` 修改 `syncContactsToBackend()`：请求 body 增加 `aiReportEnabled: alertSettings.value.aiReportEnabled`
- [ ] 5.2 `frontend/src/App.vue` 新增 watch：`watch(() => alertSettings.value.aiReportEnabled, syncContactsToBackend)`
- [ ] 5.3 `backend_system/src/main/java/com/smartclass/monitor/service/ReportService.java` 修改 `checkAndAutoGenerate()`：在 `if (!aiEnabled) return;` 之后增加 `aiReportEnabled` 检查：`Object aiReportEnabledObj = settings.get("aiReportEnabled"); if (aiReportEnabledObj != null && !Boolean.TRUE.equals(aiReportEnabledObj)) return;`
- [ ] 5.4 验证：前端关闭 AI 日报开关后 `PUT /api/settings` 请求 body 含 `aiReportEnabled: false`
- [ ] 5.5 验证：`aiReportEnabled=false` 时 `checkAndAutoGenerate()` 跳过自动生成
- [ ] 5.6 验证：`aiReportEnabled` 未设置时（向后兼容）自动生成正常执行

## 6. 修复 snapshotUrl null 字符串 bug

- [ ] 6.1 `backend_system/src/main/java/com/smartclass/monitor/service/ReportService.java` 修改 `queryTodayAlerts()`：`m.put("snapshotUrl", a.getSnapshotUrl())` 改为先 null 检查 `if (a.getSnapshotUrl() != null && !a.getSnapshotUrl().isBlank()) { m.put("snapshotUrl", a.getSnapshotUrl()); }`
- [ ] 6.2 验证：`snapshotUrl` 为 null 时结果 Map 不含 `"snapshotUrl"` key
- [ ] 6.3 验证：`generateReport()` 中 `a.getOrDefault("snapshotUrl", "")` 对不含 key 的 Map 返回空字符串，跳过截图处理

## 7. 前端告警等级可配置

- [ ] 7.1 `frontend/src/services/smartClassApi.js` 修改 `normalizeRule()`：增加 `level: optional(item.level, "warning")` 字段映射
- [ ] 7.2 `frontend/src/services/smartClassApi.js` 新增 `updateRule(id, data)` 函数：调用 `PUT /rules/{id}`，请求 body 为 `data`
- [ ] 7.3 `frontend/src/App.vue` 修改规则卡片模板：在 `threshold_seconds` 控件和 `el-switch` 之间增加等级选择器 `el-select`（选项：`high`/`warning`/`info`），`v-model="rule.level"`，`@change="handleUpdateRule(rule)"`
- [ ] 7.4 `frontend/src/App.vue` 修改 `threshold_seconds` 的 `el-input-number`：增加 `@change="handleUpdateRule(rule)"`
- [ ] 7.5 `frontend/src/App.vue` 新增 `handleUpdateRule(rule)` 函数：调用 `updateRule(rule.id, { threshold_seconds: rule.threshold_seconds, level: rule.level })`
- [ ] 7.6 验证：规则卡片显示等级选择器，切换等级后 `PUT /rules/{id}` 请求 body 含 `level` 字段

## 8. 日报卡片关闭按钮

- [ ] 8.1 `frontend/src/App.vue` 修改日报卡片模板：在卡片顶部增加关闭按钮 `<el-button size="small" text @click="latestReport = null">关闭</el-button>`
- [ ] 8.2 验证：点击关闭按钮后日报卡片隐藏

## 9. 日报数据从 localStorage 分离

- [ ] 9.1 `frontend/src/App.vue` 新增独立 ref：`const latestReport = ref(null)` 和 `const reportHistory = ref([])`
- [ ] 9.2 `frontend/src/App.vue` 修改 `alertSettings` 初始化：删除 `latestReport` 和 `reportHistory` 属性
- [ ] 9.3 `frontend/src/App.vue` 新增 `loadLatestReport()` 函数：调用 `GET /report/latest`，设置 `latestReport.value`
- [ ] 9.4 `frontend/src/App.vue` 修改 `generateAiReport()`：结果存入 `latestReport.value` 而非 `alertSettings.value.latestReport`
- [ ] 9.5 `frontend/src/App.vue` 修改模板：所有 `alertSettings.latestReport` 引用改为 `latestReport`，`alertSettings.reportHistory` 改为 `reportHistory`
- [ ] 9.6 `frontend/src/App.vue` 在页面初始化逻辑中调用 `loadLatestReport()`
- [ ] 9.7 验证：localStorage 中不再包含 `latestReport` 和 `reportHistory`
- [ ] 9.8 验证：页面加载时从后端 `GET /report/latest` 获取最新日报
- [ ] 9.9 验证：手动生成日报后 `latestReport` ref 更新，日报卡片正确展示

## 10. 编译与集成验证

- [ ] 10.1 SpringBoot 编译通过（`mvn -DskipTests compile`）
- [ ] 10.2 AI 服务语法检查通过（`python -m py_compile` 对 fire_service / behavior_service / zone_service / alert_client / app.py）
- [ ] 10.3 前端构建通过（`npm run build` 或 `npm run dev` 无报错）
- [ ] 10.4 端到端验证：关闭火焰检测规则 → AI 不再产出 `flame_detected` 事件
- [ ] 10.5 端到端验证：关闭钉钉开关 → 告警推送后不触发钉钉通知
- [ ] 10.6 端到端验证：关闭 AI 日报开关 → 定时任务不生成日报
- [ ] 10.7 端到端验证：修改规则等级 → 后续告警使用新等级
