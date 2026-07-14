# 区域类型精简 — 技术设计

## Context

### 已有基础设施

**区域数据模型**：`danger_zone` 表存储所有区域，`zone_type` 列当前允许 `danger / seat / phone_forbidden / roi` 四种值。Spring Boot `ZoneCreateRequest` 用 `@Pattern` 正则校验。前端 `zoneTypeOptions` 提供四种下拉选项。

**ZoneService（AI 端）**：`zone_service.py` 的 `detect()` 接收全部 zones，遍历每个 zone 做人员脚点-多边形判断，统一产出 `danger_zone_intrusion` / `danger_zone_stay` / `danger_zone_approach` 三种事件。**不区分 zone_type**，`phone_forbidden` 区域也会触发 `danger_zone_intrusion`。

**BehaviorService（AI 端）**：`behavior_service.py` 的 `detect_from_objects()` 检测手机时只看 person bbox 与 phone bbox 的 IoU-like 重叠，**不检查手机是否在禁用区坐标内**。无论画面中哪个位置出现手机，都产出 `phone_usage` 事件。

**AnalysisService（AI 端）**：`analysis_service.py` 的 `analyze_frame()` 将 `config_client.get_zones(stream_id)` 返回的全部 zones 传给 `zone_service.detect()`，不按类型分流。`_draw_zones()` 统一用红色 `(0, 0, 255)` 绘制所有区域。

**前端展示过滤**：`App.vue` 中 `confirmedForbiddenZones` 只筛选 `zone_type === "phone_forbidden"` 的区域，`phoneDetectionsInForbiddenZone` 做手机检测 bbox 与禁用区的矩形交集判断，`isPhoneItemInForbiddenZone()` 过滤掉不在禁用区内的手机告警。但这些过滤仅影响前端展示，后端已将所有 `phone_usage` 事件推送到数据库和钉钉。

**seat / roi**：后端 AI 无任何逻辑消费这两种类型。前端有选项但无对应功能。

## Goals / Non-Goals

**Goals:**

1. `ZoneService.detect()` 只对 `zone_type == "danger"` 的区域执行入侵检测，`phone_forbidden` 区域不再触发 `danger_zone_intrusion`
2. `BehaviorService.detect_from_objects()` 手机检测增加 `phone_forbidden_zones` 参数，手机 bbox 中心在禁用区多边形内才产出事件，事件携带 zone 信息
3. `AnalysisService.analyze_frame()` 按 zone_type 分流 zones，分别传给 zone_service 和 behavior_service
4. 前端和 Spring Boot 移除 seat / roi 选项，只保留 `danger` / `phone_forbidden`
5. AI 端区域绘制按 zone_type 区分颜色

**Non-Goals:**

- 不改数据库已有 seat / roi 数据（可手动清理）
- 不改 `danger_zone` 表名
- 不改 `config_client.get_zones()` 返回结构
- 不实现 seat 离座检测或 roi 裁剪检测
- 不移除前端 `isPhoneRelated()` / `isPhoneItemInForbiddenZone()` 展示过滤（作为冗余安全网保留）

## Decisions

| 决策                           | 选择                                                        | 理由                                                                                                                        |
| ------------------------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| zone_type 分流位置             | `AnalysisService.analyze_frame()`                           | 分流是一次性列表过滤，放在调用方比放在各 service 内部更清晰，service 保持职责单一                                           |
| 手机区域判断方式               | 手机 bbox 中心点 `point_in_polygon`                         | 复用已有 `geometry.point_in_polygon`，与人员入侵检测的脚点判断逻辑一致；中心点比 IoU 更简单且语义清晰（"手机出现在区域内"） |
| 无禁用区时手机检测行为         | 跳过手机检测                                                | 与前端"无禁用区则手机规则禁用"的逻辑一致，避免产出无区域关联的手机告警                                                      |
| phone_usage 事件携带 zone 信息 | 是，复用 `zone_info` 结构                                   | 与 `danger_zone_intrusion` 事件格式一致，前端已有 zone 展示逻辑，无需额外适配                                               |
| 区域绘制颜色区分               | danger 红色 `(0,0,255)`，phone_forbidden 橙色 `(0,140,255)` | BGR 格式：红色不变，橙色视觉区分明显但不突兀                                                                                |
| 前端区域草稿默认类型           | `danger`                                                    | 与现有行为一致（`zoneForm.zone_type` 默认 `"danger"`）                                                                      |

## Architecture

### 数据流变更

```
analyze_frame(stream_id, frame)
      │
      │ config_client.get_zones(stream_id)
      │ → [zone_danger_1, zone_danger_2, zone_phone_1, zone_phone_2, ...]
      │
      ├── 按 zone_type 分流
      │     danger_zones = [z for z in zones if z.zone_type == "danger"]
      │     phone_forbidden_zones = [z for z in zones if z.zone_type == "phone_forbidden"]
      │
      ├── zone 模块
      │     zone_service.detect(stream_id, persons, danger_zones, rule)
      │     → danger_zone_intrusion / stay / approach
      │     ✅ phone_forbidden 区域不再触发入侵事件
      │
      ├── behavior 模块
      │     behavior_service.detect_from_objects(
      │         stream_id, objects, rules,
      │         phone_forbidden_zones=phone_forbidden_zones   ← 新增参数
      │     )
      │     → phone_usage（仅手机中心在禁用区内）
      │     → head_down / crowd_gathering / fall_detected（不受影响）
      │
      └── 绘制
            _draw_zones(frame, zones)  ← 按 zone_type 区分颜色
```

