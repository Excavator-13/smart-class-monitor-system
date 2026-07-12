## FIXED Requirements

### Requirement: normalizeZone parses JSON string coordinates

`normalizeZone` SHALL parse the `coordinates` field when it is a JSON string. The backend `ZoneVO.coordinates` is a JSON string (e.g., `"[{\"x\":0.1,\"y\":0.2}]"`), not a parsed array. The frontend SHALL detect string values and parse them before assignment.

#### Scenario: Coordinates returned as JSON string

- **WHEN** backend returns a zone with `coordinates: "[{\"x\":0.1,\"y\":0.2},{\"x\":0.3,\"y\":0.4}]"`
- **THEN** `normalizeZone` SHALL parse the string and produce `coordinates: [{ x: 0.1, y: 0.2 }, { x: 0.3, y: 0.4 }]`

#### Scenario: Coordinates already an array

- **WHEN** backend returns a zone with `coordinates: [{ x: 0.1, y: 0.2 }]` (already parsed, e.g., from mock data)
- **THEN** `normalizeZone` SHALL keep the array as-is without double-parsing

#### Scenario: Coordinates is null or empty

- **WHEN** backend returns a zone with `coordinates: null` or `coordinates: ""`
- **THEN** `normalizeZone` SHALL produce `coordinates: []`

#### Scenario: Coordinates is invalid JSON

- **WHEN** backend returns a zone with `coordinates: "not-json"`
- **THEN** `normalizeZone` SHALL produce `coordinates: []` (graceful fallback)

### Requirement: zoneCoordinateText displays parsed coordinates

After `normalizeZone` correctly parses coordinates, `zoneCoordinateText` SHALL display the coordinate values instead of "暂无坐标" when the zone has valid coordinates.

#### Scenario: Zone with 4 corner coordinates

- **WHEN** a zone row has `coordinates: [{ x: 0.1, y: 0.2 }, { x: 0.3, y: 0.2 }, { x: 0.3, y: 0.4 }, { x: 0.1, y: 0.4 }]`
- **THEN** `zoneCoordinateText` SHALL display `(0.1000, 0.2000) / (0.3000, 0.2000) / (0.3000, 0.4000) / (0.1000, 0.4000)`

#### Scenario: Zone with empty coordinates

- **WHEN** a zone row has `coordinates: []`
- **THEN** `zoneCoordinateText` SHALL display "暂无坐标"
