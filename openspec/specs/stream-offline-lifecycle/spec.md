# Stream Offline Lifecycle Specification

## Requirement: Stream offline requires sustained unavailability

AI 服务必须将单次读取失败视为暂时不可用，只有连续不可用达到 `offline_after_seconds` 后才能确认 `stream_offline`。

### Scenario: Transient failure recovers before timeout

- **GIVEN** 视频流发生一次读取失败
- **WHEN** 流在离线超时之前恢复
- **THEN** 系统 SHALL NOT 上报 `stream_offline`
- **AND** 系统 SHALL 清除失败周期

### Scenario: Failure reaches timeout

- **GIVEN** 视频流持续无法读取
- **WHEN** 连续失败达到 `offline_after_seconds`
- **THEN** 系统 SHALL 上报一次 `stream_offline`

## Requirement: One continuous offline episode emits one alert

同一进程内，一个持续离线周期无论存在多少视频消费者或检查次数，都必须最多发出一次离线告警；读取成功后才开始新的周期。

### Scenario: Repeated checks during one outage

- **GIVEN** 当前离线周期已经上报
- **WHEN** 一个或多个消费者继续检查离线状态
- **THEN** 系统 SHALL NOT 重复上报该周期

### Scenario: Recovery followed by a new outage

- **GIVEN** 上一个离线周期已经上报且视频随后恢复
- **WHEN** 新的连续失败再次达到超时
- **THEN** 系统 SHALL 上报具有新事件 ID 的离线事件

## Requirement: Failed reads do not analyze stale frames

进入连续失败周期后，AI 服务不得把缓存旧帧当作新帧继续执行异常检测。

### Scenario: Previous frame remains cached after failure

- **GIVEN** 流状态缓存了上一帧
- **WHEN** 当前读取已经失败
- **THEN** `get_frame` SHALL 返回 null
- **AND** 分析服务 SHALL NOT 基于该旧帧生成新的行为异常
