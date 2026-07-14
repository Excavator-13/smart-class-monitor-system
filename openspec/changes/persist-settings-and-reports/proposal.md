# 钉钉/AI日报设置与报告本地 JSON 持久化

## 动机

当前钉钉通知和 AI 日报的设置、报告全部存储在内存中，服务重启即丢失：

| 数据                                 | 当前存储                              | 问题                       |
| ------------------------------------ | ------------------------------------- | -------------------------- |
| 联系人/责任人/上报间隔               | Spring Boot 内存 Map + Flask 内存变量 | 重启丢失，需重新配置       |
| 钉钉通知开关 / AI日报开关 / 日报时间 | Spring Boot 内存 Map                  | 重启丢失                   |
| 日报内容（最新 + 历史）              | Spring Boot 内存变量/List             | 重启丢失，无法回顾         |
| 钉钉 APP_KEY/SECRET/WEBHOOK/GROUP_ID | Python 源码硬编码                     | 密钥泄露风险，换号需改代码 |
| 千问 API Key                         | Java @Value 默认值硬编码              | 密钥泄露风险               |

此外，前端 `localStorage` 虽然持久化了部分设置，但它只是前端缓存，不是权威数据源——后端重启后前端推过来的设置会覆盖后端默认值，但日报历史等数据无法恢复。

## 范围

### 1. 设置持久化（Spring Boot → 本地 JSON 文件）

- `SettingsController` 写设置时同步写 `data/settings.json`
- 启动时从 `data/settings.json` 加载到内存缓存
- 内存缓存作为读取层，零延迟

### 2. 日报持久化（Spring Boot → 本地 JSON 文件）

- `ReportService.generateReport()` 生成日报时写 `data/reports/{date}.json`
- `getLatestReport()` 内存优先，空则从文件加载
- `getHistory()` 扫描 `data/reports/` 目录按日期倒序返回
- 新增 `GET /report/{date}` 按日期查询

### 3. 钉钉密钥外部化（Flask AI → .env 环境变量）

- `dingtalk_service.py` 的 APP_KEY/SECRET/WEBHOOK/GROUP_ID 从 `os.environ` 读取
- `.env` / `.env.example` 新增对应变量
- 代码中移除硬编码密钥

### 4. 千问 API Key 外部化（Spring Boot → 环境变量）

- `application.yml` 新增 `report.qwen.*` 配置节，通过 `${QWEN_API_KEY:}` 引用环境变量
- `ReportService.java` 的 `@Value` 从配置读取，不再硬编码默认密钥

### 5. Flask AI 启动恢复

- `app.py` 启动时从 Spring Boot `GET /api/settings` 拉取联系人/责任人/间隔
- 恢复 `dingtalk_service` 的 PERSONS / PRIMARY / STEP_TIMEOUT

### 6. .gitignore

- 新增 `data/` 目录排除，避免提交本地运行时数据

## 不做

- 不使用数据库存储设置和日报（用户明确要求不上云，本地 JSON 足够）
- 不引入 SQLite / H2 等嵌入式数据库（设置+日报数据量小，JSON 文件更简单可读）
- 不修改前端代码（API 接口不变，前端无感知）
- 不修改钉钉通知的业务逻辑（逐级上报、Stream 收回复等不变）
- 不修改 AI 日报的生成逻辑（千问调用、VL 分析等不变）
- 不实现文件锁或并发写入保护（单实例部署，Spring Boot 单线程写文件）
