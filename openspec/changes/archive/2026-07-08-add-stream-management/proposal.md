## Why

鉴权模块已就绪，需要实现视频源管理模块。视频源的 `stream_id` 是后续 AI 拉流分析、区域绑定、告警关联的核心标识，应尽早实现。

## What Changes

- 新增 `video_stream` 数据库表 DDL
- 新增 `GET /streams`：查询视频源列表（返回 `id` 和 `stream_id`）
- 新增 `POST /streams`：新增视频源（`stream_id` 需唯一）
- 新增 `GET /streams/{stream_id}/status`：请求 Nginx 9092 `/stat` XML 判断在线状态
- 新增 `GET /streams/enabled`：获取已启用视频源
- 新增 `GET /streams/{id}`、`PUT /streams/{id}`、`DELETE /streams/{id}`：管理 CRUD（🟡 待定）
- 新增 `GET /streams/{stream_id}/preview-url`：返回播放地址（不代理视频流）
- 新增 `NginxClient`：封装 Nginx `/stat` XML 请求与解析
- 路径参数区分：实时类接口用 `stream_id`（业务标识），管理 CRUD 用 `id`（数据库主键）
- **不加 `/api/v1` 前缀**
- **不代理视频流**

## Capabilities

### New Capabilities
- `stream-crud`: 视频源增删改查（GET/POST/PUT/DELETE /streams）
- `stream-status`: 视频源推流状态检测（GET /streams/{stream_id}/status → Nginx /stat）
- `stream-preview`: 返回播放地址（GET /streams/{stream_id}/preview-url）
- `nginx-client`: Nginx /stat XML 请求与解析客户端

### Modified Capabilities
<!-- 无 -->

## Impact

- 新增数据库表：`video_stream`
- 新增 Java 包：`integration/` 下的 `NginxClient`
- 新增文件：Entity、Mapper、DTO、VO、Service、Controller、NginxClient
- 依赖变更：需添加 XML 解析依赖（使用 JDK 内置 `javax.xml`，无需额外依赖）
