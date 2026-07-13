# 智慧教室 SpringBoot 后端接口文档

> **文档版本**: v2.1
> **最后更新**: 2026-07-08
> **文档状态**: 持续更新中（项目处于起步阶段，本文件会频繁变动）
>
> **状态标记说明**:
> - 🟢 **已确定**: 已与前端、AI 对齐，短期内不会大改，可进入开发
> - 🟡 **待定**: 方向基本确定，但细节（入参、返回、路径）可能调整，开发前请再次确认
> - 🔵 **扩展**: 后续版本计划，当前阶段不实现

---

## 一、文档定位

本文档是 SpringBoot 后端开发的**主要参考依据**，覆盖：

- 后端职责边界与技术栈
- 云服务器流媒体（Nginx RTMP）对接方式
- 对前端暴露的 RESTful API 清单与约定
- AI 服务调用的接口（告警入库、配置拉取）
- SpringBoot 调用 AI 服务的接口封装
- 数据库表结构与接口的对应关系
- 关键业务流程与优先级

**谁应该读这份文档**：SpringBoot 后端开发、前端联调人员、AI 服务联调人员。

### 系统整体架构

| 层级 | 技术栈 | 端口 | 职责 |
| --- | --- | --- | --- |
| 前端 | Vue3 + Element Plus + Axios | 客户端 | 页面渲染、用户交互 |
| 业务后端 | SpringBoot + MyBatis + MySQL | 8080 | 结构化数据管理、告警流转、鉴权 |
| AI 分析 | Python Flask + OpenCV + InsightFace + YOLO | 5000 | 视频帧分析、人脸识别、异常检测 |
| 流媒体 | Nginx RTMP | **9090** (RTMP) + **9092** (HTTP) | 推拉流、自动录像、截图/录像文件分发 |

### 云服务器信息

| 项目 | 值 |
| --- | --- |
| 服务器公网 IP | `39.106.209.208` |
| RTMP 推拉流端口 | `9090` |
| 静态资源 HTTP 端口 | `9092`（已开启 CORS + 目录浏览） |
| 录像存储目录 | `/usr/local/rtmp_video` |
| 推流地址格式 | `rtmp://39.106.209.208:9090/live/{stream_id}` |

**前端环境变量约定**（前端 `.env` 中配置，后端开发需了解）：

| 变量 | 指向 | 开发环境默认值 | 生产环境值 |
| --- | --- | --- | --- |
| `VITE_API_BASE` | SpringBoot 后端 | `http://localhost:8080` | `http://39.106.209.208:8080` |
| `VITE_AI_BASE` | Flask AI 服务 | `http://localhost:5000` | `http://39.106.209.208:5000` |
| `VITE_NGINX_BASE` | Nginx HTTP 静态资源 (9092) | `http://39.106.209.208:9092`（服务器部署，无本地环境） |

> ⚠️ **后端核心约定**：
> - 接口返回的文件路径（截图、录像）**必须是相对路径**（以 `/` 开头，如 `/snapshots/xxx.jpg`），前端会拼上 `VITE_NGINX_BASE` 访问。
> - **禁止在 JSON 响应中硬编码服务器 IP**。开发环境和生产环境 IP 不同，硬编码会导致跨环境访问失败。
> - Nginx 9092 端口已开启 `autoindex on` 和 CORS，前端可直接通过浏览器访问目录结构和文件。

---

## 二、后端职责边界

### SpringBoot 后端负责

| 职责 | 说明 | 状态 |
| --- | --- | --- |
| 用户与鉴权 | 登录、JWT Token、角色区分（admin/teacher） | 🟢 |
| 人员与人脸档案 | 学生基础信息管理、人脸注册记录、特征元数据 | 🟢 |
| 视频源管理 | stream_id、RTMP 地址、启停、状态探活 | 🟢 |
| 区域配置 | 危险区域、座位区域、禁手机区域、ROI 坐标 | 🟢 |
| 行为规则 | 低头、离座、区域入侵、手机、明火、摔倒等阈值 | 🟢 |
| 告警事件 | 接收 AI 告警、保存截图/视频路径、状态流转 | 🟢 |
| 统计概览 | 首页指标、告警统计、服务健康探活 | 🟢 |
| 操作日志 | 管理员操作审计 | 🔵 |

### SpringBoot 后端不负责

| 不负责内容 | 替代方案 |
| --- | --- |
| 视频帧推理、AI 模型运行 | 由 Flask AI 服务承担 |
| 实时视频流代理/转发 | 前端直连 Flask MJPEG 流或 Nginx |
| 截图/录像文件的物理存储和分发 | 由 Nginx 提供静态文件访问，SpringBoot 只存路径 |

---

## 三、云服务器流媒体对接（Nginx RTMP）

> SpringBoot 不直接处理视频流，但需要与 Nginx 服务器交互以获取推流状态和管理录像/截图文件索引。
> 详细说明见《智慧教室云服务器流媒体服务对接文档》，以下为 SpringBoot 开发必须掌握的关键信息。

### 3.1 RTMP 推拉流地址

| 用途 | 地址格式 | 示例 |
| --- | --- | --- |
| 推流（OBS/摄像头） | `rtmp://39.106.209.208:9090/live/{stream_id}` | `rtmp://39.106.209.208:9090/live/classroom_01` |
| 拉流（AI 分析） | `rtmp://39.106.209.208:9090/live/{stream_id}` | `rtmp://39.106.209.208:9090/live/classroom_01` |

> SpringBoot 在 `/streams` POST 时，`rtmp_url` 字段即为此格式。`stream_id` 需与推流端配置的 Stream Key 完全一致。

### 3.2 推流状态检测（SpringBoot → Nginx）

SpringBoot 判断某路视频是否在线，需请求 Nginx 内置状态页并解析 XML：

- **状态页地址**：`http://39.106.209.208:9092/stat`
- **返回格式**：XML
- **解析逻辑**：查找 `<stream>` 标签下的 `<publish>` 子标签，`active` 属性为 `true` 表示正在推流

```xml
<!-- /stat 返回片段示例 -->
<stream>
  <name>classroom_01</name>
  <publish active="true" time="2026-07-07T10:00:00+08:00" />
</stream>
```

> ⚠️ `/streams/{stream_id}/status` 接口的实现核心就是解析 `/stat` XML，返回在线状态和推流时长。

#### 3.2.1 `stream_offline` 双重检测职责分工

