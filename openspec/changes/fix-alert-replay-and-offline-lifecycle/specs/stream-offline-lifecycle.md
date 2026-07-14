## MODIFIED Requirements

### Requirement: Stream offline requires sustained unavailability

AI 服务必须将单次读取失败视为暂时不可用，只有连续不可用达到 `offline_after_seconds` 后才能确认 `stream_offline`。

#### Scenario: Transient read failure recovers before timeout

- **GIVEN** 视频流发生一次读取失败
- **WHEN** 流在 `offline_after_seconds` 之前恢复读取
- **THEN** 系统 SHALL NOT 上报 `stream_offline`
- **AND** 恢复后 SHALL 清除当前失败周期

#### Scenario: Stream remains unavailable through timeout

- **GIVEN** 视频流从时间 T 开始持续无法读取
- **WHEN** 连续不可用时间达到 `offline_after_seconds`
- **THEN** 系统 SHALL 上报一次 `stream_offline`
- **AND** 告警发生时间 SHALL 反映持续离线确认时刻

### Requirement: One continuous offline episode emits one alert

同一进程内，一个持续离线周期无论存在多少 `/video_feed` 消费者或轮询次数，都必须最多发出一次离线告警；读取成功后才开始新的周期。

#### Scenario: Repeated checks during one outage

- **GIVEN** 当前离线周期已经上报过 `stream_offline`
- **WHEN** 一个或多个视频请求继续检查同一离线状态
- **THEN** 系统 SHALL NOT 再次上报该周期

#### Scenario: Recovery followed by a new outage

- **GIVEN** 上一个离线周期已上报
- **AND** 视频读取随后成功恢复
- **WHEN** 新的连续失败再次达到离线超时
- **THEN** 系统 SHALL 上报一个具有新事件 ID 的离线事件

### Requirement: Failed reads do not analyze stale frames

当读取线程已判定当前帧不可用时，分析接口不得继续把旧帧作为新帧执行异常检测。

#### Scenario: Capture fails while a previous frame is cached

- **GIVEN** 流状态中缓存了上一帧
- **WHEN** 当前读取失败且进入失败周期
- **THEN** `get_frame` SHALL 返回 null
- **AND** 分析服务 SHALL NOT 对缓存旧帧产生新的行为或人员异常
