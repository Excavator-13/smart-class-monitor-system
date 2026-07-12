# Monitor Multiple Zones Specification

## ADDED Requirements

### Requirement: Persist a confirmed monitor zone

The frontend SHALL create a `phone_forbidden` zone through `POST /zones` only after the user confirms a valid draft rectangle.

#### Scenario: Confirm succeeds

- **WHEN** the user confirms a valid rectangle for the active stream
- **THEN** the frontend sends its four normalized corner coordinates to `POST /zones`
- **AND** the returned zone appears on the video and in the deletion list

#### Scenario: Confirm fails

- **WHEN** `POST /zones` fails
- **THEN** the draft remains available for retry
- **AND** the frontend shows an error instead of claiming persistence succeeded

### Requirement: Display multiple confirmed zones

The frontend SHALL render all enabled `phone_forbidden` zones returned for the active stream and SHALL permit another draft while confirmed zones remain visible.

#### Scenario: Multiple zones exist

- **WHEN** the active stream has three enabled phone-forbidden zones
- **THEN** all three rectangles appear simultaneously
- **AND** all three zones appear as separate entries in the management list

### Requirement: Selectively delete a zone

The frontend SHALL provide a delete control for every persisted phone-forbidden zone and SHALL call `DELETE /zones/{id}` for the selected zone.

#### Scenario: Delete succeeds

- **WHEN** the user selects delete for one of several zones
- **THEN** only that zone is removed from the video and list after the request succeeds
- **AND** the remaining zones stay active

#### Scenario: Delete fails

- **WHEN** `DELETE /zones/{id}` fails
- **THEN** the selected zone remains visible
- **AND** the frontend reports the failure

### Requirement: Match phone events against every zone

Phone-related events SHALL participate in display and scoring only when their API-provided target rectangle intersects at least one confirmed phone-forbidden zone.

#### Scenario: Phone outside all zones

- **WHEN** a phone target does not intersect any confirmed zone
- **THEN** it is not displayed as a phone-zone violation

#### Scenario: Phone intersects one of multiple zones

- **WHEN** a phone target intersects any confirmed zone
- **THEN** it is displayed as a phone-zone violation

