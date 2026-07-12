# AI 服务端多推理后端支持（CUDA / Apple Silicon）

## 动机

当前 AI 服务端（`backend_ai`）的依赖和代码硬绑定了 NVIDIA CUDA：

- `requirements.txt` 指定 `--extra-index-url https://download.pytorch.org/whl/cu128`，锁死 `torch==2.11.0+cu128`、`torchvision==0.26.0+cu128`、`onnxruntime-gpu==1.23.2`
- `face_service.py` 中 InsightFace 初始化硬编码 `CUDAExecutionProvider` 和 `ctx_id=0`
- `behavior_service.py` 中 YOLO 推理未显式指定设备，依赖 Ultralytics 自动检测，但 CUDA 版 PyTorch 在 Mac 上无法安装

这导致在 MacBook（Apple Silicon）上完全无法运行 AI 服务，开发者在没有 NVIDIA GPU 的环境下无法进行本地联调。需要让两种推理后端并存，按运行环境自动选择或手动切换。

## 范围

- 新增 `requirements-mac.txt`，提供 Apple Silicon 兼容的依赖声明（`onnxruntime` + 标准 `torch`/`torchvision`）
- 修改 `face_service.py`，InsightFace 的 ONNX Provider 和 `ctx_id` 根据平台自动适配（macOS arm64 → CoreML/CPU，其他 → CUDA/CPU）
- 修改 `behavior_service.py`，YOLO 模型加载时根据平台自动选择设备（`cuda` → `mps` → `cpu`）
- 在 `model.yaml` 中新增可选的 `device` 配置项，允许手动覆盖自动检测结果
- 更新 `app.py` 中模型加载逻辑，将 `device` 配置传递给各 Service

## 不涉及

- 不修改现有 CUDA 依赖声明（`requirements.txt` 保持不变，NVIDIA 环境继续使用）
- 不引入 Docker 或远程推理方案
- 不改变任何 API 接口和业务逻辑
- 不修改 `backend_system`、`frontend` 或其他模块
