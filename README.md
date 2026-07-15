# 🎯 智慧教室实时行为分析与安全监测系统

## 1. 项目简介

本项目设计并实现了一套面向智慧教室场景的实时视频分析监测系统。系统基于计算机视觉与深度学习技术，对课堂视频流进行实时分析，实现人脸识别、目标检测与异常行为检测，并对异常事件进行告警与记录。

系统采用前后端分离架构：

- 前端：Vue3 + Element Plus
- AI 视频分析服务：Python + Flask + OpenCV + YOLO + InsightFace
- 用户与告警管理系统：SpringBoot + MyBatis + MySQL
- 视频流传输：RTMP + Nginx
- 告警通知：钉钉企业机器人
- AI 日报：通义千问（Qwen）大模型

---

## 2. 项目功能

### 2.1 实时视频监控

- 支持 RTMP 视频流接入
- 前端实时展示监控画面
- 支持多路视频切换
- 录像切片自动存储

### 2.2 人脸识别功能

- 基于 InsightFace 的人脸检测与特征提取
- 支持人脸注册与档案管理
- 实时人脸检测与身份识别
- 陌生人检测与标记
- 防伪检测（眨眼检测 + 纹理分析 + Deepfake 检测）

### 2.3 目标检测功能

- 基于 YOLOv8 的人员检测
- 支持危险区域入侵检测
- 支持区域停留时间判断
- 火灾烟雾检测

### 2.4 异常行为检测

- 长时间低头检测
- 长时间离开座位检测
- 异常行为实时告警
- 告警截图自动推送至服务器

### 2.5 告警中心

- 告警记录存储与状态管理（未处理/已处理）
- 告警信息展示与查询
- 钉钉机器人实时推送告警通知

### 2.6 AI 日报

- 基于通义千问大模型自动生成课堂日报
- 支持截图引用与数据统计

---

## 3. 系统架构

```
摄像头 / OBS
    ↓
RTMP 推流（Nginx）
    ↓
Flask AI 服务（视频分析）
    ↓
SpringBoot 后端（用户 + 告警管理）──→ 钉钉通知 / AI 日报
    ↓
MySQL 数据库
    ↓
Vue 前端展示
```

---

## 4. 技术栈

| 层级             | 技术                                                                    |
| ---------------- | ----------------------------------------------------------------------- |
| 前端             | Vue3、Element Plus、Axios、Vite                                         |
| 后端（管理系统） | SpringBoot、MyBatis、MySQL、Swagger / OpenAPI                           |
| AI 分析服务      | Python 3.10+、Flask、OpenCV、InsightFace、Ultralytics (YOLOv8)、PyTorch |
| 流媒体服务       | Nginx RTMP 模块                                                         |
| 告警通知         | 钉钉企业机器人                                                          |
| AI 日报          | 通义千问（Qwen）                                                        |

---

## 5. 项目运行方式

> 启动顺序：Nginx → MySQL → backend_system → backend_ai → frontend

### 5.1 前置依赖

| 依赖              | 版本  | 说明                |
| ----------------- | ----- | ------------------- |
| Java              | 17+   | backend_system      |
| Maven             | 3.8+  | backend_system 构建 |
| Python            | 3.10+ | backend_ai          |
| Node.js           | 18+   | frontend            |
| MySQL             | 8.0+  | 数据库              |
| Nginx + RTMP 模块 | -     | 视频流              |
| FFmpeg CLI        | 6+    | AI 音频采集         |
| CUDA（可选）      | 12.8+ | GPU 加速推理        |

### 5.2 Nginx RTMP 服务器

```bash
# 验证 RTMP 端口
curl http://<server-ip>:9092/stat   # 应返回 XML
```

### 5.3 MySQL 数据库

```bash
# 创建数据库
mysql -u root -e "CREATE DATABASE IF NOT EXISTS appdb DEFAULT CHARSET utf8mb4;"

# 表结构由 Spring Boot 启动时自动创建（schema.sql + data.sql）
```

