## ADDED Requirements

### Requirement: Nginx serves recording segments via /records/ path

The nginx HTTP server on port 9092 SHALL serve recording segment MP4 files from the segments directory via a `location /records/` block.

#### Scenario: Segment MP4 served via /records/ URL

- **GIVEN** a segment MP4 file exists at `/usr/local/rtmp_video/segments/20260713/classroom_01-2026-07-13-08_30_00.mp4`
- **WHEN** a GET request is made to `http://server:9092/records/20260713/classroom_01-2026-07-13-08_30_00.mp4`
- **THEN** the MP4 file SHALL be served with appropriate `Content-Type` header
- **AND** HTTP Range requests SHALL be supported for video seeking

#### Scenario: Non-existent segment returns 404

- **GIVEN** no file exists at the requested path under `/records/`
- **WHEN** a GET request is made
- **THEN** the response SHALL be HTTP 404

#### Scenario: Directory listing disabled for /records/

- **GIVEN** the `location /records/` block is configured
- **WHEN** a GET request is made to `http://server:9092/records/` or `http://server:9092/records/20260713/`
- **THEN** directory listing SHALL be disabled (`autoindex off`)

### Requirement: Segment files cleaned after 7 days

The `clean_records.sh` script SHALL delete segment MP4 files older than 7 days from the segments directory.

#### Scenario: Old segment MP4 files deleted

- **GIVEN** a segment MP4 file at `/usr/local/rtmp_video/segments/20260706/` (7+ days old)
- **WHEN** `clean_records.sh` is executed
- **THEN** the MP4 file SHALL be deleted

#### Scenario: Recent segment files preserved

- **GIVEN** a segment MP4 file at `/usr/local/rtmp_video/segments/20260712/` (within 7 days)
- **WHEN** `clean_records.sh` is executed
- **THEN** the MP4 file SHALL NOT be deleted

#### Scenario: Empty segment directories removed

- **GIVEN** all files in `/usr/local/rtmp_video/segments/20260706/` have been deleted
- **WHEN** `clean_records.sh` is executed
- **THEN** the empty directory SHALL be removed
