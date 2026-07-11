## Requirement: Spring Boot 敏感配置外部化

`application.yml` 中的数据库 URL、账号、密码、JWT 密钥、AI 内部 Token 必须支持通过环境变量覆盖，不得将生产凭据硬编码在代码仓库中。
未设置环境变量时，应使用合理的本地开发默认值。

### Scenario: 数据库连接通过环境变量覆盖

- GIVEN 生产环境设置环境变量 `SPRING_DATASOURCE_URL`、`SPRING_DATASOURCE_USERNAME`、`SPRING_DATASOURCE_PASSWORD`
- WHEN Spring Boot 应用启动
- THEN 数据源使用环境变量中的值连接数据库

### Scenario: 数据库连接使用默认值

- GIVEN 本地开发环境未设置上述环境变量
- WHEN Spring Boot 应用启动
- THEN 数据源使用 `application.yml` 中的默认值（localhost）

### Scenario: JWT 密钥通过环境变量覆盖

- GIVEN 生产环境设置环境变量 `AUTH_JWT_SECRET`
- WHEN 应用签发或验证 JWT
- THEN 使用环境变量中的密钥

### Scenario: AI 内部 Token 通过环境变量覆盖

- GIVEN 生产环境设置环境变量 `AI_INTERNAL_TOKEN`
- WHEN 后端调用 AI 服务内部接口
- THEN 请求携带环境变量中的 Token

## Requirement: Spring Boot 服务地址配置化

`ai.base-url` 和 `nginx.stat-url` 必须支持通过环境变量覆盖，以便不同环境指向不同服务实例。

### Scenario: AI 服务地址通过环境变量覆盖

- GIVEN 设置环境变量 `AI_BASE_URL=http://10.0.0.5:5000`
- WHEN 后端调用 AI 服务
- THEN 请求发送到 `http://10.0.0.5:5000`

### Scenario: Nginx stat 地址通过环境变量覆盖

- GIVEN 设置环境变量 `NGINX_STAT_URL=http://10.0.0.5:9092/stat`
- WHEN 后端查询流状态
- THEN 请求发送到 `http://10.0.0.5:9092/stat`

## Requirement: StreamService MJPEG URL 消除硬编码

`StreamService.getPreviewUrl()` 中不得硬编码 IP 地址拼接 MJPEG URL，必须从 `ai.base-url` 配置读取。

### Scenario: MJPEG URL 从配置生成

- GIVEN `ai.base-url` 配置为 `http://10.0.0.5:5000`
- WHEN 调用 `getPreviewUrl("classroom_01")`
- THEN 返回的 `mjpegUrl` 为 `http://10.0.0.5:5000/video_feed/classroom_01`

### Scenario: 配置变更后 URL 随之变更

- GIVEN `ai.base-url` 从 `http://39.106.209.208:5000` 改为 `http://10.0.0.5:5000`
- WHEN 调用 `getPreviewUrl`
- THEN 返回的 `mjpegUrl` 使用新地址，不再包含旧 IP

## Requirement: CORS 允许域名配置化

`CorsConfig` 中不得硬编码生产服务器 IP，允许的域名列表必须从配置读取。

### Scenario: CORS 域名从配置读取

- GIVEN 配置 `cors.allowed-origins` 为 `["http://localhost:*","http://10.0.0.5:*"]`
- WHEN CorsFilter 初始化
- THEN 允许的 Origin Pattern 为配置中的列表

### Scenario: 未配置时使用默认值

- GIVEN 未设置 `cors.allowed-origins` 配置
- WHEN CorsFilter 初始化
- THEN 允许的 Origin Pattern 为 `["http://localhost:*","http://127.0.0.1:*"]`

## Requirement: Flask AI 服务地址支持环境变量覆盖

`backend_ai/config/app.yaml` 中的 `spring.base_url` 必须支持通过环境变量 `SPRING_BASE_URL` 覆盖。

### Scenario: AI 服务调用后端地址通过环境变量覆盖

- GIVEN 设置环境变量 `SPRING_BASE_URL=http://10.0.0.5:8080`
- WHEN AI 服务启动并初始化 ConfigClient
- THEN ConfigClient 的 base_url 为 `http://10.0.0.5:8080`

### Scenario: 未设置环境变量时使用 yaml 默认值

- GIVEN 未设置 `SPRING_BASE_URL`
- WHEN AI 服务启动
- THEN ConfigClient 使用 `app.yaml` 中的 `http://localhost:8080`

## Requirement: Mock SpringBoot 启动参数外部化

`mock_springboot/app.py` 中硬编码的 `host`、`port`、`debug` 必须支持通过环境变量覆盖。

### Scenario: 通过环境变量指定端口

- GIVEN 设置环境变量 `MOCK_PORT=9090`
- WHEN 运行 `python app.py`
- THEN 服务监听端口 9090

### Scenario: 未设置环境变量时使用默认值

- GIVEN 未设置 `MOCK_PORT`
- WHEN 运行 `python app.py`
- THEN 服务监听默认端口 8080

## Requirement: 前端环境配置分离

前端 `.env` 文件不得包含生产 IP，必须拆分为 `.env`（本地开发）和 `.env.production`（生产构建），生产地址通过环境变量注入。

### Scenario: 本地开发使用 .env

- GIVEN 开发者运行 `npm run dev`
- WHEN Vite 加载环境变量
- THEN `VITE_API_BASE` 为 `http://127.0.0.1:8080`，`VITE_NGINX_BASE` 为本地地址

### Scenario: 生产构建使用 .env.production

- GIVEN 存在 `.env.production` 文件，其中 `VITE_NGINX_BASE` 通过构建时环境变量注入
- WHEN 运行 `npm run build`
- THEN 构建产物中的 API 地址为生产值，不包含硬编码 IP

## Requirement: runtime-config.js 默认值可配置

`frontend/public/runtime-config.js` 中的默认地址不得硬编码生产 IP，默认值应指向本地开发网关。

### Scenario: runtime-config.js 使用本地默认值

- GIVEN 未通过部署脚本覆盖 `runtime-config.js`
- WHEN 前端加载运行时配置
- THEN `API_BASE` 默认为 `http://127.0.0.1:18080/api`

### Scenario: 部署时替换为生产地址

- GIVEN 部署脚本将 `runtime-config.js` 中的地址替换为生产值
- WHEN 前端加载运行时配置
- THEN 使用生产环境地址

## Requirement: local-runtime 网关地址统一从 .env 读取

`local-gateway.mjs` 中的 fallback 硬编码地址必须移除，所有目标地址统一从 `.env` 文件读取。

### Scenario: 所有地址从 .env 读取

- GIVEN `.env` 文件设置 `API_TARGET=http://127.0.0.1:8080`
- WHEN 启动本地网关
- THEN `/api` 前缀转发到 `.env` 中指定的地址

### Scenario: .env 缺失时给出明确提示

- GIVEN 未提供 `.env` 文件且未设置环境变量
- WHEN 启动本地网关
- THEN 控制台输出警告信息，提示用户配置目标地址
