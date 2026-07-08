## 技术方案

### 前端
- 在 `frontend/src/App.vue` 增加页面级统计 computed，用现有 mock/API 返回数据计算数量、状态和趋势。
- 将 AI 研判助手面板增加 `featured-ai` 样式，放在右侧栏首位，扩大分数环、摘要区和动作标签。
- 在告警、规则、人脸库、系统状态页面加入 `page-kpis`、`detail-grid`、`info-list` 等复用样式。

### 数据来源
- 告警统计来自 `alerts`。
- 规则统计来自 `rules`。
- 人员统计来自 `students`。
- 系统状态来自 `streams`、`health` 和 `modelStatus`。
- 新增内容均为前端展示层聚合，不要求后端新增字段。

### 风险
- 页面内容增加后移动端可能拥挤，需要通过响应式网格自动折叠。
- Element Plus 表格和新增卡片会增加一点首屏体积，但不影响当前演示场景。
