# 截图本地残留清理 + 钉钉上传通路改造 — 技术设计

## Context

### 已有基础设施

**截图保存**：`AnalysisService._save_snapshot()` 将帧写入 `BASE_DIR/static/snapshots/{day}/{event_id}.jpg`，返回 `/snapshots/{day}/{event_id}.jpg`。`snapshot_root` 硬编码为 `BASE_DIR / "static" / "snapshots"`。

**截图推送**：`SnapshotPusher` 通过 SSH `mkdir -p` + SCP 异步推送截图到云服务器 `/data/snapshots/{day}/{event_id}.jpg`。推送失败仅 log warning，不影响告警流程。配置来自 `config/app.yaml` 的 `snapshot_remote` 节 + 环境变量覆盖。

**前端取截图**：`joinResourceUrl()` 将 `/snapshots/...` 与 `NGINX_BASE`（`http://39.106.209.208:9092`）拼接，通过 nginx 9092 的 `location /snapshots/ { alias /data/snapshots/; }` 从云服务器取图。此通路正确。

**钉钉通知**：`AlertClient.push_alert()` → `_resolve_local_snapshot()` 将 `/snapshots/xxx` 转换为本地绝对路径 → `dingtalk_service._upload_image()` 通过 `open(file_path, "rb")` 读本地文件上传到钉钉获取 `media_id` → 发送 Markdown 消息引用 `media_id`。

**Flask 本地端点**：`app.py` 注册了 `GET /snapshots/<path:filename>` 路由，`send_from_directory` 从本地 `static/snapshots/` 提供文件。无消费者。

**死代码**：`image_utils.save_snapshot()` 函数全项目无人调用。`AnalysisService._save_snapshot()` 使用自己的实现。

## Goals / Non-Goals

**Goals:**

1. SCP 推送成功后删除本地截图文件，避免磁盘无限增长
2. 推送失败时保留本地文件（容错）
3. 钉钉上传通路改为优先本地、回退云端，不再硬依赖本地文件存在
4. 移除 Flask `/snapshots/` 死路由
5. 移除 `image_utils.save_snapshot()` 死代码

**Non-Goals:**

- 不引入对象存储（OSS/S3）替代 SCP
- 不修改前端截图 URL 拼接逻辑
- 不修改 SpringBoot 侧 `snapshot_path` 的存储和映射
- 不修改 `_save_snapshot()` 的保存路径和返回值格式
- 不引入本地截图的定时清理任务
- 不修改录像文件的存储逻辑

## Decisions

| 决策                        | 选择                                                             | 理由                                                       |
| --------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------- |
| 本地清理时机                | SCP 推送成功后即时删除                                           | 最简单可靠，无需引入定时任务或后台扫描                     |
| 推送失败处理                | 保留本地文件，不删除                                             | 容错：下次无重试机制但文件仍在，钉钉通知可用               |
| 空目录清理                  | 删除文件后检查父目录是否为空，为空则删除                         | 避免留下空日期目录树                                       |
| 钉钉上传回退策略            | 本地文件存在 → 用本地；不存在 → 从云服务器 HTTP 下载临时文件     | 零风险过渡，推送成功后本地已删的场景走云端下载             |
| 临时文件管理                | `tempfile.NamedTemporaryFile(delete=False)` + 上传后 `os.unlink` | 跨平台安全，上传完即清理                                   |
| 云端 URL 构造               | `AlertClient` 新增 `nginx_base_url` 参数                         | 与现有 `snapshot_remote.host` 配置一致，显式传入而非硬编码 |
| Flask 死路由                | 直接删除                                                         | 无消费者，留着误导                                         |
| `image_utils.save_snapshot` | 直接删除                                                         | 全项目无人调用                                             |

## Architecture

### 改动前数据流

```
AI 检测到告警
    │
    ▼
_save_snapshot(frame, event_id)
    │
    ├── cv2.imwrite → 本地 static/snapshots/{day}/{event_id}.jpg  ← 💩 永远不清理
    ├── snapshot_pusher.push_async() → SCP 到云 /data/snapshots/  ← ✅
    └── 返回 "/snapshots/{day}/{event_id}.jpg"
           │
           ├── 存入数据库 (SpringBoot)                             ← ✅
           ├── 前端通过 nginx:9092 从云取                          ← ✅
           └── 钉钉 _resolve_local_snapshot() → 读本地文件上传     ← ⚠️ 硬依赖本地
```