### ZoneService 变更

```python
class ZoneService:
    def detect(self, stream_id, persons, zones, rule=None):
        # 新增：过滤只处理 danger 类型区域
        danger_zones = [z for z in zones if z.get("zone_type") == "danger"]
        detections = []
        # ... 后续逻辑不变，但遍历 danger_zones 而非 zones
        for person in persons:
            for zone in danger_zones:
                # 入侵/停留/接近检测逻辑不变
                ...
        return detections
```

变更量：在 `detect()` 方法入口加一行列表过滤，将 `for zone in zones` 改为 `for zone in danger_zones`。

### BehaviorService 变更

```python
class BehaviorService:
    def detect_from_objects(
        self, stream_id, objects, rules,
        phone_forbidden_zones=None,          # 新增参数
    ):
        persons = [obj for obj in objects if obj.get("class_name") in {"person", "student"}]
        phones = [obj for obj in objects if obj.get("class_name") in {"phone", "cell phone", "mobile_phone"}]
        detections = []

        # ── 手机检测：加入区域判断 ──
        phone_rule = rules.get("phone_usage", {})
        if phones and phone_forbidden_zones:          # 无禁用区则跳过
            phone_threshold = float(phone_rule.get("confidence_threshold", 0.6))
            for idx, person in enumerate(persons):
                for phone in phones:
                    if phone.get("confidence", 0) < phone_threshold:
                        continue
                    if not _iou_like_relation(person["bbox"], phone["bbox"]):
                        continue
                    # 新增：手机 bbox 中心必须在禁用区内
                    phone_center = _bbox_center(phone["bbox"])
                    matched_zone = _find_matching_zone(phone_center, phone_forbidden_zones)
                    if matched_zone is None:
                        continue
                    detections.append({
                        "event_type": "phone_usage",
                        "confidence": min(1.0, float(phone.get("confidence", 0))),
                        "level": "warning",
                        "target": {"track_id": person.get("track_id", ...), "bbox": person["bbox"]},
                        "zone": {                          # 新增：携带 zone 信息
                            "zone_id": matched_zone.get("zone_id"),
                            "zone_name": matched_zone.get("zone_name"),
                            "zone_type": matched_zone.get("zone_type"),
                        },
                        "track_key": f"{person.get('track_id', ...)}:{matched_zone.get('zone_id')}:phone",
                        "threshold_seconds": float(phone_rule.get("threshold_seconds", 3)),
                        "cooldown_seconds": float(phone_rule.get("cooldown_seconds", 45)),
                    })

        # ── head_down / crowd / fall：不变 ──
        ...
        return detections


def _find_matching_zone(point, zones):
    """检查点是否落在某个禁用区多边形内，返回匹配的 zone 或 None"""
    from backend_ai.utils.geometry import parse_polygon_coordinates, point_in_polygon
    for zone in zones:
        polygon = parse_polygon_coordinates(zone.get("coordinates") or [])
        if len(polygon) < 3:
            continue
        if point_in_polygon(point, polygon):
            return zone
    return None
```

关键设计点：

1. **`phone_forbidden_zones` 参数默认 `None`**——向后兼容，现有调用方不传参时手机检测行为不变（但 AnalysisService 会传参，所以实际会走新逻辑）
2. **`if phones and phone_forbidden_zones`**——无禁用区时跳过整个手机检测循环，零开销
3. **`_find_matching_zone`**——复用 `geometry.point_in_polygon`，手机中心点落入哪个禁用区就匹配哪个
4. **`track_key` 包含 zone_id**——不同禁用区的手机事件独立去重/冷却
5. **`zone` 字段**——与 `danger_zone_intrusion` 事件格式一致，前端/告警端无需额外适配

### AnalysisService 变更

```python
def analyze_frame(self, stream_id, frame, modules=None, objects=None, audio_chunk=None):
    enabled = modules or {"face", "zone", "behavior"}
    detected = []

    # ... face 模块不变 ...

    # object_list 获取逻辑不变
    object_list = ...
    if self.behavior_service.loaded:
        self._draw_objects(frame, object_list)

    # ── 按 zone_type 分流 ──
    zones = self.config_client.get_zones(stream_id) if "zone" in enabled else []
    danger_zones = [z for z in zones if z.get("zone_type") == "danger"]
    phone_forbidden_zones = [z for z in zones if z.get("zone_type") == "phone_forbidden"]

    if "behavior" in enabled:
        rules = {k: v for k, v in self.config_client.cache.rules.items()}
        behavior_detections = self.behavior_service.detect_from_objects(
            stream_id, object_list, rules,
            phone_forbidden_zones=phone_forbidden_zones,   # 传入禁用区
        )
        detected.extend(behavior_detections)
        self._draw_detections(frame, behavior_detections, color=(0, 255, 255))

    if "zone" in enabled:
        started = time.perf_counter()
        self._draw_zones(frame, zones)
        if not zones:
            self._draw_status(frame, "Danger zone not configured", color=(0, 220, 255))
        persons = [obj for obj in object_list if obj.get("class_name") in {"person", "student"}]
        zone_detections = self.zone_service.detect(
            stream_id, persons, danger_zones,               # 只传 danger 类型
            self.config_client.get_rule("danger_zone"),
        )
        detected.extend(zone_detections)
        self._draw_detections(frame, zone_detections, color=(0, 0, 255))
        self._observe_latency("zone", started)

    # ... fire / audio / events 不变 ...
```

