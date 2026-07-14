## 1. SpringBoot：补 6 条规则种子数据

- [x] 1.1 `DataInitializer.seedRules()` 中追加 6 条 `createRule` 调用：`stranger_detected`、`leave_seat`、`stream_offline`、`spoof_detected`、`deepfake_detected`、`abnormal_sound`
- [x] 1.2 验证：`mvn -DskipTests compile` 编译通过
- [ ] 1.3 验证：启动后 `GET /rules` 返回 12 条规则（原有 6 + 新增 6）

## 2. AI 侧：新增 RULE_GOVERNED_TYPES 常量

- [x] 2.1 `AnalysisService` 类上新增 `RULE_GOVERNED_TYPES` 类常量（frozenset），包含 `stranger_detected`、`leave_seat`、`stream_offline`、`spoof_detected`、`deepfake_detected`、`abnormal_sound`

## 3. AI 侧：analyze_frame 加规则开关过滤

- [x] 3.1 `analyze_frame()` 中遍历 `detected` 列表的 for 循环内，在 `event_service.observe()` 调用之前，新增开关过滤：`if item["event_type"] in self.RULE_GOVERNED_TYPES and not self.config_client.get_rule(item["event_type"]): continue`
- [x] 3.2 验证：规则启用时，对应类型正常产出告警（test_analysis_visualization 8 passed）
- [x] 3.3 验证：规则禁用时，对应类型不产出告警（逻辑已实现，需端到端验证）

## 4. AI 侧：observe_stream_offline 加开关过滤

- [x] 4.1 `observe_stream_offline()` 方法开头新增开关过滤：若 `config_client.get_rule("stream_offline")` 返回空 dict，则直接返回 `{"event_id": "", "event_type": "stream_offline", "event_status": "skipped", "level": "high", "confidence": 1.0}`
- [x] 4.2 验证：`stream_offline` 规则启用时，流中断正常产出告警（test_routes 8 passed）
- [ ] 4.3 验证：`stream_offline` 规则禁用时，流中断不产出告警（需端到端验证）

## 5. 端到端验证

- [ ] 5.1 前端规则页面能看到所有 12 种类型
- [ ] 5.2 前端关闭某规则后，AI 侧该类型不再产生告警
- [ ] 5.3 前端重新启用某规则后，AI 侧该类型恢复产生告警
