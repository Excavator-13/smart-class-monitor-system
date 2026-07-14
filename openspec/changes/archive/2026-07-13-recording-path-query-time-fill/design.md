# 录像路径改为查询时动态填充 — 技术设计

## Context

### 已有基础设施

**告警入库管道**：AI 端 `AlertClient.push_alert()` → SpringBoot `AiAlertController` → `AlertEventService.ingestAlert()` → `AlertEventMapper.insert()`。`AlertIngestRequest` 已支持 `recordPath` 和 `eventTimeOffset` 字段，入库时写入 `alert_event` 表对应列。

**告警查询管道**：`AlertController` → `AlertService.listAlerts()` / `getAlertDetail()` → `AlertEventMapper.findAlerts()` / `findAlertDetail()` → `AlertService.mapToAlertVO()` → `AlertVO`。当前 `mapToAlertVO()` 直接将 `record_path` 列映射为 `recordUrl`，不做任何动态计算。

**录像文件入库**：ffmpeg 每 30 秒切片 → flv close_write → `flv2mp4.sh` 转 mp4 → 解析文件名 → `INSERT recording_file`。从事件发生到录像入库有约 30 秒延迟。

**RecordingFileMapper.findContainingRecording**：已实现，SQL `WHERE stream_id = ? AND started_at <= ? AND (ended_at IS NULL OR ended_at >= ?) ORDER BY started_at DESC LIMIT 1`，根据 stream_id + 时间戳查找包含该时刻的录像记录。

**AlertEventService.ingestAlert 中的录像查找**（需移除）：当前在 `ingestAlert()` 中注入了 `RecordingFileMapper`，在告警入库时调用 `findContainingRecording` 查库填充 `record_path` 和 `event_time_offset`。但由于录像入库延迟，ingest 时查库一定返回 NULL。

**AlertVO**：当前有 `recordUrl` 字段（映射自 `record_path`），但没有 `eventTimeOffset` 字段。前端回放需要此值来定位视频播放起始位置。

**前端**：`normalizeAlert()` 已映射 `event_time_offset`（`item.event_time_offset ?? item.eventTimeOffset ?? null`）。`openReplayDialog()` 已读取 `row.event_time_offset`。`evidenceSummary()` 只检查 `snapshot_url`，不考虑 `record_url`。录像按钮 `disabled` 取决于 `!row.record_url`。

## Goals / Non-Goals

**Goals:**

1. 移除 `AlertEventService.ingestAlert()` 中的录像查找逻辑，让 ingest 回归纯粹的告警入库职责
2. 在 `AlertService.mapToAlertVO()` 中根据 `stream_id` + `occurred_at` 动态查询录像并填充 `recordUrl` + `eventTimeOffset`
3. `AlertVO` 新增 `eventTimeOffset` 字段返回给前端
4. 前端 `evidenceSummary()` 增强，同时考虑 `record_url` 状态

**Non-Goals:**

- 不改数据库 schema（`alert_event` 表的 `record_path`、`event_time_offset` 列保留）
- 不改 AI 端代码（上一轮已移除 AI 端的录像查找逻辑）
- 不改前端录像播放器逻辑（`openReplayDialog`、`onReplayReady` 已完整支持）
- 不引入缓存机制（每次查询动态查库）
- 不实现"录像生成中"的主动推送通知

## Decisions

| 决策                     | 选择                                                | 理由                                                                                                           |
| ------------------------ | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 填充时机                 | 查询时动态计算，而非 ingest 时写入                  | 录像入库延迟 ~30s，ingest 时查库一定为 NULL；查询时查库可保证数据已入库                                        |
| 查询性能                 | 每次查库，不引入缓存                                | 告警列表查询频率不高（用户手动刷新），`findContainingRecording` 走 `stream_id` + `started_at` 索引，性能可接受 |
| record_path 列保留       | 保留但不在 ingest 时写入                            | 未来可能有其他渠道写入（如人工关联录像），保留列不破坏现有 schema                                              |
| eventTimeOffset 字段类型 | `Double`（与 `alert_event.event_time_offset` 一致） | 保持类型一致，前端 `?? 0` 兜底                                                                                 |
| 录像路径替换             | `/segments` → `/records`（与 nginx alias 对应）     | 与上一轮 ingest 中的替换逻辑一致，nginx `/records/` alias 到切片存储目录                                       |
| 前端 evidenceSummary     | 增强：区分"仅截图"、"截图+录像"、"证据生成中"       | 用户可直观看到当前告警有哪些证据可用                                                                           |

## Architecture

### 数据流对比

**改动前（ingest 时填充，有 bug）：**

```
AI push_alert()
    │
    ▼
AlertEventService.ingestAlert()
    │
    ├── INSERT alert_event (record_path=NULL, event_time_offset=NULL)
    │     ↑ findContainingRecording 查库返回 NULL
    │     ↑ 因为录像还没入库（延迟 ~30s）
    │
    └── 前端查询 → recordUrl=NULL → 录像按钮永远灰色
```

