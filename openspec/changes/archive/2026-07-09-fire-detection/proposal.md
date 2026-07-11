# 明火检测模块

## 动机

AI 服务端核心分析能力原设计明确将明火检测列为"预留但不实现"功能（Non-Goal）。当前已完成核心骨架（face/zone/behavior）的建设与联调，视频流框架和事件引擎已就绪。在真实教室场景中，明火是安全威胁级别最高的事件类型，需要独立的 YOLO 模型检测通道，并接入现有的候选事件-确认告警机制。

因此将明火检测从"预留"状态升级为实际实现的功能模块。

## 范围

- **必须实现**：
  - 使用 YOLOv8 模型检测画面中的明火（火焰）
  - 与 `analysis_service` 集成，作为可选检测模块（`modules=fire`）
  - 输出与现有事件系统兼容的 `flame_detected` 事件
  - 置信度阈值、冷却时间、告警分级通过 `model.yaml` 和 SpringBoot 规则配置
  - 模型状态通过 `/model/status` 接口暴露
  - 模块在视频流中默认启用（`all` 模式包含 `fire`）
  - 模型加载失败时优雅降级（不影响其他模块）

- **不实现**：
  - 烟雾检测（smoke）单独识别（与火焰共用同一模型输出 class `fire`）
  - 火焰蔓延趋势分析
  - 火焰面积增速告警
  - 消防系统联动（自动报警）
  - 火焰颜色/纹理分析（仅用 YOLO 边界框检测）

## 影响

- 新增文件：
  - `backend_ai/services/fire_service.py`
  - `backend_ai/tests/test_fire_service.py`
  - `backend_ai/models/yolo/yolo_fire.pt`（模型权重，运行时放置）
- 修改文件：
  - `backend_ai/config/model.yaml`：添加 `fire` 模型配置段
  - `backend_ai/services/analysis_service.py`：添加 `fire` 模块调度分支
  - `backend_ai/services/event_service.py`：`EVENT_NAMES` 添加 `flame_detected`
  - `backend_ai/app.py`：导入、实例化、注入 FireService，更新 `/model/status` 和 `modules=all` 默认集合
  - `backend_ai/utils/geometry.py`：修复 `tuple[float, float]` 为 `Tuple[float, float]`（Python 3.8 兼容）
- 运行环境：无需新增依赖，复用已安装的 `ultralytics` 和 `torch`
