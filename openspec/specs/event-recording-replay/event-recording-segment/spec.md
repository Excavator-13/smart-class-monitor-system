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

### Requirement: Segment index uses actual media duration

切片转码完成后，系统必须使用 MP4 的真实媒体时长写入 `recording_file.duration_seconds` 和 `ended_at`，不得把目标切片长度 30 秒无条件当成实际长度。

#### Scenario: Keyframe makes a segment longer than 30 seconds

- **GIVEN** 一个切片从 `16:33:15` 开始，ffprobe 返回实际时长 `31.2` 秒
- **WHEN** 转码脚本写入该切片索引
- **THEN** `duration_seconds` SHALL 保存实际媒体时长
- **AND** 秒精度的 `ended_at` SHALL 向上覆盖到 `16:33:47`
- **AND** 发生于 `16:33:46` 的事件 SHALL 落在该切片范围内

#### Scenario: ffprobe cannot read duration

- **GIVEN** MP4 转换成功但 ffprobe 未返回有效正数时长
- **WHEN** 转码脚本写入切片索引
- **THEN** 系统 SHALL 回退到目标切片时长
- **AND** 系统 SHALL 写入可诊断的错误日志
