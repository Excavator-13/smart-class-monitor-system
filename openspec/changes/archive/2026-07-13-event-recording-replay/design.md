# 异常事件录像回放 — 技术设计

## Context

### 已有基础设施

**nginx-rtmp 录像**：`record all` + `record_unique on`，整段录制到 `/usr/local/rtmp_video/`，文件名格式 `classroom_01-<unique>-2026-07-09-11_51_34.flv`。流断才产出。

**flv2mp4.sh**：`inotifywait -m -e close_write` 监听 `/usr/local/rtmp_video/`，flv close_write 时 `ffmpeg -c copy` 转 mp4，解析文件名提取 stream_id + started_at，INSERT `recording_file` 表。

**clean_records.sh**：`find /usr/local/rtmp_video -mtime +7 -name "*.flv" -delete`，只清 flv。

**nginx 9092 静态服务**：`root /usr/local/rtmp_video; autoindex on;` + `location /snapshots/ { alias /data/snapshots/; }`。前端 `NGINX_BASE` 指向此端口。

**AI 告警管道**：`AnalysisService.analyze_frame()` → `EventService.observe()` → `should_confirm` 时 `_save_snapshot()` + `AlertClient.push_alert(event)`。`AlertClient.push_alert()` 签名已有 `record_path` 参数但未传 `event_time_offset`。`AlertClient.map_event_to_alert()` 已支持两个参数。

**数据库**：`alert_event` 表已有 `record_path VARCHAR(255)` 和 `event_time_offset DECIMAL(10,3)` 列。`recording_file` 表已有完整结构。SpringBoot `AlertEventService.ingestAlert()` 已完整写入这两个字段。

**前端**：告警列表"录像"按钮已存在，`disabled` 取决于 `row.record_url`，点击时 `<a href={resourceUrl(record_url)}>` 直接下载。`normalizeAlert()` 已映射 `record_url`，但未映射 `event_time_offset`。

## Goals / Non-Goals

**Goals:**

1. nginx-rtmp 推流时通过 `exec_publish` 启动 FFmpeg 实时切片，每 30 秒产出一个 flv 片段
2. 推流断开时 `exec_publish_done` 清理 FFmpeg 进程
3. 切片 flv 自动转 mp4 并入库 `recording_file` 表（复用 inotifywait 机制）
4. AI 端事件确认时根据事件时间算出对应切片的 `record_path` + `event_time_offset`，填入 `push_alert`
5. nginx 9092 新增 `location /records/` 提供切片静态服务
6. 前端"录像"按钮改为弹出 `<video>` 播放器，自动 seek 到事件偏移位置
7. 切片目录定期清理（7 天过期）

**Non-Goals:**

- 不改数据库 schema（字段已预留）
- 不改 SpringBoot 告警入库/查询逻辑（已完整）
- 不引入 HLS/DASH 流媒体协议
- 不实现事件前后 N 秒精准裁剪（仅定位到 30 秒片段内）
- 不迁移到对象存储（OSS/S3）
- 不改 AI 端帧拉取逻辑（StreamManager 不变）
- 不关停现有整段录像（record all 保留作为完整备份）

## Decisions

| 决策         | 选择                                                | 理由                                                          |
| ------------ | --------------------------------------------------- | ------------------------------------------------------------- |
| 切片方式     | FFmpeg `-f segment -segment_time 30 -c copy`        | copy 模式不重编码，CPU 开销极低；30 秒粒度平衡存储和回放精度  |
| 切片触发     | nginx-rtmp `exec_publish` / `exec_publish_done`     | nginx 原生钩子，推流开始/断开自动触发，无需外部调度           |
| 切片命名     | `{stream_id}-{YYYY-MM-DD-HH_MM_SS}.flv`（strftime） | 文件名自带精确开始时间，AI 端可直接算出对应片段路径，无需查库 |
| 切片存储目录 | `/usr/local/rtmp_video/segments/{YYYYMMDD}/`        | 按日期分目录，与现有 snapshots 组织方式一致，便于清理         |
| 转码入库     | 复用 inotifywait 机制，扩展监听范围                 | 现有 `flv2mp4.sh` 已验证可靠，扩展比新建管道更简单            |
| AI 路径计算  | 纯算术：根据事件时间推算文件名                      | 无 IO、无网络、无查库，零延迟；依赖文件名约定而非数据库       |
| 前端回放     | `<el-dialog>` + `<video>` + seek                    | 浏览器原生 mp4 播放 + HTTP Range，无需额外播放器库            |
| 静态服务路径 | `location /records/` alias 切片目录                 | 与 `/snapshots/` 模式一致，前端 `joinResourceUrl()` 直接复用  |
| 整段录像     | 保留 `record all`                                   | 作为完整备份，不影响切片机制；后续可按需关停                  |

