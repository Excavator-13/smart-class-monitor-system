## MODIFIED Requirements

### Requirement: DataInitializer seedRules rule_type matches AI lookup keys

`DataInitializer.seedRules()` SHALL initialize `behavior_rule` records with `rule_type` values that match the keys used by AI detection services in `config_client.cache.rules`.

| rule_type         | rule_name    | enabled | level   |
| ----------------- | ------------ | ------- | ------- |
| `phone_usage`     | 手机违规检测 | true    | info    |
| `flame_detected`  | 明火检测     | true    | high    |
| `fall_detected`   | 摔倒检测     | false   | high    |
| `head_down`       | 长时间低头   | true    | info    |
| `crowd_gathering` | 异常人流聚集 | true    | high    |
| `danger_zone`     | 区域入侵检测 | true    | warning |

The `stranger_detected` rule SHALL be removed from seed data (face_service does not read from config_client.cache.rules).

#### Scenario: flame_detected rule is readable by fire_service

- **GIVEN** a fresh database initialized by `seedRules()`
- **WHEN** `config_client.load_rules()` fetches rules from `GET /rules`
- **THEN** `cache.rules` SHALL contain key `"flame_detected"` (not `"fire_detected"`)

#### Scenario: danger_zone rule is readable by zone_service

- **GIVEN** a fresh database initialized by `seedRules()`
- **WHEN** `config_client.load_rules()` fetches rules from `GET /rules`
- **THEN** `cache.rules` SHALL contain key `"danger_zone"` (not `"zone_intrusion"`)

#### Scenario: crowd_gathering rule exists in seed data

- **GIVEN** a fresh database initialized by `seedRules()`
- **WHEN** `config_client.load_rules()` fetches rules from `GET /rules`
- **THEN** `cache.rules` SHALL contain key `"crowd_gathering"`

#### Scenario: stranger_detected is not in seed data

- **GIVEN** a fresh database initialized by `seedRules()`
- **WHEN** all rules are queried from the database
- **THEN** no rule with `rule_type="stranger_detected"` SHALL exist

### Requirement: AI detection services skip when rule is absent

When a detection service looks up its rule from `cache.rules` and the rule is not found (key absent or value is empty dict), the detection SHALL be skipped entirely. The service SHALL return an empty list, NOT proceed with default threshold values.

#### Scenario: fire_service skips when flame_detected rule is absent

- **GIVEN** `cache.rules` does not contain key `"flame_detected"`
- **WHEN** `fire_service.detect()` is called
- **THEN** the method SHALL return `[]` immediately without running model inference

#### Scenario: fire_service runs when flame_detected rule is present

- **GIVEN** `cache.rules` contains key `"flame_detected"` with a non-empty dict
- **WHEN** `fire_service.detect()` is called
- **THEN** the method SHALL proceed with fire detection model inference

#### Scenario: phone_usage skips when phone_usage rule is absent

- **GIVEN** `cache.rules` does not contain key `"phone_usage"`
- **AND** phones and phone_forbidden_zones are present in the frame
- **WHEN** `behavior_service.detect_from_objects()` is called
- **THEN** no `phone_usage` events SHALL be produced

#### Scenario: zone_service skips when danger_zone rule is absent

- **GIVEN** `cache.rules` does not contain key `"danger_zone"`
- **AND** danger zones and persons are present
- **WHEN** `zone_service.detect()` is called
- **THEN** the method SHALL return `[]` immediately

#### Scenario: head_down already skips when rule is absent (unchanged)

- **GIVEN** `cache.rules` does not contain key `"head_down"`
- **WHEN** `behavior_service.detect_from_objects()` is called
- **THEN** no `head_down` events SHALL be produced (existing behavior, no change needed)

#### Scenario: fall_detected already skips when rule is absent (unchanged)

- **GIVEN** `cache.rules` does not contain key `"fall_detected"`
- **WHEN** `behavior_service.detect_from_objects()` is called
- **THEN** no `fall_detected` events SHALL be produced (existing behavior, no change needed)
