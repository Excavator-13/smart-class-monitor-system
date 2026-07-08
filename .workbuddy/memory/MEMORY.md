# 项目长期记忆

## 技术栈与配置约定
- 后端：Spring Boot 3.3.3 + MyBatis + MySQL Connector/J 8.x + JWT(jjwt 0.12.6) + springdoc-openapi 2.6.0
- JDK 17（本地用 graalvm-jdk-17.0.12），也可用 temurin-21
- 数据库：远程 MySQL 39.106.209.208:3306/appdb，用户 appuser

## 重要踩坑
- **JDBC characterEncoding 不能用 utf8mb4**：这是 MySQL 字符集名不是 Java 字符集名，会导致 `Unsupported character encoding` 异常，所有 DB 操作失败。正确值是 `utf8`（Connector/J 自动映射到 utf8mb4）。
- data.sql 中的用户 INSERT 被注释掉了，但远程数据库已有初始化数据：admin/admin123（role=admin）、teacher/teacher123（role=teacher），密码均为 BCrypt。

## 接口约定
- 统一响应 ApiResponse：`{code, message, data}`，成功 code=0
- JSON 字段 snake_case（Jackson SNAKE_CASE 策略）
- 全局异常：BusinessException 按业务 code 返回；其他异常兜底 500 "服务内部异常"
- health 接口 /system/health 返回 backend/database/ai/rtmp 状态，组件不可用仍返回 200
