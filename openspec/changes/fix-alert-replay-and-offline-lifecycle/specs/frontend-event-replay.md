## MODIFIED Requirements

### Requirement: Video player dialog cleanup preserves reactive consistency

回放弹窗关闭时，前端必须同时释放媒体资源并清空响应式录像 URL，使相同 `record_url` 在下次打开时能够重新绑定到 `<video>`。

#### Scenario: Reopen the same alert recording

- **GIVEN** 用户已打开并关闭录像 URL `A`
- **WHEN** 用户再次打开同一条告警的录像 URL `A`
- **THEN** `<video>` SHALL 重新加载 URL `A`
- **AND** 播放器 SHALL 再次定位到该告警的 `event_time_offset`

#### Scenario: Two alerts share one segment

- **GIVEN** 告警 A 和告警 B 具有相同 `record_url` 但不同 `event_time_offset`
- **WHEN** 用户先播放并关闭 A，再点击 B
- **THEN** 播放器 SHALL 重新加载共享切片
- **AND** 播放器 SHALL 定位到 B 的偏移而不是保持空 source 或 A 的偏移

#### Scenario: Dialog cleanup releases media

- **GIVEN** 回放视频正在加载或播放
- **WHEN** 用户关闭弹窗
- **THEN** 前端 SHALL 暂停视频
- **AND** 前端 SHALL 清空响应式 `replayUrl`
- **AND** 前端 SHALL 重置回放偏移并释放媒体资源
