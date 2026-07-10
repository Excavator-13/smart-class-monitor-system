# AI 服务端核心分析能力设计

## Goals

- 建立可运行的 Flask AI 服务端骨架，统一封装视频流、模型状态、事件查询、人脸特征提取和配置刷新接口。
- 从 Nginx RTMP 拉取课堂视频流，输出可由前端 `<img>` 直接展示的 MJPEG 标注视频。
- 使用 InsightFace/ArcFace 作为人脸特征提取方案，统一输出 512 维特征向量。
- 使用 YOLO/Ultralytics 和规则判断实现危险区域、长时间低头、异常人流聚集和使用手机检测。
- 将 AI 候选事件和 SpringBoot 正式告警分层处理，降低误报和重复入库风险。
- 通过 SpringBoot 统一管理视频源、区域、规则、人脸特征和正式告警数据。

## Non-Goals

- 不实现明火检测，保留接口枚举和模块扩展位置即可。
- 不实现活体检测、防欺骗认证、摔倒检测、异常声学检测。
- 不实现人员轨迹持久化、轨迹查询接口和轨迹前端展示。
- 不实现钉钉通知和 AI 日报生成。
- 不由 AI 服务直接管理用户、学生、规则、区域和告警数据库。

## Architecture

```text
OBS/摄像头
    |
    v
Nginx RTMP
    |
    v
stream_manager.py
    |
    v
analysis_service.py
    |--------------------|
    v                    v
face_service.py      zone_service.py
    |                    |
    |                    v
    |               behavior_service.py
    |                    |
    |--------------------|
             |
             v
event_service.py
    |              |
    v              v
/analysis/events  alert_client.py -> SpringBoot /alerts/ai

/video_feed/{stream_id} <- annotated frame encoder
config_client.py <------ SpringBoot streams/zones/rules/face-features
```

## Proposed File Structure

```text
backend_ai/
  app.py
  config/
    app.yaml
    model.yaml
  services/
    stream_manager.py
    analysis_service.py
    face_service.py
    zone_service.py
    behavior_service.py
    event_service.py
    alert_client.py
    config_client.py
  utils/
    geometry.py
    image_utils.py
    response.py
    logger.py
  tests/
    test_geometry.py
    test_response.py
    test_event_service.py
    test_config_client.py
    test_alert_client.py
    test_routes.py
  static/
    snapshots/
  requirements.txt
```

## Key Decisions

- **接口路径不增加 `/ai` 前缀**：保持与现有接口文档一致，前端和 SpringBoot 直接调用 `/video_feed/{stream_id}`、`/analysis/events`、`/model/status` 等路径。
- **人脸特征统一为 512 维**：使用 InsightFace/ArcFace，替代旧文档中可能出现的 128 维描述。
- **候选事件与正式告警分层**：AI 服务先生成 `event_status=candidate` 的内存候选事件，满足持续时间、置信度和冷却规则后再调用 SpringBoot `/alerts/ai` 入库。
- **配置以 SpringBoot 为准**：视频源、危险区域、规则和人脸特征库由 SpringBoot 管理；AI 服务启动拉取、定时拉取，并支持 SpringBoot 主动触发刷新。
- **前端只直接消费实时画面和候选事件**：正式告警列表、告警详情、截图 URL 和处理状态仍由 SpringBoot 提供。
- **检测模块可开关**：`/video_feed/{stream_id}` 支持 `modules=face,zone,behavior` 控制启用模块，便于联调和性能排查。
- **明火检测只预留，不实现**：事件枚举可保留 `flame_detected`，但本次不加载模型、不生成明火事件。
- **测试优先覆盖稳定边界**：开发阶段使用 pytest 覆盖几何计算、统一响应、事件规则、字段映射、配置解析和 Flask 路由；真实 RTMP、真实模型效果、真实 SpringBoot 入库留到联调阶段验证。

## Runtime Baseline