## Architecture

### 整体数据流

```
摄像头/OBS
    │ rtmp push
    ▼
nginx-rtmp (port 9090, application live)
    │
    ├── live on ──────────────────────→ AI cv2.VideoCapture 拉帧分析
    │
    ├── record all ───────────────────→ 整段 flv（现有机制，保留）
    │
    └── exec_publish ────────────────→ FFmpeg -f segment 实时切片
           │                               │
           │                          每30s产出 .flv 片段
           │                               │
           │                          /usr/local/rtmp_video/segments/20260713/
           │                          classroom_01-2026-07-13-08_30_00.flv
           │                          classroom_01-2026-07-13-08_30_30.flv
           │                               │
           │                          inotifywait close_write
           │                               │
           │                          flv2mp4.sh → ffmpeg -c copy → .mp4
           │                               │
           │                          解析文件名 → INSERT recording_file
           │
    └── exec_publish_done ──────────→ kill FFmpeg 进程


AI 检测到异常事件 (occurred_at = 2026-07-13T08:30:17+08:00)
    │
    ├── _save_snapshot() → /snapshots/20260713/evt_xxx.jpg（已有）
    │
    └── _resolve_record_segment()
         │
         │ 片段开始时间 = floor(08:30:17, 30s) = 08:30:00
         │ record_path = /records/20260713/classroom_01-2026-07-13-08_30_00.mp4
         │ event_time_offset = 17.0 秒
         │
         └── push_alert(event, record_path, event_time_offset)
                │
                └── SpringBoot /alerts/ai → INSERT alert_event
                     record_path = /records/20260713/classroom_01-2026-07-13-08_30_00.mp4
                     event_time_offset = 17.000


前端告警列表
    │
    └── 点击"录像"按钮
         │
         └── 弹出 <el-dialog>
              <video src="http://39.106.209.208:9092/records/20260713/classroom_01-2026-07-13-08_30_00.mp4"
                     @loadedmetadata → currentTime = 17.0 />
```

### 切片文件命名约定

```
目录: /usr/local/rtmp_video/segments/{YYYYMMDD}/
文件: {stream_id}-{YYYY-MM-DD-HH_MM_SS}.flv
转码后: {stream_id}-{YYYY-MM-DD-HH_MM_SS}.mp4

示例:
  classroom_01-2026-07-13-08_30_00.flv   → 08:30:00 ~ 08:30:30
  classroom_01-2026-07-13-08_30_30.flv   → 08:30:30 ~ 08:31:00
  classroom_01-2026-07-13-08_31_00.flv   → 08:31:00 ~ 08:31:30
```

命名规则：`{stream_id}-{4位年}-{2位月}-{2位日}-{2位时}_{2位分}_{2位秒}.flv`

- 文件名中的时间 = 该片段的第一帧时间（对齐到 30 秒边界）
- 同一 stream_id 同一天内，文件名按时间排序即按播放顺序
- AI 端根据事件 `occurred_at` 向下取整到 30 秒边界即可算出文件名

### AI 端路径计算算法

