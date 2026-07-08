# OpenSpec / SDD 工作区

本目录用于智慧教室实时行为分析与安全监测系统的规范驱动开发（SDD）。

## 目录职责

```text
openspec/
├── config.yaml
├── specs/
│   └── <capability>/spec.md
└── changes/
    ├── <change-id>/
    │   ├── proposal.md
    │   ├── design.md
    │   ├── tasks.md
    │   └── specs/<capability>.md
    └── archive/
        └── YYYY-MM-DD-<change-id>/
```

## 开发原则

1. 行为变更先写 OpenSpec，再改代码。
2. 每个变更使用一个 `openspec/changes/<change-id>/` 目录。
3. `change-id` 和 `capability` 使用 kebab-case。
4. 实现前必须读取 `proposal.md`、`design.md`、`tasks.md` 和 `specs/*.md`。
5. 每完成一个实现步骤，立即勾选 `tasks.md`。
6. 功能完成后同步正式规范到 `openspec/specs/<capability>/spec.md`。
7. 确认完成后再归档到 `openspec/changes/archive/YYYY-MM-DD-<change-id>/`。

## 当前正式规范

- `openspec/specs/frontend/spec.md`：前端监控界面、接口服务层、运行时兜底、主题切换、盆栽交互、部署拆分。

## 项目补充说明

更详细的流程、模板和示例见：

- `docs/openspec-standard-programming.md`
- `docs/codex-sdd-setup.md`
