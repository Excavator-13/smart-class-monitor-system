## 1. 数据库与 AiClient 扩展

- [x] 1.1 追加 `danger_zone` 表 DDL
- [x] 1.2 AiClient 增加 `reloadConfig`

## 2. Entity、Mapper

- [x] 2.1 创建 `DangerZone` Entity
- [x] 2.2 创建 `DangerZoneMapper`

## 3. DTO、VO

- [x] 3.1 创建 `ZoneCreateRequest`
- [x] 3.2 创建 `ZoneUpdateRequest`
- [x] 3.3 创建 `ZoneVO`（含 safe_distance）

## 4. Service + Controller

- [x] 4.1 创建 `ZoneService`（CRUD + reloadConfig）
- [x] 4.2 创建 `ZoneController`（6 个端点）

## 5. 编译与验证

- [x] 5.1 运行 `mvn -DskipTests compile`
- [x] 5.2 确认 zone_type 使用 danger/seat/phone_forbidden/roi
- [x] 5.3 确认 coordinates 为归一化 JSON
- [x] 5.4 确认 PUT/DELETE 后调用 reloadConfig
