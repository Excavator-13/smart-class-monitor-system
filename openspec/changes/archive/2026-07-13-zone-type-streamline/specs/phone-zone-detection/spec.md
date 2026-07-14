## ADDED Requirements

### Requirement: Phone detection scoped to phone_forbidden zones

`BehaviorService.detect_from_objects()` SHALL accept a `phone_forbidden_zones` parameter. A `phone_usage` event SHALL only be produced when the phone bounding-box center point falls inside a `phone_forbidden` zone polygon.

#### Scenario: Phone inside forbidden zone

- **GIVEN** a `phone_forbidden` zone exists with a polygon
- **AND** a person is holding a phone whose bbox center is inside that polygon
- **WHEN** `BehaviorService.detect_from_objects()` is called with `phone_forbidden_zones` containing that zone
- **THEN** a `phone_usage` event SHALL be produced
- **AND** the event SHALL contain a `zone` field with `zone_id`, `zone_name`, and `zone_type`

#### Scenario: Phone outside forbidden zone

- **GIVEN** a `phone_forbidden` zone exists with a polygon
- **AND** a person is holding a phone whose bbox center is outside that polygon
- **WHEN** `BehaviorService.detect_from_objects()` is called with `phone_forbidden_zones` containing that zone
- **THEN** no `phone_usage` event SHALL be produced for that phone

#### Scenario: No forbidden zones configured

- **GIVEN** no `phone_forbidden` zones exist for the stream
- **WHEN** `BehaviorService.detect_from_objects()` is called with `phone_forbidden_zones=None` or an empty list
- **THEN** no `phone_usage` events SHALL be produced

#### Scenario: Phone in one of multiple forbidden zones

- **GIVEN** two `phone_forbidden` zones exist
- **AND** a phone bbox center falls inside zone A but not zone B
- **WHEN** `BehaviorService.detect_from_objects()` is called
- **THEN** a `phone_usage` event SHALL be produced with `zone.zone_id` matching zone A

### Requirement: phone_usage event carries zone info

When a `phone_usage` event is produced by the phone-zone check, the event dict SHALL include a `zone` key containing `zone_id`, `zone_name`, and `zone_type` of the matched forbidden zone.

#### Scenario: Event structure

- **WHEN** a `phone_usage` event is produced for a phone inside a forbidden zone
- **THEN** the event dict SHALL contain:
  - `event_type`: `"phone_usage"`
  - `zone.zone_id`: the matched zone's ID
  - `zone.zone_name`: the matched zone's name
  - `zone.zone_type`: `"phone_forbidden"`
  - `track_key`: `"{person_track_id}:{zone_id}:phone"` (includes zone_id for per-zone deduplication)

### Requirement: AnalysisService routes zones by type

`AnalysisService.analyze_frame()` SHALL split zones by `zone_type` before passing them to services:

- `zone_type == "danger"` zones → `ZoneService.detect()`
- `zone_type == "phone_forbidden"` zones → `BehaviorService.detect_from_objects()` via `phone_forbidden_zones` parameter

#### Scenario: Zones are routed correctly

- **GIVEN** a stream has one `danger` zone and one `phone_forbidden` zone
- **WHEN** `analyze_frame()` runs
- **THEN** `ZoneService.detect()` SHALL receive only the `danger` zone
- **AND** `BehaviorService.detect_from_objects()` SHALL receive the `phone_forbidden` zone in `phone_forbidden_zones`
