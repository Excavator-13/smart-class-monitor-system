## ADDED Requirements

### Requirement: Alert recording button opens video player dialog

When a user clicks the "录像" button on an alert row that has a `record_url`, the system SHALL open a dialog containing an HTML5 `<video>` player that loads and plays the recording segment.

#### Scenario: Click recording button with record_url present

- **GIVEN** an alert row has `record_url = "/records/20260713/classroom_01-2026-07-13-08_30_00.mp4"`
- **AND** `event_time_offset = 17.0`
- **WHEN** the user clicks the "录像" button
- **THEN** a dialog SHALL open
- **AND** the dialog SHALL contain a `<video>` element with `src` set to `joinResourceUrl(record_url)`
- **AND** the video SHALL have `controls` attribute enabled

#### Scenario: Recording button disabled when no record_url

- **GIVEN** an alert row has `record_url = null` or `record_url = ""`
- **WHEN** the alert list is rendered
- **THEN** the "录像" button SHALL be disabled

### Requirement: Video player seeks to event time offset

When the video player has loaded the recording segment's metadata, it SHALL automatically seek to the `event_time_offset` position and begin playback.

#### Scenario: Auto-seek to event offset

- **GIVEN** the video player dialog is open
- **AND** `event_time_offset = 17.0`
- **WHEN** the `<video>` element fires `loadedmetadata`
- **THEN** `video.currentTime` SHALL be set to `17.0`
- **AND** `video.play()` SHALL be called

#### Scenario: No offset when event_time_offset is null

- **GIVEN** the video player dialog is open
- **AND** `event_time_offset` is `null` or `undefined`
- **WHEN** the `<video>` element fires `loadedmetadata`
- **THEN** `video.currentTime` SHALL remain at `0`
- **AND** `video.play()` SHALL be called

### Requirement: Video player dialog cleanup

When the video player dialog is closed, the video SHALL be paused and the source released to free network and decode resources.

#### Scenario: Dialog close pauses and releases video

- **GIVEN** the video player dialog is open and the video is playing
- **WHEN** the user closes the dialog
- **THEN** `video.pause()` SHALL be called
- **AND** `video.src` SHALL be set to `""` to release the resource

### Requirement: normalizeAlert maps event_time_offset

The `normalizeAlert()` function SHALL map the `event_time_offset` field from the API response to the normalized alert object.

#### Scenario: event_time_offset mapped from API response

- **GIVEN** an API response alert with `eventTimeOffset = 17.0`
- **WHEN** `normalizeAlert()` is called
- **THEN** the normalized alert SHALL have `event_time_offset = 17.0`

#### Scenario: event_time_offset null when absent

- **GIVEN** an API response alert without `eventTimeOffset` or `event_time_offset`
- **WHEN** `normalizeAlert()` is called
- **THEN** the normalized alert SHALL have `event_time_offset = null`
