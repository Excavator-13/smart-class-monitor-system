# 修复异常录像回放与离线事件生命周期

## Why

全链路联调确认了三个相互叠加的缺陷：

1. FFmpeg 使用 `-c copy -segment_time 30` 时，实际切片边界受关键帧影响，并不严格等于 30 秒；当前入库脚本却固定写入 `duration_seconds=30`、`ended_at=started_at+30s`，导致真实录像存在但数据库时间范围出现空洞。
2. 前端关闭回放弹窗时直接清空 DOM `video.src`，但保留响应式 `replayUrl`；多个异常共享同一切片 URL 时，后续点击不会触发 Vue 重新绑定 `src`。
3. AI 在单次 `cap.read()` 失败后立即将流标记离线，且 `stream_offline` 阈值为 0；短暂拉流抖动会产生假离线，恢复后真正断流又产生第二条告警。

## What Changes

- Nginx 转码入库脚本通过 `ffprobe` 读取 MP4 真实时长，并据此写入切片 `duration_seconds` 和 `ended_at`。
- SpringBoot 的异常录像动态关联只选择 `source_type='segment'` 的 MP4 切片，不再回退到完整 `nginx_record`。
- Vue 回放弹窗关闭时同步清空响应式 URL 和偏移，确保相同切片可以重复打开并按不同偏移播放。
- Flask AI 将“读取暂时失败”和“持续离线告警”分离：失败期间不再分析陈旧帧，只有持续超过 `offline_after_seconds` 才发出一次离线告警；读取恢复后才允许下一次离线周期告警。
- 增加针对真实切片时长、切片筛选、重复回放状态和离线状态跃迁的验证。

## Capabilities

- **recording-segment-metadata**：切片索引反映媒体真实时长。
- **alert-recording-resolution**：事件回放只关联事件切片。
- **frontend-event-replay**：相同录像 URL 可重复打开并重新定位。
- **stream-offline-lifecycle**：持续离线单周期只告警一次。

## Non-Goals

- 不修改数据库表结构。
- 不裁剪事件前后固定秒数的新视频文件。
- 不取消 Nginx 完整录像备份。
- 不引入 WebSocket、消息队列或多实例分布式锁。
- 不自动修复既有 `recording_file` 历史数据；历史数据可按实际媒体时长单独回填。

## Impact

- `nginx/flv2mp4.sh`
- `backend_system` 的 `RecordingFileMapper`、录像动态关联测试/文档
- `frontend/src/App.vue`
- `backend_ai/services/stream_manager.py`、`backend_ai/app.py` 及对应测试
- `/alerts` 响应契约字段不变，数据库 schema 不变
