## 1. Stream lifecycle and frame freshness

- [x] 1.1 Add frame sequence, recovery-candidate state, and configurable stable-recovery timing to `StreamManager`.
- [x] 1.2 Add a thread-safe one-time analysis claim for each `(stream_id, frame_sequence)` while preserving the existing frame API.
- [x] 1.3 Update `/video_feed` to analyze only newly claimed frames and quarantine frames during an unresolved offline episode.
- [x] 1.4 Add stream regression tests for repeated cached-frame polling, concurrent consumers, buffered-frame bursts, one offline alert per episode, and stable recovery.

## 2. Zone coordinate and visualization fixes

- [x] 2.1 Add geometry helpers that normalize pixel bbox centers/foot points using the current frame dimensions while remaining compatible with normalized test data.
- [x] 2.2 Pass frame dimensions through `AnalysisService` to phone and danger-zone matching without changing returned pixel target boxes.
- [x] 2.3 Add danger-zone event labels to target drawing and confirmed alert overlays.
- [x] 2.4 Add regression tests using realistic pixel bbox values for phone-forbidden and danger zones, plus configuration reload coverage.

## 3. Fire false-positive controls

- [x] 3.1 Resolve `fire_detected`/`flame_detected` rule aliases, skip business detection when the rule is disabled, and apply the stricter effective confidence threshold.
- [x] 3.2 Filter model results with a configurable fire-class allowlist while retaining compatibility with single-class weights that lack usable names.
- [x] 3.3 Add fire tests for the backend rule alias, disabled rule, stricter threshold, allowed class, rejected class, and rule duration propagation.

## 4. Configuration and documentation

- [x] 4.1 Add documented defaults for stream recovery timing and fire allowed classes without overwriting the user's model enablement changes.
- [x] 4.2 Update `docs/AI服务详细设计文档.md` and the fire detection spec to describe coordinate normalization, frame freshness, rule aliases, and false-positive filtering.

## 5. Verification

- [x] 5.1 Run focused AI pytest suites for stream, behavior, zone, fire, configuration, and visualization.
- [x] 5.2 Run the complete `backend_ai` pytest suite and resolve regressions within this change's scope.
- [x] 5.3 Validate the OpenSpec change and review the final diff for unrelated edits.
