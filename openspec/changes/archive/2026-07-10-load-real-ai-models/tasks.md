# 任务清单

- [x] 创建真实模型加载相关 OpenSpec 文档。
- [x] 新增 YOLO 权重目录占位文件。
- [x] 在启动时按 `model.yaml` 加载 InsightFace。
- [x] InsightFace 配置为 `CUDAExecutionProvider`。
- [x] 在启动时按 `model.yaml` 加载 Ultralytics YOLOv8。
- [x] 将初版 YOLOv8 模型配置为 `models/yolo/yolov8n.pt`。
- [x] 使用 YOLOv8 COCO 的 `person` 支撑危险区域检测。
- [x] 使用 YOLOv8 COCO 的 `cell phone` 支撑手机检测。
- [x] 将 Ultralytics 配置目录改到项目内，避免 AppData 权限问题。
- [x] 在 `/model/status` 中暴露模型加载状态和错误原因。
- [x] 下载并放置 `backend_ai/models/yolo/yolov8n.pt`。
- [x] 运行 AI 单元测试。
