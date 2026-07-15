## ADDED Requirements

### Requirement: Register face for a student
The system SHALL provide `POST /students/{id}/face` accepting a base64-encoded image. The system SHALL call AI `/face/feature/extract`, validate `face_count == 1`, persist the feature to `face_feature`, update `student.face_registered = true`, and notify AI to reload.

#### Scenario: Successful face registration
- **WHEN** a valid base64 image is uploaded for an existing enabled student
- **THEN** the feature SHALL be saved with `feature_dim` from AI response, `student.face_registered` SHALL be set to `true`, and the response SHALL include quality score and bbox

#### Scenario: No face detected
- **WHEN** AI returns `face_count = 0` or error code 40002
- **THEN** the response SHALL have `code: 400` and message "未检测到人脸"

#### Scenario: Multiple faces detected
- **WHEN** AI returns `face_count > 1` or error code 40003
- **THEN** the response SHALL have `code: 400` and message "检测到多个人脸"

#### Scenario: Student not found
- **WHEN** the student `id` does not exist
- **THEN** the response SHALL have `code: 404`

#### Scenario: AI service unavailable
- **WHEN** AI `/face/feature/extract` request times out or fails
- **THEN** the response SHALL have `code: 500` and NO data SHALL be written to `face_feature`

### Requirement: Feature dimension is dynamic
The system SHALL store `feature_dim` from AI response. The code SHALL NOT hardcode 128 or 512.

#### Scenario: Feature dimension saved from AI response
- **WHEN** AI returns `feature_dim: 512`
- **THEN** `face_feature.feature_dim` SHALL be `512`
- **WHEN** AI returns `feature_dim: 128`
- **THEN** `face_feature.feature_dim` SHALL be `128`

### Requirement: Reload failure does not block registration
If AI `/face/features/reload` fails, the registration SHALL still succeed. The error SHALL be logged.

#### Scenario: Reload fails after successful registration
- **WHEN** feature is saved but `/face/features/reload` call fails
- **THEN** the registration response SHALL still have `code: 0`
