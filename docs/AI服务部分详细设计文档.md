# AI服务详细设计文档

# AI 服务部分详细设计文档

版本：V0\.1

日期：2026\-07\-07

---

## 1\. 文档目的

本文档面向 AI 分析服务开发，基于当前前端接口记录、模块依赖调用说明以及项目概要设计，对 AI 服务的功能边界、模块划分、数据流、接口协作、核心算法流程和联调约定进行详细设计。

AI 服务当前需要重点实现四类能力：

1. 人脸识别：人脸检测、特征提取、身份识别、陌生人检测。

2. 危险区域检测：支持前端/管理端配置危险区域，当人员进入或停留超时触发告警。

3. 目标行为检测：识别使用手机等课堂异常行为，并结合时间窗口触发告警。

4. 明火检测：识别明火/疑似火焰目标，并生成安全告警。

---

## 2\. 与现有前端/后端设计的对齐结论

### 2\.1 服务边界

|服务|默认端口|前端环境变量|主要职责|
|---|---|---|---|
|Vue 前端|5173/8081 等|\-|页面展示、视频播放、区域绘制、告警查询、人员注册入口|
|Flask AI 服务|5000|`VITE_AI_BASE`|视频拉流、模型推理、画框标注、实时候选事件输出、人脸特征提取|
|SpringBoot 管理端|8080|`VITE_API_BASE`|用户、人员、视频源、规则、区域、告警、统计、数据库持久化|
|Nginx RTMP/静态资源|9090/9092|`VITE_NGINX_BASE`|RTMP 推拉流、截图/录像静态访问|

### 2\.2 AI 服务与其他模块的调用关系

```Plaintext
flowchart LR
    A["摄像头 / OBS / 手机推流"] -->|RTMP| B["Nginx RTMP 服务<br/>9090"]
    B -->|cv2.VideoCapture 拉流| C["Flask AI 分析服务<br/>5000"]
    C -->|MJPEG 处理后视频流| D["Vue 前端"]
    C -->|候选事件 / 模型状态| D
    D -->|区域/规则/告警查询| E["SpringBoot 管理端<br/>8080"]
    E -->|读取/写入| F["MySQL"]
    C -->|告警事件入库| E
    E -->|人脸注册时请求特征提取| C
    C -->|截图文件路径| G["Nginx 静态资源<br/>9092"]
    D -->|查看截图/录像| G
```

### 2\.3 前端联调原则

前端不应硬编码服务 IP，应通过 `.env` 配置：

```Plaintext
VITE_API_BASE=http://39.106.209.208:8080
VITE_AI_BASE=http://39.106.209.208:5000
VITE_NGINX_BASE=http://39.106.209.208:9092
```

前端页面中：

- 实时视频展示使用 `VITE_AI_BASE + /video_feed/{stream_id}`。

- 实时 AI 候选事件可轮询 `VITE_AI_BASE + /analysis/events`。

- 告警列表、告警状态、人员信息、区域配置、规则配置走 SpringBoot。

- 告警截图和录像 URL 由 SpringBoot 返回相对路径，前端拼接 `VITE_NGINX_BASE` 访问。

---

## 3\. AI 服务总体设计

### 3\.1 技术栈

|类型|技术|
|---|---|
|语言环境|Python 3\.8|
|Web 框架|Flask，统一封装 AI 服务对外接口|
|视频处理|OpenCV|
|人脸识别|OpenCV \+ InsightFace|
|目标检测|YOLO|
|数据交互|HTTP REST、MJPEG Streaming，后续可扩展 WebSocket|
|配置管理|YAML/JSON 配置 \+ 从 SpringBoot 拉取规则/区域配置|

### 3\.2 AI 服务职责

AI 服务只负责“非结构化视频分析能力”，不负责用户体系和业务数据持久化。

具体职责包括：

- 从 Nginx RTMP 服务读取视频流。

- 按配置进行抽帧、缩放、模型推理。

- 对视频帧进行人脸框、人员框、危险区域、行为标签、火焰标签等可视化标注。

- 向前端提供处理后 MJPEG 视频流。

- 向前端提供实时候选事件列表。

- 在确认异常后调用 SpringBoot 告警入库接口。

- 在人脸注册流程中被 SpringBoot 调用，提取人脸特征向量并返回。

### 3\.3 不属于 AI 服务的职责

以下能力由 SpringBoot 或前端承担：

- 用户登录、鉴权、权限管理。

- 人员信息 CRUD。

- 区域规则配置 CRUD。

- 告警记录长期存储和状态流转。

- 视频源管理。

- 告警统计。

- 页面展示、表单交互、ROI 区域绘制。

---

## 4\. AI 服务内部模块划分

