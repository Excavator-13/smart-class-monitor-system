## Context

`NginxClient` 和 `AiClient` 已就绪。SystemController 已有基础 health（backend+DB）。本 change 增强 health + 新增 recordings。

## Goals / Non-Goals

**Goals:**
- recording_file 表 + 分页查询
- system/health 增加 AI 和 Nginx 状态

**Non-Goals:**
- 不实现录像自动写入（后续）
- 不修改前端/AI/Nginx

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| system/health 增强方式 | 扩展 SystemController（原地增强） | 不新建 Controller |
| Nginx 探活 | 复用 NginxClient.getStreamStatus + 额外通用探活方法 | 已有客户端 |
| AI 探活 | AiClient 新增 `checkHealth()` → GET /model/status | 已有客户端 |
| recording_file.available | 计算字段：file_path 可访问 + 未过期 | 7天过期 |
