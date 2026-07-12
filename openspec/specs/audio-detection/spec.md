# 异常声学检测模块规范

> 对应代码：`backend_ai/services/audio_service.py`

## 功能

实时检测尖叫、玻璃破碎、枪声、爆炸声等异常声学事件。

## 检测机制

| 步骤 | 说明 |
|------|------|
| 基线建立 | 前50帧（~5s）建立环境噪声能量基线 |
| 能量检测 | 当前窗口RMS能量超过基线3倍触发 |
| 频域匹配 | FFT能量谱匹配5种声学事件频段 |

## 支持的声学事件

| 事件 | 频率范围 | 能量比阈值 |
|------|---------|-----------|
| scream | 500-4000 Hz | 3.0x |
| glass_break | 3000-8000 Hz | 2.5x |
| gunshot | 200-2000 Hz | 8.0x |
| explosion | 50-500 Hz | 10.0x |
| loud_crash | 100-2000 Hz | 4.0x |

## 配置 (`model.yaml`)

```yaml
audio:
  enabled: true
  provider: signal
  sample_rate: 16000
  window_ms: 1000
```

## 事件输出

```json
{"event_type": "abnormal_sound", "level": "high", "confidence": 0.85,
 "target": {"sound_type": "scream", "sound_label": "尖叫声", "energy_ratio": 4.2}}
```

## 注意事项

- 需要音频输入源（RTMP音频轨道或独立音频设备）
- 当前 `analyze_frame` 支持 `audio_chunk` 参数，无音频输入时优雅跳过
