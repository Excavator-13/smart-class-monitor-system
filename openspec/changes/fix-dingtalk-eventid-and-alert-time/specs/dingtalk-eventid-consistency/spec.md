## Requirement: 钉钉事件ID与数据库一致

系统必须保证钉钉通知中的事件ID与数据库 `alert_event.event_id` 完全一致，使消息可双向关联。

### Scenario: 钉钉事件ID与入库事件ID相同

- GIVEN AI 检测到一个安全事件，`EventState` 生成 event_id = `evt_a3b2c1d4e5f67890`
- WHEN 系统调用 `push_alert(event)` 并触发钉钉通知
- THEN 钉钉群消息中显示「事件ID：evt_a3b2c1d4e5f67890」
- AND 数据库 `alert_event` 表中该告警的 `event_id` = `evt_a3b2c1d4e5f67890`

### Scenario: 长按回复匹配的事件ID可在数据库中查到

- GIVEN 钉钉群内有一条告警消息，事件ID = `evt_a3b2c1d4e5f67890`
- WHEN 用户长按该消息回复「已处理」
- THEN 系统解析到事件ID = `evt_a3b2c1d4e5f67890`
- AND 该事件ID可在数据库 `alert_event` 表中查到对应记录

## Requirement: 逐级上报告警时间一致性

同一事件的所有上报消息必须显示相同的"告警时间"（事件真实发生时间），逐级上报消息额外显示"上报时间"（本次消息发送时间）。

### Scenario: 首次通知显示事件发生时间

- GIVEN AI 检测到事件，`occurred_at` = `2026-07-15T10:00:00+08:00`
- WHEN 系统发送首次告警通知
- THEN 消息中「告警时间：2026-07-15 10:00:00」
- AND 消息中不包含"上报时间"字段

### Scenario: 告警升级显示相同的告警时间和不同的上报时间

- GIVEN 首次通知于 10:00:00 发出，事件 `occurred_at` = `2026-07-15T10:00:00+08:00`
- WHEN 45 秒后系统自动升级到上级
- THEN 升级消息中「告警时间：2026-07-15 10:00:00」（与首次通知一致）
- AND 升级消息中「上报时间：2026-07-15 10:00:45」（本次发送时间）

### Scenario: 紧急升级显示相同的告警时间

- GIVEN 事件 `occurred_at` = `2026-07-15T10:00:00+08:00`
- WHEN 逐级上报完成后仍无人响应，系统发送紧急升级消息
- THEN 紧急升级消息中「告警时间：2026-07-15 10:00:00」（与首次通知一致）
- AND 紧急升级消息中「上报时间」为本次发送时间

### Scenario: 无 occurred_at 时 fallback 到当前时间

- GIVEN `trigger_alert` 被调用时未传入 `occurred_at`（如测试脚本直接调用）
- WHEN 系统发送告警消息
- THEN 「告警时间」显示为消息发送时的当前时间
