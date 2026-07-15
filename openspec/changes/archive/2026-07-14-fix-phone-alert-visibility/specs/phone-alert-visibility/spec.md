## ADDED Requirements

### Requirement: Confirmed phone alerts remain visible
SpringBoot 已入库的 `phone_usage` 告警 SHALL 在前端告警管理中显示，不得因响应缺少目标框而被过滤。

#### Scenario: Historical alert has no target bbox
- **WHEN** `/alerts` 返回一条无 `target_info` 的已入库手机告警
- **THEN** 前端 SHALL 显示该告警

### Requirement: Alert API returns target metadata
`/alerts` 列表和详情 SHALL 返回数据库中的 `target_info` 与 `zone_id`。

#### Scenario: Phone alert contains target data
- **WHEN** 数据库记录包含目标框和区域 ID
- **THEN** API SHALL 原样返回这些字段

### Requirement: Confirmed phone box persists briefly
AI SHALL 在手机事件确认后短时保持最近目标框和 `Using phone` 标签。

#### Scenario: Raw detection disappears after confirmation
- **WHEN** 手机事件已确认但后续帧短暂未识别到手机
- **THEN** 视频 SHALL 在配置时长内继续显示最近确认框

### Requirement: Legacy event route remains compatible
AI SHALL 支持 `/events` 查询并返回与 `/analysis/events` 相同的数据结构。

#### Scenario: Legacy client queries events
- **WHEN** 客户端请求 `GET /events`
- **THEN** AI SHALL 返回事件列表而不是 404
