# 前端设置链路修复 + 规则配置生效 + 日报交互改进 — 技术设计

## Context

### 已有基础设施

**设置同步**：前端 `syncContactsToBackend()` 调用 `PUT /api/settings`，将 `contacts`、`responsible`、`reportTime`、`alertInterval` 四个字段推给 SpringBoot。SpringBoot `SettingsController` 存入内存 Map + 文件 `data/settings.json`，同时转发给 AI 服务 `POST /api/contacts/sync`。AI 服务 `contacts_sync()` 只消费 `contacts`、`responsible`、`alertInterval` 三个字段。

**钉钉通知**：`AlertClient` 构造时 `dingtalk=trigger_alert`，`push_alert()` 中 `if self.dingtalk:` 直接调用，无启用/禁用检查。`dingtalk_service.trigger_alert()` 只检查 APP_KEY/APP_SECRET/WEBHOOK 是否完整。

**AI日报自动生成**：`ReportService.checkAndAutoGenerate()` 由 `@Scheduled(fixedRate=600000)` 驱动，只读 `@Value("${report.ai-enabled:true}")` 和 `settings.reportTime`，不读前端 `aiReportEnabled` 开关。

**规则配置**：`DataInitializer.seedRules()` 初始化6条规则到 `behavior_rule` 表。AI 服务 `ConfigClient.load_rules()` 从 `GET /rules` 拉取，过滤 `enabled=True` 的规则，以 `rule_type` 为 key 存入 `cache.rules`。各检测服务从 `cache.rules` 中按 key 查找规则。

**规则更新**：SpringBoot `RuleService.updateRule()` 支持 `PUT /rules/{id}` 更新全部字段（含 `level`），更新后调用 `aiClient.reloadConfig()` 通知 AI 刷新。前端目前只有 `toggleRule()` 调用 `PUT /rules/{id}/toggle`，没有通用更新逻辑。

**日报数据流**：`ReportService.generateReport()` → `queryTodayAlerts()` 从数据库取告警 → 拼接截图 URL + VL 分析 → 存入 `latestReport` 内存变量 + 写文件。前端 `generateAiReport()` 调用 `POST /report/generate` 获取日报，存入 `alertSettings.latestReport`（localStorage）。

**前端状态管理**：`alertSettings` 是一个大型 ref，混合了 UI 状态（`generating`）、开关（`dingtalkEnabled`、`aiReportEnabled`）、配置（`contacts`、`reportTime`）和日报数据（`latestReport`、`reportHistory`）。`watch(alertSettings, saveSettings, { deep: true })` 将整个对象序列化存入 localStorage。

## Goals / Non-Goals

**Goals:**

1. 修复 `DataInitializer.seedRules()` 中 `rule_type` 命名，使其与 AI 检测服务查找的 key 一致；补充 `crowd_gathering` 规则；删除无用的 `stranger_detected` 规则
2. AI 检测服务在规则不存在时跳过检测，而非使用默认值继续
3. 打通 `dingtalkEnabled` 前端→后端→AI 的完整链路
4. 打通 `aiReportEnabled` 前端→后端的完整链路
5. 修复 `ReportService.queryTodayAlerts()` 中 `String.valueOf(null)` 产生 `"null"` 字符串的 bug
6. 前端增加告警等级编辑 UI，AI 检测服务从规则中读取 `level`
7. 日报卡片增加关闭按钮
8. 日报数据从 localStorage 分离，改为从后端 API 获取

**Non-Goals:**

- 不修改 `stream_offline` 的等级逻辑（不在规则表中，硬编码 high 合理）
- 不让 `face_service` 读取规则（检测逻辑差异大，超出范围）
- 不重构 `alertSettings` 整体结构（只分离日报数据）
- 不修改 `config_client.load_rules()` 的 `enabled` 过滤逻辑（行为正确）
- 不增加日报定时自动刷新（页面加载时拉取即可）
- 不修改日报后端存储逻辑（`data/reports/` 文件存储不变）

## Decisions

