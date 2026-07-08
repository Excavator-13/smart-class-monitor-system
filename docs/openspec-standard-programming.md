# OpenSpec 规范化编程指南

本文档用于智慧教室实时行为分析与安全监测系统的规范驱动开发。目标是让每次功能开发都先有清晰说明书，再写代码，最后把正式规范沉淀到 `openspec/specs/`。

## 1. 当前仓库结构

```text
openspec/
├── README.md
├── config.yaml
├── 全流程范例.md
├── specs/
│   └── example-add-api/
│       └── spec.md
└── changes/
    └── archive/
        └── 2026-07-07-example-add-api/
            ├── proposal.md
            ├── design.md
            ├── tasks.md
            └── specs/add-api.md

.claude/
├── commands/opsx/
│   ├── explore.md
│   ├── propose.md
│   ├── apply.md
│   ├── archive.md
│   └── sync.md
└── skills/
    ├── openspec-explore/
    ├── openspec-propose/
    ├── openspec-apply-change/
    ├── openspec-archive-change/
    └── openspec-sync-specs/
```

仓库中已有 Claude Code 的 `/opsx:*` 命令和 skill 说明，但当前本机未检测到 `openspec` CLI。没有 CLI 时，仍然可以按本文档手工创建规范文件并让 AI 按规范实现。

## 2. 目录职责

| 目录 | 用途 | 规则 |
|---|---|---|
| `openspec/changes/<change-id>/` | 开发中的需求草稿 | 每个功能一个目录，名称用 kebab-case |
| `openspec/changes/<change-id>/proposal.md` | 为什么做、做什么、不做什么 | 先写清范围，避免实现跑偏 |
| `openspec/changes/<change-id>/design.md` | 技术方案和影响面 | 说明涉及前端、后端、AI、数据库或 Nginx 哪些模块 |
| `openspec/changes/<change-id>/tasks.md` | 可勾选实现步骤 | AI 每完成一步应把 `- [ ]` 改为 `- [x]` |
| `openspec/changes/<change-id>/specs/<capability>.md` | 本次变更的需求规范 | 使用 Requirement + Scenario，场景用 GIVEN/WHEN/THEN |
| `openspec/specs/<capability>/spec.md` | 正式版规范 | 功能完成并确认后同步到这里 |
| `openspec/changes/archive/YYYY-MM-DD-<change-id>/` | 已完成变更归档 | 保留 proposal/design/tasks/specs 作为过程记录 |

## 3. 标准开发流程

### Step 1: Explore

目的：先想清楚问题，不写代码。

适用场景：

- 需求还模糊。
- 不确定功能放前端、SpringBoot、Flask、Nginx 还是数据库。
- 需要比较多种实现方案。

输出可以是一段结论，也可以进入 Step 2 创建变更。

### Step 2: Propose

为功能创建变更目录：

```text
openspec/changes/<change-id>/
├── proposal.md
├── design.md
├── tasks.md
└── specs/
    └── <capability>.md
```

`change-id` 使用 kebab-case，例如：

- `fix-frontend-blank-screen`
- `add-alert-management-page`
- `connect-ai-video-feed`
- `add-face-registration-flow`

### Step 3: Apply

实现前必须读取：

1. `proposal.md`
2. `design.md`
3. `tasks.md`
4. `specs/*.md`

实现时遵守：

- 只做 `proposal.md` 范围内的内容。
- 每个任务完成后立即勾选 `tasks.md`。
- 如果发现规范和真实代码冲突，先暂停并更新 OpenSpec 文档，再继续编码。
- 前端代码优先放在 `frontend/src/`，接口地址从 `.env` 的 `VITE_API_BASE`、`VITE_AI_BASE`、`VITE_NGINX_BASE` 读取。
- 不要把服务器 IP、端口、文件静态路径硬编码在组件里。

### Step 4: Sync

功能完成后，把变更规范同步到正式规范：

```text
openspec/specs/<capability>/spec.md
```

如果 `openspec/changes/<change-id>/specs/<capability>.md` 使用了 delta 格式，则按以下规则合并：

- `ADDED Requirements`：新增到正式规范。
- `MODIFIED Requirements`：只合并新增或修改的场景，保留旧场景。
- `REMOVED Requirements`：从正式规范移除。
- `RENAMED Requirements`：重命名正式规范中的 Requirement。

