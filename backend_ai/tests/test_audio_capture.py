from __future__ import annotations

from io import BytesIO

import numpy as np

from backend_ai.services.audio_capture import AudioCapture


class FakeProcess:
    def __init__(self, raw: bytes = b"", return_code=None, pid: int = 1234):
        self.stdout = BytesIO(raw)
        self.return_code = return_code
        self.pid = pid

    def poll(self):
        return self.return_code

    def terminate(self):
        self.return_code = 0

    def wait(self, timeout=None):
        return self.return_code

    def kill(self):
        self.return_code = -9


def test_missing_ffmpeg_is_reported(monkeypatch):
    capture = AudioCapture("rtmp://example/live/test", restart_interval_seconds=0)
    monkeypatch.setattr(capture, "_resolve_ffmpeg_executable", lambda: None)

    assert not capture.start()
    assert capture._proc is None
    assert capture.last_error == "ffmpeg executable not found"


def test_read_chunk_restarts_finished_process(monkeypatch):
    samples = np.full(160, 0.25, dtype=np.float32)
    replacement = FakeProcess(samples.tobytes())
    capture = AudioCapture("rtmp://example/live/test", sample_rate=1600, restart_interval_seconds=0)
    capture._proc = FakeProcess(return_code=1)

    monkeypatch.setattr(capture, "_resolve_ffmpeg_executable", lambda: "ffmpeg")
    monkeypatch.setattr("backend_ai.services.audio_capture.subprocess.Popen", lambda *args, **kwargs: replacement)

    chunk = capture.read_chunk(chunk_ms=100)

    assert np.allclose(chunk, samples)
    assert capture.chunks_read == 1
    assert capture.last_chunk_at is not None


def test_conda_ffmpeg_fallback(monkeypatch, tmp_path):
    executable = tmp_path / "Library" / "bin" / "ffmpeg.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()
    capture = AudioCapture("rtmp://example/live/test")

    monkeypatch.setattr("backend_ai.services.audio_capture.shutil.which", lambda _name: None)
    monkeypatch.setattr("backend_ai.services.audio_capture.sys.prefix", str(tmp_path))

    assert capture._resolve_ffmpeg_executable() == str(executable)
