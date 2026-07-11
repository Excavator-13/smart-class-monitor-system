# 云端静态 / 本地非静态部署分类

本项目按部署位置拆成两类：

## 云服务器端：静态前端

部署目录：

- `frontend/dist`

生成方式：

```powershell
cd C:\Users\adwe2\Desktop\smart-class-monitor-system\frontend
npm.cmd run build
```

部署时把 `frontend/dist` 整个目录放到云服务器 Nginx、静态站点或对象存储中。这里面只包含 HTML、CSS、JS 和运行时配置文件，不需要 Node 服务常驻。

关键文件：

- `frontend/public/runtime-config.js`
- 构建后会复制为 `frontend/dist/runtime-config.js`

默认配置指向本地接口网关：

```js
window.__SMART_CLASS_CONFIG__ = {
  API_BASE: "http://127.0.0.1:18080/api",
  AI_BASE: "http://127.0.0.1:18080/ai",
  NGINX_BASE: "http://127.0.0.1:18080/media"
};
```

云端静态页面需要换接口地址时，优先改 `runtime-config.js`，不需要重新编译 Vue 源码。

## 本地端：非静态接口网关

部署目录：

- `local-runtime`

启动方式：

```powershell
cd C:\Users\adwe2\Desktop\smart-class-monitor-system\local-runtime
node local-gateway.mjs
```

也可以双击：

```text
local-runtime/start-local-gateway.bat
```

默认转发关系：

- `http://127.0.0.1:18080/api/*` -> `http://127.0.0.1:8080/*`
- `http://127.0.0.1:18080/ai/*` -> `http://127.0.0.1:5000/*`
- `http://127.0.0.1:18080/media/*` -> `http://127.0.0.1:9092/*`

如果本地后端端口不同，复制 `local-runtime/.env.example` 为 `local-runtime/.env`，然后修改：

```env
LOCAL_GATEWAY_PORT=18080
API_TARGET=http://127.0.0.1:8080
AI_TARGET=http://127.0.0.1:5000
MEDIA_TARGET=http://127.0.0.1:9092
```

## 分类结果

- 静态页面、样式、前端交互：`frontend/src`，构建后部署到云服务器的 `frontend/dist`。
- 接口转发、服务地址、本地运行逻辑：`local-runtime`，部署并运行在本地。
- 运行时接口配置：`frontend/public/runtime-config.js`，随静态包部署，但可独立修改。
