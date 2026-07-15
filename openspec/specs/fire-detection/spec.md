# 明火检测规范

## Purpose

定义 AI 服务使用 YOLO 从实时视频帧检测明火、过滤无效结果、生成标准事件并接入告警系统的行为。
## Requirements
### Requirement: Fire model loading and graceful degradation

AI 服务 SHALL 按 `backend_ai/config/model.yaml` 加载 `fire` 模型；模型被禁用或加载失败时 SHALL 将模块状态标记为未加载，且不得影响人脸、行为、区域或音频模块运行。

#### Scenario: Fire model loads successfully
- **WHEN** `fire.enabled` 为 true 且配置的 YOLO 权重可以加载
- **THEN** `/model/status` 中 fire 模块 SHALL 返回 `loaded: true`

#### Scenario: Fire model is unavailable
- **WHEN** 模型被禁用、权重不存在或加载失败
- **THEN** fire 模块 SHALL 返回空检测结果
- **AND** 其他 AI 模块 SHALL 继续运行

### Requirement: Fire inference filters invalid boxes

AI 服务 SHALL 对明火模型结果应用有效置信度、最小框面积和单帧最大数量限制，并按置信度降序返回有效结果。

#### Scenario: Detection is below confidence threshold
- **WHEN** 模型框置信度低于当前有效阈值
- **THEN** AI 服务 SHALL 丢弃该检测框

#### Scenario: Detection area is too small
- **WHEN** 模型框面积小于 `min_bbox_area`
- **THEN** AI 服务 SHALL 丢弃该检测框

#### Scenario: Too many valid detections
- **WHEN** 单帧有效检测数量超过 `max_detections`
- **THEN** AI 服务 SHALL 按置信度降序仅保留前 `max_detections` 项

### Requirement: Fire detection emits standard events

每个有效明火检测 SHALL 生成 `event_type: flame_detected` 的标准事件候选，包含置信度、等级、目标像素框、稳定 track key、持续阈值和冷却时间，并交由事件引擎确认及告警入库。

#### Scenario: Valid fire detection
- **WHEN** 一个明火检测通过全部过滤条件
- **THEN** 事件候选 SHALL 包含原始像素 `target.bbox`
- **AND** 置信度不低于 0.8 时等级 SHALL 为 `high`
- **AND** 置信度处于 0.6 至 0.8 之间时等级 SHALL 为 `warning`
- **AND** 置信度低于 0.6 时等级 SHALL 为 `info`

### Requirement: Fire module participates in video analysis

`GET /video_feed/<stream_id>` SHALL 支持通过 `modules` 参数启用 fire 模块；`modules=all` SHALL 包含 fire，显式不包含 fire 时 SHALL 跳过明火推理。

#### Scenario: All modules requested
- **WHEN** 客户端请求视频流并使用 `modules=all`
- **THEN** 已加载的 fire 模块 SHALL 分析每个被认领的新帧

#### Scenario: Fire module omitted
- **WHEN** `modules` 参数不包含 `fire`
- **THEN** AI 服务 SHALL NOT 对该请求执行明火推理

### Requirement: Fire detection applies the active rule threshold

AI 明火服务 MUST 将 SpringBoot 的 `fire_detected` 规则视为 `flame_detected` 事件的有效规则别名，并 SHALL 使用模型安全下限与启用规则阈值中的较大值过滤检测框。

#### Scenario: Backend rule is stricter than model default
- **WHEN** 模型配置阈值为 0.25 且启用的 `fire_detected` 规则阈值为 0.80
- **THEN** 置信度低于 0.80 的检测 SHALL NOT 生成 `flame_detected`

#### Scenario: Fire rule is disabled
- **WHEN** 配置缓存中不存在启用的 `fire_detected` 或 `flame_detected` 规则
- **THEN** 明火检测 SHALL NOT 生成业务事件或告警

### Requirement: Fire detection filters non-fire classes

当模型结果包含类别元数据时，AI 服务 SHALL 只接受配置白名单中的火焰类别，不得把其他类别的任意检测框映射为 `flame_detected`。

#### Scenario: Non-fire class has high confidence
- **WHEN** 模型以高置信度返回一个不在 `allowed_classes` 中的类别
- **THEN** AI 服务 SHALL 丢弃该检测且 SHALL NOT 推进明火事件状态

#### Scenario: Allowed flame class persists
- **WHEN** 白名单火焰类别持续达到有效置信度和规则持续时间
- **THEN** AI 服务 SHALL 生成并确认 `flame_detected` 告警
