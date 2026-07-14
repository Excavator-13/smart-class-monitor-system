# Design: 连续事件与同类冷却

## 当前问题

`EventService` 以 `(stream_id, event_type, track_key)` 保存状态：

1. 状态仅在 300 秒未观察到后过期，故 `threshold_seconds` 不是连续时长。
2. 同类事件的不同 `track_key` 各自拥有冷却，可在同一视频流中密集触发。
3. 已确认状态在冷却结束后可再次确认，并复用原事件 ID。
4. 每次观察都会向内存队列插入一条记录，导致事件流和统计重复。

## 设计决策

### 连续事件周期

事件状态按 `(stream_id, event_type)` 聚合。两次有效观察间隔不超过 `continuity_gap_seconds` 时视为同一连续周期；超过该间隔则开始新周期、重新计算持续时间并生成新事件 ID。

默认 `continuity_gap_seconds=2`，通过 `backend_ai/config/app.yaml` 的 `events` 节配置。

### 一次周期只确认一次

状态从 `candidate` 进入 `confirmed` 后，本周期内不再返回新的确认信号。因此持续异常不会在冷却结束时反复截图、入库和发送钉钉通知。

最新 `dev` 的告警叠加层仍由 `AnalysisService` 在 `should_confirm` 时写入，因此它只在新周期首次确认时展示；截图上传、钉钉通知和录像证据路径继续沿用新版链路。

### 同类事件冷却

最近告警时间独立保存在 `(stream_id, event_type)` 维度。新周期即使达到时间阈值，也必须等待该类型冷却结束后才确认。首次出现不受初始时间值影响，可正常确认。

全局默认冷却继续使用最新 `dev` 的 10 秒配置，避免改变现有部署参数。

### 事件列表去重

内存队列中相同 `event_id` 采用更新而非追加。候选状态、持续时长和确认状态仍可更新，但查询结果中一次异常周期只占一条。

## 影响范围

- `backend_ai/services/event_service.py`
- `backend_ai/app.py`
- `backend_ai/config/app.yaml`
- `backend_ai/tests/test_event_service.py`

接口与数据库契约不变。
