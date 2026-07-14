## 1. 钉钉密钥外部化

- [x] 1.1 `dingtalk_service.py`：APP_KEY/APP_SECRET/ROBOT_CODE/GROUP_ID/WEBHOOK 改为从 `os.environ.get()` 读取，默认空字符串
- [x] 1.2 `dingtalk_service.py`：`trigger_alert()` 和 `start_stream()` 开头校验必填项，空值时 log warning 并跳过（不崩溃）
- [x] 1.3 `.env` 新增 `DINGTALK_APP_KEY`、`DINGTALK_APP_SECRET`、`DINGTALK_WEBHOOK`、`DINGTALK_GROUP_ID`
- [x] 1.4 `.env.example` 新增对应变量（值为空占位）

## 2. 千问 API Key 外部化

- [x] 2.1 `application.yml` 新增 `report.qwen.*` 和 `report.ai-enabled`、`report.snapshot-base-url` 配置节
- [x] 2.2 `ReportService.java`：`@Value` 注解改为从配置读取，移除硬编码默认密钥；`callQwen()` 使用 `this.qwenUrl` 替代硬编码 URL

## 3. 设置持久化

- [x] 3.1 `SettingsController.java`：新增 `data/settings.json` 文件读写逻辑（`writeToFile` / `loadFromFile`）
- [x] 3.2 `SettingsController.java`：`@PostConstruct` 启动时从文件加载设置到内存 store
- [x] 3.3 `SettingsController.java`：`PUT` 方法末尾调用 `writeToFile()`
- [x] 3.4 `SettingsController.java`：`GET` 方法在 store 为空时返回 DEFAULTS（含文件加载逻辑）

## 4. 日报持久化

- [x] 4.1 `ReportService.java`：新增 `data/reports/` 目录和文件读写逻辑（`writeReportToFile` / `loadLatestReportFromFile` / `scanReportFiles`）
- [x] 4.2 `ReportService.java`：`generateReport()` 末尾调用 `writeReportToFile()`
- [x] 4.3 `ReportService.java`：`getLatestReport()` 在内存为空时从文件加载
- [x] 4.4 `ReportService.java`：`getHistory()` 改为扫描 `data/reports/` 目录
- [x] 4.5 `ReportController.java`：新增 `GET /report/{date}` 按日期查询

## 5. Flask AI 启动恢复

- [x] 5.1 `app.py`：`create_app()` 中在 `start_stream()` 前新增 `_restore_dingtalk_settings()`，从 Spring Boot `GET /api/settings` 拉取联系人/责任人/间隔
- [x] 5.2 恢复失败时 log warning，使用默认值继续运行

## 6. .gitignore

- [x] 6.1 项目根 `.gitignore` 新增 `data/` 排除（`*.json` 已覆盖，`data/` 为显式声明）

## 7. 编译与验证

- [x] 7.1 `mvn -DskipTests compile` 编译通过
- [ ] 7.2 验证 `PUT /api/settings` 后 `data/settings.json` 文件已生成
- [ ] 7.3 验证重启 Spring Boot 后 `GET /api/settings` 返回持久化的设置
- [ ] 7.4 验证 `POST /report/generate` 后 `data/reports/{date}.json` 文件已生成
- [ ] 7.5 验证 `GET /report/history` 返回文件中的日报列表
- [ ] 7.6 验证 `GET /report/{date}` 返回指定日期的日报
- [ ] 7.7 验证重启 Spring Boot 后 `GET /report/latest` 返回持久化的日报
- [ ] 7.8 验证 Flask AI 启动时从 Spring Boot 恢复联系人
- [ ] 7.9 验证 `.env` 中无钉钉密钥时 Flask AI 不崩溃，仅 log warning
