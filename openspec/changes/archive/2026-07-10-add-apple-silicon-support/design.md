## 技术方案

- 平台检测：使用 `platform.system()` 和 `platform.machine()` 判断运行环境，macOS arm64 走 Apple Silicon 路径，其余走 CUDA 路径
- InsightFace 适配：`face_service.py` 中 `load_model()` 根据 `platform` 自动选择 ONNX Provider 列表和 `ctx_id`；macOS arm64 使用 `["CoreMLExecutionProvider", "CPUExecutionProvider"]` + `ctx_id=-1`，其余使用 `["CUDAExecutionProvider", "CPUExecutionProvider"]` + `ctx_id=0`
- YOLO 适配：`behavior_service.py` 中模型加载时根据 `torch.cuda.is_available()` 和 `torch.backends.mps.is_available()` 自动选择设备，优先级 `cuda` > `mps` > `cpu`
- 配置覆盖：`model.yaml` 新增顶层 `device` 可选字段（值可为 `cuda`、`mps`、`cpu`），若设置则覆盖自动检测结果
- 依赖分离：保留原 `requirements.txt`（CUDA），新增 `requirements-mac.txt`（Apple Silicon），后者使用 `onnxruntime` + 标准 `torch`/`torchvision`
- 涉及文件：
  - `backend_ai/requirements-mac.txt`（新增）
  - `backend_ai/config/model.yaml`（新增 `device` 字段）
  - `backend_ai/services/face_service.py`（Provider 和 ctx_id 自动适配）
  - `backend_ai/services/behavior_service.py`（设备自动适配）
  - `backend_ai/app.py`（传递 device 配置到各 Service）