| 决策                         | 选择                                                                 | 理由                                                                                                         |
| ---------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| rule_type 命名统一方向       | 以 AI 检测服务的事件类型为准，修改初始化数据                         | AI 侧事件类型名已散布在 `analysis_service`、`event_service`、`dingtalk_service` 等多处，改初始化数据成本最低 |
| 规则不存在时的行为           | 跳过检测，返回空列表                                                 | 语义清晰：规则被关闭 = 不检测。与 `head_down`/`crowd_gathering`/`fall_detected` 已有的行为一致               |
| 钉钉开关传递方式             | 复用现有 `POST /api/contacts/sync` 通道，增加 `dingtalkEnabled` 字段 | 无需新增 API 端点，与现有 `contacts`/`responsible`/`alertInterval` 同通道                                    |
| 钉钉开关在 AI 侧的存储       | `AlertClient` 新增 `dingtalk_enabled` 实例属性                       | 最小改动，`push_alert()` 中一处 `if` 检查即可                                                                |
| AI日报开关存储               | SpringBoot `SettingsController.store` Map                            | 已有 `reportTime` 的同类存储模式，`ReportService.updateSettings()` 已接收整个 Map                            |
| `snapshotUrl` null 修复方式  | `queryTodayAlerts()` 中 null 时不放入 Map                            | 最小改动，下游 `generateReport()` 的 `getOrDefault` 逻辑自然走默认值                                         |
| 等级配置传递                 | AI 检测服务从 `rules[rule_type]["level"]` 读取                       | 与 `confidence_threshold` 等字段的读取模式一致，无需新增数据结构                                             |
| 等级 fallback                | 规则中无 `level` 时使用硬编码默认值                                  | 向后兼容，已有规则记录可能无 `level` 字段                                                                    |
| 日报关闭按钮行为             | 前端 `latestReport` ref 置为 null，不删除后端数据                    | 关闭只是隐藏视图，数据仍可从后端重新获取                                                                     |
| 日报数据获取方式             | 页面加载时 `GET /report/latest`，存入独立 ref                        | 后端已有接口，无需新增；独立 ref 不污染 localStorage                                                         |
| `stranger_detected` 规则处理 | 从 `seedRules()` 中删除                                              | `face_service` 不从 `config_client.cache.rules` 读取，此规则记录无用                                         |

## Architecture

### 改动前：设置同步数据流

```
前端 alertSettings
    │
    ├── dingtalkEnabled ──────── ❌ 不传 ────────────────────── 无消费者
    ├── aiReportEnabled ──────── ❌ 不传 ────────────────────── 无消费者
    ├── contacts / responsible / reportTime / alertInterval
    │       │
    │       ▼
    │   PUT /api/settings ──→ SettingsController.store ──→ POST /api/contacts/sync
    │                                                          │
    │                                                          ├── contacts → ds.PERSONS
    │                                                          ├── responsible → ds.PRIMARY
    │                                                          └── alertInterval → ds.STEP_TIMEOUT
    │
    └── latestReport / reportHistory ──→ localStorage（持续增长，5MB 风险）
```

### 改动后：设置同步数据流

```
前端 alertSettings
    │
    ├── dingtalkEnabled ──────── ✅ 传入 ──┐
    ├── aiReportEnabled ──────── ✅ 传入 ──┤
    ├── contacts / responsible / reportTime / alertInterval ──┤
    │       │                                                  │
    │       ▼                                                  ▼
    │   PUT /api/settings ──→ SettingsController.store ──→ POST /api/contacts/sync
    │                               │                          │
    │                               ├── aiReportEnabled        ├── contacts → ds.PERSONS
    │                               │   → ReportService        ├── responsible → ds.PRIMARY
    │                               │     .settings Map        ├── alertInterval → ds.STEP_TIMEOUT
    │                               │                          └── dingtalkEnabled → AlertClient
    │                               │                                .dingtalk_enabled
    │                               └── dingtalkEnabled
    │                                     → 同上
    │
    └── latestReport / reportHistory ──→ 独立 ref，从 GET /report/latest 获取
                                         不再存 localStorage
```

### 改动前：规则配置数据流

```
DataInitializer.seedRules()
    │
    ├── phone_usage ──────────── ✅ 匹配
    ├── fire_detected ────────── ❌ AI 查找 "flame_detected"
    ├── fall_detected ────────── ✅ 匹配
    ├── head_down ───────────── ✅ 匹配
    ├── stranger_detected ───── ❌ AI 不读取
    ├── zone_intrusion ──────── ❌ AI 查找 "danger_zone"
    └── （缺 crowd_gathering） ─ ❌ 无初始化数据
           │
           ▼
    config_client.load_rules() ──→ cache.rules（以 rule_type 为 key）
           │
           ├── fire_service: rules.get("flame_detected", {}) → {} → 用默认阈值继续 ❌
           ├── phone_usage:  不检查规则是否存在 ❌
           ├── zone_service: 不检查规则开关 ❌
           ├── head_down:    if head_rule: → 跳过 ✅
           ├── crowd:        if crowd_rule: → 跳过 ✅（但永远跳过，因为无数据）
           └── fall:         if not fall_rule: return ✅
```

