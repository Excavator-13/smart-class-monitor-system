## FIXED Requirements

### Requirement: ReportService.queryTodayAlerts handles null snapshotUrl

`queryTodayAlerts()` SHALL NOT produce the string `"null"` when `snapshotUrl` is null in the database. When `snapshotUrl` is null or blank, the key SHALL NOT be added to the result map.

#### Scenario: null snapshotUrl is not serialized as "null"

- **GIVEN** an alert record has `snapshot_url = NULL` in the database
- **WHEN** `queryTodayAlerts()` processes this record
- **THEN** the result map SHALL NOT contain key `"snapshotUrl"`
- **AND** `String.valueOf(null)` SHALL NOT be used on the snapshotUrl field

#### Scenario: valid snapshotUrl is preserved

- **GIVEN** an alert record has `snapshot_url = "/snapshots/20260714/evt_abc.jpg"`
- **WHEN** `queryTodayAlerts()` processes this record
- **THEN** the result map SHALL contain `"snapshotUrl": "/snapshots/20260714/evt_abc.jpg"`

#### Scenario: generateReport skips null snapshotUrl

- **GIVEN** `queryTodayAlerts()` returns an alert map without `"snapshotUrl"` key
- **WHEN** `generateReport()` processes this alert
- **THEN** `a.getOrDefault("snapshotUrl", "")` SHALL return `""`
- **AND** the `snap.isBlank()` check SHALL be true
- **AND** no VL analysis SHALL be attempted for this alert

## ADDED Requirements

### Requirement: Report card close button

The AI report card displayed on the alerts page SHALL have a close button that hides the card without deleting the report data from the backend.

#### Scenario: Close button hides report card

- **GIVEN** the AI report card is visible (latestReport is not null)
- **WHEN** the user clicks the close button
- **THEN** the report card SHALL be hidden
- **AND** the backend report data SHALL NOT be deleted

#### Scenario: Report can be re-fetched after closing

- **GIVEN** the user has closed the report card
- **WHEN** the page is reloaded
- **THEN** the report SHALL be fetched from `GET /report/latest` and displayed again

### Requirement: Report data stored in independent ref, not localStorage

`latestReport` and `reportHistory` SHALL be stored in independent Vue refs, not inside `alertSettings`. They SHALL NOT be persisted to localStorage. The report data SHALL be fetched from the backend API on page load.

#### Scenario: latestReport is an independent ref

- **WHEN** the frontend initializes
- **THEN** `latestReport` SHALL be a standalone `ref(null)`, not a property of `alertSettings`

#### Scenario: Report data is not in localStorage

- **WHEN** `saveSettings()` serializes `alertSettings` to localStorage
- **THEN** the serialized data SHALL NOT contain `latestReport` or `reportHistory` keys

#### Scenario: Report fetched from backend on page load

- **GIVEN** the backend has a latest report stored
- **WHEN** the frontend page loads
- **THEN** `GET /report/latest` SHALL be called
- **AND** `latestReport.value` SHALL be set to the response data

#### Scenario: Report generated manually updates independent ref

- **WHEN** the user clicks "生成日报" and the report is generated
- **THEN** `latestReport.value` SHALL be set to the generated report
- **AND** `alertSettings` SHALL NOT be modified with report data
