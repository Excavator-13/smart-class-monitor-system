# AI Alert Output Specification

## ADDED Requirements

### Requirement: Throttle repeated database alerts

The AI service SHALL push at most one alert for the same stream, event type, and target track during any ten-second cooldown window.

#### Scenario: Repeated detection inside cooldown

- **WHEN** an alert is pushed and the same event is detected again one second later
- **THEN** the second detection is not pushed to SpringBoot

#### Scenario: Detection after cooldown

- **WHEN** the same event remains detectable ten seconds after its previous push
- **THEN** AI pushes a new alert with a new event ID

### Requirement: Show short-lived stream alerts

The annotated video stream SHALL show each newly confirmed alert in the top-left for two seconds.

#### Scenario: Fire alert is confirmed

- **WHEN** a flame detection becomes a confirmed alert
- **THEN** a `Fire detected` entry appears in the top-left
- **AND** it disappears two seconds later unless a new confirmed fire alert is generated

#### Scenario: Phone alert is confirmed

- **WHEN** a phone-use detection becomes a confirmed alert
- **THEN** a `Using phone` entry appears in the top-left for two seconds

### Requirement: Preserve ingestion idempotency

Every alert allowed after a cooldown SHALL use a new event ID, while retries of that alert SHALL retain the same ID.

## CLARIFIED Requirements

### Requirement: Fall alert provenance

The current `fall_detected` event SHALL be understood as a rule-derived candidate based on a YOLO person bounding-box aspect ratio, not output from a dedicated fall model.