### 改动后：规则配置数据流

```
DataInitializer.seedRules()
    │
    ├── phone_usage ──────────── ✅ 匹配
    ├── flame_detected ───────── ✅ 匹配（改名）
    ├── fall_detected ────────── ✅ 匹配
    ├── head_down ───────────── ✅ 匹配
    ├── crowd_gathering ─────── ✅ 匹配（新增）
    ├── danger_zone ─────────── ✅ 匹配（改名）
    └── （删除 stranger_detected）
           │
           ▼
    config_client.load_rules() ──→ cache.rules（含 level 字段）
           │
           ├── fire_service:  if "flame_detected" not in rules: return [] ✅
           ├── phone_usage:   if not phone_rule: skip ✅
           ├── zone_service:  if not rule: return [] ✅
           ├── head_down:     if head_rule: ✅
           ├── crowd:         if crowd_rule: ✅
           └── fall:          if not fall_rule: return ✅
           │
           └── 所有检测: rule.get("level", DEFAULT_LEVEL) ✅
```

## 详细设计

### 1. 修复 DataInitializer.seedRules() 的 rule_type 命名

**文件**：`backend_system/src/main/java/com/smartclass/monitor/config/DataInitializer.java`

修改 `seedRules()` 方法：

```java
private void seedRules() {
    log.info("插入测试规则...");
    List<BehaviorRule> rules = Arrays.asList(
            createRule("phone_usage", "手机违规检测", true, 5, 0.75, 30, "info"),
            createRule("flame_detected", "明火检测", true, 3, 0.80, 20, "high"),
            createRule("fall_detected", "摔倒检测", false, 4, 0.78, 20, "high"),
            createRule("head_down", "长时间低头", true, 6, 0.70, 60, "info"),
            createRule("crowd_gathering", "异常人流聚集", true, 3, 0.70, 30, "high"),
            createRule("danger_zone", "区域入侵检测", true, 5, 0.75, 30, "warning")
    );
    for (BehaviorRule r : rules) {
        behaviorRuleMapper.insert(r);
    }
}
```

变更点：

1. `fire_detected` → `flame_detected`（匹配 AI 查找 key）
2. `zone_intrusion` → `danger_zone`（匹配 AI 查找 key）
3. 删除 `stranger_detected`（face_service 不读取）
4. 新增 `crowd_gathering`（人群聚集检测）
5. 等级调整：`phone_usage` → info，`head_down` → info，`crowd_gathering` → high

注意：此修改只影响新部署的数据库。已有数据库需手动执行 SQL 更新，或删除 `data/` 目录让应用重新初始化。

### 2. AI 检测服务：规则不存在时跳过检测

#### 2a. fire_service.py

**文件**：`backend_ai/services/fire_service.py`

在 `detect()` 方法开头增加规则存在性检查：

```python
def detect(self, stream_id, frame, rules=None):
    if self.model is None:
        return []

    rule = (rules or {}).get("flame_detected", {})
    if not rule:                          # 新增：规则不存在或已关闭时跳过
        return []

    threshold = float(rule.get("confidence_threshold", self.confidence_threshold))
    cooldown = float(rule.get("cooldown_seconds", 10))
    threshold_seconds = float(rule.get("threshold_seconds", 0))
    level = rule.get("level", "high")     # 新增：从规则读取 level

    # ... 后续检测逻辑不变，但 level 使用 rule 中的值 ...
    # detections.append 中 "level": level 替代 self._classify_level(conf)
```

变更点：

1. `if not rule: return []` — 规则不存在时跳过检测
2. `level = rule.get("level", "high")` — 从规则读取等级，fallback 到 `"high"`
3. 检测结果中 `"level": level` 替代 `"level": self._classify_level(conf)`
4. `_classify_level()` 方法保留但不再被 `detect()` 调用（可作为内部工具方法）

#### 2b. behavior_service.py — phone_usage

**文件**：`backend_ai/services/behavior_service.py`

修改 `detect_from_objects()` 中手机检测部分：

