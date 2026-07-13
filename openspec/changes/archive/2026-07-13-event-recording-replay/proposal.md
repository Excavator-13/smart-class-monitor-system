# 异常事件录像回放

## Why

当前系统检测到异常事件时，只保存截图（单帧 jpg），无法回放事件发生前后的视频片段。告警列表的"录像"按钮始终 disabled，`alert_event.record_path` 和 `event_time_offset` 虽已在数据库和 API 中预留，但从未被填充。

根本原因：nginx-rtmp 的 `record all` 模式在整段直播结束后才产出一个完整 flv 文件（可能数小时、数 GB），无法为某个具体事件提供可定位、可下载的短片段。现有 `flv2mp4.sh` 仅在流断后触发 inotifywait 做整段转码入库，实时性不足。

## What Changes

### 1. nginx-rtmp 侧：FFmpeg 实时切片录制

在 nginx-rtmp 的 `exec_publish` 钩子中启动 FFmpeg 进程，以 `-c copy -f segment -segment_time 30` 模式拉取同一 rtmp 流，每 30 秒产出一个独立 flv 片段。推流断开时通过 `exec_publish_done` 杀掉 FFmpeg 进程。

片段命名采用 strftime 格式，文件名自带精确的开始时间，便于 AI 端根据事件时间直接算出对应片段路径，无需查库。

### 2. 服务器侧：切片自动转码入库

复用现有 `flv2mp4.sh` 的 inotifywait 机制，扩展监听范围至切片目录。每个 flv 片段 close_write 时自动转 mp4、解析文件名入库 `recording_file` 表。

### 3. AI 侧：事件确认时填充 record_path + event_time_offset

在 `AnalysisService.analyze_frame()` 中，当事件确认（`should_confirm`）时，根据 `stream_id` + `occurred_at` 算出对应 30s 切片的相对路径和片内时间偏移，通过 `AlertClient.push_alert(event, record_path=..., event_time_offset=...)` 传入。SpringBoot 侧已有完整的 `record_path` + `event_time_offset` 入库逻辑，无需改动。

### 4. 前端侧：录像按钮改为内嵌播放器回放

告警列表"录像"按钮从 `<a>` 直接下载改为弹出 `<el-dialog>` 内嵌 `<video>` 播放器，加载后自动 seek 到 `eventTimeOffset` 位置。

### 5. nginx 静态服务：新增 /records/ 路径

在 nginx 9092 server 中新增 `location /records/`，alias 到切片存储目录，提供 mp4 文件的静态下载和流式播放服务。

## Capabilities

### New Capabilities

- **event-recording-segment**: nginx-rtmp 推流时 FFmpeg 实时切片，每 30 秒产出一个 flv/mp4 片段
- **event-recording-ingest**: 切片文件自动转码入库 recording_file 表
- **event-recording-resolve**: AI 端根据事件时间算出录像片段路径和片内偏移
- **event-recording-replay**: 前端告警列表点击"录像"弹出播放器，自动定位到事件发生时刻

### Modified Capabilities

- **alert-ingest**: `push_alert` 调用时填充 `record_path` 和 `event_time_offset`（数据库和 API 契约已预留，只需 AI 端传值）
- **recording-query**: `recording_file` 表新增 `source_type = 'segment'` 的切片记录，现有查询接口自动涵盖

## Impact

### nginx（云服务器配置）

- `nginx.conf`：rtmp application 新增 `exec_publish` / `exec_publish_done` 指令；http 9092 server 新增 `location /records/`
- 新增 `start_segment.sh`：FFmpeg 实时切片启动脚本
- 新增 `stop_segment.sh`：FFmpeg 进程清理脚本
- 修改 `flv2mp4.sh`：扩展 inotifywait 监听范围，适配切片文件名格式
- 修改 `clean_records.sh`：增加切片目录清理逻辑
- 新增 `服务器配置指导.md`：部署步骤文档

### backend_ai（Python / Flask）

- `services/analysis_service.py`：新增 `_resolve_record_segment()` 方法，在 `push_alert` 时传入 `record_path` + `event_time_offset`
- `services/alert_client.py`：`push_alert()` 签名增加 `event_time_offset` 参数（当前只传了 `record_path`，漏传了 `event_time_offset`）
- `config/app.yaml`：新增 `recording` 配置节（`segment_seconds`、`segment_dir`）

### frontend（Vue3 / Element Plus）

- `App.vue`：告警列表"录像"按钮改为弹出 `<el-dialog>` + `<video>` 播放器，加载后 seek 到 `eventTimeOffset`
- `services/smartClassApi.js`：`normalizeAlert()` 增加 `event_time_offset` 字段映射

### 不改

- **数据库 schema**：`alert_event` 表已有 `record_path`、`event_time_offset` 列；`recording_file` 表结构不变
- **SpringBoot**：`AlertIngestRequest`、`AlertEventService`、`AlertService` 已完整支持 `recordPath` + `eventTimeOffset`，无需改动
- **AI 截图逻辑**：`_save_snapshot()` 和 `SnapshotPusher` 不变
- **整段录像**：nginx-rtmp `record all` 保留，作为完整备份，不影响切片机制

## 不做

- 不改数据库 schema（字段已预留）
- 不改 SpringBoot 侧告警入库和查询逻辑（已完整）
- 不引入 HLS/DASH 流媒体协议（直接用 mp4 静态文件 + HTTP Range 播放）
- 不实现录像片段的自动裁剪（如事件前后 10 秒精准剪辑），仅定位到 30 秒片段内
- 不实现录像片段的云端对象存储迁移
- 不修改 AI 端的帧拉取逻辑（`StreamManager` 不变）
- 不引入 FFmpeg Python 绑定（切片在 nginx 侧 shell 脚本完成，AI 端只做路径计算）
