## ADDED Requirements

### Requirement: AI writes confirmed alert via POST /alerts/ai
The system SHALL provide `POST /alerts/ai` accepting AI alert data. The endpoint SHALL be in `controller.ai` package. `event_id` SHALL be used for idempotency: duplicate `event_id` SHALL return the existing `alert_id` without creating a new record.

#### Scenario: New alert created
- **WHEN** AI posts a new `event_id` with valid fields
- **THEN** a new `alert_event` record SHALL be inserted with `status = "unhandled"`

#### Scenario: Duplicate event_id
- **WHEN** AI posts an `event_id` that already exists
- **THEN** the response SHALL contain the existing `alert_id` and `status`, and NO new record SHALL be inserted

#### Scenario: event_id is required
- **WHEN** `event_id` is missing from the request
- **THEN** the response SHALL have `code: 400`

### Requirement: Path fields must be relative
`snapshot_path` and `record_path` SHALL start with `/` and SHALL NOT contain `://` or `..`. Invalid paths SHALL be rejected with `code: 400`.

#### Scenario: Absolute URL rejected
- **WHEN** `snapshot_path` contains `http://`
- **THEN** the response SHALL have `code: 400`

### Requirement: AI alert ingest does NOT use /internal/ai/**
The endpoint SHALL be `POST /alerts/ai` exactly as defined in the interface doc v2.1.

### Requirement: AI alert ingest uses event_id not event_uid
The idempotent field SHALL be named `event_id`.

### Requirement: Alert ingest is in controller.ai
The controller SHALL be in `com.smartclass.monitor.controller.ai` package, tagged as `ai-internal-api`.
