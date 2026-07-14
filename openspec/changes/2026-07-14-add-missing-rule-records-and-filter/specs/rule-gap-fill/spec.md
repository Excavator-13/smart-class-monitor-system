## ADDED Requirements

### Requirement: DataInitializer seeds 6 missing rule records

`DataInitializer.seedRules()` SHALL insert 6 additional rule records into the `behavior_rule` table, covering event types that currently have no rule record: `stranger_detected`, `leave_seat`, `stream_offline`, `spoof_detected`, `deepfake_detected`, `abnormal_sound`.

#### Scenario: Startup seeds all 12 rules

- **GIVEN** the `behavior_rule` table is empty
- **WHEN** `DataInitializer.run()` executes
- **THEN** the table SHALL contain 12 rule records: the original 6 (`phone_usage`, `flame_detected`, `fall_detected`, `head_down`, `crowd_gathering`, `danger_zone`) plus the 6 new ones

#### Scenario: stranger_detected rule is enabled by default

- **GIVEN** the `behavior_rule` table has no `stranger_detected` record
- **WHEN** `seedRules()` runs
- **THEN** a `stranger_detected` rule SHALL be inserted with `enabled = true`, `threshold_seconds = 0`, `confidence_threshold = 0.45`, `cooldown_seconds = 10`

#### Scenario: leave_seat rule is disabled by default

- **GIVEN** the `behavior_rule` table has no `leave_seat` record
- **WHEN** `seedRules()` runs
- **THEN** a `leave_seat` rule SHALL be inserted with `enabled = false`, `threshold_seconds = 10`, `confidence_threshold = 0.60`, `cooldown_seconds = 30`

#### Scenario: stream_offline rule is enabled by default

- **GIVEN** the `behavior_rule` table has no `stream_offline` record
- **WHEN** `seedRules()` runs
- **THEN** a `stream_offline` rule SHALL be inserted with `enabled = true`, `threshold_seconds = 10`, `confidence_threshold = 1.0`, `cooldown_seconds = 30`

#### Scenario: spoof_detected rule is enabled by default

- **GIVEN** the `behavior_rule` table has no `spoof_detected` record
- **WHEN** `seedRules()` runs
- **THEN** a `spoof_detected` rule SHALL be inserted with `enabled = true`, `threshold_seconds = 0`, `confidence_threshold = 0.70`, `cooldown_seconds = 30`

#### Scenario: deepfake_detected rule is enabled by default

- **GIVEN** the `behavior_rule` table has no `deepfake_detected` record
- **WHEN** `seedRules()` runs
- **THEN** a `deepfake_detected` rule SHALL be inserted with `enabled = true`, `threshold_seconds = 3`, `confidence_threshold = 0.70`, `cooldown_seconds = 60`

#### Scenario: abnormal_sound rule is enabled by default

- **GIVEN** the `behavior_rule` table has no `abnormal_sound` record
- **WHEN** `seedRules()` runs
- **THEN** an `abnormal_sound` rule SHALL be inserted with `enabled = true`, `threshold_seconds = 0`, `confidence_threshold = 0.50`, `cooldown_seconds = 15`

#### Scenario: Seeding is idempotent

- **GIVEN** the `behavior_rule` table already has a `stranger_detected` record
- **WHEN** `seedRules()` runs
- **THEN** no duplicate `stranger_detected` record SHALL be inserted (existing `findAll(ruleType)` check prevents it)

### Requirement: AnalysisService filters governed event types by rule switch

`AnalysisService` SHALL define a `RULE_GOVERNED_TYPES` class constant containing the set of event types whose alert output is controlled by the rule switch: `stranger_detected`, `leave_seat`, `stream_offline`, `spoof_detected`, `deepfake_detected`, `abnormal_sound`.

#### Scenario: Governed event type with rule enabled passes through

- **GIVEN** `config_client.get_rule("stranger_detected")` returns a non-empty dict (rule is enabled)
- **AND** `analyze_frame()` produces a detected item with `event_type = "stranger_detected"`
- **WHEN** the detected items are iterated
- **THEN** the `stranger_detected` item SHALL proceed to `event_service.observe()`

#### Scenario: Governed event type with rule disabled is skipped

- **GIVEN** `config_client.get_rule("stranger_detected")` returns an empty dict (rule is disabled or missing)
- **AND** `analyze_frame()` produces a detected item with `event_type = "stranger_detected"`
- **WHEN** the detected items are iterated
- **THEN** the `stranger_detected` item SHALL be skipped and NOT enter `event_service.observe()`

#### Scenario: Non-governed event type is never filtered

- **GIVEN** `analyze_frame()` produces a detected item with `event_type = "phone_usage"` (not in `RULE_GOVERNED_TYPES`)
- **WHEN** the detected items are iterated
- **THEN** the `phone_usage` item SHALL proceed to `event_service.observe()` regardless of rule state

### Requirement: observe_stream_offline respects rule switch

`observe_stream_offline()` SHALL check the `stream_offline` rule switch before proceeding with event observation.

#### Scenario: stream_offline rule enabled

- **GIVEN** `config_client.get_rule("stream_offline")` returns a non-empty dict
- **WHEN** `observe_stream_offline(stream_id)` is called
- **THEN** the method SHALL proceed with `event_service.observe()` and potentially push an alert

#### Scenario: stream_offline rule disabled

- **GIVEN** `config_client.get_rule("stream_offline")` returns an empty dict
- **WHEN** `observe_stream_offline(stream_id)` is called
- **THEN** the method SHALL return a dict with `event_type = "stream_offline"`, `event_status = "skipped"`, and SHALL NOT call `event_service.observe()` or `alert_client.push_alert()`
