## 1. SnapshotPusher 推送成功后清理本地文件

- [x] 1.1 `services/snapshot_push.py` 修改 `_push()` 方法：SCP 推送成功后（`returncode == 0`）调用 `local_path.unlink(missing_ok=True)` 删除本地文件
- [x] 1.2 `services/snapshot_push.py` 修改 `_push()` 方法：删除文件后检查父目录 `parent.is_dir() and not any(parent.iterdir())`，为空则 `parent.rmdir()`
- [x] 1.3 `services/snapshot_push.py` 修改 `_push()` 方法：清理动作加 debug 日志（`Local snapshot cleaned: {path}`），清理失败加 warning 日志，不影响推送成功的返回

## 2. AlertClient 截图路径解析增加云端回退

- [x] 2.1 `services/alert_client.py` 修改 `__init__()`：新增 `nginx_base_url: str | None = None` 参数，存储为 `self.nginx_base_url`（去除尾部斜杠）
- [x] 2.2 `services/alert_client.py` 修改 `_resolve_local_snapshot()`：本地文件存在时返回本地绝对路径（现有逻辑不变）；本地文件不存在且 `nginx_base_url` 非空时，返回 `{nginx_base_url}{snapshot_path}`；否则返回原始路径
- [x] 2.3 `app.py` 修改 `create_app()`：从 `remote_host` 和 `SNAPSHOT_NGINX_PORT` 环境变量构造 `nginx_base_url`，传入 `AlertClient` 构造函数

## 3. 钉钉上传支持 HTTP URL

- [x] 3.1 `services/dingtalk_service.py` 修改 `_upload_image()`：参数名改为 `file_path_or_url`，通过 `startswith("http://")` 或 `startswith("https://")` 区分本地路径与 HTTP URL
- [x] 3.2 `services/dingtalk_service.py` 修改 `_upload_image()`：HTTP URL 分支使用 `requests.get()` 下载到 `tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)`，上传后 `os.unlink()` 清理临时文件
- [x] 3.3 `services/dingtalk_service.py` 修改 `_upload_image()`：本地路径分支保持现有逻辑不变（`open(file_path, "rb")` 读取上传）

## 4. 移除 Flask /snapshots/ 死路由

- [x] 4.1 `app.py` 删除 `serve_snapshot` 路由（`@app.get("/snapshots/<path:filename>")` 及其函数体）

## 5. 移除 image_utils.save_snapshot 死代码

- [x] 5.1 `utils/image_utils.py` 删除 `save_snapshot()` 函数定义

## 6. 验证

- [x] 6.1 验证 SCP 推送成功后本地文件被删除（代码审查 + py_compile 通过）
- [x] 6.2 验证 SCP 推送失败后本地文件保留（代码审查：`return` 在清理逻辑之前）
- [x] 6.3 验证本地文件删除后空日期目录被清理（代码审查：`parent.rmdir()` 逻辑）
- [x] 6.4 验证本地文件删除后非空日期目录保留（代码审查：`not any(parent.iterdir())` 条件）
- [x] 6.5 验证钉钉上传：本地文件存在时走本地路径（代码审查：`local.exists()` 分支优先）
- [x] 6.6 验证钉钉上传：本地文件不存在时走云端 HTTP URL 下载（代码审查：`nginx_base_url` 回退分支）
- [x] 6.7 验证钉钉上传：HTTP 下载临时文件上传后被清理（代码审查：`finally: os.unlink(tmp_path)`）
- [x] 6.8 验证 `nginx_base_url` 未配置时 `_resolve_local_snapshot()` 返回原始路径（代码审查：条件分支覆盖）
- [x] 6.9 验证 Flask `/snapshots/` 路由已移除（代码审查：路由已删除，`send_from_directory` import 已清理）