系统中存在两套视频源离线检测机制，需明确各自职责：

| 检测方 | 检测方式 | 用途 | 频率 |
| --- | --- | --- | --- |
| SpringBoot `/streams/{stream_id}/status` | 请求 Nginx `/stat` XML 解析 `<publish active>` | 前端展示视频源在线/离线状态 | 低频轮询（按需或 30s+） |
| AI Flask 服务 | OpenCV 拉流超时判断 | 触发 `stream_offline` 告警入库 | 实时检测（拉流中断即触发） |

> ⚠️ 两者结果不一致时（如 AI 拉流超时但 Nginx 认为推流仍在），**以 AI 实时拉流状态为准**生成告警。SpringBoot 探活结果仅用于前端 UI 状态展示，不影响告警生成。

### 3.3 自动录像机制

Nginx 在推流期间**自动持续录像**，无需额外接口调用：

| 项目 | 说明 |
| --- | --- |
| 录像格式 | 实时生成 `.flv`，后台脚本自动转 `.mp4` |
| 文件命名 | `{stream_id}-{年-月-日-时_分_秒}.flv`，如 `classroom_01-2026-07-07-10_30_00.flv` |
| 存储目录 | `/usr/local/rtmp_video` |
| **保留策略** | **仅保留最近 7 天**，超期自动清理 |

> ⚠️ **对 SpringBoot 的影响**：
> - `/recordings` 接口返回的文件列表中，优先使用 `.mp4` 格式 URL（前端用 `<video>` 标签直接播放，无需 flv.js）。
> - 录像文件超过 7 天会被自动清理，数据库中如有录像记录需考虑过期处理。
> - 推流未断开时，录像文件不会生成完整回看文件。

### 3.4 截图文件

| 项目 | 说明 |
| --- | --- |
| 生成方 | AI Flask 服务（检测到异常时截取当前帧） |
| 存储路径 | `/usr/local/rtmp_video/snapshots/` |
| 入库流程 | AI 生成截图 → 调 `POST /alerts/ai` 将相对路径（如 `/snapshots/xxx.jpg`）传给 SpringBoot → SpringBoot 存入 `alert_event.snapshot_path` → 前端拿到后拼上 `VITE_NGINX_BASE` 展示 |

### 3.5 静态资源访问

- **Base URL**：`http://39.106.209.208:9092`
- **文件 URL 构成**：`{VITE_NGINX_BASE}` + `{相对路径}`
- **CORS**：9092 端口已开启跨域支持
- **目录浏览**：浏览器访问 `http://39.106.209.208:9092/` 可查看文件目录结构

> SpringBoot 返回给前端的 `snapshot_url` 和 `video_clip_url` 必须是相对路径，前端自行拼接。示例：
> - 数据库存：`/snapshots/20260707/phone_0001.jpg`
> - 前端拼接：`http://39.106.209.208:9092/snapshots/20260707/phone_0001.jpg`

---

## 四、统一接口约定

### 4.1 路径规范

> ⚠️ 本阶段接口路径以前端文档为基准，暂不添加 `/api/v1` 版本前缀。后续如需版本化，统一添加即可，前端同步调整 `VITE_API_BASE` 或路径拼接方式。

| 接口类型 | 路径特征 | 说明 |
| --- | --- | --- |
| 前端业务接口 | `/auth` `/streams` `/students` `/zones` `/rules` `/alerts` `/alert-stats` `/recordings` `/system` `/operation-logs` `/dashboard` `/files` | 前端直接调用的接口 |
| AI 调用接口（写） | `POST /alerts/ai` | AI 检测到异常后回写告警，唯一入口 |
| AI 调用接口（读） | `GET /streams` `GET /zones` `GET /rules` `GET /students/face-features` | AI 启动/刷新时拉取配置和人脸特征（复用前端接口或专用接口） |
| 健康检查 | `/system/health` | 统一探活入口 |

### 4.2 统一返回结构

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

分页返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "records": [],
    "page": 1,
    "page_size": 10,
    "total": 0
  }
}
```

### 4.3 状态码

| code | 含义 | 使用场景 |
| --- | --- | --- |
| 0 | 成功 | 正常返回 |
| 400 | 参数错误 | 必填字段缺失、格式不正确 |
| 401 | 未登录或 token 失效 | 前端跳转登录页 |
| 403 | 无权限 | 普通用户访问管理接口 |
| 404 | 资源不存在 | ID 查不到记录 |
| 409 | 状态冲突或重复数据 | 重复 stream_id、student_no 等 |
| 500 | 服务端异常 | 未预期的服务器错误 |

### 4.4 字段命名

```yaml
spring:
  jackson:
    property-naming-strategy: SNAKE_CASE    # JSON 使用 snake_case，与前端的 Axios、Python 风格一致
    time-zone: Asia/Shanghai
    date-format: yyyy-MM-dd HH:mm:ss
```

Java 内部仍使用驼峰，由 Jackson 自动转换。

### 4.5 枚举约定

| 枚举 | 可选值 | 状态 |
| --- | --- | --- |
| 用户角色 | `admin`、`teacher` | 🟢 |
| 视频源状态 | `enabled`、`disabled`、`online`、`offline` | 🟢 |
| 区域类型 | `danger`、`seat`、`phone_forbidden`、`roi` | 🟢 |
| 告警/事件类型 | `face_recognized`、`stranger_detected`、`danger_zone_intrusion`、`danger_zone_stay`、`danger_zone_approach`、`phone_usage`、`head_down`、`leave_seat`、`flame_detected`、`fall_detected`、`stream_offline` | 🟢 |
| 告警等级 | `info`、`warning`、`high` | 🟢 |
| 告警状态 | `unhandled`、`processing`、`handled`、`false_alarm`、`ignored` | 🟢 |

---

## 五、前端业务接口清单

> **标记规则**: 🟢 = 已与前端对齐，可开发；🟡 = 方向确定、细节待定；🔵 = 后续扩展

### 5.1 登录与用户模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/auth/login` | POST | 系统登录 | `username`、`password` | `token`、用户信息、角色 | 区分 admin 和 teacher |
| 🟢 | `/auth/info` | GET | 获取当前登录用户信息 | Header: token | 用户名、角色、头像 | 路由守卫、页面刷新恢复登录态 |
| 🟡 | `/auth/logout` | POST | 退出登录 | Header: token | 操作结果 | 初版可前端直接清 token |
| 🟢 | `/users` | GET | 用户列表 | `role`、`status`、`page`、`pageSize` | 用户分页 | 仅管理员；前端用户管理页使用 |
| 🟢 | `/users/{id}` | GET | 用户详情 | `id` | 用户基本信息 | 仅管理员 |
| 🟢 | `/users/{id}` | PUT | 编辑用户资料 | `nickname`、`avatar_url` | 更新后的用户 | 仅管理员 |
| 🟢 | `/users/{id}/role` | PUT | 修改用户角色 | `role`：`admin`/`teacher` | 更新结果 | 仅管理员；不能修改自己 |
| 🟢 | `/users/{id}/status` | PUT | 启停用户 | `status`：`enabled`/`disabled` | 更新结果 | 仅管理员；不能禁用自己 |
| 🟢 | `/users/{id}` | DELETE | 软删除用户 | `id` | 删除结果 | 仅管理员；不能删除自己 |

