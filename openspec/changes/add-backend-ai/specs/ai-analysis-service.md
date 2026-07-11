## Requirement: AI 服务状态查询

系统必须提供 `GET /model/status` 接口，返回 Flask AI 服务状态、模型加载状态、视频源在线状态、当前 FPS 和最近帧时间。
系统必须使用统一 JSON 返回格式，包含 `code`、`message`、`data`、`timestamp` 和 `trace_id`。

### Scenario: 查询运行中的 AI 服务状态
- GIVEN Flask AI 服务已经启动
- AND 至少一个视频源已配置
- WHEN SpringBoot 或前端调用 `GET /model/status`
- THEN 系统返回 `code=0`
- AND `data.service_status` 为 `running`
- AND `data.models` 包含人脸、危险区域和行为检测模块状态
- AND `data.streams` 包含视频源在线状态、FPS 和最近帧时间

### Scenario: 模型未加载时返回状态而不是中断服务
- GIVEN AI 服务已启动
- AND 某个模型加载失败
- WHEN 调用 `GET /model/status`
- THEN 系统返回 `code=0`
- AND 对应模型的 `loaded` 为 `false`
- AND 返回错误说明或模型不可用状态

## Requirement: 实时视频流输出

系统必须提供 `GET /video_feed/{stream_id}` 接口，返回 `multipart/x-mixed-replace` MJPEG 视频流。
系统必须支持 `annotate` 参数控制是否返回标注画面，支持 `modules` 参数控制启用的 AI 检测模块。

### Scenario: 前端播放带标注实时画面
- GIVEN `stream_id=classroom_01` 的 RTMP 视频源在线
- AND AI 服务已经成功读取视频帧
- WHEN 前端通过 `<img>` 请求 `/video_feed/classroom_01?annotate=true&modules=face,zone,behavior`
- THEN 系统持续返回 MJPEG 帧
- AND 返回帧中包含已启用模块产生的标注信息

### Scenario: 视频源不存在
- GIVEN 请求的 `stream_id` 不在视频源配置中
- WHEN 前端请求 `/video_feed/unknown_stream`
- THEN 系统返回 404
- AND 响应体包含 `code=40401`
- AND `message` 表示视频源不存在

### Scenario: 视频源离线
- GIVEN `stream_id=classroom_01` 已配置
- AND RTMP 拉流失败或长时间没有新帧
- WHEN 前端请求 `/video_feed/classroom_01`
- THEN 系统返回离线占位帧或 503 错误
- AND 前端可以根据响应展示视频源离线或重连状态

## Requirement: 人脸特征提取

系统必须提供 `POST /face/feature/extract` 接口，接收 base64 图片并返回 InsightFace/ArcFace 512 维人脸特征向量。
系统必须拒绝无法解析的图片、无人脸图片和多脸图片。

### Scenario: 单人脸图片提取 512 维特征
- GIVEN SpringBoot 在人脸注册流程中传入一张有效单人脸 base64 图片
- WHEN 调用 `POST /face/feature/extract`
- THEN 系统返回 `code=0`
- AND `data.face_count` 等于 1
- AND `data.feature_dim` 等于 512
- AND `data.feature_vector` 包含 512 个数值
- AND 返回人脸框和质量信息

### Scenario: 图片中未检测到人脸
- GIVEN 请求图片中没有可检测人脸
- WHEN 调用 `POST /face/feature/extract`
- THEN 系统返回错误码 `40002`
- AND `message` 表示未检测到人脸

### Scenario: 图片中检测到多个人脸
- GIVEN 请求图片中包含多个人脸
- WHEN 调用 `POST /face/feature/extract`
- THEN 系统返回错误码 `40003`
- AND `message` 表示检测到多个人脸

### Scenario: 图片无法解析
- GIVEN 请求体中的 `image` 字段为空或不是有效 base64 图片
- WHEN 调用 `POST /face/feature/extract`
- THEN 系统返回错误码 `40001`
- AND 不执行人脸特征提取

## Requirement: 配置与人脸特征缓存刷新

系统必须从 SpringBoot 拉取视频源、危险区域、行为规则和人脸特征库配置。
系统必须支持 SpringBoot 通过刷新接口通知 AI 服务立即更新缓存，同时保留定时拉取作为兜底。

### Scenario: 刷新视频源、区域和规则配置
- GIVEN SpringBoot 修改了视频源、危险区域或检测规则
- WHEN SpringBoot 调用 `POST /config/reload`
- THEN AI 服务根据 `reload_items` 拉取对应配置
- AND 更新本地缓存
- AND 返回刷新数量和更新时间

### Scenario: 刷新人脸特征库
- GIVEN SpringBoot 新增或更新了学生人脸特征
- WHEN SpringBoot 调用 `POST /face/features/reload`
- THEN AI 服务重新拉取人脸特征库
- AND 返回已加载特征数量

### Scenario: Push 刷新失败后定时拉取兜底
- GIVEN SpringBoot 未能成功调用 AI 服务刷新接口
- WHEN 到达 AI 服务定时拉取周期
- THEN AI 服务主动请求 SpringBoot 配置接口
- AND 更新过期缓存

## Requirement: 实时候选事件查询

系统必须提供 `GET /analysis/events` 接口，返回 AI 服务内存中的候选事件。
候选事件必须使用 `event_status` 表示候选状态，不得与 SpringBoot 正式告警的 `alert_status` 混用。

