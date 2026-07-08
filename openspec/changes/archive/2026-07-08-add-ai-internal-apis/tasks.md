## 1. 数据库

- [x] 1.1 追加 `alert_event` 表 DDL

## 2. Entity、Mapper

- [x] 2.1 创建 `AlertEvent` Entity
- [x] 2.2 创建 `AlertEventMapper`（findByEventId + insert）

## 3. AI 内部鉴权

- [x] 3.1 `application.yml` 增加 `ai.internal-token`
- [x] 3.2 创建 `InternalTokenInterceptor`
- [x] 3.3 JwtAuthenticationInterceptor 白名单增加 /alerts/ai + /students/face-features
- [x] 3.4 WebMvcConfig 注册 InternalTokenInterceptor

## 4. Service + Controller

- [x] 4.1 创建 `AlertEventService`（event_id 幂等 + 路径校验）
- [x] 4.2 创建 `AiAlertController`（controller.ai，POST /alerts/ai）

## 5. DTO、VO

- [x] 5.1 创建 `AlertIngestRequest`（含所有字段 + @Schema）
- [x] 5.2 创建 `AlertIngestResponse`（alert_id + status）

## 6. 现有接口检查

- [x] 6.1 确认 GET /students/face-features 在 controller.ai（已实现）
- [x] 6.2 确认 GET /streams 返回 rtmp_url（StreamVO 含）
- [x] 6.3 确认 GET /zones 返回 coordinates（ZoneVO 含）
- [x] 6.4 确认 GET /rules 返回 confidence_threshold + cooldown_seconds（RuleVO 含）

## 7. 编译与验证

- [x] 7.1 运行 `mvn -DskipTests compile`
- [x] 7.2 确认 `/alerts/ai` 是 `/alerts/ai`
- [x] 7.3 确认幂等字段是 `event_id`
- [x] 7.4 确认 snapshot_path/record_path 路径校验
- [x] 7.5 确认 InternalTokenInterceptor 只拦截 AI 路径
- [x] 7.6 确认 `/alerts/ai` 在 JWT 白名单中
