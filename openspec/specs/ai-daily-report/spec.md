## Requirement: AI 日报生成
系统必须每日生成安防日报，包含 AI 总结、告警类型统计、截图VL分析。
日报必须支持手动生成和定时自动生成。
日报必须支持导出为可下载的 HTML/PDF 文件。

### Scenario: 手动生成日报
- GIVEN 用户在告警管理页点击「生成日报」
- WHEN 系统查询当日所有告警记录
- THEN 调用千问 API 生成 AI 总结
- AND 对有截图的告警调用 Qwen VL 分析画面内容
- AND 前端展示：AI总结 + 条形统计图 + 告警详情（含截图和VL分析）

### Scenario: 定时自动生成
- GIVEN 前端设置了日报时间（如 18:00）
- WHEN SpringBoot @Scheduled 定时检查到达设定时间
- THEN 自动查询当日告警 → 调用千问 → 生成日报 → 存入历史
- AND 前端下次打开时能看到最新日报

### Scenario: 导出日报
- GIVEN 日报已生成
- WHEN 用户点击「导出 PDF」
- THEN 生成完整 HTML 文件（含截图与VL分析文字）
- AND 浏览器打印 → 另存为 PDF

### Scenario: 查看往期日报
- GIVEN 已生成多条日报
- WHEN 用户点击「往期日报」
- THEN 弹窗展示历次日报列表
- AND 点击任一条可查看完整内容

### Scenario: 日报统计数据
- GIVEN 日报已生成
- WHEN 前端渲染统计区域
- THEN 条形图展示各类型告警数量（type_counts）
- AND 数据来自全量统计，不与告警列表截断

### Requirement: 截图 VL 分析
系统必须对数据库中有 snapshot_path 的告警记录调用 Qwen VL 模型进行截图分析。
系统不得因截图加载失败影响日报正常生成。

### Scenario: 有截图的分析
- GIVEN 告警记录包含 snapshot_path
- WHEN 生成日报时遍历告警列表
- THEN 通过 9092 端口访问截图文件
- AND 调用 qwen-vl-plus 模型分析画面内容
- AND 分析结果以 vlAnalysis 字段存入每条告警详情

### Scenario: 无截图的跳过
- GIVEN 告警记录不含 snapshot_path
- WHEN 生成日报时遍历告警列表
- THEN 跳过 VL 分析
- AND 告警详情中不展示截图和分析
