"""全模块摄像头实时测试 — 火焰 + 反欺骗 + 异常声学"""
import os, sys, time, threading
from pathlib import Path
from collections import deque

os.environ["PYTHONUTF8"] = "1"
os.environ["ULTRALYTICS_DIR"] = str(Path(__file__).parent / "backend_ai" / "models" / "yolo")

import cv2
import numpy as np
from ultralytics import YOLO

# ── 模型加载 ─────────────────────────────────────────
PROJECT = Path(__file__).parent

fire_model = YOLO(str(PROJECT / "backend_ai" / "models" / "yolo" / "yolo_fire.pt"))
fire_threshold = 0.25

# dlib 活体检测（如果可用）
dlib_ok = False
try:
    import dlib
    DAT_DIR = PROJECT / "backend_ai" / "models" / "dlib"
    predictor = dlib.shape_predictor(str(DAT_DIR / "shape_predictor_68_face_landmarks.dat"))
    detector = dlib.get_frontal_face_detector()
    dlib_ok = True
    print("[dlib] 人脸关键点模型加载成功")
except Exception as e:
    print(f"[dlib] 加载失败: {e}，反欺骗模块将跳过")

# 音频捕获（如果可用）
audio_ok = False
try:
    import sounddevice as sd
    audio_ok = True
    print("[audio] 麦克风就绪")
except Exception:
    print("[audio] sounddevice 未安装，声学检测将跳过")

# ── 反欺骗参数 ────────────────────────────────────────
EAR_BLINK_THRESH = 999999.0    # 已关闭（设为极大值）
EAR_VALUE_THRESH = 0.18     # 眨眼 EAR 阈值
last_blink_time = time.time()
ear_history: deque = deque(maxlen=10)
deepfake_scores: deque = deque(maxlen=20)
deepfake_alert = False
deepfake_score = 0.0

def eye_aspect_ratio(eye):
    """EAR: (|p1-p5| + |p2-p4|) / (2*|p0-p3|)"""
    a = np.linalg.norm(eye[1] - eye[5])
    b = np.linalg.norm(eye[2] - eye[4])
    c = np.linalg.norm(eye[0] - eye[3])
    return (a + b) / (2.0 * c) if c > 0 else 0

def detect_blink(history):
    """开口 → 闭口 → 开口 模式"""
    if len(history) < 4:
        return False
    r = list(history)[-4:]
    return r[0] > EAR_VALUE_THRESH and min(r[1:3]) < EAR_VALUE_THRESH and r[3] > EAR_VALUE_THRESH

# ── 音频参数 ──────────────────────────────────────────
audio_buffer = deque(maxlen=16000 * 3)
energy_history: deque = deque(maxlen=30)
baseline_energy = 0.0
baseline_count = 0
loud_event = False
loud_event_time = 0.0

def audio_callback(indata, frames, time_info, status):
    if status:
        return
    audio_buffer.extend(indata[:, 0].tolist())

def process_audio():
    """分析当前音频缓冲区，返回事件信息或None"""
    global baseline_energy, baseline_count, loud_event, loud_event_time
    if len(audio_buffer) < 16000:  # 至少1秒
        return None
    chunk = np.array(list(audio_buffer), dtype=np.float32)[-16000:]
    energy = float(np.sqrt(np.mean(chunk ** 2)))
    energy_history.append(energy)

    if baseline_count < 50:
        baseline_energy = (baseline_energy * baseline_count + energy) / (baseline_count + 1)
        baseline_count += 1
        return None

    ratio = energy / max(baseline_energy, 1e-9)
    if ratio < 3.0 or loud_event:
        return None
    loud_event = True
    loud_event_time = time.time()

    # 频域分析
    fft = np.abs(np.fft.rfft(chunk))
    n = len(fft)
    fft_energy = fft ** 2
    total = fft_energy.sum()
    if total == 0:
        return None
    fft_energy /= total

    low = int(500 / 8000 * n)
    high = int(4000 / 8000 * n)
    scream_ratio = float(fft_energy[low:high].sum()) if high > low else 0

    return {"ratio": round(ratio, 1), "scream_conf": round(min(1.0, scream_ratio * 3), 2)}

# ── 主循环 ────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if audio_ok:
    stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=16000)
    stream.start()

fire_count = 0
spoof_count = 0
audio_count = 0
frame_idx = 0
t0 = time.time()

