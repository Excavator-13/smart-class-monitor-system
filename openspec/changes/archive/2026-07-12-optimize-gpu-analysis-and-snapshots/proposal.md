# AI GPU 推理、模型日志与告警展示优化

## Why

当前 `device: auto` 未被正确解析为 CUDA，InsightFace 和 YOLO 实际使用 CPU，导致视频流卡顿；启动日志缺少人脸与行为模型的加载设备信息；所有确认事件都会保存截图，产生大量无意义文件；行为检测画框过多，且使用手机、低头应明确为整帧规则而非危险区域规则。

## What Changes

- 将 Windows/NVIDIA 环境的模型设备显式配置为 CUDA，并让 InsightFace、行为 YOLO、明火 YOLO 推理使用同一设备配置。
- 启动时打印 InsightFace `buffalo_l` 模型、ONNX Runtime provider、YOLOv8 权重和设备信息，并打印加载失败原因。
- 仅 `danger_zone_intrusion` 确认事件保存并推送截图；其他事件仍可入库，但 `snapshot_path` 为空。
- 视频画面仅绘制 `person/student` 目标框和 `face_recognized` 已识别人脸框；隐藏陌生人、手机、低头、区域及其他事件框。使用手机与低头仍继续对整帧检测结果生效，不依赖危险区域。
- 增加针对设备传递、截图策略和绘制过滤的回归测试。

## Capabilities

- 修改 AI 模型运行时设备选择与可观测性。
- 修改告警截图生成策略。
- 修改视频分析画框策略与行为规则作用域。

## Impact

影响 `backend_ai` 的模型配置、应用装配、InsightFace、YOLO 行为/明火推理、分析编排和相关测试。不改变前后端 API 契约和数据库结构。
