## Spring Boot 敏感配置外部化

- [x] `application.yml` 中数据库 URL/账号/密码保留本地默认值（localhost），确认 Spring Boot Relaxed Binding 自动映射环境变量覆盖
- [x] `application.yml` 中 JWT secret 确认可通过 `AUTH_JWT_SECRET` 环境变量覆盖
- [x] `application.yml` 中 AI internal-token 确认可通过 `AI_INTERNAL_TOKEN` 环境变量覆盖

## Spring Boot 服务地址配置化

- [x] `application.yml` 中 `ai.base-url` 确认可通过 `AI_BASE_URL` 环境变量覆盖
- [x] `application.yml` 中 `nginx.stat-url` 确认可通过 `NGINX_STAT_URL` 环境变量覆盖

## StreamService MJPEG URL 消除硬编码

- [x] `StreamService.java` 注入 `@Value("${ai.base-url}")` 替代硬编码的 `"http://39.106.209.208:5000"`
- [x] 验证 `getPreviewUrl()` 返回的 mjpegUrl 从配置生成

## CORS 允许域名配置化

- [x] `CorsConfig.java` 新增 `cors.allowed-origins` 配置项，通过 `@Value` 读取允许的域名列表
- [x] 移除 `CorsConfig.java` 中硬编码的 `"http://39.106.209.208:*"`
- [x] 默认值为 `["http://localhost:*", "http://127.0.0.1:*"]`

## Flask AI 服务地址环境变量覆盖

- [x] `backend_ai/app.py` 的 `create_app` 优先读取 `os.environ.get("SPRING_BASE_URL")`
- [x] 未设置环境变量时 fallback 到 `app.yaml` 中的 `spring.base_url`

## Mock SpringBoot 启动参数外部化

- [x] `mock_springboot/app.py` 优先读取 `MOCK_HOST` / `MOCK_PORT` / `MOCK_DEBUG` 环境变量
- [x] 未设置时使用现有默认值（`0.0.0.0:8080:True`）

## 前端环境配置分离

- [x] 创建 `.env.production` 文件，生产地址通过构建时环境变量注入（不硬编码 IP）
- [x] `.env` 保持本地开发值（`127.0.0.1`），移除其中含生产 IP 的项

## runtime-config.js 默认值可配置

- [x] `frontend/public/runtime-config.js` 默认值改为本地开发网关地址（`127.0.0.1:18080`）
- [x] 确认部署脚本可替换为生产地址

## local-runtime 网关地址统一 .env

- [x] 移除 `local-gateway.mjs` 中的 fallback 硬编码地址（`http://127.0.0.1:8080` 等）
- [x] 所有目标地址必须从 `.env` 或环境变量读取
- [x] 缺失时 `console.warn` 提示并拒绝启动

## 额外清理：Swagger @Schema example 值

- [x] 清理 5 个 VO/DTO 文件中 `@Schema(example=...)` 的硬编码生产 IP，改为 `localhost`

## 验证

- [ ] 本地开发环境不设置任何新环境变量，应用正常启动且使用默认值
- [ ] 模拟生产环境设置全部相关环境变量，验证各模块读取正确值
