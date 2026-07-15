## ADDED Requirements

### Requirement: List video streams
The system SHALL provide `GET /streams` returning a paginated list of video sources. Each record MUST include both `id` (database primary key) and `stream_id` (business identifier).

#### Scenario: List all streams
- **WHEN** `GET /streams` is called with optional `status` and `keyword` filters
- **THEN** the response SHALL include `records` with `id` and `stream_id` for each stream

### Requirement: Create video stream
The system SHALL provide `POST /streams` accepting `stream_name`, `stream_id`, `rtmp_url`, `remark`. `stream_id` MUST be unique. `rtmp_url` MUST follow format `rtmp://<host>:9090/live/{stream_id}`.

#### Scenario: Create stream successfully
- **WHEN** valid `stream_name`, `stream_id`, `rtmp_url` are submitted
- **THEN** the response SHALL have `code: 0` and the new stream's `id`

#### Scenario: Duplicate stream_id
- **WHEN** a `stream_id` that already exists is submitted
- **THEN** the response SHALL have `code: 409`

### Requirement: Get stream detail by id
The system SHALL provide `GET /streams/{id}` returning stream details by database primary key.

#### Scenario: Stream found
- **WHEN** `GET /streams/{id}` is called with a valid id
- **THEN** the response SHALL contain stream detail including `stream_name`, `stream_id`, `rtmp_url`, `status`, `remark`

#### Scenario: Stream not found
- **WHEN** `GET /streams/{id}` is called with a non-existent id
- **THEN** the response SHALL have `code: 404`

### Requirement: Update video stream
The system SHALL provide `PUT /streams/{id}` accepting `stream_name`, `rtmp_url`, `status`, `remark`.

#### Scenario: Update stream successfully
- **WHEN** valid fields are submitted for an existing stream
- **THEN** the response SHALL have `code: 0`

### Requirement: Delete video stream (soft delete)
The system SHALL provide `DELETE /streams/{id}` that sets `deleted_at` instead of physically removing the record.

#### Scenario: Soft delete stream
- **WHEN** `DELETE /streams/{id}` is called for an existing stream
- **THEN** the stream's `deleted_at` SHALL be set and the stream SHALL no longer appear in `GET /streams`

### Requirement: Get enabled streams
The system SHALL provide `GET /streams/enabled` returning streams with `status = 'enabled'` and `deleted_at IS NULL`.

#### Scenario: Get enabled streams
- **WHEN** `GET /streams/enabled` is called
- **THEN** only streams with `status = 'enabled'` SHALL be returned