### 5.4 backend_system（Spring Boot，端口 8080）

```bash
cd backend_system

# 1. 配置环境变量（首次）
cp .env.example .env
# 编辑 .env，填入数据库连接、JWT 密钥、AI 地址等

# 2. 启动
mvn spring-boot:run

# 3. 验证
curl http://localhost:8080/system/health
# 应返回 {"code":0,"data":{"backend":"up","database":"up",...}}
```

**环境变量说明（`.env`）：**

| 变量                         | 说明                 | 默认值                                  |
| ---------------------------- | -------------------- | --------------------------------------- |
| `SPRING_DATASOURCE_URL`      | MySQL 连接串         | `jdbc:mysql://localhost:3306/appdb?...` |
| `SPRING_DATASOURCE_USERNAME` | 数据库用户           | `root`                                  |
| `SPRING_DATASOURCE_PASSWORD` | 数据库密码           | 空                                      |
| `AUTH_JWT_SECRET`            | JWT 签名密钥         | -                                       |
| `AI_BASE_URL`                | AI 服务地址          | `http://localhost:5001`                 |
| `AI_INTERNAL_TOKEN`          | 内部接口鉴权 Token   | 需与 AI 端一致                          |
| `NGINX_STAT_URL`             | Nginx RTMP stat 地址 | `http://localhost:9092/stat`            |
| `CORS_ALLOWED_ORIGINS`       | CORS 白名单          | `http://localhost:*`                    |
| `QWEN_API_URL`               | 通义千问 API 地址    | -                                       |
| `QWEN_API_KEY`               | 通义千问 API Key     | -                                       |
| `QWEN_MODEL`                 | 通义千问模型名       | `qwen3.7-plus`                          |
| `REPORT_AI_ENABLED`          | 是否启用 AI 日报     | `true`                                  |
| `SNAPSHOT_BASE_URL`          | 截图基础 URL         | -                                       |

### 5.5 backend_ai（Flask，端口 5001）

```bash
cd backend_ai

# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# 2. 安装依赖
#    GPU 服务器（Linux + CUDA）：
pip install -r requirements.txt
#    Mac / CPU 环境：
pip install -r requirements-mac.txt

# 2.1 安装外部 FFmpeg（PyPI 的 ffmpeg 包不包含可执行文件）
#     Windows Conda：
conda install --override-channels -c defaults ffmpeg
#     Ubuntu / Debian：
sudo apt install ffmpeg
#     macOS：
brew install ffmpeg

# 验证 AI 进程可以找到音频采集工具
ffmpeg -version
ffprobe -version

# 3. 配置环境变量（首次）
cp .env.example .env
# 编辑 .env，填入 Spring Boot 地址和内部 Token

# 4. 配置模型（首次）
# 编辑 config/model.yaml，启用/禁用所需模型，调整置信度等参数

# 5. 启动
python app.py

# 6. 验证
curl http://localhost:5001/model/status
# 应返回 {"code":0,"data":{"loaded":true,...}}
```

**环境变量说明（`.env`）：**

| 变量                        | 说明                   | 默认值                  |
| --------------------------- | ---------------------- | ----------------------- |
| `SPRING_BASE_URL`           | Spring Boot 地址       | `http://localhost:8080` |
| `INTERNAL_TOKEN`            | 内部接口鉴权 Token     | 需与 Spring Boot 端一致 |
| `SNAPSHOT_REMOTE_HOST`      | 截图推送服务器地址     | 空（不推送）            |
| `SNAPSHOT_REMOTE_USER`      | 截图推送服务器用户     | `root`                  |
| `SNAPSHOT_REMOTE_PATH`      | 截图推送远程路径       | `/data/snapshots`       |
| `RECORDING_SEGMENT_SECONDS` | 录像切片时长（秒）     | `30`                    |
| `RECORDING_SEGMENT_DIR`     | 录像存储目录           | `/records`              |
| `DINGTALK_APP_KEY`          | 钉钉机器人 AppKey      | 空（不推送）            |
| `DINGTALK_APP_SECRET`       | 钉钉机器人 AppSecret   | 空                      |
| `DINGTALK_WEBHOOK`          | 钉钉机器人 Webhook URL | 空                      |
| `DINGTALK_GROUP_ID`         | 钉钉群组 ID            | 空                      |

