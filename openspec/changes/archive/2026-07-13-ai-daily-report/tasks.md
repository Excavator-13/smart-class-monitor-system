## 1. 后端日报服务

- [x] 1.1 ReportService.java 实现 queryTodayAlerts 查数据库
- [x] 1.2 generateReport 调用 callQwen 生成 AI 总结
- [x] 1.3 generateReport 遍历告警，调用 analyzeImage VL 分析
- [x] 1.4 添加 type_counts 全量统计字段
- [x] 1.5 @Scheduled 定时自动生成日报
- [x] 1.6 snapshotBaseUrl 配置为 http://39.106.209.208:9092

## 2. 前端日报展示

- [x] 2.1 日报卡片展示 AI 总结（renderMd 转换 Markdown）
- [x] 2.2 告警详情展示截图（getSnapshotUrl）
- [x] 2.3 VL 分析文字展示
- [x] 2.4 条形统计图（reportChart computed）
- [x] 2.5 统计图蓝色渐变样式，调整排版

## 3. PDF 导出

- [x] 3.1 导出按钮放顶部设置栏
- [x] 3.2 PDF 导出使用完整 9092 URL 加载图片
- [x] 3.3 导出内容包含 AI 总结 + 截图 + VL 分析
- [x] 3.4 PDF 导出 Markdown 渲染

## 4. 截图基础设施

- [x] 4.1 云服务器 /data/snapshots/ 目录确认
- [x] 4.2 9092 端口软链接指向 /data/snapshots
- [x] 4.3 SnapshotPusher 代码确认