变更点：

1. zones 获取提前到 behavior 模块之前（原来只在 zone 模块内获取）
2. 按 `zone_type` 分流为 `danger_zones` 和 `phone_forbidden_zones`
3. `behavior_service.detect_from_objects()` 传入 `phone_forbidden_zones`
4. `zone_service.detect()` 传入 `danger_zones` 而非全部 zones

### \_draw_zones 颜色区分

```python
ZONE_COLORS = {
    "danger": (0, 0, 255),           # 红色（BGR，不变）
    "phone_forbidden": (0, 140, 255), # 橙色（BGR）
}

def _draw_zones(self, frame, zones):
    height, width = frame.shape[:2]
    for zone in zones:
        polygon = parse_polygon_coordinates(zone.get("coordinates") or [])
        if len(polygon) < 3:
            continue
        points = [...]
        pts = np.asarray(points, dtype=np.int32)
        zone_type = zone.get("zone_type", "danger")
        color = self.ZONE_COLORS.get(zone_type, (0, 0, 255))
        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
        label = str(zone.get("zone_name") or zone.get("zone_type") or "zone")
        x0, y0 = points[0]
        draw_text(frame, label, (x0, max(18, y0 - 8)), font_scale=0.55, color=color, thickness=2)
```

### 前端变更

**zoneTypeOptions**：

```javascript
// 之前
const zoneTypeOptions = [
  { label: "危险区", value: "danger" },
  { label: "座位区", value: "seat" },
  { label: "手机禁用区", value: "phone_forbidden" },
  { label: "识别区域", value: "roi" },
];

// 之后
const zoneTypeOptions = [
  { label: "危险区", value: "danger" },
  { label: "手机禁用区", value: "phone_forbidden" },
];
```

**zoneTypeText**：

```javascript
// 移除 seat / roi 映射
function zoneTypeText(type) {
  return (
    {
      danger: "危险区",
      phone_forbidden: "手机禁用区",
    }[type] ||
    type ||
    "未分类"
  );
}
```

**区域编辑弹窗**：移除 seat / roi 的 `<el-option>`。

**其他前端逻辑不变**：`confirmedForbiddenZones`、`isPhoneRelated()`、`isPhoneItemInForbiddenZone()`、`phoneDetectionsInForbiddenZone` 等逻辑已正确只关注 `phone_forbidden`，无需修改。

### Spring Boot 变更

**ZoneCreateRequest.java**：

```java
// 之前
@Pattern(regexp = "^(danger|seat|phone_forbidden|roi)$", message = "区域类型必须为 danger、seat、phone_forbidden 或 roi")

// 之后
@Pattern(regexp = "^(danger|phone_forbidden)$", message = "区域类型必须为 danger 或 phone_forbidden")
```

**ZoneUpdateRequest.java**：如有同款校验同步修改。

**DataInitializer.java**：`seedZones()` 中已有 `danger` 和 `phone_forbidden` 两种区域，无需改动（seat / roi 从未被种子数据使用）。

**schema.sql**：`zone_type` 列注释更新为 `danger / phone_forbidden`。

## Risks / Trade-offs

| 风险                                | 影响                                                                          | 缓解                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **已有 seat / roi 数据**            | 数据库中可能存在 zone_type 为 seat / roi 的记录，AI 端分流时会忽略它们        | 可接受——这些区域本来就不生效；用户可在前端手动删除；如需批量清理可执行 SQL      |
| **手机检测精度依赖区域绘制**        | 用户必须准确绘制 phone_forbidden 区域，否则手机检测可能漏报                   | 前端绘制交互已成熟；区域可随时调整；这是设计意图而非风险                        |
| **手机 bbox 中心点判断**            | 手机 bbox 较大时，中心点可能在区域外但部分 bbox 在区域内                      | 中心点判断比 IoU 更保守（少报优于多报）；如需放宽可改为 bbox 四角任一点在区域内 |
| **无禁用区时手机检测完全跳过**      | 如果用户删除了所有 phone_forbidden 区域，手机检测立即停止                     | 与前端"无禁用区则手机规则禁用"逻辑一致；用户重新绘制区域后自动恢复              |
| **phone_usage 事件 track_key 变更** | 原来 track_key 是 `person_track_id`，现在变为 `person_track_id:zone_id:phone` | 冷却/去重 key 变化，旧状态自然过期（300s），不影响新事件产出                    |
