## ADDED Requirements

### Requirement: AI resolves recording segment path from event time

When a confirmed event is pushed to SpringBoot, the AI service SHALL compute the corresponding 30-second segment's relative path and the event's offset within that segment, based on the event's `occurred_at` timestamp and the `stream_id`.

#### Scenario: Event maps to correct segment

- **GIVEN** a confirmed event with `stream_id = "classroom_01"` and `occurred_at = "2026-07-13T08:30:17+08:00"`
- **AND** segment duration is 30 seconds
- **WHEN** `_resolve_record_segment()` is called
- **THEN** `record_path` SHALL be `/records/20260713/classroom_01-2026-07-13-08_30_00.mp4`
- **AND** `event_time_offset` SHALL be `17.0`

#### Scenario: Event at exact segment boundary

- **GIVEN** a confirmed event with `occurred_at = "2026-07-13T08:30:30+08:00"`
- **WHEN** `_resolve_record_segment()` is called
- **THEN** `record_path` SHALL be `/records/20260713/classroom_01-2026-07-13-08_30_30.mp4`
- **AND** `event_time_offset` SHALL be `0.0`

#### Scenario: Event at last second of segment

- **GIVEN** a confirmed event with `occurred_at = "2026-07-13T08:30:29+08:00"`
- **WHEN** `_resolve_record_segment()` is called
- **THEN** `record_path` SHALL be `/records/20260713/classroom_01-2026-07-13-08_30_00.mp4`
- **AND** `event_time_offset` SHALL be `29.0`

#### Scenario: Event near midnight cross-day boundary

- **GIVEN** a confirmed event with `occurred_at = "2026-07-13T23:59:45+08:00"`
- **WHEN** `_resolve_record_segment()` is called
- **THEN** `record_path` SHALL be `/records/20260713/classroom_01-2026-07-13-23_59_30.mp4`
- **AND** `event_time_offset` SHALL be `15.0`

#### Scenario: Event in early morning

- **GIVEN** a confirmed event with `occurred_at = "2026-07-13T00:00:05+08:00"`
- **WHEN** `_resolve_record_segment()` is called
- **THEN** `record_path` SHALL be `/records/20260713/classroom_01-2026-07-13-00_00_00.mp4`
- **AND** `event_time_offset` SHALL be `5.0`

### Requirement: Recording segment configuration

The AI service SHALL read segment recording configuration from `config/app.yaml` under a `recording` section, with environment variable overrides.

| Config key                  | Env var                     | Description                       | Default    |
| --------------------------- | --------------------------- | --------------------------------- | ---------- |
| `recording.segment_seconds` | `RECORDING_SEGMENT_SECONDS` | Segment duration in seconds       | `30`       |
| `recording.segment_dir`     | `RECORDING_SEGMENT_DIR`     | Relative path prefix for segments | `/records` |

#### Scenario: Default segment duration

- **GIVEN** no `recording.segment_seconds` is configured
- **WHEN** `_resolve_record_segment()` is called
- **THEN** the segment duration SHALL be 30 seconds

#### Scenario: Custom segment duration

- **GIVEN** `recording.segment_seconds` is configured as `60`
- **WHEN** `_resolve_record_segment()` is called
- **THEN** segments SHALL be calculated at 60-second boundaries

### Requirement: push_alert includes record_path and event_time_offset

When `AnalysisService.analyze_frame()` confirms an event and calls `AlertClient.push_alert()`, it SHALL pass the resolved `record_path` and `event_time_offset` values.

#### Scenario: Confirmed event includes recording info

- **GIVEN** a confirmed event for stream `classroom_01` at `2026-07-13T08:30:17+08:00`
- **WHEN** `push_alert()` is called
- **THEN** the payload SHALL include `record_path = "/records/20260713/classroom_01-2026-07-13-08_30_00.mp4"`
- **AND** the payload SHALL include `event_time_offset = 17.0`

#### Scenario: Recording segment not yet available

- **GIVEN** a confirmed event occurs and the corresponding segment MP4 has not yet been produced by FFmpeg (still recording)
- **WHEN** `push_alert()` is called
- **THEN** `record_path` and `event_time_offset` SHALL still be computed and sent
- **AND** the segment file SHALL become available within 30 seconds

### Requirement: push_alert passes event_time_offset to map_event_to_alert

The `AlertClient.push_alert()` method SHALL accept and forward `event_time_offset` to `map_event_to_alert()`.

#### Scenario: event_time_offset forwarded correctly

- **GIVEN** `push_alert(event, record_path="/records/...", event_time_offset=17.0)` is called
- **WHEN** `map_event_to_alert()` constructs the payload
- **THEN** the payload SHALL include `event_time_offset = 17.0`

#### Scenario: event_time_offset defaults to None

- **GIVEN** `push_alert(event)` is called without `event_time_offset`
- **WHEN** `map_event_to_alert()` constructs the payload
- **THEN** the payload SHALL include `event_time_offset = None`
## MODIFIED Requirements

### Requirement: Alert replay resolves only segment MP4 recordings

当告警自身没有持久化录像路径时，SpringBoot 必须根据 `stream_id + occurred_at` 查找包含事件时刻的 `source_type='segment'` MP4，不得用完整 `nginx_record` 作为异常片段回放结果。

#### Scenario: Segment and complete recording overlap

- **GIVEN** 同一事件时刻同时落在切片和完整录像时间范围内
- **WHEN** `/alerts` 或 `/alerts/{id}` 动态解析录像
- **THEN** 系统 SHALL 选择切片 MP4
- **AND** `record_url` SHALL 使用 `/records/{date}/{filename}.mp4`

#### Scenario: No segment contains the event

- **GIVEN** 只有完整录像覆盖事件时刻，或没有切片覆盖事件时刻
- **WHEN** 后端解析异常录像
- **THEN** `record_url` 和 `event_time_offset` SHALL 为 null
- **AND** 系统 SHALL NOT 返回完整录像根目录 URL
