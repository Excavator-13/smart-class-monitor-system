## Context

人员基础 CRUD 已就绪（`add-student-management`）。人脸注册依赖 Flask AI 服务的 `/face/feature/extract` 接口。`AiClient` 与 `NginxClient` 同属 `integration/` 包，遵循相同的封装模式。

## Goals / Non-Goals

**Goals:**
- `face_feature` 表 + Entity + Mapper
- `AiClient` 封装 `/face/feature/extract`、`/face/features/reload`
- `POST /students/{id}/face` 完整注册流程
- `GET /students/{id}/face-features` 前端用（无向量）
- `GET /students/face-features` AI 内部用（有向量）
- `feature_dim` 动态保存

**Non-Goals:**
- 不实现 AI 接口鉴权（本期直连）
- 不实现人脸特征删除 `/students/{id}/face-features/{feature_id}` DELETE
- 不实现活体检测

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| AiClient 实现 | `RestTemplate` + `SimpleClientHttpRequestFactory` | 与 NginxClient 一致 |
| AI 超时 | 连接 3s，读取 10s | 特征提取可能较慢 |
| reload 失败处理 | 记日志，不阻断注册 | 详细设计 §7.4 要求 |
| 特征向量存储 | MySQL JSON 类型 | 接口文档 §8 建议 |
| face_count 校验 | 必须 == 1 | AI 文档错误码 40002/40003 |
| AI 内部接口位置 | `controller.ai.AiFaceFeatureController` | 详细设计 §3.3 包结构 |

## 人脸注册流程

```
POST /students/{id}/face { image: "base64..." }
  → 校验 student 存在且 status=enabled
  → 校验 image 不为空
  → AiClient.extractFeature(image, studentId)
  → 校验 face_count == 1（否则返回对应错误）
  → 写入 face_feature: feature_dim, feature_vector, quality_score, bbox_json ...
  → 更新 student.face_registered = true
  → AiClient.reloadFeatures()（失败记日志不阻断）
  → 返回 { face_count, feature_dim, quality_score, bbox }
```

## Risks / Trade-offs

- **[AI 不可用]** 特征提取超时或 AI 宕机 → 返回业务错误，不写数据库
- **[大图片]** base64 图片可能很大 → 建议前端压缩后再上传，后端可加大小限制
- **[并发注册]** 同一学生多次注册 → 每次新增一条 face_feature 记录（一对多），version 递增
