## 1. 钉钉通知改造

- [x] 1.1 trigger_alert 生成唯一 event_id
- [x] 1.2 _step 函数签名改为 _step(msg, event_id, ch, idx, snapshot)
- [x] 1.3 定时器 key 改为 event_id（避免同内容告警冲突）
- [x] 1.4 逐级上报改为 text + @，去掉 markdown 截图
- [x] 1.5 三条消息都带上「事件ID：evt_xxx」

## 2. 回复处理

- [x] 2.1 AlertHandler 匹配 target_key = eid（不是 ekey）
- [x] 2.2 匹配到事件ID → 只停单个事件
- [x] 2.3 有活动事件但未匹配 → 全部停止
- [x] 2.4 无活动事件 → 提示「当前无活动告警」
- [x] 2.5 修复缺少 clear timer 的 bug

## 3. 日报统计图

- [x] 3.1 后端 ReportService 添加 type_counts 完整类型统计
- [x] 3.2 前端 reportChart 从 raw.type_counts 读取数据
- [x] 3.3 条形图样式改为蓝色渐变，排版优化

## 4. 日报前端展示

- [x] 4.1 最新日报卡片展示截图（getSnapshotUrl）
- [x] 4.2 VL 分析文字展示
- [x] 4.3 Markdown 渲染（**加粗** → <b>）
- [x] 4.4 PDF 导出使用完整 9092 URL
