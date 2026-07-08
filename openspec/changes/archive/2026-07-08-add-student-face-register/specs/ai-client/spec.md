## ADDED Requirements

### Requirement: AiClient calls AI feature extraction
The system SHALL provide `AiClient` in `com.smartclass.monitor.integration` with method `extractFeature(String base64Image, String studentId)` that calls `POST {AI_BASE_URL}/face/feature/extract` and returns parsed result.

#### Scenario: Successful extraction
- **WHEN** AI `/face/feature/extract` returns valid JSON with `code: 0`
- **THEN** `AiClient` SHALL return `FaceExtractResult` containing `faceCount`, `featureDim`, `featureVector`, `qualityScore`, `bbox`

#### Scenario: AI returns error
- **WHEN** AI returns non-zero `code`
- **THEN** `AiClient` SHALL throw `BusinessException` with the AI error code and message

#### Scenario: AI unreachable
- **WHEN** HTTP request to AI times out
- **THEN** `AiClient` SHALL throw `BusinessException(500, "AI 服务不可用")`

### Requirement: AiClient calls face features reload
The system SHALL provide method `reloadFeatures()` that calls `POST {AI_BASE_URL}/face/features/reload`.

### Requirement: AI base URL configurable
AI service base URL SHALL be configured via `application.yml` property `ai.base-url`.

#### Scenario: Base URL from configuration
- **WHEN** application starts
- **THEN** `AiClient` SHALL read `ai.base-url` (default: `http://39.106.209.208:5000`)
