# Codex SDD 配置说明

本项目已经在 `openspec/` 中配置 OpenSpec / SDD 工作区，并在 `docs/openspec-standard-programming.md` 中维护完整流程。

## 当前状态

Codex 会话尝试写入 `.codex/skills/openspec-standard-programming/SKILL.md` 时，系统 ACL 对 `.codex` 目录存在显式 Deny，自动写入被拒绝。因此本文件提供手动启用方式。

## 手动启用 Codex Skill

在本机文件管理器或 VS Code 中创建：

```text
.codex/skills/openspec-standard-programming/SKILL.md
```

写入以下内容：

```markdown
---
name: openspec-standard-programming
description: Use this project-specific skill when working in the smart-class-monitor-system repository and the user asks for SDD, OpenSpec, spec-driven development, standardized programming, proposal/design/spec/tasks creation, applying an OpenSpec change, syncing specs, or archiving completed changes.
---

# OpenSpec Standard Programming

## Required Reading

Before changing code, read:

1. `docs/openspec-standard-programming.md`
2. `openspec/config.yaml`
3. Related stable specs under `openspec/specs/`
4. Related active change artifacts under `openspec/changes/`

## Workflow

1. Explore: inspect existing specs, changes, and code before implementation.
2. Propose: create `openspec/changes/<change-id>/proposal.md`, `design.md`, `tasks.md`, and `specs/<capability>.md` when no active change covers the request.
3. Apply: read all change artifacts, implement only the described scope, and check off `tasks.md` after each completed task.
4. Verify: run relevant commands, such as `npm.cmd run build` for the Vue frontend.
5. Sync: merge finished requirements into `openspec/specs/<capability>/spec.md`.
6. Archive: after implementation and spec sync, move completed changes to `openspec/changes/archive/YYYY-MM-DD-<change-id>/`.

## Rules

- Do not edit behavior code until OpenSpec artifacts exist and have been read.
- Use kebab-case for change and capability names.
- Write scenarios with GIVEN/WHEN/THEN.
- Do not hardcode server IPs in frontend components.
- Use `VITE_API_BASE`, `VITE_AI_BASE`, and `VITE_NGINX_BASE`.
- Use `frontend/src/services/smartClassApi.js` for frontend API calls.
```

## 以后如何要求 Codex 按 SDD 开发

你可以直接这样说：

```text
请按 SDD/OpenSpec 流程实现 <功能名>，先创建 change，再按 tasks 编码、验证、同步 spec。
```

Codex 应先检查 `openspec/changes/`，没有对应 change 时先创建规范文件，再进行实现。
