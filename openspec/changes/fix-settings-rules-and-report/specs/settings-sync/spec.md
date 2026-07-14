## ADDED Requirements

### Requirement: dingtalkEnabled setting propagates to AI service

The `dingtalkEnabled` boolean setting SHALL be transmitted from the frontend through SpringBoot to the AI service, and the AI service SHALL use it to control whether DingTalk notifications are sent.

#### Scenario: Frontend sends dingtalkEnabled to backend

- **WHEN** the user toggles the DingTalk switch on the frontend
- **THEN** `syncContactsToBackend()` SHALL include `dingtalkEnabled` in the `PUT /api/settings` request body

#### Scenario: SpringBoot stores and forwards dingtalkEnabled

- **WHEN** SpringBoot receives `dingtalkEnabled` in `PUT /api/settings`
- **THEN** the value SHALL be stored in `SettingsController.store`
- **AND** the value SHALL be forwarded to the AI service via `POST /api/contacts/sync`

#### Scenario: AI service disables DingTalk when dingtalkEnabled is false

- **GIVEN** `AlertClient.dingtalk_enabled` is `False`
- **WHEN** `push_alert()` is called with an event in `DINGTALK_ALERT_TYPES`
- **THEN** the DingTalk notification SHALL NOT be sent
- **AND** the alert SHALL still be pushed to SpringBoot

#### Scenario: AI service enables DingTalk when dingtalkEnabled is true

- **GIVEN** `AlertClient.dingtalk_enabled` is `True`
- **AND** `self.dingtalk` callback is configured
- **WHEN** `push_alert()` is called with an event in `DINGTALK_ALERT_TYPES`
- **THEN** the DingTalk notification SHALL be sent

#### Scenario: AI service restores dingtalkEnabled on startup

- **GIVEN** SpringBoot has `dingtalkEnabled=false` in its settings store
- **WHEN** the AI service starts up and calls `_restore_dingtalk_settings()`
- **THEN** `AlertClient.dingtalk_enabled` SHALL be set to `False`

#### Scenario: dingtalkEnabled defaults to true when not set

- **GIVEN** SpringBoot settings do not contain `dingtalkEnabled`
- **WHEN** the AI service initializes `AlertClient`
- **THEN** `AlertClient.dingtalk_enabled` SHALL default to `True` (backward compatible)

### Requirement: aiReportEnabled setting controls auto report generation

The `aiReportEnabled` boolean setting SHALL be transmitted from the frontend to SpringBoot, and `ReportService.checkAndAutoGenerate()` SHALL respect it.

#### Scenario: Frontend sends aiReportEnabled to backend

- **WHEN** the user toggles the AI Report switch on the frontend
- **THEN** `syncContactsToBackend()` SHALL include `aiReportEnabled` in the `PUT /api/settings` request body

#### Scenario: Auto report skipped when aiReportEnabled is false

- **GIVEN** `settings` Map contains `aiReportEnabled=false`
- **AND** the current time matches `reportTime`
- **WHEN** `checkAndAutoGenerate()` runs
- **THEN** the report SHALL NOT be generated

#### Scenario: Auto report runs when aiReportEnabled is true

- **GIVEN** `settings` Map contains `aiReportEnabled=true`
- **AND** the current time matches `reportTime`
- **WHEN** `checkAndAutoGenerate()` runs
- **THEN** the report SHALL be generated

#### Scenario: Auto report runs when aiReportEnabled is not set (backward compatible)

- **GIVEN** `settings` Map does not contain `aiReportEnabled`
- **AND** the current time matches `reportTime`
- **WHEN** `checkAndAutoGenerate()` runs
- **THEN** the report SHALL be generated (treats absent as true)

### Requirement: Frontend watches dingtalkEnabled and aiReportEnabled changes

The frontend SHALL trigger `syncContactsToBackend()` when `dingtalkEnabled` or `aiReportEnabled` changes, not just when contacts or responsible person changes.

#### Scenario: Toggling DingTalk switch syncs to backend

- **WHEN** the user toggles `alertSettings.dingtalkEnabled`
- **THEN** `syncContactsToBackend()` SHALL be called

#### Scenario: Toggling AI Report switch syncs to backend

- **WHEN** the user toggles `alertSettings.aiReportEnabled`
- **THEN** `syncContactsToBackend()` SHALL be called
