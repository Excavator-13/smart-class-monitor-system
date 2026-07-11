## ADDED Requirements

### Requirement: User can register a new account

The system SHALL provide `POST /auth/register` accepting `username`, `password`, and optional `nickname`, creating a new user and returning a JWT token and user information on success. The password SHALL be hashed using BCrypt before storage.

#### Scenario: Successful registration

- **WHEN** a valid `username` and `password` are submitted with no existing user by that name
- **THEN** the response SHALL contain `code: 0`, a JWT `token`, and user info including `user_id`, `username`, `role` (default `teacher`), `nickname`, `avatar_url` (null)

#### Scenario: Duplicate username

- **WHEN** a `username` that already exists is submitted
- **THEN** the response SHALL have `code: 409` and message indicating the username is already taken

#### Scenario: Missing username

- **WHEN** `username` is missing or blank
- **THEN** the response SHALL have `code: 400` and message indicating username is required

#### Scenario: Missing password

- **WHEN** `password` is missing or blank
- **THEN** the response SHALL have `code: 400` and message indicating password is required

#### Scenario: Username too short

- **WHEN** `username` is shorter than 2 characters
- **THEN** the response SHALL have `code: 400` and message indicating username length constraint

#### Scenario: Username too long

- **WHEN** `username` exceeds 64 characters
- **THEN** the response SHALL have `code: 400` and message indicating username length constraint

#### Scenario: Password too short

- **WHEN** `password` is shorter than 6 characters
- **THEN** the response SHALL have `code: 400` and message indicating password length constraint

#### Scenario: Password too long

- **WHEN** `password` exceeds 128 characters
- **THEN** the response SHALL have `code: 400` and message indicating password length constraint

#### Scenario: Nickname too long

- **WHEN** `nickname` exceeds 64 characters
- **THEN** the response SHALL have `code: 400` and message indicating nickname length constraint

### Requirement: Register endpoint is excluded from JWT authentication

The system SHALL allow unauthenticated access to `POST /auth/register`, consistent with `/auth/login`.

#### Scenario: Register endpoint is excluded from auth

- **WHEN** a request is made to `POST /auth/register` without a JWT token
- **THEN** the JWT interceptor SHALL NOT block the request

### Requirement: Registered user defaults

A newly registered user SHALL have `role` set to `teacher`, `status` set to `enabled`, and `avatar_url` set to null.

#### Scenario: Default values applied

- **WHEN** a user is successfully registered
- **THEN** the created user record SHALL have `role = "teacher"`, `status = "enabled"`, `avatar_url = null`

### Requirement: Register request body uses snake_case

The register request DTO SHALL use Java camelCase internally and serialize to snake_case JSON (`{ "username": "...", "password": "...", "nickname": "..." }`).

#### Scenario: snake_case JSON accepted

- **WHEN** a POST to `/auth/register` sends `{ "username": "newuser", "password": "123456", "nickname": "New User" }`
- **THEN** the server SHALL correctly parse and accept the request
