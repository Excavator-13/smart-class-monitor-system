## ADDED Requirements

### Requirement: @RequireRole annotation for method-level access control

The system SHALL provide a `@RequireRole` annotation that can be placed on Controller classes or methods to declare the minimum required role(s). The annotation SHALL accept one or more role strings.

#### Scenario: Method requires admin role

- **WHEN** a Controller method is annotated with `@RequireRole("admin")`
- **AND** the current user's role is `admin`
- **THEN** the request SHALL proceed normally

#### Scenario: Method requires admin but user is teacher

- **WHEN** a Controller method is annotated with `@RequireRole("admin")`
- **AND** the current user's role is `teacher`
- **THEN** the response SHALL have `code: 403` and message indicating insufficient permissions

#### Scenario: Method allows multiple roles

- **WHEN** a Controller method is annotated with `@RequireRole({"admin", "teacher"})`
- **AND** the current user's role is `teacher`
- **THEN** the request SHALL proceed normally

#### Scenario: Class-level annotation applies to all methods

- **WHEN** a Controller class is annotated with `@RequireRole("admin")`
- **THEN** all methods in that class SHALL require the `admin` role unless overridden by a method-level annotation

#### Scenario: Method-level annotation overrides class-level

- **WHEN** a Controller class is annotated with `@RequireRole("admin")`
- **AND** a specific method is annotated with `@RequireRole({"admin", "teacher"})`
- **THEN** that method SHALL accept both `admin` and `teacher` roles

### Requirement: RequireRoleInterceptor enforces role checks

The system SHALL provide a `RequireRoleInterceptor` that executes after `JwtAuthenticationInterceptor`, reads `currentRole` from request attributes, and checks against the `@RequireRole` annotation on the handler method or its declaring class.

#### Scenario: No @RequireRole annotation means all authenticated users allowed

- **WHEN** a Controller method has no `@RequireRole` annotation (and neither does its class)
- **AND** the request has a valid JWT token
- **THEN** the request SHALL proceed regardless of role

#### Scenario: Role not in allowed set returns 403

- **WHEN** `@RequireRole("admin")` is present
- **AND** `currentRole` is `teacher`
- **THEN** the response SHALL have `code: 403` and message "权限不足"

#### Scenario: Unauthenticated request already rejected by JWT interceptor

- **WHEN** no valid JWT token is present
- **THEN** the JWT interceptor SHALL reject with 401 before the role interceptor executes

### Requirement: First registered user becomes admin

`POST /auth/register` SHALL check if the `user` table is empty (no records with `deleted_at IS NULL`). If empty, the new user's role SHALL be `admin`; otherwise, the role SHALL be `teacher`.

#### Scenario: First user registration

- **WHEN** no users exist in the database (0 records with `deleted_at IS NULL`)
- **AND** a new user registers
- **THEN** the new user's `role` SHALL be `admin`

#### Scenario: Subsequent user registration

- **WHEN** at least one user exists in the database
- **AND** a new user registers
- **THEN** the new user's `role` SHALL be `teacher`

#### Scenario: First user receives admin role in JWT

- **WHEN** the first user registers successfully
- **THEN** the returned JWT token SHALL contain `role: "admin"`
- **AND** the `LoginResponse` SHALL contain `role: "admin"`

### Requirement: User management API — list users

`GET /users` SHALL return a paginated list of users. Only users with `role: admin` SHALL be allowed to access this endpoint.

#### Scenario: Admin lists users

- **WHEN** an admin calls `GET /users`
- **THEN** the response SHALL contain paginated user records with `id`, `username`, `role`, `nickname`, `avatar_url`, `status`, `last_login_at`, `created_at`

#### Scenario: Teacher cannot list users

- **WHEN** a teacher calls `GET /users`
- **THEN** the response SHALL have `code: 403`

#### Scenario: Filter by role

- **WHEN** `GET /users?role=admin` is called
- **THEN** only users with `role: admin` SHALL be returned

#### Scenario: Filter by status

- **WHEN** `GET /users?status=enabled` is called
- **THEN** only users with `status: enabled` SHALL be returned

### Requirement: User management API — get user detail

`GET /users/{id}` SHALL return detailed information for a specific user. Only admin SHALL access.

#### Scenario: Admin gets user detail

- **WHEN** an admin calls `GET /users/{id}` with a valid user ID
- **THEN** the response SHALL contain `id`, `username`, `role`, `nickname`, `avatar_url`, `status`, `last_login_at`, `created_at`

#### Scenario: User not found

- **WHEN** an admin calls `GET /users/{id}` with a non-existent ID
- **THEN** the response SHALL have `code: 404`

### Requirement: User management API — update user role

`PUT /users/{id}/role` SHALL allow an admin to change a user's role. Request body: `{ "role": "admin" | "teacher" }`.

#### Scenario: Admin changes user role

- **WHEN** an admin calls `PUT /users/{id}/role` with `{ "role": "admin" }`
- **THEN** the user's role SHALL be updated to `admin`

#### Scenario: Teacher cannot change role

- **WHEN** a teacher calls `PUT /users/{id}/role`
- **THEN** the response SHALL have `code: 403`

#### Scenario: Invalid role value

