## 1. dingtalk_service.py 签名与逻辑改造

- [x] 1.1 新增 `_format_occurred_at(iso_str)` 辅助函数，将 ISO 8601 转为 `YYYY-MM-DD HH:MM:SS`，异常时 fallback 返回原字符串
- [x] 1.2 `trigger_alert` 新增可选参数 `event_id: str | None = None` 和 `occurred_at: str | None = None`；`event_id` 为 `None` 时 fallback 到原 `evt_{timestamp}_{tid}` 生成逻辑
- [x] 1.3 `_step` 新增可选参数 `occurred_at: str | None = None`；内部将 `now = time.strftime(...)` 替换为 `alert_time`（来自 `occurred_at`）和 `report_time`（取当前时间）两个变量
- [x] 1.4 首次通知消息模板：`告警时间` 使用 `alert_time`，不显示"上报时间"
- [x] 1.5 告警升级消息模板：`告警时间` 使用 `alert_time`，新增 `上报时间：{report_time}`
- [x] 1.6 紧急升级消息模板：`告警时间` 使用 `alert_time`，新增 `上报时间：{report_time}`
- [x] 1.7 `_step` 内部定时器回调 `check()` 调用 `_step` 时传入 `occurred_at=occurred_at`

## 2. alert_client.py 传参补全

- [x] 2.1 `push_alert()` 中 `self.dingtalk()` 调用新增 `event_id=event.get("event_id")` 和 `occurred_at=event.get("occurred_at")` 关键字参数

## 3. 验证

- [ ] 3.1 验证：触发一个告警，钉钉消息中的事件ID与数据库 `alert_event.event_id` 一致
- [ ] 3.2 验证：逐级上报的三条消息中"告警时间"相同，均为事件发生时间
- [ ] 3.3 验证：升级消息和紧急升级消息中"上报时间"不同，分别为各自发送时间
- [ ] 3.4 验证：长按回复匹配到的事件ID可在数据库中查到对应告警记录
- [ ] 3.5 验证：不传 `event_id` 和 `occurred_at` 时（兼容场景）fallback 行为正常
