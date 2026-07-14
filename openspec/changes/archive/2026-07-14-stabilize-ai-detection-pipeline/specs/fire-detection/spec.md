## ADDED Requirements

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