### 改动后数据流

```
AI 检测到告警
    │
    ▼
_save_snapshot(frame, event_id)
    │
    ├── cv2.imwrite → 本地 static/snapshots/{day}/{event_id}.jpg
    ├── snapshot_pusher.push_async()
    │       │
    │       ├── SCP 成功 → 删除本地文件 ✅ → 检查空目录并清理 ✅
    │       └── SCP 失败 → 保留本地文件（容错）
    │
    └── 返回 "/snapshots/{day}/{event_id}.jpg"
           │
           ├── 存入数据库 (SpringBoot)                             ← ✅
           ├── 前端通过 nginx:9092 从云取                          ← ✅
           └── 钉钉 _resolve_local_snapshot()
                  │
                  ├── 本地文件存在 → 读本地文件上传                 ← ✅ 兼容推送失败
                  └── 本地文件不存在 → 从云 HTTP 下载临时文件上传   ← ✅ 新增回退
```

## 详细设计

### 1. SnapshotPusher 推送后清理本地文件

**文件**：`backend_ai/services/snapshot_push.py`

在 `_push()` 方法中，SCP 推送成功后增加本地文件清理逻辑：

```python
def _push(self, local_path: Path, relative_path: str) -> None:
    try:
        # ... 现有 SSH mkdir + SCP 逻辑不变 ...

        result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            self.logger.warning("SCP push failed for %s: %s", relative_path, result.stderr.strip())
            return

        self.logger.debug("Snapshot pushed: %s → %s:%s", relative_path, self.host, remote_file)

        # 新增：推送成功后清理本地文件
        try:
            local_path.unlink(missing_ok=True)
            parent = local_path.parent
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
            self.logger.debug("Local snapshot cleaned: %s", local_path)
        except OSError as exc:
            self.logger.warning("Failed to clean local snapshot %s: %s", local_path, exc)

    except Exception as exc:
        self.logger.warning("Snapshot push error for %s: %s", relative_path, exc)
```

关键点：

- `local_path.unlink(missing_ok=True)`：文件可能已被其他进程删除，不报错
- 检查父目录是否为空：`not any(parent.iterdir())`，为空则 `parent.rmdir()`
- 清理失败仅 log warning，不影响推送成功的返回
- 清理逻辑在 SCP 成功分支内，推送失败时本地文件保留

### 2. AlertClient 截图路径解析增加云端回退

**文件**：`backend_ai/services/alert_client.py`

#### 2.1 构造函数新增 `nginx_base_url` 参数

```python
class AlertClient:
    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 5.0,
                 session: Any | None = None, internal_token: str | None = None,
                 dingtalk: Any | None = None, snapshot_root: Path | None = None,
                 nginx_base_url: str | None = None):
        # ... 现有属性 ...
        self.nginx_base_url = (nginx_base_url or "").rstrip("/")
```

#### 2.2 `_resolve_local_snapshot` 增加云端回退

```python
def _resolve_local_snapshot(self, snapshot_path: str) -> str:
    if not snapshot_path:
        return snapshot_path

    # 1. 优先检查本地文件
    if self.snapshot_root is not None and snapshot_path.startswith("/snapshots/"):
        local = self.snapshot_root / snapshot_path[len("/snapshots/"):]
        if local.exists():
            return str(local)

    # 2. 本地不存在，回退到云服务器 HTTP URL
    if self.nginx_base_url and snapshot_path.startswith("/"):
        return f"{self.nginx_base_url}{snapshot_path}"

    return snapshot_path
```

解析策略变更：

| 场景                  | 本地文件 | 返回值                           | 钉钉上传方式         |
| --------------------- | -------- | -------------------------------- | -------------------- |
| 推送成功，本地已清理  | 不存在   | `http://host:9092/snapshots/...` | HTTP 下载临时文件    |
| 推送失败，本地保留    | 存在     | 本地绝对路径                     | 直接读本地文件       |
| 未配置 nginx_base_url | 不存在   | 原始路径                         | 无法上传（降级行为） |

#### 2.3 `app.py` 传入 `nginx_base_url`

