## Requirement: AI 日报生成与展示
系统必须支持通过千问 API 自动生成日报，包含 AI 总结、截图 VL 分析、类型统计条形图。
日报必须支持手动生成和定时自动生成。

### Scenario: 生成 AI 总结
- GIVEN 用户点击「生成日报」
- WHEN 系统查询当日告警数据
- THEN 调用 qwen3.7-plus 生成日报总结
- AND 前端展示 AI 生成的专业日报文案

### Scenario: VL 截图分析
- GIVEN 告警记录包含 snapshot_path
- WHEN 生成日报时遍历告警列表
- THEN 从 9092 端口下载截图
- AND 调用 qwen-vl-plus 模型分析
- AND 分析结果嵌入每条告警详情

### Scenario: 统计条形图
- GIVEN 日报已生成
- WHEN 前端渲染统计区域
- THEN 后端返回 raw.type_counts 全量统计
- AND 前端绘制蓝色渐变条形图

### Scenario: Markdown 渲染
- GIVEN AI 总结包含 **加粗** 或 ## 标题等 Markdown 语法
- WHEN 前端渲染日报卡片
- THEN 转换为 <b> <h3> 等 HTML 标签
