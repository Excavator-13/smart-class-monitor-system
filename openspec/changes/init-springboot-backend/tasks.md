## 1. Maven 项目骨架

- [x] 1.1 创建 `backend_system/pom.xml`：SpringBoot 3.x parent、Java 17、依赖 spring-boot-starter-web、mybatis-spring-boot-starter、mysql-connector-j、springdoc-openapi-starter-webmvc-ui 2.x、spring-boot-starter-validation、lombok、spring-boot-starter-test
- [x] 1.2 创建 `backend_system/src/main/resources/application.yml`：server.port=8080、MySQL 数据源占位符（注释说明）、Jackson snake_case + Asia/Shanghai + yyyy-MM-dd HH:mm:ss、mybatis 基础配置、springdoc 分组配置（frontend-api / ai-internal-api / system-api）

## 2. 启动类与基础包结构

- [x] 2.1 创建 `SmartClassMonitorApplication.java` 主启动类（`com.smartclass.monitor`）
- [x] 2.2 创建空包骨架（每个放 `.gitkeep`）：`controller`、`controller.ai`、`service`、`mapper`、`entity`、`dto`、`vo`、`integration`、`security`、`common/enums`

## 3. 统一响应与分页

- [x] 3.1 创建 `ApiResponse<T>`：`code`(int)、`message`(String)、`data`(T)；静态工厂方法 `success(T data)`、`error(int code, String message)`
- [x] 3.2 创建 `PageResult<T>`：`records`(List<T>)、`page`(int)、`page_size`(int)、`total`(long)；静态工厂方法 `of(List<T> records, int page, int pageSize, long total)`

## 4. 业务异常与全局异常处理

- [x] 4.1 创建 `BusinessException`：`code`(int)、`message`(String)，构造函数接收 code 和 message
- [x] 4.2 创建 `GlobalExceptionHandler`（`@RestControllerAdvice`）：处理 `MethodArgumentNotValidException` → 400、`BusinessException` → 按 code 返回、`Exception` → 500 不暴露堆栈

## 5. Jackson、CORS、Swagger 配置

- [x] 5.1 创建 `JacksonConfig`：`SNAKE_CASE` 命名策略、`Asia/Shanghai` 时区、`yyyy-MM-dd HH:mm:ss` 日期格式
- [x] 5.2 创建 `CorsConfig`：允许 `localhost:5173`、`localhost:8081`、`127.0.0.1:5173`、生产域名；允许所有 HTTP 方法和常用 Header
- [x] 5.3 创建 `SwaggerConfig`：`@OpenAPIDefinition` 定义 info（标题、版本）；`GroupedOpenApi` 分组 `frontend-api`（匹配 `/auth/**` `/streams/**` `/students/**` `/zones/**` `/rules/**` `/alerts/**` `/alert-stats/**` `/recordings/**`）、`ai-internal-api`（匹配 `/alerts/ai` `/students/face-features`）、`system-api`（匹配 `/system/**` `/operation-logs/**` `/dashboard/**`）

## 6. 健康检查端点

- [x] 6.1 创建 `SystemController`（`@RestController`、`@Tag(name = "system-api")`）：`GET /system/health`，返回 `ApiResponse<Map>` 含 `backend: "up"` + `database: "up"/"down"`。数据库检查用 `DataSource.getConnection()` 或 `SELECT 1`（失败时不抛异常，标记为 down）

## 7. 验证

- [x] 7.1 在 `backend_system/` 下运行 `mvn -DskipTests compile`，确保编译通过
- [x] 7.2 确认只有一个 Controller（`SystemController`），只有一个端点（`/system/health`）
