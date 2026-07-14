## 1. Backend contract

- [x] 1.1 Add target_info and zone_id to AlertVO and service mapping.
- [x] 1.2 Update Swagger/interface documentation and backend tests or compilation verification.

## 2. AI visualization and compatibility

- [x] 2.1 Cache confirmed target bbox in alert overlays and draw it for the configured duration.
- [x] 2.2 Increase the default overlay duration to five seconds.
- [x] 2.3 Add `/events` as a compatibility alias and cover it with route tests.

## 3. Frontend visibility

- [x] 3.1 Preserve target_info/zone_id during alert normalization.
- [x] 3.2 Show persisted phone alerts even when historical target metadata is absent.

## 4. Verification

- [x] 4.1 Run focused AI pytest, frontend build, backend Maven tests, and diff checks.
