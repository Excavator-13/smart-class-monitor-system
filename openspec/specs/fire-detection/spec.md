# 明火检测模块规范（正式版）

> 对应代码：`backend_ai/services/fire_service.py` 及相关配置

---

## 1. 功能目标

从实时视频帧中检测明火（火焰），生成标准化事件并接入现有告警系统。

## 2. 模块规格

| 属性 | 值 |
|------|------|
| 模块名 | `fire` |
| 模型 | YOLOv8 (`yolo_fire.pt`) |
| 输入 | `numpy.ndarray` (BGR, 任意尺寸) |
| 输出 | `list[dict]` 检测事件列表 |
| 默认启用 | 是（`modules=all` 包含） |
| 降级策略 | 模型加载失败时 `loaded=false`，不影响其他模块 |

## 3. 配置参数

`backend_ai/config/model.yaml`：

```yaml
fire:
  enabled: true
  provider: ultralytics
  weights: models/yolo/yolo_fire.pt
  confidence_threshold: 0.25
  max_detections: 20
  min_bbox_area: 1000
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | bool | true | 是否启用火焰检测 |
| provider | string | ultralytics | 模型框架 |
| weights | string | models/yolo/yolo_fire.pt | 模型权重路径 |
| confidence_threshold | float | 0.25 | 最低置信度，低于此值过滤 |
| max_detections | int | 20 | 单帧最大检测数 |
| min_bbox_area | int | 1000 | 最小火焰框面积（像素） |

## 4. 事件输出

每个检测结果生成如下事件结构：

```json
{
  "event_type": "flame_detected",
  "event_name": "明火检测",
  "confidence": 0.4090,
  "level": "warning",
  "target": {
    "track_id": "fire_0",
    "bbox": [100.0, 120.0, 300.0, 400.0]
  },
  "track_key": "fire_0",
  "threshold_seconds": 0,
  "cooldown_seconds": 10
}
```

## 5. 告警分级规则

| 置信度范围 | 告警等级 |
|-----------|----------|
| >= 0.8 | `high`（严重） |
| 0.6 ~ 0.8 | `warning`（警告） |
| < 0.6 | `info`（提示） |

## 6. 接口规范

### 6.1 GET /model/status

返回 models 数组包含 fire 项：

```json
{"module": "fire", "loaded": true, "model_name": "ultralytics", "version": "v1", "avg_infer_ms": null}
```

### 6.2 GET /video_feed/<stream_id>

`modules` 参数：
- `all`（默认）：启用全部模块（含 fire）
- `fire`：仅启用火焰检测（可与其他模块组合）
- `face,zone,behavior`：不启用火焰检测，向后兼容

## 7. 检测流程

```
视频帧 → YOLO 推理 → 置信度过滤 → 面积过滤 → 分级 → 排序取 top-N → 生成事件 → 事件引擎冷却/确认 → 告警入库
```

## 8. 测试覆盖

9 个 pytest 用例全部通过：

| 用例 | 验证内容 |
|------|----------|
| test_fire_service_loaded | 有模型时 loaded=true |
| test_fire_service_not_loaded | 无模型时 loaded=false |
| test_detect_returns_empty_when_no_model | 无模型返回空列表 |
| test_detect_finds_flame | 超阈值检测生成 flame_detected |
| test_detect_filters_low_confidence | 低置信度过滤 |
| test_detect_filters_small_area | 小面积过滤 |
| test_classify_level | 告警分级规则 |
| test_detect_sorted_by_confidence | 按置信度降序排列 |
| test_status | 状态信息完整 |

总测试数：32/32 通过（含现有 23 个 + 新增 9 个）。

## 9. 相关文件

| 文件 | 说明 |
|------|------|
| `services/fire_service.py` | 核心检测逻辑 |
| `services/analysis_service.py` | 模块调度集成 |
| `services/event_service.py` | 事件枚举 |
| `app.py` | 服务注册与路由 |
| `config/model.yaml` | 模型配置 |
| `tests/test_fire_service.py` | 单元测试 |
| `models/yolo/yolo_fire.pt` | 模型权重（运行时） |
