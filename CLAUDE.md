# Project Instructions

本项目使用 OpenSpec / SDD 规范驱动开发。Claude Code 在本项目中工作时，应优先遵循下面的流程。

## SDD 工作流

1. 需求不清楚时，先使用 `/opsx:explore` 梳理需求，不要直接写代码。
2. 新功能、接口变更、数据库结构调整或较大重构，必须先使用 `/opsx:propose <change-name>` 生成 proposal、design、spec、tasks。
3. 只有在 spec 和 tasks 明确后，才能使用 `/opsx:apply <change-name>` 实现代码。
4. 功能完成并验证后，使用 `/opsx:archive <change-name>` 归档，并同步正式 spec。
5. 不要绕过 `openspec/changes` 直接做大功能开发。
6. 小修小补可以直接改，但如果影响接口契约、数据库表或模块边界，应补 OpenSpec change。

## 项目技术栈

- 前端：Vue3、Element Plus、Axios
- 后端：SpringBoot、MyBatis、MySQL、Swagger / OpenAPI
- AI 服务：Python Flask、OpenCV、YOLO、dlib
- 流媒体：Nginx RTMP
- 数据库：MySQL

## 模块边界

- SpringBoot 后端负责结构化数据管理、鉴权、人员、人脸档案、视频源、区域规则、告警流转、统计和 Swagger 接口文档。
- Flask AI 服务负责视频帧分析、人脸识别、目标检测、异常检测和处理后视频流输出。
- Nginx RTMP 负责推流、拉流、录像和静态截图/视频文件访问。
- 前端通过 `VITE_API_BASE` 调 SpringBoot，通过 `VITE_AI_BASE` 调 Flask，通过 `VITE_NGINX_BASE` 访问静态资源。

## 后端接口约定

- 当前阶段以前端接口文档为联调基准，SpringBoot 路径暂不强制添加 `/api/v1` 前缀。
- SpringBoot 对前端暴露 `/auth`、`/streams`、`/students`、`/zones`、`/rules`、`/alerts`、`/alert-stats`、`/recordings`、`/system/health`、`/operation-logs` 等接口。
- AI 内部调用 SpringBoot 的接口使用 `/internal/ai/**` 前缀。
- JSON 字段使用 `snake_case`。
- 列表接口统一使用 `page`、`page_size`、`records`、`total`。
- 告警截图和录像路径由 SpringBoot 返回相对路径，前端拼接 `VITE_NGINX_BASE`，后端不要硬编码服务器 IP。

## 开发要求

- 新增或修改接口时，同步更新 Swagger 注解、DTO/VO 示例和 `docs/backend-interface-and-module-notes.md`。
- 修改接口契约前，先检查前端文档和 OpenSpec change，避免前后端路径或字段漂移。
- AI 不建议直接访问 MySQL，应通过 SpringBoot 内部接口同步配置、特征和告警结果。
- 告警写入接口必须支持 `event_uid` 幂等，避免 AI 重试导致重复入库。
- 不要提交无关格式化、无关重构或未验证的大范围改动。