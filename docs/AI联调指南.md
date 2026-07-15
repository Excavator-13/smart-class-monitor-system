# AI模块与云服务器推拉流联调指南

## 前置准备

### 1. 启动服务

```bash
# 终端1：启动 mock_springboot（端口 8080）
cd mock_springboot
pip install flask pyyaml python-dotenv
python app.py

# 终端2：启动 backend_ai（端口 5000）
cd backend_ai
pip install -r requirements.txt
python app.py
```

### 2. 环境变量确认

| 服务 | 变量 | 默认值 | 说明 |
| --- | --- | --- | --- |
| backend_ai | `SPRING_BASE_URL` | `http://localhost:8080` | mock服务地址 |
| mock_springboot | `RTMP_BASE_URL` | `localhost` | mock_data.yaml中推流地址占位 |

联调云服务器时，将 `RTMP_BASE_URL` 改为云服务器RTMP地址（如 [`your-server.com`](http://your-server.com)），将 mock_data.yaml 中的 `rtmp_url` 配置为实际的RTMP拉流地址。

***

## 一、AI模块接口（Postman / 浏览器）

### 1.1 GET `/model/status` — 服务与模型状态

- **方式**：Postman GET
- **URL**：[`http://localhost:5000/model/status`](http://localhost:5000/model/status)
- **正常返回**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "service_status": "running",
    "models": [
      {
        "module": "face",
        "loaded": false,
        "model_name": "insightface",
        "version": "v1",
        "avg_infer_ms": null
      },
      {
        "module": "zone",
        "loaded": true,
        "model_name": "rule",
        "version": "v1",
        "avg_infer_ms": null
      },
      {
        "module": "behavior",
        "loaded": false,
        "model_name": "ultralytics",
        "version": "v1",
        "avg_infer_ms": null
      },
      {
        "module": "fire",
        "loaded": false,
        "model_name": "reserved",
        "version": "not_in_scope",
        "avg_infer_ms": null
      }
    ],
    "streams": []
  },
  "timestamp": "2026-07-09T10:00:00+08:00",
  "trace_id": "req_..."
}
```

> `streams` 数组在未加载流配置时为空，执行 `/config/reload` 后会填充。

***

### 1.2 POST `/config/reload` — 重载配置

AI模块启动时不会自动拉取配置，需手动触发。首次联调**必须先调用此接口**。

- **方式**：Postman POST
- **URL**：[`http://localhost:5000/config/reload`](http://localhost:5000/config/reload)
- **Content-Type**：`application/json`
- **请求体**：

```json
{
  "stream_id": null,
  "reload_items": ["streams", "zones", "rules"]
}
```

| 参数 | 说明 |
| --- | --- |
| `stream_id` | 指定流ID则只加载该流的区域，`null`加载全部 |
| `reload_items` | 可选子集：`streams`、`zones`、`rules`，默认全部 |

- **正常返回**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "stream_id": null,
    "updated_at": 1720490400.0,
    "streams_loaded": 1,
    "zones_loaded": 1,
    "rules_loaded": 1
  },
  "timestamp": "2026-07-09T10:00:00+08:00",
  "trace_id": "req_..."
}
```

***

### 1.3 POST `/face/features/reload` — 重载人脸特征库

- **方式**：Postman POST
- **URL**：[`http://localhost:5000/face/features/reload`](http://localhost:5000/face/features/reload)
- **Content-Type**：`application/json`
- **请求体**：

```json
{
  "scope": "all",
  "student_id": null
}
```

| 参数 | 说明 |
| --- | --- |
| `scope` | `all`加载全部，`single`加载指定学生 |
| `student_id` | scope为`single`时必填 |

- **正常返回**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "loaded_count": 0,
    "updated_at": 1720490400.0
  },
  "timestamp": "...",
  "trace_id": "req_..."
}
```

> mock_springboot 的 `/students/face-features` 默认返回空列表，`loaded_count` 为 0 属正常。

***

### 1.4 POST `/face/feature/extract` — 提取人脸特征

- **方式**：Postman POST
- **URL**：[`http://localhost:5000/face/feature/extract`](http://localhost:5000/face/feature/extract)
- **Content-Type**：`application/json`
- **请求体**：

```json
{
  "image": "<base64编码的图片>",
  "student_id": "stu_001"
}
```