### Step 5: Archive

确认代码完成、任务全勾选、正式规范已同步后，把目录移动到：

```text
openspec/changes/archive/YYYY-MM-DD-<change-id>/
```

## 4. 文件模板

### proposal.md

```markdown
# <功能名称>

## 动机
说明为什么需要这个功能。

## 范围
- 做什么
- 做什么
- 做什么

## 不做
- 明确本次不包含的内容

## 影响模块
- frontend
- backend_system
- backend_ai
- database
- nginx
```

### design.md

```markdown
## 技术方案

### 前端
- 页面/组件：
- 接口调用：
- 状态管理：

### 后端
- SpringBoot 接口：
- Flask 接口：
- 数据表：

### 依赖与配置
- `.env` 变量：
- Nginx 静态资源：

### 风险
- 风险 1：
- 风险 2：
```

### specs/<capability>.md

新功能建议使用 delta 格式，方便同步：

```markdown
## ADDED Requirements

### Requirement: <能力名称>
系统必须……
系统不得……

#### Scenario: 正常流程
- GIVEN 已经……
- WHEN 用户……
- THEN 系统……

#### Scenario: 异常流程
- GIVEN ……
- WHEN ……
- THEN ……
```

已有功能修改使用：

```markdown
## MODIFIED Requirements

### Requirement: <已有能力名称>
#### Scenario: 新增场景
- GIVEN ……
- WHEN ……
- THEN ……
```

正式规范 `openspec/specs/<capability>/spec.md` 可以使用更简洁结构：

```markdown
## Requirement: <能力名称>
系统必须……

### Scenario: <场景名称>
- GIVEN ……
- WHEN ……
- THEN ……
```

### tasks.md

```markdown
- [ ] 阅读现有代码并确认影响范围
- [ ] 实现前端页面/组件
- [ ] 封装接口调用
- [ ] 增加 mock 或降级展示
- [ ] 运行构建或测试
- [ ] 同步正式 spec
```

## 5. 智慧教室项目约定

### 前端

- 技术栈：Vue 3、Vite、Element Plus、Axios。
- 入口：`frontend/src/main.js`。
- 主组件：`frontend/src/App.vue`。
- 接口服务层：`frontend/src/services/`。
- 演示数据：`frontend/src/data/mockData.js`。
- 运行命令：

```powershell
cd frontend
npm.cmd run dev:open
```

### 接口地址

必须通过环境变量读取：

```text
VITE_API_BASE=http://localhost:8080
VITE_AI_BASE=http://localhost:5000
VITE_NGINX_BASE=http://localhost:9092
```

### 模块依赖

```text
摄像头/OBS
  -> Nginx RTMP
  -> Flask AI 分析
  -> SpringBoot 业务管理
  -> MySQL
  -> Vue 前端展示
```

前端主动调用：

- Flask：`/video_feed/{stream_id}`、`/analysis/events`、`/analysis/summary/{stream_id}`。
- SpringBoot：`/auth/*`、`/streams`、`/students`、`/rules`、`/zones`、`/alerts`、`/system/health`。
- Nginx：截图和录像静态资源。

## 6. 给 AI 的执行要求

当用户要求“按 OpenSpec 开发”“规范化编程”“走 skill”时：

1. 先检查 `openspec/changes/` 是否已有相关变更。
2. 没有变更时，先创建 `proposal.md`、`design.md`、`tasks.md`、`specs/*.md`。
3. 未读完 OpenSpec 文档前，不直接改业务代码。
4. 编码时逐项完成 `tasks.md`，并同步勾选。
5. 完成后运行可用验证命令，例如前端 `npm.cmd run build`。
6. 总结时说明：变更目录、完成任务、验证结果、是否已同步正式 spec。

## 7. 无 OpenSpec CLI 时的手工命令

创建目录：

```powershell
mkdir openspec\changes\fix-example
mkdir openspec\changes\fix-example\specs
New-Item openspec\changes\fix-example\proposal.md
New-Item openspec\changes\fix-example\design.md
New-Item openspec\changes\fix-example\tasks.md
New-Item openspec\changes\fix-example\specs\fix-example.md
```

归档目录：

```powershell
mkdir openspec\changes\archive
Move-Item openspec\changes\fix-example openspec\changes\archive\2026-07-07-fix-example
```
