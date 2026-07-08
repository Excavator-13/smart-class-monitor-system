## ADDED Requirements

### Requirement: Logout endpoint
The system SHALL provide `POST /auth/logout` that accepts a valid JWT token and returns success. In the initial version, this is a no-op on the server side.

#### Scenario: Logout returns success
- **WHEN** a valid token is provided to `POST /auth/logout`
- **THEN** the response SHALL have `code: 0` and `message: "success"`

#### Scenario: Logout requires authentication
- **WHEN** no token is provided to `POST /auth/logout`
- **THEN** the response SHALL have `code: 401`
