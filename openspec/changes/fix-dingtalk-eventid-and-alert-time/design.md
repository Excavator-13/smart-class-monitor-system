# 钉钉事件ID与数据库对齐 + 逐级上报告警时间一致性 — 技术设计

## Context

### 已有基础设施

**事件ID生成**：`EventState` 在 `event_service.observe()` 首次观测到事件时生成，格式 `evt_{uuid4().hex[:16]}`。同一事件的后续观测复用该 ID。该 ID 通过 `alert_client.map_event_to_alert()` 映射为 `AlertIngestRequest.eventId`，存入数据库 `alert_event.event_id`。

**钉钉通知调用链**：`analysis_service` → `alert_client.push_alert(event)` → `self.dingtalk(msg, snapshot=...)` → `dingtalk_service.trigger_alert(msg, start, snapshot)` → `_step(msg, event_id, ch, idx, snapshot)`。

**事件发生时间**：`EventState.occurred_at` 在首次观测时由 `now_iso()` 生成（ISO 8601 格式，如 `2026-07-15T10:00:00+08:00`），同一事件后续观测复用。该时间通过 `map_event_to_alert()` 映射为 `AlertIngestRequest.occurredAt`，存入数据库 `alert_event.occurred_at`。

**钉钉消息格式**：`_step()` 中每级消息都包含"告警时间"和"事件ID"字段。当前"告警时间"取自 `time.strftime("%Y-%m-%d %H:%M:%S")`（消息发送时间），"事件ID"取自 `trigger_alert()` 自行生成的 `evt_{timestamp}_{thread_id}`。

### 数据流断裂点

```
event_service.observe()
    │
    ├── event_id = "evt_a3b2c1d4e5f67890"  (UUID)
    ├── occurred_at = "2026-07-15T10:00:00+08:00"
    │
    ▼
alert_client.push_alert(event)
    │
    ├── map_event_to_alert() → payload.event_id = "evt_a3b2c1d4e5f67890"  ✅ 入库正确
    │
    ├── self.dingtalk(f"{alert_name} | 摄像头：{stream}", snapshot=local_snapshot)
    │       │
    │       │  ❌ event_id 和 occurred_at 丢失！只传了 msg 和 snapshot
    │       ▼
    trigger_alert(msg, start, snapshot)
        │
        ├── event_id = f"evt_{int(time.time())}_{threading.get_ident()}"  ❌ 重新生成
        │
        ▼
    _step(msg, event_id, ch, idx, snapshot)
        │
        ├── now = time.strftime(...)  ❌ 每次取当前时间
        │
        └── 消息中：事件ID = 重新生成的ID，告警时间 = 消息发送时间
```

## Goals / Non-Goals

**Goals:**

1. 钉钉消息中的事件ID与数据库 `alert_event.event_id` 完全一致
2. 同一事件所有上报级别的"告警时间"保持不变（使用事件真实发生时间）
3. 逐级上报消息中增加"上报时间"字段，显示本次消息发送时间
4. 长按回复匹配到的事件ID可直接在数据库中查到对应告警记录

**Non-Goals:**

- 不修改 `EventState` 的事件ID生成逻辑（UUID 格式已经是正确的）
- 不修改 `EventState` 的 `occurred_at` 生成逻辑
- 不修改 `alert_client.map_event_to_alert()` 的映射逻辑（已经正确传递 event_id 和 occurred_at）
- 不修改 SpringBoot 端的告警入库逻辑
- 不修改钉钉 Stream 回复处理逻辑（`AlertHandler` 按 event_id 匹配的逻辑已正确，只是之前匹配到的是假 ID）

## Decisions

