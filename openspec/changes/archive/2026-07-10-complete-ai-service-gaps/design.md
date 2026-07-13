# 设计说明

## 总体目标

本次变更目标是让 AI 服务从“模型可加载”推进到“联调闭环可用”：

- 能启动后自动同步配置。
- 能调用 SpringBoot 内部接口并通过鉴权。
- 能给前端提供实时摘要。
- 能把确认告警写入 SpringBoot。
- 能提供截图证据。
- 能暴露模型状态和推理耗时。

## 任务拆分

### 1. 研判摘要

新增接口：

```http
GET /analysis/summary/{stream_id}
```

返回内容：

- `stream_id`
- `risk_score`
- `risk_level`
- `summary`
- `counts`
- `stream_status`
- `suggestion`

摘要先基于内存事件和视频流状态规则生成，不接入大模型。

### 2. 内部接口鉴权

AI 调 SpringBoot 内部接口时增加请求头：

```http
X-Internal-Token: <token>
```

token 来源：

- 环境变量 `AI_INTERNAL_TOKEN`
- 或 `backend_ai/config/app.yaml` 的 `spring.internal_token`

### 3. 配置和人脸特征同步

启动时执行一次 bootstrap：

- 加载 `/streams`
- 加载 `/zones`
- 加载 `/rules`
- 加载 `/students/face-features`

后台按配置间隔轮询：

- `streams_poll_seconds`
- `zones_poll_seconds`
- `rules_poll_seconds`
- `face_features_poll_seconds`

### 4. 告警证据保存

告警确认时保存当前帧截图。

保存位置：

```text
backend_ai/static/snapshots/YYYYMMDD/<event_id>.jpg
```

传给 SpringBoot 的相对路径：

```text
/snapshots/YYYYMMDD/<event_id>.jpg
```

### 5. 视频流离线告警

当 `stream_manager.get_frame(stream_id)` 返回空帧时，AI 服务生成：

```text
stream_offline
```

该事件同样走 `EventService` 的冷却和确认逻辑。

### 6. 模型耗时统计

`AnalysisService` 记录最近若干次推理耗时。

`/model/status` 返回：

- face 平均耗时
- behavior 平均耗时
- zone 平均耗时

### 7. 事件状态过期

`EventService` 为同一 `(stream_id, event_type, track_key)` 维护状态。

状态在长时间未出现后自动过期，避免同一个事件确认后永远不能再次告警。

### 8. 事件类型边界

- `phone_usage`：已基于 YOLOv8 `person` + `cell phone` 实现。
- `danger_zone_*`：已基于 YOLOv8 `person` 和 polygon 规则实现。
- `fall_detected`：当前为人员框宽高比启发式。
- `head_down`：仅保留 `head_down_ratio` 规则入口。
- `leave_seat`：等待座位配置。
- `flame_detected`：等待火焰/烟雾模型。

## 风险与取舍

- 截图保存依赖本地目录可写。
- `fall_detected` 当前不是生产级摔倒检测。
- `head_down`、`leave_seat`、`flame_detected` 需要额外模型或业务配置。
- 配置轮询失败不会中断服务，但会记录 `last_error`。

## 验证方式

运行 AI 测试：

```powershell
pytest backend_ai\tests
```

预期结果：

```text
29 passed
```
