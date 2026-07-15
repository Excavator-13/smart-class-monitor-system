# 前端设置链路修复 + 规则配置生效 + 日报交互改进

## 动机

系统当前存在三类系统性缺陷，导致用户在前端的操作（开关、配置）无法正确传导到后端执行，以及日报展示的交互问题。经深入排查，根因可归纳为：

### 问题一：前端设置→后端执行链路断裂

`syncContactsToBackend()` 只传了 `contacts`、`responsible`、`reportTime`、`alertInterval` 四个字段，**遗漏了 `dingtalkEnabled` 和 `aiReportEnabled` 两个关键开关**。即使传了，后端和 AI 服务也没有消费这些字段的逻辑。结果是：

- **钉钉开关形同虚设**：前端关闭后，`alert_client.push_alert()` 中的 `self.dingtalk` 是硬编码传入的回调函数，不检查任何开关，钉钉通知照发不误
- **AI日报开关形同虚设**：`ReportService.checkAndAutoGenerate()` 只读 `@Value("${report.ai-enabled:true}")`，这是 Spring 配置项，不受前端开关控制

### 问题二：规则配置→AI检测执行链路断裂

#### 2a. rule_type 命名错配

`DataInitializer.seedRules()` 初始化的 `rule_type` 与 AI 检测服务中查找的 key 不一致：

| 数据库 `rule_type`  | AI 服务查找的 key       | 匹配？ | 后果                                |
| ------------------- | ----------------------- | ------ | ----------------------------------- |
| `phone_usage`       | `phone_usage`           | ✅     | 正常                                |
| `fire_detected`     | `flame_detected`        | ❌     | 火焰规则永远读不到，用默认阈值 0.25 |
| `fall_detected`     | `fall_detected`         | ✅     | 正常                                |
| `head_down`         | `head_down`             | ✅     | 正常                                |
| `stranger_detected` | （face_service 不读取） | ❌     | 规则记录无用                        |
| `zone_intrusion`    | `danger_zone`           | ❌     | 区域规则永远读不到                  |

此外，`crowd_gathering` 没有初始化数据，导致人群聚集检测永远被跳过。

#### 2b. 规则关闭后检测不停止

AI 检测服务把"规则不存在于 cache.rules"等同于"使用默认值继续检测"，而非"跳过检测"：

| 事件类型          | 关闭后是否跳过 | 原因                                                                                                |
| ----------------- | -------------- | --------------------------------------------------------------------------------------------------- |
| `flame_detected`  | ❌             | `rules.get("flame_detected", {})` 返回空字典，`rule.get("confidence_threshold", 0.25)` 用默认值继续 |
| `phone_usage`     | ❌             | 不检查规则是否存在，只检查手机和禁用区                                                              |
| `danger_zone_*`   | ❌             | zone_service 不检查规则开关                                                                         |
| `head_down`       | ✅             | `if head_rule:` 空字典为 falsy                                                                      |
| `crowd_gathering` | ✅             | `if crowd_rule:` 空字典为 falsy                                                                     |
| `fall_detected`   | ✅             | `if not fall_rule: return`                                                                          |

#### 2c. 告警等级完全硬编码

AI 检测服务中所有事件的 `level` 均硬编码，不读取规则配置中的 `level` 字段。前端 `normalizeRule()` 也没有映射 `level`，没有等级编辑 UI。后端 `RuleVO` 和 `RuleUpdateRequest` 虽有 `level` 字段，但 AI 不消费。

部分等级设置不合理：

- `danger_zone_intrusion`（进入危险区）= warning，`danger_zone_stay`（停留）= high——进入比停留更紧急，等级倒挂
- `phone_usage`、`head_down` 固定 warning，课堂场景偏重

### 问题三：日报交互缺陷

#### 3a. 日报卡片无法关闭

`v-if="alertSettings.latestReport"` 没有关闭/折叠按钮，日报一旦显示就永远占据页面。

