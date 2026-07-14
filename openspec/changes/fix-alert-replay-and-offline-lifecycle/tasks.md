## 1. OpenSpec 与范围确认

- [x] 1.1 创建并阅读 proposal、design、delta specs 和 tasks
- [x] 1.2 确认不修改 API 契约和数据库结构

## 2. 录像切片索引与解析

- [x] 2.1 修改 `flv2mp4.sh`，通过 ffprobe 获取实际 MP4 时长
- [x] 2.2 使用实际时长计算切片 `duration_seconds` 与秒精度向上取整的 `ended_at`
- [x] 2.3 修改 `RecordingFileMapper.findContainingRecording`，仅匹配 `segment` MP4
- [x] 2.4 同步后端接口说明中的异常录像解析规则

## 3. 前端重复回放

- [x] 3.1 修改回放关闭逻辑，同步清空 `replayUrl`、偏移和媒体资源
- [x] 3.2 验证同一切片 URL 可连续打开并按不同偏移播放

## 4. AI 离线生命周期

- [x] 4.1 为 `StreamState` 增加连续失败时间与单周期告警状态
- [x] 4.2 实现持续达到 `offline_after_seconds` 才允许发出一次告警
- [x] 4.3 读取恢复后重置离线周期，失败期间不返回陈旧帧分析
- [x] 4.4 调整 `/video_feed` 仅在离线状态跃迁时调用告警上报
- [x] 4.5 增加短暂失败、持续离线、单周期去重和恢复后新周期测试

## 5. 验证与同步

- [x] 5.1 运行 AI 针对性单元测试
- [x] 5.2 运行 SpringBoot 编译/测试
- [x] 5.3 运行 Vue 生产构建
- [x] 5.4 校验 OpenSpec 文件结构和场景完整性
- [x] 5.5 将完成后的规范同步到 `openspec/specs/`
- [ ] 5.6 提示用户确认是否归档 change
