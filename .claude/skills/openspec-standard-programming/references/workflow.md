# Project OpenSpec Workflow Reference

## Repository facts

- Project: 智慧教室实时行为分析与安全监测系统.
- OpenSpec root: `openspec/`.
- Project config: `openspec/config.yaml`.
- Team-facing guide: `docs/openspec-standard-programming.md`.
- Current machine may not have the `openspec` CLI installed; use manual file operations if CLI commands are unavailable.

## Required artifact set

For each behavioral change, create or update:

```text
openspec/changes/<change-id>/
├── proposal.md
├── design.md
├── tasks.md
└── specs/<capability>.md
```

Use kebab-case for `<change-id>` and `<capability>`.

## Artifact rules

- `proposal.md`: motivation, scope, non-goals, affected modules.
- `design.md`: frontend/backend/AI/database/Nginx approach, config, risks.
- `tasks.md`: checklist with `- [ ]`; mark each task `- [x]` immediately after completing it.
- `specs/*.md`: Requirement and Scenario format; scenarios use GIVEN/WHEN/THEN.

Prefer delta sections in active changes:

```markdown
## ADDED Requirements

### Requirement: Capability Name
The system must ...

#### Scenario: Normal flow
- GIVEN ...
- WHEN ...
- THEN ...
```

Use `MODIFIED`, `REMOVED`, and `RENAMED` sections when changing existing capabilities.

## Apply workflow

1. Read `openspec/config.yaml`.
2. Read related active change artifacts, if they exist.
3. If no active change exists for the requested feature, create the artifact set before editing app code.
4. Read all artifacts before editing.
5. Keep implementation scoped to `proposal.md`.
6. Update `tasks.md` after each completed task.
7. If code reveals a design/spec issue, pause and update artifacts before continuing.
8. Run available verification commands.
9. Sync finished specs to `openspec/specs/<capability>/spec.md`.
10. Archive only after implementation and spec sync are complete.

## Smart classroom constraints

- Frontend: Vue 3, Vite, Element Plus, Axios.
- Frontend env vars: `VITE_API_BASE`, `VITE_AI_BASE`, `VITE_NGINX_BASE`.
- Do not hardcode server IPs in components.
- Flask AI endpoints include `/video_feed/{stream_id}`, `/analysis/events`, `/analysis/summary/{stream_id}`, `/model/status`.
- SpringBoot endpoints include `/streams`, `/students`, `/rules`, `/zones`, `/alerts`, `/alert-stats`, `/system/health`.
- Nginx 9092 serves screenshots and recordings returned by SpringBoot paths.
