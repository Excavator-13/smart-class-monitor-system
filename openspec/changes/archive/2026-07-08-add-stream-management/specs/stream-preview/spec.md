## ADDED Requirements

### Requirement: Return preview URLs
The system SHALL provide `GET /streams/{stream_id}/preview-url` returning MJPEG, RTMP, and HLS playback URLs. The endpoint SHALL NOT proxy or forward video streams.

#### Scenario: Return preview URLs
- **WHEN** `GET /streams/{stream_id}/preview-url` is called for an existing stream
- **THEN** the response SHALL include `mjpeg_url`, `rtmp_url`, `hls_url` as URL strings

#### Scenario: Stream not found
- **WHEN** `stream_id` does not exist
- **THEN** the response SHALL have `code: 404`

### Requirement: No video proxying
The preview-url endpoint SHALL return address strings only. SpringBoot SHALL NOT read or forward video stream bytes.

#### Scenario: Response is JSON metadata only
- **WHEN** `GET /streams/{stream_id}/preview-url` is called
- **THEN** the response Content-Type SHALL be `application/json` (not video/*)
