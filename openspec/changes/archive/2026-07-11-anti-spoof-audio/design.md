# 防欺骗 + 声学检测 + MesoNet CNN 技术设计

## Goals
- 增加活体检测层（眨眼检测 + 换脸检测），在 face_service 之后运行
- 增加异常声学事件检测，通过能量基线 + FFT 频域匹配
- 集成 Meso4 CNN 用于高精度换脸检测，支持自训练和官方权重

## Architecture

```
video_feed frame
  ├── face_service (InsightFace)
  │     ├── 512维特征 → 人脸识别
  │     └── 人脸框 → anti_spoof_service
  │           ├── EAR眨眼检测 → spoof_detected
  │           └── MesoNet CNN → deepfake_detected
  ├── zone_service (多边形规则)
  ├── behavior_service (YOLO + 规则)
  ├── fire_service (YOLO fire)
  └── audio_service (信号处理, 独立音频通道)
```

## Key Decisions
- 反欺骗纯规则驱动（EAR + 拉普拉斯），无需 GPU
- MesoNet CNN 可选启用（有权重文件时自动加载）
- 声学检测独立于视频管线，需音频输入源（RTMP音频或麦克风）
- 自训练模式优先于下载预训练权重（避免网络依赖）

## Detection Flow
1. face_service 输出人脸框和特征
2. anti_spoof_service 接收人脸ROI，计算 EAR 和 blink 状态
3. 若长时间未眨眼 → spoof_detected 事件
4. 若 MesoNet CNN 可用 → CNN 推理 → deepfake_detected 事件
5. audio_service 接收音频数据，维持能量基线
6. 能量突变 + 频域匹配 → abnormal_sound 事件
