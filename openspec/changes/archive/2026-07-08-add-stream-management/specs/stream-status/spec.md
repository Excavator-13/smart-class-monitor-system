## ADDED Requirements

### Requirement: Check stream push status via Nginx
The system SHALL provide `GET /streams/{stream_id}/status` that queries Nginx `/stat` XML and returns online/offline status. The path parameter `stream_id` is the business identifier (not database id).

#### Scenario: Stream is online
- **WHEN** Nginx `/stat` XML contains `<publish active="true"/>` for the target `stream_id`
- **THEN** the response SHALL include `online: true` and `uptime`

#### Scenario: Stream is offline
- **WHEN** Nginx `/stat` XML does not contain an active publish for the target `stream_id`
- **THEN** the response SHALL include `online: false`

#### Scenario: Stream not found in database
- **WHEN** `stream_id` does not match any record in `video_stream` table
- **THEN** the response SHALL have `code: 404`

#### Scenario: Nginx unreachable
- **WHEN** Nginx `/stat` request times out or fails
- **THEN** the response SHALL return `online: false` and status `unknown` (NOT HTTP 500)

### Requirement: Status endpoint does not proxy video
The `/streams/{stream_id}/status` endpoint SHALL NOT proxy or forward any video stream. It only returns metadata.

#### Scenario: No video data in response
- **WHEN** `GET /streams/{stream_id}/status` is called
- **THEN** the response SHALL contain only JSON metadata (no binary video data)