| 参数 | 说明 |
| --- | --- |
| `image` | base64图片字符串，支持带`data:image/...;base64,`前缀 |
| `student_id` | 可选，回显在返回中 |

- **正常返回**（无人脸模型时使用OpenCV Haar级联降级检测）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "face_count": 1,
    "feature_dim": 512,
    "feature_vector": [0.0, 0.12, ...],
    "quality": { "score": 1.0, "brightness": "unknown", "blur": "unknown" },
    "bbox": [100, 200, 300, 400],
    "student_id": "stu_001"
  },
  "timestamp": "...",
  "trace_id": "req_..."
}
```

- **异常返回**：

| code | message | 场景 |
| --- | --- | --- |
| 40001 | invalid image | 图片base64无效 |
| 40002 | no face detected | 图片中无人脸 |
| 40003 | multiple faces detected | 检测到多张人脸 |

***

### 1.5 GET `/analysis/events` — 查询事件

- **方式**：Postman GET
- **URL**：[`http://localhost:5000/analysis/events`](http://localhost:5000/analysis/events)
- **查询参数**：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `stream_id` | string | 全部 | 按流ID过滤 |
| `event_type` | string | 全部 | 按事件类型过滤 |
| `level` | string | 全部 | 按级别过滤（info/warning/high） |
| `limit` | int | 20 | 返回条数，1~200 |
| `since` | string | 无 | ISO时间，返回此时间之后的事件 |

- **示例**：[`http://localhost:5000/analysis/events?stream_id=classroom_01&limit=10`](http://localhost:5000/analysis/events?stream_id=classroom_01&limit=10)
- **正常返回**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "event_id": "evt_a1b2c3d4e5f67890",
        "stream_id": "classroom_01",
        "event_type": "stranger_detected",
        "event_name": "陌生人出现",
        "level": "warning",
        "event_status": "candidate",
        "confidence": 0.0,
        "occurred_at": "2026-07-09T10:05:00+08:00",
        "duration_seconds": 0.0,
        "target": { "track_id": "face_1", "bbox": [100, 200, 300, 400] },
        "zone": null,
        "snapshot_path": null
      }
    ]
  },
  "timestamp": "...",
  "trace_id": "req_..."
}
```

***

### 1.6 GET `/video_feed/<stream_id>` — 实时视频流（浏览器访问）

- **方式**：浏览器直接访问
- **URL**：[`http://localhost:5000/video_feed/classroom_01`](http://localhost:5000/video_feed/classroom_01)
- **查询参数**：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `annotate` | `true` | 是否叠加检测标注，设为`false`则返回原始画面 |
| `modules` | `all` | 启用的分析模块，逗号分隔，如`face,zone` |

- **示例**：

    - 带标注：[`http://localhost:5000/video_feed/classroom_01`](http://localhost:5000/video_feed/classroom_01)
    - 仅区域检测：[`http://localhost:5000/video_feed/classroom_01?modules=zone`](http://localhost:5000/video_feed/classroom_01?modules=zone)
    - 原始画面：[`http://localhost:5000/video_feed/classroom_01?annotate=false`](http://localhost:5000/video_feed/classroom_01?annotate=false)

- **正常表现**：浏览器显示MJPEG实时视频画面
- **流不在线时**：显示黑底白字 "stream offline"
- **流ID不存在时**：返回JSON错误：

```json
{
  "code": 40401,
  "message": "stream not found",
  "data": null,
  "timestamp": "...",
  "trace_id": "req_..."
}
```

***

## 二、Mock SpringBoot 接口（AI模块内部调用，可单独验证）

以下接口由AI模块的 `ConfigClient` / `AlertClient` 内部调用。联调时可先用Postman单独验证mock服务是否正常。

### 2.1 GET `/streams` — 获取流列表

- **URL**：[`http://localhost:8080/streams`](http://localhost:8080/streams)
- **正常返回**：

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "stream_id": "classroom_01",
        "rtmp_url": "rtmp://localhost/live/classroom_01",
        "name": "教室1",
        "status": "enabled"
      }
    ]
  }
}
```

### 2.2 GET `/zones` — 获取区域配置

- **URL**：[`http://localhost:8080/zones?stream_id=classroom_01`](http://localhost:8080/zones?stream_id=classroom_01)
- **正常返回**：

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "zone_id": "zone_01",
        "stream_id": "classroom_01",
        "name": "讲台区域",
        "polygon": [
          [0.1, 0.1],
          [0.5, 0.1],
          [0.5, 0.5],
          [0.1, 0.5]
        ],
        "enabled": true
      }
    ]
  }
}
```

### 2.3 GET `/rules` — 获取规则配置

- **URL**：[`http://localhost:8080/rules`](http://localhost:8080/rules)
- **正常返回**：

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "rule_type": "zone_intrusion",
        "name": "区域入侵检测",
        "enabled": true,
        "threshold_seconds": 3,
        "confidence_threshold": 0.6
      }
    ]
  }
}
```

### 2.4 GET `/students/face-features` — 获取人脸特征

- **URL**：[`http://localhost:8080/students/face-features`](http://localhost:8080/students/face-features)
- **正常返回**：

