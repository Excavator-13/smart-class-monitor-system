# 完善 AI 服务联调闭环

## 背景

在 YOLOv8 和 InsightFace 模型加载接入后，AI 服务仍存在若干联调闭环缺口。

主要问题包括：

- AI 调 SpringBoot 内部接口缺少鉴权 token。
- 启动时没有自动加载视频源、区域、规则和人脸特征。
- 没有 `/analysis/summary/{stream_id}`，前端只能使用 mock 数据。
- 告警缺少截图证据。
- 视频流离线没有形成正式 `stream_offline` 告警。
- 事件中文名存在乱码。
- 告警推送失败被静默吞掉，排查困难。
- 部分事件类型仍只是文档枚举，缺少清晰边界说明。

## 变更内容

- 增加 AI 出站请求的 `X-Internal-Token`。
- AI 服务启动时自动拉取：
  - 视频源
  - 区域配置
  - 规则配置
  - 人脸特征库
- 增加后台定时刷新配置和人脸特征。
- 新增 `/analysis/summary/{stream_id}`。
- 告警确认时保存截图，并传递相对路径 `snapshot_path`。
- 视频流无帧时生成 `stream_offline` 事件。
- 修复事件中文名称。
- 增加模型平均推理耗时统计。
- 增加告警推送失败日志。
- 增加事件状态过期，避免同一事件永远不能再次告警。
- 增加 `fall_detected` 初版启发式检测。
- 明确 `head_down`、`leave_seat`、`flame_detected` 当前限制。

## 影响范围

涉及文件：

- `backend_ai/app.py`
- `backend_ai/services/alert_client.py`
- `backend_ai/services/analysis_service.py`
- `backend_ai/services/behavior_service.py`
- `backend_ai/services/config_client.py`
- `backend_ai/services/event_service.py`
- `backend_ai/tests/`

新增或完善的能力：

- `GET /analysis/summary/{stream_id}`
- `GET /model/status` 平均耗时字段
- 告警截图保存
- `stream_offline` 告警
- 内部接口 token 鉴权

## 仍需后续输入的能力

以下能力当前只做边界说明或初版启发式，不等同于生产级模型能力：

- `head_down`：YOLOv8 COCO 不输出低头姿态，需要姿态模型、头部模型或自训练行为模型。
- `leave_seat`：需要座位区域或座位分配配置。
- `flame_detected`：需要单独火焰/烟雾检测模型。
- `fall_detected`：当前为人体框宽高比启发式，后续建议改为 YOLO pose 或专用摔倒检测模型。
