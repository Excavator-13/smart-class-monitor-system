import sys, cv2; sys.path.insert(0,'backend_ai')
from services.deepfake_detector import DeepfakeDetector

detector = DeepfakeDetector('backend_ai/models/mesonet/meso4_weights.pth')
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

for label, files in [
    ("AI", ["face/test1.png","face/test3.png","face/test4.png","face/ai_01.png","face/ai_02.png"]),
    ("REAL", ["face/test2.jpg","face/real_01.png","face/real_02.png","face/real_03.png"]),
]:
    print(f"--- {label} ---")
    for f in files:
        img = cv2.imread(f)
        if img is None: continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.05, 4, minSize=(60,60))
        if len(faces)==0:
            print(f"  {f}: no face")
            continue
        x,y,w,h = faces[0]
        r = detector.predict(img[y:y+h, x:x+w])
        tag = "FAKE" if r["is_fake"] else "OK"
        ok = tag == ("FAKE" if label=="AI" else "OK")
        mark = "[OK]" if ok else "[FAIL]"
        print(f"  {mark} {f}: {tag} cnn={r['cnn_score']:.4f}")
