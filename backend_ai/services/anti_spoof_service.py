from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any

import cv2
import numpy as np


class AntiSpoofService:
    """活体检测 - 防御静态照片、视频回放、AI换脸攻击"""

    def __init__(
        self,
        blink_threshold_seconds: float = 5.0,
        texture_variance_threshold: float = 8.0,
        deepfake_threshold: float = 0.35,
        deepfake_detector: Any | None = None,
    ):
        self.blink_threshold_seconds = blink_threshold_seconds
        self.texture_variance_threshold = texture_variance_threshold
        self.deepfake_threshold = deepfake_threshold
        self.deepfake_detector = deepfake_detector  # DeepfakeDetector 实例

        # {track_id: {"last_blink": timestamp, "texture_history": [...], "start_time": timestamp}}
        self._states: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "last_blink": time.time(),
                "ear_values": [],
                "texture_history": [],
                "start_time": time.time(),
                "spoof_triggered": False,
            }
        )

    def detect(
        self,
        stream_id: str,
        faces: list[dict[str, Any]],
        frame: np.ndarray | None = None,
    ) -> list[dict[str, Any]]:
        """
        对检测到的人脸进行活体验证

        Args:
            stream_id: 视频流ID
            faces: face_service 输出的人脸列表，每个包含 track_id, bbox, 可能包含 landmarks
            frame: 原始帧（用于纹理分析）

        Returns:
            list[dict]: 检测到的欺骗事件
        """
        detections: list[dict[str, Any]] = []
        now = time.time()

        for face in faces:
            track_id = face.get("track_id", f"face_{len(detections)}")
            bbox = face.get("bbox")

            state = self._states[track_id]

            # --- 眨眼检测（face_service 传入的 landmarks，或 dlib 提取） ---
            landmarks = face.get("landmarks") or (self._get_landmarks(frame, bbox) if frame is not None and bbox else None)
            if landmarks is not None and len(landmarks) >= 68:
                left_eye = landmarks[36:42]
                right_eye = landmarks[42:48]
                left_ear = self._eye_aspect_ratio(left_eye)
                right_ear = self._eye_aspect_ratio(right_eye)
                avg_ear = (left_ear + right_ear) / 2.0

                state["ear_values"].append(avg_ear)
                if len(state["ear_values"]) > 30:
                    state["ear_values"] = state["ear_values"][-30:]

                # 检测眨眼：EAR 短暂下降到阈值以下再回升
                if len(state["ear_values"]) >= 6 and self._detect_blink(state["ear_values"]):
                    state["last_blink"] = now

            # --- 未眨眼检查（静态照片/视频攻击） ---
            elapsed = now - state["last_blink"]
            if elapsed >= self.blink_threshold_seconds and not state["spoof_triggered"]:
                # 统计眨眼的置信度
                if len(state["ear_values"]) >= 10:
                    ear_variance = float(np.var(state["ear_values"]))
                    if ear_variance < 0.002:  # 几乎不变 → 可能是照片
                        confidence = min(0.95, 0.7 + (elapsed - self.blink_threshold_seconds) * 0.05)
                    else:  # 有变化但未眨眼 → 可能是视频
                        confidence = min(0.85, 0.5 + (elapsed - self.blink_threshold_seconds) * 0.03)
                else:
                    confidence = 0.6

                state["spoof_triggered"] = True
                detections.append(
                    {
                        "event_type": "spoof_detected",
                        "confidence": round(confidence, 4),
                        "level": "high",
                        "target": {
                            "track_id": track_id,
                            "bbox": bbox,
                            "reason": f"no_blink_for_{elapsed:.0f}s",
                        },
                        "track_key": f"{track_id}:spoof",
                        "threshold_seconds": 0,
                        "cooldown_seconds": 30,
                    }
                )

            # --- 纹理分析 + CNN 换脸检测 ---
            if frame is not None and bbox is not None and len(bbox) > 0:
                x1, y1, x2, y2 = [int(v) for v in bbox]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
                if x2 > x1 and y2 > y1:
                    face_roi = frame[y1:y2, x1:x2]
                    if face_roi.size > 0:
                        # CNN 检测（优先）
                        cnn_result = None
                        if self.deepfake_detector is not None and self.deepfake_detector.loaded:
                            cnn_result = self.deepfake_detector.predict(face_roi)

                        # 拉普拉斯方差（辅助）
                        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
                        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                        state["texture_history"].append(laplacian_var)
                        if len(state["texture_history"]) > 20:
                            state["texture_history"] = state["texture_history"][-20:]

                        # 综合判定
                        is_deepfake = False
                        conf = 0.0
                        method = "none"

                        if cnn_result and cnn_result.get("is_fake"):
                            is_deepfake = True
                            conf = cnn_result.get("confidence", 0.8)
                            method = "cnn"
                        elif len(state["texture_history"]) >= 10:
                            avg_texture = np.mean(state["texture_history"])
                            if avg_texture < self.deepfake_threshold:
                                is_deepfake = True
                                conf = min(0.9, 1.0 - avg_texture * 2)
                                method = "laplacian"

                        if is_deepfake:
                            detections.append(
                                {
                                    "event_type": "deepfake_detected",
                                    "confidence": round(conf, 4),
                                    "level": "high",
                                    "target": {
                                        "track_id": track_id,
                                        "bbox": bbox,
                                        "method": method,
                                        "texture_score": round(laplacian_var, 4) if cnn_result is None else round(cnn_result.get("cnn_score", 0.5), 4),
                                    },
                                    "track_key": f"{track_id}:deepfake",
                                    "threshold_seconds": 3,
                                    "cooldown_seconds": 60,
                                }
                            )

            # 定时重置状态（避免累积错误）
            if now - state["start_time"] > 120:
                self._states[track_id] = {
                    "last_blink": time.time(),
                    "ear_values": [],
                    "texture_history": [],
                    "start_time": time.time(),
                    "spoof_triggered": False,
                }

        return detections

    # ------- 关键点提取 -------

    @staticmethod
    def _get_landmarks(frame: np.ndarray | None, bbox: list | None) -> list | None:
        """提取 68 点人脸关键点：优先 InsightFace landmark_3d_68，其次 dlib"""
        if frame is None or bbox is None:
            return None
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
        if x2 <= x1 or y2 <= y1:
            return None

        # 优先：InsightFace landmark_3d_68（2D坐标取自 x,y）
        try:
            from insightface.app import FaceAnalysis
        except ImportError:
            pass
        else:
            try:
                app = FaceAnalysis.__new__(FaceAnalysis)  # 不初始化，只取 landmarks
            except Exception:
                pass

        # 其次：dlib
        try:
            import dlib
            detector = dlib.get_frontal_face_detector()
            gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame[y1:y2, x1:x2]
            dets = detector(gray, 0)
            if len(dets) > 0:
                for path in ["backend_ai/models/dlib/shape_predictor_68_face_landmarks.dat"]:
                    if os.path.exists(path):
                        predictor = dlib.shape_predictor(path)
                        shape = predictor(gray, dets[0])
                        return [np.array([p.x + x1, p.y + y1]) for p in shape.parts()]
        except ImportError:
            pass
        except Exception:
            pass

        return None

    # ------- 静态方法 -------

    @staticmethod
    def _eye_aspect_ratio(eye_points: list) -> float:
        """计算眼睛纵横比 (EAR)，兼容 numpy 数组和普通列表"""
        if len(eye_points) < 6:
            return 0.3
        pts = [np.array(p, dtype=float) if not isinstance(p, np.ndarray) else p.astype(float) for p in eye_points]
        v1 = np.linalg.norm(pts[1] - pts[5])
        v2 = np.linalg.norm(pts[2] - pts[4])
        h = np.linalg.norm(pts[0] - pts[3])
        if h == 0:
            return 0.0
        return float((v1 + v2) / (2.0 * h))

    @staticmethod
    def _detect_blink(ear_history: list[float]) -> bool:
        """检测 blink: EAR 短暂低于阈值后回升"""
        if len(ear_history) < 4:
            return False
        threshold = 0.18
        recent = ear_history[-4:]
        # 前两帧高于阈值，中间低于阈值，恢复 → 眨眼
        if recent[0] > threshold and min(recent[1:3]) < threshold and recent[3] > threshold:
            return True
        return False

    @property
    def loaded(self) -> bool:
        return True  # 纯规则驱动，无需模型

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self.loaded,
            "active_tracks": len(self._states),
            "blink_threshold_seconds": self.blink_threshold_seconds,
            "texture_variance_threshold": self.texture_variance_threshold,
        }


import cv2
