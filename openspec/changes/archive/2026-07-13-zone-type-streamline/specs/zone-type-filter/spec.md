## MODIFIED Requirements

### Requirement: zone_type enumeration

zone_type SHALL be one of: `danger`, `phone_forbidden`. The values `seat` and `roi` are removed.

#### Scenario: Create zone with valid type

- **WHEN** `POST /zones` with `zone_type=danger` or `zone_type=phone_forbidden`
- **THEN** the response SHALL have `code: 0`

#### Scenario: Create zone with removed type

- **WHEN** `POST /zones` with `zone_type=seat` or `zone_type=roi`
- **THEN** the response SHALL have `code: 400`

#### Scenario: Frontend zone type options

- **WHEN** the zone editing dialog is opened
- **THEN** only "危险区" (`danger`) and "手机禁用区" (`phone_forbidden`) SHALL be available

### Requirement: ZoneService filters by zone_type

`ZoneService.detect()` SHALL only process zones where `zone_type == "danger"`. Zones with `zone_type == "phone_forbidden"` SHALL NOT produce `danger_zone_intrusion`, `danger_zone_stay`, or `danger_zone_approach` events.

#### Scenario: phone_forbidden zone does not trigger intrusion

- **GIVEN** a zone with `zone_type=phone_forbidden` exists
- **AND** a person's foot point is inside that zone's polygon
- **WHEN** `ZoneService.detect()` is called
- **THEN** no `danger_zone_intrusion` event SHALL be produced for that zone

#### Scenario: danger zone triggers intrusion as before

- **GIVEN** a zone with `zone_type=danger` exists
- **AND** a person's foot point is inside that zone's polygon
- **WHEN** `ZoneService.detect()` is called
- **THEN** a `danger_zone_intrusion` event SHALL be produced for that zone

### Requirement: Zone drawing color by type

The annotated video stream SHALL draw zones with distinct colors by `zone_type`.

#### Scenario: danger zone color

- **WHEN** a zone with `zone_type=danger` is drawn on the frame
- **THEN** the polygon outline and label SHALL be red `(0, 0, 255)` in BGR

#### Scenario: phone_forbidden zone color

- **WHEN** a zone with `zone_type=phone_forbidden` is drawn on the frame
- **THEN** the polygon outline and label SHALL be orange `(0, 140, 255)` in BGR
