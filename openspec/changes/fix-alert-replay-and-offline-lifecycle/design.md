# 异常录像回放与离线事件生命周期修复设计

## Goals

- 让 `recording_file` 的切片时间范围覆盖实际 MP4 媒体时长，消除关键帧导致的查询空洞。
- 保证异常回放解析只返回 `/records/**` 切片路径。
- 保证同一个切片被不同异常或同一异常重复打开时都能重新加载。
- 将短暂拉流失败与持续离线分开，并确保一个持续离线周期只入库一次。

## Non-Goals

- 不重构现有 MJPEG 输出架构。
- 不解决多进程/多实例间的分布式离线去重。
- 不改变告警 API、JSON 字段或数据库表。
- 不改变 30 秒目标切片配置；30 秒仍是目标值，不再被当成实际媒体时长。

## Current Failure Timeline

实测第一段文件为 `16:33:15-16:33:46`，下一段从 `16:33:47` 开始。旧脚本把第一段登记成 `16:33:15-16:33:45`，所以 `16:33:46` 的事件无法匹配切片，转而匹配完整录像；更长的关键帧漂移还会让真实存在于切片中的事件得到 `record_url=null`。

前端中多条告警可共享相同 `record_url`。关闭时直接把 DOM `src` 清空，而 `replayUrl` 仍保存旧值；下一条告警再次赋相同 URL 时 Vue 不执行 DOM patch。

AI 读取线程在任意一次读取失败后立即设置 `online=false`，`/video_feed` 随即以零阈值上报离线。拉流恢复后事件周期重置，真正停止推流时再产生一条新的离线告警。

## Decisions

### 1. 以 ffprobe 真实时长建立切片索引

`flv2mp4.sh` 在 MP4 转换成功后调用：

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 file.mp4
```

- 对 `segment` 和 `nginx_record` 都优先采用真实媒体时长。
- 切片 `ended_at` 使用 `started_at + ceil(duration)`，避免 DATETIME 秒精度在小数截断后重新制造不足一秒的空洞。
- `duration_seconds` 保留 ffprobe 返回的小数值。
- ffprobe 失败时，切片保守回退 30 秒；完整录像保留现有 mtime 推算逻辑。

### 2. 事件回放只解析 segment MP4

`findContainingRecording` 增加：

```sql
AND source_type = 'segment'
AND file_ext = 'mp4'
```

完整录像继续由 `/recordings` 管理，但不参与异常事件的 30 秒片段回放。这样避免根目录 `/` 被拼成 `//filename`，也避免停止推流后匹配结果从切片切换到完整录像。

### 3. 保持 Vue 响应式状态与 video DOM 一致

关闭弹窗时：

1. 暂停当前视频；
2. 设置 `replayUrl.value = ""`；
3. 设置 `replayOffset.value = 0`；
4. 调用 `video.load()` 释放当前资源。

不再只修改 DOM `src`。再次打开相同 URL 时，响应式状态从空字符串变为 URL，Vue 必然重新绑定。

### 4. 离线采用持续超时和单次跃迁门控

`StreamState` 增加：

- `failure_started_at`：当前连续不可用周期开始时间；
- `offline_alerted`：本周期是否已经发出离线告警。

读取失败时立即停止向分析层返回旧帧，但只记录失败周期。`StreamManager.should_emit_offline_alert(stream_id)` 仅在以下条件全部满足时返回一次 `true`：

- 连续不可用时间达到 `offline_after_seconds`；
- 当前周期尚未告警。

读取成功后清空失败时间和告警门控。`/video_feed` 在帧为空时只在该方法返回 `true` 时调用 `observe_stream_offline`。

该方案保持改动最小，同时消除单次读取失败和同一进程内多个视频消费者造成的重复告警。离线检测仍由视频请求驱动，多实例去重不在本次范围。

## Risks / Trade-offs

| 风险 | 影响 | 处理 |
|---|---|---|
| 服务器缺少 ffprobe | 真实时长无法读取 | ffmpeg 部署通常自带 ffprobe；脚本保留回退值并记录错误 |
| `ceil(duration)` 最多扩大不足 1 秒 | 相邻片段可能轻微重叠 | 查询按 `started_at DESC` 选择最新片段，重叠比空洞安全 |
| 离线告警延后 | 真正断流需等待默认 10 秒 | 符合现有 `offline_after_seconds` 配置语义，避免抖动误报 |
| 无浏览器视频消费者时仍不触发告警 | 延续当前架构限制 | 本次不引入独立后台监控线程，后续可单独演进 |
| 历史索引仍为固定 30 秒 | 旧事件仍可能匹配失败 | 本次只保证新文件正确；需要时另行执行一次性回填 |

## Verification

- Shell 静态检查并以模拟 ffprobe 数值验证 `ended_at` 计算。
- SpringBoot mapper 测试/编译确认 SQL 仅选择 segment MP4。
- Vue 构建通过，并人工验证相同 URL 关闭后再次打开。
- AI 单元测试覆盖短暂失败、持续超时、同周期只发一次、恢复后可发新周期。
- OpenSpec change 结构与场景完整性校验。
