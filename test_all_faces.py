"""测全部图片 — 标注预期类型并对比"""
import sys, cv2
from pathlib import Path
sys.path.insert(0, 'backend_ai')
from services.deepfake_detector import DeepfakeDetector

d = DeepfakeDetector('backend_ai/models/mesonet/meso4_weights.pth')
c = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

ok = 0
fail = 0

for f in sorted(Path('face').glob('*')):
    if f.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
        continue

    img = cv2.imread(str(f))
    if img is None:
        continue

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = c.detectMultiScale(gray, 1.05, 4, minSize=(60, 60))
    if len(faces) == 0:
        print(f"{f.name:20s} no face")
        continue

    x, y, w, h = faces[0]
    r = d.predict(img[y:y+h, x:x+w])
    pred = 'FAKE' if r['is_fake'] else 'REAL'

    # 根据文件名判断预期
    name = f.name.lower()
    expect = 'REAL' if name.startswith('real_') or name.startswith('test2') else 'FAKE'

    match = 'OK' if pred == expect else 'FAIL'
    if match == 'OK':
        ok += 1
    else:
        fail += 1

    print(f"  [{match}] {f.name:20s} {pred:4s} (expect {expect:4s}) cnn={r['cnn_score']:.4f}")

print(f"\nTotal: {ok+fail} | OK: {ok} | FAIL: {fail}")
