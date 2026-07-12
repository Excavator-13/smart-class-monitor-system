## MODIFIED Requirements

### Requirement: Frontend register form calls POST /auth/register

The frontend register form SHALL call `POST /auth/register` with `{ username, password, nickname? }` and automatically log the user in upon success, instead of showing a placeholder notice.

#### Scenario: Successful registration and auto-login

- **WHEN** a user fills in `username`, `password`, and optional `nickname` on the register form and submits
- **THEN** the frontend SHALL call `POST /auth/register` with `{ username, password, nickname }`
- **AND** upon receiving `{ code: 0, data: { token, user_id, username, role, nickname, avatar_url } }`, the frontend SHALL store the JWT token and user info (same as login flow) and enter the authenticated app
- **AND** the user SHALL see the main dashboard without needing to manually log in again

#### Scenario: Duplicate username shows error

- **WHEN** the backend returns `code: 409` with message "用户名已存在"
- **THEN** the frontend SHALL display the error message from the backend response
- **AND** the register form SHALL remain visible for the user to correct the input

#### Scenario: Validation error from backend

- **WHEN** the backend returns `code: 400` with a validation error message (e.g., username too short, password too short)
- **THEN** the frontend SHALL display the backend error message
- **AND** the register form SHALL remain visible

#### Scenario: Network error during registration

- **WHEN** the registration request fails due to network error
- **THEN** the frontend SHALL display a generic error message: "注册请求失败，请确认后端服务可用。"
- **AND** the register form SHALL remain visible

### Requirement: Register form fields align with backend RegisterRequest DTO

The register form SHALL use `username` and `password` fields matching the backend `RegisterRequest` DTO. The form SHALL NOT use `phone`, `role`, `confirmPassword`, or `remark` fields.

#### Scenario: Register form has username field

- **WHEN** the register form is displayed
- **THEN** it SHALL contain an input labeled "用户名" bound to `registerForm.username`
- **AND** it SHALL NOT contain a "手机号" input

#### Scenario: Register form has password field

- **WHEN** the register form is displayed
- **THEN** it SHALL contain a password input labeled "密码" bound to `registerForm.password`

#### Scenario: Register form has optional nickname field

- **WHEN** the register form is displayed
- **THEN** it SHALL contain an optional input labeled "昵称" bound to `registerForm.nickname`
- **AND** the placeholder SHALL indicate the field is optional

#### Scenario: Register form does not have role selector

- **WHEN** the register form is displayed
- **THEN** it SHALL NOT contain a role selector (role is always `teacher` by backend default)

#### Scenario: Register form does not have confirm password

- **WHEN** the register form is displayed
- **THEN** it SHALL NOT contain a "确认密码" input

#### Scenario: Register form does not have remark field

- **WHEN** the register form is displayed
- **THEN** it SHALL NOT contain a "申请说明" textarea

### Requirement: Register API function in smartClassApi.js

`smartClassApi.js` SHALL export a `register` function that calls `POST /auth/register` via `apiClient`.

#### Scenario: Register function sends correct request

- **WHEN** `register({ username: "newuser", password: "123456", nickname: "New User" })` is called
- **THEN** it SHALL send `POST /auth/register` with body `{ username: "newuser", password: "123456", nickname: "New User" }`
- **AND** it SHALL return the unwrapped response data (same as `login`)

### Requirement: Remove "规则配置" button from header

The top header bar SHALL NOT contain a standalone "规则配置" button. The "区域规则" entry in the left sidebar navigation is the sole navigation path to the rules page.

#### Scenario: Header has no rules button

- **WHEN** the authenticated app is displayed
- **THEN** the header actions area SHALL NOT contain a button with text "规则配置"
- **AND** the left sidebar SHALL still contain the "区域规则" navigation item
