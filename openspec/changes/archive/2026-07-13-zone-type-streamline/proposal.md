# 区域类型精简：danger 入侵 + phone_forbidden 手机禁用

## Why

当前区域配置支持四种 `zone_type`（danger / seat / phone_forbidden / roi），但后端 AI 实际只对**所有区域统一做"人员入侵"检测**，不区分类型。这导致三个问题：

1. **danger 不纯粹**——画了一个 `phone_forbidden` 区域，后端 AI 也会对其产出 `danger_zone_intrusion` 告警，语义矛盾
2. **phone_forbidden 不生效**——后端 `BehaviorService` 检测手机时只看"人+手机 bbox 重叠"，不检查手机是否在禁用区坐标内；前端做了展示层过滤，但告警已推送到数据库和钉钉
3. **seat / roi 是空壳**——后端没有任何逻辑消费这两种类型，画了等于白画

## What Changes

### 1. ZoneService 按 zone_type 分流检测

`zone_service.py` 的 `detect()` 方法当前遍历所有 zones 做入侵检测。改为：

- 只对 `zone_type == "danger"` 的区域执行人员入侵/停留/接近检测
- `zone_type == "phone_forbidden"` 的区域跳过（手机检测由 BehaviorService 负责）

### 2. BehaviorService 手机检测加入 phone_forbidden 区域判断

`behavior_service.py` 的 `detect_from_objects()` 方法当前检测手机时不考虑区域。改为：

- 新增 `phone_forbidden_zones` 参数
- 检测到 `phone_usage` 时，检查手机 bbox 中心点是否落入某个 `phone_forbidden` 区域多边形内
- 只有在禁用区内的手机才产出 `phone_usage` 事件
- 如果没有任何启用的 `phone_forbidden` 区域，跳过手机检测（与前端"无禁用区则手机规则禁用"的逻辑一致）
- 命中禁用区的手机事件携带 `zone` 信息（zone_id / zone_name / zone_type）

### 3. AnalysisService 串联 zone_type 分流

`analysis_service.py` 的 `analyze_frame()` 方法当前将所有 zones 传给 `zone_service.detect()`。改为：

- 按 `zone_type` 将 zones 分为 `danger_zones` 和 `phone_forbidden_zones`
- `danger_zones` 传给 `zone_service.detect()` 做入侵检测
- `phone_forbidden_zones` 传给 `behavior_service.detect_from_objects()` 做手机区域过滤
- 绘制区域时按 zone_type 使用不同颜色区分（danger 红色，phone_forbidden 橙色）

### 4. 前端移除 seat / roi 选项

- `zoneTypeOptions` 从四项缩减为 `danger` + `phone_forbidden`
- 区域编辑弹窗的 `<el-option>` 同步移除 seat / roi
- `zoneTypeText()` 移除 seat / roi 的映射
- `confirmedForbiddenZones` 计算逻辑不变（已正确只看 `phone_forbidden`）

### 5. 后端 Spring Boot 校验收窄

- `ZoneCreateRequest.java` 的 `@Pattern` 正则从 `danger|seat|phone_forbidden|roi` 改为 `danger|phone_forbidden`
- `schema.sql` 的 `zone_type` 列注释同步更新

## Capabilities

### Modified Capabilities

- **zone-intrusion-detection**: `ZoneService.detect()` 只对 `danger` 类型区域执行入侵检测，`phone_forbidden` 区域不再误触发 `danger_zone_intrusion`
- **phone-usage-detection**: `BehaviorService.detect_from_objects()` 手机检测增加 `phone_forbidden_zones` 参数，只有手机 bbox 中心在禁用区多边形内才产出事件，事件携带 zone 信息
- **zone-crud**: 前端和后端校验只允许 `danger` / `phone_forbidden` 两种类型

### Removed Capabilities

- **seat-zone-type**: 移除座位区类型（后端无对应检测逻辑）
- **roi-zone-type**: 移除识别区域类型（后端无对应检测逻辑）

## Impact

### backend_ai（Python / Flask）

- `services/zone_service.py`：`detect()` 过滤只处理 `zone_type == "danger"` 的区域
- `services/behavior_service.py`：`detect_from_objects()` 新增 `phone_forbidden_zones` 参数，手机检测加入区域判断
- `services/analysis_service.py`：`analyze_frame()` 按 zone_type 分流 zones，分别传给 zone_service 和 behavior_service；区域绘制按类型区分颜色
- `tests/test_zone_service.py`：补充 `phone_forbidden` 区域不应触发入侵检测的测试
- `tests/test_behavior_service.py`：补充手机在禁用区内/外分别产出/不产出事件的测试

### backend_system（Java / Spring Boot）

- `dto/ZoneCreateRequest.java`：`@Pattern` 正则改为 `danger|phone_forbidden`
- `dto/ZoneUpdateRequest.java`：如有同款校验同步修改
- `config/DataInitializer.java`：`seedZones()` 中只有 `danger` 和 `phone_forbidden` 两种区域
- `resources/sql/schema.sql`：`zone_type` 列注释更新

### frontend（Vue3 / Element Plus）

- `App.vue`：`zoneTypeOptions` 移除 seat / roi；区域编辑弹窗 `<el-option>` 移除 seat / roi；`zoneTypeText()` 移除 seat / roi 映射；绘制区域时按 zone_type 区分颜色

## 不做

- 不改数据库已有数据（已有 seat / roi 类型的区域记录在迁移后可能残留，但不会被 AI 使用，可手动清理）
- 不改 `danger_zone` 表名（虽然现在不只存 danger 类型，但改名涉及面太广，性价比低）
- 不改 `config_client.py` 的 `get_zones()` 返回结构（仍返回全部 zones，分流在 analysis_service 层完成）
- 不实现 seat 离座检测或 roi 裁剪检测（超出本次范围）
- 不改前端 `isPhoneRelated()` / `isPhoneItemInForbiddenZone()` 的展示过滤逻辑（后端配合后，这些逻辑仍然正确，只是从"前端补救"变为"前后端一致"的冗余安全网）
