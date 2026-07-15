# Mock SpringBoot 服务器

## 动机

AI 模块与云媒体服务器的联调需要 SpringBoot 后端提供配置接口（streams/zones/rules/face-features）和告警接收接口（alerts/ai）。在 SpringBoot 尚未就绪或需独立调试 AI 模块时，需要一个本地 Mock 服务器模拟这些接口，使 AI 模块可以完整运行推流分析→事件检测→告警推送的全链路。

## 范围

- 本地 Flask Mock 服务器，监听 8080 端口，模拟 SpringBoot 对外接口
- 实现 GET /streams、GET /zones、GET /rules、GET /students/face-features 四个配置查询接口
- 实现 POST /alerts/ai 告警接收接口，终端打印告警内容
- 配置数据（rtmp_url、zone polygon 等）通过 YAML 文件管理，方便切换不同测试场景
- 不涉及数据库，不涉及真实 SpringBoot 代码