**模型配置（`config/model.yaml`）：**

| 模型         | 说明                 | 默认启用 |
| ------------ | -------------------- | -------- |
| `face`       | InsightFace 人脸识别 | ❌       |
| `behavior`   | YOLOv8 行为检测      | ✅       |
| `zone`       | 区域入侵检测         | ✅       |
| `fire`       | 火灾烟雾检测         | ❌       |
| `anti_spoof` | 防伪检测             | ❌       |
| `audio`      | 音频信号检测         | ✅       |

**依赖区别：**

| 文件                   | 适用环境    | 区别                             |
| ---------------------- | ----------- | -------------------------------- |
| `requirements.txt`     | Linux + GPU | `onnxruntime-gpu`、`torch+cu128` |
| `requirements-mac.txt` | macOS / CPU | `onnxruntime`、`torch`（CPU）    |

### 5.6 frontend（Vue，端口 5173）

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 配置运行时地址（首次）
cp public/runtime-config.example.js public/runtime-config.js
# 编辑 runtime-config.js，填入 API_BASE / AI_BASE / NGINX_BASE

# 3. 启动开发服务器
npm run dev

# 4. 访问
# http://localhost:5173
```

**运行时配置（`public/runtime-config.js`）：**

此文件在 `public/` 目录下，**不经过 Vite 构建**，部署后可直接修改无需重新打包。

| 字段         | 说明                                |
| ------------ | ----------------------------------- |
| `API_BASE`   | Spring Boot 后端地址                |
| `AI_BASE`    | AI 服务地址                         |
| `NGINX_BASE` | Nginx RTMP 流媒体地址（含截图服务） |

---

## 6. 生产环境配置

生产环境的完整配置文件及真实值请参考 **[PRODUCTION_CONFIG.md](./PRODUCTION_CONFIG.md)**，包含：

- `backend_ai/config/model.yaml` — 模型配置
- `backend_ai/.env` — AI 服务环境变量
- `backend_system/.env` — 后端管理系统环境变量
- `frontend/public/runtime-config.js` — 前端运行时地址

> ⚠️ **关键**：`backend_ai/.env` 的 `INTERNAL_TOKEN` 必须与 `backend_system/.env` 的 `AI_INTERNAL_TOKEN` 完全一致。

---

## 7. 核心功能说明

### 人脸识别流程

1. 摄像头采集图像
2. InsightFace 检测人脸并提取 512 维特征向量
3. 与数据库比对
4. 输出身份结果
5. 可选防伪检测（眨眼 + 纹理 + Deepfake）

### 异常检测流程

1. 视频流输入
2. YOLOv8 检测目标
3. 行为规则判断（时间 + 区域）
4. 触发告警
5. 存入数据库 + 钉钉推送

### AI 日报流程

1. SpringBoot 汇总当日告警与统计数据
2. 调用通义千问 API 生成自然语言日报
3. 日报存储并展示

---

## 8. 项目特色

- 前后端分离架构
- AI 实时视频分析（支持 GPU 加速）
- 多模型可插拔配置（model.yaml 热切换）
- 钉钉机器人实时告警通知
- 通义千问 AI 日报自动生成
- 前端运行时配置（无需重新构建即可修改服务地址）
- 工业级分层设计（Controller / Service / AI 模块）

---

## 9. 适用场景

- 智慧教室
- 校园安全监控
- 教学行为分析
- 安防系统原型
