from __future__ import annotations

import subprocess
import threading
from pathlib import Path

from backend_ai.utils.logger import get_logger


class SnapshotPusher:
    def __init__(self, host: str, user: str, remote_path: str):
        self.host = host
        self.user = user
        self.remote_path = remote_path
        self.logger = get_logger(__name__)

    @property
    def enabled(self) -> bool:
        return bool(self.host)

    def push_async(self, local_path: Path, relative_path: str) -> None:
        if not self.enabled:
            return
        t = threading.Thread(target=self._push, args=(local_path, relative_path), daemon=True)
        t.start()

    def _push(self, local_path: Path, relative_path: str) -> None:
        try:
            sub_path = relative_path.lstrip("/")
            if sub_path.startswith("snapshots/"):
                sub_path = sub_path[len("snapshots/"):]
            remote_dir = f"{self.remote_path}/{sub_path.rsplit('/', 1)[0]}"
            remote_file = f"{self.remote_path}/{sub_path}"
            target = f"{self.user}@{self.host}"

            mkdir_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", target, f"mkdir -p {remote_dir}"]
            result = subprocess.run(mkdir_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.logger.warning("SSH mkdir failed for %s: %s", remote_dir, result.stderr.strip())
                return

            scp_cmd = [
                "scp", "-o", "StrictHostKeyChecking=no",
                str(local_path),
                f"{target}:{remote_file}",
            ]
            result = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.logger.warning("SCP push failed for %s: %s", relative_path, result.stderr.strip())
                return

            self.logger.debug("Snapshot pushed: %s → %s:%s", relative_path, self.host, remote_file)
        except Exception as exc:
            self.logger.warning("Snapshot push error for %s: %s", relative_path, exc)