> **前端对齐说明**: 前端文档中 `/auth/info` 已确认。`/auth/logout` 在前端文档中未单独列出，前端初版可能直接清 token，后端可先提供空实现。

### 5.2 视频源管理模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/streams` | GET | 获取可切换视频源列表 | `status`、`keyword` | 视频源列表、RTMP 地址 | 首页下拉和后台管理共用 |
| 🟢 | `/streams` | POST | 新增视频源 | `stream_name`、`stream_id`、`rtmp_url`、`remark` | 新增结果 | `stream_id` 需唯一且与推流端 Stream Key 一致；`rtmp_url` 格式为 `rtmp://IP:9090/live/{stream_id}` |
| 🟢 | `/streams/{stream_id}/status` | GET | 查询当前视频源推流状态 | `stream_id` | 在线状态、延迟、断流时间 | SpringBoot 请求 Nginx `/stat` XML 并解析 `<publish active>` 判断在线状态 |
| 🟡 | `/streams/enabled` | GET | 获取已启用的视频源 | 无 | `stream_id`、名称、预览地址、状态 | 首页下拉和 AI 同步复用 |
| 🟡 | `/streams/{id}` | GET | 视频源详情 | `id` | 视频源详情、关联区域数、规则数 | 管理页详情弹窗 |
| 🟡 | `/streams/{id}` | PUT | 编辑视频源 | `stream_name`、`rtmp_url`、`status`、`remark` | 更新结果 | 管理员操作 |
| 🟡 | `/streams/{id}` | DELETE | 删除视频源 | `id` | 删除结果 | 有关联告警时建议软删除 |
| 🟡 | `/streams/{stream_id}/preview-url` | GET | 获取前端播放地址 | `stream_id` | `mjpeg_url`、`rtmp_url`、`hls_url` | SpringBoot 返回各协议地址，不代理视频流 |

> ⚠️ **路径参数区分**：`/streams/{stream_id}/...` 中的 `stream_id` 是**业务标识符**（如 `classroom_01`，与推流端 Stream Key 一致），而 `/streams/{id}` 中的 `id` 是**数据库自增主键**。`/streams` GET 返回的数据中同时包含 `id` 和 `stream_id`，前端应根据接口路径使用对应的标识符：
> - 详情/编辑/删除接口使用数据库 `id`（`/streams/{id}` GET/PUT/DELETE）
> - 状态查询、预览地址等实时接口使用业务 `stream_id`（`/streams/{stream_id}/status`、`/streams/{stream_id}/preview-url`）

### 5.3 人员与人脸管理模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/students` | GET | 人员库列表 | `class_name`、`keyword`、`face_registered`、分页 | 人员分页列表 | 管理人员基础信息 |
| 🟢 | `/students` | POST | 新增人员 | `student_no`、`name`、`class_name` | 新增结果 | 人脸注册的前置步骤，先建人员再注册人脸 |
| 🟢 | `/students/{id}/face` | POST | **人脸注册** | `image`（base64） | 注册成功/失败、质量评分 | 前端发图→SpringBoot 校验→调 AI 提取特征→入库 |
| 🟡 | `/students/{id}` | GET | 人员详情 | `id` | 人员信息、人脸注册状态 | 详情页 |
| 🟡 | `/students/{id}` | PUT | 编辑人员 | `name`、`class_name`、`status`、`remark` | 更新结果 | 管理员操作 |
| 🟡 | `/students/{id}` | DELETE | 删除人员 | `id` | 删除结果 | 建议软删除 |
| 🟡 | `/students/{id}/face-features` | GET | 查看人脸特征记录 | `id` | 特征元数据（不含完整向量） | 只返回图片路径、创建时间等 |
| 🟡 | `/students/{id}/face-features/{feature_id}` | DELETE | 删除某条人脸特征 | `feature_id` | 删除结果 | 删除后通知 AI 刷新缓存 |

> **前端对齐说明**: 前端文档中使用 `/students/{id}/face`（不是 `/students/{id}/face-register`），已确认对齐。

### 5.4 区域配置模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/zones` | GET | 查询区域配置 | `stream_id`、`zone_type` | 区域名称、坐标、阈值 | 前端用于区域管理和告警匹配；持久化区域由 AI 视频流绘制，前端不重复叠加 |
| 🟡 | `/zones` | POST | 新增区域 | `stream_id`、`zone_name`、`zone_type`、`coordinates`、`threshold_seconds`、`safe_distance` | 保存结果 | `coordinates` 为归一化坐标 JSON；`safe_distance` 用于接近预警（人员距边缘低于此值时触发 `danger_zone_approach`） |
| 🟡 | `/zones/{id}` | GET | 区域详情 | `id` | 区域详情 | 编辑弹窗回填 |
| 🟢 | `/zones/{id}` | PUT | 修改区域 | `zone_name`、`zone_type`、`coordinates`、`threshold_seconds`、`safe_distance`、`enabled` | 更新结果 | `zone_type` 限 `danger`/`seat`/`phone_forbidden`/`roi`；修改后通知 AI 刷新 |
| 🟡 | `/zones/{id}` | DELETE | 删除区域 | `id` | 删除结果 | 建议软删除 |
| 🟡 | `/streams/{stream_id}/zones` | GET | 获取某视频源全部区域 | `stream_id` | 区域列表 | 首页初始化或 AI 同步可用 |

**坐标格式约定**（使用归一化比例 `0-1`，不存像素值）：

