# 恢复危险区并默认停用换脸检测

## Why

`8c772fc` 将缺少对应规则的事件改为默认放行，使 `danger_zone` 总规则无法稳定管控 `danger_zone_*` 子事件；同时规则切换额外触发全量配置刷新，可以意外影响区域缓存。`deepfake_detected` 也被从“未开放”状态改成可操作，且关闭规则时仍会执行换脸推理。

## What Changes

- 为换脸检测增加默认关闭的模块开关，关闭时不加载、不推理、不产生事件。
- 前端恢复 `deepfake_detected` 为不可操作项，强制显示关闭的灰色开关；视频不绘制 Deepfake 标注。
- 建立 `danger_zone_* -> danger_zone` 规则映射，缺少或关闭规则时不产生告警。
- `ZoneService` 显式遵守 `enabled`，但区域轮廓的绘制不受告警开关影响。
- 删除规则切换时重复、硬编码的 Flask 全量刷新，仅保留现有 `AiClient` 规则刷新。

## Impact

- AI：`analysis_service.py`、`anti_spoof_service.py`、`app.py`、`model.yaml`、`zone_service.py`
- SpringBoot：`RuleController.java`
- Frontend：`App.vue`
- 不修改数据库结构和对外 API。
