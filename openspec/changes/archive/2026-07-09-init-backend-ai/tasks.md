# Tasks

## 1. 服务骨架与配置

- [x] 1.1 创建 `backend_ai/app.py`，初始化 Flask 应用和路由注册。
- [x] 1.2 创建 `backend_ai/config/app.yaml` 和 `backend_ai/config/model.yaml`，配置服务端口、SpringBoot 地址、模型路径、阈值默认值和轮询间隔。
- [x] 1.3 创建 `backend_ai/utils/response.py`，统一 JSON 返回格式、错误码、时间戳和 `trace_id`。
- [x] 1.4 创建 `backend_ai/utils/logger.py`，统一服务日志输出。
- [x] 1.5 创建 `backend_ai/requirements.txt`，记录 `classroom-ai-gpu` 环境核心依赖版本。
- [x] 1.6 创建 `backend_ai/tests/` 测试目录，配置 pytest 测试发现规则。

## 2. 配置同步与外部客户端

- [x] 2.1 实现 `services/config_client.py`，从 SpringBoot 拉取 `/streams`、`/zones`、`/rules` 和 `/students/face-features`。
- [x] 2.2 实现配置缓存结构，支持按 `stream_id` 获取视频源、区域和规则。
- [x] 2.3 实现 `POST /config/reload`，支持刷新视频源、区域和规则缓存。
- [x] 2.4 实现 `POST /face/features/reload`，支持刷新全部或指定学生的人脸特征缓存。
- [x] 2.5 实现定时拉取兜底逻辑，避免 SpringBoot Push 失败后配置长期不一致。

## 3. 视频流与状态接口

- [x] 3.1 实现 `services/stream_manager.py`，通过 OpenCV `VideoCapture` 拉取 RTMP 视频流。
- [x] 3.2 实现帧缓存、离线状态、最后一帧时间和基础重连逻辑。
- [x] 3.3 实现 `GET /model/status`，返回服务状态、模型加载状态和视频源状态。
- [x] 3.4 实现 `GET /video_feed/{stream_id}`，返回 `multipart/x-mixed-replace` MJPEG 视频流。
- [x] 3.5 支持 `annotate` 和 `modules` 查询参数，便于关闭标注或按模块联调。

## 4. 人脸识别

- [x] 4.1 实现 `services/face_service.py`，加载 InsightFace/ArcFace 模型。
- [x] 4.2 实现图片解析和人脸检测，处理非法图片、无人脸、多脸错误。
- [x] 4.3 实现 `POST /face/feature/extract`，返回 512 维 `feature_vector`、质量信息和人脸框。
- [x] 4.4 实现实时帧中的人脸识别，与缓存特征库进行相似度比对。
- [x] 4.5 生成人脸识别事件 `face_recognized` 和陌生人事件 `stranger_detected`。

## 5. 危险区域检测

- [x] 5.1 实现 `utils/geometry.py`，支持点在 polygon 内、点到 polygon 边缘距离、归一化坐标转换。
- [x] 5.2 实现 `services/zone_service.py`，根据人员脚点判断 `danger_zone_intrusion`。
- [x] 5.3 实现危险区域停留计时，超过 `threshold_seconds` 生成 `danger_zone_stay`。
- [x] 5.4 实现危险区域接近预警，低于 `config_json.safe_distance` 生成 `danger_zone_approach`。
- [x] 5.5 将区域信息填充到候选事件的 `zone` 字段。

## 6. 目标行为检测

- [x] 6.1 实现 `services/behavior_service.py`，封装 YOLO/Ultralytics 目标检测调用。
- [x] 6.2 实现使用手机检测 `phone_usage`，结合 person 与 phone 的空间关系、置信度和持续时间。
- [x] 6.3 实现长时间低头检测 `head_down`，初版可基于头部/人体框比例或姿态结果的规则判断。
- [x] 6.4 实现异常人流聚集检测，基于同一画面局部区域人员数量、距离或密度阈值判断。
- [x] 6.5 将行为检测结果转换为统一候选事件结构。

## 7. 事件管理与告警入库

- [x] 7.1 实现 `services/event_service.py`，维护内存候选事件列表，支持按 `stream_id`、`event_type`、`level`、`since` 和 `limit` 查询。
- [x] 7.2 实现 `GET /analysis/events`，返回统一 JSON 格式的候选事件。
- [x] 7.3 实现事件去重、持续时间累计、置信度阈值和冷却窗口。
- [x] 7.4 实现截图保存到 `static/snapshots/`，失败时返回或记录 `50004`。
- [x] 7.5 实现 `services/alert_client.py`，将确认事件映射并推送到 SpringBoot `/alerts/ai`。
- [x] 7.6 入库成功后将候选事件标记为 `event_status=confirmed`，失败时保留错误日志和重试线索。

## 8. 验证与联调

- [x] 8.1 添加 `tests/test_geometry.py`，验证点在 polygon 内、点到边缘距离、归一化坐标转换。
- [x] 8.2 添加 `tests/test_response.py`，验证统一 JSON 返回格式、错误码、时间戳和 `trace_id`。
- [x] 8.3 添加 `tests/test_event_service.py`，验证候选事件过滤、去重、持续时间累计、冷却窗口和 confirmed 状态。
- [x] 8.4 添加 `tests/test_config_client.py`，使用 mock SpringBoot 响应验证视频源、区域、规则和人脸特征缓存刷新。
- [x] 8.5 添加 `tests/test_alert_client.py`，使用 mock SpringBoot `/alerts/ai` 验证正式告警入库字段映射和失败处理。
- [x] 8.6 添加 `tests/test_routes.py`，验证 `/model/status`、`/analysis/events`、`/face/feature/extract` 的正常和异常响应。
- [x] 8.7 使用 mock 区域和人员框验证危险区域进入、停留、接近检测。
- [x] 8.8 使用 mock YOLO 结果验证手机、低头、聚集事件生成，不依赖真实模型准确率。
- [x] 8.9 使用前端或浏览器验证 `/video_feed/{stream_id}` MJPEG 输出和断流重连表现。
- [x] 8.10 确认明火检测、活体检测、摔倒检测、音频检测、钉钉通知和日报功能未被纳入本次实现。