```json
{
  "coordinates": [
    {"x": 0.12, "y": 0.18},
    {"x": 0.48, "y": 0.18},
    {"x": 0.46, "y": 0.52},
    {"x": 0.10, "y": 0.50}
  ]
}
```

### 5.5 行为规则模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/rules` | GET | 查询规则开关和阈值 | `rule_type` | 规则列表 | 规则配置页核心接口 |
| 🟢 | `/rules/{id}` | PUT | 更新规则 | `enabled`、`threshold_seconds`、`confidence_threshold`、`cooldown_seconds`、`config_json` | 更新结果 | 阈值不建议前端写死；`confidence_threshold` 和 `cooldown_seconds` 为 AI 端直接使用的独立字段 |
| 🟡 | `/rules/{id}` | GET | 规则详情 | `id` | 规则详情 | 编辑弹窗回填 |
| 🟡 | `/rules` | POST | 新增规则 | `rule_type`、`threshold_seconds`、`confidence_threshold`、`cooldown_seconds`、`enabled`、`config_json` | 新增结果 | 初版可预置规则，此接口作为扩展 |
| 🟡 | `/rules/{id}` | DELETE | 删除规则 | `id` | 删除结果 | 初版可不开放删除 |

**规则初始阈值建议**：

| 规则类型 | 初始阈值建议 | 说明 | 状态 |
| --- | --- | --- | --- |
| `phone_usage` | 连续 3 秒 | 过滤短暂看时间的动作 | 🟡 |
| `flame_detected` | 连续检测置信度达标 | 火情最高优先级 | 🟡 |
| `danger_zone_intrusion` | 进入即告警 | 人员进入危险区域 | 🟡 |
| `danger_zone_stay` | 停留超 N 秒 | 危险区域停留超时 | 🟡 |
| `danger_zone_approach` | 距边缘低于 `safe_distance` | 接近预警，比进入更早触发 | 🟡 |
| `head_down` | 连续 N 秒 | 课堂注意力异常 | 🟡 |
| `leave_seat` | 连续 N 秒 | 离座未返回 | 🟡 |
| `fall_detected` | 检测到即告警 | 人员摔倒检测 | 🟡 |

> ⚠️ 阈值是调参结果，初期使用建议值，后续根据实际模型表现和业务需求调整。Config 应存储在数据库或配置表中，不要硬编码。

### 5.6 告警管理模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/alerts` | GET | 告警列表和历史追溯 | `time_range`、`alert_type`、`status`、`level`、`stream_id`、`page`、`page_size` | 告警分页、统计数量 | 告警管理页核心接口 |
| 🟢 | `/alerts/{id}` | GET | 告警详情 | `id` | 告警详情、截图URL、视频片段URL | URL 指向 Nginx 9092 端口 |
| 🟢 | `/alerts/{id}/status` | PUT | 标记告警状态 | `status`、`remark`、`handler_id` | 更新结果 | 支持 unhandled / processing / handled / false_alarm / ignored |
| 🟢 | `/alert-stats` | GET | 首页统计卡片 | `date_range`、`stream_id` | 今日告警数、未处理数、分类统计 | 首页指标卡 |
| 🟡 | `/alerts/{id}/feedback` | POST | 误报反馈 | `feedback_type`、`remark` | 反馈结果 | 后续可用于模型优化 |
| 🔵 | `/alerts/export` | GET | 导出告警记录 | 同查询条件 | Excel/CSV 文件 | 后续扩展 |

> **前端对齐说明**: 前端文档中使用 `/alert-stats`（不是 `/alerts/statistics`），已确认对齐。告警列表入参中的 `time_range`、分页字段名（`page`、`page_size`）与前端文档保持一致。

**告警详情返回示例**：

```json
{
  "id": 1001,
  "stream_id": "classroom_01",
  "stream_name": "一号教室",
  "student_id": 12,
  "student_name": "张三",
  "alert_type": "phone_usage",
  "level": "warning",
  "status": "unhandled",
  "confidence": 0.91,
  "snapshot_url": "/snapshots/20260707/phone_0001.jpg",
  "record_url": "/classroom_01-2026-07-07-10_30_00.mp4",
  "occurred_at": "2026-07-07T10:21:35+08:00",
  "handled_at": null,
  "remark": null
}
```

> ⚠️ **字段映射说明**：
> - `snapshot_url`（告警详情返回）对应 AI 入库时的 `snapshot_path`（入库请求字段）。AI 传路径，SpringBoot 存储后以 URL 字段返回给前端。
> - `record_url` 初版指向 Nginx 自动录像文件（如 `/classroom_01-2026-07-07-10_30_00.mp4`），不依赖 AI 视频切片。初版无切片能力时，此字段指向整段录像，后续切片能力上线后改为指向告警片段。
> - 所有路径均为相对路径（以 `/` 开头），前端拼上 `VITE_NGINX_BASE`（9092 端口）访问。后端不要返回带服务器 IP 的绝对路径。

### 5.7 录像与文件资源模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/recordings` | GET | 查询录像或视频片段列表 | `stream_id`、`time_range`、`event_id` | 录像文件列表、访问地址 | Nginx 自动录像 .flv→.mp4，仅保留 7 天；优先返回 .mp4 地址供前端 `<video>` 播放 |
| 🟡 | `/files/snapshots/{alert_id}` | GET | 查看告警截图 | `alert_id` | 图片资源 | 可做权限校验后转发或重定向 |
| 🔵 | `/files/recordings/{recording_id}` | GET | 查看/下载视频片段 | `recording_id` | 视频资源 | 后续接入录像回放 |

### 5.8 系统概览与日志模块

| 状态 | 接口 | 方法 | 使用场景 | 主要入参 | 主要返回 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 🟢 | `/system/health` | GET | 服务状态展示 | 无 | RTMP、AI 服务、后端、数据库状态 | SpringBoot 统一探活各组件 |
| 🟢 | `/operation-logs` | GET | 查看操作审计 | `user_id`、`action`、`time_range`、分页 | 操作日志分页 | 管理员追溯 |
| 🟡 | `/dashboard/overview` | GET | 首页概览 | `stream_id`、`date` | 视频源数量、今日告警、待处理数、AI 状态 | 更丰富的首页指标 |

> **前端对齐说明**: 前端文档中 `/system/health` 用于系统运行概览。`/alert-stats` 已单独覆盖首页统计卡片场景，`/dashboard/overview` 作为补充概览接口（🟡 待定）。

