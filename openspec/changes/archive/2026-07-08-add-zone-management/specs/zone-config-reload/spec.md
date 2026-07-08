## ADDED Requirements

### Requirement: Notify AI on zone config change
After creating, updating, or deleting a zone, the system SHALL call `POST {AI}/config/reload` with the affected `stream_id` and `reload_items` containing `"zones"`. Failure SHALL be logged but SHALL NOT roll back the database transaction.

#### Scenario: Reload succeeds
- **WHEN** zone is updated and AI reload returns success
- **THEN** the zone update response SHALL have `code: 0`

#### Scenario: Reload fails
- **WHEN** zone is updated but AI reload fails
- **THEN** the zone update response SHALL still have `code: 0`
- **THEN** the failure SHALL be logged

### Requirement: AiClient supports config reload
`AiClient` SHALL provide `reloadConfig(String streamId, List<String> reloadItems)` calling `POST /config/reload`.

#### Scenario: Full reload
- **WHEN** `reloadConfig("classroom_01", ["zones"])` is called
- **THEN** the request body SHALL include `stream_id` and `reload_items`
