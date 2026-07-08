## ADDED Requirements

### Requirement: List students with pagination
The system SHALL provide `GET /students` returning paginated student list. Filters SHALL include `class_name`, `keyword` (matches `name` or `student_no`), `face_registered`. Pagination SHALL use `page`, `page_size`, `records`, `total`.

#### Scenario: List with keyword filter
- **WHEN** `GET /students?keyword=张三&page=1&page_size=10` is called
- **THEN** records matching "张三" in name or student_no SHALL be returned

#### Scenario: List with class_name filter
- **WHEN** `GET /students?class_name=软件工程1班` is called
- **THEN** only students in that class SHALL be returned

### Requirement: Create student
The system SHALL provide `POST /students` accepting `student_no`, `name`, `class_name`. `student_no` MUST be unique. `face_registered` SHALL default to `false`.

#### Scenario: Create successfully
- **WHEN** valid `student_no`, `name`, `class_name` are submitted
- **THEN** the response SHALL have `code: 0` and the new student's `id`

#### Scenario: Duplicate student_no
- **WHEN** an existing `student_no` is submitted
- **THEN** the response SHALL have `code: 409`

#### Scenario: Missing required fields
- **WHEN** `student_no` or `name` is missing
- **THEN** the response SHALL have `code: 400`

### Requirement: Get student detail
The system SHALL provide `GET /students/{id}` returning full student information.

#### Scenario: Student found
- **WHEN** a valid `id` is provided
- **THEN** student details including `student_no`, `name`, `class_name`, `face_registered`, `status` SHALL be returned

#### Scenario: Student not found
- **WHEN** an invalid `id` is provided
- **THEN** the response SHALL have `code: 404`

### Requirement: Update student
The system SHALL provide `PUT /students/{id}` accepting `name`, `class_name`, `status`, `remark`.

#### Scenario: Update successfully
- **WHEN** valid fields are submitted for an existing student
- **THEN** the response SHALL have `code: 0`

### Requirement: Soft delete student
The system SHALL provide `DELETE /students/{id}` that sets `deleted_at` without physical removal.

#### Scenario: Soft delete
- **WHEN** a valid `id` is provided
- **THEN** the student's `deleted_at` SHALL be set and the student SHALL no longer appear in `GET /students`
