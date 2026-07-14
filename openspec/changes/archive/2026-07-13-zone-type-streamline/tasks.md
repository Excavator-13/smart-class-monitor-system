## 1. ZoneService 按 zone_type 过滤

- [x] 1.1 `zone_service.py` 的 `detect()` 方法入口过滤 `zone_type == "danger"` 的区域，遍历 `danger_zones` 而非全部 zones
- [x] 1.2 验证：`phone_forbidden` 区域不再产出 `danger_zone_intrusion` / `danger_zone_stay` / `danger_zone_approach`

## 2. BehaviorService 手机检测加入区域判断

- [x] 2.1 `behavior_service.py` 的 `detect_from_objects()` 新增 `phone_forbidden_zones=None` 参数
- [x] 2.2 手机检测逻辑：`if phones and phone_forbidden_zones` 时才进入手机检测循环，否则跳过
- [x] 2.3 新增 `_find_matching_zone(point, zones)` 辅助函数，用 `geometry.point_in_polygon` 检查手机 bbox 中心是否在禁用区内
- [x] 2.4 新增 `_bbox_center(bbox)` 辅助函数，计算 bbox 中心点
- [x] 2.5 手机检测命中禁用区时，事件 dict 携带 `zone` 字段（`zone_id` / `zone_name` / `zone_type`）
- [x] 2.6 `track_key` 改为 `"{person_track_id}:{zone_id}:phone"`，按区域独立去重
- [x] 2.7 验证：手机 bbox 中心在禁用区内 → 产出 `phone_usage`；在禁用区外 → 不产出

## 3. AnalysisService 分流 zones

- [x] 3.1 `analysis_service.py` 的 `analyze_frame()` 中 zones 获取提前到 behavior 模块之前
- [x] 3.2 按 `zone_type` 分流为 `danger_zones` 和 `phone_forbidden_zones`
- [x] 3.3 `behavior_service.detect_from_objects()` 传入 `phone_forbidden_zones`
- [x] 3.4 `zone_service.detect()` 传入 `danger_zones` 而非全部 zones
- [x] 3.5 验证：danger 区域只触发入侵检测，phone_forbidden 区域只触发手机检测

## 4. 区域绘制颜色区分

- [x] 4.1 `analysis_service.py` 新增 `ZONE_COLORS` 字典：`danger` → `(0, 0, 255)` 红色，`phone_forbidden` → `(0, 140, 255)` 橙色
- [x] 4.2 `_draw_zones()` 按 `zone_type` 查表取色绘制多边形和标签

## 5. 前端移除 seat / roi

- [x] 5.1 `App.vue` 的 `zoneTypeOptions` 移除 `seat` 和 `roi` 选项
- [x] 5.2 区域编辑弹窗的 `<el-option>` 移除 `seat` 和 `roi`（共用 `zoneTypeOptions`，已随 5.1 同步移除）
- [x] 5.3 `zoneTypeText()` 移除 `seat` / `roi` 映射
- [x] 5.4 验证：前端区域类型下拉只有"危险区"和"手机禁用区"

## 6. Spring Boot 校验收窄

- [x] 6.1 `ZoneCreateRequest.java` 的 `@Pattern` 正则改为 `^(danger|phone_forbidden)$`
- [x] 6.2 `ZoneUpdateRequest.java` 同步修改 `@Pattern` 正则
- [x] 6.3 `schema.sql` 的 `zone_type` 列注释更新为 `danger / phone_forbidden`
- [x] 6.4 验证：Spring Boot 编译通过

## 7. 测试

- [x] 7.1 `test_zone_service.py`：补充 `phone_forbidden` 区域不触发入侵检测的测试
- [x] 7.2 `test_behavior_service.py`：补充手机在禁用区内/外分别产出/不产出事件的测试
- [x] 7.3 `test_behavior_service.py`：补充无禁用区时跳过手机检测的测试
- [x] 7.4 `test_behavior_service.py`：补充 `phone_usage` 事件携带 `zone` 字段的测试

## 8. 修复已有测试兼容性

- [x] 8.1 `test_routes.py`：`FakeBehaviorService.detect_from_objects()` 新增 `phone_forbidden_zones=None` 参数
- [x] 8.2 `test_analysis_visualization.py`：`FakeBehaviorService.detect_from_objects()` 新增 `phone_forbidden_zones=None` 参数
- [x] 8.3 `test_analysis_visualization.py`：修正 `test_only_danger_zone_intrusion_saves_snapshot` → `test_snapshot_event_types_save_snapshots`（`phone_usage` 本就在 `SNAPSHOT_EVENT_TYPES` 中）
- [x] 8.4 `test_config_client.py`：修复 `FakeSession` 的 `params` key 名 `stream_id` → `streamId`
- [x] 8.5 `test_zone_service.py`：已有 `test_zone_approach_does_not_mark_intrusion` 补充 `zone_type: "danger"`