```Plaintext
flowchart TB
    A["app.py / Flask 路由层"] --> B["StreamManager 视频流管理"]
    A --> C["AnalysisService 分析编排"]
    A --> D["FaceService 人脸识别"]
    A --> E["ZoneService 危险区域检测"]
    A --> F["BehaviorService 目标行为检测"]
    A --> G["FireService 明火检测"]
    C --> H["EventService 事件聚合与去重"]
    H --> I["AlertClient 调 SpringBoot 入库"]
    C --> J["ConfigClient 拉取区域/规则/人员特征"]
    B --> K["FrameReader OpenCV 拉流"]
    C --> L["Annotator 画框标注"]
```

### 4\.1 Flask 路由层

负责接收前端和 SpringBoot 的 HTTP 请求，对外暴露：

- 视频流接口。

- 实时事件接口。

- 模型状态接口。

- 人脸特征提取接口。

- 配置刷新接口。

路由层不直接写复杂算法逻辑，只做参数校验、调用服务、统一返回。

### 4\.2 StreamManager 视频流管理模块

职责：

- 根据 `stream_id` 获取 RTMP 地址。

- 使用 `cv2.VideoCapture` 拉取视频帧。

- 维护流状态：在线、断流、重连中、错误。

- 支持分辨率缩放、跳帧、帧率统计、延迟估计。

建议参数：

|参数|默认值|说明|
|---|---|---|
|`target_width`|640|分析帧宽度，性能不足时可降到 480|
|`target_height`|480|分析帧高度|
|`frame_skip`|3\-5|每 N 帧分析一次|
|`reconnect_interval`|3 秒|断流重连间隔|
|`jpeg_quality`|70|MJPEG 输出 JPEG 质量|

### 4\.3 AnalysisService 分析编排模块

职责：

1. 接收视频帧。

2. 调用人脸识别、目标检测、危险区域、行为检测、明火检测模块。

3. 汇总检测结果。

4. 调用事件聚合模块进行时间窗口判断。

5. 调用标注模块绘制画面。

6. 输出前端可展示的视频帧与事件数据。

---

## 5\. 四个核心功能模块详细设计

## 5\.1 人脸识别模块

### 5\.1\.1 功能目标

- 支持人脸注册时使用 InsightFace 提取人脸 embedding（常见为 512 维，具体维度以所选模型输出为准）。

- 支持实时视频中的人脸检测与身份识别。

- 对未匹配到人员库的人脸标记为陌生人。

### 5\.1\.2 输入输出

|类型|内容|
|---|---|
|输入|视频帧、注册图片、人员特征库、识别阈值|
|输出|人脸框、人脸 ID、姓名/编号、匹配距离、是否陌生人、候选事件|

### 5\.1\.3 注册流程

```Plaintext
sequenceDiagram
    participant F as Vue 前端
    participant S as SpringBoot
    participant A as Flask AI
    participant DB as MySQL

    F->>S: POST /students/{id}/face(image)
    S->>A: POST /ai/face/feature/extract(image)
    A->>A: 检测人脸数量
    A->>A: 使用 InsightFace 提取人脸 embedding
    A-->>S: 返回 feature_vector / quality
    S->>DB: 保存人员与人脸特征
    S-->>F: 返回注册结果
```

### 5\.1\.4 实时识别流程

1. 从视频帧中检测人脸。

2. 使用 OpenCV 完成图像预处理，并通过 InsightFace 提取人脸 embedding。

3. 与本地缓存的人脸特征库进行距离计算。

4. 距离小于阈值则认为匹配成功。

5. 未匹配则标记为 `Stranger`。

6. 连续出现超过阈值时生成 `stranger_detected` 告警。

### 5\.1\.5 特征库同步策略

初版实现：

- 前端上传照片，调用Flask提取人脸512维特征（初次注册）

- Flask调用springboot接口，将特征json文件写入数据库

- Flask 启动时调用 SpringBoot 获取全部已注册人脸特征。

- Flask 缓存到内存，格式为 `student_id -> feature_vector[]`。

- SpringBoot 完成人脸注册后，可调用 Flask `/face/features/reload` 通知刷新。

后续优化：

- 支持定时刷新。

- 支持按班级/课程加载。

- 支持多张特征向量取最小距离或平均距离。

---

## 5\.2 危险区域检测模块

### 5\.2\.1 功能目标

管理员可在前端绘制危险区域或限制区域，例如讲台设备区、实验器材区、门口禁入区等。当人员进入该区域，或停留时间超过阈值时，系统触发告警。

### 5\.2\.2 区域数据来源

区域由前端在“区域与规则配置页面”绘制，经 SpringBoot 保存到 MySQL。AI 服务从 SpringBoot 拉取区域配置。

区域建议数据结构：

