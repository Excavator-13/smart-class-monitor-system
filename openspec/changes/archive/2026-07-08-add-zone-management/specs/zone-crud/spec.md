## ADDED Requirements

### Requirement: List zones
The system SHALL provide `GET /zones` with optional `stream_id` and `zone_type` filters.

#### Scenario: Filter by stream_id
- **WHEN** `GET /zones?stream_id=classroom_01` is called
- **THEN** only zones for that stream SHALL be returned

#### Scenario: Filter by zone_type
- **WHEN** `GET /zones?zone_type=danger` is called
- **THEN** only danger zones SHALL be returned

### Requirement: Create zone
The system SHALL provide `POST /zones` accepting `stream_id`, `zone_name`, `zone_type`, `coordinates` (0-1 normalized JSON), `threshold_seconds`, `safe_distance`, `enabled`.

#### Scenario: Create zone successfully
- **WHEN** valid zone data is submitted
- **THEN** the response SHALL have `code: 0`

### Requirement: Get zone detail
`GET /zones/{id}` SHALL return zone detail by database primary key.

### Requirement: Update zone
`PUT /zones/{id}` SHALL update zone fields. After successful update, the system SHALL call AI `/config/reload`. Reload failure SHALL NOT block the update.

### Requirement: Soft delete zone
`DELETE /zones/{id}` SHALL set `deleted_at`. After deletion, the system SHALL call AI `/config/reload`.

### Requirement: Get zones by stream_id
`GET /streams/{stream_id}/zones` SHALL return all zones for a given `stream_id`.

### Requirement: zone_type enumeration
zone_type SHALL be one of: `danger`, `seat`, `phone_forbidden`, `roi`.

#### Scenario: Invalid zone_type
- **WHEN** an unrecognized `zone_type` is submitted
- **THEN** the response SHALL have `code: 400`
