## 1. AlertEventService 移除 ingest 时录像查找

- [x] 1.1 `AlertEventService.java`：移除 `RecordingFileMapper recordingMapper` 字段和构造函数参数
- [x] 1.2 `AlertEventService.java`：移除 `ingestAlert()` 中 `if (event.getOccurredAt() != null && event.getStreamId() != null)` 整个 try-catch 块（含 `findContainingRecording` 调用、`/segments` → `/records` 替换、`Duration.between` 计算）
- [x] 1.3 `AlertEventService.java`：移除不再需要的 import（`RecordingFile`、`RecordingFileMapper`、`Duration`）

## 2. AlertService 查询时动态填充录像信息

- [x] 2.1 `AlertService.java`：注入 `RecordingFileMapper`（构造函数新增参数）
- [x] 2.2 `AlertService.java`：新增 import（`RecordingFile`、`RecordingFileMapper`、`Duration`）
- [x] 2.3 `AlertService.java`：修改 `mapToAlertVO()`，当 `record_path` 列为空且 `stream_id` + `occurred_at` 非空时，调用 `findContainingRecording` 查库
- [x] 2.4 `AlertService.java`：查到录像时构造 `recordUrl`（`filePath` 的 `/segments` 替换为 `/records` + `/` + `fileName`），计算 `eventTimeOffset`（`Math.max(0, Duration.between(startedAt, occurredAt).getSeconds())`）
- [x] 2.5 `AlertService.java`：`filePath` 为 null 时 `recordUrl` 仅用 `/` + `fileName`
- [x] 2.6 `AlertService.java`：查库异常时 log warning，`recordUrl` 和 `eventTimeOffset` 保持 null

## 3. AlertVO 新增 eventTimeOffset 字段

- [x] 3.1 `AlertVO.java`：新增 `eventTimeOffset` 字段（`Double`，nullable），添加 `@Schema` 注解
- [x] 3.2 `AlertVO.java`：新增 getter/setter

## 4. 前端 evidenceSummary 增强

- [x] 4.1 `App.vue`：修改 `evidenceSummary()` 函数，同时检查 `snapshot_url` 和 `record_url`，返回"截图 + 录像"、"已保存截图"、"仅录像"、"证据生成中"

## 5. 编译与验证

- [x] 5.1 `mvn -DskipTests compile` 编译通过
- [ ] 5.2 验证 `GET /alerts` 返回的 AlertVO 包含 `eventTimeOffset` 字段
- [ ] 5.3 验证告警 `record_path` 为空且录像已入库时，`recordUrl` 和 `eventTimeOffset` 被动态填充
- [ ] 5.4 验证告警 `record_path` 为空且录像未入库时，`recordUrl` 和 `eventTimeOffset` 为 null
- [ ] 5.5 验证告警 `record_path` 已有值时，不触发动态查询，直接映射列值
- [ ] 5.6 验证前端 `evidenceSummary()` 在不同证据组合下显示正确文本
- [ ] 5.7 验证前端录像按钮在 `record_url` 有值时可点击，回放 seek 到 `event_time_offset` 位置
