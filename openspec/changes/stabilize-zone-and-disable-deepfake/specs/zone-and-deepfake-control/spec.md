## ADDED Requirements

### Requirement: Deepfake detection is disabled by default

The AI service SHALL keep Deepfake detection disabled unless an explicit runtime configuration enables it.

#### Scenario: Default startup

- **GIVEN** `deepfake_enabled` is absent or false
- **WHEN** the AI service starts and analyzes faces
- **THEN** it SHALL NOT load or invoke the Deepfake detector
- **AND** it SHALL NOT emit or draw `deepfake_detected`

### Requirement: Deepfake rule is visibly unavailable

The frontend SHALL show the `deepfake_detected` rule as off and disabled while the capability is unavailable.

#### Scenario: Existing database rule is enabled

- **GIVEN** the backend returns `deepfake_detected.enabled=true`
- **WHEN** the rule list is rendered while the capability is unavailable
- **THEN** its switch SHALL still appear off and disabled

### Requirement: Danger-zone subevents use the danger-zone rule

The AI service SHALL govern `danger_zone_intrusion`, `danger_zone_stay`, and `danger_zone_approach` with the `danger_zone` rule.

#### Scenario: Danger-zone rule is enabled

- **GIVEN** an enabled `danger_zone` rule and a configured danger polygon
- **WHEN** a person enters the polygon
- **THEN** danger-zone detections SHALL be produced and remain visible on annotated video

#### Scenario: Danger-zone rule is disabled or missing

- **GIVEN** the `danger_zone` rule is disabled or missing
- **WHEN** a person enters a configured danger polygon
- **THEN** no danger-zone event SHALL be observed or alerted
- **AND** the configured polygon MAY still be drawn

### Requirement: Rule toggles only refresh rules

Changing a rule SHALL use the configured AI client to refresh rule data only and SHALL NOT issue a second hard-coded full configuration reload.

#### Scenario: Toggle a non-zone rule

- **WHEN** a rule switch is changed
- **THEN** the AI rules cache SHALL be refreshed
- **AND** the zones cache SHALL not be reloaded by that operation
