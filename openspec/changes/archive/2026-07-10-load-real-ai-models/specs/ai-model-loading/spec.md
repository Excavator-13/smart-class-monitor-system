## 新增需求

### 需求：加载真实 YOLOv8 行为检测模型

AI 服务在行为检测模块启用时，必须根据 `backend_ai/config/model.yaml` 加载 Ultralytics YOLOv8 模型。

AI 服务必须使用项目内 Ultralytics 配置目录，避免依赖 Windows 用户目录写权限。

#### 场景：加载 YOLOv8 权重用于人员和手机检测

- 假设 `models.behavior.enabled=true`
- 并且 `models.behavior.weights=models/yolo/yolov8n.pt`
- 并且 `backend_ai/models/yolo/yolov8n.pt` 文件存在
- 当 Flask AI 服务启动
- 那么服务应加载 Ultralytics YOLO 模型
- 并且 `/model/status` 中行为检测模型状态为 `loaded=true`
- 并且该模型可输出 COCO 类别 `person` 和 `cell phone`

#### 场景：YOLOv8 权重文件缺失

- 假设 `models.behavior.enabled=true`
- 并且配置的 YOLOv8 权重文件不存在
- 当 Flask AI 服务启动
- 那么服务仍应保持运行
- 并且 `/model/status` 中行为检测模型状态为 `loaded=false`
- 并且 `last_error` 说明权重文件缺失

#### 场景：默认 Ultralytics 用户配置目录不可写

- 假设默认 Ultralytics 用户配置目录不可写
- 当 Flask AI 服务加载行为检测模型
- 那么服务应使用 `backend_ai/config/ultralytics`
- 并且不应因为 `AppData/Roaming/Ultralytics/settings.json` 权限问题导致模型加载失败

### 需求：基于 YOLOv8 目标检测生成手机使用事件

AI 服务必须使用 YOLOv8 的 `person` 和 `cell phone` 检测结果生成 `phone_usage` 候选事件。

#### 场景：人员框关联手机框

- 假设 YOLOv8 检测到 `person`
- 并且 YOLOv8 检测到 `cell phone`
- 并且手机置信度达到 `phone_usage` 规则阈值
- 并且手机中心点位于人员框内
- 当 AI 服务分析当前视频帧
- 那么服务应为该人员生成 `phone_usage` 候选事件

### 需求：基于 YOLOv8 人员框执行危险区域检测

AI 服务必须将 YOLOv8 的 `person` 检测结果作为危险区域规则检测输入。

#### 场景：人员进入危险区域

- 假设 SpringBoot 已为视频源配置 polygon 危险区域
- 并且 YOLOv8 检测到 `person`
- 并且该人员脚点位于危险区域 polygon 内
- 当 AI 服务分析当前视频帧
- 那么服务应生成 `danger_zone_intrusion`
- 并且继续按停留阈值评估 `danger_zone_stay`

### 需求：加载 GPU InsightFace 人脸模型

AI 服务在人脸模块启用时，必须使用 ONNX Runtime `CUDAExecutionProvider` 加载 InsightFace。

#### 场景：InsightFace 使用 CUDA Provider

- 假设 `models.face.enabled=true`
- 并且 `models.face.providers` 包含 `CUDAExecutionProvider`
- 当 Flask AI 服务启动
- 那么服务应使用配置的 provider 初始化 InsightFace
- 并且 `/model/status` 应返回 provider 配置和加载结果
