# 明火检测模块实现任务

- [x] 创建 `backend_ai/services/fire_service.py`（FireService 类）
- [x] 创建 `backend_ai/tests/test_fire_service.py`（9 个 pytest 用例）
- [x] 修改 `backend_ai/config/model.yaml`：fire 段 enabled=true，配置权重路径和参数
- [x] 修改 `backend_ai/services/analysis_service.py`：AnalysisService 构造函数添加 fire_service，analyze_frame 添加 fire 分支
- [x] 修改 `backend_ai/services/event_service.py`：EVENT_NAMES 添加 flame_detected
- [x] 修改 `backend_ai/app.py`：导入 FireService，创建时加载模型，注入到 AnalysisService，注册到 extensions，更新 model_status 和 modules=all
- [x] 修复 `backend_ai/utils/geometry.py`：tuple[float, float] → Tuple[float, float]（Python 3.8 兼容）
- [x] 放置 `yolo_fire.pt` 模型到 `backend_ai/models/yolo/`
- [x] 运行全部测试验证：32/32 通过
- [x] 创建 OpenSpec 归档（changes/archive/2026-07-09-fire-detection/）
- [x] 同步正式 spec 到 `openspec/specs/fire-detection/`