```python
phone_rule = rules.get("phone_usage", {})
if phone_rule and phones and phone_forbidden_zones:    # 新增 phone_rule 检查
    phone_threshold = float(phone_rule.get("confidence_threshold", 0.6))
    phone_level = phone_rule.get("level", "info")      # 新增：从规则读取 level
    for idx, person in enumerate(persons):
        for phone in phones:
            # ... 检测逻辑不变 ...
            detections.append({
                ...
                "level": phone_level,                   # 使用规则中的 level
                ...
            })
```

变更点：

1. `if phone_rule and phones and phone_forbidden_zones:` — 增加 `phone_rule` 检查
2. `phone_level = phone_rule.get("level", "info")` — 从规则读取等级，fallback 到 `"info"`
3. 检测结果中 `"level": phone_level`

#### 2c. behavior_service.py — head_down / crowd_gathering / fall_detected

这些规则已有存在性检查（`if head_rule:` / `if crowd_rule:` / `if not fall_rule: return`），只需增加 level 读取：

```python
# head_down
head_rule = rules.get("head_down", {})
if head_rule:
    head_level = head_rule.get("level", "info")    # 新增
    detections.append({ ... "level": head_level })  # 替代硬编码 "warning"

# crowd_gathering
crowd_rule = rules.get("crowd_gathering", {})
if crowd_rule:
    crowd_level = crowd_rule.get("level", "warning")  # 新增
    detections.append({ ... "level": crowd_level })    # 替代硬编码 "warning"

# fall_detected
fall_rule = rules.get("fall_detected", {})
if not fall_rule:
    return detections
fall_level = fall_rule.get("level", "high")        # 新增
detections.append({ ... "level": fall_level })     # 替代硬编码 "high"
```

#### 2d. zone_service.py

**文件**：`backend_ai/services/zone_service.py`

增加规则存在性检查和 level 读取：

```python
def detect(self, stream_id, persons, zones, rule=None):
    if not rule:                                     # 新增：规则不存在时跳过
        return []

    danger_zones = [z for z in zones if z.get("zone_type") == "danger"]
    if not danger_zones:                             # 新增：无 danger 区域时跳过
        return []

    config = parse_json_field((rule or {}).get("config_json"), {})
    safe_distance = float(config.get("safe_distance", 0.05))

    # 从规则读取各事件类型的等级
    intrusion_level = rule.get("level", "high")      # 新增：intrusion 默认 high
    stay_level = config.get("stay_level", "high")    # 新增：stay 默认 high
    approach_level = config.get("approach_level", "warning")  # 新增：approach 默认 warning

    detections = []
    for person in persons:
        # ... 检测逻辑不变，但 level 使用规则值 ...
        if point_in_polygon(foot, polygon):
            detections.append({ "level": intrusion_level, ... })
            detections.append({ "level": stay_level, ... })
        else:
            if distance < safe_distance:
                detections.append({ "level": approach_level, ... })
    return detections
```

变更点：

1. `if not rule: return []` — 规则不存在时跳过
2. `if not danger_zones: return []` — 无 danger 区域时跳过（防御性检查）
3. 从规则读取 `level` 作为 `intrusion_level`，fallback 到 `"high"`（修正原来的等级倒挂）
4. `stay_level` 和 `approach_level` 从 `config_json` 中读取，fallback 到合理默认值

### 3. 打通钉钉开关链路

#### 3a. 前端 syncContactsToBackend()

**文件**：`frontend/src/App.vue`

```javascript
const syncContactsToBackend = async () => {
  try {
    await fetch("http://127.0.0.1:8080/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contacts: alertSettings.value.contacts,
        responsible: alertSettings.value.responsible,
        reportTime: alertSettings.value.reportTime,
        alertInterval: alertSettings.value.alertInterval,
        dingtalkEnabled: alertSettings.value.dingtalkEnabled, // 新增
        aiReportEnabled: alertSettings.value.aiReportEnabled, // 新增
      }),
    });
  } catch {}
};
```

同时为 `dingtalkEnabled` 和 `aiReportEnabled` 增加 watch 触发同步：

```javascript
watch(() => alertSettings.value.dingtalkEnabled, syncContactsToBackend);
watch(() => alertSettings.value.aiReportEnabled, syncContactsToBackend);
```

#### 3b. AI 服务 contacts_sync() 消费 dingtalkEnabled

**文件**：`backend_ai/app.py`

