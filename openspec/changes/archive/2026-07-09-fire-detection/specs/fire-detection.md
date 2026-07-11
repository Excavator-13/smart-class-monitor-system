# 明火检测模块规范

## Requirement: 明火检测

系统必须能够从视频帧中检测火焰（明火），并生成标准化事件。
系统不得因火焰检测模块加载失败而影响其他检测模块（face、zone、behavior）的正常运行。

### Scenario: 模型加载成功
- GIVEN `model.yaml` 中 `fire.enabled=true` 且 `yolo_fire.pt` 存在
- WHEN Flask 应用启动时初始化 FireService
- THEN `fire.loaded=true`，`/model/status` 接口返回 fire 模块状态为 loaded

### Scenario: 视频流中检测到火焰
- GIVEN 某视频流帧中存在可见火焰区域
- WHEN `modules=all` 或 `modules=fire` 时分析该帧
- THEN `analysis_service.analyze_frame()` 通过 `fire_service.detect()` 生成至少一个 `event_type="flame_detected"` 的检测项
- AND 每个检测项包含 `confidence`、`level`、`target.bbox` 和 `track_key`

### Scenario: 置信度过滤
- GIVEN 模型输出中某个火焰检测的置信度低于 `model.yaml` 配置的 `confidence_threshold`
- WHEN `fire_service.detect()` 执行过滤
- THEN 该低置信度检测结果不被包含在返回列表中

### Scenario: 小面积过滤
- GIVEN 模型输出中某个火焰检测的边界框面积小于 `min_bbox_area`（默认 1000 像素）
- WHEN `fire_service.detect()` 执行过滤
- THEN 该小面积检测结果不被包含在返回列表中

### Scenario: 告警分级
- GIVEN 某个火焰检测的置信度为 `conf`
- WHEN `FireService._classify_level(conf)` 被调用
- THEN
  - `conf >= 0.8` → 返回 `"high"`
  - `0.6 <= conf < 0.8` → 返回 `"warning"`
  - `conf < 0.6` → 返回 `"info"`

### Scenario: 模型加载失败优雅降级
- GIVEN `yolo_fire.pt` 文件不存在或格式损坏
- WHEN Flask 应用启动时尝试加载 FireService
- THEN 捕获异常，创建 `FireService(model=None)`
- AND 其他模块（face/zone/behavior）正常启动
- AND `/model/status` 中 fire 返回 `loaded=false`

### Scenario: 事件冷却与确认
- GIVEN 同一火焰区域（相同 `track_key`）在视频流中持续出现
- WHEN 首次检测满足 `threshold_seconds` 后，且距离上次确认超过 `cooldown_seconds`
- THEN `event_service.observe()` 将事件状态置为 `confirmed`
- AND `alert_client.push_alert()` 将事件推送到 SpringBoot `/alerts/ai`

## 配置规范

`model.yaml` 中 `fire` 段：

```yaml
fire:
  enabled: true
  provider: ultralytics
  weights: models/yolo/yolo_fire.pt
  confidence_threshold: 0.25
  max_detections: 20
  min_bbox_area: 1000
  cooldown_seconds: 10
```

- `enabled`: 是否启用火焰检测模块
- `provider`: 模型提供方，固定为 `ultralytics`
- `weights`: 模型权重文件路径，相对 `backend_ai/` 目录
- `confidence_threshold`: 最低置信度（0.0~1.0），低于此值的检测被过滤
- `max_detections`: 单帧最大检测数量，超过按置信度取 top-N
- `min_bbox_area`: 最小火焰框面积（像素），过滤噪点
- `cooldown_seconds`: 同一火焰区域的重复告警冷却时间（秒）

## 接口规范

### GET /model/status

返回 models 数组中包含 fire 项：
```json
{
  "module": "fire",
  "loaded": true,
  "model_name": "ultralytics",
  "version": "v1",
  "avg_infer_ms": null
}
```

### GET /video_feed/<stream_id>

`modules` 参数：
- `all`（默认）：启用 `face`、`zone`、`behavior`、`fire` 全部模块
- `face,zone,behavior`：不启用火焰检测，向后兼容
- `fire`：仅启用火焰检测（可与其他模块组合如 `face,fire`）

## 事件字段规范

`flame_detected` 事件通过 `event_service.observe()` 生成，字段与现有事件一致：

| 字段 | 类型 | 说明 |
|------|------|------|
| event_type | string | 固定为 `"flame_detected"` |
| event_name | string | 固定为 `"明火检测"` |
| confidence | float | 模型输出的置信度，保留 4 位小数 |
| level | string | `"high"` / `"warning"` / `"info"` |
| target.track_id | string | 如 `"fire_0"`、`"fire_1"` |
| target.bbox | list[float] | 火焰边界框 `[x1, y1, x2, y2]`，像素坐标 |
| track_key | string | 与 track_id 相同，用于冷却去重 |
| threshold_seconds | float | 来自规则配置，默认 0（立即确认） |
| cooldown_seconds | float | 来自规则配置，默认 10 |

## 依赖关系

```
fire_service.py
  ├── ultralytics.YOLO (推理引擎)
  ├── numpy.ndarray (输入帧)
  └── config/model.yaml (配置参数)

analysis_service.py
  ├── fire_service (检测逻辑)
  ├── event_service (事件管理)
  └── config_client (规则配置)
```
