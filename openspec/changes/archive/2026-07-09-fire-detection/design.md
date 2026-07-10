# 明火检测模块技术设计

## 架构

```text
RTMP 视频流 (Nginx)
    |
    v
stream_manager.get_frame(stream_id)
    |
    v
analysis_service.analyze_frame(stream_id, frame, modules={...})
    |-- face_service
    |-- zone_service
    |-- behavior_service
    +-- fire_service (新增)  <-- 独立分支，不依赖 persons/objects
         |                        直接对原始帧进行 YOLO 推理
         v
    event_service.observe(...)  <-- 复用现有的候选/确认/冷却机制
         |                        event_type = "flame_detected"
         v
    alert_client.push_alert(...) --> SpringBoot /alerts/ai
         |
         v
    /model/status 返回 fire.loaded 状态
```

## 关键设计决策

- **独立检测分支**：火焰检测不依赖 `persons` 或 `objects` 列表，直接在 `frame` 上运行 YOLO 推理。这是合理设计，因为火焰不需要关联人员。
- **复用事件引擎**：通过 `event_service.observe()` 实现冷却、持续时间和确认机制，与现有模块完全一致。
- **配置驱动**：`model.yaml` 中 `fire` 段控制 `enabled`、`weights` 路径、`confidence_threshold`（默认 0.25）、`max_detections`（默认 20）等参数。
- **模型加载失败降级**：`app.py` 中 `try/except` 包裹 YOLO 加载，失败时 `fire_service = FireService(model=None)`，不影响其他模块启动。
- **告警分级**：`info`（< 0.6）、`warning`（0.6-0.8）、`high`（>= 0.8），与项目现有三级体系一致。
- **面积过滤**：`min_bbox_area=1000` 过滤噪点（如蜡烛火焰、屏幕反光等）。
- **最大检测数**：`max_detections=20` 防止单帧过多框影响标注和事件性能。
- **Python 3.8 兼容**：`geometry.py` 中 `tuple[float, float]` 改为 `Tuple[float, float]`，避免 `TypeError: 'type' object is not subscriptable`。

## 文件结构

```
backend_ai/
  services/
    fire_service.py          ← FireService 类（核心检测逻辑）
  tests/
    test_fire_service.py     ← 9 个 pytest 用例（覆盖加载、检测、过滤、排序、分级）
  models/yolo/
    yolo_fire.pt             ← 模型权重（运行时放置，不提交到 Git）
```

## 接口变更

### `/model/status` (GET)

返回 `models` 数组中新增 fire 项：
```json
{"module": "fire", "loaded": true, "model_name": "ultralytics", "version": "v1", "avg_infer_ms": null}
```

### `/video_feed/<stream_id>` (GET)

`modules=all` 默认集合扩展为 `{"face", "zone", "behavior", "fire"}`。
`modules=face,zone` 时仍不启用火焰检测，保持向后兼容。

## 事件类型

新增 `flame_detected`，对应 `EVENT_NAMES` 中：
```python
"flame_detected": "明火检测"
```

## 测试策略

- 使用 `FakeFireModel` 模拟 YOLO 输出，验证 `detect()` 的过滤、排序和分级逻辑。
- 测试覆盖：
  1. 有模型时 loaded = True
  2. 无模型时 loaded = False
  3. 无模型时 detect 返回空列表
  4. 置信度超阈值时生成 `flame_detected` 事件
  5. 低置信度过滤
  6. 小面积过滤
  7. 告警分级规则
  8. 按置信度降序排序
  9. status() 返回正确信息
- 与现有测试集一起运行：共 32 个测试全部通过（含新增 9 个）。

## 验证

- 使用合成火焰图片（CV 绘制红橙黄色椭圆）验证模型能加载、能推理、不报错。
- 使用真实火焰图片验证检测数量和置信度。
- 使用 `/model/status` 验证 fire 模块状态正确。
- 使用 `pytest` 验证所有测试通过（32/32）。
