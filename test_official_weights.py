import sys, cv2
sys.path.insert(0, 'backend_ai')
from services.deepfake_detector import DeepfakeDetector

detector = DeepfakeDetector('backend_ai/models/mesonet/meso4_official.pth')
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

for f in ['face/test1.png', 'face/test2.jpg', 'face/test3.png', 'face/test4.png']:
    img = cv2.imread(f)
    if img is None:
        print(f"{f}: not found")
        continue
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.05, 4, minSize=(80, 80))
    if len(faces) == 0:
        print(f"{f}: no face")
        continue
    x, y, w, h = faces[0]
    roi = img[y:y+h, x:x+w]
    r = detector.predict(roi)
    tag = "FAKE" if r["is_fake"] else "OK"
    print(f"{f}: [{tag}] cnn={r['cnn_score']:.4f} lap={r['laplacian_var']}")