在 `contacts_sync()` 中增加 `dingtalkEnabled` 的消费：

```python
@app.post("/api/contacts/sync")
def contacts_sync():
    body = request.get_json(silent=True) or {}
    contacts = body.get("contacts", [])
    # ... 现有 contacts/responsible/alertInterval 逻辑不变 ...

    # 新增：钉钉开关
    dingtalk_enabled = body.get("dingtalkEnabled")
    if dingtalk_enabled is not None:
        ai_services = app.extensions.get("ai_services", {})
        alert_client = ai_services.get("alert_client")
        if alert_client:
            alert_client.dingtalk_enabled = bool(dingtalk_enabled)

    return json_response({"ok": True, "count": len(new_persons)})
```

#### 3c. AlertClient 新增 dingtalk_enabled 属性

**文件**：`backend_ai/services/alert_client.py`

```python
class AlertClient:
    def __init__(self, ..., dingtalk_enabled: bool = True):
        # ... 现有属性 ...
        self.dingtalk_enabled = dingtalk_enabled

    def push_alert(self, event, record_path=None, event_time_offset=None):
        # ... 现有 SpringBoot 推送逻辑不变 ...

        # 钉钉通知
        if self.dingtalk and self.dingtalk_enabled:    # 新增 dingtalk_enabled 检查
            try:
                # ... 现有钉钉逻辑不变 ...
```

#### 3d. app.py 初始化时恢复 dingtalk_enabled

**文件**：`backend_ai/app.py`

在 `_restore_dingtalk_settings()` 中增加 `dingtalkEnabled` 的恢复：

```python
def _restore_dingtalk_settings(spring_base_url, internal_token):
    try:
        # ... 现有逻辑不变 ...
        dingtalk_enabled = data.get("dingtalkEnabled")
        if dingtalk_enabled is not None:
            # 存入 app.extensions 供后续 contacts_sync 使用
            # 或直接设置 alert_client（此时 alert_client 尚未创建，改为在 create_app 中处理）
    except Exception:
        pass
```

在 `create_app()` 中，构造 `AlertClient` 后从 settings 恢复：

```python
alert_client = AlertClient(
    base_url=spring_base_url,
    internal_token=internal_token,
    dingtalk=trigger_alert,
    snapshot_root=snapshot_root,
    nginx_base_url=nginx_base_url,
)

# 恢复钉钉开关状态
try:
    headers = {"X-Internal-Token": internal_token} if internal_token else None
    settings_resp = requests.get(f"{spring_base_url}/api/settings", headers=headers, timeout=5)
    if settings_resp.ok:
        settings_data = settings_resp.json()
        dingtalk_enabled = settings_data.get("dingtalkEnabled")
        if dingtalk_enabled is not None:
            alert_client.dingtalk_enabled = bool(dingtalk_enabled)
except Exception:
    pass
```

注意：`_restore_dingtalk_settings()` 已有 `GET /api/settings` 调用，可以将 `dingtalkEnabled` 的恢复合并到该函数中，避免重复请求。具体做法是在 `_restore_dingtalk_settings()` 中返回 `dingtalk_enabled` 值，在 `create_app()` 中传给 `AlertClient` 构造函数。

### 4. 打通 AI日报开关链路

#### 4a. 后端 ReportService 读取 aiReportEnabled

**文件**：`backend_system/src/main/java/com/smartclass/monitor/service/ReportService.java`

修改 `checkAndAutoGenerate()`：

```java
@Scheduled(fixedRate = 600000)
public void checkAndAutoGenerate() {
    if (!aiEnabled) return;

    // 新增：检查前端 aiReportEnabled 开关
    Object aiReportEnabledObj = settings.get("aiReportEnabled");
    if (aiReportEnabledObj != null && !Boolean.TRUE.equals(aiReportEnabledObj)) {
        return;
    }

    String setTime = String.valueOf(settings.getOrDefault("reportTime", "18:00"));
    String now = LocalTime.now().truncatedTo(ChronoUnit.MINUTES).toString();
    if (now.length() >= 5) now = now.substring(0, 5);
    if (now.equals(setTime)) {
        log.info("定时生成日报 {} ", now);
        generateReport(queryTodayAlerts());
    }
}
```

逻辑：`aiReportEnabled` 为 null（未设置，向后兼容）或 true 时正常生成；为 false 时跳过。

