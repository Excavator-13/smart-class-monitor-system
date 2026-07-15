# 录像路径改为查询时动态填充

## 动机

### 问题

在上一轮改动（第 3 步）中，我们将录像路径查找从 AI 端移到了 SpringBoot 端的 `AlertEventService.ingestAlert()`，在告警入库时调用 `RecordingFileMapper.findContainingRecording(streamId, occurredAt)` 查库填充 `record_path` 和 `event_time_offset`。

**但这有一个时序缺陷**：录像文件在事件发生后约 30 秒才入库（ffmpeg 切片 → flv2mp4.sh 转码 → insert_recording），而告警 ingest 是实时的，所以 ingest 时查 `recording_file` 表一定是 NULL。结果就是 `alert_event.record_path` 和 `event_time_offset` 永远不会被填充，前端录像按钮始终灰色不可用。

### 方案

将录像路径的填充从 **ingest 写入时** 改为 **查询时动态计算**：

- `alert_event` 表的 `record_path` / `event_time_offset` 列保留但不再在 ingest 时写入
- 在 `AlertService.mapToAlertVO()` 中，根据 `stream_id` + `occurred_at` 调用 `findContainingRecording` 动态填充 `recordUrl` 和 `eventTimeOffset`
- 告警刚发生时录像按钮灰色（录像尚未入库），约 30 秒后刷新即可点击——符合"证据生成中"的直觉

## 范围

### 1. AlertEventService：移除 ingest 时的录像查找逻辑

移除 `ingestAlert()` 中注入 `RecordingFileMapper`、调用 `findContainingRecording`、替换 `/segments` → `/records`、计算 `eventTimeOffset` 的整段代码。`ingestAlert` 回归纯粹的告警入库职责，不再关心录像。

### 2. AlertService：查询时动态填充录像信息

- 注入 `RecordingFileMapper`
- 在 `mapToAlertVO()` 中，当 `record_path` 为空且 `stream_id` + `occurred_at` 非空时，调用 `findContainingRecording` 查库
- 查到录像时：将 `file_path` 中的 `/segments` 前缀替换为 `/records`（对应 nginx alias），拼接 `file_name` 得到 `recordUrl`；用 `Duration.between(startedAt, occurredAt)` 计算 `eventTimeOffset`
- 查不到时：`recordUrl` 和 `eventTimeOffset` 保持为 null，前端录像按钮灰色

### 3. AlertVO：新增 eventTimeOffset 字段

当前 `AlertVO` 没有 `eventTimeOffset` 字段，前端回放需要此值来定位视频播放起始位置。新增该字段并返回给前端。

### 4. 前端 evidenceSummary 可选增强

`evidenceSummary()` 当前只检查 `snapshot_url`，可增强为同时考虑 `record_url`，给出更精确的证据描述（如"已保存截图 + 录像"、"仅截图"、"证据生成中"等）。`openReplayDialog` 已读取 `row.event_time_offset`，无需改动。

## 不做

- 不改数据库 schema（`alert_event` 表的 `record_path`、`event_time_offset` 列保留，只是不在 ingest 时写入）
- 不改 AI 端代码（上一轮已移除 AI 端的录像查找逻辑）
- 不改前端录像播放器逻辑（`openReplayDialog`、`onReplayReady` 已完整支持 `event_time_offset`）
- 不引入缓存机制（每次查询动态查库，告警列表查询频率不高，`findContainingRecording` 走索引性能可接受）
- 不实现"录像生成中"的主动推送通知（前端轮询刷新即可）

## 影响模块

### backend_system（Java / SpringBoot）

- `service/AlertEventService.java`：移除 `RecordingFileMapper` 注入和 `ingestAlert` 中的录像查找逻辑
- `service/AlertService.java`：注入 `RecordingFileMapper`，在 `mapToAlertVO` 中动态查询录像并填充 `recordUrl` + `eventTimeOffset`
- `vo/AlertVO.java`：新增 `eventTimeOffset` 字段（Double 类型）

### frontend（Vue3 / Element Plus）

- `App.vue`：`evidenceSummary()` 增强，同时考虑 `record_url` 状态
- `services/smartClassApi.js`：`normalizeAlert()` 已有 `event_time_offset` 映射，无需改动
