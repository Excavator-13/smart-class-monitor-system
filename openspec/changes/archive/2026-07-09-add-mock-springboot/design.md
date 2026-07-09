## 技术方案

- 框架：Flask
- 端口：8080
- 接口：GET /streams、GET /zones、GET /rules、GET /students/face-features、POST /alerts/ai
- 配置：YAML 文件管理 Mock 数据（streams/zones/rules），路径为 mock_springboot/mock_data.yaml
- 返回：统一 JSON 格式 {"code": 0, "data": {"items": [...]}}
- 告警接口：POST /alerts/ai 接收 JSON，终端打印，返回 {"code": 0, "message": "ok"}
- 文件路径：mock_springboot/app.py
- 不依赖数据库，不依赖 AI 模块代码
