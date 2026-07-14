## Context

### 已有基础设施

**SettingsController**：`PUT /api/settings` 接收前端设置，存入内存 `Map<String, Object> store`，同步调用 `reportService.updateSettings(body)` 和 `POST http://127.0.0.1:5001/api/contacts/sync` 推送到 Flask AI。`GET /api/settings` 返回内存 Map，为空时返回硬编码默认值。

**ReportService**：`generateReport()` 生成日报存入内存 `latestReport` 和 `List<Map> history`。`getLatestReport()` / `getHistory()` 直接读内存。`@Scheduled(fixedRate=600000)` 每 10 分钟检查日报时间。`@Value` 硬编码千问 API Key。

**dingtalk_service.py**：APP_KEY/APP_SECRET/WEBHOOK/GROUP_ID 硬编码为模块级常量。PERSONS/PRIMARY/STEP_TIMEOUT 为模块级可变变量，由 `contacts_sync.py` 或 `app.py` 中的 `/api/contacts/sync` 路由更新。

**app.py**：`create_app()` 构造 `AlertClient` 时传入 `dingtalk=trigger_alert`，调用 `start_stream()` 启动钉钉 Stream。`/api/contacts/sync` 路由更新 `ds.PERSONS` / `ds.PRIMARY` / `ds.STEP_TIMEOUT`。

**Flask .env**：已有 `SPRING_BASE_URL`、`INTERNAL_TOKEN`、`SNAPSHOT_REMOTE_*` 等环境变量，通过 `load_dotenv()` 加载。

**Spring Boot application.yml**：已有 `ai.*`、`auth.*`、`nginx.*`、`cors.*` 等配置节，均支持环境变量覆盖。

## Goals / Non-Goals

**Goals:**

1. 设置写入时同步持久化到 `data/settings.json`，启动时从文件恢复
2. 日报生成时持久化到 `data/reports/{date}.json`，历史从文件目录扫描
3. 钉钉密钥从 `.env` 环境变量读取，不硬编码
4. 千问 API Key 从 `application.yml` 配置读取，支持环境变量覆盖
5. Flask AI 启动时从 Spring Boot 拉取设置恢复联系人
6. `data/` 目录加入 `.gitignore`

**Non-Goals:**

- 不引入数据库（云 DB 或嵌入式）
- 不修改前端代码
- 不修改钉钉通知 / AI 日报的业务逻辑
- 不实现文件并发写入保护

## Decisions

| 决策           | 选择                                      | 理由                                                                                       |
| -------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------ |
| 持久化格式     | JSON 文件                                 | 零依赖，可读性好，Python/Java 标准库均支持，数据量小（设置几 KB，日报每天一个文件几十 KB） |
| 设置文件路径   | `backend_system/data/settings.json`       | 与项目根目录同级，Spring Boot 工作目录即为项目根                                           |
| 日报文件路径   | `backend_system/data/reports/{date}.json` | 按日期分文件，便于查找和清理                                                               |
| 读取策略       | 内存缓存优先                              | 设置读取频率高（每次钉钉通知都查联系人），走缓存零延迟；仅启动和写操作碰文件               |
| 写入策略       | 同步写文件                                | 设置变更频率极低（人工操作），同步写保证一致性，无需异步                                   |
| 密钥存储       | .env / 环境变量                           | 密钥不入文件仓库，.env 已在 .gitignore 中                                                  |
| Flask 启动恢复 | 从 Spring Boot 拉取                       | Spring Boot 是设置的权威源，Flask 作为消费者从中同步                                       |
| 日报历史查询   | 扫描目录                                  | 日报量小（每天一个文件），`Files.list()` 扫描即可，无需索引                                |

## 详细设计

### 1. 设置持久化

#### SettingsController 改造

```
PUT /api/settings
    │
    ├─ 写内存 store（现有逻辑）
    ├─ reportService.updateSettings(body)（现有逻辑）
    ├─ 推送 Flask AI（现有逻辑）
    └─ 新增：writeSettingsToFile()
          └─ ObjectMapper.writeValue(data/settings.json, store)

GET /api/settings
    │
    ├─ store 非空 → 返回 store（现有逻辑）
    └─ store 为空 → 新增：loadSettingsFromFile()
                       ├─ 文件存在 → 读入 store，返回
                       └─ 文件不存在 → 返回硬编码默认值（现有逻辑）
```

#### 文件结构

```json
{
  "dingtalkEnabled": true,
  "aiReportEnabled": true,
  "reportTime": "18:00",
  "alertInterval": 45,
  "responsible": "项重善",
  "contacts": [
    { "name": "项重善", "mobile": "18601033435" },
    { "name": "章志超", "mobile": "15270985055" }
  ]
}
```

#### 初始化

`@PostConstruct` 中调用 `loadSettingsFromFile()`，确保启动时内存缓存已加载。

### 2. 日报持久化

#### ReportService 改造