```python
def _resolve_record_segment(
    self, stream_id: str, occurred_at: str
) -> tuple[str | None, float | None]:
    """
    输入: stream_id, occurred_at (ISO 8601, 如 "2026-07-13T08:30:17+08:00")
    输出: (record_path, event_time_offset)

    record_path: 相对路径, 如 "/records/20260713/classroom_01-2026-07-13-08_30_00.mp4"
    event_time_offset: 事件在片段内的偏移秒数, 如 17.0
    """
    # 1. 解析 occurred_at 为本地 datetime
    dt = datetime.fromisoformat(occurred_at)

    # 2. 计算当天从 0 点开始的秒数
    seconds_of_day = dt.hour * 3600 + dt.minute * 60 + dt.second

    # 3. 向下取整到 30 秒边界
    segment_seconds = (seconds_of_day // SEGMENT_SECONDS) * SEGMENT_SECONDS

    # 4. 片内偏移
    time_offset = float(seconds_of_day - segment_seconds)

    # 5. 构造片段开始时间
    segment_start = dt.replace(hour=0, minute=0, second=0, microsecond=0) \
                     + timedelta(seconds=segment_seconds)

    # 6. 拼接路径
    day_str = segment_start.strftime("%Y%m%d")
    time_str = segment_start.strftime("%Y-%m-%d-%H_%M_%S")
    filename = f"{stream_id}-{time_str}.mp4"
    record_path = f"/records/{day_str}/{filename}"

    return record_path, time_offset
```

### 前端播放器设计

```
告警列表 "录像" 按钮
    │
    ├── record_url 为空 → disabled（现有逻辑不变）
    │
    └── record_url 有值 → 点击
         │
         ├── 设置 replayUrl = joinResourceUrl(record_url)
         ├── 设置 replayOffset = alert.event_time_offset ?? 0
         ├── replayVisible = true
         │
         └── <el-dialog>
              <video :src="replayUrl" controls @loadedmetadata="onReplayReady" />

              onReplayReady():
                  video.currentTime = replayOffset
                  video.play()
```

关键点：

- 使用浏览器原生 `<video>` 播放 mp4，依赖 HTTP Range 请求实现 seek，无需流媒体服务器
- `loadedmetadata` 事件触发后 seek，确保 duration 已加载
- 对话框关闭时暂停并释放视频

## Risks / Trade-offs

| 风险                       | 影响                                                            | 缓解                                                                                                              |
| -------------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **时间对齐偏差**           | FFmpeg 切片边界受关键帧影响，实际片段开始时间可能与文件名差几秒 | 推流端 GOP 设为 2~4 秒；AI 端 seek 偏移量有 ±2 秒误差可接受                                                       |
| **FFmpeg 僵尸进程**        | nginx 异常重启时 `exec_publish_done` 不触发，FFmpeg 进程残留    | cron 每小时检查 `/tmp/ffmpeg_seg_*.pid`，进程不存在则清 pid 文件                                                  |
| **`-c copy` 片段首帧花屏** | 关键帧不在片段边界时，首帧可能解码异常                          | 浏览器播放器通常自动跳到下一个关键帧，视觉影响小；极端情况可改用 `-c:v libx264 -preset ultrafast`（CPU 开销增大） |
| **磁盘空间增长**           | 每流每分钟 2 个 mp4（30s/个），1Mbps 码率约 10GB/天/流          | `clean_records.sh` 扩展到清理 segments 目录，保留 7 天                                                            |
| **多流并发 FFmpeg**        | 每路流一个 FFmpeg 进程，10 路流 10 个进程                       | `-c copy` 模式 CPU 占用极低（< 1%/进程），主要消耗 IO；可设进程数上限                                             |
| **切片尚未产出**           | 事件发生后对应片段可能还在写入中（最多等 30 秒）                | 前端播放器加 loading + 重试逻辑；`record_path` 先入库，片段稍后可用                                               |
| **跨天片段**               | 23:59:45 的事件，片段从 23:59:30 开始，跨到次日 00:00:00        | FFmpeg 按实际时间命名，跨天片段文件名仍是前一天的日期；AI 端计算不受影响                                          |
