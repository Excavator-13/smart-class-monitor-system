## Requirement: 回复精确停止
系统必须支持根据回复的消息内容匹配事件ID，精确停止单个告警的上报链。
系统必须保证相同内容的两条告警不会互相干扰。

### Scenario: 相同消息不同事件
- GIVEN 两条内容相同的告警同时运行
- WHEN 用户回复「已处理 evt_A」
- THEN 只停止事件A
- AND 事件B继续上报

### Scenario: 逐级上报 text 通知
- GIVEN 负责人超过 45 秒未响应
- WHEN 系统执行逐级上报
- THEN 发送 text 消息（蓝色 @上级）
- AND 消息包含同一事件ID

### Scenario: 消息带事件ID
- GIVEN 告警链的每一级（负责人/逐级/@全体）
- WHEN 发送消息时
- THEN 每条消息底部包含「事件ID：evt_xxx」
