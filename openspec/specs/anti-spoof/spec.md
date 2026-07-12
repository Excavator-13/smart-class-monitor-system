# 防欺骗认证模块规范

> 对应代码：`backend_ai/services/anti_spoof_service.py`

## 功能

检测并防御静态照片、视频回放、AI换脸等欺骗攻击。

## 检测机制

| 检测类型 | 方法 | 依赖 |
|---------|------|------|
| 静态照片/视频 | 眨眼检测（EAR < 0.18） + 持续观察 | 68点人脸关键点 |
| AI换脸 | 拉普拉斯纹理方差（< 0.35） | 人脸ROI |

## 配置 (`model.yaml`)

```yaml
anti_spoof:
  enabled: true
  provider: rule
  blink_threshold_seconds: 5.0
  texture_variance_threshold: 8.0
```

## 事件输出

```json
// 未眨眼攻击
{"event_type": "spoof_detected", "level": "high",
 "target": {"track_id": "...", "reason": "no_blink_for_8s"}}

// AI换脸攻击
{"event_type": "deepfake_detected", "level": "high",
 "target": {"texture_score": 0.12}}
```
