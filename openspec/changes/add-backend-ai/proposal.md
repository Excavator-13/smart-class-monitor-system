# AI 服务端核心分析能力

## Why

智慧教室实时行为分析与安全监测系统需要一个独立的 Flask AI 服务端，负责接入实时视频流、执行视觉分析、输出带标注视频画面，并将异常事件与 SpringBoot 管理端打通。

当前项目已经明确前端、SpringBoot 管理端、Nginx RTMP 与 AI 服务端之间的调用关系，但 AI 服务端核心能力尚未形成可实施的 OpenSpec 变更文档。需要先沉淀服务边界、接口行为、检测能力和联调顺序，避免后续实现时出现职责混乱、事件字段不一致或告警重复入库。

## What Changes

- 新增 Flask AI 服务端基础能力：
  - 拉取 Nginx RTMP 视频流并维护帧缓存。
  - 提供 `/video_feed/{stream_id}` MJPEG 视频流，返回 AI 标注后的实时画面。
  - 提供 `/model/status` 查询服务、模型和视频源状态。
  - 提供 `/analysis/events` 查询 AI 内存中的实时候选事件。
- 新增人脸识别能力：
  - 使用 OpenCV + InsightFace/ArcFace 提取 512 维人脸特征。
  - 支持 `/face/feature/extract` 供 SpringBoot 在人脸注册流程中调用。
  - 支持启动加载、定时拉取和 `/face/features/reload` 刷新人脸特征库。
- 新增危险区域检测能力：
  - 从 SpringBoot 拉取视频源、危险区域和规则配置。
  - 支持危险区域进入、停留超时和接近预警检测。
- 新增目标行为检测能力：
  - 支持长时间低头、异常人流聚集和使用手机检测。
  - 基于规则阈值、持续时间和冷却时间生成候选事件。
- 新增事件与告警联动能力：
  - AI 服务内部维护候选事件，前端可轮询展示。
  - 候选事件满足确认条件后，调用 SpringBoot `/alerts/ai` 入库为正式告警。
  - 区分候选事件 `event_status` 与正式告警 `alert_status`。
- 明确本次不实现：
  - 明火检测。
  - 活体检测、防欺骗认证。
  - 摔倒检测。
  - 异常声学事件检测。
  - 人员轨迹存储与轨迹查询。
  - 钉钉通知。
  - AI 日报生成。

## Capabilities

- 新增 `ai-analysis-service`：AI 服务端实时视频分析、事件生成、告警入库和状态查询能力。

## Impact

- 影响代码目录：
  - `backend_ai/app.py`
  - `backend_ai/config/`
  - `backend_ai/services/`
  - `backend_ai/utils/`
  - `backend_ai/static/snapshots/`
  - `backend_ai/tests/`
  - `backend_ai/requirements.txt`
- 影响 AI 服务端对外接口：
  - `GET /video_feed/{stream_id}`
  - `GET /analysis/events`
  - `GET /model/status`
  - `POST /face/feature/extract`
  - `POST /face/features/reload`
  - `POST /config/reload`
- 依赖 SpringBoot 管理端接口：
  - `POST /alerts/ai`
  - `GET /streams`
  - `GET /zones?stream_id=...`
  - `GET /rules`
  - `GET /students/face-features`
- 运行环境基线：
  - Conda env: `classroom-ai-gpu`
  - Python 3.10.20
  - Flask 3.1.3
  - pytest
  - OpenCV 5.0.0.93
  - ultralytics 8.4.90
  - insightface 1.0.1
  - onnxruntime-gpu 1.23.2
  - torch 2.11.0+cu128
  - GPU: NVIDIA GeForce RTX 5060 Laptop GPU
