## ADDED Requirements

### Requirement: User can login with username and password
The system SHALL provide `POST /auth/login` accepting `username` and `password`, returning a JWT token and user information on success. Passwords SHALL be verified using BCrypt against the stored `password_hash`.

#### Scenario: Successful login
- **WHEN** valid `username` and `password` are submitted
- **THEN** the response SHALL contain `code: 0`, a JWT `token`, and user info including `user_id`, `username`, `role`, `nickname`, `avatar_url`

#### Scenario: Wrong password
- **WHEN** an incorrect `password` is submitted
- **THEN** the response SHALL have `code: 400` and message indicating invalid credentials

#### Scenario: User not found
- **WHEN** a non-existent `username` is submitted
- **THEN** the response SHALL have `code: 400` and message indicating invalid credentials

#### Scenario: Disabled user
- **WHEN** a valid `username` and `password` are submitted but the user's `status` is `disabled`
- **THEN** the response SHALL have `code: 403` and message indicating account is disabled

#### Scenario: Missing required fields
- **WHEN** `username` or `password` is missing from the request
- **THEN** the response SHALL have `code: 400` and indicate which field is missing

### Requirement: Login updates last login time
The system SHALL update `user.last_login_at` to the current timestamp upon successful login.

#### Scenario: Last login time updated
- **WHEN** a user successfully logs in
- **THEN** the `last_login_at` field of that user SHALL be updated in the database

### Requirement: Login request body uses snake_case
The login request DTO SHALL use Java camelCase internally and serialize to snake_case JSON (`{ "username": "...", "password": "..." }`).

#### Scenario: snake_case JSON accepted
- **WHEN** a POST to `/auth/login` sends `{ "username": "admin", "password": "123456" }`
- **THEN** the server SHALL correctly parse and accept the request
