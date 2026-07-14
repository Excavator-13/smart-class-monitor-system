# Stabilize AI Alert Output

## Motivation

AI detections currently use inconsistent per-module cooldowns and reuse one event ID for a continuously tracked event, so database write frequency is unpredictable. The annotated stream also lacks a short-lived alert list, and the rule-only fall heuristic can create alerts even though no fall model is integrated.

## Scope

- Enforce a 10-second database alert cooldown per stream, event type, and target track.
- Generate a new idempotency event ID for each alert allowed after the cooldown.
- Show newly confirmed alerts in the top-left of the annotated stream for two seconds.
- Document that current fall alerts originate from a person bounding-box aspect-ratio heuristic, not a YOLO fall class or dedicated model.

## Out of Scope

- Adding or training a fall-detection model.
- Changing the SpringBoot alert ingestion contract or database schema.
- Changing detector confidence and duration thresholds.

## Impacted Modules

- `backend_ai/services/event_service.py`
- `backend_ai/services/analysis_service.py`
- `backend_ai/config/app.yaml`
- AI unit tests