```
generateReport(alerts)
    │
    ├─ 生成日报（现有逻辑不变）
    ├─ latestReport = report（现有逻辑）
    ├─ history.add(0, report)（现有逻辑，保留内存缓存）
    └─ 新增：writeReportToFile(report)
          └─ ObjectMapper.writeValue(data/reports/{date}.json, report)

getLatestReport()
    │
    ├─ latestReport 非空 → 返回（现有逻辑）
    └─ latestReport 为空 → 新增：loadLatestReportFromFile()
                              ├─ 扫描 data/reports/ 找最新文件
                              └─ 读入 latestReport，返回

getHistory()
    │
    └─ 新增：scanReportFiles()
           ├─ Files.list(data/reports/) → 按文件名（日期）倒序
           └─ 逐个读取 JSON → 返回 List
```

#### ReportController 新增

```
GET /report/{date}  → 读取 data/reports/{date}.json，不存在返回 404
```

### 3. 钉钉密钥外部化

#### dingtalk_service.py 改造

```python
import os

APP_KEY = os.environ.get("DINGTALK_APP_KEY", "")
APP_SECRET = os.environ.get("DINGTALK_APP_SECRET", "")
ROBOT_CODE = os.environ.get("DINGTALK_APP_KEY", "")  # 同 APP_KEY
GROUP_ID = os.environ.get("DINGTALK_GROUP_ID", "")
WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "")
```

启动时校验：如果任一必填项为空，`trigger_alert` 和 `start_stream` 打 warning 日志但不崩溃（允许无钉钉环境运行）。

#### .env 新增

```env
DINGTALK_APP_KEY=dingvd9kkjc0bofwbqhu
DINGTALK_APP_SECRET=813aXbnZ6zbPM8ryKCma_8qVLzTj1D4kWSkujkjLYavI22xYHv3rhCCuxU-uYdUy
DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=ef247487bb8129668aa09a122be9161f056afaf263488d0c9285814654b06618
DINGTALK_GROUP_ID=cid+kYdFkRFkyGbzYUZc/QJCQ==
```

### 4. 千问 API Key 外部化

#### application.yml 新增

```yaml
report:
  qwen:
    url: ${QWEN_API_URL:https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions}
    key: ${QWEN_API_KEY:}
    model: ${QWEN_MODEL:qwen3.7-plus}
  ai-enabled: ${REPORT_AI_ENABLED:true}
  snapshot-base-url: ${SNAPSHOT_BASE_URL:http://39.106.209.208:9092}
```

#### ReportService.java 改造

```java
@Value("${report.qwen.url:https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions}")
private String qwenUrl;

@Value("${report.qwen.key:}")
private String qwenKey;

@Value("${report.qwen.model:qwen3.7-plus}")
private String model;

@Value("${report.ai-enabled:true}")
private boolean aiEnabled;

@Value("${report.snapshot-base-url:http://39.106.209.208:9092}")
private String snapshotBaseUrl;
```

移除 `callQwen()` 中硬编码的 `apiUrl` 变量，改用 `this.qwenUrl`。

### 5. Flask AI 启动恢复

#### app.py 改造

在 `create_app()` 末尾、`start_stream()` 之前，新增：

```python
def _restore_dingtalk_settings():
    try:
        resp = requests.get(f"{spring_base_url}/api/settings",
                           headers={"X-Internal-Token": internal_token} if internal_token else None,
                           timeout=5)
        if resp.ok:
            data = resp.json()
            contacts = data.get("contacts", [])
            new_persons = {}
            for c in contacts:
                name = c.get("name", "")
                mobile = c.get("mobile", "")
                if name and mobile:
                    new_persons[name] = {"name": name, "mobile": mobile}
            if new_persons:
                ds.PERSONS.clear()
                ds.PERSONS.update(new_persons)
            responsible = data.get("responsible", "")
            if responsible:
                ds.PRIMARY = responsible
            interval = data.get("alertInterval")
            if interval:
                ds.STEP_TIMEOUT = int(interval)
            logger.info("从 Spring Boot 恢复钉钉设置: %d 联系人, 责任人=%s", len(new_persons), responsible)
    except Exception:
        logger.warning("从 Spring Boot 恢复钉钉设置失败，使用默认值")
```

### 6. .gitignore

新增：

```
data/
```

## Risks / Trade-offs

- **[文件写入失败]** 磁盘满或权限不足时写文件失败 → 写入失败只 log warning，不影响内存操作和 API 响应；下次启动将从空状态恢复
- **[日报文件累积]** 长期运行后 `data/reports/` 文件增多 → 每天一个文件（约 10-50KB），一年 365 个文件约 18MB，完全可接受；如需清理可手动删除旧文件
- **[无并发保护]** 多实例部署时文件写入冲突 → 当前单实例部署，不涉及；如未来多实例，需改为数据库或共享存储
- **[密钥在 .env 中]** .env 文件本身在服务器上 → .env 已在 .gitignore 中，不入代码仓库；服务器安全由运维保障
