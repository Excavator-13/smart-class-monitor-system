## 1. recording_file 表 + 录像查询

- [x] 1.1 追加 `recording_file` 表 DDL
- [x] 1.2 创建 `RecordingFile` Entity
- [x] 1.3 创建 `RecordingFileMapper`
- [x] 1.4 创建 `RecordingVO`（含 available 字段，相对路径）
- [x] 1.5 创建 `RecordingService`
- [x] 1.6 创建 `RecordingController`（GET /recordings）

## 2. NginxClient + AiClient 扩展

- [x] 2.1 NginxClient 增加 checkHealth()
- [x] 2.2 AiClient 增加 checkHealth()

## 3. SystemController 增强

- [x] 3.1 重写 health()：backend + database + ai + rtmp 四组件

## 4. 编译与验证

- [x] 4.1 运行 `mvn -DskipTests compile`
- [x] 4.2 确认 /recordings file_path 相对路径
- [x] 4.3 确认 /system/health 包含 backend/database/ai/rtmp
- [x] 4.4 确认 /system/health 不因 AI/Nginx 不可用而 500
