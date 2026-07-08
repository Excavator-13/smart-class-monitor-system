## Why

人员基础管理已完成，需要实现人脸注册功能。人脸注册是 AI 识别的数据基础——前端上传照片 → SpringBoot 调 AI 提取特征 → 入库 → 通知 AI 刷新缓存。

## What Changes

- 新增 `face_feature` 数据库表 DDL
- 新增 `POST /students/{id}/face`：接收 base64 图片 → 调 AI `/face/feature/extract` → 写入 `face_feature` → 更新 `student.face_registered` → 通知 AI 刷新
- 新增 `GET /students/{id}/face-features`：返回特征元数据（图片路径、质量评分、创建时间），**不返回 `feature_vector`**
- 新增 `GET /students/face-features`：**AI 内部接口**（`controller.ai`），返回完整 `feature_vector`，**禁止前端访问**
- 新增 `AiClient`：封装调用 Flask AI 服务的 HTTP 客户端
- 新增 AI 配置：`application.yml` 中 `ai.base-url`
- `feature_dim` 保存实际值，不硬编码 128 或 512

## Capabilities

### New Capabilities
- `face-register`: 人脸注册流程（前端→SpringBoot→AI→入库→刷新）
- `face-features-api`: 人脸特征数据查询（前端元数据 + AI 内部全量）
- `ai-client`: 封装对 Flask AI 服务的 HTTP 调用

### Modified Capabilities
<!-- 无 -->

## Impact

- 新增数据库表：`face_feature`
- 新增依赖：AiClient（Spring `RestTemplate`，无额外 Maven 依赖）
- 新增包：`controller.ai`
- 新增配置：`ai.base-url`、连接/读取超时
