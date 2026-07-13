## MODIFIED Requirements

### Requirement: Segment index uses actual media duration

切片转码完成后，系统必须根据生成的 MP4 文件真实媒体时长写入 `recording_file.duration_seconds` 和 `ended_at`，不得把目标切片长度 30 秒无条件当成实际长度。

#### Scenario: Keyframe makes a segment longer than 30 seconds

- **GIVEN** 一个切片从 `16:33:15` 开始，ffprobe 返回实际时长 `31.2` 秒
- **WHEN** `flv2mp4.sh` 写入该切片索引
- **THEN** `duration_seconds` SHALL 保存实际媒体时长 `31.2`
- **AND** `ended_at` SHALL 至少覆盖到 `16:33:47`
- **AND** 发生于 `16:33:46` 的事件 SHALL 落在该切片索引范围内

#### Scenario: Media duration has fractional seconds

- **GIVEN** ffprobe 返回非整数媒体时长
- **WHEN** 系统计算 DATETIME 秒精度的 `ended_at`
- **THEN** 系统 SHALL 向上取整结束秒数
- **AND** 系统 SHALL NOT 因截断小数产生新的时间空洞

#### Scenario: ffprobe cannot read duration

- **GIVEN** MP4 转换成功但 ffprobe 未返回有效正数时长
- **WHEN** 系统写入切片索引
- **THEN** 系统 SHALL 使用目标切片时长作为保守回退
- **AND** 系统 SHALL 记录可诊断的时长读取失败信息
