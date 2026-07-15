---
name: openspec-standard-programming
description: Use this project-specific skill when working in the smart-class-monitor-system repository and the user asks for OpenSpec, spec-driven development, standardized programming, proposal/design/spec/tasks creation, applying an OpenSpec change, syncing specs, or archiving completed changes.
---

# OpenSpec Standard Programming

## Overview

Use OpenSpec as the contract before changing behavior. Create or update proposal, design, specs, and tasks before implementation; then code only what the artifacts describe.

## Required Reading

Read `references/workflow.md` before changing code. If the task is broad or ambiguous, also read `docs/openspec-standard-programming.md` and `openspec/config.yaml`.

## Decision Flow

1. If the user is exploring or comparing options, investigate code and OpenSpec artifacts, but do not implement.
2. If the user requests a new feature or behavior change, create an OpenSpec change first unless an active change already covers it.
3. If the user asks to implement, read the active change artifacts and work through `tasks.md`.
4. If the user asks to sync, merge change specs into `openspec/specs/<capability>/spec.md`.
5. If the user asks to archive, check artifacts and task completion, then move the change to `openspec/changes/archive/YYYY-MM-DD-<change-id>/`.

## Change Artifact Rules

- Use `openspec/changes/<change-id>/`.
- Use kebab-case names.
- Include `proposal.md`, `design.md`, `tasks.md`, and at least one `specs/<capability>.md`.
- Write scenarios with GIVEN/WHEN/THEN.
- Keep `proposal.md` scope explicit; include non-goals.
- Keep `tasks.md` as actionable checkboxes.

## Implementation Rules

- Do not edit app code for behavior changes until OpenSpec artifacts exist and have been read.
- Keep code changes scoped to tasks and proposal scope.
- Mark completed tasks in `tasks.md` immediately.
- If implementation reveals a spec/design mismatch, update artifacts before continuing.
- Run relevant verification, such as `npm.cmd run build` for the Vue frontend.
- Mention any verification that could not be run.

## CLI Fallback

If `openspec` CLI is available, use it for `list`, `status`, `instructions`, and archive context. If it is not available, create and update files manually following `references/workflow.md`.

## Output Expectations

- When creating docs: list created paths and explain how to use them.
- When implementing: report change name, tasks completed, files changed, and verification result.
- When blocked: state the missing artifact, unclear requirement, or failing command.
