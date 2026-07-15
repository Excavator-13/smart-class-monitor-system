## MODIFIED Requirements

### Requirement: alert_event record_path and event_time_offset populated by AI

The `alert_event` table columns `record_path` and `event_time_offset` SHALL be populated when the AI service pushes a confirmed alert that has a corresponding recording segment. Previously these columns were always NULL because the AI service never passed values for them.

#### Scenario: Alert ingested with recording info

- **GIVEN** the AI service detects a confirmed event on stream `classroom_01` at `2026-07-13T08:30:17+08:00`
- **WHEN** the alert is ingested via `POST /alerts/ai`
- **THEN** the `alert_event` row SHALL have `record_path = "/records/20260713/classroom_01-2026-07-13-08_30_00.mp4"`
- **AND** `event_time_offset = 17.000`

#### Scenario: Alert without recording info (backward compatible)

- **GIVEN** the AI service pushes an alert for a `stream_offline` event (no recording segment)
- **WHEN** the alert is ingested via `POST /alerts/ai`
- **THEN** `record_path` SHALL be NULL
- **AND** `event_time_offset` SHALL be NULL

### Requirement: AlertVO includes event_time_offset in API response

The `GET /alerts` and `GET /alerts/{id}` responses SHALL include `event_time_offset` in the returned alert data, mapped from the `alert_event.event_time_offset` column.

#### Scenario: Alert detail includes event_time_offset

- **GIVEN** an `alert_event` row with `event_time_offset = 17.000`
- **WHEN** `GET /alerts/{id}` is called
- **THEN** the response SHALL include `event_time_offset = 17.0`

#### Scenario: Alert with null event_time_offset

- **GIVEN** an `alert_event` row with `event_time_offset = NULL`
- **WHEN** `GET /alerts/{id}` is called
- **THEN** the response SHALL include `event_time_offset = null`
