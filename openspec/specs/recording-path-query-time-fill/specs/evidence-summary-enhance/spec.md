## MODIFIED Requirements

### Requirement: evidenceSummary displays evidence status considering both snapshot and recording

The `evidenceSummary()` function SHALL consider both `snapshot_url` and `record_url` to provide a descriptive summary of available evidence for an alert row.

#### Scenario: Both snapshot and recording available

- **GIVEN** an alert row with `snapshot_url = "/snapshots/20260713/evt_xxx.jpg"` and `record_url = "/records/20260713/classroom_01.mp4"`
- **WHEN** `evidenceSummary(row)` is called
- **THEN** the result SHALL be `"截图 + 录像"`

#### Scenario: Only snapshot available

- **GIVEN** an alert row with `snapshot_url = "/snapshots/20260713/evt_xxx.jpg"` and `record_url = null`
- **WHEN** `evidenceSummary(row)` is called
- **THEN** the result SHALL be `"已保存截图"`

#### Scenario: Only recording available

- **GIVEN** an alert row with `snapshot_url = null` and `record_url = "/records/20260713/classroom_01.mp4"`
- **WHEN** `evidenceSummary(row)` is called
- **THEN** the result SHALL be `"仅录像"`

#### Scenario: Neither snapshot nor recording available

- **GIVEN** an alert row with `snapshot_url = null` and `record_url = null`
- **WHEN** `evidenceSummary(row)` is called
- **THEN** the result SHALL be `"证据生成中"`

#### Scenario: Empty string treated as unavailable

- **GIVEN** an alert row with `snapshot_url = ""` and `record_url = ""`
- **WHEN** `evidenceSummary(row)` is called
- **THEN** the result SHALL be `"证据生成中"` (empty string is falsy)