---

## 六、AI 服务调用 SpringBoot 的接口

> ⚠️ 以下接口由 Flask AI 服务调用，SpringBoot 负责实现。
> **开发阶段**可直接访问；**生产环境**建议限制内网访问 + 内部 token 或签名校验。
>
> 接口路径与 AI 服务接口文档（V0.1）保持一致，部分接口复用前端接口路径。

### 6.1 告警入库（AI → SpringBoot）

```http
POST /alerts/ai
Content-Type: application/json
```

| 状态 | 使用场景 | 说明 |
| --- | --- | --- |
| 🟡 | AI 检测到异常后回写正式告警 | **核心接口**，需幂等处理（相同 `event_id` 不重复插入） |

**请求体**：

```json
{
  "event_id": "evt_20260707102030001",
  "stream_id": "classroom_01",
  "alert_type": "flame_detected",
  "alert_name": "明火检测",
  "level": "high",
  "confidence": 0.91,
  "occurred_at": "2026-07-07T10:20:30+08:00",
  "duration_seconds": 1.5,
  "student_id": null,
  "target_info": {
    "track_id": "fire_1",
    "bbox": [300, 120, 380, 240]
  },
  "zone_id": null,
  "snapshot_path": "/snapshots/20260707/evt_20260707102030001.jpg",
  "record_path": "/records/20260707/classroom_01.flv",
  "event_time_offset": 630.5,
  "extra": {
    "model": "yolo_fire_v1",
    "rule": "flame_confidence_duration"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `event_id` | string | 是 | AI 生成的事件唯一 ID，SpringBoot 用于幂等去重 |
| `stream_id` | string | 是 | 视频源 ID |
| `alert_type` | string | 是 | 告警类型，见枚举约定 |
| `alert_name` | string | 否 | 告警中文名称 |
| `level` | string | 是 | `info` / `warning` / `high` |
| `confidence` | float | 否 | 置信度 0-1 |
| `occurred_at` | string | 是 | 事件发生时间，ISO 8601 格式 |
| `duration_seconds` | float | 否 | 持续时间（秒） |
| `student_id` | string | 否 | 关联学生 ID，陌生人或无法识别时为空 |
| `target_info` | object | 否 | 目标信息（track_id、bbox 像素坐标） |
| `zone_id` | int | 否 | 关联区域 ID |
| `snapshot_path` | string | 否 | 截图文件路径（Nginx 静态目录下） |
| `record_path` | string | 否 | 录像文件路径（Nginx 静态目录下） |
| `event_time_offset` | float | 否 | 事件在录像中的时间偏移（秒），用于定位告警时刻在录像中的位置 |
| `extra` | object | 否 | 扩展信息（模型名、触发规则等） |

**SpringBoot 返回**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "alert_id": 10086,
    "status": "unhandled"
  }
}
```

> ⚠️ `event_id` 必须全局唯一。SpringBoot 做幂等处理：相同 `event_id` 的重复请求直接返回已有 `alert_id`，不重复插入。

#### 6.1.1 候选事件 → 告警入库字段映射

AI 端候选事件（`/analysis/events` 返回）与 SpringBoot 告警入库请求（`POST /alerts/ai`）的字段对应关系：

| AI 候选事件字段 | SpringBoot 告警入库字段 | 映射说明 |
| --- | --- | --- |
| `event_id` | `event_id` | 直接映射，用于幂等去重 |
| `stream_id` | `stream_id` | 直接映射 |
| `event_type` | `alert_type` | 字段名不同，值一致（如 `phone_usage`） |
| `event_name` | `alert_name` | 字段名不同，可选的显示名称 |
| `level` | `level` | 直接映射 |
| `confidence` | `confidence` | 直接映射 |
| `occurred_at` | `occurred_at` | 直接映射，ISO 8601 格式 |
| `duration_seconds` | `duration_seconds` | 直接映射 |
| `target.track_id` | `target_info.track_id` | 嵌套 → 扁平化：AI 端 `target` 对象拆分 |
| `target.student_id` | `student_id` | 提升为顶级字段 |
| `target.student_name` | — | 不传，SpringBoot 根据 `student_id` 查询 |
| `target.bbox` | `target_info.bbox` | 嵌套 → 扁平化 |
| `zone.zone_id` | `zone_id` | 提升为顶级字段 |
| `zone.zone_name` | — | 不传，SpringBoot 根据 `zone_id` 查询 |
| `snapshot_path` | `snapshot_path` | 直接映射 |
| `record_file_path` | `record_path` | 字段名不同，统一为 `record_path` |
| `event_time_offset` | `event_time_offset` | 直接映射（可选） |

> ⚠️ AI 开发者在将候选事件转为正式告警入库时，需要按上表进行字段名和结构转换。核心变化：`event_type` → `alert_type`，嵌套 `target`/`zone` → 扁平化 + 顶级字段。

### 6.2 获取视频源配置（AI → SpringBoot）

```http
GET /streams?status=enabled
```

AI 启动或配置刷新时调用，获取所有已启用的视频源及其 RTMP 地址。

> 复用前端 `/streams` 接口，AI 只需 `stream_id`、`stream_name`、`rtmp_url`、`status` 字段。

| 状态 | 说明 |
| --- | --- |
| 🟡 | 与前端共用接口，确保返回字段包含 `rtmp_url` |

### 6.3 获取区域配置（AI → SpringBoot）

```http
GET /zones?stream_id=classroom_01
```

AI 按视频源拉取区域配置，坐标用于判断人员是否进入危险区域。

> 复用前端 `/zones` 接口。返回的 `zone_type` 值为 `danger`、`seat`、`phone_forbidden`、`roi`。

| 状态 | 说明 |
| --- | --- |
| 🟡 | 与前端共用接口，coordinates 为归一化坐标 |

### 6.4 获取行为规则（AI → SpringBoot）

```http
GET /rules
```

AI 获取所有启用的行为检测规则及阈值。

> 复用前端 `/rules` 接口。返回字段需包含 `rule_type`、`enabled`、`threshold_seconds`、`confidence_threshold`、`cooldown_seconds`、`config_json`。

| 状态 | 说明 |
| --- | --- |
| 🟡 | 与前端共用接口，规则变更后 SpringBoot 应通知 AI 刷新 |