**改动后（查询时动态填充）：**

```
AI push_alert()
    │
    ▼
AlertEventService.ingestAlert()
    │
    └── INSERT alert_event (record_path=NULL, event_time_offset=NULL)
          ↑ 不再查录像，纯入库

          ... ~30s 后录像入库 ...

前端查询告警列表
    │
    ▼
AlertService.mapToAlertVO()
    │
    ├── record_path 列为空？
    │     └── 是 → findContainingRecording(stream_id, occurred_at)
    │               ├── 查到 → 动态填充 recordUrl + eventTimeOffset
    │               └── 未查到 → recordUrl=null, eventTimeOffset=null
    │
    └── record_path 列有值？
          └── 直接映射（兼容未来其他渠道写入）
```

### AlertService.mapToAlertVO 改动详细设计

```
mapToAlertVO(row)
    │
    ├── 现有字段映射（不变）
    │
    ├── snapshotUrl = row.snapshot_path（不变）
    │
    ├── recordUrl 处理：
    │     │
    │     ├── record_path 列有值 → 直接映射（兼容）
    │     │
    │     └── record_path 列为空 AND stream_id 非空 AND occurred_at 非空
    │           │
    │           └── findContainingRecording(stream_id, occurred_at)
    │                 │
    │                 ├── 查到 RecordingFile rec
    │                 │     ├── recordUrl = rec.filePath.replace("/segments", "/records")
    │                 │     │              + "/" + rec.fileName
    │                 │     └── eventTimeOffset = max(0, Duration.between(rec.startedAt, occurredAt).seconds)
    │                 │
    │                 └── 未查到 → recordUrl = null, eventTimeOffset = null
    │
    └── eventTimeOffset 处理：
          ├── 从动态查询结果获取（如上）
          └── 兜底：从 row.event_time_offset 获取（兼容已有数据）
```

关键实现细节：

- `row` 是 `Map<String, Object>`，`occurred_at` 的 Java 类型是 `LocalDateTime`
- `findContainingRecording` 返回 `RecordingFile` 实体，包含 `filePath`、`fileName`、`startedAt`
- `filePath` 以 `/segments` 开头时替换为 `/records`，对应 nginx 9092 的 `location /records/` alias
- `Duration.between(startedAt, occurredAt).getSeconds()` 可能为负（时钟偏移），用 `Math.max(0, ...)` 兜底
- 查询异常时 log warning，不抛出，`recordUrl` 和 `eventTimeOffset` 保持为 null

### AlertEventService.ingestAlert 移除内容

移除以下代码：

1. `RecordingFileMapper recordingMapper` 字段和构造函数参数
2. `ingestAlert()` 中 `if (event.getOccurredAt() != null && event.getStreamId() != null)` 整个 try-catch 块（含 `findContainingRecording` 调用、`/segments` → `/records` 替换、`Duration.between` 计算）
3. 相关 import：`RecordingFile`、`RecordingFileMapper`、`Duration`

### AlertVO 新增字段

```java
@Schema(description = "事件在录像中的时间偏移（秒）", example = "17.0")
private Double eventTimeOffset;

// getter/setter
public Double getEventTimeOffset() { return eventTimeOffset; }
public void setEventTimeOffset(Double v) { this.eventTimeOffset = v; }
```

### 前端 evidenceSummary 增强

```
evidenceSummary(row):
    hasSnapshot = !!row.snapshot_url
    hasRecord   = !!row.record_url

    hasSnapshot AND hasRecord   → "截图 + 录像"
    hasSnapshot AND !hasRecord  → "已保存截图"
    !hasSnapshot AND hasRecord  → "仅录像"
    !hasSnapshot AND !hasRecord → "证据生成中"
```

## Risks / Trade-offs

| 风险                       | 影响                                           | 缓解                                                                                     |
| -------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **查询时额外 DB 查询**     | 每条告警多一次 `findContainingRecording` 查询  | 告警列表通常 10~20 条/页，查询频率低；SQL 走索引，单次 < 1ms                             |
| **录像入库延迟窗口**       | 事件发生后 ~30s 内查询，录像按钮仍灰色         | 符合"证据生成中"的直觉，用户刷新即可；`evidenceSummary` 显示"证据生成中"提示             |
| **大量告警批量查询**       | 管理员查看全部告警时，N 条记录 N 次查库        | 分页限制每页数量（默认 20）；后续可加批量查询优化或缓存                                  |
| **RecordingFile 时钟偏移** | `started_at` 与 `occurred_at` 来自不同机器时钟 | `Duration.between` 结果可能为负，`Math.max(0, ...)` 兜底；偏移通常 < 1s，seek 精度可接受 |
| **filePath 为 null**       | 早期录像记录可能 `file_path` 为空              | `filePath` 为 null 时跳过录像填充，`recordUrl` 保持 null                                 |
