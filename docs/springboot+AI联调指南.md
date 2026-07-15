# Spring Boot + AI 联调指南

## 启动

```bash
cd backend_system && mvn spring-boot:run   # 端口 8080
cd backend_ai && python app.py             # 端口 5000
```

## 鉴权

| 调用方             | Header                                                          |
| ------------------ | --------------------------------------------------------------- |
| 前端 → Spring Boot | `Authorization: Bearer <jwt>` （登录获取）                      |
| AI → Spring Boot   | `X-Internal-Token: smart-class-ai-internal-token-2026-dev-only` |

---

## 一、AI 调 Spring Boot（5 个接口）

### 1. 视频流列表

```
GET /streams
X-Internal-Token: <token>
```

→ `{"code":0,"data":{"items":[{"stream_id":"classroom_01","stream_name":"一号教室","rtmp_url":"rtmp://...","status":"enabled"}]}}`

### 2. 区域列表

```
GET /zones?stream_id=classroom_01
X-Internal-Token: <token>
```

→ `{"code":0,"data":[{"zone_id":"zone_01","zone_type":"danger","coordinates":"[{...}]","threshold_seconds":2,"safe_distance":0.05,"enabled":true}]}`

### 3. 规则列表

```
GET /rules
X-Internal-Token: <token>
```

→ `{"code":0,"data":[{"rule_type":"danger_zone","enabled":true,"threshold_seconds":2,"confidence_threshold":0.6,"cooldown_seconds":45,"level":"warning"}]}`

### 4. 人脸特征

```
GET /students/face-features
X-Internal-Token: <token>
```

→ `{"code":0,"data":[{"student_id":"1","feature_vector":[0.1,...],"quality_score":0.91}]}`

### 5. 告警入库

```
POST /alerts/ai
X-Internal-Token: <token>
```

```json
{
  "event_id": "evt_20260709143000001",
  "stream_id": "classroom_01",
  "alert_type": "danger_zone_intrusion",
  "alert_name": "危险区域入侵",
  "level": "warning",
  "confidence": 0.85,
  "occurred_at": "2026-07-09T14:30:00",
  "duration_seconds": 3.5,
  "student_id": null,
  "target_info": { "track_id": 1, "bbox": [100, 200, 150, 300] },
  "zone_id": 1,
  "snapshot_path": "/snapshots/evt_xxx.jpg",
  "record_path": null,
  "event_time_offset": null,
  "extra": { "source": "backend_ai" }
}
```

→ `{"code":0,"data":{"alert_id":1,"status":"unhandled"}}` （event_id 幂等）

---

## 二、前端调 Spring Boot

### 2.1 认证（无需 JWT）

**登录** `POST /auth/login`

```json
{ "username": "admin", "password": "admin123" }
```

→ `{"code":0,"data":{"token":"eyJ...","user_id":1,"username":"admin","role":"admin"}}`

**其他** `GET /auth/info` | `POST /auth/logout` — 需 JWT

### 2.2 视频源

| 方法   | URL                                | 说明       |
| ------ | ---------------------------------- | ---------- |
| GET    | `/streams?page=1&pageSize=10`      | 分页列表   |
| GET    | `/streams/enabled`                 | 已启用列表 |
| POST   | `/streams`                         | 新增       |
| PUT    | `/streams/{id}`                    | 编辑       |
| DELETE | `/streams/{id}`                    | 删除       |
| GET    | `/streams/{stream_id}/status`      | 推流状态   |
| GET    | `/streams/{stream_id}/preview-url` | 播放地址   |

新增 Body：`{"stream_name":"一号教室","stream_id":"classroom_01","rtmp_url":"rtmp://...","remark":""}`

### 2.3 区域

| 方法   | URL                          | 说明             |
| ------ | ---------------------------- | ---------------- |
| GET    | `/zones?streamId=&zoneType=` | 列表             |
| POST   | `/zones`                     | 新增             |
| PUT    | `/zones/{id}`                | 修改             |
| DELETE | `/zones/{id}`                | 删除             |
| GET    | `/streams/{stream_id}/zones` | 某视频源全部区域 |

新增 Body：`{"stream_id":"classroom_01","zone_name":"讲台危险区","zone_type":"danger","coordinates":"[{...}]","threshold_seconds":2,"safe_distance":0.05}`

### 2.4 规则

| 方法   | URL                | 说明 |
| ------ | ------------------ | ---- |
| GET    | `/rules?ruleType=` | 列表 |
| POST   | `/rules`           | 新增 |
| PUT    | `/rules/{id}`      | 更新 |
| DELETE | `/rules/{id}`      | 删除 |

新增 Body：`{"rule_type":"phone_usage","rule_name":"手机使用检测","enabled":true,"threshold_seconds":3,"confidence_threshold":0.6,"cooldown_seconds":45,"level":"warning","config_json":"{}"}`

### 2.5 告警

| 方法 | URL                                                       | 说明     |
| ---- | --------------------------------------------------------- | -------- |
| GET  | `/alerts?streamId=&alertType=&status=&page=1&pageSize=10` | 列表     |
| GET  | `/alerts/{id}`                                            | 详情     |
| PUT  | `/alerts/{id}/status`                                     | 更新状态 |
| GET  | `/alert-stats`                                            | 统计卡片 |

更新状态 Body：`{"status":"processing","handler_id":1,"remark":"正在处理"}`
status 可选：`unhandled` / `processing` / `handled` / `false_alarm` / `ignored`

### 2.6 人员

| 方法   | URL                            | 说明                       |
| ------ | ------------------------------ | -------------------------- |
| GET    | `/students?page=1&pageSize=10` | 列表                       |
| POST   | `/students`                    | 新增                       |
| PUT    | `/students/{id}`               | 编辑                       |
| DELETE | `/students/{id}`               | 删除                       |
| POST   | `/students/{id}/face`          | 人脸注册（Spring Boot→AI） |
| GET    | `/students/{id}/face-features` | 特征记录（不含向量）       |

新增 Body：`{"student_no":"2024001","name":"张三","class_name":"软件工程1班"}`
人脸注册 Body：`{"image":"data:image/jpeg;base64,..."}` → `{"code":0,"data":{"face_count":1,"feature_dim":512,"quality_score":0.91}}`

### 2.7 其他

```
GET /recordings?streamId=&page=1&pageSize=10       # 录像
GET /operation-logs?userId=&action=&page=1&pageSize=10  # 操作日志
GET /system/health                                  # 健康检查（无需 JWT）
```

---

## 三、AI 补充接口（仅 summary 未测）

```
GET http://localhost:5000/analysis/summary/classroom_01
```

→ `{"code":0,"data":{"stream_id":"classroom_01","risk_score":30,"risk_level":"warning","summary":"危险区域入侵2起，使用手机1起","counts":{"danger_zone_intrusion":2,"phone_usage":1}}}`

---

## 四、联调步骤

1. **连通** — `GET /system/health` 确认 backend、database up
2. **认证** — `POST /auth/login` 拿 JWT，后续前端请求带上
3. **AI→Spring Boot** — Postman 带 `X-Internal-Token` 逐个调 5 个接口，验证返回格式
4. **端到端** — `POST http://localhost:5000/config/reload` 触发 AI 拉配置，观察日志；触发告警确认入库
5. **前端 CRUD** — 视频源/区域/规则/人员增删改查；人脸注册验证 Spring Boot→AI 联动；告警列表+统计
