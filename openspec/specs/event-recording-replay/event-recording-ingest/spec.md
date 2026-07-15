## ADDED Requirements

### Requirement: Segment FLV files auto-converted to MP4

When a segment FLV file is closed (finished writing), the `flv2mp4.sh` inotifywait listener SHALL detect the `close_write` event, convert the FLV to MP4 using `ffmpeg -c copy`, and delete the source FLV.

#### Scenario: Segment FLV converted to MP4

- **GIVEN** a segment FLV file is written to `/usr/local/rtmp_video/segments/20260713/classroom_01-2026-07-13-08_30_00.flv`
- **WHEN** the file is closed (inotifywait detects `close_write`)
- **THEN** `ffmpeg -c copy` SHALL convert it to `classroom_01-2026-07-13-08_30_00.mp4` in the same directory
- **AND** the source FLV file SHALL be deleted

#### Scenario: Conversion failure does not delete source

- **GIVEN** a segment FLV file triggers `close_write`
- **WHEN** the FFmpeg conversion fails (corrupt file, disk full, etc.)
- **THEN** the source FLV file SHALL NOT be deleted
- **AND** the error SHALL be logged

### Requirement: Segment MP4 files auto-ingested into recording_file table

After a segment FLV is successfully converted to MP4, the script SHALL parse the filename to extract `stream_id` and `started_at`, then INSERT a row into the `recording_file` table.

#### Scenario: Segment ingested into recording_file

- **GIVEN** MP4 file `classroom_01-2026-07-13-08_30_00.mp4` is produced
- **WHEN** the ingest logic runs
- **THEN** a row SHALL be inserted into `recording_file` with:
  - `stream_id` = `classroom_01`
  - `event_id` = NULL
  - `file_path` = `/segments/20260713/` (relative path to directory)
  - `file_name` = `classroom_01-2026-07-13-08_30_00.mp4`
  - `file_ext` = `mp4`
  - `file_size` = actual file size in bytes
  - `started_at` = `2026-07-13 08:30:00`
  - `ended_at` = `2026-07-13 08:30:30`
  - `duration_seconds` = `30.000`
  - `source_type` = `segment`

#### Scenario: Filename parsing for segment files

- **GIVEN** a segment filename `classroom_01-2026-07-13-08_30_00.mp4`
- **WHEN** the filename is parsed
- **THEN** `stream_id` SHALL be `classroom_01`
- **AND** `started_at` SHALL be `2026-07-13 08:30:00`

#### Scenario: Unrecognized filename format skipped

- **GIVEN** a file `random_file.mp4` in the segments directory that does not match the naming convention
- **WHEN** the ingest logic attempts to parse it
- **THEN** the file SHALL be skipped (no INSERT)
- **AND** no error SHALL be raised

### Requirement: flv2mp4.sh monitors both root and segments directories

The `flv2mp4.sh` script SHALL use inotifywait to monitor both `/usr/local/rtmp_video/` (existing whole-stream recordings) and `/usr/local/rtmp_video/segments/` (new segment recordings).

#### Scenario: Whole-stream recording still processed

- **GIVEN** a whole-stream FLV file is written to `/usr/local/rtmp_video/classroom_01-xxx.flv`
- **WHEN** the file is closed
- **THEN** it SHALL be converted to MP4 and ingested with `source_type = 'nginx_record'` (existing behavior unchanged)

#### Scenario: Segment recording processed

- **GIVEN** a segment FLV file is written to `/usr/local/rtmp_video/segments/20260713/classroom_01-2026-07-13-08_30_00.flv`
- **WHEN** the file is closed
- **THEN** it SHALL be converted to MP4 and ingested with `source_type = 'segment'`
