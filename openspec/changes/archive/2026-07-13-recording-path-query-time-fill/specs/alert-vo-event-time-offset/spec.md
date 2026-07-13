## ADDED Requirements

### Requirement: AlertVO includes eventTimeOffset field

The `AlertVO` response object SHALL include an `eventTimeOffset` field of type `Double` (nullable). This field represents the offset in seconds from the start of the recording segment to the moment the alert event occurred. It is used by the frontend video player to seek to the event position during replay.

#### Scenario: Alert with eventTimeOffset from dynamic lookup

- **GIVEN** an `alert_event` with `record_path = NULL`, `stream_id = "classroom_01"`, `occurred_at = 2026-07-13T08:30:17`
- **AND** a matching `recording_file` with `started_at = 2026-07-13T08:30:00`
- **WHEN** `GET /alerts` or `GET /alerts/{id}` is called
- **THEN** the response SHALL include `eventTimeOffset = 17.0`

#### Scenario: Alert with eventTimeOffset from database column

- **GIVEN** an `alert_event` with `event_time_offset = 5.0` and `record_path` is not NULL
- **WHEN** `GET /alerts/{id}` is called
- **THEN** the response SHALL include `eventTimeOffset = 5.0` (from column, no dynamic lookup)

#### Scenario: Alert with null eventTimeOffset

- **GIVEN** an `alert_event` with `record_path = NULL`, `event_time_offset = NULL`
- **AND** no matching `recording_file` found
- **WHEN** `GET /alerts/{id}` is called
- **THEN** the response SHALL include `eventTimeOffset = null`

#### Scenario: Frontend normalizeAlert maps eventTimeOffset

- **GIVEN** an API response alert with `eventTimeOffset = 17.0`
- **WHEN** `normalizeAlert()` is called
- **THEN** the normalized alert SHALL have `event_time_offset = 17.0`
- **AND** the existing mapping logic (`item.event_time_offset ?? item.eventTimeOffset ?? null`) SHALL continue to work
