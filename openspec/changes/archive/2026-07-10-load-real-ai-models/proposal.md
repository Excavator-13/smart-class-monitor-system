# 加载真实 AI 模型

## 背景

AI 服务此前已经具备 Flask 路由、视频流处理、区域规则和事件生成骨架，但启动时没有真正加载 YOLOv8 和 InsightFace 模型。

这会导致：

- 使用手机检测无法基于真实视频帧识别 `cell phone`。
- 危险区域检测缺少 YOLOv8 输出的 `person` 人员框。
- 人脸识别没有走 InsightFace GPU 推理链路。

## 变更内容

- 启动 Flask AI 服务时加载 InsightFace `buffalo_l`。
- InsightFace 使用 `CUDAExecutionProvider`，优先走 `onnxruntime-gpu`。
- 启动时加载 Ultralytics YOLOv8 模型。
- 初版使用 YOLOv8 COCO 模型 `yolov8n.pt`。
- 使用 YOLOv8 COCO 的 `person` 类别作为危险区域检测输入。
- 使用 YOLOv8 COCO 的 `cell phone` 类别作为使用手机检测输入。
- 当模型或权重文件缺失时，服务不崩溃，而是在 `/model/status` 中返回加载失败原因。
- 增加项目内 YOLO 权重目录结构。

## 影响范围

涉及文件：

- `backend_ai/app.py`
- `backend_ai/config/model.yaml`
- `backend_ai/services/face_service.py`
- `backend_ai/services/behavior_service.py`
- `backend_ai/models/yolo/`
- `backend_ai/config/ultralytics/`

接口路径不变：

- `GET /model/status`
- `GET /video_feed/{stream_id}`
- `GET /analysis/events`
- `POST /face/feature/extract`

## 运行要求

- YOLOv8 权重文件位于：
  `backend_ai/models/yolo/yolov8n.pt`
- InsightFace `buffalo_l` 模型由 InsightFace 缓存目录管理，通常位于：
  `C:\Users\20943\.insightface\models\buffalo_l`
- Conda 环境：
  `classroom-ai-gpu`
- ONNX Runtime 应能识别：
  `CUDAExecutionProvider`
