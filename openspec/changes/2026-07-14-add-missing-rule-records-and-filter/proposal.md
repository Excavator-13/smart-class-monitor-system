# 补齐缺失规则记录 + AI 侧规则开关过滤

## Why

AI 侧有 6 种告警事件类型在 SpringBoot 的 `behavior_rule` 表中没有对应的规则记录：

| 缺失类型            | 说明         | 当前状态                                        |
| ------------------- | ------------ | ----------------------------------------------- |
| `stranger_detected` | 陌生人员检测 | 检测始终运行，无法通过前端关闭                  |
| `leave_seat`        | 离座检测     | AI 侧连检测代码都没写，但 `score_config` 已占位 |
| `stream_offline`    | 视频流中断   | 检测始终运行，无法通过前端关闭                  |
| `spoof_detected`    | 活体检测异常 | 检测始终运行，无法通过前端关闭                  |
| `deepfake_detected` | 换脸检测     | 检测始终运行，无法通过前端关闭                  |
| `abnormal_sound`    | 异常声学事件 | 检测始终运行，无法通过前端关闭                  |

这导致三个问题：

1. **前端规则页面看不到这些类型**——`GET /rules` 只返回 `behavior_rule` 表中的 6 条记录，前端无法展示和管理这 6 种类型
2. **这些类型的检测始终运行，无法通过前端关闭**——AI 侧 `analyze_frame()` 不检查规则开关，所有检测模块无条件执行
3. **`leave_seat` 连 AI 检测代码都没写**——但 `score_config` 表已有 `leave_seat` 配置，属于空壳占位

## What Changes

### 1. SpringBoot：补 6 条规则记录

在 `DataInitializer.seedRules()` 中追加 6 条规则种子数据：

- `stranger_detected`：陌生人员检测，默认启用
- `leave_seat`：离座检测，默认禁用（AI 侧还没写检测代码）
- `stream_offline`：视频流中断，默认启用
- `spoof_detected`：活体检测异常，默认启用
- `deepfake_detected`：换脸检测，默认启用
- `abnormal_sound`：异常声学事件，默认启用

阈值参数取自各模块当前的硬编码默认值，仅做占位。

### 2. AI 侧：加规则开关过滤

在 `AnalysisService` 中：

- 新增 `RULE_GOVERNED_TYPES` 常量集合，标识受规则开关管控的事件类型
- `analyze_frame()` 中遍历 `detected` 列表进入 `event_service.observe()` 之前，对 `RULE_GOVERNED_TYPES` 中的类型检查规则开关，关闭则跳过
- `observe_stream_offline()` 方法开头加同样的开关过滤

## Capabilities

### Modified Capabilities

- **rule-crud**：`GET /rules` 返回 12 条规则（原有 6 + 新增 6），前端规则页面可看到所有 12 种类型
- **ai-analysis**：`analyze_frame()` 和 `observe_stream_offline()` 受规则开关管控，关闭的类型不再产出告警

### New Capabilities

- **rule-governed-filter**：AI 侧新增规则开关过滤机制，`RULE_GOVERNED_TYPES` 中的事件类型受 `config_client.get_rule()` 管控

## Impact

### backend_system（Java / Spring Boot）

- `config/DataInitializer.java`：`seedRules()` 追加 6 条规则

### backend_ai（Python / Flask）

- `services/analysis_service.py`：新增 `RULE_GOVERNED_TYPES` 常量；`analyze_frame()` 加开关过滤；`observe_stream_offline()` 加开关过滤