### 5. 修复 snapshotUrl 的 null 字符串 bug

**文件**：`backend_system/src/main/java/com/smartclass/monitor/service/ReportService.java`

修改 `queryTodayAlerts()`：

```java
public List<Map<String, Object>> queryTodayAlerts() {
    try {
        // ... 现有查询逻辑不变 ...
        return records.stream().map(a -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("alertType", a.getAlertType());
            m.put("level", a.getLevel());
            m.put("streamId", a.getStreamId());
            // 修复：null 时不放入 Map，避免 String.valueOf(null) 产生 "null" 字符串
            if (a.getSnapshotUrl() != null && !a.getSnapshotUrl().isBlank()) {
                m.put("snapshotUrl", a.getSnapshotUrl());
            }
            m.put("occurredAt", String.valueOf(a.getOccurredAt()));
            m.put("confidence", a.getConfidence());
            return m;
        }).collect(Collectors.toList());
    } catch (Exception e) {
        log.warn("查询今日告警失败: {}", e.getMessage());
        return Collections.emptyList();
    }
}
```

变更点：`m.put("snapshotUrl", a.getSnapshotUrl())` 改为先 null 检查，null 时不放入 Map。这样 `generateReport()` 中 `a.getOrDefault("snapshotUrl", "")` 会走默认值 `""`，`"".isBlank()` 为 true，不会进入截图处理逻辑。

### 6. 告警等级可配置

#### 6a. 前端 normalizeRule() 增加 level 映射

**文件**：`frontend/src/services/smartClassApi.js`

```javascript
export function normalizeRule(item = {}) {
  return {
    id: optional(item.id, item.rule_id),
    rule_type: optional(item.rule_type, item.ruleType || item.type || ""),
    name: optional(
      item.name,
      item.rule_name ||
        item.ruleName ||
        item.rule_type ||
        item.ruleType ||
        "未命名规则",
    ),
    enabled: item.enabled ?? item.status === "enabled",
    threshold_seconds:
      item.threshold_seconds ??
      item.thresholdSeconds ??
      item.duration_threshold ??
      1,
    confidence_threshold:
      item.confidence_threshold ??
      item.confidenceThreshold ??
      item.confidence ??
      null,
    cooldown_seconds: item.cooldown_seconds ?? item.cooldownSeconds ?? null,
    zone_type: optional(item.zone_type, item.zoneType || ""),
    summary: optional(item.summary, item.description || ""),
    level: optional(item.level, "warning"), // 新增
  };
}
```

#### 6b. 前端新增 updateRule() API 函数

**文件**：`frontend/src/services/smartClassApi.js`

```javascript
export async function updateRule(id, data) {
  return requestData(apiClient, {
    method: "put",
    url: `/rules/${id}`,
    data,
  });
}
```

#### 6c. 前端规则卡片增加等级选择器

**文件**：`frontend/src/App.vue`

在规则卡片的 `<article>` 中，在 `threshold_seconds` 控件和 `el-switch` 之间增加等级选择器：

```html
<article v-for="rule in rules" :key="rule.id">
  <div>
    <b>{{ ruleNameText(rule) }}</b>
    <span>{{ ruleSummaryText(rule) }}</span>
  </div>
  <div class="rule-threshold-control">
    <span>持续阈值（秒）</span>
    <el-input-number
      v-model="rule.threshold_seconds"
      :min="1"
      :max="30"
      size="small"
      :disabled="!isAdmin"
      @change="handleUpdateRule(rule)"
    />
  </div>
  <div class="rule-level-control">
    <span>告警等级</span>
    <el-select
      v-model="rule.level"
      size="small"
      :disabled="!isAdmin"
      @change="handleUpdateRule(rule)"
    >
      <el-option label="高危" value="high" />
      <el-option label="警告" value="warning" />
      <el-option label="提示" value="info" />
    </el-select>
  </div>
  <el-switch
    :model-value="rule.enabled"
    :disabled="!hasConfirmedForbiddenZone && isPhoneRelated(rule)"
    @change="handleToggleRule(rule)"
  />
</article>
```

#### 6d. 前端新增 handleUpdateRule()

**文件**：`frontend/src/App.vue`

```javascript
async function handleUpdateRule(rule) {
  const id = rule?.id;
  try {
    await updateRule(id, {
      threshold_seconds: rule.threshold_seconds,
      level: rule.level,
    });
  } catch (error) {
    ElMessage.error(userFacingError(error, "规则更新失败，请稍后重试。"));
  }
}
```

