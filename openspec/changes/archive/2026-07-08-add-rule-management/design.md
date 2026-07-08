## Context

区域 CRUD 已完成（reloadConfig 联动已验证）。规则模块复用同一模式。`confidence_threshold` 和 `cooldown_seconds` 是 AI 端的顶级配置字段，必须在 PUT 接口中作为独立字段暴露。

## Goals / Non-Goals

**Goals:**
- behavior_rule 表 + CRUD + 软删除
- PUT 支持 `enabled`、`threshold_seconds`、`confidence_threshold`、`cooldown_seconds`、`config_json`
- 修改后调 AI `/config/reload`（rules + zones 一起 reload）

**Non-Goals:**
- 不实现告警模块
- 不实现规则自动推荐

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| confidence_threshold 存储 | DECIMAL(5,4) | 精度足够 |
| AI reload items | `["rules"]` | Zone 变更时用 `["zones"]`，Rule 变更时用 `["rules"]` |
| 初版规则 | 不预置数据，由管理端 POST 创建 | 灵活 |
