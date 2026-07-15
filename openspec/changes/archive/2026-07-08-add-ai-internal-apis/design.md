## Context

AI 内部接口需与前端接口在鉴权、路径、数据访问上完全隔离。`/students/face-features` 已在 `controller.ai.AiFaceFeatureController` 实现。本 change 重点实现 `POST /alerts/ai` 并建立内部鉴权机制。

## Goals / Non-Goals

**Goals:**
- alert_event 表 + Entity + Mapper
- `POST /alerts/ai`：幂等写入，校验路径格式
- `X-Internal-Token` 鉴权拦截器（放行前端 JWT 拦截器，内部自校验）
- 检查现有接口的 AI 兼容性

**Non-Goals:**
- 不实现 `/alerts` GET（前端列表，下一步）
- 不实现 `/alerts/{id}` / `/alerts/{id}/status`
- 不改路径名、字段名

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 幂等实现 | `SELECT event_id → 存在则返回已有` | 简单可靠，唯一索引兜底 |
| 内部 Token | 配置 `ai.internal-token`，拦截器校验 `X-Internal-Token` 头 | 与前端 JWT 完全隔离 |
| 内部拦截器范围 | 仅拦截 `/alerts/ai` + `/students/face-features` | 最小权限 |
| 路径校验 | 必须以 `/` 开头，不含 `://`、`..` | 接口文档 §9.3 |
| status 默认 | `unhandled` | 详细设计 §4.7 |

## JWT 拦截器调整

```
JwtAuthenticationInterceptor 白名单新增:
  + /alerts/ai          (由 InternalTokenInterceptor 保护)
  + /students/face-features (由 InternalTokenInterceptor 保护)

InternalTokenInterceptor:
  拦截 /alerts/ai, /students/face-features
  校验 X-Internal-Token == ${ai.internal-token}
```

## Risks

- **[内部 Token 泄露]** 配置文件中的 internal-token 需保密 → 生产环境用环境变量注入
