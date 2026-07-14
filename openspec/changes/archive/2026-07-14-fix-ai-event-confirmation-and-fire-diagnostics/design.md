## Context

通用 YOLO 对小手机检测间歇，当前全局两秒 gap 会重建候选事件。明火服务只取一个规则键且规则缺失直接跳过推理。Flask jsonify 直接序列化事件缓存。

## Decisions

- EventService.observe 接受可选的事件级 continuity gap，手机默认 6 秒，其他事件维持全局 2 秒。
- FireService 接受两个规则别名并记录每次推理的 raw/class/confidence/area 统计。
- YOLO 推理阶段最低置信度读取 `model.yaml` 的 `inference_confidence_threshold`；业务过滤继续读取 SpringBoot 规则，并使用配置文件 `confidence_threshold` 作为兜底。
- json_response 在 envelope 前递归转换 ndarray、numpy scalar、tuple、set 和 datetime。

## Risks / Trade-offs

- 手机短暂消失仍可能累计持续时间 → 仅对已命中禁用区的手机事件放宽至 6 秒。
- 诊断统计是进程内最近一次推理数据 → 重启后清零。
