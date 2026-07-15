## Why

手机单帧检测会因两秒连续性窗口反复归零而无法确认入库；明火规则名称可能不一致且缺少运行诊断；事件查询可能因运行期对象不可 JSON 序列化返回 500。

## What Changes

- 为手机事件提供独立的连续性容忍窗口。
- 明火兼容 `fire_detected` 与 `flame_detected`，暴露原始和过滤统计。
- AI JSON 响应统一转换 NumPy 等特殊类型。

## Impact

修改 AI EventService、BehaviorService、FireService、响应工具、模型状态与测试，不改变数据库结构和外部字段命名。
