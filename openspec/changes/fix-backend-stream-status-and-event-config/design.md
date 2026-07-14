# 设计：视频源状态与事件配置解耦

## 1. 视频源敏感字段与在线状态

### 1.1 RTMP 地址权限

`JwtAuthenticationInterceptor` 已把 `currentRole` 写入 request attribute。视频源查询接口根据调用者决定是否映射 `rtmp_url`：

- `admin`：返回完整 RTMP 地址。
- `teacher`：`rtmp_url` 不序列化或返回 `null`。
- 携带合法 `X-Internal-Token` 的 AI 内部调用：返回完整地址，并在 request attribute 中标记内部调用。

权限判断必须在 SpringBoot 响应生成阶段完成，前端的条件渲染只负责展示，不能作为安全边界。

### 1.2 在线状态

`video_stream.status` 继续表示配置状态 `enabled/disabled`，不代表推流在线。

`GET /streams/{stream_id}/status` 读取 Nginx-RTMP `/stat` XML：

- 找到同名 `<stream>`，且其 `<clients>` 中至少一个 `<client>` 含 `<publishing/>`，返回 `online`。
- 兼容已有 `publish active="true"` 格式。
- 找到流但无发布者或找不到流，返回 `offline`。
- HTTP 请求失败、XML 无法解析，返回 `unknown`。
- 在线时优先使用 `<stream><time>` 作为 uptime。

前端加载视频源列表后并发调用状态接口，用结果覆盖展示状态；不得再把 `enabled` 映射为 `online`。

## 2. 事件等级配置

### 2.1 数据模型

沿用 `score_config` 表作为事件展示配置表，键改为实际 `event_type`，新增：

- `level`: `info | warning | high`

每行表示一个具体异常事件的中文名、默认等级、评分和说明。检测规则 `behavior_rule` 不再向 DTO/VO、AI 缓存或前端暴露 `level`。

### 2.2 配置传播

1. 管理员通过 `PUT /score-config/{id}` 修改 `level` 或 `score`。
2. SpringBoot 保存后通知 AI 重载 `event_configs`。
3. AI `ConfigClient` 从 `/score-config` 缓存 `event_type -> config`。
4. `AnalysisService` 在进入 `EventService.observe()` 前统一按 `event_type` 覆盖等级；`stream_offline` 同样走该配置。
5. SpringBoot `AlertEventService` 入库时再次按 `alert_type` 查配置并覆盖请求等级，作为最终一致性保护。

未知事件类型使用请求中的合法等级；请求等级也无效时回退 `warning`。

### 2.3 默认事件配置

初始化覆盖当前 AI 的异常事件集合：

`stranger_detected`、`danger_zone_intrusion`、`danger_zone_stay`、`danger_zone_approach`、`phone_usage`、`head_down`、`crowd_gathering`、`fall_detected`、`leave_seat`、`flame_detected`、`spoof_detected`、`deepfake_detected`、`abnormal_sound`、`stream_offline`，另保留 `general` 作为前端未知类型兜底。

`face_recognized` 属于正常识别事件，不初始化为告警配置。

## 3. 初始化策略

移除 `truncateAll()`。初始化采用按业务唯一键“缺失才插入”的方式：

- 用户按 `username`。
- 视频源按 `stream_id`。
- 行为规则按 `rule_type`。
- 事件配置按 `alert_type`。
- 演示人员、区域和告警不再在每次启动时重复插入；已有业务数据必须保留。

行为规则只初始化当前真正由规则缓存驱动的六项：

`phone_usage`、`flame_detected`、`fall_detected`、`head_down`、`crowd_gathering`、`danger_zone`。

## 4. 风险与处理

- 旧前端依赖规则 `level`：本次同步把等级编辑器移到告警配置模块。
- 旧 AI 只重载 `rules`：配置轮询和启动 bootstrap 增加 `event_configs`，同时保留后端入库校正。
- Nginx 状态页可能采用不同 XML：解析同时支持标准 `<publishing/>` 和旧 `publish active="true"`。
- 旧数据库仍有 `behavior_rule.level`：本次不执行破坏性删列；代码停止使用即可完成解耦，后续数据库迁移可单独归档。