- Conda env: `classroom-ai-gpu`
- Python: 3.10.20
- Flask: 3.1.3
- Werkzeug: 3.1.8
- ultralytics: 8.4.90
- opencv-python: 5.0.0.93
- insightface: 1.0.1
- onnxruntime-gpu: 1.23.2
- numpy: 2.2.6
- torch: 2.11.0+cu128
- torchvision: 0.26.0+cu128
- GPU: NVIDIA GeForce RTX 5060 Laptop GPU
- ONNX Runtime providers: TensorRT, CUDA, CPU

## Detection Flow

1. `stream_manager.py` 根据 `stream_id` 拉取 RTMP 地址，持续读取最新帧。
2. `analysis_service.py` 获取帧并调度检测模块。
3. `face_service.py` 检测人脸、提取 512 维特征，与缓存特征库比对，生成已识别或陌生人事件。
4. `zone_service.py` 使用人员脚点与 polygon 配置判断危险区域进入、停留和接近。
5. `behavior_service.py` 基于检测结果和规则判断长时间低头、异常聚集和使用手机。
6. `event_service.py` 聚合检测结果，执行持续时间、置信度、去重和冷却判断。
7. `alert_client.py` 将确认事件映射为 SpringBoot `/alerts/ai` 请求体并入库。
8. 标注后的帧经 MJPEG 响应返回前端。

## Testing Strategy

- 使用 pytest 作为开发阶段测试框架，测试文件集中放在 `backend_ai/tests/`。
- 优先测试纯函数和业务规则：
  - `utils/geometry.py`：点在 polygon 内、点到边缘距离、归一化坐标转换。
  - `utils/response.py`：统一 JSON 格式、错误码、时间戳和 `trace_id`。
  - `event_service.py`：候选事件过滤、去重、持续时间累计、冷却窗口和 confirmed 状态。
  - `alert_client.py`：候选事件到 SpringBoot `/alerts/ai` 请求体的字段映射。
  - `config_client.py`：SpringBoot 配置响应解析和缓存刷新。
  - Flask routes：`/model/status`、`/analysis/events`、`/face/feature/extract` 的正常和异常响应。
- 模型相关测试先验证接口结构和异常处理，不在开发阶段验证识别准确率。
- RTMP 拉流、真实 YOLO 推理、真实 InsightFace 准确率、真实 SpringBoot 入库和前端展示放到联调测试阶段。
- 测试不得重复实现业务逻辑，只通过 Given/When/Then 风格输入输出验证模块边界。

## Risks / Trade-offs

- **实时性能压力**：人脸识别、YOLO 和 MJPEG 编码同时运行可能导致 FPS 下降。初版需要支持模块开关和模型状态耗时统计。
- **误报与重复告警**：课堂动作存在短时抖动，必须使用持续时间、置信度和冷却窗口控制正式告警入库。
- **RTMP 拉流不稳定**：视频源离线或网络抖动时，应保留服务可用性，返回占位帧或明确错误状态。
- **配置一致性**：AI 服务缓存可能与 SpringBoot 数据短暂不一致，因此需要推模式刷新和拉模式兜底同步。
- **Ultralytics 配置目录权限**：运行时需确保 Ultralytics 配置目录可读写，否则导入或首次运行可能失败。
- **OpenCV 5 兼容性**：当前环境使用 OpenCV 5.0.0.93，若部署环境降级到 4.x，需要重新验证 RTMP 拉流和编码行为。
- **测试与实现耦合**：若测试复制实现细节，会形成维护冗余。测试应关注规则输入输出、接口契约和错误码，而不是重复内部算法步骤。

## Validation

- 使用 pytest 验证 `geometry`、`response`、`event_service`、`config_client`、`alert_client` 和 Flask routes。
- 使用 `/model/status` 验证服务、模型、视频源状态。
- 使用测试图片验证 `/face/feature/extract` 输出 512 维特征，并覆盖无人脸、多脸和非法图片错误。
- 使用模拟区域 polygon 和人员框验证危险区域进入、停留、接近判断。
- 使用 mock YOLO 结果验证手机、低头、聚集事件生成、去重和冷却。
- 使用 mock SpringBoot 接口验证 `/alerts/ai` 入库字段映射。
- 使用前端 `<img>` 或浏览器验证 `/video_feed/{stream_id}` MJPEG 可持续输出。