### 6.5 获取人脸特征库（AI → SpringBoot）

```http
GET /students/face-features
```

AI 启动或收到刷新通知后调用，获取全量人脸特征向量用于实时识别。

> ⚠️ **此接口不对前端开放**。返回包含 `feature_vector`，前端不应获取原始特征数据。

| 状态 | 使用场景 | 主要返回 | 备注 |
| --- | --- | --- | --- |
| 🟡 | AI 启动加载 / 定时刷新 / 收到 reload 后 | `student_id`、`student_name`、`class_name`、`feature_vector`、`enabled` | 需做接口鉴权，禁止前端访问 |

**关键返回字段**：

```json
{
  "student_id": "2024001",
  "student_name": "张三",
  "class_name": "软件工程 1 班",
  "feature_vector": [0.0123, -0.0345, 0.0678],
  "enabled": true
}
```

### 6.6 AI 调用 SpringBoot 接口汇总

| 状态 | 接口 | 方法 | AI 使用场景 | 复用前端 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 🟡 | `/alerts/ai` | POST | 写入确认告警 | 否 | 专用接口，幂等处理 |
| 🟡 | `/streams` | GET | 获取视频源及 RTMP 地址 | 是 | AI 只需 `status=enabled` 过滤 |
| 🟡 | `/zones` | GET | 获取区域配置 | 是 | 按 `stream_id` 筛选 |
| 🟡 | `/rules` | GET | 获取行为规则及阈值 | 是 | AI 需 `confidence_threshold`、`cooldown_seconds` 等字段 |
| 🟡 | `/students/face-features` | GET | 同步人脸特征向量 | 否 | **禁止前端访问**，需单独鉴权 |

---

## 七、SpringBoot 调用 AI 服务的接口

> 以下接口由 Flask AI 服务提供，SpringBoot 需要封装 `AiClient` 调用。不要在 Controller 中直接写 HTTP 调用。
>
> AI 服务 Base URL 通过配置项管理：
> ```yaml
> ai:
>   base-url: http://39.106.209.208:5000
> ```

### 7.1 人脸特征提取

```http
POST {AI_BASE_URL}/face/feature/extract
Content-Type: application/json
```

| 状态 | 调用场景 | 说明 |
| --- | --- | --- |
| 🟡 | 前端调用 `/students/{id}/face` 注册人脸时，SpringBoot 内部调用此接口 | 提取成功后 SpringBoot 将特征向量写入 `face_feature` 表 |

**请求体**：

```json
{
  "student_id": "2024001",
  "image": "/9j/4AAQSkZJRg...",
  "image_type": "base64"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `student_id` | string | 否 | 人员 ID，AI 原样返回 |
| `image` | string | 是 | base64 图片内容，可带或不带 dataURL 前缀 |
| `image_type` | string | 否 | 默认 `base64` |

**返回示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "student_id": "2024001",
    "face_count": 1,
    "feature_dim": 512,
    "feature_vector": [0.0123, -0.0345, 0.0678],
    "quality": {
      "score": 0.91,
      "brightness": "normal",
      "blur": "low"
    },
    "bbox": [160, 80, 320, 260]
  }
}
```

**错误场景**：

| 场景 | code | message |
| --- | --- | --- |
| 未检测到人脸 | 40002 | no face detected |
| 多个人脸 | 40003 | multiple faces detected |
| 图片无法解析 | 40001 | invalid image |
| 人脸模型未加载 | 50001 | face model not loaded |

### 7.2 刷新人脸特征缓存

```http
POST {AI_BASE_URL}/face/features/reload
Content-Type: application/json
```

| 状态 | 调用场景 | 说明 |
| --- | --- | --- |
| 🟡 | SpringBoot 新增或更新人脸特征后，通知 Flask 重新加载特征库 | 可选：Flask 也可定时调用 `/students/face-features` 增量同步 |

**请求体**：

```json
{
  "scope": "all",
  "student_id": null
}
```

**返回示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "loaded_count": 126,
    "updated_at": "2026-07-07T10:20:30+08:00"
  }
}
```

### 7.3 刷新配置缓存

```http
POST {AI_BASE_URL}/config/reload
Content-Type: application/json
```

| 状态 | 调用场景 | 说明 |
| --- | --- | --- |
| 🟡 | SpringBoot 修改视频源、区域或规则后，通知 Flask 重新拉取配置 | 可按需指定刷新范围 |

**请求体**：

```json
{
  "stream_id": "classroom_01",
  "reload_items": ["streams", "zones", "rules"]
}
```

**返回示例**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "stream_id": "classroom_01",
    "streams_loaded": 1,
    "zones_loaded": 3,
    "rules_loaded": 8
  }
}
```

### 7.4 查询模型运行状态

```http
GET {AI_BASE_URL}/model/status
```

| 状态 | 调用场景 | 说明 |
| --- | --- | --- |
| 🟡 | `/system/health` 探活时调用，汇总 AI 模型状态 | 也可用于运维调试页 |

### 7.5 SpringBoot → AI 接口汇总

| 状态 | AI 接口 | 方法 | 调用场景 | 主要入参 | 主要返回 |
| --- | --- | --- | --- | --- | --- |
| 🟡 | `/face/feature/extract` | POST | 人脸注册时提取特征 | `image`(base64)、`student_id` | `feature_vector`(512维)、`face_count`、`quality` |
| 🟡 | `/face/features/reload` | POST | 人脸变更后通知 AI 刷新特征库 | `scope`、`student_id` | `loaded_count`、`updated_at` |
| 🟡 | `/config/reload` | POST | 规则/区域/视频源变更后通知 AI 刷新 | `stream_id`、`reload_items` | 各类型加载数量 |
| 🟡 | `/model/status` | GET | 系统健康检查时查询 AI 状态 | 无 | 模型加载状态、版本、推理耗时、流状态 |

> ⚠️ `/video_feed/{stream_id}` 返回 MJPEG 流，前端通过 `<img>` 标签直连 Flask 渲染。SpringBoot 在 `/streams/{stream_id}/preview-url` 中返回该地址即可，**不要代理视频流**。

---

## 八、数据库表与接口关系