#### 3b. 日报数据存入 localStorage 不合理

`latestReport` 和 `reportHistory` 存入 localStorage，持续增长。超过 5MB 限制后 `setItem` 静默失败，所有设置一起丢失。日报数据本质上是服务端数据，后端已有 `getLatestReport()` / `getHistory()` 接口。

#### 3c. 日报中无截图的告警显示损毁图标

`ReportService.queryTodayAlerts()` 中 `String.valueOf(null)` 把数据库 NULL 变成了字符串 `"null"`，`!"null".isBlank()` 为 true，日报中 `snapshotUrl` 值为字符串 `"null"`。前端 `v-if="a.snapshotUrl"` 判断字符串 `"null"` 为 truthy，`getSnapshotUrl("null")` 拼出无效 URL，图片加载失败。

## 范围

### 一、修复 rule_type 命名错配（P0）

修改 `DataInitializer.seedRules()` 中的 `rule_type`，以 AI 检测服务实际查找的 key 为准：

- `fire_detected` → `flame_detected`
- `zone_intrusion` → `danger_zone`
- 删除 `stranger_detected`（face_service 不从 rules 读取）
- 新增 `crowd_gathering`（人群聚集检测）

修改后的初始化规则列表：

| rule_type         | rule_name    | enabled | threshold_seconds | confidence_threshold | cooldown_seconds | level   |
| ----------------- | ------------ | ------- | ----------------- | -------------------- | ---------------- | ------- |
| `phone_usage`     | 手机违规检测 | true    | 5                 | 0.75                 | 30               | info    |
| `flame_detected`  | 明火检测     | true    | 3                 | 0.80                 | 20               | high    |
| `fall_detected`   | 摔倒检测     | false   | 4                 | 0.78                 | 20               | high    |
| `head_down`       | 长时间低头   | true    | 6                 | 0.70                 | 60               | info    |
| `crowd_gathering` | 异常人流聚集 | true    | 3                 | 0.70                 | 30               | high    |
| `danger_zone`     | 区域入侵检测 | true    | 5                 | 0.75                 | 30               | warning |

### 二、修复规则开关不生效（P0）

在 AI 检测服务中，规则不存在时跳过检测，而非使用默认值继续：

1. **fire_service.py**：`detect()` 开头检查 `flame_detected` 规则是否存在于 `rules`，不存在则直接返回空列表
2. **behavior_service.py**：`phone_usage` 检测前检查 `phone_usage` 规则是否存在，不存在则跳过
3. **zone_service.py**：`detect()` 增加 `enabled` 参数或检查 `danger_zone` 规则是否存在，不存在则跳过
4. **analysis_service.py**：传给 `zone_service.detect()` 时传入规则启用状态

### 三、打通前端设置→后端→AI 的开关链路（P1）

#### 3a. 钉钉开关

1. 前端 `syncContactsToBackend()` 传入 `dingtalkEnabled`
2. 后端 `SettingsController` 接收并推给 AI 服务 `/api/contacts/sync`
3. AI 服务 `alert_client.py` 新增 `dingtalk_enabled` 属性，`push_alert()` 中检查该属性，关闭时跳过钉钉调用
4. `app.py` 构造 `AlertClient` 时从 SpringBoot settings 读取 `dingtalkEnabled`

#### 3b. AI日报开关

1. 前端 `syncContactsToBackend()` 传入 `aiReportEnabled`
2. 后端 `SettingsController` 接收并存入 settings Map
3. `ReportService.checkAndAutoGenerate()` 从 settings Map 读取 `aiReportEnabled`，为 false 时跳过自动生成

### 四、修复日报中 snapshotUrl 的 null 字符串问题（P1）

修改 `ReportService.queryTodayAlerts()`：对 `snapshotUrl` 做 null 检查，null 时不放入 Map（或放入 null 值），避免 `String.valueOf(null)` 产生字符串 `"null"`。

### 五、告警等级可配置（P2）

