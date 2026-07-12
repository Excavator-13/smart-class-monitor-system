# Complete Frontend Admin and Zone Flow

## Motivation

Persisted zones are already drawn into the MJPEG stream by the AI service, but the Vue monitor draws the same zones again. Monitor-created zones are also hardcoded as `phone_forbidden`, while the backend update DTO silently ignores `zone_type`. The frontend has no user administration page despite the existing admin-only `/users` API, the monitor alert history is unnecessarily short, and the root HTTP test file is long, garbled, and inconsistent with current request contracts.

## Scope

- Show only the local draft zone overlay in the Vue monitor; let AI own persisted-zone visualization.
- Require a zone name and type when confirming a monitor draft, with `danger` as the default.
- Allow the backend zone update contract to change `zone_type`.
- Add an admin-only user management page that lists users and changes `admin`/`teacher` roles through `/users`.
- Increase the monitor alert tracking table height.
- Audit non-report frontend mock/local-only behavior and keep mock fallback limited to the explicit developer mode.
- Replace `api-test.http` with a concise, UTF-8, backend-aligned smoke suite.

## Out of Scope

- AI report, DingTalk report settings, report persistence, or any related frontend/backend code.
- Changing AI zone rendering behavior.
- Modifying README files.

## Impacted Modules

- `frontend/src/App.vue`
- `frontend/src/services/smartClassApi.js`
- `frontend/src/styles.css`
- `backend_system/.../ZoneUpdateRequest.java`
- `backend_system/.../ZoneService.java`
- `api-test.http`