```JSON
{
  "zone_id": 1,
  "stream_id": "classroom_01",
  "zone_name": "讲台设备危险区",
  "zone_type": "danger",
  "shape": "polygon",
  "coordinates": [
    {"x": 0.12, "y": 0.20},
    {"x": 0.35, "y": 0.20},
    {"x": 0.35, "y": 0.55},
    {"x": 0.12, "y": 0.55}
  ],
  "threshold_seconds": 2,
  "enabled": true
}
```

说明：

- 坐标建议使用归一化坐标，范围 0\-1，避免前端显示尺寸和后端分析尺寸不一致。

- 如果前端暂时只支持矩形，也可用 polygon 的四个点表示。

### 5\.2\.3 检测逻辑

1. YOLO 或人员检测模型输出 `person` 目标框。

2. 取人员框底部中心点作为“脚点”。

3. 判断脚点是否落入危险区域 polygon。

4. 对同一目标维护进入时间。

5. 如果进入时间超过阈值，生成 `danger_zone_intrusion` 事件。

### 5\.2\.4 去重策略

为避免同一人连续触发大量告警：

- 同一 `stream_id + zone_id + track_id` 在 `cooldown_seconds` 内只生成一次告警。

- 初版没有目标跟踪时，可用目标框中心点近似匹配。

---

## 5\.3 目标行为检测模块：使用手机等行为

### 5\.3\.1 功能目标

识别课堂中的违规使用手机等行为，输出实时标签并在持续时间超过阈值时触发告警。

### 5\.3\.2 初版检测策略

推荐初版采用“目标检测 \+ 空间关系 \+ 时间窗口”方案：

1. YOLO 检测 `person` 和 `cell phone`。

2. 判断手机框是否与人员框存在包含、重叠或近距离关系。

3. 判断手机是否位于人体上半身/手部附近区域。

4. 连续多帧满足条件，累计持续时间。

5. 超过阈值后生成 `phone_usage` 告警。

### 5\.3\.3 可扩展行为类型

|行为类型|event\_type|初版可行方案|后续优化|
|---|---|---|---|
|使用手机|`phone_usage`|YOLO 检测手机 \+ 人员关联|姿态估计 \+ 手部检测|
|长时间低头|`head_down`|人脸/头部角度近似判断|姿态估计或专用分类模型|
|长时间离座|`leave_seat`|座位区域内人员缺失持续时间|人员跟踪 \+ 座位绑定|
|异常聚集|`abnormal_gathering`|区域内人数超过阈值|轨迹分析|

本文档当前开发重点为“使用手机”，可扩展行为类型后续再实现。

---

## 5\.4 明火检测模块

### 5\.4\.1 功能目标

识别教室或实验场景中出现的明火、火焰或疑似烟火风险，并生成高等级安全告警。

### 5\.4\.2 初版检测策略

推荐优先使用 YOLO 明火检测模型：

- 类别：`fire`、`flame`，后续可扩展 `smoke`。

- 输出火焰框、置信度、位置。

- 置信度超过阈值且连续 N 帧出现时触发告警。

如果暂时没有明火模型，可采用降级方案：

- 基于颜色阈值提取红/橙/黄色高亮区域。

- 结合形态变化和面积阈值判断疑似火焰。

- 该方案误报较高，只建议用于原型演示或兜底提示，不建议作为正式判断依据。

### 5\.4\.3 告警等级

明火检测建议默认高优先级：

|条件|告警等级|
|---|---|
|明火置信度 ≥ 0\.70，持续 ≥ 1 秒|高|
|明火置信度 0\.50\-0\.70，持续 ≥ 2 秒|中|
|颜色阈值疑似火焰|低/待确认|

---

## 6\. 事件与告警设计

### 6\.1 候选事件与正式告警的区别

|类型|存储位置|用途|
|---|---|---|
|候选事件 candidate event|AI 服务内存缓存|前端实时展示，可能还未达到告警阈值|
|正式告警 alert event|SpringBoot \+ MySQL|已满足触发条件，需要追踪、查询、处理|

### 6\.2 事件类型枚举

|event\_type|中文名称|来源模块|默认等级|
|---|---|---|---|
|`face_recognized`|已识别人员|人脸识别|info|
|`stranger_detected`|陌生人出现|人脸识别|warning|
|`danger_zone_intrusion`|危险区域入侵|危险区域|warning/high|
|`phone_usage`|使用手机|行为检测|warning|
|`head_down`|长时间低头|行为检测扩展|warning|
|`leave_seat`|长时间离座|行为检测扩展|warning|
|`flame_detected`|明火检测|明火检测|high|
|`stream_offline`|视频流中断|视频流管理|warning|

### 6\.3 统一事件结构

