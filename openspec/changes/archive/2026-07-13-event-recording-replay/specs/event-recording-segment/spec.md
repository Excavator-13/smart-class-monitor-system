## ADDED Requirements

### Requirement: FFmpeg real-time segment recording on publish

When a client begins pushing an RTMP stream to nginx-rtmp, the server SHALL start an FFmpeg process that pulls the same stream and outputs 30-second FLV segments using `-c copy -f segment -segment_time 30`. The FFmpeg process SHALL be started via nginx-rtmp `exec_publish` directive.

#### Scenario: Stream publish starts segment recording

- **GIVEN** nginx-rtmp is configured with `exec_publish` pointing to `start_segment.sh`
- **WHEN** a client begins pushing RTMP stream `classroom_01` to `rtmp://server:9090/live/`
- **THEN** an FFmpeg process SHALL be started that reads `rtmp://localhost:9090/live/classroom_01`
- **AND** the FFmpeg process SHALL output FLV segments to `/usr/local/rtmp_video/segments/{YYYYMMDD}/`
- **AND** the FFmpeg process PID SHALL be written to `/tmp/ffmpeg_seg_classroom_01.pid`

#### Scenario: Segment files are produced every 30 seconds

- **GIVEN** an RTMP stream `classroom_01` is being published
- **AND** FFmpeg segment recording is active
- **WHEN** 30 seconds of stream data have been processed
- **THEN** a complete FLV segment file SHALL be closed and written to disk
- **AND** the next segment SHALL begin recording

#### Scenario: Segment file naming convention

- **GIVEN** FFmpeg produces a segment starting at 2026-07-13 08:30:00 for stream `classroom_01`
- **WHEN** the segment file is written
- **THEN** the filename SHALL be `classroom_01-2026-07-13-08_30_00.flv`
- **AND** the file SHALL be located at `/usr/local/rtmp_video/segments/20260713/classroom_01-2026-07-13-08_30_00.flv`

#### Scenario: Segment directory created by date

- **GIVEN** no directory `/usr/local/rtmp_video/segments/20260713/` exists
- **WHEN** FFmpeg starts writing a segment for that date
- **THEN** the directory SHALL be created automatically

### Requirement: FFmpeg segment process cleanup on publish done

When an RTMP stream disconnects, the server SHALL kill the associated FFmpeg segment recording process via nginx-rtmp `exec_publish_done` directive.

#### Scenario: Stream disconnect kills FFmpeg process

- **GIVEN** an FFmpeg segment process is running for stream `classroom_01` with PID stored in `/tmp/ffmpeg_seg_classroom_01.pid`
- **WHEN** the RTMP stream `classroom_01` disconnects
- **THEN** the FFmpeg process SHALL be killed (SIGTERM)
- **AND** the PID file `/tmp/ffmpeg_seg_classroom_01.pid` SHALL be removed

#### Scenario: PID file missing on disconnect

- **GIVEN** the RTMP stream `classroom_01` disconnects
- **AND** the PID file `/tmp/ffmpeg_seg_classroom_01.pid` does not exist
- **THEN** no error SHALL be raised; the cleanup script SHALL exit cleanly

### Requirement: Segment recording uses stream copy mode

FFmpeg SHALL use `-c copy` (stream copy) mode for segment recording, meaning no re-encoding occurs. This minimizes CPU overhead.

#### Scenario: No re-encoding during segment recording

- **GIVEN** the source RTMP stream uses H.264 video and AAC audio
- **WHEN** FFmpeg records segments
- **THEN** the output FLV segments SHALL contain the same H.264 and AAC codecs without re-encoding
- **AND** CPU usage per FFmpeg process SHALL be minimal (no decode/encode cycle)
