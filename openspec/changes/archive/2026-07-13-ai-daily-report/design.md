## Context
日报后端使用 SpringBoot ReportService，前端在 App.vue 告警管理页展示。截图文件通过 SnapshotPusher 同步到云服务器 /data/snapshots/，9092 端口通过软链接提供 HTTP 访问。

## Decisions
- type_counts 由后端全量统计（不依赖前端截断后的 alerts 列表）
- 截图通过 getSnapshotUrl() 补全 9092 URL
- VL 分析结果存入 vlAnalysis 字段，每条告警独立
- Markdown 渲染在前端完成（renderMd 函数），不依赖后端
- PDF 导出使用完整 URL 而非 base64（避免文件过大）

## Risks
- 截图文件存在但数据库记录缺失（DataInitializer 清库）
- 9092 软链接可能被覆盖或删除
- Qwen VL 多次调用可能产生 API 费用
