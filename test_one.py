import sys, cv2; sys.path.insert(0,'backend_ai')
from services.deepfake_detector import DeepfakeDetector
d = DeepfakeDetector('backend_ai/models/mesonet/meso4_weights.pth')
c = cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
for fname in sys.argv[1:] if len(sys.argv) > 1 else ['face/test6.jpg', 'face/test7.jpg']:
    img = cv2.imread(fname)
    if img is None:
        print(f"{fname}: not found")
        continue
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    f = c.detectMultiScale(g, 1.05, 4, minSize=(60,60))
    if len(f)==0:
        print(f"{fname}: no face")
        continue
    x,y,w,h = f[0]
    r = d.predict(img[y:y+h, x:x+w])
    t = 'FAKE' if r['is_fake'] else 'REAL'
    print(f"{fname}: {t} cnn={r['cnn_score']:.4f} lap={r['laplacian_var']}")
