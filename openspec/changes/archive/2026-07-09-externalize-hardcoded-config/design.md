## 技术方案

- 框架：Spring Boot 原生外部化配置 + Flask 环境变量 + Vite .env 多环境
- Spring Boot 敏感配置：`application.yml` 保留本地开发默认值（localhost），生产值通过环境变量覆盖；Spring Boot 的 `Relaxed Binding` 自动映射 `SPRING_DATASOURCE_URL` → `spring.datasource.url`、`AUTH_JWT_SECRET` → `auth.jwt.secret`、`AI_INTERNAL_TOKEN` → `ai.internal-token`、`AI_BASE_URL` → `ai.base-url`、`NGINX_STAT_URL` → `nginx.stat-url`
- StreamService MJPEG URL：注入 `@Value("${ai.base-url}")` 替代硬编码 IP 拼接
- CORS 域名：新增配置项 `cors.allowed-origins`，`CorsConfig` 通过 `@Value` 读取，默认值为 `localhost:*` 和 `127.0.0.1:*`
- Flask AI 服务：`app.py` 的 `create_app` 中优先读取 `os.environ.get("SPRING_BASE_URL")`，未设置则 fallback 到 `app.yaml`
- Mock SpringBoot：`app.py` 优先读取 `os.environ.get("MOCK_HOST")`、`os.environ.get("MOCK_PORT")`、`os.environ.get("MOCK_DEBUG")`，未设置则使用现有默认值
- 前端环境分离：拆分 `.env`（本地开发，`127.0.0.1` 地址）和 `.env.production`（生产地址通过 `VITE_*` 环境变量注入，不硬编码 IP）
- runtime-config.js：默认值改为本地开发网关地址（`127.0.0.1:18080`），部署时由 CI/CD 脚本替换
- local-runtime 网关：移除 `local-gateway.mjs` 中的 fallback 硬编码地址，必须从 `.env` 读取；缺失时 `console.warn` 提示并拒绝启动
- 不引入配置中心，不改变现有 API 接口和业务逻辑
