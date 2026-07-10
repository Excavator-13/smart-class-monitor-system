# 任务清单

## 接口与联调闭环

- [x] 实现 `GET /analysis/summary/{stream_id}`。
- [x] AI 调 SpringBoot 内部接口时增加 `X-Internal-Token`。
- [x] 启动时自动加载视频源、区域、规则和人脸特征。
- [x] 增加后台定时刷新配置和人脸特征。

## 告警与证据

- [x] 告警确认时保存截图。
- [x] 将截图相对路径 `snapshot_path` 传给 SpringBoot。
- [x] 保留 `record_path` 和 `event_time_offset` 传递入口。
- [x] 视频流无帧时生成 `stream_offline` 告警。
- [x] 告警推送失败时写日志。

## 事件与模型状态

- [x] 修复事件中文名乱码。
- [x] 增加事件状态过期机制。
- [x] 在 `/model/status` 中返回平均推理耗时。
- [x] 增加 `fall_detected` 初版启发式检测。

## 边界说明

- [x] 明确 `head_down` 当前依赖 `head_down_ratio`，YOLOv8 COCO 本身不支持低头识别。
- [x] 明确 `leave_seat` 需要座位区域或座位分配配置。
- [x] 明确 `flame_detected` 需要独立火焰/烟雾模型。

## 验证

- [x] 更新相关单元测试。
- [x] 运行 `pytest backend_ai\tests`。
- [x] 测试通过，结果为 `29 passed`。
