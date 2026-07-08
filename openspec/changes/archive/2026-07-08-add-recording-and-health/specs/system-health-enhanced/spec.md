## ADDED Requirements

### Requirement: Enhanced health check
`GET /system/health` SHALL return status for `backend`, `database`, `ai`, and `rtmp` components.

#### Scenario: All components healthy
- **WHEN** all components are reachable
- **THEN** each component SHALL be marked as "up"

#### Scenario: AI degraded
- **WHEN** AI `/model/status` is unreachable
- **THEN** `ai` SHALL be "down" and HTTP status SHALL still be 200

#### Scenario: Nginx degraded
- **WHEN** Nginx `/stat` is unreachable
- **THEN** `rtmp` SHALL be "down" and HTTP status SHALL still be 200

### Requirement: AI health probe uses /model/status
AiClient SHALL provide `checkHealth()` that calls `GET {AI}/model/status`.

### Requirement: Nginx health probe uses /stat
NginxClient SHALL provide `checkHealth()` that calls `GET /stat` and checks if response is valid XML.

### Requirement: Health endpoint does not require authentication
`/system/health` SHALL remain in JWT interceptor whitelist.
