"""照片换脸检测 v3 — CNN MesoNet + 规则融合"""
from __future__ import annotations

import sys, os
from pathlib import Path

import cv2
import numpy as np

os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent / "backend_ai"))

# Haar cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# MesoNet
cnn_available = False
detector = None
try:
    from services.deepfake_detector import DeepfakeDetector

    weights = Path(__file__).parent / "backend_ai" / "models" / "mesonet" / "meso4_weights.pth"
    detector = DeepfakeDetector(str(weights) if weights.exists() else None)
    cnn_available = detector.loaded
    print(f"[CNN] MesoNet {'loaded' if cnn_available else 'no weights (rule-based fallback)'}")
except Exception as e:
    print(f"[CNN] Failed: {e} (rule-based fallback)")


def detect_faces(img: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.05, 4, minSize=(80, 80))
    return [(x, y, x + w, y + h) for (x, y, w, h) in faces]


def check_image(path: str) -> dict:
    img = cv2.imread(path)
    if img is None:
        return {"error": f"Cannot read: {path}"}

    h, w = img.shape[:2]
    faces = detect_faces(img)

    if not faces:
        return {"size": f"{w}x{h}", "faces": 0, "warning": "No face detected"}

    results = []
    for x1, y1, x2, y2 in faces:
        if (x2 - x1) < 40 or (y2 - y1) < 40:
            continue
        face_roi = img[y1:y2, x1:x2]

        if detector is not None:
            r = detector.predict(face_roi)
            results.append({
                "bbox": [x1, y1, x2, y2],
                "is_fake": r["is_fake"],
                "confidence": r["confidence"],
                "method": r["method"],
                "cnn_score": r.get("cnn_score", 0.5),
                "laplacian": r.get("laplacian_var", 0),
                "verdict": "FAKE" if r["is_fake"] else "REAL",
            })
        else:
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            fft = np.fft.fft2(gray.astype(np.float32))
            fft_mag = np.abs(np.fft.fftshift(fft))
            total = fft_mag.sum()
            low_ratio = 0.0
            if total > 0:
                ch, cw = gray.shape[0] // 2, gray.shape[1] // 2
                r_fft = max(1, min(ch, cw) // 3)
                low_ratio = float(fft_mag[ch - r_fft:ch + r_fft, cw - r_fft:cw + r_fft].sum() / total)
            is_fake = lap_var < 10.0 and low_ratio > 0.65
            results.append({
                "bbox": [x1, y1, x2, y2],
                "is_fake": is_fake,
                "confidence": round(max(0.0, 1.0 - lap_var / 20.0), 2),
                "method": "rule",
                "laplacian": lap_var,
                "verdict": "FAKE" if is_fake else "REAL",
            })

    return {"size": f"{w}x{h}", "faces": len(results), "results": results}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect_deepfake.py <image>")
        sys.exit(1)

    path = sys.argv[1]
    result = check_image(path)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    print(f"\nImage: {path}  Size: {result['size']}  Faces: {result['faces']}")
    if result.get("warning"):
        print(f"WARNING: {result['warning']}")
        sys.exit(0)

    for i, r in enumerate(result["results"]):
        tag = "FAKE" if r["is_fake"] else "REAL"
        print(f"  Face {i+1}: {tag}  method={r['method']}  conf={r['confidence']}")
        if "cnn_score" in r:
            print(f"           cnn_score={r['cnn_score']}  laplacian={r['laplacian']}")

        # Save annotated
        img = cv2.imread(path)
        x1, y1, x2, y2 = r["bbox"]
        color = (0, 0, 255) if r["is_fake"] else (0, 255, 0)
        label = f"{r['verdict']} ({r['method']})"
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        cv2.putText(img, label, (x1, max(y1 - 10, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        out = Path(path).stem + "_result.jpg"
        cv2.imwrite(out, img)
        print(f"  Saved: {out}")
        print()
