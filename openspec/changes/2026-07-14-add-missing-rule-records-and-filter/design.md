# 补齐缺失规则记录 + AI 侧规则开关过滤 — 技术设计

## Context

### 已有基础设施

**规则数据模型**：`behavior_rule` 表存储规则，字段包括 `rule_type`、`rule_name`、`enabled`、`threshold_seconds`、`confidence_threshold`、`cooldown_seconds`、`config_json`。`DataInitializer.seedRules()` 在启动时幂等插入 6 条种子规则（`phone_usage`、`flame_detected`、`fall_detected`、`head_down`、`crowd_gathering`、`danger_zone`）。

**规则 CRUD API**：`RuleController` 提供 `GET /rules`、`POST /rules`、`PUT /rules/{id}`、`DELETE /rules/{id}`，前端规则页面通过 `GET /rules` 获取列表并展示开关。

**ConfigClient 规则缓存**：AI 侧 `ConfigClient.load_rules()` 从 `GET /rules` 拉取规则，存入 `self.cache.rules`（dict，key 为 `rule_type`，value 为规则 dict）。`get_rule(rule_type)` 返回 `self.cache.rules.get(rule_type, {})`。注意：`load_rules()` 只缓存 `enabled=True` 的规则，禁用的规则不在缓存中。

**AnalysisService 检测流程**：`analyze_frame()` 中各检测模块（face、zone、behavior、fire、anti_spoof、audio）将检测结果放入 `detected` 列表，然后遍历 `detected` 调用 `event_service.observe()` 确认告警。当前**不检查规则开关**，所有检测结果都会进入 observe 流程。

**observe_stream_offline()**：在 `stream_manager` 检测到视频流中断时调用，直接进入 `event_service.observe()`，不检查任何开关。

**score_config 表**：已有全部 15 种告警类型的评分配置（包括 `stranger_detected`、`leave_seat`、`stream_offline`、`spoof_detected`、`deepfake_detected`、`abnormal_sound`），不受本次改动影响。

### 缺失的 6 种类型

| rule_type           | AI 检测模块                                  | 当前是否有检测代码 | 当前行为                         |
| ------------------- | -------------------------------------------- | ------------------ | -------------------------------- |
| `stranger_detected` | `FaceService.recognize_frame()`              | ✅ 有              | 始终运行，无法关闭               |
| `leave_seat`        | 无                                           | ❌ 无              | 无检测代码，仅 score_config 占位 |
| `stream_offline`    | `StreamManager` + `observe_stream_offline()` | ✅ 有              | 始终运行，无法关闭               |
| `spoof_detected`    | `AntiSpoofService.detect()`                  | ✅ 有              | 始终运行，无法关闭               |
| `deepfake_detected` | `AntiSpoofService.detect()`                  | ✅ 有              | 始终运行，无法关闭               |
| `abnormal_sound`    | `AudioService.process_audio()`               | ✅ 有              | 始终运行，无法关闭               |

## Goals / Non-Goals

**Goals:**

1. `DataInitializer.seedRules()` 追加 6 条规则种子数据，`leave_seat` 默认禁用，其余 5 个默认启用
2. `AnalysisService` 新增 `RULE_GOVERNED_TYPES` 常量，标识受规则开关管控的事件类型
3. `analyze_frame()` 中对 `RULE_GOVERNED_TYPES` 内的事件类型检查规则开关，关闭则跳过 observe
4. `observe_stream_offline()` 开头加开关过滤，关闭则返回 skipped 事件

**Non-Goals:**

- 不改各模块的阈值读取逻辑（继续用硬编码/构造函数参数）
- 不改 `face_service`、`anti_spoof_service`、`audio_service`、`stream_manager` 的内部代码
- 不改 `score_config` 表（已经配齐）
- 不新增 `leave_seat` 的检测代码（后续单独做）
- 不改 `ConfigClient.load_rules()` 的缓存逻辑（已正确只缓存 enabled 规则）
- 不改 `behavior_rule` 表结构（不加 `level` 列，level 由 `score_config` 管理）

## Decisions