| 表名 | 用途 | 关键字段 | 主要关联接口 | 状态 |
| --- | --- | --- | --- | --- |
| `user` | 登录用户/管理员 | `id`、`username`、`password_hash`、`role`、`status` | `/auth`、`/users` | 🟢 |
| `student` | 人员基础信息 | `id`、`student_no`、`name`、`class_name`、`face_registered` | `/students` | 🟢 |
| `face_feature` | 人脸特征向量（512维） | `id`、`student_id`、`feature_vector`、`image_path`、`version` | `/students/{id}/face`、`/students/face-features` | 🟡 |
| `video_stream` | 视频源配置 | `id`、`stream_id`、`stream_name`、`rtmp_url`、`status` | `/streams` | 🟢 |
| `danger_zone` | 区域配置 | `id`、`stream_id`、`zone_name`、`zone_type`、`coordinates`、`threshold_seconds`、`safe_distance` | `/zones` | 🟡 |
| `behavior_rule` | 行为检测规则 | `id`、`rule_type`、`threshold_seconds`、`confidence_threshold`、`cooldown_seconds`、`enabled`、`config_json` | `/rules` | 🟡 |
| `alert_event` | 告警事件记录 | `id`、`event_id`、`stream_id`、`student_id`、`alert_type`、`level`、`confidence`、`snapshot_path`、`record_path`、`event_time_offset`、`status`、`occurred_at` | `/alerts`、`/alert-stats`、`/alerts/ai` | 🟢 |
| `operation_log` | 操作审计日志 | `id`、`user_id`、`action`、`target_type`、`target_id` | `/operation-logs` | 🔵 |

**表关系**：

- `student` 与 `face_feature`：**一对多**（一个学生可有多条人脸采集记录）
- `video_stream` 与 `danger_zone`：**一对多**（不同视频源有不同区域配置）
- `behavior_rule`：初版做**全局规则**，后续可扩展为按 `stream_id` 或场景模板
- `alert_event`：关联 `student`（陌生人或无法识别时 `student_id` 为空）
- `alert_event.event_id`：**唯一索引**，用于 AI 回写幂等

---

## 九、关键业务流程

### 9.1 实时视频分析 → 告警生成流程 🟢

```
摄像头/OBS → RTMP推流 → Nginx(9090)
                              ↓
                    Flask AI 拉流分析
                    （从 SpringBoot 拉取区域、规则、人脸特征缓存）
                              ↓
                    检测到异常 → 去抖确认
                              ↓
                    POST /alerts/ai → SpringBoot 入库
                              ↓
                    前端 GET /alerts 展示告警列表
```

### 9.2 人脸注册流程 🟢

```
管理员上传人脸图片（前端）
        ↓
POST /students/{id}/face → SpringBoot
        ↓
SpringBoot: 校验 student 存在、图片格式
        ↓
SpringBoot: 调 AI POST /face/feature/extract
        ↓
AI: 校验单帧人脸数量、提取 512 维特征向量、质量评分
        ↓
SpringBoot: 将特征向量写 face_feature，更新 student.face_registered = true
        ↓
SpringBoot: 调 AI POST /face/features/reload 通知刷新
（或等待 AI 下次主动调用 GET /students/face-features 增量同步）
```

### 9.3 告警状态处理流程 🟢

```
AI 写入告警 → alert_event.status = "unhandled"
        ↓
前端告警列表展示 → 教师/管理员查看详情
        ↓
PUT /alerts/{id}/status → processing / handled / false_alarm / ignored
        ↓
SpringBoot: 写入处理时间、处理人、备注
        ↓
若标记为 false_alarm → 可调 POST /alerts/{id}/feedback 记录误报原因
```

---

## 十、开发优先级与路线

### 🥇 第一优先级（MVP 核心）

- [ ] SpringBoot + MyBatis + MySQL 基础工程搭建
- [ ] Swagger / springdoc-openapi 接入（`/swagger-ui.html` 可访问）
- [ ] 统一返回结构、全局异常处理、分页封装
- [ ] `/auth/login` + `/auth/info`（JWT 简化版）
- [ ] `/streams` GET + POST（视频源基础 CRUD）
- [ ] `/streams/{stream_id}/status` GET
- [ ] `/students` GET + POST（人员基础管理）
- [ ] `/zones` GET
- [ ] `/rules` GET + `/rules/{id}` PUT
- [ ] `/alerts` GET + `/alerts/{id}` GET + `/alerts/{id}/status` PUT
- [ ] `/alert-stats` GET
- [ ] `/system/health` GET
- [ ] Swagger `frontend-api` 分组，确保前端可联调

### 🥈 第二优先级（AI 联调 + 完整 CRUD）

- [ ] `/students/{id}/face` POST（人脸注册 → 调 AI `/face/feature/extract` → 入库）
- [ ] AI 调用接口：`POST /alerts/ai`（幂等）、`GET /students/face-features`（特征同步）
- [ ] 视频源、人员、区域、规则的完整 CRUD（详情、编辑、删除）
- [ ] `/recordings` GET（录像片段列表）
- [ ] 配置变更后通知 AI 刷新：`POST /config/reload`、`POST /face/features/reload`

### 🥉 第三优先级（完善 + 扩展）

- [ ] `/operation-logs` GET（操作审计）
- [ ] 操作日志 AOP 自动记录
- [ ] `/users` 用户管理 CRUD
- [ ] WebSocket / SSE 实时告警推送（减少前端轮询）
- [ ] 告警导出 Excel/CSV
- [ ] 更细粒度的权限控制

---

## 十一、当前阶段待确认问题

