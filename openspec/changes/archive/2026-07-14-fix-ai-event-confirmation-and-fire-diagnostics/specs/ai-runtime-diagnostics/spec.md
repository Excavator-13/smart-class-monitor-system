## ADDED Requirements

### Requirement: Intermittent phone detections can confirm
手机已持续位于禁用区时，短于手机专用连续性窗口的模型漏帧 SHALL NOT 重置候选事件。

#### Scenario: Phone disappears briefly
- **WHEN** 两次有效手机检测间隔不超过 6 秒
- **THEN** 事件 SHALL 延续同一候选周期

### Requirement: Fire diagnostics identify filtering stage
模型状态 SHALL 返回最近一次明火推理的原始框数及类别、置信度、面积过滤数量。

#### Scenario: Model returns no boxes
- **WHEN** 明火模型完成推理但没有原始框
- **THEN** 状态 SHALL 显示 raw_detections 为 0

### Requirement: AI event responses are JSON safe
事件查询 SHALL 将 NumPy 等运行期类型转换为标准 JSON 类型，不得因此返回 500。

#### Scenario: Event contains numpy values
- **WHEN** 事件目标包含 NumPy 数组或标量
- **THEN** `/analysis/events` SHALL 返回 200 和标准数组/数字
