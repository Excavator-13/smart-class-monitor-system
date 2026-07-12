## FIXED Requirements

### Requirement: AI pushes snapshot to cloud server after local save

After `_save_snapshot()` saves the JPEG file locally, the AI service SHALL asynchronously push the file to the cloud server via SCP. The remote directory structure SHALL mirror the local structure (`{remote_path}/{day}/{event_id}.jpg`).

#### Scenario: Snapshot pushed to cloud server

- **WHEN** `_save_snapshot()` saves a file to `static/snapshots/20260712/evt_abc123.jpg`
- **AND** `snapshot_remote.host` is configured
- **THEN** the file SHALL be pushed to `{snapshot_remote.user}@{snapshot_remote.host}:{snapshot_remote.path}/20260712/evt_abc123.jpg`
- **AND** the push SHALL be asynchronous (non-blocking to the alert pipeline)

#### Scenario: Remote push fails gracefully

- **WHEN** the SCP push fails (network error, authentication error, etc.)
- **THEN** the local file SHALL still exist and the alert SHALL still be pushed to SpringBoot
- **AND** a warning SHALL be logged with the error details
- **AND** the `snapshot_path` SHALL still be returned (local file exists, may be synced later)

#### Scenario: Remote push not configured

- **WHEN** `snapshot_remote.host` is not configured (empty or absent)
- **THEN** no SCP push SHALL be attempted
- **AND** the snapshot SHALL only be saved locally

### Requirement: Snapshot remote push configuration

The AI service SHALL read remote push configuration from `config/app.yaml` under `snapshot_remote` section, with environment variable overrides:

| Config key             | Env var                | Description              | Default                |
| ---------------------- | ---------------------- | ------------------------ | ---------------------- |
| `snapshot_remote.host` | `SNAPSHOT_REMOTE_HOST` | Cloud server hostname/IP | (empty, push disabled) |
| `snapshot_remote.user` | `SNAPSHOT_REMOTE_USER` | SSH username             | `root`                 |
| `snapshot_remote.path` | `SNAPSHOT_REMOTE_PATH` | Remote directory path    | `/data/snapshots`      |

#### Scenario: Configuration from environment variable

- **WHEN** env var `SNAPSHOT_REMOTE_HOST` is set to `39.106.209.208`
- **THEN** `snapshot_remote.host` SHALL be `39.106.209.208` regardless of `app.yaml` value

#### Scenario: Configuration from app.yaml

- **WHEN** env var `SNAPSHOT_REMOTE_HOST` is not set
- **AND** `app.yaml` contains `snapshot_remote.host: 39.106.209.208`
- **THEN** `snapshot_remote.host` SHALL be `39.106.209.208`

### Requirement: SCP push uses existing SSH authentication

The SCP push SHALL use the system's existing SSH configuration (default key `~/.ssh/id_rsa` or ssh-agent). No password prompt SHALL be expected. The push SHALL be executed via `subprocess` calling `scp -o StrictHostKeyChecking=no`.

#### Scenario: SCP uses default SSH credentials

- **WHEN** a snapshot is pushed to the remote server
- **THEN** the SCP command SHALL use the default SSH key / ssh-agent
- **AND** SHALL NOT prompt for a password

#### Scenario: Remote directory auto-created

- **WHEN** the remote day subdirectory does not exist (e.g., `/data/snapshots/20260712/`)
- **THEN** the SCP command SHALL create parent directories as needed (using `mkdir -p` via SSH before SCP)

### Requirement: Frontend accesses snapshots via Nginx on cloud server

The frontend SHALL continue to use `joinResourceUrl(snapshot_url)` which concatenates `NGINX_BASE` with the relative `snapshot_url`. The cloud server Nginx SHALL serve snapshot files from the remote path configured in `snapshot_remote.path`.

#### Scenario: Frontend accesses snapshot via Nginx

- **WHEN** an alert has `snapshot_url: "/snapshots/20260712/evt_abc.jpg"`
- **AND** `NGINX_BASE` is `http://39.106.209.208:9092`
- **THEN** the frontend SHALL request `http://39.106.209.208:9092/snapshots/20260712/evt_abc.jpg`
- **AND** Nginx SHALL serve the file from `/data/snapshots/20260712/evt_abc.jpg`

### Requirement: Flask local /snapshots route as fallback

The Flask application SHALL register a route for `/snapshots/<path:filename>` that serves files from the `static/snapshots` directory using `send_from_directory`. This serves as a local fallback for development and direct AI access.

#### Scenario: Local snapshot served correctly

- **WHEN** a snapshot file exists at `static/snapshots/20260712/evt_abc123.jpg`
- **AND** a GET request is made to `/snapshots/20260712/evt_abc123.jpg` on the Flask server
- **THEN** the Flask server SHALL return the JPEG file with `Content-Type: image/jpeg`

#### Scenario: Snapshot path traversal blocked

- **WHEN** a GET request is made to `/snapshots/../../etc/passwd`
- **THEN** the Flask server SHALL return HTTP 404 or 400
- **AND** SHALL NOT serve files outside the `static/snapshots` directory

---

## Cloud Server Manual Setup (NOT automated by this change)

The following steps MUST be performed manually on the cloud server. This change does NOT automate cloud server configuration.

### Step 1: Create snapshot directory

```bash
mkdir -p /data/snapshots
```

### Step 2: Configure Nginx to serve snapshots

Add the following `location` block to the Nginx configuration (the same Nginx that serves RTMP on port 9092):

```nginx
location /snapshots/ {
    alias /data/snapshots/;
    autoindex off;
}
```

After editing, reload Nginx:

```bash
nginx -t && nginx -s reload
```

### Step 3: Verify SCP works from local machine

From the machine where the AI service runs, verify that passwordless SCP to the cloud server works:

```bash
echo "test" | scp - /tmp/test_scp.txt root@39.106.209.208:/data/snapshots/test_scp.txt
```

If this prompts for a password, set up SSH key authentication first:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
ssh-copy-id root@39.106.209.208
```
