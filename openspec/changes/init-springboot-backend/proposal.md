## Why

`backend_system/` 目录当前为空（仅有 `.gitkeep`），需要搭建 SpringBoot 基础工程骨架，为后续业务模块开发提供统一的配置、异常处理、分页结构和接口文档基础设施。

## What Changes

- 创建 Maven 项目骨架（pom.xml），引入 SpringBoot 3.x、MyBatis、MySQL、springdoc-openapi、Jackson、Validation 等依赖
- 建立 `com.smartclass.monitor` 基础包结构：config、common、controller、service、mapper、entity、dto、vo、integration、security
- 实现 `common` 包：`ApiResponse<T>`（统一响应 `code/message/data`）、`PageResult<T>`（分页 `records/page/page_size/total`）、`BusinessException`（业务异常）、`GlobalExceptionHandler`（全局异常处理，映射 400/401/403/404/409/500）
- 配置 Jackson：JSON 字段 snake_case，时区 Asia/Shanghai，日期格式 `yyyy-MM-dd HH:mm:ss`
- 配置 CORS：允许前端开发端口跨域请求
- 配置 Swagger/springdoc-openapi：`/swagger-ui.html` 可访问，分组 `frontend-api`、`ai-internal-api`、`system-api`
- 提供 `GET /system/health` 最小可用接口：返回后端和数据库状态（不因数据库不可用而抛 500）
- **不实现**任何业务模块（登录、学生、视频源、区域、规则、告警等）

## Capabilities

### New Capabilities
- `springboot-project-scaffold`: SpringBoot 基础工程骨架，包含依赖管理、包结构、统一响应、分页、异常处理、Jackson/CORS/Swagger 配置、健康检查端点

### Modified Capabilities
<!-- 无现有 capability 需要修改 -->

## Impact

- 新增目录：`backend_system/` 下完整 Maven 项目结构
- 新增依赖：SpringBoot 3.x、MyBatis、MySQL Connector、springdoc-openapi 2.x、Lombok
- 无数据库表变更（仅使用 `SELECT 1` 检测连通性）
- 无前端/AI/Nginx 影响
