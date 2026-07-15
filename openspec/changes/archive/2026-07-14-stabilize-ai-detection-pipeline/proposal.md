## Why

当前 AI 实时分析链路在推流终止、区域坐标匹配和明火规则读取上存在回归：同一次断流会被拆成两次离线告警，断流后的缓冲帧仍会产生异常截图，真实 YOLO 像素框无法命中前端保存的归一化区域，并且明火规则键不一致导致生产阈值未生效。这些问题会直接造成漏报、误报和错误证据入库，需要作为同一条检测稳定性变更统一修复并补齐回归测试。

## What Changes

- 将 RTMP 读取成功与“流已真实恢复”分离；进入离线候选周期后，不允许滞后的缓冲帧重置门控或进入分析，确保一个连续断流周期只产生一次 `stream_offline`，且断流后不再产生其他异常及截图。
- 为区域判断建立明确的坐标空间转换：YOLO 像素框与前端 0–1 归一化多边形在匹配前统一到同一坐标系，同时保留像素框用于视频画框。
- 对命中手机禁用区的手机使用事件和命中危险区的人员入侵事件返回可见画框、区域信息和左上角告警提示。
- 统一 SpringBoot `fire_detected` 规则与 AI `flame_detected` 事件的规则解析，应用更严格的有效阈值，并只接受配置允许的火焰类别，降低无火场景误报。
- 增加覆盖真实像素坐标、配置热刷新、断流缓冲、单周期幂等和明火阈值/类别过滤的回归测试。

## Capabilities

### New Capabilities

- `ai-detection-stability`: 约束离线生命周期、区域坐标匹配、检测标注与明火误报抑制在同一实时 AI 分析链路中的稳定行为。

### Modified Capabilities

- `fire-detection`: 明火检测必须读取当前启用规则的阈值、过滤非火焰类别，并经过连续观察后才生成告警。

## Impact

- AI 服务：`stream_manager.py`、`analysis_service.py`、`behavior_service.py`、`zone_service.py`、`fire_service.py`、坐标工具与对应 pytest。
- 配置：`backend_ai/config/app.yaml`、`backend_ai/config/model.yaml` 的流新鲜度和明火过滤参数；保留用户当前对模型启用状态的本地修改。
- SpringBoot/前端接口契约不新增字段、不调整数据库结构；继续使用现有 `snake_case` 事件、区域和告警入库格式。
- 文档：同步修订明火检测规范与 AI 服务说明；不涉及 Nginx 对外路径和前端 API 路径变更。