| 决策                 | 选择                                               | 理由                                                             |
| -------------------- | -------------------------------------------------- | ---------------------------------------------------------------- |
| event_id 来源        | 从 `event` 字典传入，不再自行生成                  | 数据库中的 event_id 由 `EventState` 生成，钉钉消息必须使用同一个 |
| occurred_at 传入方式 | 作为 `trigger_alert` 和 `_step` 的参数一路传递     | 与 event_id 的传递模式一致，最小改动                             |
| 告警时间显示         | 使用 `occurred_at`（ISO 8601 格式转换为可读格式）  | 这是事件真实发生时间，与数据库 `occurred_at` 一致                |
| 上报时间显示         | 新增"上报时间"字段，取 `time.strftime()` 当前时间  | 逐级上报时用户需要知道本次通知是什么时候发出的                   |
| occurred_at 格式转换 | ISO 8601 → `YYYY-MM-DD HH:MM:SS`                   | 钉钉消息中的时间格式应与现有风格一致                             |
| trigger_alert 兼容性 | `event_id` 和 `occurred_at` 参数设为可选，有默认值 | 避免其他调用点（如测试脚本）需要修改                             |

## Architecture

### 改动前

```
push_alert(event)
    │ event = {event_id: "evt_uuid", occurred_at: "2026-07-15T10:00:00+08:00", ...}
    │
    ├── POST /alerts/ai  →  payload.event_id = "evt_uuid"  ✅
    │
    └── self.dingtalk("明火检测 | 摄像头：c01", snapshot=...)
            │  ❌ event_id 和 occurred_at 丢失
            ▼
    trigger_alert(msg, start, snapshot)
        │ event_id = f"evt_{timestamp}_{tid}"  ❌ 新ID
        ▼
    _step(msg, event_id, ch, idx, snapshot)
        │ now = time.strftime(...)  ❌ 每次取当前时间
        │
        └── 消息：事件ID=假ID, 告警时间=发送时间
```

### 改动后

```
push_alert(event)
    │ event = {event_id: "evt_uuid", occurred_at: "2026-07-15T10:00:00+08:00", ...}
    │
    ├── POST /alerts/ai  →  payload.event_id = "evt_uuid"  ✅
    │
    └── self.dingtalk("明火检测 | 摄像头：c01", snapshot=..., event_id="evt_uuid", occurred_at="2026-07-15T10:00:00+08:00")
            │  ✅ event_id 和 occurred_at 一路传递
            ▼
    trigger_alert(msg, start, snapshot, event_id="evt_uuid", occurred_at="2026-07-15T10:00:00+08:00")
        │ event_id = event_id  ✅ 使用传入的ID
        ▼
    _step(msg, event_id, ch, idx, snapshot, occurred_at="2026-07-15T10:00:00+08:00")
        │ alert_time = _format_occurred_at(occurred_at)  ✅ 事件发生时间
        │ report_time = time.strftime(...)  ✅ 本次上报时间
        │
        └── 消息：事件ID=真实ID, 告警时间=事件发生时间, 上报时间=发送时间
```

## 详细设计

### 1. trigger_alert 签名扩展

**文件**：`backend_ai/services/dingtalk_service.py`

```python
# 改动前
def trigger_alert(msg: str, start: str | None = None, snapshot: str = ""):
    event_id = f"evt_{int(time.time())}_{threading.get_ident()}"

# 改动后
def trigger_alert(msg: str, start: str | None = None, snapshot: str = "",
                  event_id: str | None = None, occurred_at: str | None = None):
    if not event_id:
        event_id = f"evt_{int(time.time())}_{threading.get_ident()}"
```

- `event_id` 可选，默认 `None`。为 `None` 时 fallback 到原逻辑（兼容测试脚本等直接调用场景）
- `occurred_at` 可选，默认 `None`。为 `None` 时 `_step` 中"告警时间" fallback 到取当前时间

### 2. \_step 签名扩展

**文件**：`backend_ai/services/dingtalk_service.py`

```python
# 改动前
def _step(msg: str, event_id: str, ch: list, idx: int, snapshot: str = ""):

# 改动后
def _step(msg: str, event_id: str, ch: list, idx: int, snapshot: str = "",
          occurred_at: str | None = None):
```

### 3. \_step 内部时间逻辑

