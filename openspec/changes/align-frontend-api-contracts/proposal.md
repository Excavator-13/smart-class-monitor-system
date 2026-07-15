# Align Frontend API Contracts

## Motivation

The current Vue frontend still behaves like a demo prototype: API failures are silently replaced with local mock data, login can fall back to a demo token, and several AI/alert behaviors are derived from hardcoded UI assumptions instead of documented SpringBoot, Flask AI, and Nginx contracts.

This makes integration misleading because the page can look healthy while backend, AI, or media APIs are failing or returning incompatible fields.

## Scope

- Align frontend service calls with the documented SpringBoot endpoints:
  - `/auth/login`, `/auth/info`, `/auth/logout`
  - `/streams`, `/streams/enabled`, `/streams/{stream_id}/status`, `/streams/{stream_id}/preview-url`
  - `/alerts`, `/alert-stats`
  - `/rules`, `/zones`, `/streams/{stream_id}/zones`
  - `/students`, `/system/health`
- Align frontend AI calls with the documented Flask endpoints:
  - `/model/status`
  - `/analysis/events`
  - `/analysis/summary/{stream_id}`
  - `/video_feed/{stream_id}`
- Use Nginx media base only for backend/AI-returned relative snapshot and recording paths.
- Remove implicit demo fallbacks from production-like execution.
- Keep local mock data only behind an explicit `VITE_USE_MOCK=true` / runtime `USE_MOCK` switch.
- Add adapter logic so the UI consumes normalized frontend models while preserving documented snake_case API fields.
- Replace hardcoded phone violation and AI summary assumptions with API-derived event/alert data and clear empty states.

## Out of Scope

- Implementing backend, AI, database, or Nginx services.
- Inventing missing backend APIs.
- Changing `openspec/README.md`.
- Creating git commits, merges, or branch operations.

## Impacted Modules

- `frontend/src/services`
- `frontend/src/App.vue`
- `frontend/src/data/mockData.js`
- `openspec/changes/align-frontend-api-contracts`