```json
{ "code": 0, "data": { "items": [] } }
```

### 2.5 POST `/alerts/ai` — 接收告警

- **URL**：[`http://localhost:8080/alerts/ai`](http://localhost:8080/alerts/ai)
- **Content-Type**：`application/json`
- **说明**：AI模块在事件确认后自动推送，mock服务会在终端打印收到的告警内容
- **正常返回**：

```json
{ "code": 0, "message": "ok" }
```

***

## 三、联调流程

### 步骤1：启动并验证mock服务

```bash
cd mock_springboot && python app.py
```

Postman访问 [`http://localhost:8080/streams`](http://localhost:8080/streams)，确认返回流列表。

### 步骤2：启动AI模块并加载配置

```bash
cd smart-class-monitor-system && python -m backend_ai.app
```

Postman POST [`http://localhost:5000/config/reload`](http://localhost:5000/config/reload)，确认 `streams_loaded ≥ 1`。

### 步骤3：配置云服务器RTMP推流

1. 在云服务器上启动RTMP服务（如 nginx-rtmp），推流到 `rtmp://<服务器>/live/classroom_01`
2. 修改 `mock_springboot/.env` 中 `RTMP_BASE_URL=<服务器地址>`
3. 重启 mock_springboot，再次执行 `/config/reload`

### 步骤4：浏览器查看视频流

浏览器打开 [`http://localhost:5000/video_feed/classroom_01`](http://localhost:5000/video_feed/classroom_01)

- 若RTMP流正常：显示实时画面+检测标注
- 若RTMP流不通：显示 "stream offline"

### 步骤5：验证事件检测与告警推送

1. 浏览器观看视频流，等待检测事件产生
2. Postman GET [`http://localhost:5000/analysis/events?stream_id=classroom_01`](http://localhost:5000/analysis/events?stream_id=classroom_01) 查看事件
3. 观察 mock_springboot 终端是否打印告警日志（事件需持续超过 `threshold_seconds` 且通过冷却期后才会推送）

### 步骤6：验证模型状态

Postman GET [`http://localhost:5000/model/status`](http://localhost:5000/model/status)，确认 `streams` 数组中对应流的 `online` 状态和 `fps`。

***

## 四、事件类型速查

| event_type | event_name | level | 触发条件 |
| --- | --- | --- | --- |
| `face_recognized` | 已识别人员 | info | 人脸匹配特征库且相似度≥阈值 |
| `stranger_detected` | 陌生人出现 | warning | 人脸未匹配特征库 |
| `danger_zone_intrusion` | 危险区域入侵 | warning | 人员脚点在危险区域内 |
| `danger_zone_stay` | 危险区域停留超时 | high | 人员在危险区域内停留超时 |
| `danger_zone_approach` | 危险区域接近预警 | warning | 人员脚点距危险区域<安全距离 |
| `phone_usage` | 使用手机 | warning | 检测到人与手机关联 |
| `head_down` | 长时间低头 | warning | 低头比例超阈值 |
| `crowd_gathering` | 异常人流聚集 | warning | 密集人群超过最小数量 |
| `stream_offline` | 视频流中断 | — | 流读取失败 |

> `phone_usage`、`head_down`、`crowd_gathering` 需要 behavior 模型（ultralytics）加载后才可检测；`face_recognized`/`stranger_detected` 需要 face 模型加载。`danger_zone_*` 系列仅依赖规则引擎，无需额外模型。
