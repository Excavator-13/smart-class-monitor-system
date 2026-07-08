## Context

所有业务模块已完成。操作日志用于记录管理员和教师的关键操作，供后续审计。

## Goals / Non-Goals

**Goals:**
- operation_log 表 + 分页查询
- `OperationLogService.log(action, targetType, targetId, ...)` 供其他 Service 调用
- 敏感字段脱敏

**Non-Goals:**
- 不实现 AOP 自动记录（后续扩展）
- 不修改已有业务代码（本次只建表和查询接口，手动记录由后续 change 在各 Service 中添加）

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 脱敏方式 | 调用方负责不传入敏感数据 | 简单，日志服务不参与数据解析 |
| request_body | 可选字段，默认 null | 初版不记录请求体 |
| 查询权限 | admin 可查所有，teacher 有限 | 初版暂不做角色过滤 |
