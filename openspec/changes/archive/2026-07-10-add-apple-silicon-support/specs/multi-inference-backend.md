## Requirement: 多推理后端支持

系统必须在 NVIDIA CUDA 和 Apple Silicon 两种硬件环境下均可运行 AI 服务端，自动检测平台并选择对应的推理后端，同时支持通过配置手动覆盖自动检测结果。
原 `requirements.txt`（CUDA）保持不变，新增 `requirements-mac.txt` 供 Apple Silicon 环境使用。

### Scenario: macOS arm64 自动使用 CoreML/CPU 推理 InsightFace

- GIVEN 运行环境为 macOS arm64
- AND `model.yaml` 中未配置 `device` 字段
- WHEN `FaceService.load_model()` 初始化 InsightFace
- THEN providers 为 `["CoreMLExecutionProvider", "CPUExecutionProvider"]`
- AND `ctx_id` 为 -1

### Scenario: Linux x86_64 自动使用 CUDA 推理 InsightFace

- GIVEN 运行环境为 Linux x86_64 且 CUDA 可用
- AND `model.yaml` 中未配置 `device` 字段
- WHEN `FaceService.load_model()` 初始化 InsightFace
- THEN providers 为 `["CUDAExecutionProvider", "CPUExecutionProvider"]`
- AND `ctx_id` 为 0

### Scenario: macOS arm64 自动使用 MPS 推理 YOLO

- GIVEN 运行环境为 macOS arm64
- AND `model.yaml` 中未配置 `device` 字段
- WHEN `BehaviorService` 加载 YOLO 模型
- THEN 模型设备为 `"mps"`

### Scenario: Linux x86_64 自动使用 CUDA 推理 YOLO

- GIVEN 运行环境为 Linux x86_64 且 CUDA 可用
- AND `model.yaml` 中未配置 `device` 字段
- WHEN `BehaviorService` 加载 YOLO 模型
- THEN 模型设备为 `"cuda"`

### Scenario: 配置手动覆盖设备选择

- GIVEN `model.yaml` 中 `device` 字段为 `"cpu"`
- WHEN `FaceService.load_model()` 和 `BehaviorService` 初始化
- THEN InsightFace 使用 `["CPUExecutionProvider"]`，`ctx_id` 为 -1
- AND YOLO 模型设备为 `"cpu"`

### Scenario: Apple Silicon 环境使用 requirements-mac.txt 安装依赖

- GIVEN 运行环境为 macOS arm64
- WHEN 执行 `pip install -r requirements-mac.txt`
- THEN 安装 `onnxruntime`（非 gpu 版）、标准版 `torch`、标准版 `torchvision`
- AND 不依赖任何 CUDA 专有包

### Scenario: NVIDIA 环境使用原 requirements.txt 安装依赖

- GIVEN 运行环境为 Linux x86_64 且有 NVIDIA GPU
- WHEN 执行 `pip install -r requirements.txt`
- THEN 安装 `onnxruntime-gpu`、`torch+cu128`、`torchvision+cu128`
- AND 行为与改动前完全一致
