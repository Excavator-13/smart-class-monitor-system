# 修复视频源状态、事件等级配置与后端初始化

## 背景

当前后端存在三类相互关联的问题：

1. 视频源接口向教师返回了 RTMP 地址，系统状态页也把配置状态 `enabled` 误当成真实在线状态；后端 Nginx 状态解析依赖非标准的 `publish active` 节点，无法正确识别常见 Nginx-RTMP `/stat` XML。
2. 告警等级存放在 `behavior_rule.level`，导致检测参数和异常事件严重性耦合。部分检测器不使用行为规则，同一规则还可能产生多个严重程度不同的事件，因此该模型无法覆盖全部异常事件。
3. `DataInitializer` 每次 SpringBoot 启动都会清空所有业务表并插入演示数据，既会破坏已有数据，也缺少与 AI 实际事件类型一一对应的完整默认配置。

## 目标

- 管理员可查看视频源 RTMP 地址，教师收到的接口响应中不包含该敏感字段；AI 内部调用仍可获得完整地址。
- 视频源在线状态来自 Nginx-RTMP `/stat` 中真实发布者状态，状态服务不可达时明确返回 `unknown`。
- 检测规则只管理启用、持续阈值、置信度、冷却时间等检测参数。
- 每个异常 `event_type` 在事件配置中独立拥有告警等级和评分，并由 AI 与 SpringBoot 告警入库共同遵守。
- 初始化数据与当前 AI 能力对齐，启动初始化幂等，不再清空已有业务数据。

## 范围

- SpringBoot 视频源接口、Nginx 状态解析、事件配置、告警入库和初始化逻辑。
- Flask AI 配置缓存与事件等级解析。
- Vue 系统状态页和告警配置页的契约适配。
- Swagger/DTO/VO 示例及 `docs/backend-interface-and-module-notes.md`。

## 非目标

- 不修改 AI 日报功能。
- 不改变异常检测算法、模型权重或告警冷却策略。
- 不修改录像、截图和钉钉通知的存储方案。

## 兼容性说明

- `/score-config` 路径保留，新增 `level` 字段；原有 `score`、`label`、`note` 字段继续兼容。
- AI 上报中的 `level` 暂时保留以兼容旧客户端，但 SpringBoot 按 `alert_type` 的事件配置进行最终校正。
- 旧数据库中的 `behavior_rule.level` 可以暂时保留为未使用兼容列；新接口和新代码不再读写该字段。
- 本 change 替代 `fix-settings-rules-and-report` 中“从规则读取 level”和“在规则卡片编辑 level”的相关设计。

