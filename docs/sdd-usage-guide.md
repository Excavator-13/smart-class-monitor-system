# Claude / Codex 使用 SDD 指南

## 当前配置状态

本项目已经配置了 OpenSpec / SDD：

- `openspec/`：统一的 SDD 规范目录
- `.claude/commands/opsx/`：Claude Code slash commands
- `.claude/skills/openspec-*`：Claude Code OpenSpec skills
- `CLAUDE.md`：Claude Code 项目说明
- `AGENTS.md`：Codex 项目说明
- `openspec/config.yaml`：OpenSpec 项目上下文

## 在 Claude Code 中使用

必须从项目根目录启动 Claude Code：

```powershell
cd "D:\team-homework\smart-class-monitor-system"
claude
```

常用流程：

```text
/opsx:explore
/opsx:propose add-alert-management
/opsx:apply add-alert-management
/opsx:archive add-alert-management
```

推荐用法：

```text
/opsx:explore
我想做 SpringBoot 告警管理接口，包括告警列表、详情、状态标记和首页统计。
```

然后生成规范：

```text
/opsx:propose add-alert-management
```

确认 `openspec/changes/add-alert-management/` 下的文档没问题后再实现：

```text
/opsx:apply add-alert-management
```

功能完成后归档：

```text
/opsx:archive add-alert-management
```

## 在 Codex 中使用

Codex 不直接使用 Claude 的 `/opsx:*` slash commands。Codex 会读取项目根目录的 `AGENTS.md`，然后通过 `openspec` CLI 完成同样的 SDD 流程。

你可以直接对 Codex 说：

```text
按 SDD 流程做 add-alert-management，先生成 OpenSpec 文档，不要直接写代码。
```

或者：

```text
按 openspec/changes/add-alert-management/tasks.md 实现这个 change。
```

Codex 会使用的底层命令大致是：

```powershell
openspec new change "add-alert-management"
openspec status --change "add-alert-management" --json
openspec instructions proposal --change "add-alert-management" --json
openspec instructions design --change "add-alert-management" --json
openspec instructions spec --change "add-alert-management" --json
openspec instructions tasks --change "add-alert-management" --json
openspec instructions apply --change "add-alert-management" --json
openspec validate --change "add-alert-management"
openspec archive "add-alert-management"
```

## 什么时候必须走 SDD

建议必须走 SDD 的情况：

- 新增 SpringBoot 模块或接口
- 修改前后端接口路径、字段、返回结构
- 修改数据库表结构
- 新增 AI 与 SpringBoot 内部接口
- 改变告警流程、人脸注册流程、视频源流程
- 跨 `frontend`、`backend_system`、`backend_ai` 多模块改动

可以不走 SDD 的情况：

- 修 typo
- 改 README 小段说明
- 小范围样式调整
- 不影响接口和数据结构的局部 bugfix

## 推荐 change 命名

使用 kebab-case：

- `add-alert-management`
- `add-student-face-register`
- `add-stream-management`
- `add-ai-internal-alert-events`
- `update-backend-api-contract`

## 注意

Claude 和 Codex 共用同一个 `openspec/` 目录。一个工具生成的 change，另一个工具也能继续实现或归档。