### Scenario: 查询最近候选事件
- GIVEN AI 服务已经检测到一个使用手机候选事件
- WHEN 前端调用 `/analysis/events?stream_id=classroom_01&limit=10`
- THEN 系统返回 `code=0`
- AND `data.items` 最多包含 10 条事件
- AND 事件包含 `event_id`、`stream_id`、`event_type`、`event_name`、`level`、`event_status`、`confidence` 和 `occurred_at`

### Scenario: 按事件类型过滤候选事件
- GIVEN AI 服务内存中同时存在人脸、区域和行为事件
- WHEN 前端调用 `/analysis/events?event_type=phone_usage`
- THEN 系统只返回 `event_type=phone_usage` 的候选事件

### Scenario: 无候选事件
- GIVEN AI 服务尚未检测到任何候选事件
- WHEN 前端调用 `/analysis/events`
- THEN 系统返回 `code=0`
- AND `data.items` 为空数组

## Requirement: 危险区域检测

系统必须根据 SpringBoot 下发的 polygon 区域配置和规则阈值，检测危险区域进入、停留超时和接近预警。

### Scenario: 人员进入危险区域
- GIVEN SpringBoot 已配置 `classroom_01` 的危险区域 polygon
- AND AI 服务检测到人员脚点位于 polygon 内
- WHEN 分析当前视频帧
- THEN 系统生成 `danger_zone_intrusion` 候选事件
- AND 事件 `zone` 字段包含 `zone_id` 和 `zone_name`

### Scenario: 人员在危险区域停留超时
- GIVEN 人员脚点持续位于危险区域 polygon 内
- AND 停留时间超过规则的 `threshold_seconds`
- WHEN 事件服务聚合检测结果
- THEN 系统生成或确认 `danger_zone_stay` 事件
- AND 根据冷却规则避免重复生成正式告警

### Scenario: 人员接近危险区域
- GIVEN 人员脚点未进入危险区域 polygon
- AND 人员脚点到 polygon 边缘的最短距离小于 `config_json.safe_distance`
- WHEN 分析当前视频帧
- THEN 系统生成 `danger_zone_approach` 候选事件
- AND 不将该事件误判为 `danger_zone_intrusion`

## Requirement: 目标行为检测

系统必须支持长时间低头、异常人流聚集和使用手机检测。
系统必须根据置信度阈值、持续时间阈值和冷却时间控制候选事件与正式告警。

### Scenario: 检测使用手机行为
- GIVEN YOLO 检测到 person 和 phone 目标
- AND phone 与 person 满足空间关联规则
- AND 置信度达到规则阈值
- WHEN 行为持续时间超过 `threshold_seconds`
- THEN 系统生成 `phone_usage` 候选事件

### Scenario: 检测长时间低头
- GIVEN AI 服务持续检测到某个目标满足低头规则
- AND 持续时间超过规则阈值
- WHEN 事件服务聚合检测结果
- THEN 系统生成 `head_down` 候选事件
- AND 事件目标包含 `track_id` 或人员框信息

### Scenario: 检测异常人流聚集
- GIVEN 同一局部区域内检测到人员数量或密度超过规则阈值
- WHEN 聚集状态持续超过配置时间
- THEN 系统生成异常人流聚集候选事件
- AND 事件等级为 `warning` 或规则指定等级

### Scenario: 短暂行为不入库
- GIVEN 某个学生短暂低头或短暂拿起手机
- AND 行为持续时间未达到规则阈值
- WHEN 事件服务处理检测结果
- THEN 系统可以保留候选状态
- AND 不调用 SpringBoot `/alerts/ai` 入库正式告警

## Requirement: 候选事件确认与正式告警入库

系统必须在候选事件满足确认条件后调用 SpringBoot `/alerts/ai` 入库。
系统必须将 AI 候选事件字段映射为 SpringBoot 告警入库字段。

### Scenario: 候选事件确认后入库
- GIVEN AI 服务已经生成 `phone_usage` 候选事件
- AND 事件满足置信度、持续时间和冷却规则
- WHEN 事件服务确认该事件
- THEN `alert_client.py` 调用 SpringBoot `/alerts/ai`
- AND 请求体包含 `event_id`、`stream_id`、`alert_type`、`alert_name`、`level`、`confidence`、`occurred_at` 和 `duration_seconds`
- AND 入库成功后候选事件更新为 `event_status=confirmed`

### Scenario: SpringBoot 告警入库失败
- GIVEN 候选事件已经满足确认条件
- AND SpringBoot `/alerts/ai` 返回错误或不可达
- WHEN AI 服务尝试入库
- THEN 系统记录错误日志
- AND 返回或内部标记 `50003` 类错误
- AND 不将候选事件错误标记为已确认

### Scenario: 截图保存失败
- GIVEN 候选事件确认时需要保存截图
- AND 截图目录不可写或编码失败
- WHEN 系统保存截图
- THEN 系统记录截图保存失败
- AND 使用错误码 `50004` 表示截图保存失败

## Requirement: 本次范围排除项

系统本次不得实现明火检测、活体检测、摔倒检测、异常声学检测、轨迹存储查询、钉钉通知和 AI 日报生成。
系统可以保留事件枚举或模块扩展点，但不得将这些能力作为本次交付验收内容。

### Scenario: 明火检测不作为本次交付内容
- GIVEN 请求启用 `modules=fire`
- WHEN 当前版本未实现明火检测模块
- THEN 系统不得加载明火检测模型
- AND 不生成 `flame_detected` 事件
- AND 可在状态接口中标记该模块未启用或不在本次范围
