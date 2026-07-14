## ADDED Requirements

### Requirement: 启动初始化不得破坏已有数据

SpringBoot 启动初始化 SHALL 幂等执行，SHALL NOT 清空已有业务表。

#### Scenario: 已有业务数据时重启

- **GIVEN** 数据库已有用户、视频源、人员、区域或告警
- **WHEN** SpringBoot 重启并执行初始化器
- **THEN** 已有记录 SHALL 保留
- **AND** 默认记录 SHALL NOT 重复插入

### Requirement: 默认行为规则覆盖当前规则驱动检测能力

初始化器 SHALL 确保六个规则类型存在：`phone_usage`、`flame_detected`、`fall_detected`、`head_down`、`crowd_gathering`、`danger_zone`。

#### Scenario: 部分规则缺失

- **GIVEN** 行为规则表只包含部分默认规则
- **WHEN** 初始化器运行
- **THEN** 缺失规则 SHALL 被补齐
- **AND** 已有规则的管理员配置 SHALL 保持不变

### Requirement: 默认事件配置覆盖所有异常事件

初始化器 SHALL 为当前 AI 定义的每个异常事件建立独立事件配置，并排除正常事件 `face_recognized`。

#### Scenario: 空事件配置表启动

- **WHEN** 初始化器运行
- **THEN** 所有已定义异常事件 SHALL 拥有唯一 `alert_type` 配置
- **AND** 每项 SHALL 具有合法 `level` 和 0 到 100 的 `score`

