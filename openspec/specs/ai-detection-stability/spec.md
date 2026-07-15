# ai-detection-stability Specification

## Purpose
定义智慧教室实时 AI 分析链路对新鲜帧唯一处理、断流缓冲隔离、稳定复流、区域坐标匹配、检测画框标注以及区域配置热刷新的统一稳定性要求，避免重复告警、断流后误报和真实视频区域漏检。

## Requirements
### Requirement: One fresh frame advances analysis once

AI 服务 SHALL 为每个视频流发布单调递增的帧序号，并且同一帧序号在一个进程内最多推进一次异常事件状态，不得因 MJPEG 轮询速度或消费者数量重复分析。

#### Scenario: Generator polls without a new frame
- **WHEN** 视频生成器多次读取到相同帧序号
- **THEN** AI 服务 SHALL NOT 再次执行该帧的行为、区域或明火事件观察
- **AND** SHALL NOT 因该旧帧生成新的截图或告警

#### Scenario: Multiple consumers read one frame
- **WHEN** 多个 `/video_feed` 消费者同时读取同一流的同一帧序号
- **THEN** 其中最多一个消费者 SHALL 推进该帧的分析状态

### Requirement: Offline episode quarantines buffered frames

AI 服务 SHALL 在首次读取失败后进入一个连续离线候选周期；候选期间到达的短暂缓冲帧不得被分析，也不得立即重置离线告警门控，只有新帧连续成功达到稳定恢复窗口后才算复流。

#### Scenario: Buffered frames arrive after publisher stops
- **WHEN** 推流关闭后读取先失败，随后仅短暂读到缓冲帧并再次失败
- **THEN** AI 服务 SHALL 将其视为同一个离线周期
- **AND** SHALL NOT 对缓冲帧生成其他异常、截图或第二条 `stream_offline`

#### Scenario: Stream recovers stably
- **WHEN** 新帧连续到达达到 `recovery_after_seconds`
- **THEN** AI 服务 SHALL 清除上一离线周期并恢复分析
- **AND** 后续新的持续断流 MAY 生成新的离线事件

### Requirement: Pixel detections match normalized zones

AI 服务 SHALL 在区域几何判断前将 YOLO 像素检测框与前端 0–1 归一化区域统一到同一坐标空间，并保留原始像素框作为事件目标框。

#### Scenario: Phone inside phone-forbidden zone
- **WHEN** 像素坐标的手机框中心位于已启用的归一化 `phone_forbidden` 区域内，且手机属于区域内人员
- **THEN** AI 服务 SHALL 产生 `phone_usage` 检测
- **AND** 返回人员像素框及命中的区域信息用于画框标注

#### Scenario: Person enters danger zone
- **WHEN** 像素坐标人员框的脚点位于已启用的归一化 `danger` 区域内
- **THEN** AI 服务 SHALL 产生 `danger_zone_intrusion` 检测
- **AND** 视频 SHALL 显示人员目标框，事件确认后 SHALL 显示告警覆盖提示

### Requirement: Zone reload affects live analysis

SpringBoot 创建、更新、启停或删除区域后，AI 服务 SHALL 通过现有配置重载链路替换对应视频流的区域缓存，后续新帧 SHALL 使用最新配置。

#### Scenario: Newly created zone is reloaded
- **WHEN** SpringBoot 调用 `/config/reload` 并传入 `stream_id` 与 `reload_items: ["zones"]`
- **THEN** AI 服务 SHALL 仅刷新该流的启用区域缓存
- **AND** 下一新帧 SHALL 使用刷新后的手机禁用区和危险区
