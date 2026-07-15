# 设计说明

## 目标

- 在 AI 服务启动阶段加载真实模型。
- 使用 InsightFace + ONNX Runtime GPU 完成人脸检测和特征提取。
- 使用 YOLOv8 完成人员和手机目标检测。
- 当模型不可用时，服务保持可启动，并通过 `/model/status` 明确暴露原因。
- 保持现有单元测试可通过 mock 服务注入运行。

## 模型设计

### 人脸识别模型

使用 InsightFace `buffalo_l` 模型包。

包含的关键 ONNX 模型：

- `det_10g.onnx`：人脸检测。
- `w600k_r50.onnx`：512 维人脸特征提取。

配置来源：

```yaml
models:
  face:
    enabled: true
    provider: insightface
    name: buffalo_l
    providers:
      - CUDAExecutionProvider
    ctx_id: 0
    det_size: [640, 640]
    feature_dim: 512
    similarity_threshold: 0.45
```

### 行为检测模型

使用 Ultralytics YOLOv8。

初版权重：

```text
backend_ai/models/yolo/yolov8n.pt
```

检测类别：

- `person`：用于危险区域检测的人体框。
- `cell phone`：用于使用手机检测。

配置来源：

```yaml
models:
  behavior:
    enabled: true
    provider: ultralytics
    name: yolov8n-coco
    weights: models/yolo/yolov8n.pt
    confidence_threshold: 0.6
```

## 关键决策

- YOLOv8 权重路径相对 `backend_ai/` 解析。
- YOLOv8 权重文件放在项目目录，便于部署和版本确认。
- InsightFace 模型沿用官方缓存机制，不强制放入项目 `models` 目录。
- Ultralytics 配置目录改为项目内：
  `backend_ai/config/ultralytics`
- 这样可以避免 Windows 下 `AppData/Roaming/Ultralytics/settings.json` 权限异常。
- `/model/status` 返回模型名称、权重路径、加载状态和失败原因。

## 降级策略

当 YOLOv8 权重不存在时：

- `behavior.loaded=false`
- `behavior.last_error` 返回具体缺失路径
- Flask 服务继续运行

当 InsightFace/CUDA 加载失败时：

- `face.loaded=false`
- `face.last_error` 返回异常信息
- 其他模块继续可用

## 验证方式

- 运行 AI 单元测试：

```powershell
pytest backend_ai\tests
```

- 使用 `classroom-ai-gpu` 检查模型状态：

```powershell
conda run --no-capture-output -n classroom-ai-gpu python -c "from backend_ai.app import create_app; app=create_app(); print(app.test_client().get('/model/status').get_json()['data']['models'])"
```
