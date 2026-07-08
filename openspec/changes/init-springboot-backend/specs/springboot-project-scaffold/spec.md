## ADDED Requirements

### Requirement: Maven Project Structure
The project SHALL be a Maven project at `backend_system/` with SpringBoot 3.x, MyBatis, MySQL Connector, springdoc-openapi 2.x, and Lombok dependencies. The base package SHALL be `com.smartclass.monitor`.

#### Scenario: Project compiles successfully
- **WHEN** developer runs `mvn compile` in `backend_system/`
- **THEN** the project SHALL compile without errors

#### Scenario: Required dependencies are available
- **WHEN** application starts
- **THEN** SpringBoot Web, MyBatis, MySQL, springdoc-openapi, and Jackson SHALL be on classpath

---

### Requirement: Unified API Response
All API responses SHALL use `ApiResponse<T>` with structure `{ "code": 0, "message": "success", "data": {...} }`. Fields SHALL be serialized in snake_case.

#### Scenario: Successful response
- **WHEN** any controller returns `ApiResponse.success(data)`
- **THEN** JSON output SHALL contain `code: 0`, `message: "success"`, and the data under `data`

#### Scenario: Error response
- **WHEN** any controller returns `ApiResponse.error(404, "not found")`
- **THEN** JSON output SHALL contain `code: 404` and `message: "not found"`

---

### Requirement: Unified Pagination
Paginated list responses SHALL use `PageResult<T>` with structure `{ "records": [...], "page": 1, "page_size": 10, "total": 100 }`.

#### Scenario: Paginated response
- **WHEN** a list endpoint returns paginated data
- **THEN** JSON output SHALL include `records`, `page`, `page_size`, and `total` fields

---

### Requirement: Global Exception Handling
The system SHALL provide a `GlobalExceptionHandler` that maps exceptions to unified error responses with appropriate HTTP status codes.

#### Scenario: Parameter validation failure
- **WHEN** a request has missing required fields
- **THEN** the response SHALL have HTTP status 400 and `code: 400`

#### Scenario: Resource not found
- **WHEN** a `BusinessException` with code 404 is thrown
- **THEN** the response SHALL have HTTP status 404 and `code: 404`

#### Scenario: Conflict error
- **WHEN** a duplicate unique key error occurs
- **THEN** the response SHALL have HTTP status 409 and `code: 409`

#### Scenario: Unexpected server error
- **WHEN** an unhandled exception occurs
- **THEN** the response SHALL have HTTP status 500 and `code: 500`, and SHALL NOT expose stack traces

---

### Requirement: Jackson Configuration
Jackson SHALL serialize all JSON fields in snake_case. Timezone SHALL be `Asia/Shanghai`. Date format SHALL be `yyyy-MM-dd HH:mm:ss`.

#### Scenario: camelCase Java field becomes snake_case JSON
- **WHEN** a Java DTO has field `streamId`
- **THEN** the JSON output SHALL use `stream_id`

#### Scenario: Date formatting
- **WHEN** a response contains a `LocalDateTime` field
- **THEN** it SHALL be serialized as `"2026-07-08 10:00:00"` (not ISO 8601 with T separator)

---

### Requirement: CORS Configuration
The system SHALL allow cross-origin requests from frontend development ports (5173, 8081, etc.) and production origins.

#### Scenario: Preflight request from frontend dev server
- **WHEN** browser sends OPTIONS request from `http://localhost:5173`
- **THEN** the response SHALL include appropriate CORS headers and return 200

#### Scenario: Normal request from allowed origin
- **WHEN** browser sends GET request from an allowed origin
- **THEN** the response SHALL include `Access-Control-Allow-Origin` header

---

### Requirement: Swagger / OpenAPI Documentation
The system SHALL expose OpenAPI documentation via `springdoc-openapi`. Swagger UI SHALL be accessible at `/swagger-ui.html`. APIs SHALL be grouped into `frontend-api`, `ai-internal-api`, and `system-api`.

#### Scenario: Swagger UI accessible
- **WHEN** developer navigates to `/swagger-ui.html`
- **THEN** the Swagger UI page SHALL load and display API groups

#### Scenario: OpenAPI JSON available
- **WHEN** developer requests `/v3/api-docs`
- **THEN** a valid OpenAPI 3.0 JSON SHALL be returned

---

### Requirement: Package Structure Skeleton
The project SHALL contain placeholder packages: `config`, `common`, `controller`, `controller.ai`, `service`, `mapper`, `entity`, `dto`, `vo`, `integration`, `security`.

#### Scenario: All base packages exist
- **WHEN** project is imported into IDE
- **THEN** all placeholder packages SHALL be visible in the package explorer
- **THEN** empty packages SHALL contain `.gitkeep` files

---

### Requirement: Health Check Endpoint
The system SHALL provide `GET /system/health` returning backend and database connectivity status. The endpoint SHALL NOT require authentication.

#### Scenario: All components healthy
- **WHEN** `GET /system/health` is called and database is reachable
- **THEN** the response SHALL be `{ "code": 0, "data": { "backend": "up", "database": "up" } }`

#### Scenario: Database unreachable
- **WHEN** `GET /system/health` is called and database connection fails
- **THEN** the response SHALL still return HTTP 200 with `"database": "down"` (NOT HTTP 500)

### Requirement: No Business Modules
This change SHALL NOT implement any business logic for login, student management, video source management, zone configuration, behavior rules, or alert management.

#### Scenario: Only health endpoint exists
- **WHEN** project compiles
- **THEN** the only controller with an endpoint SHALL be `SystemController` with `GET /system/health`