1. **前端 `normalizeRule()`**：增加 `level` 字段映射
2. **前端规则卡片**：增加等级选择器（`el-select`：high / warning / info），修改后调用 `PUT /rules/{id}` 保存
3. **前端增加通用规则更新逻辑**：`updateRule(id, data)` 调用 `PUT /rules/{id}`，用于保存 threshold_seconds 和 level 的变更
4. **AI 检测服务**：从规则配置中读取 `level` 字段，规则中无 `level` 时 fallback 到硬编码默认值
5. **调整默认等级**：`phone_usage` → info，`head_down` → info，`crowd_gathering` → high，`danger_zone_intrusion` → high

### 六、日报交互改进（P2）

#### 6a. 日报卡片增加关闭按钮

在日报卡片顶部增加关闭按钮，点击后设置 `latestReport` 为 null（前端状态），卡片隐藏。不影响后端存储的日报数据。

#### 6b. 日报数据从后端 API 获取

- 将 `latestReport` 和 `reportHistory` 从 `alertSettings` 中分离为独立 ref
- 页面加载时从后端 `GET /report/latest` 获取最新日报
- 不再将日报数据存入 localStorage
- `alertSettings` 只保留轻量配置（开关、联系人、时间等），继续存 localStorage

## 不做

- 不修改 `stream_offline` 的等级逻辑（它不在规则表中，由 analysis_service 硬编码为 high，合理）
- 不修改 `stranger_detected` 让 face_service 读取规则（face_service 的检测逻辑与行为规则差异较大，超出本次范围）
- 不修改 `face_recognized` 的等级（已识别人员不是告警，不需要等级配置）
- 不重构 `alertSettings` 的整体结构（只分离日报数据，其余保持不变）
- 不修改日报的后端存储逻辑（已有 `data/reports/` 文件存储，不做改动）
- 不增加日报的定时自动刷新（前端手动生成或页面加载时拉取即可）
- 不修改 `config_client.load_rules()` 的过滤逻辑（`enabled=False` 的规则不入 cache 是正确行为，问题在于检测服务不检查规则是否存在）

## 影响模块

### backend_system（Java / SpringBoot）

- `config/DataInitializer.java`：`seedRules()` 修改 rule_type 命名、调整默认等级、新增 crowd_gathering 规则、删除 stranger_detected 规则
- `service/ReportService.java`：`queryTodayAlerts()` 修复 `String.valueOf(null)` 问题；`checkAndAutoGenerate()` 从 settings 读取 `aiReportEnabled`
- `controller/SettingsController.java`：`PUT /api/settings` 接收 `dingtalkEnabled` 和 `aiReportEnabled`，推给 AI 服务

### backend_ai（Python / Flask）

- `services/fire_service.py`：`detect()` 开头检查规则是否存在，不存在则返回空列表
- `services/behavior_service.py`：`phone_usage` 检测前检查规则是否存在；所有检测从规则中读取 `level`
- `services/zone_service.py`：`detect()` 检查规则是否存在/启用，不存在则返回空列表；从规则中读取 `level`
- `services/alert_client.py`：新增 `dingtalk_enabled` 属性，`push_alert()` 中检查该属性
- `services/analysis_service.py`：传给 zone_service 时传入规则启用状态；各检测服务传入的 rules 中读取 level
- `app.py`：构造 `AlertClient` 时从 settings 读取 `dingtalkEnabled`

### frontend（Vue3 / Element Plus）

- `App.vue`：
  - `syncContactsToBackend()` 传入 `dingtalkEnabled` 和 `aiReportEnabled`
  - 日报卡片增加关闭按钮
  - 将 `latestReport` / `reportHistory` 从 `alertSettings` 分离为独立 ref
  - 页面加载时从后端获取最新日报
  - 规则卡片增加等级选择器
  - 增加规则更新逻辑（`updateRule`）
- `services/smartClassApi.js`：`normalizeRule()` 增加 `level` 映射；新增 `updateRule()` 函数
