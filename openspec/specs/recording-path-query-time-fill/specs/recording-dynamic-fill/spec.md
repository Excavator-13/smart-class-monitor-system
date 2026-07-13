## MODIFIED Requirements

### Requirement: AlertEventService.ingestAlert no longer looks up recording files

`AlertEventService.ingestAlert()` SHALL NOT query the `recording_file` table. The `RecordingFileMapper` SHALL NOT be injected into `AlertEventService`. The `record_path` and `event_time_offset` columns in the `alert_event` table SHALL remain NULL when ingested (unless explicitly provided by the AI service in the request body).

#### Scenario: Alert ingested without recording lookup

- **GIVEN** the AI service pushes an alert for stream `classroom_01` at `2026-07-13T08:30:17+08:00`
- **AND** a `recording_file` row exists for that stream and time
- **WHEN** `ingestAlert()` is called
- **THEN** the `alert_event` row SHALL have `record_path = NULL` and `event_time_offset = NULL`
- **AND** `RecordingFileMapper.findContainingRecording()` SHALL NOT be called

#### Scenario: Alert ingested with explicit record_path from AI (backward compatible)

- **GIVEN** the AI service pushes an alert with `recordPath = "/records/20260713/test.mp4"` and `eventTimeOffset = 5.0`
- **WHEN** `ingestAlert()` is called
- **THEN** the `alert_event` row SHALL have `record_path = "/records/20260713/test.mp4"` and `event_time_offset = 5.0`
- **AND** the values SHALL come directly from the request body, not from a database lookup

### Requirement: AlertService.mapToAlertVO dynamically fills recording info at query time

When mapping an `alert_event` row to `AlertVO`, if the `record_path` column is NULL and both `stream_id` and `occurred_at` are present, `AlertService` SHALL query `RecordingFileMapper.findContainingRecording(streamId, occurredAt)` to dynamically populate `recordUrl` and `eventTimeOffset`.

#### Scenario: Recording found at query time

- **GIVEN** an `alert_event` row with `record_path = NULL`, `stream_id = "classroom_01"`, `occurred_at = 2026-07-13T08:30:17`
- **AND** a `recording_file` row with `stream_id = "classroom_01"`, `started_at = 2026-07-13T08:30:00`, `ended_at = 2026-07-13T08:30:30`, `file_path = "/segments/20260713"`, `file_name = "classroom_01-2026-07-13-08_30_00.mp4"`
- **WHEN** `mapToAlertVO()` is called
- **THEN** `recordUrl` SHALL be `/records/20260713/classroom_01-2026-07-13-08_30_00.mp4` (`/segments` replaced with `/records`)
- **AND** `eventTimeOffset` SHALL be `17.0` (Duration.between startedAt and occurredAt in seconds)

#### Scenario: Recording not yet available at query time

- **GIVEN** an `alert_event` row with `record_path = NULL`, `stream_id = "classroom_01"`, `occurred_at = 2026-07-13T08:30:17`
- **AND** no `recording_file` row exists for that stream and time (recording not yet ingested)
- **WHEN** `mapToAlertVO()` is called
- **THEN** `recordUrl` SHALL be `null`
- **AND** `eventTimeOffset` SHALL be `null`

#### Scenario: record_path column already has value (no dynamic lookup)

- **GIVEN** an `alert_event` row with `record_path = "/records/20260713/custom.mp4"`, `event_time_offset = 5.0`
- **WHEN** `mapToAlertVO()` is called
- **THEN** `recordUrl` SHALL be `/records/20260713/custom.mp4` (directly from column)
- **AND** `eventTimeOffset` SHALL be `5.0` (directly from column)
- **AND** `findContainingRecording()` SHALL NOT be called

#### Scenario: stream_id or occurred_at is null (no dynamic lookup)

- **GIVEN** an `alert_event` row with `record_path = NULL`, `stream_id = NULL`
- **WHEN** `mapToAlertVO()` is called
- **THEN** `recordUrl` SHALL be `null`
- **AND** `eventTimeOffset` SHALL be `null`
- **AND** `findContainingRecording()` SHALL NOT be called

#### Scenario: Recording lookup exception handled gracefully

- **GIVEN** an `alert_event` row with `record_path = NULL`, `stream_id = "classroom_01"`, `occurred_at = 2026-07-13T08:30:17`
- **AND** `findContainingRecording()` throws an exception
- **WHEN** `mapToAlertVO()` is called
- **THEN** a warning SHALL be logged with the exception message
- **AND** `recordUrl` SHALL be `null`
- **AND** `eventTimeOffset` SHALL be `null`
- **AND** the exception SHALL NOT propagate to the caller

#### Scenario: eventTimeOffset negative value clamped to zero

- **GIVEN** a `recording_file` row with `started_at = 2026-07-13T08:30:20` (clock skew, after occurred_at)
- **AND** an `alert_event` with `occurred_at = 2026-07-13T08:30:17`
- **WHEN** `mapToAlertVO()` computes `Duration.between(startedAt, occurredAt)`
- **THEN** `eventTimeOffset` SHALL be `0.0` (clamped via `Math.max(0, offsetSeconds)`)

#### Scenario: Recording file_path with /segments prefix replaced

- **GIVEN** a `recording_file` row with `file_path = "/segments/20260713"`, `file_name = "classroom_01-2026-07-13-08_30_00.mp4"`
- **WHEN** `mapToAlertVO()` constructs `recordUrl`
- **THEN** `recordUrl` SHALL be `/records/20260713/classroom_01-2026-07-13-08_30_00.mp4`

#### Scenario: Recording file_path without /segments prefix (no replacement)

- **GIVEN** a `recording_file` row with `file_path = "/data/recordings/20260713"`, `file_name = "classroom_01.mp4"`
- **WHEN** `mapToAlertVO()` constructs `recordUrl`
- **THEN** `recordUrl` SHALL be `/data/recordings/20260713/classroom_01.mp4` (no replacement applied)

#### Scenario: Recording file_path is null

- **GIVEN** a `recording_file` row with `file_path = NULL`, `file_name = "classroom_01-2026-07-13-08_30_00.mp4"`
- **WHEN** `mapToAlertVO()` constructs `recordUrl`
- **THEN** `recordUrl` SHALL be `/classroom_01-2026-07-13-08_30_00.mp4` (only file_name with leading `/`)
