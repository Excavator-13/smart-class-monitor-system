## 1. Deepfake 默认停用

- [x] 1.1 增加 `deepfake_enabled: false` 并只在启用时加载检测器
- [x] 1.2 `AntiSpoofService` 关闭时不执行 Deepfake 分支
- [x] 1.3 从视频标注白名单移除 `deepfake_detected`
- [x] 1.4 前端将 Deepfake 规则显示为关闭且置灰

## 2. Danger zone 规则恢复

- [x] 2.1 增加 `danger_zone_* -> danger_zone` 规则映射与 fail-closed 过滤
- [x] 2.2 `ZoneService` 遵守 `danger_zone.enabled`
- [x] 2.3 “未配置”提示按 danger 类型判断，保留区域及事件标注
- [x] 2.4 删除 RuleController 重复全量刷新

## 3. 验证

- [x] 3.1 补 Deepfake 停用、无标注测试
- [x] 3.2 补 danger zone 启停和子事件映射测试
- [x] 3.3 运行 AI 相关测试、SpringBoot 测试和前端构建
