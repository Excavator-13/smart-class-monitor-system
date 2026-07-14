# Snapshot Local Cleanup Specification

## MODIFIED Requirements

### Requirement: Local snapshot file deleted after successful SCP push

After `SnapshotPusher._push()` successfully pushes a snapshot to the remote server via SCP, the local file SHALL be deleted. If the parent directory becomes empty after deletion, the parent directory SHALL also be removed.

#### Scenario: SCP push succeeds — local file cleaned

- **GIVEN** `_save_snapshot()` saves a file to `static/snapshots/20260714/evt_abc123.jpg`
- **AND** `snapshot_remote.host` is configured
- **WHEN** the SCP push completes successfully (exit code 0)
- **THEN** the local file `static/snapshots/20260714/evt_abc123.jpg` SHALL be deleted
- **AND** a debug log SHALL record the cleanup

#### Scenario: SCP push succeeds — empty parent directory cleaned

- **GIVEN** a snapshot file is the only file in `static/snapshots/20260714/`
- **AND** the SCP push completes successfully
- **WHEN** the local file is deleted
- **THEN** the now-empty directory `static/snapshots/20260714/` SHALL also be removed

#### Scenario: SCP push succeeds — parent directory not empty

- **GIVEN** another snapshot file still exists in `static/snapshots/20260714/`
- **AND** the SCP push completes successfully
- **WHEN** the local file is deleted
- **THEN** the directory `static/snapshots/20260714/` SHALL NOT be removed

#### Scenario: SCP push fails — local file retained

- **GIVEN** `_save_snapshot()` saves a file locally
- **WHEN** the SCP push fails (network error, authentication error, timeout, etc.)
- **THEN** the local file SHALL NOT be deleted
- **AND** a warning log SHALL record the push failure

#### Scenario: SCP push not configured — local file retained

- **GIVEN** `snapshot_remote.host` is not configured (empty)
- **WHEN** `_save_snapshot()` saves a file locally
- **THEN** no SCP push SHALL be attempted
- **AND** the local file SHALL remain (no cleanup applicable)

#### Scenario: Local file already missing during cleanup

- **GIVEN** the SCP push completes successfully
- **AND** the local file has already been deleted by another process
- **WHEN** the cleanup logic attempts to delete the local file
- **THEN** no error SHALL be raised
- **AND** a debug log SHALL record the cleanup attempt

### Requirement: DingTalk upload falls back to cloud HTTP URL when local file absent

`AlertClient._resolve_local_snapshot()` SHALL first check if the local snapshot file exists. If the local file does not exist and `nginx_base_url` is configured, it SHALL construct a cloud server HTTP URL as fallback. `dingtalk_service._upload_image()` SHALL support both local file paths and HTTP URLs.

#### Scenario: Local file exists — use local path

- **GIVEN** `snapshot_path` is `/snapshots/20260714/evt_abc123.jpg`
- **AND** the local file `static/snapshots/20260714/evt_abc123.jpg` exists
- **WHEN** `_resolve_local_snapshot()` is called
- **THEN** it SHALL return the local absolute path string
- **AND** `_upload_image()` SHALL read the local file and upload to DingTalk

#### Scenario: Local file deleted after push — fall back to cloud URL

- **GIVEN** `snapshot_path` is `/snapshots/20260714/evt_abc123.jpg`
- **AND** the local file does NOT exist (deleted after successful SCP push)
- **AND** `nginx_base_url` is `http://39.106.209.208:9092`
- **WHEN** `_resolve_local_snapshot()` is called
- **THEN** it SHALL return `http://39.106.209.208:9092/snapshots/20260714/evt_abc123.jpg`
- **AND** `_upload_image()` SHALL download the file from the HTTP URL to a temporary file, upload to DingTalk, then delete the temporary file

#### Scenario: Local file absent and nginx_base_url not configured

- **GIVEN** `snapshot_path` is `/snapshots/20260714/evt_abc123.jpg`
- **AND** the local file does NOT exist
- **AND** `nginx_base_url` is not configured (empty)
- **WHEN** `_resolve_local_snapshot()` is called
- **THEN** it SHALL return the original `snapshot_path` unchanged
- **AND** `_upload_image()` SHALL attempt to open it as a local path (which will fail gracefully)

#### Scenario: HTTP URL download fails — DingTalk notification still sent

- **GIVEN** `_resolve_local_snapshot()` returns an HTTP URL
- **WHEN** `_upload_image()` fails to download the file (network error, 404, etc.)
- **THEN** `_upload_image()` SHALL return an empty string (no media_id)
- **AND** the DingTalk notification SHALL still be sent with text content only (no image)
- **AND** an exception log SHALL record the upload failure

#### Scenario: Temporary file from HTTP download is cleaned up

- **GIVEN** `_upload_image()` downloads a file from an HTTP URL to a temporary file
- **WHEN** the DingTalk upload completes (success or failure)
- **THEN** the temporary file SHALL be deleted

### Requirement: AlertClient accepts nginx_base_url parameter

`AlertClient` constructor SHALL accept an optional `nginx_base_url` parameter. When provided, it SHALL be used by `_resolve_local_snapshot()` to construct cloud HTTP URLs as fallback paths.

#### Scenario: nginx_base_url derived from snapshot_remote.host

- **GIVEN** `snapshot_remote.host` is `39.106.209.208`
- **AND** `SNAPSHOT_NGINX_PORT` env var is not set
- **WHEN** `create_app()` constructs `AlertClient`
- **THEN** `nginx_base_url` SHALL be `http://39.106.209.208:9092`

#### Scenario: nginx_base_url with custom port

- **GIVEN** `snapshot_remote.host` is `39.106.209.208`
- **AND** `SNAPSHOT_NGINX_PORT` env var is `8080`
- **WHEN** `create_app()` constructs `AlertClient`
- **THEN** `nginx_base_url` SHALL be `http://39.106.209.208:8080`

#### Scenario: snapshot_remote.host not configured

- **GIVEN** `snapshot_remote.host` is empty
- **WHEN** `create_app()` constructs `AlertClient`
- **THEN** `nginx_base_url` SHALL be empty string

## REMOVED Requirements

### Requirement: Flask /snapshots/ local fallback route

The `GET /snapshots/<path:filename>` route in `app.py` SHALL be removed. The frontend accesses snapshots via the cloud server Nginx 9092 endpoint; no consumer uses the Flask local route.

### Requirement: image_utils.save_snapshot function

The `save_snapshot()` function in `backend_ai/utils/image_utils.py` SHALL be removed. No code in the project calls this function; `AnalysisService._save_snapshot()` uses its own implementation.
