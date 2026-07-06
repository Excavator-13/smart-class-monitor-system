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

### 5.1 启动Nginx推流服务器

```bash
service nginx start
```

### 5.2 启动AI服务（Flask）

```bash
cd backend-ai
python app.py
```

### 5.3 启动SpringBoot后端

```bash
cd backend-system
mvn spring-boot:run
```

### 5.4 启动前端

```bash
cd frontend
npm install
npm run serve
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
