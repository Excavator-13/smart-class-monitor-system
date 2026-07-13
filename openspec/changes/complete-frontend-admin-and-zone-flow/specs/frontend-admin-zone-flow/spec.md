# Frontend Admin and Zone Flow Specification

## ADDED Requirements

### Requirement: Persisted zones are rendered once

The Vue monitor SHALL render only a local draft rectangle. Persisted zones SHALL be displayed through the annotated AI video stream.

#### Scenario: Zone creation succeeds

- **WHEN** a draft is confirmed and `POST /zones` succeeds
- **THEN** the Vue draft overlay disappears
- **AND** Vue does not add a second persisted rectangle overlay

### Requirement: Monitor drafts support all zone types

Before confirmation, the user SHALL provide a name and select `danger`, `seat`, `phone_forbidden`, or `roi`; the initial type SHALL be `danger`.

#### Scenario: Create a seat zone

- **WHEN** the user draws a rectangle, selects `seat`, enters a name, and confirms
- **THEN** `POST /zones` receives `zone_type: seat` and the four normalized coordinates

### Requirement: Zone type can be updated

`PUT /zones/{id}` SHALL accept `zone_type` and SHALL persist the new value before triggering the existing AI configuration reload.

### Requirement: Admin-only user management

Only authenticated admins SHALL see the User Management navigation item and page. The page SHALL list backend users and update roles through `PUT /users/{id}/role`.

#### Scenario: Teacher signs in

- **WHEN** the current role is `teacher`
- **THEN** User Management is absent from navigation

#### Scenario: Admin changes another user role

- **WHEN** an admin changes another user from `teacher` to `admin`
- **THEN** the frontend sends the API request and updates the row only after success

### Requirement: Monitor alert history has useful height

The monitor alert tracking table SHALL show substantially more vertical content than the previous 248-pixel table.

### Requirement: HTTP smoke tests match backend contracts

`api-test.http` SHALL be concise, readable UTF-8, and use current endpoint paths, query parameter names, authentication headers, and JSON field formats.

