## Requirement: 加法计算
系统必须提供 GET /api/add 接口，接收 a、b 两个数字参数，返回它们的和。
系统不得接受非数字输入，必须返回 400 错误。

### Scenario: 1+1=2
- GIVEN 用户输入 a=1, b=1
- WHEN 调用 /api/add?a=1&b=1
- THEN 返回 {"result": 2}

### Scenario: 非法输入
- GIVEN 用户输入 a="abc", b=2
- WHEN 系统校验
- THEN 返回 400 错误 "请输入数字"