### 7. 日报卡片增加关闭按钮

**文件**：`frontend/src/App.vue`

在日报卡片顶部增加关闭按钮：

```html
<div v-if="latestReport" class="module-board" style="margin-bottom: 6px">
  <section class="panel span-12" style="padding: 12px 20px">
    <div
      style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px"
    >
      <h3>AI 日报</h3>
      <el-button size="small" text @click="latestReport = null">关闭</el-button>
    </div>
    <!-- 日报内容不变 -->
  </section>
</div>
```

注意：`latestReport` 将从 `alertSettings.latestReport` 分离为独立 ref（见 8a），所以 `v-if` 和 `@click` 都操作独立 ref。

### 8. 日报数据从 localStorage 分离

#### 8a. 将 latestReport 分离为独立 ref

**文件**：`frontend/src/App.vue`

```javascript
// 之前
const alertSettings = ref({
  dingtalkEnabled: saved.dingtalkEnabled ?? true,
  aiReportEnabled: saved.aiReportEnabled ?? true,
  ...
  latestReport: saved.latestReport ?? null,
  reportHistory: saved.reportHistory ?? [],
});

// 之后
const latestReport = ref(null);        // 独立 ref，不存 localStorage
const reportHistory = ref([]);         // 独立 ref，不存 localStorage

const alertSettings = ref({
  dingtalkEnabled: saved.dingtalkEnabled ?? true,
  aiReportEnabled: saved.aiReportEnabled ?? true,
  ...
  // 删除 latestReport 和 reportHistory
});
```

#### 8b. 页面加载时从后端获取最新日报

**文件**：`frontend/src/App.vue`

```javascript
async function loadLatestReport() {
  try {
    const resp = await fetch("http://127.0.0.1:8080/report/latest");
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.date) {
        latestReport.value = data;
      }
    }
  } catch {}
}

// 在 onMounted 或页面初始化时调用
loadLatestReport();
```

#### 8c. 生成日报后更新独立 ref

**文件**：`frontend/src/App.vue`

修改 `generateAiReport()` 函数，将结果存入独立 ref：

```javascript
const generateAiReport = async () => {
  alertSettings.value.generating = true;
  try {
    // ... 现有生成逻辑不变 ...
    if (report) {
      latestReport.value = report; // 存入独立 ref，不再存 alertSettings
    }
  } finally {
    alertSettings.value.generating = false;
  }
};
```

#### 8d. 模板中引用更新

所有模板中 `alertSettings.latestReport` 改为 `latestReport`，`alertSettings.reportHistory` 改为 `reportHistory`。

## Risks / Trade-offs

| 风险                                     | 影响                                                                                    | 缓解                                                                                                                           |
| ---------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **已有数据库 rule_type 不匹配**          | 修改 `seedRules()` 只影响新部署，已有数据库中 `fire_detected`/`zone_intrusion` 仍然存在 | 需要手动执行 SQL：`UPDATE behavior_rule SET rule_type='flame_detected' WHERE rule_type='fire_detected'` 等；或在部署文档中说明 |
| **已有数据库无 crowd_gathering 规则**    | 升级后人群聚集检测仍无规则记录，检测被跳过                                              | 需手动插入规则记录，或删除 `data/` 目录重新初始化                                                                              |
| **钉钉开关状态在 AI 服务重启后丢失**     | `AlertClient.dingtalk_enabled` 是内存状态，AI 服务重启后从 SpringBoot settings 恢复     | `_restore_dingtalk_settings()` 中已增加恢复逻辑，重启后自动同步                                                                |
| **zone_service 等级从 config_json 读取** | `stay_level`/`approach_level` 从 `config_json` 读取，需要用户在规则中配置               | fallback 到合理默认值（high/warning），不影响现有行为；后续可在前端增加配置 UI                                                 |
| **日报数据分离后首次加载变慢**           | 之前从 localStorage 即时读取，现在需等后端 API 响应                                     | 日报卡片在 API 返回前不显示，用户体验可接受；API 响应通常 <100ms                                                               |
| **规则 threshold_seconds 变更即时同步**  | `handleUpdateRule()` 在每次 `@change` 时调用 API，频繁操作可能产生多次请求              | `el-input-number` 的 `@change` 只在失焦或按回车时触发，不会连续调用；如需防抖可后续优化                                        |
