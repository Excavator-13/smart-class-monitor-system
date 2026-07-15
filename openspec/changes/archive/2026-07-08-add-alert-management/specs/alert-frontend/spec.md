## ADDED Requirements

### Requirement: Paginated alert list
`GET /alerts` SHALL return paginated alerts. Filters: `time_range`, `alert_type`, `status`, `level`, `stream_id`. Pagination: `page`, `page_size`, `records`, `total`.

### Requirement: Alert detail
`GET /alerts/{id}` SHALL return alert detail including `stream_name`, `student_name`, `snapshot_url`, `record_url` as relative paths.

#### Scenario: Detail with relative paths
- **WHEN** alert detail is queried
- **THEN** `snapshot_url` SHALL be a relative path (e.g. `/snapshots/...`)
- **THEN** `record_url` SHALL be a relative path or null

### Requirement: Update alert status
`PUT /alerts/{id}/status` SHALL accept `status`, `handler_id`, `remark`. `handled_at` SHALL be set to current time. Status MUST be one of: `unhandled`, `processing`, `handled`, `false_alarm`, `ignored`.

#### Scenario: Valid status transition
- **WHEN** valid status and handler_id are submitted
- **THEN** `handled_at` SHALL be recorded and status SHALL be updated

#### Scenario: Invalid status
- **WHEN** status is not in the enum
- **THEN** response SHALL have `code: 400`

### Requirement: Alert statistics
`GET /alert-stats` SHALL return today's alert count, unhandled count, and breakdown by alert_type.

### Requirement: No IP in paths
`snapshot_url` and `record_url` SHALL NOT contain server IP addresses.
