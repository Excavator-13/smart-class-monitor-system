# Design

## Goals / Non-Goals

Goals:

- 确保配置为 CUDA 时，InsightFace 和两个 YOLO 模型均在 GPU 上执行。
- 启动日志清晰显示模型名称、权重、provider 和设备。
- 只为危险区域进入事件生成截图。
- 减少前端视频流上的行为检测框，并保持手机/低头为整帧检测。

Non-Goals:

- 不修改视频源解码、抽帧频率或模型精度参数。
- 不修改告警 API、数据库表或危险区域判断算法。
- 不将手机或低头检测绑定到任何区域。

## Decisions

- `model.yaml` 使用 `device: cuda`，避免 `auto` 在各框架间含义不一致。
- InsightFace 根据设备构造 `CUDAExecutionProvider`，并记录实际 session providers；CUDA 加载失败时保留明确错误日志，不静默伪装成 GPU 成功。
- Ultralytics 行为模型在 `predict()` 传入 `device`；明火模型加载后调用 `to(device)`，推理时同样传入设备。
- 截图白名单仅包含 `danger_zone_intrusion`，判断放在事件确认分支内，其他告警照常推送。
- `_draw_objects` 仅允许 person/student 类；`_draw_detections` 仅允许 `face_recognized`，行为计算本身不读取 zones。

## Risks / Trade-offs

- CUDA 或 `onnxruntime-gpu` 不可用时模型加载会失败或由底层回退；启动日志必须暴露实际 provider，便于部署诊断。
- 强制 CUDA 后，纯 CPU 机器需显式把 `device` 改回 `cpu`。
- 不绘制手机/低头框会减少画面定位信息，但能满足简洁展示要求，事件数据仍保留目标信息。
