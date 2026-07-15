## ADDED Requirements

### Requirement: Paginated operation log query
`GET /operation-logs` SHALL support filters: `user_id`, `action`, `target_type`, `target_id`, `time_range`. Pagination: `records/page/page_size/total`.

### Requirement: Operation log fields
Each record SHALL include: `id`, `user_id`, `username`, `action`, `target_type`, `target_id`, `method`, `request_uri`, `request_ip`, `result_code`, `result_message`, `created_at`.

### Requirement: Sensitive data exclusion
`request_body` SHALL NOT contain `password`, `token`, `feature_vector`.

### Requirement: No frontend modification
This change SHALL only affect SpringBoot backend code.
