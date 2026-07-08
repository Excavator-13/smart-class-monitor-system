## ADDED Requirements

### Requirement: List rules
`GET /rules` SHALL return rules, optionally filtered by `rule_type`.

### Requirement: Create rule
`POST /rules` SHALL accept `rule_type`, `rule_name`, `threshold_seconds`, `confidence_threshold`, `cooldown_seconds`, `level`, `enabled`, `config_json`.

### Requirement: Get rule detail
`GET /rules/{id}` SHALL return rule detail including all threshold fields.

### Requirement: Update rule
`PUT /rules/{id}` SHALL support `enabled`, `threshold_seconds`, `confidence_threshold`, `cooldown_seconds`, `config_json` as independent fields. After update, SHALL call AI `/config/reload`.

#### Scenario: Update confidence_threshold
- **WHEN** `PUT /rules/{id}` includes `confidence_threshold: 0.85`
- **THEN** the value SHALL be saved to `behavior_rule.confidence_threshold` column

#### Scenario: Update cooldown_seconds
- **WHEN** `PUT /rules/{id}` includes `cooldown_seconds: 60`
- **THEN** the value SHALL be saved to `behavior_rule.cooldown_seconds` column

### Requirement: Soft delete rule
`DELETE /rules/{id}` SHALL soft delete and notify AI.

### Requirement: Rule types
Supported rule types: `phone_usage`, `flame_detected`, `danger_zone_intrusion`, `danger_zone_stay`, `danger_zone_approach`, `head_down`, `leave_seat`, `fall_detected`, `stream_offline`.
