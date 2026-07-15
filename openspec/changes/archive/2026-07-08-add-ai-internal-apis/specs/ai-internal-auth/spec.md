## ADDED Requirements

### Requirement: AI endpoints protected by internal token
AI internal endpoints (`/alerts/ai`, `/students/face-features`) SHALL use `X-Internal-Token` header for authentication, NOT frontend JWT. The internal token SHALL be configurable via `ai.internal-token`.

#### Scenario: Valid internal token
- **WHEN** request includes correct `X-Internal-Token`
- **THEN** the request SHALL proceed to the controller

#### Scenario: Missing or wrong internal token
- **WHEN** `X-Internal-Token` is missing or incorrect
- **THEN** the response SHALL have `code: 401`

### Requirement: AI endpoints excluded from JWT interceptor
`/alerts/ai` and `/students/face-features` SHALL be added to `JwtAuthenticationInterceptor` exclude list so frontend JWT is not required for these paths.

### Requirement: Internal auth does NOT affect frontend JWT
The internal token interceptor SHALL only apply to AI-specific paths. Frontend JWT SHALL continue to work for all other endpoints.
