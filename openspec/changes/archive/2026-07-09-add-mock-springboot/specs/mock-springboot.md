## Requirement: Mock SpringBoot 配置与告警接口

系统必须提供本地 Mock 服务器（端口 8080），模拟 SpringBoot 后端对 AI 模块的全部依赖接口。
配置数据通过 YAML 文件管理，支持切换测试场景。

### Scenario: 查询视频流列表

- GIVEN AI 模块调用 GET /streams
- WHEN Mock 服务器收到请求
- THEN 返回 200，body 包含 code=0 及 items 数组，每个 item 含 stream_id、rtmp_url、name、status 字段

### Scenario: 查询区域配置

- GIVEN AI 模块调用 GET /zones?stream_id=classroom_01
- WHEN Mock 服务器收到请求
- THEN 返回 200，body 包含 code=0 及 items 数组，每个 item 含 zone_id、stream_id、name、polygon、enabled 字段

### Scenario: 查询规则配置

- GIVEN AI 模块调用 GET /rules
- WHEN Mock 服务器收到请求
- THEN 返回 200，body 包含 code=0 及 items 数组，每个 item 含 rule_type、name、enabled、threshold_seconds、confidence_threshold 字段

### Scenario: 查询人脸特征库

- GIVEN AI 模块调用 GET /students/face-features
- WHEN Mock 服务器收到请求
- THEN 返回 200，body 包含 code=0 及 items 数组（默认为空）

### Scenario: 接收告警推送

- GIVEN AI 模块检测到异常事件
- WHEN 调用 POST /alerts/ai 并发送告警 JSON
- THEN 返回 200，body 包含 code=0、message="ok"，同时在 Mock 服务器终端打印告警内容
