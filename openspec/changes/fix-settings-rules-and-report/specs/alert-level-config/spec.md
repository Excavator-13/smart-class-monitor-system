## ADDED Requirements

### Requirement: AI detection services read alert level from rule configuration

Each AI detection service SHALL read the `level` field from its rule dict in `cache.rules`. When the rule does not contain a `level` field, the service SHALL fall back to a hardcoded default value.

| Event type              | Rule key          | Default level |
| ----------------------- | ----------------- | ------------- |
| `flame_detected`        | `flame_detected`  | `high`        |
| `phone_usage`           | `phone_usage`     | `info`        |
| `head_down`             | `head_down`       | `info`        |
| `crowd_gathering`       | `crowd_gathering` | `warning`     |
| `fall_detected`         | `fall_detected`   | `high`        |
| `danger_zone_intrusion` | `danger_zone`     | `high`        |
| `danger_zone_stay`      | `danger_zone`     | `high`        |
| `danger_zone_approach`  | `danger_zone`     | `warning`     |

#### Scenario: fire_service uses level from rule

- **GIVEN** `cache.rules["flame_detected"]` contains `{"level": "warning", ...}`
- **WHEN** `fire_service.detect()` produces a detection
- **THEN** the detection dict SHALL have `"level": "warning"`

#### Scenario: fire_service falls back to default level

- **GIVEN** `cache.rules["flame_detected"]` contains `{"confidence_threshold": 0.8}` (no `level` key)
- **WHEN** `fire_service.detect()` produces a detection
- **THEN** the detection dict SHALL have `"level": "high"` (default)

#### Scenario: phone_usage uses level from rule

- **GIVEN** `cache.rules["phone_usage"]` contains `{"level": "info", ...}`
- **WHEN** a `phone_usage` event is produced
- **THEN** the event dict SHALL have `"level": "info"`

#### Scenario: zone_service uses level from rule for intrusion

- **GIVEN** `cache.rules["danger_zone"]` contains `{"level": "high", ...}`
- **WHEN** a `danger_zone_intrusion` event is produced
- **THEN** the event dict SHALL have `"level": "high"`

#### Scenario: zone_service uses config_json for stay and approach levels

- **GIVEN** `cache.rules["danger_zone"]` contains `{"level": "high", "config_json": "{\"stay_level\":\"high\",\"approach_level\":\"warning\"}"}`
- **WHEN** a `danger_zone_stay` event is produced
- **THEN** the event dict SHALL have `"level": "high"`
- **WHEN** a `danger_zone_approach` event is produced
- **THEN** the event dict SHALL have `"level": "warning"`

#### Scenario: zone_service falls back to defaults for stay and approach levels

- **GIVEN** `cache.rules["danger_zone"]` contains `{"level": "high"}` (no config_json or no stay_level/approach_level)
- **WHEN** a `danger_zone_stay` event is produced
- **THEN** the event dict SHALL have `"level": "high"` (default)
- **WHEN** a `danger_zone_approach` event is produced
- **THEN** the event dict SHALL have `"level": "warning"` (default)

### Requirement: Frontend normalizes and displays rule level

The frontend `normalizeRule()` function SHALL map the `level` field from the API response. The rule card UI SHALL display a level selector that allows editing.

#### Scenario: normalizeRule maps level field

- **GIVEN** the API returns a rule with `level: "high"`
- **WHEN** `normalizeRule()` processes the rule
- **THEN** the result SHALL contain `level: "high"`

#### Scenario: normalizeRule defaults level to warning

- **GIVEN** the API returns a rule without a `level` field
- **WHEN** `normalizeRule()` processes the rule
- **THEN** the result SHALL contain `level: "warning"` (default)

#### Scenario: Rule card displays level selector

- **WHEN** a rule card is rendered
- **THEN** an `el-select` with options "高危" (`high`), "警告" (`warning`), "提示" (`info`) SHALL be displayed

#### Scenario: Changing level saves to backend

- **WHEN** the user changes the level selector to "高危"
- **THEN** `updateRule(id, { level: "high", threshold_seconds: ... })` SHALL be called
- **AND** the backend `PUT /rules/{id}` SHALL update the rule's `level` field

### Requirement: Frontend updateRule API function

The frontend SHALL provide an `updateRule(id, data)` function that calls `PUT /rules/{id}` with a request body containing the fields to update.

#### Scenario: updateRule calls PUT /rules/{id}

- **WHEN** `updateRule(5, { level: "high", threshold_seconds: 10 })` is called
- **THEN** an HTTP `PUT /rules/5` request SHALL be sent with body `{ "level": "high", "threshold_seconds": 10 }`

#### Scenario: Rule threshold_seconds change saves to backend

- **WHEN** the user changes the threshold_seconds input on a rule card
- **THEN** `updateRule(id, { threshold_seconds, level })` SHALL be called
- **AND** the backend SHALL persist the change
