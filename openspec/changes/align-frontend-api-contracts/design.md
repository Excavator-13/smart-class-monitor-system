# Design

## API Response Handling

SpringBoot and AI JSON APIs both return an envelope with `code`, `message`, and `data`. AI may additionally include `timestamp` and `trace_id`.

The frontend service layer shall:

- unwrap only successful envelopes where `code === 0`;
- throw an error for non-zero `code`;
- not swallow request failures unless explicit mock mode is enabled;
- normalize paged responses from `records`, `items`, `list`, or direct arrays.

## Mock Mode

Mock data remains useful for offline UI work, but must not be implicit.

Mock mode is enabled only when:

- `window.__SMART_CLASS_CONFIG__.USE_MOCK === true`, or
- `VITE_USE_MOCK=true`.

When mock mode is disabled, failed APIs surface as empty/error states in the UI.

## Frontend Model Normalization

The UI should not guess backend field variants in templates. Service/adapters normalize:

- alerts: `id`, `event_id`, `stream_id`, `stream_name`, `student_name`, `alert_type`, `level`, `status`, `confidence`, `snapshot_url`, `record_url`, `occurred_at`, `target`;
- streams: `id`, `stream_id`, `stream_name`, `location`, `status`, `rtmp_url`, `mjpeg_url`, `hls_url`;
- rules: `id`, `rule_type`, `name`, `enabled`, `threshold_seconds`, `confidence_threshold`, `cooldown_seconds`, `zone_type`;
- zones: `id`, `zone_id`, `stream_id`, `zone_name`, `zone_type`, `coordinates`, `enabled`;
- students: `id`, `student_no`, `name`, `class_name`, `status`, `face_registered`, `last_seen`;
- AI events: `event_id`, `stream_id`, `event_type`, `event_name`, `level`, `event_status`, `confidence`, `occurred_at`, `duration_seconds`, `target`, `zone`, `snapshot_path`;
- AI model status: `service_status`, `models`, `streams`.

## Phone Violation Rule

Before a forbidden zone is confirmed, phone-related alerts/events are hidden from phone-violation UI surfaces.

After a forbidden zone is confirmed:

- phone violation is shown only when an API-returned phone event/alert target bounding box intersects the selected forbidden zone;
- if no phone target bbox exists, the UI does not fabricate a phone violation;
- AI annotation overlays use event/alert target data when available.

## Media URL Handling

Frontend static assets must not be placed under `/media` because Vite proxies `/media` to Nginx.

Backend/AI returned relative media paths are joined with `VITE_NGINX_BASE` / runtime `NGINX_BASE`.

## Missing APIs

For UI controls that do not have confirmed APIs, the frontend should show a clear unavailable state or use local-only pending state, not pretend persistence succeeded.