```python
# 构造 nginx_base_url
nginx_base_url = ""
if remote_host:
    nginx_port = os.environ.get("SNAPSHOT_NGINX_PORT", "9092")
    nginx_base_url = f"http://{remote_host}:{nginx_port}"

alert_client = alert_client or AlertClient(
    base_url=spring_base_url,
    internal_token=internal_token,
    dingtalk=trigger_alert,
    snapshot_root=snapshot_root,
    nginx_base_url=nginx_base_url,
)
```

`nginx_base_url` 从 `snapshot_remote.host` 推导，无需新增配置项。端口默认 9092，可通过环境变量 `SNAPSHOT_NGINX_PORT` 覆盖。

### 3. 钉钉上传支持 HTTP URL

**文件**：`backend_ai/services/dingtalk_service.py`

修改 `_upload_image()` 函数，支持接收本地路径或 HTTP URL：

```python
def _upload_image(file_path_or_url: str) -> str:
    """上传图片到钉钉，返回 media_id。支持本地路径和 HTTP URL。"""
    try:
        token = _get_token()

        if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
            # HTTP URL：下载到临时文件后上传
            import tempfile
            import os
            resp = requests.get(file_path_or_url, timeout=15)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
            try:
                with open(tmp_path, "rb") as f:
                    upload_resp = requests.post(
                        f"https://oapi.dingtalk.com/media/upload?access_token={token}&type=image",
                        files={"media": f},
                        timeout=15,
                    )
                return upload_resp.json().get("media_id", "")
            finally:
                os.unlink(tmp_path)
        else:
            # 本地路径：直接读取上传
            with open(file_path_or_url, "rb") as f:
                resp = requests.post(
                    f"https://oapi.dingtalk.com/media/upload?access_token={token}&type=image",
                    files={"media": f},
                    timeout=15,
                )
            return resp.json().get("media_id", "")
    except Exception:
        logger.exception("上传图片失败")
        return ""
```

关键点：

- 通过 `startswith("http")` 区分本地路径和 HTTP URL
- HTTP 下载使用 `requests.get`，超时 15 秒
- 临时文件使用 `tempfile.NamedTemporaryFile(delete=False)`，上传后 `os.unlink` 清理
- `try/finally` 确保临时文件一定被清理
- 上传失败返回空字符串，与现有行为一致

### 4. 移除 Flask `/snapshots/` 死路由

**文件**：`backend_ai/app.py`

删除以下代码：

```python
@app.get("/snapshots/<path:filename>")
def serve_snapshot(filename: str):
    snapshot_dir = BASE_DIR / "static" / "snapshots"
    return send_from_directory(snapshot_dir, filename)
```

前端取截图走云服务器 Nginx 9092，此路由无消费者。

### 5. 移除 `image_utils.save_snapshot` 死代码

**文件**：`backend_ai/utils/image_utils.py`

删除 `save_snapshot()` 函数（第 111-116 行）。全项目无人调用此函数，`AnalysisService` 使用自己的 `_save_snapshot()` 方法。

## Risks / Trade-offs

| 风险                        | 影响                                                                     | 缓解                                                                                                                                                                       |
| --------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **SCP 推送与清理的竞态**    | 推送成功后、清理前，钉钉可能正在读取同一本地文件                         | 极低概率：推送是异步线程，钉钉上传在推送之后的 `push_alert` 调用中触发，时序上推送完成 → 清理 → 钉钉上传，钉钉上传时本地文件可能已被删。但回退机制会自动走云端下载，无影响 |
| **云服务器 HTTP 下载失败**  | 钉钉上传图片失败，告警通知无截图                                         | 降级行为：钉钉通知仍会发送（文字部分），仅缺少图片。与当前推送失败后本地文件仍在时的行为一致                                                                               |
| **临时文件残留**            | `_upload_image` 中 `os.unlink` 前进程崩溃，临时文件残留                  | `/tmp` 目录通常有 OS 级定期清理；残留文件体积小（一张 jpg），影响可忽略                                                                                                    |
| **空目录清理的边界**        | 同一目录下两个截图同时推送，一个先完成清理了目录，另一个的父目录已不存在 | `local_path.unlink(missing_ok=True)` 不报错；父目录 `rmdir` 仅在目录为空时执行，不会误删含文件的目录                                                                       |
| **`nginx_base_url` 未配置** | 推送成功后本地已清理，钉钉回退时无云端 URL                               | 仅在 `snapshot_remote.host` 为空时发生，此时推送本身也不会执行，本地文件保留，钉钉走本地路径                                                                               |
