# 防欺骗认证 + 异常声学检测模块

## 动机

智慧教室场景中，仅依靠人脸识别无法区分真实人员与静态照片、视频回放或AI换脸攻击。同时，教室内可能发生尖叫、玻璃破碎、爆炸等异常声学事件需要实时告警。

## 范围

### 反欺骗认证
- 眨眼检测：基于眼部关键点计算EAR（Eye Aspect Ratio），检测自然眨眼模式
- 纹理分析：人脸区域拉普拉斯方差分析，AI换脸图像边缘更平滑
- 输出两种事件：`spoof_detected`（未眨眼攻击）、`deepfake_detected`（纹理异常）

### 异常声学检测
- 能量基线建立：前50帧建立环境噪声基线
- 能量比异常：当前帧RMS能量超过基线3倍触发
- 频域匹配：FFT能量谱分析，匹配尖叫/玻璃破碎/枪声频段
- 输出事件：`abnormal_sound`（含sound_type子分类）

## 影响

- 新增：`services/anti_spoof_service.py`、`services/audio_service.py`
- 新增测试：`tests/test_anti_spoof_service.py`（9用例）、`tests/test_audio_service.py`（7用例）
- 修改：`analysis_service.py`、`app.py`、`model.yaml`、`event_service.py`
