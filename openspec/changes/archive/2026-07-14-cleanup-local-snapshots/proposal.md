# 截图本地残留清理 + 钉钉上传通路改造

## 动机

AI 服务在检测到告警事件时，`AnalysisService._save_snapshot()` 会将截图写入本地 `backend_ai/static/snapshots/{day}/{event_id}.jpg`，然后通过 `SnapshotPusher` 异步 SCP 推送到云服务器 `/data/snapshots/`。前端取截图走的是云服务器 Nginx 9092 端口，这条通路是正确的。

但存在三个问题：

### 问题一：截图存本地后永远不清理

`_save_snapshot()` 调用 `cv2.imwrite()` 写入本地文件后，调用 `snapshot_pusher.push_async()` 推送到云服务器，但**本地文件永远不会被删除**。每次告警都会在 AI 服务的 `static/snapshots/` 目录下留下一个 `.jpg` 文件，日积月累磁盘会被吃光。这就是"随地拉shit"——拉完不冲。

### 问题二：钉钉通知依赖本地截图文件

`AlertClient._resolve_local_snapshot()` 将 `/snapshots/xxx` 路径转换为本地绝对路径，`dingtalk_service._upload_image()` 通过 `open(file_path, "rb")` 读取本地文件上传到钉钉。如果直接删除本地截图，钉钉通知中的告警图片上传会失败。

这形成了设计矛盾：想清理本地文件（问题一），但钉钉需要读本地文件（问题二）。

### 问题三：Flask `/snapshots/` 端点是死代码

`app.py` 中注册了 `GET /snapshots/<path:filename>` 路由，从本地 `static/snapshots/` 提供文件服务。但前端取截图走的是云服务器 Nginx 9092，没有任何消费者使用这个端点。留着容易误导，暗示"本地截图是可访问的"这种过时设计。

此外，`image_utils.py` 中的 `save_snapshot()` 函数全项目无人调用，属于死代码。

## 范围

### 一、截图推送成功后清理本地文件

修改 `SnapshotPusher._push()`：SCP 推送成功后，删除本地文件。具体逻辑：

1. SCP 推送成功后，调用 `local_path.unlink()` 删除本地截图文件
2. 删除后检查父目录是否为空，若为空则删除父目录（避免留下空目录树）
3. 推送失败时保留本地文件（容错：下次推送可重试，钉钉通知也能用）
4. 在日志中记录清理动作

### 二、钉钉上传改为从云服务器下载

修改 `AlertClient._resolve_local_snapshot()` 的解析策略：

1. 优先检查本地文件是否存在（兼容推送失败、本地文件仍在的场景）
2. 本地文件不存在时，将 `/snapshots/{day}/{event_id}.jpg` 转换为云服务器 HTTP URL（`http://{host}:9092/snapshots/{day}/{event_id}.jpg`）
3. `dingtalk_service._upload_image()` 支持接收 HTTP URL：当参数为 HTTP URL 时，先下载到临时文件再上传，上传后删除临时文件

这样即使本地截图已被清理，钉钉通知仍能正常工作。

### 三、移除 Flask `/snapshots/` 端点

删除 `app.py` 中的 `serve_snapshot` 路由。前端取截图走云服务器 Nginx，此端点无消费者。

### 四、移除 `image_utils.save_snapshot` 死代码

删除 `image_utils.py` 中无人调用的 `save_snapshot()` 函数。

## 不做

- 不引入对象存储（OSS/S3）替代 SCP 推送
- 不修改前端截图 URL 拼接逻辑（已正确走 Nginx 9092）
- 不修改 SpringBoot 侧 `snapshot_path` 的存储和映射逻辑
- 不修改 `AnalysisService._save_snapshot()` 的保存路径和返回值格式
- 不修改 `SnapshotPusher` 的推送协议（仍用 SCP）
- 不引入本地截图的定时清理任务（推送后即时清理即可）
- 不修改录像文件（`/records/`）的存储逻辑

## 影响模块

### backend_ai（Python / Flask）

- `services/snapshot_push.py`：`_push()` 方法增加推送成功后删除本地文件的逻辑
- `services/alert_client.py`：`_resolve_local_snapshot()` 增加本地文件不存在时回退到云服务器 HTTP URL 的逻辑；`AlertClient` 构造函数增加 `nginx_base_url` 参数
- `services/dingtalk_service.py`：`_upload_image()` 支持 HTTP URL 参数，自动下载临时文件后上传
- `app.py`：移除 `serve_snapshot` 路由；`AlertClient` 构造时传入 `nginx_base_url`
- `utils/image_utils.py`：移除无人调用的 `save_snapshot()` 函数
