## ADDED Requirements

### Requirement: Get face feature metadata for a student (frontend)
The system SHALL provide `GET /students/{id}/face-features` returning feature metadata (image path, quality score, created_at, version). The response SHALL NOT include `feature_vector`.

#### Scenario: Return metadata only
- **WHEN** `GET /students/{id}/face-features` is called
- **THEN** records SHALL include `id`, `image_path`, `quality_score`, `quality_json`, `bbox_json`, `feature_dim`, `version`, `created_at`
- **THEN** records SHALL NOT include `feature_vector`

### Requirement: Get full face features for AI (internal)
The system SHALL provide `GET /students/face-features` in `controller.ai` package. This endpoint SHALL return complete feature data including `feature_vector`. This endpoint SHALL NOT be accessible to frontend.

#### Scenario: AI gets full features
- **WHEN** `GET /students/face-features` is called by AI service with internal credentials
- **THEN** records SHALL include `student_id`, `student_name`, `class_name`, `feature_vector`, `feature_dim`, `enabled`

#### Scenario: Frontend cannot access
- **WHEN** `GET /students/face-features` is called with a frontend JWT token
- **THEN** the controller SHALL be in `controller.ai` package (not `controller`), separated from frontend routing
