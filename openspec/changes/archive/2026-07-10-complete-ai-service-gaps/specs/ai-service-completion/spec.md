## 新增需求

### 需求：AI 服务联调闭环

AI 服务必须补齐告警联调、配置同步、摘要展示、证据留存和运行状态观测能力。

### 场景：返回视频源研判摘要

- 假设 AI 服务内存中已有候选事件
- 当 前端请求 `/analysis/summary/{stream_id}`
- 那么 AI 服务应返回：
  - 风险分 `risk_score`
  - 风险等级 `risk_level`
  - 摘要文本 `summary`
  - 事件计数 `counts`
  - 视频流状态 `stream_status`
  - 处置建议 `suggestion`

### 场景：AI 内部调用 SpringBoot 通过鉴权

- 假设已配置 `AI_INTERNAL_TOKEN`
- 当 AI 服务调用 SpringBoot 内部接口
- 那么请求头必须包含：

```http
X-Internal-Token: <token>
```

### 场景：启动时加载配置和人脸特征

- 假设 SpringBoot 服务可访问
- 当 Flask AI 服务启动
- 那么 AI 服务应主动拉取：
  - 视频源配置
  - 区域配置
  - 行为规则
  - 人脸特征库
- 并且启动后台轮询作为兜底同步机制

### 场景：确认告警包含截图证据

- 假设某个候选事件满足确认条件
- 并且当前视频帧可编码
- 当 AI 服务推送正式告警到 SpringBoot
- 那么 AI 服务应保存截图
- 并且在入库请求中传递相对路径 `snapshot_path`

### 场景：视频流离线生成告警

- 假设某个已配置视频源无法获取视频帧
- 当 AI 服务观察到该离线状态
- 那么服务应生成 `stream_offline` 事件
- 并且该事件必须遵守冷却规则，避免频繁重复入库

### 场景：模型状态包含推理耗时

- 假设 AI 服务已经执行过人脸、行为或区域分析
- 当 调用 `/model/status`
- 那么响应中对应模型项应包含 `avg_infer_ms`

### 场景：事件状态可过期

- 假设某个事件已确认
- 并且该目标长时间未再次出现
- 当 后续同一类型事件再次发生
- 那么 AI 服务应允许重新生成确认告警

### 场景：需要额外模型或配置的行为能力保持显式说明

- 假设当前行为模型是 YOLOv8 COCO
- 当 系统评估 `head_down`、`leave_seat` 或 `flame_detected`
- 那么：
  - `head_down` 仅在上游对象提供 `head_down_ratio` 时触发
  - `leave_seat` 在座位区域或座位分配配置完成前不作为已完成能力
  - `flame_detected` 在火焰/烟雾模型接入前不作为已完成能力
