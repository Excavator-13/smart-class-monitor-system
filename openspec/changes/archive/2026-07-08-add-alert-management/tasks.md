## 1. Mapper 扩展

- [x] 1.1 AlertEventMapper 追加分页查询、详情、状态更新、统计方法

## 2. VO

- [x] 2.1 创建 `AlertVO`（snapshot_url + record_url 相对路径）
- [x] 2.2 创建 `AlertStatsVO`

## 3. DTO

- [x] 3.1 创建 `AlertStatusUpdateRequest`

## 4. Service + Controller

- [x] 4.1 创建 `AlertService`（分页+详情+状态校验+统计）
- [x] 4.2 创建 `AlertController`（GET /alerts, GET /alerts/{id}, PUT /alerts/{id}/status, GET /alert-stats）

## 5. 编译与验证

- [x] 5.1 运行 `mvn -DskipTests compile`
- [x] 5.2 确认 snapshot_url/record_url 为相对路径
- [x] 5.3 确认 AlertController 不改 /alerts/ai
