# Design

## Zone Ownership

The AI service is the source of persisted-zone pixels. It loads enabled zones from SpringBoot and draws them in `analysis_service._draw_zones`. Vue renders only the rectangle currently being dragged or awaiting confirmation. After `POST /zones` succeeds, the draft disappears and the reloaded AI stream becomes responsible for displaying it.

The monitor confirmation controls collect `zone_name` and one of `danger`, `seat`, `phone_forbidden`, or `roi`. The default is `danger`. Region management remains in the Region Rules page. `PUT /zones/{id}` accepts `zone_type` so editing a type is not a false-success UI operation.

## User Administration

The navigation derives visible items from the authenticated role. Only an admin sees User Management. The page loads `GET /users`, shows username, nickname, role, status, creation time, and last login, and sends `PUT /users/{id}/role` for role changes. The current admin cannot change their own role, matching the backend rule. Backend `@RequireRole("admin")` remains the authority even if client-side navigation is bypassed.

## Demo-state Audit

Authentication token storage is legitimate session persistence and remains unchanged. Mock data remains available only when the user explicitly enters Developer Mode or sets `VITE_USE_MOCK=true`; production API failures are not converted to success. AI report code is excluded by user request.

## HTTP Smoke Suite

The root HTTP file keeps one representative request per core flow, uses UTF-8 Chinese labels, uses backend query parameter names, and uses snake_case JSON fields as serialized by the configured Jackson naming strategy. Destructive requests are clearly grouped and use replaceable IDs.

