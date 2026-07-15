# AGENTS.md

本项目使用 OpenSpec / SDD（Spec-Driven Development）规范驱动开发。Codex 在本项目中工作时，应优先遵循本文件。

## SDD 基本原则

1. 需求不明确时，先和用户澄清需求，不要直接实现。
2. 新功能、接口变更、数据库结构调整、跨模块改动或较大重构，必须先创建 OpenSpec change。
3. 开发前应先生成并阅读 proposal、design、spec、tasks。
4. 只有 tasks 明确后，才开始改代码。
5. 功能完成并验证后，将 change 归档，同步到 `openspec/specs/`。
6. 小修小补可以直接实现；但只要影响接口契约、数据库表、AI/前端/后端边界，就应补 OpenSpec change。

## Codex 中的 SDD 操作方式

Codex 不使用 Claude 的 `/opsx:*` slash commands。Codex 应通过 `openspec` CLI 和自然语言执行同等流程。

常用命令：

```powershell
openspec new change "change-name"
openspec status --change "change-name" --json
openspec instructions proposal --change "change-name" --json
openspec instructions design --change "change-name" --json
openspec instructions spec --change "change-name" --json
openspec instructions tasks --change "change-name" --json
openspec instructions apply --change "change-name" --json
openspec validate --change "change-name"
openspec archive "change-name"
```

用户如果说“按 SDD 做某功能”，Codex 应执行：

1. 为功能选择 kebab-case change 名称。
2. 创建 `openspec/changes/<change-name>/`。
3. 按 OpenSpec instructions 生成 proposal、design、spec、tasks。
4. 等用户确认或需求足够明确后，再根据 tasks 实现代码。
5. 实现后运行可用的验证命令。
6. 完成后提示用户是否归档。

## Claude 与 Codex 的区别

- Claude Code 可直接使用 `.claude/commands/opsx/*.md` 中的 `/opsx:explore`、`/opsx:propose`、`/opsx:apply`、`/opsx:archive`。
- Codex 不依赖 `.claude/commands`，而是读取本 `AGENTS.md`，用 `openspec` CLI 执行同样流程。
- 两者共用同一个 `openspec/` 目录，所以生成的 proposal、spec、design、tasks 应保持兼容。

## 项目技术栈

- 前端：Vue3、Element Plus、Axios
- 后端：SpringBoot、MyBatis、MySQL、Swagger / OpenAPI
- AI 服务：Python Flask、OpenCV、YOLO、dlib
- 流媒体：Nginx RTMP
- 数据库：MySQL

## 项目模块边界

- SpringBoot：结构化数据管理、鉴权、人员、人脸档案、视频源、区域规则、告警流转、统计和 Swagger 接口文档。
- Flask AI：视频帧分析、人脸识别、目标检测、异常检测和处理后视频流输出。
- Nginx RTMP：推流、拉流、录像和静态截图/视频文件访问。
- Vue 前端：页面展示、视频播放、接口联调、规则配置和告警处理。

## 接口约定

- 当前阶段以前端接口文档为联调基准，SpringBoot 路径暂不强制添加 `/api/v1` 前缀。
- SpringBoot 对前端暴露 `/auth`、`/streams`、`/students`、`/zones`、`/rules`、`/alerts`、`/alert-stats`、`/recordings`、`/system/health`、`/operation-logs` 等接口。
- AI 内部调用 SpringBoot 的接口使用 `/internal/ai/**` 前缀。
- JSON 字段使用 `snake_case`。
- 列表接口统一使用 `page`、`page_size`、`records`、`total`。
- 告警截图和录像路径由 SpringBoot 返回相对路径，前端拼接 `VITE_NGINX_BASE`，后端不要硬编码服务器 IP。

## 开发要求

- 新增或修改接口时，同步更新 Swagger 注解、DTO/VO 示例和 `docs/backend-interface-and-module-notes.md`。
- 修改接口契约前，先检查前端文档、后端接口文档和 OpenSpec change。
- AI 不建议直接访问 MySQL，应通过 SpringBoot 内部接口同步配置、特征和告警结果。
- 告警写入接口必须支持 `event_uid` 幂等，避免 AI 重试导致重复入库。
- 不要提交无关格式化、无关重构或未验证的大范围改动。