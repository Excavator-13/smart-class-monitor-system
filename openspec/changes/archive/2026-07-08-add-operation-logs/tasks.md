## 1. 数据库与数据层

- [x] 1.1 追加 `operation_log` 表 DDL
- [x] 1.2 创建 `OperationLog` Entity
- [x] 1.3 创建 `OperationLogMapper`（分页查询+insert）

## 2. VO + Service + Controller

- [x] 2.1 创建 `OperationLogVO`（不含 request_body）
- [x] 2.2 创建 `OperationLogService`（listLogs + log 手动记录方法）
- [x] 2.3 创建 `OperationLogController`（GET /operation-logs, system-api 分组）

## 3. 编译与验证

- [x] 3.1 运行 `mvn -DskipTests compile`
- [x] 3.2 确认分页 records/page/page_size/total
- [x] 3.3 确认 request_body 默认不保存敏感数据（注释说明 + log() 方法文档要求调用方脱敏）
