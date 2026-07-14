## Context

数据库已有 `target_info` 和 `zone_id`，入库链路也已写入，但 `AlertVO` 丢弃了两者。前端只显示能与禁用区再次相交的手机告警，因此列表记录被隐藏。AI 的检测框仅按当前帧绘制，确认覆盖层只画左上角文字。

## Goals / Non-Goals

**Goals:** 返回完整目标数据、保证已入库手机告警可见、让确认框保持可辨识时长、兼容旧事件查询路径。

**Non-Goals:** 不修改表结构，不改变手机检测模型和五秒确认规则。

## Decisions

- `AlertVO.targetInfo` 使用 Object，由 MyBatis JSON 值原样返回；前端现有 `parseMaybeJson` 兼容对象和字符串。
- 前端仅对 AI 候选事件执行区域相交校验；SpringBoot 已入库 `phone_usage` 视为 AI 已完成区域判定。
- 告警覆盖缓存同时保存 bbox，存活时间继续由 `alert_overlay_seconds` 配置，默认从 2 秒提高到 5 秒。
- `/events` 复用同一 handler，作为向后兼容别名。

## Risks / Trade-offs

- 历史记录可能没有 target_info → 仍显示告警，但不展示目标框。
- 框保持期间人物可能移动 → 仅保持五秒并明确表示最近确认位置。
