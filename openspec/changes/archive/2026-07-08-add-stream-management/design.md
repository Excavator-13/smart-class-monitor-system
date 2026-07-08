## Context

鉴权模块已完成（`add-auth-api`）。视频源模块需要新建 `video_stream` 表、NginxClient 集成，以及对前端的 8 个 REST 接口。`stream_id` 是视频源的核心业务标识，后续 AI 拉流、区域绑定、告警关联均依赖它。

## Goals / Non-Goals

**Goals:**
- video_stream 表 + Entity + Mapper
- 8 个 REST 接口全部实现（含 Swagger 注解）
- NginxClient 封装 `/stat` XML 请求与解析
- `id` vs `stream_id` 路径参数严格区分
- 所有接口受 JWT 鉴权保护（`/streams/**` 不走白名单）

**Non-Goals:**
- 不代理视频流（preview-url 只返回地址字符串）
- 不实现 MJPEG/HLS/RTMP 服务端
- 不实现视频源状态定时轮询（按需查询）
- 不加 `/api/v1` 前缀

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| XML 解析 | JDK 内置 `javax.xml.parsers.DocumentBuilder` | 零额外依赖，/stat 返回的 XML 结构简单 |
| NginxClient 位置 | `com.smartclass.monitor.integration.NginxClient` | 详细设计 §3.3 包结构要求 |
| 软删除 | `deleted_at` 字段 | 保护历史告警关联 |
| 推流状态存储 | **不存数据库**，实时查 Nginx | 状态变化频繁，存入 DB 无意义且滞后 |
| stream_id 唯一性 | 数据库 UNIQUE 索引 + Service 层校验 | 双重保障 |
| rtmp_url 格式 | `rtmp://39.106.209.208:9090/live/{stream_id}` | 接口文档 §3.1 |
| 状态枚举 | `enabled`/`disabled`（配置状态）vs `online`/`offline`（实时状态） | 详细设计 §5.6 设计说明 |

## Nginx /stat 解析逻辑

```
GET http://39.106.209.208:9092/stat
    ↓
解析 XML:
<rtmp>
  <server>
    <application>
      <live>
        <stream>
          <name>classroom_01</name>
          <publish active="true" time="2026-07-07T10:00:00+08:00"/>
        </stream>
      </live>
    </application>
  </server>
</rtmp>
    ↓
查找 stream/name = target stream_id
    ↓
返回 publish@active + publish@time
```

## Risks / Trade-offs

- **[Nginx 不可达]** `/stat` 请求超时或 Nginx 宕机 → 返回 `offline`/`unknown`，不抛 500
- **[XML 格式变化]** Nginx RTMP 模块版本升级可能导致 XML 结构变化 → NginxClient 解析失败时返回 `degraded` 状态
- **[无视频源时 status 查询]** 请求不存在的 stream_id → 先查 DB 确认视频源存在，不存在返回 404

## Open Questions

- Nginx /stat 地址当前硬编码 `http://39.106.209.208:9092/stat`，是否需配置化？→ 建议配置化到 `application.yml` 的 `nginx.stat-url`
