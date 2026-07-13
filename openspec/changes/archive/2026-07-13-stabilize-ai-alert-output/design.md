# Design

## Alert Identity and Cooldown

The cooldown key remains `(stream_id, event_type, track_key)`. `AnalysisService` applies one configured cooldown, defaulting to 10 seconds, instead of accepting detector-specific cooldown values. The first qualifying observation is pushed immediately. Further observations inside ten seconds remain candidates for display/query but are not pushed to SpringBoot. When the cooldown elapses, `EventService` creates a fresh event ID before the next push so SpringBoot idempotency permits a new database row.

## Stream Alert Overlay

`AnalysisService` owns an in-memory queue per stream. A confirmed event adds one entry containing its event ID, human-readable event name, and an expiry timestamp two seconds in the future. At the end of every analyzed frame, expired entries are removed and active entries are drawn as compact dark-backed text lines in the top-left. Candidate detections do not continuously refresh the expiry.

## Fall Detection Clarification

The existing behavior service derives `fall_detected` from the width/height ratio of a YOLO `person` box. YOLO supplies only the person box; the fall classification is a local geometric heuristic. No behavior change is included because replacing or disabling it requires a separate product decision.
