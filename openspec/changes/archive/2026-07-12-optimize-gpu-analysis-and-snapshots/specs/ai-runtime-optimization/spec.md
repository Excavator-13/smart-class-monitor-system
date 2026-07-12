# AI Runtime Optimization Specification

## MODIFIED Requirements

### Requirement: GPU model execution

The AI service SHALL pass the configured CUDA device to InsightFace and all Ultralytics inference models.

#### Scenario: CUDA models load successfully

- **GIVEN** `model.yaml` configures `device: cuda`
- **WHEN** the AI application starts
- **THEN** InsightFace SHALL request `CUDAExecutionProvider`
- **AND** behavior YOLOv8 and fire YOLO SHALL execute inference on CUDA

#### Scenario: CUDA runtime is unavailable

- **GIVEN** CUDA or the GPU runtime dependency is unavailable
- **WHEN** a model is loaded
- **THEN** the console SHALL report the model load failure or actual fallback provider
- **AND** SHALL NOT report a false GPU success state

### Requirement: Model startup logs

The AI service SHALL log the InsightFace model name and provider, and the behavior YOLO model weights and device.

#### Scenario: Models load successfully

- **WHEN** InsightFace buffalo_l and YOLOv8 load successfully
- **THEN** the console SHALL contain success logs with model name or weights
- **AND** the console SHALL contain the selected device/provider

### Requirement: Danger-zone-only snapshots

The AI service SHALL generate a snapshot only for a confirmed `danger_zone_intrusion` event.

#### Scenario: Person enters danger zone

- **GIVEN** a `danger_zone_intrusion` event becomes confirmed
- **WHEN** the alert is pushed
- **THEN** one snapshot SHALL be saved
- **AND** its relative path SHALL be included in the alert

#### Scenario: Other event is confirmed

- **GIVEN** a face, phone, head-down, fire, audio, or other non-intrusion event becomes confirmed
- **WHEN** the alert is pushed
- **THEN** no snapshot SHALL be saved or pushed
- **AND** the alert `snapshot_path` SHALL remain empty

### Requirement: Global behavior detection with reduced overlays

Phone usage and head-down detection SHALL operate on the full frame and SHALL NOT depend on configured zones. The returned video frame SHALL draw only person/student object boxes and successfully recognized `face_recognized` boxes. Stranger, phone, head-down, zone and other event boxes SHALL NOT be drawn.

#### Scenario: Phone is detected outside all zones

- **GIVEN** a phone overlaps a detected person anywhere in the frame
- **WHEN** behavior rules are evaluated
- **THEN** a `phone_usage` event SHALL be produced regardless of zone configuration
- **AND** no phone or phone-usage box SHALL be drawn

#### Scenario: Head-down behavior is detected

- **GIVEN** a person has a head-down ratio above the configured threshold
- **WHEN** behavior rules are evaluated
- **THEN** a `head_down` event SHALL be produced regardless of zone configuration
- **AND** no head-down event box SHALL be drawn

#### Scenario: Stranger face is detected

- **GIVEN** an unrecognized face produces a `stranger_detected` event
- **WHEN** the returned video frame is rendered
- **THEN** the stranger event SHALL still be processed
- **AND** no stranger face box SHALL be drawn
