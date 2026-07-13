## MODIFIED Requirements

### Requirement: AI event feed deduplicates cross-source events

When the same physical event appears in both `alerts` (from SpringBoot `/alerts`) and `analysisEvents` (from AI `/analysis/events`), the `activeRiskEvents` computed property SHALL keep only one version, preferring the one with a non-zero `risk_score`.

#### Scenario: Same event from both sources, one has score

- **GIVEN** an event with `event_type: "stranger_detected"` exists in `analysisEvents` with `confidence: 0.9`
- **AND** the same event exists in `alerts` with `alert_type: "stranger_detected"` and a different `event_id`
- **WHEN** `activeRiskEvents` is computed
- **THEN** only one version of this event SHALL appear
- **AND** the version with `risk_score > 0` SHALL be kept

#### Scenario: Both sources have score, keep higher confidence

- **GIVEN** an event exists in both `alerts` and `analysisEvents` with the same `event_type` and `occurred_at`
- **AND** both versions would have `risk_score > 0`
- **WHEN** `activeRiskEvents` is computed
- **THEN** only one version SHALL appear
- **AND** the version with higher `confidence` SHALL be kept

#### Scenario: No duplicate events

- **GIVEN** events in `alerts` and `analysisEvents` are all distinct
- **WHEN** `activeRiskEvents` is computed
- **THEN** all events SHALL appear (no false deduplication)

### Requirement: AI event feed only shows events with risk score

The `aiEventFeed` computed property SHALL only include events that have `risk_score > 0`. Events with `risk_score === 0` SHALL be excluded from the event feed display.

#### Scenario: Event with zero score excluded from feed

- **GIVEN** `activeRiskEvents` contains an event with `risk_score: 0`
- **WHEN** `aiEventFeed` is computed
- **THEN** that event SHALL NOT appear in the feed

#### Scenario: Event with positive score shown in feed

- **GIVEN** `activeRiskEvents` contains an event with `risk_score: 72`
- **WHEN** `aiEventFeed` is computed
- **THEN** that event SHALL appear in the feed

### Requirement: Cross-source event matching uses event type and timestamp

To identify duplicate events across `alerts` and `analysisEvents`, the system SHALL match events by `event_type`/`alert_type` + `stream_id` + `occurred_at` (within a 5-second tolerance), rather than relying solely on `event_id` which differs between AI and SpringBoot.

#### Scenario: Events matched by type and time

- **GIVEN** an `analysisEvent` with `{ event_type: "fire", stream_id: "classroom_01", occurred_at: "2026-07-11 10:30:00" }`
- **AND** an `alert` with `{ alert_type: "fire", stream_id: "classroom_01", occurred_at: "2026-07-11 10:30:02" }`
- **WHEN** deduplication runs
- **THEN** these two events SHALL be considered the same physical event (within 5-second tolerance)
- **AND** only one version SHALL be kept

#### Scenario: Events with different types not matched

- **GIVEN** an `analysisEvent` with `event_type: "fire"`
- **AND** an `alert` with `alert_type: "stranger_detected"`
- **WHEN** deduplication runs
- **THEN** these SHALL NOT be considered duplicates
