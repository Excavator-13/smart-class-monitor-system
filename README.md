# 🎯 智慧教室实时行为分析与安全监测系统

## 1. 项目简介

本项目设计并实现了一套面向智慧教室场景的实时视频分析监测系统。系统基于计算机视觉与深度学习技术，对课堂视频流进行实时分析，实现人脸识别、目标检测与异常行为检测，并对异常事件进行告警与记录。

系统采用前后端分离架构：

- 前端：Vue
- AI视频分析服务：Python + Flask + OpenCV + YOLO
- 用户与告警管理系统：SpringBoot + MySQL
- 视频流传输：RTMP + Nginx

---

## 2. 项目功能

### 2.1 实时视频监控

- 支持RTMP视频流接入
- 前端实时展示监控画面
- 支持多路视频切换

### 2.2 人脸识别功能

- 支持人脸注册
- 实时人脸检测与身份识别
- 陌生人检测与标记

### 2.3 目标检测功能

- 基于YOLO的人员检测
- 支持危险区域入侵检测
- 支持区域停留时间判断

### 2.4 异常行为检测

- 长时间低头检测
- 长时间离开座位检测
- 异常行为实时告警

### 2.5 告警中心

- 告警记录存储
- 告警状态管理（未处理/已处理）
- 告警信息展示与查询

---

## 3. 系统架构

系统整体架构如下：
摄像头/OBS
↓
RTMP推流（Nginx）
↓
Flask AI服务（视频分析）
↓
SpringBoot后端（用户+告警管理）
↓
MySQL数据库
↓
Vue前端展示

---

## 4. 技术栈

### 前端

- Vue3
- Element Plus
- Axios

### 后端（管理系统）

- SpringBoot
- MyBatis
- MySQL
- Swagger

### AI分析服务

- Python 3.8
- Flask
- OpenCV
- dlib
- YOLO（可选）

### 流媒体服务

- Nginx RTMP模块

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

### 5.2 Nginx RTMP 服务器

```bash
# 验证 RTMP 端口
curl http://xxx:9092/stat   # 应返回 XML
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
| `AUTH_JWT_SECRET`            | JWT 签名密钥         | `smart-class-monitor-system-...`        |
| `AI_BASE_URL`                | AI 服务地址          | `http://localhost:5001`                 |
| `AI_INTERNAL_TOKEN`          | 内部接口鉴权 Token   | 需与 AI 端一致                          |
| `NGINX_STAT_URL`             | Nginx RTMP stat 地址 | `http://localhost:9092/stat`            |

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

# 3. 配置环境变量（首次）
cp .env.example .env
# 编辑 .env，填入 Spring Boot 地址和内部 Token

# 4. 启动
python app.py

# 5. 验证
curl http://localhost:5001/model/status
# 应返回 {"code":0,"data":{"loaded":true,...}}
```

**环境变量说明（`.env`）：**

| 变量              | 说明               | 默认值                  |
| ----------------- | ------------------ | ----------------------- |
| `SPRING_BASE_URL` | Spring Boot 地址   | `http://localhost:8080` |
| `INTERNAL_TOKEN`  | 内部接口鉴权 Token | 需与 Spring Boot 端一致 |

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

# 2. 启动开发服务器
npm run dev

# 3. 访问
# http://localhost:5173
```

## 6. 核心功能说明

### 人脸识别流程

1. 摄像头采集图像
2. dlib检测人脸
3. 提取128维特征向量
4. 与数据库比对
5. 输出身份结果

### 异常检测流程

1. 视频流输入
2. YOLO检测目标
3. 行为规则判断（时间+区域）
4. 触发告警
5. 存入数据库

## 7. 项目特色

- 前后端分离架构
- AI实时视频分析
- 支持多种异常行为检测
- 可扩展智慧校园场景
- 工业级分层设计（Controller / Service / AI模块）

## 8. 适用场景

- 智慧教室
- 校园安全监控
- 教学行为分析
- 安防系统原型
