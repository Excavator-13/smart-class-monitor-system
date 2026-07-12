# Persist Multiple Monitor Zones

## Motivation

The real-time monitor currently stores a single hand-drawn forbidden zone only in Vue memory. Confirming or clearing the rectangle does not call SpringBoot, so the AI zone cache is not refreshed and the zone disappears after a reload. The monitor also cannot display or selectively delete multiple forbidden zones.

## Scope

- Persist each confirmed rectangle through `POST /zones` as a `phone_forbidden` zone.
- Render all enabled `phone_forbidden` zones returned for the active stream.
- Delete a selected zone through `DELETE /zones/{id}` from a visible zone list.
- Keep one draft rectangle at a time while allowing any number of confirmed rectangles.
- Treat SpringBoot as the only frontend-facing configuration service; SpringBoot remains responsible for notifying AI through `/config/reload`.
- Apply the same multi-zone overlays and controls to normal and full-screen video.

## Out of Scope

- Changing the `/zones` backend contract or database schema.
- Calling the Flask AI service directly from the browser for zone changes.
- Changing non-phone zone detection semantics.
- Modifying any README file.

## Impacted Modules

- `frontend/src/services/smartClassApi.js`
- `frontend/src/App.vue`
- `frontend/src/styles.css`

