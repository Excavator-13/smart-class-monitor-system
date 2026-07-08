## Why

视频源和鉴权已就绪，需要实现人员基础管理模块。人员库是后续人脸注册的前置依赖（先建人员再注册人脸），也是告警关联学生身份的基础。

## What Changes

- 新增 `student` 数据库表 DDL
- `GET /students`：分页查询，支持 `class_name`、`keyword`、`face_registered` 筛选
- `POST /students`：新增人员（`student_no`、`name`、`class_name`），`student_no` 唯一
- `GET /students/{id}`：人员详情
- `PUT /students/{id}`：编辑人员
- `DELETE /students/{id}`：软删除
- 分页统一 `records/page/page_size/total`
- **不实现**人脸注册 `/students/{id}/face`
- **不实现**人脸特征 `/students/face-features`

## Capabilities

### New Capabilities
- `student-crud`: 人员基础信息增删改查（GET/POST/PUT/DELETE /students）

### Modified Capabilities
<!-- 无 -->

## Impact

- 新增数据库表：`student`
- 新增文件：Entity、Mapper、DTO、VO、Service、Controller
- 无外部依赖变更
