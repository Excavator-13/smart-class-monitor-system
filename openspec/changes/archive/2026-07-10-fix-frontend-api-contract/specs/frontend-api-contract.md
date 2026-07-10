## FIXED Requirements

### Requirement: Alert stats field names match backend contract

`fetchAlertStats` SHALL use field names `today_total` and `unhandled_count` to match `GET /alert-stats` response defined in SpringBoot doc §2.4. The legacy names `today_alerts` and `pending_alerts` SHALL NOT be used.

#### Scenario: Stats card displays today_total

- **WHEN** backend returns `{ today_total: 42, unhandled_count: 5, by_type: [...] }`
- **THEN** the "今日告警" metric card SHALL display `42`

#### Scenario: Stats card displays unhandled_count

- **WHEN** backend returns `{ today_total: 42, unhandled_count: 5, by_type: [...] }`
- **THEN** the "待处理告警" metric card SHALL display `5`

### Requirement: Stream status distinguishes config status from push status

`GET /streams` returns `status` as config status (`enabled`/`disabled`), NOT push status (`online`/`offline`). The `onlineStreamCount` computation SHALL NOT filter by `stream.status === "online"`. Instead, it SHALL count streams whose config status is `enabled`, or use `GET /streams/{stream_id}/status` to determine online/offline.

#### Scenario: Stream list with enabled/disabled config

- **WHEN** backend returns streams with `status: "enabled"` or `status: "disabled"`
- **THEN** `onlineStreamCount` SHALL NOT be `0` simply because no stream has `status: "online"`

#### Scenario: Mock data uses config status values

- **WHEN** mock fallback data is used
- **THEN** `mockStreams` items SHALL have `status: "enabled"` or `status: "disabled"`, NOT `"online"` or `"offline"`

### Requirement: Paginated list fallback uses records key

`fetchAlerts` and `fetchStudents` fallback data SHALL use the `records` key to match the `PageResult` structure defined in SpringBoot doc (`{ records, page, page_size, total }`), NOT `list`.

#### Scenario: Alerts fallback structure

- **WHEN** backend is unreachable and fallback data is used
- **THEN** the fallback SHALL be `{ records: mockAlerts, total: mockAlerts.length }`

#### Scenario: Students fallback structure

- **WHEN** backend is unreachable and fallback data is used
- **THEN** the fallback SHALL be `{ records: mockStudents, total: mockStudents.length }`

### Requirement: Analysis events fallback uses AI event format

`fetchAnalysisEvents` fallback data SHALL use AI module event fields (`event_type`, `event_name`, `event_status`, `level`, `confidence`, `occurred_at`), NOT SpringBoot alert fields (`alert_type`, `alert_status`).

#### Scenario: Fallback event has event_type not alert_type

- **WHEN** AI service is unreachable and fallback data is used
- **THEN** each fallback event SHALL contain `event_type` (e.g. `"stranger_detected"`) instead of `alert_type`

#### Scenario: Fallback event has event_status not alert_status

- **WHEN** AI service is unreachable and fallback data is used
- **THEN** each fallback event SHALL contain `event_status` (e.g. `"confirmed"`) instead of `alert_status`

### Requirement: System health mock uses backend field name

`mockHealth` and `normalizeHealth` SHALL use the field name `backend` to match `GET /system/health` response defined in SpringBoot doc §10.1. The legacy name `api` SHALL NOT be used in mock data.

#### Scenario: Health mock matches backend contract

- **WHEN** mock fallback data is used
- **THEN** `mockHealth` SHALL contain `{ backend: "online", database: "online", ai: "online", rtmp: "online" }`

#### Scenario: normalizeHealth reads backend field

- **WHEN** backend returns `{ backend: "up", database: "up", ai: "up", rtmp: "up" }`
- **THEN** `normalizeHealth` SHALL correctly map `backend` to the internal representation

### Requirement: Alert stats does not send unsupported stream_id

`fetchAlertStats` SHALL NOT send `stream_id` as a query parameter, because `GET /alert-stats` does not accept it per SpringBoot doc §2.4.

#### Scenario: Alert stats call without stream_id

- **WHEN** `loadDashboard` calls `fetchAlertStats`
- **THEN** the request SHALL NOT include `stream_id` in query parameters

### Requirement: Vite proxy AI target port matches AI doc default

The Vite dev server proxy for `/ai` SHALL default to `http://localhost:5001` to match the AI module default port defined in `config/app.yaml`, NOT `http://localhost:5000`.

#### Scenario: AI proxy targets port 5001

- **WHEN** `VITE_AI_BASE` environment variable is not set
- **THEN** the `/ai` proxy target SHALL be `http://localhost:5001`

### Requirement: Mock data alert fields match AlertVO contract

`mockAlerts` items SHALL include fields defined in SpringBoot doc §2.1 AlertVO: `stream_name`, `student_id`, `student_name`, `handled_at`, `remark` (nullable is acceptable), in addition to existing fields.

#### Scenario: Mock alert has stream_name

- **WHEN** mock fallback data is used
- **THEN** each mock alert SHALL contain `stream_name` field
