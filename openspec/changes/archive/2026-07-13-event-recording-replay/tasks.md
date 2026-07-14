## 1. nginx-rtmp 实时切片配置

- [x] 1.1 创建 `nginx/start_segment.sh`：接收 `$name` 参数，创建日期目录，启动 FFmpeg `-c copy -f segment -segment_time 30` 拉流切片，PID 写入 `/tmp/ffmpeg_seg_{name}.pid`
- [x] 1.2 创建 `nginx/stop_segment.sh`：接收 `$name` 参数，读取 PID 文件并 kill 进程，删除 PID 文件
- [x] 1.3 修改 `nginx/nginx.conf`：rtmp application live 新增 `exec_publish bash /opt/scripts/start_segment.sh $name;` 和 `exec_publish_done bash /opt/scripts/stop_segment.sh $name;`
- [x] 1.4 修改 `nginx/nginx.conf`：http 9092 server 新增 `location /records/ { alias /usr/local/rtmp_video/segments/; autoindex off; }`

## 2. 切片自动转码入库

- [x] 2.1 修改 `nginx/flv2mp4.sh`：inotifywait 监听扩展至 `/usr/local/rtmp_video/segments/` 目录
- [x] 2.2 修改 `nginx/flv2mp4.sh`：新增切片文件名解析逻辑（`{stream_id}-{YYYY-MM-DD-HH_MM_SS}.flv` 格式），提取 stream_id + started_at
- [x] 2.3 修改 `nginx/flv2mp4.sh`：切片入库时 `source_type = 'segment'`，`duration_seconds = 30`，`ended_at = started_at + 30s`

## 3. 切片目录清理

- [x] 3.1 修改 `nginx/clean_records.sh`：增加 `find /usr/local/rtmp_video/segments -mtime +7 -name "*.mp4" -delete` 清理过期切片
- [x] 3.2 修改 `nginx/clean_records.sh`：增加空目录清理 `find /usr/local/rtmp_video/segments -type d -empty -delete`

## 4. AI 端录像路径计算

- [x] 4.1 `config/app.yaml` 新增 `recording` 配置节（`segment_seconds: 30`，`segment_dir: /records`）
- [x] 4.2 `config/app.yaml` 同步更新 `.env.example` 新增 `RECORDING_SEGMENT_SECONDS`、`RECORDING_SEGMENT_DIR`
- [x] 4.3 `services/analysis_service.py` 新增 `_resolve_record_segment(stream_id, occurred_at)` 方法：解析时间 → 向下取整到 30s 边界 → 拼接路径 → 计算片内偏移
- [x] 4.4 `services/analysis_service.py` 修改 `analyze_frame()`：事件确认时调用 `_resolve_record_segment()` 获取 `record_path` + `event_time_offset`
- [x] 4.5 `services/alert_client.py` 修改 `push_alert()` 签名：新增 `event_time_offset` 参数（默认 None）
- [x] 4.6 `services/alert_client.py` 修改 `map_event_to_alert()`：将 `event_time_offset` 映射到请求 payload

## 5. 前端录像回放

- [x] 5.1 `services/smartClassApi.js` 修改 `normalizeAlert()`：新增 `event_time_offset` 字段映射
- [x] 5.2 `App.vue` 新增录像回放对话框：`<el-dialog>` + `<video controls>`，绑定 `replayVisible`、`replayUrl`、`replayOffset`
- [x] 5.3 `App.vue` 新增 `onReplayReady()` 方法：`loadedmetadata` 事件触发后 `video.currentTime = replayOffset` + `video.play()`
- [x] 5.4 `App.vue` 新增对话框关闭清理：`video.pause()` + `video.src = ""`
- [x] 5.5 `App.vue` 修改"录像"按钮：从 `<a>` 直接下载改为点击打开回放对话框

## 6. 服务器配置指导文档

- [x] 6.1 创建 `nginx/服务器配置指导.md`：包含部署步骤（脚本部署、nginx reload、目录创建、cron 配置、FFmpeg 僵尸进程检查、验证方法）

## 7. 验证

- [ ] 7.1 验证 `start_segment.sh` 启动后 FFmpeg 进程存在且 PID 文件已写入
- [ ] 7.2 验证推流 30 秒后 segments 目录产出 flv 片段
- [ ] 7.3 验证 `stop_segment.sh` 执行后 FFmpeg 进程已终止且 PID 文件已删除
- [ ] 7.4 验证 flv2mp4.sh 检测到切片 flv 后自动转 mp4 并入库 recording_file（source_type = segment）
- [ ] 7.5 验证 AI 端 `_resolve_record_segment()` 对边界时间计算正确（整点、跨天、0 秒偏移）
- [ ] 7.6 验证 `push_alert()` payload 包含 `record_path` 和 `event_time_offset`
- [ ] 7.7 验证前端点击"录像"按钮弹出播放器并 seek 到正确偏移位置
- [ ] 7.8 验证 nginx `/records/` 路径可访问切片 mp4 文件
- [ ] 7.9 验证 `clean_records.sh` 清理 7 天前的切片文件
