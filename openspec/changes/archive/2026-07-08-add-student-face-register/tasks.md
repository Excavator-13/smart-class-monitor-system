## 1. 数据库

- [x] 1.1 追加 `face_feature` 表 DDL

## 2. AI 配置与 AiClient

- [x] 2.1 在 `application.yml` 增加 `ai.base-url`
- [x] 2.2 创建 `AiClient`

## 3. Entity、Mapper

- [x] 3.1 创建 `FaceFeature` Entity
- [x] 3.2 创建 `FaceFeatureMapper`

## 4. DTO、VO

- [x] 4.1 创建 `FaceRegisterRequest` DTO
- [x] 4.2 创建 `FaceRegisterResponse` VO
- [x] 4.3 创建 `FaceFeatureVO` VO（无 feature_vector）
- [x] 4.4 创建 `FaceFeatureFullVO` VO（有 feature_vector，AI 内部）

## 5. Service

- [x] 5.1 创建 `FaceService.registerFace()`
- [x] 5.2 `FaceService.getFaceFeatures()` / `getAllFaceFeatures()`

## 6. Controller

- [x] 6.1 创建 `FaceController`（frontend-api）
- [x] 6.2 创建 `AiFaceFeatureController`（controller.ai, ai-internal-api）

## 7. 学生表 + Mapper 补充

- [x] 7.1 `StudentMapper` 增加 `updateFaceRegistered`
- [x] 7.2 在 `FaceService` 中调用

## 8. 编译与验证

- [x] 8.1 运行 `mvn -DskipTests compile`
- [x] 8.2 确认 `FaceFeatureVO` 不含 `feature_vector`
- [x] 8.3 确认 `GET /students/face-features` 在 `controller.ai` 包中
