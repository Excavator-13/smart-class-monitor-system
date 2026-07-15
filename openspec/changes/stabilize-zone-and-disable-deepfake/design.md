# 危险区与换脸检测稳定化设计

## Goals

1. 恢复危险区的轮廓和事件标注，让一个 `danger_zone` 开关管控三种子事件。
2. 当前阶段完全停用 Deepfake 运行路径，但保留未来再开放的代码与规则记录。
3. 用最小改动修复配置刷新副作用和默认放行问题。

## Decisions

- `ConfigClient` 仅向 AI 检测服务暴露已启用规则；禁用或缺失都按 fail-closed 处理。前端仍直接从 SpringBoot 获取完整规则列表。
- `AnalysisService` 使用 `EVENT_RULE_TYPES` 解析事件的业务规则键，对受管控事件采用 fail-closed：规则缺失或关闭均跳过。
- `danger_zone_intrusion/stay/approach` 都映射到 `danger_zone`。
- `AntiSpoofService.deepfake_enabled` 是运行开关；为 false 时跳过 CNN 和纹理换脸分支，不仅是过滤告警。
- Deepfake 不在视频可视化白名单中。Danger zone 区域轮廓和事件框保留。
- 不引入配置缓存大重构；本次只删除会意外刷新 zones 的重复 Controller 调用。

## Rule resolution

```text
detected event
  -> resolve event rule type
  -> governed type and rule missing/disabled: skip
  -> enabled: observe and optionally alert
```

`ZoneService` 在产生检测前也检查 `danger_zone.enabled`，避免无效候选事件进入后续流程。

## Non-Goals

- 不删除 MesoNet 权重、训练脚本或历史告警。
- 不改动危险区坐标模型、数据库表或 API 字段。
- 不在本变更中处理 MJPEG 性能与断流重连。
