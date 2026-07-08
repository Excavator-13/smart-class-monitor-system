## Context

人员基础管理是纯 CRUD 模块，依赖 `student` 表。本期只做基础信息管理，人脸注册（`/students/{id}/face`）和人脸特征同步（`/students/face-features`）后续独立 change。

## Goals / Non-Goals

**Goals:**
- student 表 + Entity + Mapper
- 5 个 REST 接口（列表/新增/详情/编辑/删除）
- 分页统一 `records/page/page_size/total`
- `student_no` 唯一约束

**Non-Goals:**
- 不实现 `/students/{id}/face`（人脸注册）
- 不实现 `/students/face-features`（AI 特征同步）
- 不实现 `/students/{id}/face-features`（特征元数据查看）

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 分页方式 | 查询全量后内存分页（同 StreamService） | 数据量小，简单可靠 |
| 删除方式 | 软删除 `deleted_at` | 保护历史告警关联 |
| face_registered | 默认 false，由人脸注册模块更新 | 本期无写入逻辑 |
| 搜索 | keyword 匹配 `name` 或 `student_no` | 接口文档 §5.3 |

## Risks / Trade-offs

- **[全量查询]** 学生数量增长后需改为 SQL LIMIT/OFFSET → 初版数据量小时可接受
