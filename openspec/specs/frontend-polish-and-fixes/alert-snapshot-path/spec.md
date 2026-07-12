## FIXED Requirements

### Requirement: Alert snapshot_url is correctly mapped from backend

`normalizeAlert` SHALL correctly map the `snapshot_url` field from the backend `AlertVO` response. The frontend SHALL NOT modify or drop this field during normalization.

#### Scenario: snapshot_url present in backend response

- **WHEN** backend returns an alert with `snapshot_url: "/snapshots/2026-07-11/evt_001.jpg"`
- **THEN** `normalizeAlert` SHALL produce an object with `snapshot_url: "/snapshots/2026-07-11/evt_001.jpg"`

#### Scenario: snapshot_url is null

- **WHEN** backend returns an alert with `snapshot_url: null`
- **THEN** `normalizeAlert` SHALL produce an object with `snapshot_url: null`

### Requirement: Snapshot link uses Nginx static resource base URL

When a `snapshot_url` is present, the "截图" button SHALL construct a full URL by prepending the Nginx static resource base URL (via `joinResourceUrl`). The link SHALL open in a new browser tab.

#### Scenario: Snapshot link is clickable

- **WHEN** an alert has `snapshot_url: "/snapshots/2026-07-11/evt_001.jpg"`
- **AND** `VITE_NGINX_BASE` is `http://localhost:8080/media`
- **THEN** the "截图" button SHALL link to `http://localhost:8080/media/snapshots/2026-07-11/evt_001.jpg`
- **AND** the button SHALL NOT be disabled

#### Scenario: Snapshot link is disabled when no URL

- **WHEN** an alert has `snapshot_url: null`
- **THEN** the "截图" button SHALL be disabled

### Requirement: Record URL button remains disabled

The "录像" button SHALL remain disabled for all alerts, as video clip recording is not yet implemented. This is a known limitation.

#### Scenario: Record button always disabled

- **WHEN** any alert is displayed
- **THEN** the "录像" button SHALL be disabled regardless of `record_url` value

### Requirement: evidenceSummary reflects snapshot availability

`evidenceSummary` SHALL return accurate text based on `snapshot_url` availability:

- If `snapshot_url` is present: "已保存告警截图"
- If `snapshot_url` is absent: "未生成证据文件"
- The "截图与录像片段已关联" and "已关联录像路径" messages SHALL NOT be used, since video clips are not implemented.

#### Scenario: Only snapshot available

- **WHEN** an alert has `snapshot_url` but no `record_url`
- **THEN** `evidenceSummary` SHALL return "已保存告警截图"

#### Scenario: No evidence available

- **WHEN** an alert has neither `snapshot_url` nor `record_url`
- **THEN** `evidenceSummary` SHALL return "未生成证据文件"