```python
# 改动前
now = time.strftime("%Y-%m-%d %H:%M:%S")
# 消息中：f"告警时间：{now}"

# 改动后
from datetime import datetime

def _format_occurred_at(iso_str: str) -> str:
    """将 ISO 8601 时间转为 'YYYY-MM-DD HH:MM:SS' 格式"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return iso_str

alert_time = _format_occurred_at(occurred_at) if occurred_at else time.strftime("%Y-%m-%d %H:%M:%S")
report_time = time.strftime("%Y-%m-%d %H:%M:%S")
```

### 4. 消息模板调整

三级消息中，"告警时间"统一使用 `alert_time`，新增"上报时间"使用 `report_time`：

**首次通知（idx == 0）**：无"上报时间"（首次即告警时间）

```python
text_content = (
    f"【告警通知】检测到异常事件\n\n"
    f"告警内容：{msg}\n"
    f"告警时间：{alert_time}\n"
    f"接收人：{p['name']}\n"
    f"回复「已处理」停止上报\n"
    f"超时处理：将自动上报至直属上级\n\n"
    f"事件ID：{event_id}"
)
```

**告警升级（idx > 0 且非最后）**：

```python
content = (
    f"【告警升级】{prev} 未在规定时间内响应\n\n"
    f"告警内容：{msg}\n"
    f"告警时间：{alert_time}\n"
    f"上报时间：{report_time}\n"
    f"原始接收人：{ch[0]['name']}\n"
    f"当前接收人：{p['name']}\n"
    f"请立即处理，回复「已处理」停止上报\n\n"
    f"事件ID：{event_id}"
)
```

**紧急升级（last）**：

```python
content = (
    f"【紧急升级】已逐级上报，无人响应\n\n"
    f"告警内容：{msg}\n"
    f"告警时间：{alert_time}\n"
    f"上报时间：{report_time}\n"
    f"当前状态：未处理\n"
    f"操作建议：请立即响应\n\n"
    f"事件ID：{event_id}\n\n"
    f"@全体成员"
)
```

### 5. 定时器回调传递 occurred_at

```python
# 改动前
def check():
    if event_id in _stopped:
        logger.info("已停止上报: %s", msg)
        return
    _step(msg, event_id, ch, idx + 1)

# 改动后
def check():
    if event_id in _stopped:
        logger.info("已停止上报: %s", msg)
        return
    _step(msg, event_id, ch, idx + 1, occurred_at=occurred_at)
```

注意：`snapshot` 只在首次通知时发送，逐级上报不重复发截图，所以 `check()` 调用 `_step` 时不传 `snapshot`（默认空字符串），这与现有行为一致。

### 6. alert_client.push_alert 传参

**文件**：`backend_ai/services/alert_client.py`

```python
# 改动前
self.dingtalk(f"{alert_name} | 摄像头：{stream}", snapshot=local_snapshot)

# 改动后
self.dingtalk(
    f"{alert_name} | 摄像头：{stream}",
    snapshot=local_snapshot,
    event_id=event.get("event_id"),
    occurred_at=event.get("occurred_at"),
)
```

## 影响模块

### backend_ai（Python）

| 文件                           | 改动                                                                                                                                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/dingtalk_service.py` | `trigger_alert` 新增 `event_id`、`occurred_at` 参数；`_step` 新增 `occurred_at` 参数；新增 `_format_occurred_at` 辅助函数；消息模板中"告警时间"改用 `alert_time`，升级消息新增"上报时间" |
| `services/alert_client.py`     | `push_alert()` 中 `self.dingtalk()` 调用新增 `event_id` 和 `occurred_at` 关键字参数                                                                                                      |

## Risks

- `trigger_alert` 的调用方除了 `alert_client` 外，可能还有测试脚本直接调用。新增参数均为可选且有默认值，不影响现有调用
- `_format_occurred_at` 对非法格式会 fallback 返回原始字符串，不会导致消息发送失败
