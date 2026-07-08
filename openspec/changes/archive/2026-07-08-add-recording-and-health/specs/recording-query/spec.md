## ADDED Requirements

### Requirement: Paginated recording list
`GET /recordings` SHALL support `stream_id`, `time_range`, `event_id`, `page`, `page_size`. Pagination: `records/page/page_size/total`.

### Requirement: Recording file path
`file_path` SHALL be a relative path (starting with `/`). SHALL NOT contain server IP.

### Requirement: Recording fields
Each record SHALL include: `id`, `stream_id`, `file_name`, `file_path`, `file_ext`, `file_size`, `started_at`, `ended_at`, `duration_seconds`, `source_type`, `available`.