| # | 问题 | 当前方案 | 影响范围 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | SpringBoot 版本 | 建议 Spring Boot 3.x + Java 17 | 依赖选型、Swagger 接入方式 | 🟡 |
| 2 | Swagger 依赖 | `springdoc-openapi-starter-webmvc-ui` 2.x | Swagger 分组、注解写法 | 🟡 |
| 3 | JWT 鉴权粒度 | 初版区分 admin / teacher 即可 | 接口权限校验、操作日志 | 🟢 |
| 4 | 人脸特征存储方式 | 初版 MySQL TEXT/JSON，后续可迁向量库 | `face_feature` 表结构 | 🟡 |
| 5 | AI 是否每帧回传 | **否**。SpringBoot 只存确认告警 + 低频心跳 | 数据库写入压力、前后端通信 | 🟢 |
| 6 | 前端直连 vs 后端代理视频流 | 前端直连 Flask / Nginx，SpringBoot 只返回地址 | 网络架构、跨域配置 | 🟢 |
| 7 | AI 专用接口安全 | `POST /alerts/ai` 和 `GET /students/face-features` 需内网隔离 + token，`/students/face-features` 禁止前端访问 | AI 接口鉴权 | 🟡 |
| 8 | 区域/规则变更后如何通知 AI | SpringBoot 主动调 AI `POST /config/reload`；AI 也可定时轮询 `/streams`、`/zones`、`/rules` | AI 配置刷新机制 | 🟡 |
| 9 | 告警实时推送方案 | 初版前端 3-5 秒轮询 `/alerts`，后续升级 WebSocket | 前端实时告警卡片 | 🟡 |
| 10 | 文件存储路径规范 | Nginx 静态目录，路径由 AI 写入时确定 | 截图/录像访问 | 🟡 |
| 11 | 活体检测/防欺骗认证 | 本期不实现，后续扩展 | 人脸注册安全 | 🔵 |
| 12 | 钉钉通知/告警逐级上报 | 本期不实现，后续扩展 | 告警通知模块 | 🔵 |
| 13 | AI 工作流自动生成监控日报 | 本期不实现，后续扩展 | 统计报表模块 | 🔵 |
| 14 | 行动轨迹追踪 | 本期不实现，后续扩展 | 轨迹存储与展示 | 🔵 |
| 15 | 异常声学事件检测 | 本期不实现，后续扩展 | 音频分析模块 | 🔵 |

---

## 十二、后端交付检查清单

| # | 检查项 | 完成标准 |
| --- | --- | --- |
| 1 | Swagger 可访问 | 启动后浏览器打开 `/swagger-ui.html` 或 `/swagger-ui/index.html` |
| 2 | OpenAPI JSON 可导入 | `/v3/api-docs` 可导入 Apifox/Postman |
| 3 | Controller 按调用方分组 | 前端接口和 AI 专用接口（`/alerts/ai`、`/students/face-features`）分组清晰 |
| 4 | DTO/VO 字段有 `@Schema` | 描述、示例值、必填校验齐全 |
| 5 | 列表接口统一分页 | `page`、`page_size`、`total`、`records` |
| 6 | 告警写入幂等 | 相同 `event_id` 不重复插入 |
| 7 | 异常返回统一格式 | 400/401/403/404/409/500 均有统一结构 |
| 8 | 关键字段唯一约束 | `stream_id`、`student_no`、`event_id` 数据库唯一索引 |
| 9 | Swagger 示例可直接调试 | request/response example 真实可用 |
| 10 | 跨域配置正确 | 前端 `localhost:5173` 等开发端口可正常请求 |

---

## 十三、建议包结构

```text
com.smartclass.monitor
├── config              # Swagger、跨域、JWT 拦截器、Jackson 配置
├── common              # 统一返回 ApiResponse、分页 PageResult、异常、枚举
├── controller          # 对前端公开的 REST Controller
│   ├── AuthController
│   ├── StreamController
│   ├── StudentController
│   ├── ZoneController
│   ├── RuleController
│   ├── AlertController
│   ├── RecordingController
│   ├── SystemController
│   └── OperationLogController
├── controller.ai        # AI 服务调用的专用接口（POST /alerts/ai、GET /students/face-features）
│   └── AiAlertController
├── service             # 业务逻辑层
├── mapper              # MyBatis Mapper 接口
├── entity              # 数据库实体
├── dto                 # 请求 DTO（入参）
├── vo                  # 返回 VO（出参）
└── integration         # 调用 Flask AI 服务的客户端（AiClient）
```

---

## 附录 A: 前端接口速查表

> 摘自前端文档，供后端快速对照。完整的前端视角说明见前端项目文档。

| 前端页面 | 使用的后端接口 | 数据流向 |
| --- | --- | --- |
| 登录页 | `POST /auth/login` | 前端 → SpringBoot |
| 路由守卫 | `GET /auth/info` | 前端 → SpringBoot |
| 首页实时画面 | `GET {AI}/video_feed/{stream_id}` | 前端 → Flask（MJPEG 流） |
| 首页指标卡 | `GET /alert-stats`、`GET /system/health` | 前端 → SpringBoot |
| 右侧告警栏 | `GET /alerts`（轮询）或 WebSocket | 前端 → SpringBoot |
| 告警管理页 | `GET /alerts`、`GET /alerts/{id}`、`PUT /alerts/{id}/status` | 前端 → SpringBoot |
| 告警截图/录像 | `GET {Nginx}/{path}` | 前端 → Nginx 9092 |
| 人员库页 | `GET /students`、`POST /students` | 前端 → SpringBoot |
| 人脸注册 | `POST /students/{id}/face` | 前端 → SpringBoot → Flask AI |
| 视频源管理 | `GET /streams`、`POST /streams`、`GET /streams/{stream_id}/status` | 前端 → SpringBoot |
| 实时监控 / 区域配置页 | `POST /zones`；`GET/PUT/DELETE /zones` | 监控画面拖拽新增；配置页查询、编辑、启停和删除；持久化区域由 AI 视频流统一标注 |
| 规则配置页 | `GET /rules`、`PUT /rules/{id}` | 前端 → SpringBoot |
| 录像查询 | `GET /recordings` | 前端 → SpringBoot |
| 系统日志页 | `GET /operation-logs` | 前端 → SpringBoot |
| AI 研判助手 | `GET {AI}/analysis/summary/{stream_id}` | 前端 → Flask |

---

## 附录 B: 变更记录

| 日期 | 版本 | 变更内容 | 原因 |
| --- | --- | --- | --- |
| 2026-07-08 | v2.1 | 按三端文档审查清单修正：新增 `fall_detected`、`danger_zone_approach` 事件类型；区域增加 `safe_distance` 参数；`/rules/{id}` PUT 补充 `confidence_threshold`、`cooldown_seconds`；`video_clip_url` → `record_url`；图片格式统一 base64；补充 `stream_id` vs `id` 说明；补充 `stream_offline` 双重检测职责；补充候选事件→告警字段映射表；补充可选加分项设计状态标注 | 三端文档审查问题修复 |
| 2026-07-07 | v2.0 | 重写文档；以前端文档为基准对齐接口路径；引入双轨制（已确定/待定/扩展）状态标记；精简结构 | 项目起步，以实际联调为准 |
| 2026-07-07 | v1.0 | 初始版本 | 项目规划阶段 |

> 📝 后续每次接口变更请在此记录，并同步更新对应接口的状态标记。
