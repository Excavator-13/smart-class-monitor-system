## ADDED Requirements

### Requirement: Nginx stat XML client
The system SHALL provide `NginxClient` in `com.smartclass.monitor.integration` that fetches and parses Nginx `/stat` XML. Connection timeout and read timeout SHALL be configurable.

#### Scenario: Parse active stream
- **WHEN** Nginx `/stat` returns XML with `<publish active="true"/>` for a given stream name
- **THEN** `NginxClient.getStreamStatus(streamId)` SHALL return online status with uptime

#### Scenario: Parse inactive stream
- **WHEN** Nginx `/stat` returns XML without a publish element for the stream
- **THEN** `NginxClient.getStreamStatus(streamId)` SHALL return offline status

#### Scenario: Nginx unreachable
- **WHEN** HTTP request to `/stat` fails or times out
- **THEN** `NginxClient.getStreamStatus(streamId)` SHALL return a degraded/unknown status (NOT throw unhandled exception)

### Requirement: Nginx stat URL configurable
The Nginx `/stat` URL SHALL be configurable via `application.yml` property `nginx.stat-url`.

#### Scenario: URL from configuration
- **WHEN** application starts
- **THEN** `NginxClient` SHALL read `nginx.stat-url` from configuration (default: `http://39.106.209.208:9092/stat`)
