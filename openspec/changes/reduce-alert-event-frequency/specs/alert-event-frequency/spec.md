# Alert Event Frequency Specification

## Requirement: 时间阈值表示连续出现时长

系统必须仅在同一视频流中的同类异常连续出现达到 `threshold_seconds` 后确认事件。

### Scenario: 连续观察达到阈值

- GIVEN 某事件的时间阈值为 3 秒
- WHEN 同类异常在连续性容忍间隔内持续被观察超过 3 秒
- THEN 系统确认该事件一次

### Scenario: 观察中断后重新计时

- GIVEN 某候选事件尚未确认
- WHEN 两次观察间隔超过 `continuity_gap_seconds`
- THEN 系统开始新的异常周期
- AND 持续时长从 0 重新计算

## Requirement: 同一连续周期只告警一次

同一视频流中的同类异常在持续存在期间必须只产生一次确认信号。

### Scenario: 异常持续时间超过冷却时间

- GIVEN 某异常周期已确认
- WHEN 异常持续存在且经过一个或多个冷却周期
- THEN 系统不得再次确认该周期
- AND 不得再次触发截图、入库或钉钉通知

## Requirement: 冷却按视频流和事件类型生效

系统必须以 `(stream_id, event_type)` 作为冷却维度，不得因目标标识变化绕过冷却。

### Scenario: 同类型目标变化

- GIVEN 某视频流的某类事件刚刚确认
- WHEN 同类异常以另一个目标标识出现且仍处于冷却期
- THEN 系统不得确认新的告警

### Scenario: 冷却结束后的新周期

- GIVEN 前一异常已经结束
- AND 同类事件冷却已经结束
- WHEN 新异常周期达到时间阈值
- THEN 系统确认新事件
- AND 新事件使用不同的事件 ID

## Requirement: 内存事件流按事件周期去重

系统必须保证一个事件 ID 在内存事件流中最多存在一条记录。

### Scenario: 候选事件被逐帧观察

- WHEN 同一异常周期被连续观察多次
- THEN 查询结果中只保留一条该事件记录
- AND 记录反映最新持续时长与状态

### Scenario: 多个直播请求并发分析

- GIVEN 多个客户端同时读取同一视频流
- WHEN 多个线程同时观察到同一类异常
- THEN 系统只返回一次确认信号
