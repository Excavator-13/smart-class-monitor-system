# 配置外部化：消除硬编码

## 动机

当前多个模块的 IP 地址、数据库账号密码、JWT 密钥、服务间调用地址等敏感或环境相关的值直接硬编码在源码和配置文件中，导致：

- 换环境部署必须改源码，极易遗漏出错
- 密码、密钥等敏感信息暴露在代码仓库中，存在安全隐患
- 同一配置在多处重复硬编码（如 `39.106.209.208` 出现在 10+ 处），维护困难

## 范围

- **backend_system（Spring Boot）**
  - `application.yml` 中的 MySQL URL/账号/密码 → 环境变量或 Spring profile 外部配置
  - `application.yml` 中的 JWT secret → 环境变量
  - `application.yml` 中的 AI internal-token → 环境变量
  - `application.yml` 中的 `ai.base-url`、`nginx.stat-url` → 可通过环境变量覆盖
  - `StreamService.java` 中硬编码的 MJPEG URL 拼接 → 读取 `ai.base-url` 配置
  - `CorsConfig.java` 中硬编码的 `39.106.209.208:*` → 从配置读取允许的域名列表
- **backend_ai（Flask）**
  - `config/app.yaml` 中的 `spring.base_url` → 支持环境变量覆盖
- **mock_springboot**
  - `app.py` 中硬编码的 host/port/debug → 支持环境变量或命令行参数
- **frontend**
  - `.env` 中 `VITE_NGINX_BASE` 含生产 IP → `.env.production` 分离
  - `public/runtime-config.js` 硬编码地址 → 保持运行时注入机制，但默认值改为可配置
- **local-runtime**
  - `local-gateway.mjs` fallback 地址 → 统一从 `.env` 读取，减少硬编码默认值

## 不涉及

- 不改变现有业务逻辑和 API 接口
- 不引入新的配置中心（如 Nacos、Apollo），仅使用各框架原生的外部化机制
- 不重构前端构建配置体系（Vite 环境变量机制已存在，仅做 `.env` 文件拆分）
