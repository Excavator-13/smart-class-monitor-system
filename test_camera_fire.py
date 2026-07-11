"""摄像头实时明火检测"""
import os, sys, time

os.environ["PYTHONUTF8"] = "1"
os.environ["ULTRALYTICS_DIR"] = os.path.join(os.path.dirname(__file__), "backend_ai", "models", "yolo")

import cv2
from ultralytics import YOLO
from pathlib import Path

# 加载模型
MODEL_DIR = Path(__file__).parent / "backend_ai" / "models" / "yolo"
MODEL_PATH = MODEL_DIR / "yolo_fire.pt"

print(f"加载模型: {MODEL_PATH}")
if not MODEL_PATH.exists():
    print(f"模型文件不存在！请先放到 {MODEL_PATH}")
    sys.exit(1)

model = YOLO(str(MODEL_PATH))
threshold = 0.25
print(f"模型就绪 | 阈值: {threshold}")
print(f"打开摄像头... 按 Q 退出 | +/- 调整阈值 | S 截图")

# 打开摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

detection_count = 0
last_time = time.time()
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # 每3帧检测一次（节省性能）
    if frame_count % 3 != 0:
        cv2.imshow("Fire Detection (Live)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        continue

    # YOLO 推理
    results = model(frame, verbose=False)
    fires = []

    for r in results:
        if r.boxes is not None:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf >= threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    fires.append((x1, y1, x2, y2, conf))

    if fires:
        detection_count += len(fires)

    # 绘制标注
    annotated = frame.copy()
    for x1, y1, x2, y2, conf in fires:
        if conf >= 0.8:
            color = (0, 0, 255)       # 红色 - 高危
        elif conf >= 0.6:
            color = (0, 165, 255)      # 橙色 - 警告
        else:
            color = (0, 255, 255)      # 黄色 - 提示

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"FIRE {conf:.2f}"
        cv2.putText(annotated, label, (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # 顶部警报条
    if any(c >= 0.8 for _, _, _, _, c in fires):
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (annotated.shape[1], 35), (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.4, annotated, 0.6, 0, annotated)
        cv2.putText(annotated, "FIRE ALERT!", (10, 27),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

    # 状态信息
    elapsed = time.time() - last_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    status = f"FPS:{fps:.0f} | Fires:{len(fires)} | Total:{detection_count} | Thresh:{threshold:.2f} | Q:Quit +/-:Thresh S:Shot"
    cv2.putText(annotated, status, (8, annotated.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    cv2.imshow("Fire Detection (Live)", annotated)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        os.makedirs("snapshots", exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = f"snapshots/fire_{ts}.jpg"
        cv2.imwrite(path, annotated)
        print(f"截图已保存: {path}")
    elif key in (ord('+'), ord('=')):
        threshold = min(1.0, threshold + 0.05)
        print(f"阈值: {threshold:.2f}")
    elif key == ord('-'):
        threshold = max(0.05, threshold - 0.05)
        print(f"阈值: {threshold:.2f}")

cap.release()
cv2.destroyAllWindows()
print(f"\n检测结束 | 总检测次数: {detection_count}")
