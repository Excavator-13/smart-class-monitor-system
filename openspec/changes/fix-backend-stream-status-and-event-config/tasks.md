# 实现任务

## 1. 视频源权限与真实状态

- [x] 1.1 内部令牌鉴权时写入内部调用标记
- [x] 1.2 视频源列表、详情、启用列表和播放地址按 admin/teacher/internal 脱敏 RTMP 地址
- [x] 1.3 修复 Nginx-RTMP 标准 `/stat` XML 发布者解析并安全解析 XML
- [x] 1.4 前端加载每个视频源的实时状态，不再把 `enabled` 当作 `online`
- [x] 1.5 系统状态页仅管理员显示 RTMP 地址

## 2. 事件等级与规则解耦

- [x] 2.1 `score_config` 增加 `level`，实体、Mapper、VO、Swagger 和更新接口同步
- [x] 2.2 默认评分配置改为按实际异常 `event_type` 初始化
- [x] 2.3 行为规则 DTO、VO、服务和 Mapper 停止读写 `level`
- [x] 2.4 AI ConfigClient 加载、轮询并查询 `event_configs`
- [x] 2.5 AnalysisService 在统一事件入口应用事件等级，包含 `stream_offline`
- [x] 2.6 SpringBoot 告警入库按事件配置校正等级
- [x] 2.7 更新配置后通知 AI 重载 `event_configs`
- [x] 2.8 前端将等级编辑从规则卡片移到告警事件配置

## 3. 初始化数据审计与修复

- [x] 3.1 删除启动时 truncate 行为，改为按唯一业务键缺失插入
- [x] 3.2 核对并补齐六项规则驱动检测配置
- [x] 3.3 核对并补齐所有异常事件配置，排除 `face_recognized`
- [x] 3.4 保留已有用户、视频源、人员、区域和告警，不重复制造演示记录

## 4. 文档与验证

- [x] 4.1 更新 `docs/backend-interface-and-module-notes.md`，不修改 README
- [x] 4.2 增加 Nginx 标准 XML 在线/离线/异常解析测试
- [x] 4.3 增加事件等级入库校正与初始化幂等相关测试
- [x] 4.4 运行 SpringBoot 测试或至少编译
- [x] 4.5 运行 AI 单元测试/语法检查
- [x] 4.6 运行 Vue 生产构建
