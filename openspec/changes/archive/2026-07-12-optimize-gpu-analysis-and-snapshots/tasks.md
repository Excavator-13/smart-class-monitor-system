# Tasks

## 1. GPU 模型运行时

- [x] 1.1 将模型设备配置改为 CUDA
- [x] 1.2 InsightFace 使用 CUDA provider 并暴露实际 provider 日志
- [x] 1.3 行为 YOLOv8 和明火 YOLO 使用 CUDA 推理
- [x] 1.4 增加 InsightFace buffalo_l 与 YOLOv8 启动日志

## 2. 截图策略

- [x] 2.1 仅为 `danger_zone_intrusion` 确认事件保存与推送截图
- [x] 2.2 增加危险区域与非危险区域事件截图测试

## 3. 行为检测展示与作用域

- [x] 3.1 目标框仅保留 `person/student`
- [x] 3.2 事件框仅保留 `face_recognized`，隐藏 stranger、phone、head_down 及其他事件框
- [x] 3.3 验证手机与低头基于整帧对象检测且不依赖 zones

## 4. 验证

- [x] 4.1 运行 backend_ai 相关 pytest
- [x] 4.2 运行 OpenSpec 校验或结构检查（当前环境未安装 `openspec` CLI，已按 archive 既有结构人工检查）
