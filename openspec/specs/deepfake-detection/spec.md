# 换脸检测模块规范 (DeepfakeDetector)

> 对应代码：`backend_ai/services/deepfake_detector.py`

## 功能

使用 Meso4 CNN + 拉普拉斯纹理分析判断人脸是否为 AI 生成/深度伪造。

## 模型架构

| 层 | 参数 |
|----|------|
| 类型 | Meso4 (MesoNet 论文) |
| 输入 | 256×256×3 |
| 输出 | 1 (0=REAL, 1=FAKE) |
| 大小 | ~120KB (.pth) |
| 训练数据 | DFDC / FaceForensics++ 或自训练 |

## 配置

```yaml
anti_spoof:
  deepfake_weights: models/mesonet/meso4_weights.pth
```

## 训练

```bash
# 将真人照片命名为 real_*.jpg，AI脸命名为 ai_*.png
# 放入 face/ 目录，运行:
python train_mesonet.py
```

## API

```python
detector = DeepfakeDetector('weights.pth')
result = detector.predict(face_roi)  # face_roi: BGR numpy array
# result = {"is_fake": bool, "confidence": float, "method": "cnn"}
```
