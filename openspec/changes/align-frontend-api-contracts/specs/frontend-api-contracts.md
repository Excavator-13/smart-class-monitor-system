# Frontend API Contract Alignment

## ADDED Requirements

### Requirement: Explicit Mock Mode

The frontend SHALL only use local mock data when explicit mock mode is enabled through runtime config `USE_MOCK` or build env `VITE_USE_MOCK=true`.

#### Scenario: API fails while mock mode is disabled

- **WHEN** a SpringBoot or AI request fails
- **THEN** the frontend SHALL surface an error or empty state
- **AND** SHALL NOT replace the response with mock data.

#### Scenario: API fails while mock mode is enabled

- **WHEN** a request fails and mock mode is enabled
- **THEN** the frontend MAY return local mock data for offline UI development.

### Requirement: Envelope Unwrapping

The frontend SHALL unwrap documented response envelopes and treat non-zero `code` as request failure.

#### Scenario: Successful response

- **WHEN** an API returns `{ "code": 0, "data": ... }`
- **THEN** the service layer SHALL return `data` to callers.

#### Scenario: Business error response

- **WHEN** an API returns `{ "code": nonzero, "message": "..." }`
- **THEN** the service layer SHALL throw an error containing the backend message.

### Requirement: API-Derived Phone Violation UI

The frontend SHALL derive phone violation display from confirmed forbidden zone and API-returned phone event/alert target coordinates.

#### Scenario: No confirmed forbidden zone

- **WHEN** no forbidden zone is confirmed
- **THEN** phone violation labels, heat points, and alert cards SHALL NOT be shown as active violations.

#### Scenario: Confirmed zone without intersecting phone target

- **WHEN** a forbidden zone is confirmed but no phone target bbox intersects it
- **THEN** the UI SHALL show that the zone is monitored without phone violation.

#### Scenario: Intersecting phone target

- **WHEN** an API-returned phone event/alert target bbox intersects the confirmed forbidden zone
- **THEN** the UI MAY show phone violation annotations and related alerts.

### Requirement: Media Path Separation

The frontend SHALL keep application static assets out of `/media` and reserve `/media` for Nginx-proxied classroom media resources.

#### Scenario: GIF or UI asset

- **WHEN** the frontend displays a bundled UI image/GIF
- **THEN** it SHALL import the asset from `src/assets` or another non-proxied static path.