```JSON
{
  "event_id": "evt_20260707102030001",
  "stream_id": "classroom_01",
  "event_type": "phone_usage",
  "event_name": "使用手机",
  "level": "warning",
  "status": "candidate",
  "confidence": 0.86,
  "occurred_at": "2026-07-07T10:20:30+08:00",
  "duration_seconds": 3.2,
  "target": {
    "track_id": "person_3",
    "student_id": "2024001",
    "student_name": "张三",
    "bbox": [120, 80, 260, 420]
  },
  "zone": {
    "zone_id": 2,
    "zone_name": "讲台设备危险区"
  },
  "snapshot_path": "/snapshots/20260707/evt_20260707102030001.jpg",
  "extra": {
    "model": "yolo-phone-v1",
    "rule": "phone_usage_duration"
  }
}
```

### 6\.4 告警推送 SpringBoot

AI 服务确认告警后，调用 SpringBoot 内部接口入库。建议接口为：

```HTTP
POST {VITE_API_BASE 或配置项 SPRING_API_BASE}/alerts
Content-Type: application/json
```

SpringBoot 负责保存并返回告警 ID。前端仍通过 SpringBoot `/alerts` 查询正式告警。

---

## 7\. 配置与规则设计

### 7\.1 规则来源

规则由 SpringBoot 管理，AI 服务启动或刷新时拉取。

建议规则结构：

```JSON
{
  "rule_type": "phone_usage",
  "enabled": true,
  "threshold_seconds": 3,
  "confidence_threshold": 0.6,
  "cooldown_seconds": 30,
  "config_json": {
    "need_person_phone_relation": true
  }
}
```

### 7\.2 推荐默认阈值

|规则|threshold\_seconds|confidence\_threshold|cooldown\_seconds|
|---|---|---|---|
|陌生人检测|2|0\.60|30|
|危险区域入侵|2|0\.50|30|
|使用手机|3|0\.60|45|
|明火检测|1|0\.70|60|

---

## 8\. 截图与录像文件设计

### 8\.1 截图保存

AI 服务在触发正式告警时保存当前帧截图。

建议路径：

```Plaintext
/usr/local/rtmp_video/snapshots/{yyyyMMdd}/{event_id}.jpg
```

数据库中保存相对路径：

```Plaintext
/snapshots/20260707/evt_20260707102030001.jpg
```

前端展示时：

```Plaintext
VITE_NGINX_BASE + snapshot_path
```

### 8\.2 录像片段

初版可先依赖 Nginx RTMP 自动录像文件，不强制由 AI 服务切片。AI 服务告警入库时可记录：

- `record_file_path`：告警所在录像文件。

- `event_time_offset`：事件在录像中的时间位置。

后续可扩展为告警前后 10 秒视频片段。

---

## 9\. 异常处理与降级策略

|场景|处理策略|
|---|---|
|RTMP 拉流失败|返回断流状态，前端显示视频源异常；后台定时重连|
|模型加载失败|`/ai/model/status` 返回 `degraded` 或 `error`，禁用对应检测模块|
|SpringBoot 不可用|候选事件仍可前端展示，正式告警暂存本地队列，恢复后补偿入库|
|人脸特征库为空|人脸框仍显示，身份均标记为 unknown/stranger|
|YOLO 模型不可用|禁用目标行为、明火、危险区域人员检测，保留视频流和人脸功能|

---

## 10\. 开发优先级建议

### 第一阶段：联调基础链路

- 跑通 `/video_feed/{stream_id}`。

- 前端 `<img>` 能显示处理后视频流。

- `/model/status` 能返回 AI 服务状态。

- `/analysis/events` 能返回 mock 或基础事件。

### 第二阶段：人脸识别

- 实现 `/face/feature/extract`。

- 完成 SpringBoot 调 Flask 提取特征。

- Flask 能加载人员特征库并实时识别。

### 第三阶段：危险区域

- SpringBoot 保存区域配置。

- Flask 拉取区域配置。

- 视频中绘制区域和人员框。

- 人员进入区域触发候选事件和正式告警。

### 第四阶段：手机行为与明火检测

- 接入 YOLO 目标检测。

- 实现 `phone_usage`、`flame_detected` 检测规则。

- 告警截图保存并入库。

### 第五阶段：优化与展示

- 增加事件去重、冷却时间、统计摘要。

- 可选接入 WebSocket。

- 优化模型性能和误报率。

---

## 11\. 目录结构建议

```Plaintext
backend-ai/
  app.py    #Flask主程序
  config/    #配置文件
    app.yaml
    model.yaml
  services/
    stream_manager.py    #视频拉流
    analysis_service.py    #分析
    face_service.py    #人脸识别
    zone_service.py    #危险区域识别
    behavior_service.py    #目标行为检测（使用手机）
    fire_service.py    #明火检测
    event_service.py
    alert_client.py    #调springboot入库
    config_client.py    #拉取前端配置（对危险区域的配置等）
  models/
    face/
    yolo/
  utils/
    geometry.py
    image_utils.py
    response.py
    logger.py
  static/
    snapshots/
  requirements.txt
```

---

