"""训练 MesoNet — 从 face/ 目录自动分类真人/AI脸"""
import sys, os
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).parent / "backend_ai"))
from services.deepfake_detector import DeepfakeDetector

MODEL_DIR = Path(__file__).parent / "backend_ai" / "models" / "mesonet"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
WEIGHTS = MODEL_DIR / "meso4_weights.pth"

FACE_DIR = Path("face")
real_images, fake_images = [], []

for f in sorted(FACE_DIR.glob("*")):
    if f.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        continue
    img = cv2.imread(str(f))
    if img is None:
        continue

    name = f.name.lower()
    if name.startswith("real_") or name.startswith("test2"):
        real_images.append(img)
        print(f"[REAL] {f.name}")
    else:
        fake_images.append(img)
        print(f"[FAKE] {f.name}")

if len(real_images) < 2 or len(fake_images) < 2:
    print(f"\nNeed >=2 real + >=2 fake. Got: {len(real_images)} real, {len(fake_images)} fake")
    sys.exit(1)

print(f"\nTraining: {len(real_images)} real + {len(fake_images)} fake ({(len(real_images)+len(fake_images))*4} augmented)")
print("=" * 55)

detector = DeepfakeDetector()
result = detector.train_quick(real_images, fake_images, epochs=100, save_path=str(WEIGHTS))

print("=" * 55)
print(f"Done! Accuracy: {result['accuracy']:.1%}")
print(f"Weights: {WEIGHTS}")
print(f"\nTest: python detect_deepfake.py face/test1.png")