print("\n=== 全模块实时测试 ===")
print("  Q:退出 | S:截图 | +/-:火焰阈值\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_idx += 1
    h, w = frame.shape[:2]

    # ── 1. 火焰检测 (每3帧) ──
    fires = []
    if frame_idx % 3 == 0:
        results = fire_model(frame, verbose=False)
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    conf = float(box.conf[0])
                    if conf >= fire_threshold:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        fires.append((x1, y1, x2, y2, conf))
        fire_count += len(fires)

    # ── 2. 反欺骗 (眨眼 + 换脸) ──
    spoof_msg = ""
    if dlib_ok and frame_idx % 5 == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)
        for face in faces:
            shape = predictor(frame, face)
            landmarks = np.array([[p.x, p.y] for p in shape.parts()])
            left_eye = landmarks[36:42]
            right_eye = landmarks[42:48]

            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2
            ear_history.append(ear)

            if detect_blink(ear_history):
                last_blink_time = time.time()

            elapsed = time.time() - last_blink_time
            if elapsed > EAR_BLINK_THRESH:
                spoof_msg = f"SPOOF! {elapsed:.0f}s no blink"
                spoof_count += 1

            # 换脸纹理
            rx1, ry1, rx2, ry2 = face.left(), face.top(), face.right(), face.bottom()
            rx1, ry1 = max(0, rx1), max(0, ry1)
            rx2, ry2 = min(w, rx2), min(h, ry2)
            if rx2 > rx1 and ry2 > ry1:
                roi_gray = gray[ry1:ry2, rx1:rx2]
                if roi_gray.size > 0:
                    lap_var = cv2.Laplacian(roi_gray, cv2.CV_64F).var()
                    deepfake_scores.append(lap_var)
                    if len(deepfake_scores) >= 10:
                        deepfake_score = np.mean(deepfake_scores)
                    if len(deepfake_scores) >= 10 and deepfake_score < 15:
                        deepfake_alert = True
                        spoof_msg += f" | DEEPFAKE({deepfake_score:.0f})"

    # ── 3. 音频检测 ──
    audio_msg = ""
    if audio_ok and frame_idx % 10 == 0:
        result = process_audio()
        if result:
            audio_msg = f"ABNORMAL SOUND: {result['scream_conf']:.0%} scream"
            audio_count += 1
    # 冷却重置
    if loud_event and time.time() - loud_event_time > 0.5:
        loud_event = False

    # ── 4. 绘制 ──
    draw = frame.copy()

    # 火焰框
    for x1, y1, x2, y2, conf in fires:
        color = (0, 0, 255) if conf >= 0.8 else ((0, 165, 255) if conf >= 0.6 else (0, 255, 255))
        cv2.rectangle(draw, (x1, y1), (x2, y2), color, 2)
        cv2.putText(draw, f"FIRE {conf:.2f}", (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # 状态条
    y0 = 25
    for i, (label, val) in enumerate([
        ("FIRE", f"{len(fires)} (总{fire_count})"),
        ("SPOOF", "disabled" if EAR_BLINK_THRESH > 100 else (spoof_msg or f"OK blink={time.time()-last_blink_time:.0f}s") if dlib_ok else "N/A"),
        ("DEEPFK", f"score={deepfake_score:.1f}" if dlib_ok and len(deepfake_scores) >= 10 else ("..." if dlib_ok else "N/A")),
        ("AUDIO", audio_msg or ("bld" if baseline_count < 50 else "OK")),
        ("THRESH", f"fire={fire_threshold:.2f}"),
    ]):
        color = (0, 255, 0)
        if "SPOOF!" in str(val):
            color = (0, 0, 255)
            cv2.rectangle(draw, (0, 0), (w, 32), (0, 0, 255), -1)
            cv2.putText(draw, f"⚠ SPOOF DETECTED ⚠", (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            break
        if "ABNORMAL" in str(val) or "DEEPFAKE" in str(val):
            color = (0, 0, 255)
        cv2.putText(draw, f"{label}: {val}", (10, y0 + i * 23),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    # FPS
    elapsed = time.time() - t0
    fps = frame_idx / elapsed if elapsed > 0 else 0
    cv2.putText(draw, f"FPS:{fps:.0f}", (w - 90, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    cv2.imshow("All Modules Test — Q:Quit S:Shot +/-:FireThresh", draw)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        os.makedirs("snapshots", exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(f"snapshots/test_{ts}.jpg", draw)
        print(f"  Screenshot: snapshots/test_{ts}.jpg")
    elif key in (ord('+'), ord('=')):
        fire_threshold = min(1.0, fire_threshold + 0.05)
        print(f"  Fire threshold: {fire_threshold:.2f}")
    elif key == ord('-'):
        fire_threshold = max(0.05, fire_threshold - 0.05)
        print(f"  Fire threshold: {fire_threshold:.2f}")

cap.release()
if audio_ok:
    stream.stop()
cv2.destroyAllWindows()

print(f"\n=== 测试结束 ===")
print(f"  火焰检测: {fire_count} 次")
print(f"  反欺骗告警: {spoof_count} 次")
print(f"  异常声音: {audio_count} 次")
print(f"  运行时间: {elapsed:.0f}s")
