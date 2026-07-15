## Context

`backend_system/` 目录当前为空。需要搭建 SpringBoot 3.x + MyBatis + MySQL 基础工程骨架，严格遵循 `docs/backend-interface-and-module-notes.md` (v2.1) 和 `docs/springboot-backend-detailed-design.md` (V0.3) 中已确定的统一约定。

项目整体为智慧教室系统，但本 change 仅搭建骨架——不实现任何业务模块。

## Goals / Non-Goals

**Goals:**
- 创建可编译运行的 Maven 项目，依赖 SpringBoot 3.x、MyBatis、MySQL、springdoc-openapi 2.x
- 实现统一响应 `ApiResponse<T>`（`code`/`message`/`data`）和分页 `PageResult<T>`（`records`/`page`/`page_size`/`total`）
- 实现全局异常处理：参数校验 400、认证 401、授权 403、资源不存在 404、冲突 409、服务端异常 500
- Jackson 配置 snake_case + Asia/Shanghai + `yyyy-MM-dd HH:mm:ss`
- CORS 配置允许前端开发端口
- Swagger 分组 `frontend-api`、`ai-internal-api`、`system-api`，`/swagger-ui.html` 可访问
- `GET /system/health` 返回后端和数据库连通状态，DB 不可用时仍返回 200

**Non-Goals:**
- 不实现登录/鉴权（JWT 过滤器仅留占位包 `security/`）
- 不创建业务 Controller、Service、Mapper、Entity
- 不写数据库 DDL 或 migration
- 不集成 AI Flask 客户端（`integration/` 仅留占位包）
- 不加 `/api/v1` 版本前缀

## Decisions

| 决策 | 选择 | 理由 | 备选 |
|------|------|------|------|
| 构建工具 | Maven | 中国高校项目标准，团队成员熟悉 | Gradle 学习成本高 |
| SpringBoot 版本 | 3.x + Java 17 | 详细设计文档 §3.1 明确要求 | 2.x 即将 EOL |
| 持久层 | MyBatis（非 Plus） | 接口文档技术栈明确 MyBatis | MyBatis-Plus 功能过剩 |
| 连接池 | HikariCP（SpringBoot 默认） | 性能足够，零配置 | Druid 需额外配置 |
| Swagger | springdoc-openapi 2.x | 详细设计文档 §3.1 明确要求 | SpringFox 已停止维护 |
| 序列化 | Jackson SNAKE_CASE | 接口文档 §4.4，与前端 Axios、Python 风格一致 | 驼峰 |
| 健康检查 | 仅检查 DB `SELECT 1` | 本 change 无 AI/Nginx 客户端，后续扩展 | 全组件探活 |
| 包路径 | `com.smartclass.monitor` | 接口文档 §13 建议包结构 | — |

## Risks / Trade-offs

- **[配置缺失风险]** `application.yml` 中 MySQL 连接信息使用占位符，首次运行时需开发者填入实际值 → 在 `application.yml` 中注释说明
- **[依赖版本冲突]** springdoc-openapi 2.x 需要 SpringBoot 3.x，混用 2.x 会启动失败 → pom.xml 中明确版本约束
- **[空包不被 Git 跟踪]** 空包目录需要 `.gitkeep` 文件 → 在 tasks 中明确每个空包放 `.gitkeep`

## Open Questions

- SpringBoot 具体小版本（如 3.2.x vs 3.3.x）：建议使用当前最新稳定版 3.3.x
- MySQL 版本：接口文档未强制要求，使用 MySQL 8.x 驱动兼容 5.7+
