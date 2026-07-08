## ADDED Requirements

### Requirement: Token-based authentication for protected endpoints
The system SHALL require a valid JWT token in the `Authorization: Bearer <token>` header for all endpoints except `/auth/login`, `/system/health`, Swagger UI, and API docs paths.

#### Scenario: Valid token allows access
- **WHEN** a request includes a valid, non-expired JWT token in the `Authorization` header
- **THEN** the request SHALL proceed to the controller

#### Scenario: Missing token returns 401
- **WHEN** a request to a protected endpoint has no `Authorization` header
- **THEN** the response SHALL have `code: 401` and message indicating authentication is required

#### Scenario: Expired token returns 401
- **WHEN** a request includes an expired JWT token
- **THEN** the response SHALL have `code: 401` and message indicating token expiration

#### Scenario: Invalid token returns 401
- **WHEN** a request includes a malformed or tampered JWT token
- **THEN** the response SHALL have `code: 401`

#### Scenario: Login endpoint is excluded from auth
- **WHEN** a request is made to `POST /auth/login`
- **THEN** the JWT interceptor SHALL NOT block the request

#### Scenario: Health endpoint is excluded from auth
- **WHEN** a request is made to `GET /system/health`
- **THEN** the JWT interceptor SHALL NOT block the request

### Requirement: Get current user info
The system SHALL provide `GET /auth/info` that returns the authenticated user's information based on the JWT token.

#### Scenario: Returns current user info
- **WHEN** a valid token is provided to `GET /auth/info`
- **THEN** the response SHALL contain the user's `username`, `role`, `nickname`, `avatar_url`

#### Scenario: User not found despite valid token
- **WHEN** a valid token references a `user_id` that no longer exists
- **THEN** the response SHALL have `code: 404`

### Requirement: JWT token contains required claims
The JWT token SHALL contain at minimum `user_id` (subject), `username`, `role`, issue time (`iat`), and expiration time (`exp`).

#### Scenario: Token claims are complete
- **WHEN** a token is generated after successful login
- **THEN** the token payload SHALL include `sub` (user_id), `username`, `role`, `iat`, `exp`