| 决策                                | 选择                                       | 理由                                                                                                                                            |
| ----------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 过滤位置                            | `analyze_frame()` 的 `detected` 遍历循环中 | 集中过滤，不改各检测模块内部代码，service 保持职责单一                                                                                          |
| `leave_seat` 默认状态               | `enabled=false`                            | AI 侧还没写检测代码，启用无意义                                                                                                                 |
| 其余 5 个默认状态                   | `enabled=true`                             | 与当前行为一致（这些模块本来就在跑），关闭是退步                                                                                                |
| 阈值参数取值                        | 各模块当前硬编码默认值                     | 仅做占位，本次不改 AI 侧阈值读取逻辑                                                                                                            |
| `observe_stream_offline()` 过滤方式 | 开头检查开关，关闭返回 skipped 事件        | 保持返回值结构一致（dict 含 event_type），调用方无需改动                                                                                        |
| `get_rule()` 返回空 dict 的语义     | 空 dict = 规则不存在或已禁用               | `load_rules()` 只缓存 enabled 规则，`get_rule()` 返回 `{}` 表示该类型未启用，过滤条件 `not self.config_client.get_rule(type)` 为 True，正确跳过 |
| 不在检测模块内部过滤                | 在 `analyze_frame()` 统一过滤              | 检测模块仍正常执行（如人脸识别用于其他目的），仅过滤告警产出                                                                                    |

## Architecture

### 数据流变更

```
analyze_frame(stream_id, frame)
      │
      │ 各检测模块正常执行，产出 detected 列表
      │
      ▼
  detected = [...]
      │
      │ ★ 新增：规则开关过滤
      │ for item in detected:
      │     if item["event_type"] in RULE_GOVERNED_TYPES
      │        and not config_client.get_rule(item["event_type"]):
      │         continue  ← 跳过 observe
      │
      ▼
  event_service.observe()  ← 仅通过过滤的检测项进入
      │
      ▼
  push_alert()
```

```
observe_stream_offline(stream_id)
      │
      │ ★ 新增：开关过滤
      │ if not config_client.get_rule("stream_offline"):
      │     return {"event_id": "", "event_type": "stream_offline",
      │             "event_status": "skipped", "level": "high", "confidence": 1.0}
      │
      ▼
  event_service.observe()
      │
      ▼
  push_alert()
```

### 新增规则种子数据

| rule_type           | rule_name    | enabled | threshold_seconds | confidence_threshold | cooldown_seconds |
| ------------------- | ------------ | ------- | ----------------- | -------------------- | ---------------- |
| `stranger_detected` | 陌生人员检测 | true    | 0                 | 0.45                 | 10               |
| `leave_seat`        | 离座检测     | false   | 10                | 0.60                 | 30               |
| `stream_offline`    | 视频流中断   | true    | 10                | 1.0                  | 30               |
| `spoof_detected`    | 活体检测异常 | true    | 0                 | 0.70                 | 30               |
| `deepfake_detected` | 换脸检测     | true    | 3                 | 0.70                 | 60               |
| `abnormal_sound`    | 异常声学事件 | true    | 0                 | 0.50                 | 15               |

说明：

- `threshold_seconds=0` 表示无需持续时间阈值，检测到即告警（适用于 `stranger_detected`、`spoof_detected`、`abnormal_sound`）
- `confidence_threshold` 取自各模块当前的硬编码默认值
- `cooldown_seconds` 为同类告警冷却时间，取合理默认值

### RULE_GOVERNED_TYPES 定义

```python
RULE_GOVERNED_TYPES = {
    "stranger_detected",
    "leave_seat",
    "stream_offline",
    "spoof_detected",
    "deepfake_detected",
    "abnormal_sound",
}
```

这 6 个类型是本次新增规则记录的类型，需要受规则开关管控。原有的 6 个类型（`phone_usage`、`flame_detected`、`fall_detected`、`head_down`、`crowd_gathering`、`danger_zone`）已在各自的检测模块内部读取规则开关（如 `behavior_service` 读取 `rules.get("head_down")`，`fire_service` 读取 `rules.get("flame_detected")`），不需要在 `analyze_frame()` 层面重复过滤。

### createRule 方法签名

当前 `createRule` 方法签名为 6 参数（无 level），`behavior_rule` 表也没有 `level` 列。新增 6 条规则沿用现有签名，level 由 `score_config` 表管理，不存入 `behavior_rule`。
