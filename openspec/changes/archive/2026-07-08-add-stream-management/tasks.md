## 1. 数据库与数据层

- [x] 1.1 创建 `video_stream` 表 DDL
- [x] 1.2 创建 `VideoStream` Entity
- [x] 1.3 创建 `VideoStreamMapper`

## 2. NginxClient 集成

- [x] 2.1 在 `application.yml` 增加 `nginx.stat-url`
- [x] 2.2 创建 `NginxClient`

## 3. DTO、VO

- [x] 3.1 创建 `StreamCreateRequest` DTO
- [x] 3.2 创建 `StreamUpdateRequest` DTO
- [x] 3.3 创建 `StreamVO` VO
- [x] 3.4 创建 `StreamStatusVO` VO
- [x] 3.5 创建 `StreamPreviewVO` VO

## 4. Service 层

- [x] 4.1 创建 `StreamService`

## 5. Controller 层

- [x] 5.1 创建 `StreamController`（8 个端点）

## 6. Swagger 注解

- [x] 6.1 所有 DTO/VO 字段有 `@Schema`，Controller 方法有 `@Operation`

## 7. 编译与验证

- [x] 7.1 运行 `mvn -DskipTests compile`
- [x] 7.2 确认 `GET /streams` 返回 `id` 和 `stream_id`
- [x] 7.3 确认 `GET /streams/{stream_id}/status` 路径参数名为 `stream_id`
- [x] 7.4 确认 preview-url 返回 JSON
