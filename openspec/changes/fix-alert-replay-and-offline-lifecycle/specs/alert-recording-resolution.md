## MODIFIED Requirements

### Requirement: Alert replay resolves only segment MP4 recordings

当 `alert_event.record_path` 为空时，SpringBoot 必须使用 `stream_id + occurred_at` 动态查找包含事件时刻的 `source_type='segment'` MP4，不得用完整 `nginx_record` 作为异常片段回放结果。

#### Scenario: Segment and complete recording both contain the event

- **GIVEN** 同一事件时刻同时落在 `segment` 和 `nginx_record` 两条记录范围内
- **WHEN** `/alerts` 或 `/alerts/{id}` 解析录像
- **THEN** 系统 SHALL 选择 `segment` MP4
- **AND** `record_url` SHALL 使用 `/records/{date}/{filename}.mp4`

#### Scenario: No segment contains the event

- **GIVEN** 只有完整录像覆盖事件时刻，或没有切片索引覆盖事件时刻
- **WHEN** 后端解析异常录像
- **THEN** `record_url` SHALL 为 null
- **AND** `event_time_offset` SHALL 为 null
- **AND** 系统 SHALL NOT 返回根目录双斜杠形式的完整录像 URL
