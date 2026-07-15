## ADDED Requirements

### Requirement: 异常事件独立配置等级和评分

系统 SHALL 按具体 `event_type` 保存并读取告警等级和评分，检测规则 SHALL NOT 决定告警等级。

#### Scenario: 查询事件配置

- **WHEN** 调用 `GET /score-config`
- **THEN** 每条记录 SHALL 包含 `alert_type`、`label`、`level`、`score` 和 `note`
- **AND** `alert_type` SHALL 使用 AI 实际事件类型

#### Scenario: 管理员修改事件等级

- **GIVEN** 当前用户为管理员
- **WHEN** 调用 `PUT /score-config/{id}` 并提交合法 `level`
- **THEN** SpringBoot SHALL 保存该等级
- **AND** SHALL 通知 AI 重载事件配置

#### Scenario: AI 生成异常事件

- **GIVEN** AI 缓存中存在该 `event_type` 的事件配置
- **WHEN** 检测结果进入事件确认流程
- **THEN** 事件 SHALL 使用事件配置中的 `level`
- **AND** SHALL NOT 使用行为规则中的等级

#### Scenario: SpringBoot 接收 AI 告警

- **GIVEN** SpringBoot 存在该 `alert_type` 的事件配置
- **WHEN** AI 上报告警
- **THEN** 入库 `level` SHALL 使用 SpringBoot 事件配置值

#### Scenario: 未知事件兼容

- **GIVEN** SpringBoot 不存在该事件类型配置
- **WHEN** AI 上报告警
- **THEN** 合法请求等级 SHALL 被保留
- **AND** 无效或空等级 SHALL 回退为 `warning`

## MODIFIED Requirements

### Requirement: 行为规则仅控制检测行为

行为规则接口 SHALL 只管理规则名称、启用状态、持续阈值、置信度阈值、冷却时间和扩展配置，不再暴露或更新告警等级。

#### Scenario: 更新行为规则

- **WHEN** 管理员更新持续阈值或启用状态
- **THEN** 修改 SHALL 影响 AI 检测行为
- **AND** SHALL NOT 修改任何异常事件的 `level`

