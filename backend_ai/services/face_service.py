from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from backend_ai.utils.image_utils import decode_base64_image


class FaceError(ValueError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class FaceService:
    def __init__(self, model: Any | None = None, feature_dim: int = 512, similarity_threshold: float = 0.45):
        self.model = model
        self.feature_dim = feature_dim
        self.similarity_threshold = similarity_threshold
        self.loaded = model is not None

    def load_model(self) -> None:
        if self.model is not None:
            self.loaded = True
            return
        try:
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            self.model = app
            self.loaded = True
        except Exception:
            self.loaded = False

    def _faces(self, frame: np.ndarray) -> list[Any]:
        if self.model is not None and hasattr(self.model, "get"):
            return list(self.model.get(frame))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        boxes = detector.detectMultiScale(gray, 1.1, 4)
        faces = []
        for x, y, w, h in boxes:
            roi = cv2.resize(gray[y : y + h, x : x + w], (32, 16)).astype("float32").flatten()
            feature = np.zeros(self.feature_dim, dtype="float32")
            feature[: min(len(roi), self.feature_dim)] = roi[: self.feature_dim]
            norm = np.linalg.norm(feature) or 1.0
            faces.append({"bbox": [int(x), int(y), int(x + w), int(y + h)], "embedding": feature / norm})
        return faces

    def extract_feature_from_base64(self, image: str) -> dict[str, Any]:
        try:
            frame = decode_base64_image(image)
        except ValueError as exc:
            raise FaceError(40001, "invalid image") from exc
        return self.extract_feature(frame)

    def extract_feature(self, frame: np.ndarray) -> dict[str, Any]:
        faces = self._faces(frame)
        if len(faces) == 0:
            raise FaceError(40002, "no face detected")
        if len(faces) > 1:
            raise FaceError(40003, "multiple faces detected")
        face = faces[0]
        embedding = np.asarray(face["embedding"] if isinstance(face, dict) else face.embedding, dtype=float)
        if embedding.size != self.feature_dim:
            resized = np.zeros(self.feature_dim, dtype=float)
            resized[: min(embedding.size, self.feature_dim)] = embedding[: self.feature_dim]
            embedding = resized
        bbox = face["bbox"] if isinstance(face, dict) else [int(v) for v in face.bbox]
        return {
            "face_count": 1,
            "feature_dim": self.feature_dim,
            "feature_vector": [float(v) for v in embedding.tolist()],
            "quality": {"score": 1.0, "brightness": "unknown", "blur": "unknown"},
            "bbox": bbox,
        }

    def recognize_frame(self, frame: np.ndarray, feature_cache: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        faces = self._faces(frame)
        events = []
        for idx, face in enumerate(faces):
            embedding = np.asarray(face["embedding"] if isinstance(face, dict) else face.embedding, dtype=float)
            bbox = face["bbox"] if isinstance(face, dict) else [int(v) for v in face.bbox]
            best: tuple[float, dict[str, Any] | None] = (-1.0, None)
            for student in feature_cache.values():
                vector = np.asarray(student.get("feature_vector") or [], dtype=float)
                if vector.size != embedding.size or vector.size == 0:
                    continue
                similarity = float(np.dot(embedding, vector) / ((np.linalg.norm(embedding) * np.linalg.norm(vector)) or 1.0))
                if similarity > best[0]:
                    best = (similarity, student)
            if best[1] and best[0] >= self.similarity_threshold:
                student = best[1]
                events.append(
                    {
                        "event_type": "face_recognized",
                        "confidence": best[0],
                        "level": "info",
                        "target": {
                            "track_id": f"face_{idx + 1}",
                            "student_id": student.get("student_id"),
                            "student_name": student.get("student_name"),
                            "bbox": bbox,
                        },
                        "track_key": str(student.get("student_id")),
                        "threshold_seconds": 0,
                    }
                )
            else:
                events.append(
                    {
                        "event_type": "stranger_detected",
                        "confidence": max(best[0], 0.0),
                        "level": "warning",
                        "target": {"track_id": f"face_{idx + 1}", "bbox": bbox},
                        "track_key": f"face_{idx + 1}",
                        "threshold_seconds": 0,
                    }
                )
        return events