- **WHEN** an admin calls `PUT /users/{id}/role` with `{ "role": "superuser" }`
- **THEN** the response SHALL have `code: 400` and message indicating invalid role

#### Scenario: Cannot change own role

- **WHEN** an admin calls `PUT /users/{id}/role` where `id` is their own user ID
- **THEN** the response SHALL have `code: 400` and message indicating cannot change own role

### Requirement: User management API — update user status

`PUT /users/{id}/status` SHALL allow an admin to enable or disable a user. Request body: `{ "status": "enabled" | "disabled" }`.

#### Scenario: Admin disables user

- **WHEN** an admin calls `PUT /users/{id}/status` with `{ "status": "disabled" }`
- **THEN** the user's status SHALL be updated to `disabled`

#### Scenario: Cannot disable self

- **WHEN** an admin calls `PUT /users/{id}/status` where `id` is their own user ID
- **THEN** the response SHALL have `code: 400` and message indicating cannot disable self

#### Scenario: Invalid status value

- **WHEN** an admin calls `PUT /users/{id}/status` with `{ "status": "banned" }`
- **THEN** the response SHALL have `code: 400` and message indicating invalid status

### Requirement: User management API — soft delete user

`DELETE /users/{id}` SHALL soft-delete a user by setting `deleted_at` to the current timestamp. Only admin SHALL access.

#### Scenario: Admin soft-deletes user

- **WHEN** an admin calls `DELETE /users/{id}`
- **THEN** the user's `deleted_at` SHALL be set to the current timestamp
- **AND** the user SHALL no longer appear in user listings or be able to log in

#### Scenario: Cannot delete self

- **WHEN** an admin calls `DELETE /users/{id}` where `id` is their own user ID
- **THEN** the response SHALL have `code: 400` and message indicating cannot delete self

### Requirement: User management API — update user profile

`PUT /users/{id}` SHALL allow updating a user's `nickname` and `avatar_url`. Only admin SHALL access.

#### Scenario: Admin updates user profile

- **WHEN** an admin calls `PUT /users/{id}` with `{ "nickname": "新昵称" }`
- **THEN** the user's nickname SHALL be updated

## MODIFIED Requirements

### Requirement: Write operations on streams require admin role

The following endpoints SHALL require `role: admin`:

- `POST /streams`
- `PUT /streams/{id}`
- `DELETE /streams/{id}`

Read operations (`GET /streams`, `GET /streams/{id}`, `GET /streams/enabled`, `GET /streams/{id}/status`, `GET /streams/{id}/preview-url`) SHALL remain accessible to all authenticated users.

#### Scenario: Teacher cannot create stream

- **WHEN** a teacher calls `POST /streams`
- **THEN** the response SHALL have `code: 403`

#### Scenario: Teacher can list streams

- **WHEN** a teacher calls `GET /streams`
- **THEN** the response SHALL succeed with `code: 0`

### Requirement: Write operations on students require admin role

The following endpoints SHALL require `role: admin`:

- `POST /students`
- `PUT /students/{id}`
- `DELETE /students/{id}`

Read operations (`GET /students`, `GET /students/{id}`) SHALL remain accessible to all authenticated users. Face registration (`POST /students/{id}/face`, `GET /students/{id}/face-features`) SHALL remain accessible to all authenticated users.

#### Scenario: Teacher cannot create student

- **WHEN** a teacher calls `POST /students`
- **THEN** the response SHALL have `code: 403`

#### Scenario: Teacher can register face

- **WHEN** a teacher calls `POST /students/{id}/face`
- **THEN** the request SHALL proceed normally

### Requirement: Write operations on zones require admin role

The following endpoints SHALL require `role: admin`:

- `POST /zones`
- `PUT /zones/{id}`
- `DELETE /zones/{id}`

Read operations (`GET /zones`, `GET /zones/{id}`, `GET /streams/{id}/zones`) SHALL remain accessible to all authenticated users.

### Requirement: Write operations on rules require admin role

The following endpoints SHALL require `role: admin`:

- `POST /rules`
- `PUT /rules/{id}`
- `DELETE /rules/{id}`

Read operations (`GET /rules`, `GET /rules/{id}`) SHALL remain accessible to all authenticated users.

### Requirement: Operation logs require admin role

`GET /operation-logs` SHALL require `role: admin`.

#### Scenario: Teacher cannot view operation logs

- **WHEN** a teacher calls `GET /operation-logs`
- **THEN** the response SHALL have `code: 403`

### Requirement: Report generation requires admin role

`POST /report/generate` SHALL require `role: admin`. `GET /report/latest` SHALL remain accessible to all authenticated users.

### Requirement: Alert operations accessible to all authenticated users

All alert endpoints (`GET /alerts`, `GET /alerts/{id}`, `PUT /alerts/{id}/status`, `GET /alert-stats`) SHALL remain accessible to all authenticated users (both `admin` and `teacher`).

### Requirement: Recording query accessible to all authenticated users

`GET /recordings` SHALL remain accessible to all authenticated users.

### Requirement: System health accessible without authentication

`GET /system/health` SHALL remain excluded from JWT authentication (no token required) and SHALL NOT require any specific role.
